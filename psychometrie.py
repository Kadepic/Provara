"""
psychometrie.py — Tests psychométriques (validité / fiabilité) : formules ÉTABLIES, mécanismes EXACTS.

Sujet PARTIELLEMENT factuel : on N'INVENTE PAS de résultats de test, ni de normes propres à un test
particulier. On implémente les DÉFINITIONS / FORMULES psychométriques standard (théorie classique des
tests, échelle de QI de type Wechsler) — le MÉCANISME est exact, la réponse est entièrement déterminée
par les ENTRÉES fournies (score brut, moyenne, écart-type, variances, fiabilité). Aucune donnée de test
codée en dur, aucune estimation, aucune heuristique.

Conventions SOURCÉES (établies, certaines) :
  • Échelle de QI déviation (Wechsler / Stanford-Binet moderne) : moyenne = 100, écart-type = 15.
  • Loi normale : distribution de référence des scores de QI dans la population.

Mécanismes EXACTS (manuels de psychométrie / théorie classique des tests) :

  • qi_standardise(score_brut, moyenne, ecart_type) = 100 + 15 · (score_brut − moyenne) / ecart_type
      Conversion d'un score brut en QI déviation (score standard z, ré-étalonné sur moyenne 100, σ 15).
      Ex. score = moyenne -> QI 100 ; score = moyenne + 1·σ -> QI 115 ; + 2·σ -> QI 130.
      ecart_type > 0 (dénominateur ; un test sans dispersion ne standardise rien -> abstention).

  • rang_percentile_qi(qi) = 100 · Φ((qi − 100) / 15)
      Rang percentile d'un QI sous la loi normale N(100, 15²). Φ = fonction de répartition normale
      standard (EXACTE via la fonction d'erreur : Φ(z) = ½·(1 + erf(z/√2))).
      Ex. QI 100 -> 50e percentile ; QI 115 -> ≈ 84e ; QI 130 -> ≈ 98e ; QI 85 -> ≈ 16e.
      Résultat dans l'intervalle ouvert (0, 100). (Convention d'échelle Wechsler : moyenne 100, σ 15.)

  • alpha_cronbach(k_items, variance_moyenne_item, variance_totale)
        = (k/(k−1)) · (1 − Σσ²ᵢ/σ²_total),   où Σσ²ᵢ = k · variance_moyenne_item
      Coefficient alpha de Cronbach (cohérence interne / fiabilité). 'variance_moyenne_item' est la
      variance MOYENNE des items (Σσ²ᵢ / k) ; on remonte à la somme des variances d'items par
      Σσ²ᵢ = k_items · variance_moyenne_item.
      k_items = nombre d'items, entier >= 2 (sinon k−1 = 0, indéfini -> abstention).
      variance_moyenne_item >= 0 (une variance ne peut être négative), variance_totale > 0 (dénominateur).
      α atteint son MAXIMUM 1 quand les items sont parfaitement corrélés ; il PEUT être négatif (échelle
      incohérente, covariances négatives) : c'est un résultat réel, on le renvoie sans le tronquer.
      (Cronbach, 1951 ; α ∈ [0,1] est la plage interprétable usuelle, pas une contrainte imposée.)

  • erreur_standard_mesure(ecart_type_test, fiabilite) = ecart_type_test · √(1 − fiabilite)
      Erreur standard de mesure (SEM) : dispersion de l'erreur autour du score vrai.
      ecart_type_test = écart-type des scores observés, >= 0.
      fiabilite = coefficient de fiabilité (ex. alpha), 0 <= fiabilite <= 1.
      Ex. SD 15, fiabilité 0.75 -> 15·√0.25 = 7.5. Fiabilité 1 -> SEM 0 (aucune erreur) ;
      fiabilité 0 -> SEM = SD (toute la variance est erreur).

ABSTENTION STRUCTURELLE (faux positif INTERDIT — toute entrée hors référentiel -> ValueError) :
  • ecart_type <= 0, variance_totale <= 0, k_items < 2 ou non entier, fiabilite hors [0,1],
    ecart_type_test < 0, variance_moyenne_item < 0 -> ValueError ;
  • toute valeur non finie (NaN, ±inf), non numérique ou booléenne -> ValueError.

Sorties arrondies à 6 décimales. stdlib uniquement. Fonctions pures déterministes.
"""

import math

__all__ = [
    "qi_standardise",
    "rang_percentile_qi",
    "alpha_cronbach",
    "erreur_standard_mesure",
    "MOYENNE_QI",
    "ECART_TYPE_QI",
]

# ── Conventions d'échelle SOURCÉES (QI déviation, Wechsler / Stanford-Binet moderne) ───────────────
MOYENNE_QI = 100.0
ECART_TYPE_QI = 15.0

_PRECISION = 6


