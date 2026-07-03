"""
gestion_risque.py — Gestion du risque (finance / assurance) : mesures de risque EXACTES.

Mécanismes EXACTS / définitions standard. Chaque fonction est une formule arithmétique
déterministe sur des quantités OBSERVÉES (probabilités, moyennes/écarts-types empiriques,
montants). Aucune valeur-pays/secteur inventée : on calcule la mesure, on ne devine pas la donnée.

  • esperance_perte(probabilite, montant) = probabilite · montant
      Espérance de perte (perte attendue) d'un événement défavorable.
      probabilite ∈ [0, 1] (probabilité de survenance), montant >= 0 (perte si l'événement survient).
      Ex. 0.01 · 100000 = 1000  (1 % de chance de perdre 100 000 -> perte attendue 1 000).

  • value_at_risk_parametrique(moyenne, ecart_type, z=1.645) = -(moyenne - z·ecart_type)
      VaR paramétrique (gaussienne) = perte maximale au seuil de confiance, sur l'horizon donné.
      z = quantile de la loi normale standard : 1.645 (95 %), 2.326 (99 %), 1.282 (90 %).
      moyenne = rendement/résultat attendu (réel quelconque), ecart_type > 0, z > 0.
      VaR > 0 = perte ; VaR < 0 = pas de perte attendue au seuil (le quantile reste un gain).
      Ex. moyenne 0, σ 1, z 1.645  -> -(0 - 1.645) = 1.645  (VaR d'une normale standardisée à 95 %).

  • ratio_sharpe(rendement, taux_sans_risque, ecart_type) = (rendement - taux_sans_risque) / ecart_type
      Ratio de Sharpe : excès de rendement par unité de risque (écart-type des rendements).
      ecart_type > 0 (dénominateur = risque). Peut être négatif si rendement < taux sans risque.
      Ex. (0.10 - 0.02) / 0.15 = 0.533333.

  • variance_portefeuille_2_actifs(poids1, poids2, ecart_type1, ecart_type2, correlation)
      Variance d'un portefeuille à 2 actifs (diversification) :
          w1²·σ1² + w2²·σ2² + 2·w1·w2·ρ·σ1·σ2
      poids réels quelconques (positions longues/courtes), σ >= 0, ρ ∈ [-1, 1].
      Illustre la diversification : à ρ = -1 et risques égaux/poids égaux, la variance s'annule.

  • ecart_type_portefeuille_2_actifs(...) = sqrt(variance_portefeuille_2_actifs(...))
      Risque (écart-type) du portefeuille à 2 actifs ; mêmes garde-fous, variance toujours >= 0.

  • prime_pure(frequence, cout_moyen) = frequence · cout_moyen
      Prime pure (assurance) = fréquence des sinistres × coût moyen d'un sinistre (sévérité).
      frequence >= 0 (nombre attendu de sinistres par police/période — PAS bornée à 1), cout_moyen >= 0.
      Ex. 0.05 · 2000 = 100  ;  2 · 500 = 1000.

ABSTENTION STRUCTURELLE (faux positif INTERDIT, jamais un faux -> ValueError) :
  • probabilité hors [0, 1] -> ValueError ;
  • écart-type (risque) <= 0 là où il est dénominateur/strict (VaR, Sharpe) -> ValueError ;
  • écart-type < 0 (portefeuille), corrélation hors [-1, 1], z <= 0, montant/fréquence/coût < 0 -> ValueError ;
  • toute valeur non finie / non numérique (NaN, inf, None, str, bool) -> ValueError.

Sorties arrondies à 6 décimales. stdlib uniquement, fonctions pures déterministes.
"""

import math

__all__ = [
    "esperance_perte",
    "value_at_risk_parametrique",
    "ratio_sharpe",
    "variance_portefeuille_2_actifs",
    "ecart_type_portefeuille_2_actifs",
    "prime_pure",
]

_PRECISION = 6


def _reel_fini(x, nom):
    """Convertit en float fini, sinon ValueError (abstention). bool refusé (True/False != mesure)."""
    if isinstance(x, bool):
        raise ValueError(f"{nom} booléen (non numérique) : {x!r}")
    try:
        v = float(x)
    except (TypeError, ValueError):
        raise ValueError(f"{nom} non numérique : {x!r}")
    if not math.isfinite(v):
        raise ValueError(f"{nom} non fini : {x!r}")
    return v


def _probabilite(x, nom):
    """float fini dans [0, 1], sinon ValueError."""
    v = _reel_fini(x, nom)
    if not (0.0 <= v <= 1.0):
        raise ValueError(f"{nom} hors [0, 1] : {v}")
    return v