def _reel_fini(x, nom):
    """Convertit en float fini, sinon ValueError (abstention)."""
    if isinstance(x, bool):  # True/False n'est pas une quantité psychométrique
        raise ValueError(f"{nom} booléen : {x!r}")
    try:
        v = float(x)
    except (TypeError, ValueError):
        raise ValueError(f"{nom} non numérique : {x!r}")
    if not math.isfinite(v):
        raise ValueError(f"{nom} non fini : {x!r}")
    return v


def _non_negatif(x, nom):
    """float fini >= 0, sinon ValueError."""
    v = _reel_fini(x, nom)
    if v < 0.0:
        raise ValueError(f"{nom} négatif : {v}")
    return v


def _positif(x, nom):
    """float fini > 0 (dénominateur), sinon ValueError."""
    v = _reel_fini(x, nom)
    if v <= 0.0:
        raise ValueError(f"{nom} non strictement positif : {v}")
    return v


def _entier(x, nom):
    """Entier exact (int ou float à valeur entière), non booléen, fini, sinon ValueError."""
    if isinstance(x, bool):
        raise ValueError(f"{nom} booléen : {x!r}")
    if isinstance(x, int):
        return x
    if isinstance(x, float):
        if not math.isfinite(x) or x != int(x):
            raise ValueError(f"{nom} non entier : {x!r}")
        return int(x)
    raise ValueError(f"{nom} non entier : {x!r}")


def _phi(z):
    """Fonction de répartition de la loi normale standard, EXACTE : Φ(z) = ½·(1 + erf(z/√2))."""
    return 0.5 * (1.0 + math.erf(z / math.sqrt(2.0)))


def qi_standardise(score_brut, moyenne, ecart_type):
    """
    QI standardisé (échelle déviation moyenne 100, σ 15) = 100 + 15·(score_brut − moyenne)/ecart_type.

    score_brut, moyenne : réels finis quelconques.
    ecart_type          : écart-type de l'étalonnage, > 0 (dénominateur).
    ecart_type <= 0, valeurs non finies / non numériques / booléennes -> ValueError.
    """
    s = _reel_fini(score_brut, "score_brut")
    m = _reel_fini(moyenne, "moyenne")
    sigma = _positif(ecart_type, "ecart_type")
    return round(MOYENNE_QI + ECART_TYPE_QI * (s - m) / sigma, _PRECISION)


def rang_percentile_qi(qi):
    """
    Rang percentile d'un QI sous la loi normale N(100, 15²) = 100·Φ((qi − 100)/15).

    qi  : QI déviation, réel fini quelconque.
    Résultat dans (0, 100). Valeur non finie / non numérique / booléenne -> ValueError.
    """
    q = _reel_fini(qi, "qi")
    z = (q - MOYENNE_QI) / ECART_TYPE_QI
    return round(100.0 * _phi(z), _PRECISION)


def alpha_cronbach(k_items, variance_moyenne_item, variance_totale):
    """
    Coefficient alpha de Cronbach = (k/(k−1))·(1 − Σσ²ᵢ/σ²_total), avec Σσ²ᵢ = k·variance_moyenne_item.

    k_items               : nombre d'items, entier >= 2.
    variance_moyenne_item : variance moyenne des items (Σσ²ᵢ/k), >= 0.
    variance_totale       : variance des scores totaux, > 0 (dénominateur).
    k < 2, k non entier, variance_moyenne_item < 0, variance_totale <= 0, valeurs non finies /
    non numériques / booléennes -> ValueError. α peut être négatif (renvoyé tel quel).
    """
    k = _entier(k_items, "k_items")
    if k < 2:
        raise ValueError(f"k_items doit être >= 2 (sinon k−1 = 0 indéfini) : {k}")
    v_item = _non_negatif(variance_moyenne_item, "variance_moyenne_item")
    v_tot = _positif(variance_totale, "variance_totale")
    somme_var_items = k * v_item
    alpha = (k / (k - 1.0)) * (1.0 - somme_var_items / v_tot)
    return round(alpha, _PRECISION)


def erreur_standard_mesure(ecart_type_test, fiabilite):
    """
    Erreur standard de mesure (SEM) = ecart_type_test · √(1 − fiabilite).

    ecart_type_test : écart-type des scores observés, >= 0.
    fiabilite       : coefficient de fiabilité, 0 <= fiabilite <= 1.
    ecart_type_test < 0, fiabilite hors [0,1], valeurs non finies / non numériques / booléennes
    -> ValueError.
    """
    sd = _non_negatif(ecart_type_test, "ecart_type_test")
    r = _reel_fini(fiabilite, "fiabilite")
    if r < 0.0 or r > 1.0:
        raise ValueError(f"fiabilite hors [0,1] : {r}")
    return round(sd * math.sqrt(1.0 - r), _PRECISION)