def _non_negatif(x, nom):
    """float fini >= 0, sinon ValueError."""
    v = _reel_fini(x, nom)
    if v < 0.0:
        raise ValueError(f"{nom} négatif : {v}")
    return v


def _strictement_positif(x, nom):
    """float fini > 0 (risque/dénominateur strict), sinon ValueError."""
    v = _reel_fini(x, nom)
    if v <= 0.0:
        raise ValueError(f"{nom} non strictement positif : {v}")
    return v


def _correlation(x, nom):
    """float fini dans [-1, 1] (coefficient de corrélation), sinon ValueError."""
    v = _reel_fini(x, nom)
    if not (-1.0 <= v <= 1.0):
        raise ValueError(f"{nom} hors [-1, 1] : {v}")
    return v


def esperance_perte(probabilite, montant):
    """
    Espérance de perte = probabilite · montant.

    probabilite ∈ [0, 1] ; montant >= 0 (perte encourue si l'événement survient).
    probabilité hors [0, 1], montant < 0, valeurs non finies -> ValueError.
    """
    p = _probabilite(probabilite, "probabilite")
    m = _non_negatif(montant, "montant")
    return round(p * m, _PRECISION)


def value_at_risk_parametrique(moyenne, ecart_type, z=1.645):
    """
    VaR paramétrique gaussienne = -(moyenne - z · ecart_type).

    moyenne : rendement/résultat attendu (réel fini quelconque).
    ecart_type : risque, > 0 (dénominateur de la standardisation gaussienne).
    z : quantile normal du seuil de confiance, > 0 (1.645 ≈ 95 %, 2.326 ≈ 99 %).
    ecart_type <= 0, z <= 0, valeurs non finies -> ValueError.
    """
    mu = _reel_fini(moyenne, "moyenne")
    sigma = _strictement_positif(ecart_type, "ecart_type")
    zz = _strictement_positif(z, "z")
    return round(-(mu - zz * sigma), _PRECISION)


def ratio_sharpe(rendement, taux_sans_risque, ecart_type):
    """
    Ratio de Sharpe = (rendement - taux_sans_risque) / ecart_type.

    ecart_type > 0 (risque, dénominateur). Le résultat peut être négatif.
    ecart_type <= 0, valeurs non finies -> ValueError.
    """
    r = _reel_fini(rendement, "rendement")
    rf = _reel_fini(taux_sans_risque, "taux_sans_risque")
    sigma = _strictement_positif(ecart_type, "ecart_type")
    return round((r - rf) / sigma, _PRECISION)


def variance_portefeuille_2_actifs(poids1, poids2, ecart_type1, ecart_type2, correlation):
    """
    Variance d'un portefeuille à 2 actifs :
        w1²·σ1² + w2²·σ2² + 2·w1·w2·ρ·σ1·σ2

    poids1, poids2 : pondérations réelles (longues > 0 / courtes < 0 admises).
    ecart_type1, ecart_type2 : écarts-types des actifs, >= 0 (0 = actif sans risque).
    correlation : ρ ∈ [-1, 1].
    σ < 0, ρ hors [-1, 1], valeurs non finies -> ValueError.
    """
    w1 = _reel_fini(poids1, "poids1")
    w2 = _reel_fini(poids2, "poids2")
    s1 = _non_negatif(ecart_type1, "ecart_type1")
    s2 = _non_negatif(ecart_type2, "ecart_type2")
    rho = _correlation(correlation, "correlation")
    var = w1 * w1 * s1 * s1 + w2 * w2 * s2 * s2 + 2.0 * w1 * w2 * rho * s1 * s2
    if var < 0.0:                       # garde numérique : la variance ne peut être < 0
        var = 0.0
    return round(var, _PRECISION)


def ecart_type_portefeuille_2_actifs(poids1, poids2, ecart_type1, ecart_type2, correlation):
    """
    Écart-type (risque) du portefeuille à 2 actifs = sqrt(variance_portefeuille_2_actifs(...)).
    Mêmes garde-fous que la variance ; la racine porte sur une variance >= 0 par construction.
    """
    var = variance_portefeuille_2_actifs(poids1, poids2, ecart_type1, ecart_type2, correlation)
    return round(math.sqrt(var), _PRECISION)


def prime_pure(frequence, cout_moyen):
    """
    Prime pure (assurance) = frequence · cout_moyen.

    frequence : nombre attendu de sinistres par police/période, >= 0 (NON bornée à 1).
    cout_moyen : coût moyen d'un sinistre (sévérité), >= 0.
    valeurs < 0 ou non finies -> ValueError.
    """
    f = _non_negatif(frequence, "frequence")
    c = _non_negatif(cout_moyen, "cout_moyen")
    return round(f * c, _PRECISION)
