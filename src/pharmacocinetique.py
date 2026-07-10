"""
PHARMACOCINÉTIQUE — modèle à UN COMPARTIMENT, élimination d'ORDRE 1 (linéaire).

Posture FAUX=0 (identique à `geometries_non_euclidiennes` / `galois`) : on n'expose QUE le calcul EXACT du
modèle mono-compartimental à cinétique du premier ordre, dont chaque relation est une IDENTITÉ mathématique,
pas une corrélation. Au moindre doute (domaine violé, type invalide, médicament à cinétique NON linéaire) ->
`ValueError` (abstention structurelle). Le faux NÉGATIF (abstenir) est toléré ; le faux POSITIF est INTERDIT.

MÉCANISME (modèle à un compartiment, entrée bolus IV sauf mention) :
  • Constante d'élimination      k  = Cl / Vd                     (h⁻¹)      — Cl clairance, Vd volume de distribution.
  • Demi-vie                     t½ = ln2 / k = 0.693·Vd/Cl        (h)        — temps pour diviser C par 2.
  • Concentration au temps t     C(t) = C0·e^(−k·t)                          — décroissance exponentielle.
                                 C(t) = (dose/Vd)·e^(−k·t)                    — depuis une dose bolus.
  • Aire sous la courbe (bolus)  ASC = dose / Cl                              — IDENTITÉ EXACTE, INDÉPENDANTE de Vd.
  • Doses répétées (τ intervalle) :
        Css,moy = F·dose / (Cl·τ)                                            — concentration moyenne à l'équilibre.
        facteur d'accumulation R = 1 / (1 − e^(−k·τ)).
        équilibre atteint à ≈ n demi-vies : fraction atteinte = 1 − 2^(−n)   (JAMAIS « 100 % » : 96,875 % à n=5).
  • Dose de charge               DC = C_cible·Vd / F.

HONNÊTETÉ / LIMITE DU MODÈLE : ces formules SUPPOSENT une élimination d'ordre 1 et un compartiment unique.
Pour une cinétique SATURABLE (Michaelis-Menten : éthanol, phénytoïne, aspirine à forte dose, ordre 0 ou mixte),
elles sont FAUSSES. `verifie_ordre_un` lève `ValueError` sur un catalogue de médicaments à cinétique saturable
connue, en le DISANT, et s'abstient (ValueError) sur tout médicament dont l'ordre n'est pas un fait établi.

GARANTIES (vérifiées en adverse par `valide_pharmacocinetique.py`) :
  - Cl ≤ 0, Vd ≤ 0, k ≤ 0, C0 ≤ 0, dose ≤ 0, C_cible ≤ 0 -> ValueError ;
  - t < 0 -> ValueError ; τ ≤ 0 -> ValueError ; biodisponibilité hors ]0, 1] -> ValueError ;
  - n (nombre de demi-vies) : entier ≥ 1 sinon ValueError ;
  - types invalides (bool, str, complexe, NaN, ±inf, mauvaise arité) -> ValueError ;
  - médicament à cinétique saturable (éthanol, phénytoïne, aspirine forte dose…) -> ValueError ;
  - déterministe, pur (aucun état, aucun aléa, aucune horloge) ; sorties flottantes ARRONDIES à 10 chiffres
    significatifs (précision honnête : les entrées sont des mesures flottantes).

Le module n'importe que `math` (stdlib). AUCUNE dépendance externe, aucun dataset.
"""
from __future__ import annotations

import math

SOURCE = "pharmacocinétique clinique — modèle mono-compartimental d'ordre 1 (Rowland & Tozer, 'Clinical Pharmacokinetics'; Gibaldi & Perrier)"

LN2 = math.log(2.0)  # 0.6931471805599453 : constante mathématique exacte

_CHIFFRES_SIGNIFICATIFS = 10


def _sig(x: float, n: int = _CHIFFRES_SIGNIFICATIFS) -> float:
    """Arrondit à n chiffres significatifs (précision honnête, indépendante de la magnitude)."""
    if x == 0:
        return 0.0
    return float(f"{x:.{n}g}")


def _est_reel(x) -> bool:
    """True ssi x est un réel fini (bool REFUSÉS : True n'est pas 1 ; NaN/inf REFUSÉS)."""
    return isinstance(x, (int, float)) and not isinstance(x, bool) and math.isfinite(x)


def _exige_positif(x, nom: str) -> float:
    """Grandeur physique strictement positive (clairance, volume, dose, concentration, k)."""
    if not _est_reel(x) or x <= 0:
        raise ValueError(f"{nom} invalide : un réel strictement positif est requis")
    return float(x)


def _exige_temps(t) -> float:
    """Temps écoulé : réel ≥ 0 (t=0 admis, t<0 interdit)."""
    if not _est_reel(t) or t < 0:
        raise ValueError("temps t invalide : un réel ≥ 0 est requis")
    return float(t)


def _exige_intervalle(tau) -> float:
    """Intervalle posologique τ : réel strictement positif (tau ≤ 0 interdit)."""
    if not _est_reel(tau) or tau <= 0:
        raise ValueError("intervalle τ invalide : un réel strictement positif est requis")
    return float(tau)


def _exige_biodisponibilite(F) -> float:
    """Biodisponibilité F ∈ ]0, 1] (0 exclu, 1 = IV total ; hors bornes interdit)."""
    if not _est_reel(F) or not (0.0 < F <= 1.0):
        raise ValueError("biodisponibilité invalide : un réel dans l'intervalle ]0, 1] est requis")
    return float(F)


def _exige_entier(n, mini: int) -> int:
    if not isinstance(n, int) or isinstance(n, bool):
        raise ValueError(f"entier ≥ {mini} attendu, reçu {n!r}")
    if n < mini:
        raise ValueError(f"entier ≥ {mini} attendu, reçu {n}")
    return n


# ── (a) CONSTANTE D'ÉLIMINATION & DEMI-VIE ────────────────────────────────────────────────────────────────────────
def constante_elimination(clairance: float, volume_distribution: float) -> float:
    """Constante d'élimination d'ordre 1 : k = Cl / Vd (h⁻¹). Cl ≤ 0 ou Vd ≤ 0 -> ValueError."""
    cl = _exige_positif(clairance, "clairance Cl")
    vd = _exige_positif(volume_distribution, "volume de distribution Vd")
    return _sig(cl / vd)


def demi_vie(k: float) -> float:
    """Demi-vie t½ = ln2 / k (h). k ≤ 0 -> ValueError."""
    k = _exige_positif(k, "constante d'élimination k")
    return _sig(LN2 / k)


def demi_vie_depuis(clairance: float, volume_distribution: float) -> float:
    """Demi-vie depuis Cl et Vd : t½ = ln2·Vd/Cl (identité ln2/k avec k=Cl/Vd). Cl,Vd ≤ 0 -> ValueError."""
    cl = _exige_positif(clairance, "clairance Cl")
    vd = _exige_positif(volume_distribution, "volume de distribution Vd")
    return _sig(LN2 * vd / cl)


# ── (b) CONCENTRATION AU COURS DU TEMPS ───────────────────────────────────────────────────────────────────────────
def concentration(C0: float, k: float, t: float) -> float:
    """Concentration à l'instant t : C(t) = C0·e^(−k·t). C0 ≤ 0 ou k ≤ 0 -> ValueError ; t < 0 -> ValueError."""
    C0 = _exige_positif(C0, "concentration initiale C0")
    k = _exige_positif(k, "constante d'élimination k")
    t = _exige_temps(t)
    return _sig(C0 * math.exp(-k * t))


def concentration_apres_dose(dose: float, Vd: float, k: float, t: float) -> float:
    """Concentration après une dose bolus IV : C(t) = (dose/Vd)·e^(−k·t). dose,Vd,k ≤ 0 -> ValueError ; t<0 idem."""
    dose = _exige_positif(dose, "dose")
    vd = _exige_positif(Vd, "volume de distribution Vd")
    k = _exige_positif(k, "constante d'élimination k")
    t = _exige_temps(t)
    return _sig((dose / vd) * math.exp(-k * t))


# ── (c) AIRE SOUS LA COURBE (bolus IV) ────────────────────────────────────────────────────────────────────────────
def aire_sous_courbe(dose: float, clairance: float) -> float:
    """ASC d'un bolus IV : ASC = dose / Cl (mg·h/L).

    IDENTITÉ EXACTE, INDÉPENDANTE de Vd : l'intégrale de C0·e^(−kt) vaut C0/k = (dose/Vd)/(Cl/Vd) = dose/Cl.
    dose ≤ 0 ou Cl ≤ 0 -> ValueError."""
    dose = _exige_positif(dose, "dose")
    cl = _exige_positif(clairance, "clairance Cl")
    return _sig(dose / cl)


# ── (d) DOSES RÉPÉTÉES ────────────────────────────────────────────────────────────────────────────────────────────
def concentration_equilibre_moyenne(dose: float, tau: float, clairance: float,
                                     biodisponibilite: float = 1.0) -> float:
    """Concentration moyenne à l'équilibre : Css,moy = F·dose / (Cl·τ) (mg/L).

    dose ≤ 0, Cl ≤ 0 -> ValueError ; τ ≤ 0 -> ValueError ; F hors ]0,1] -> ValueError."""
    dose = _exige_positif(dose, "dose")
    tau = _exige_intervalle(tau)
    cl = _exige_positif(clairance, "clairance Cl")
    F = _exige_biodisponibilite(biodisponibilite)
    return _sig(F * dose / (cl * tau))


def facteur_accumulation(k: float, tau: float) -> float:
    """Facteur d'accumulation à l'équilibre : R = 1 / (1 − e^(−k·τ)). k ≤ 0 -> ValueError ; τ ≤ 0 -> ValueError."""
    k = _exige_positif(k, "constante d'élimination k")
    tau = _exige_intervalle(tau)
    return _sig(1.0 / (1.0 - math.exp(-k * tau)))


def temps_pour_equilibre(demi_vie_h: float, n_demi_vies: int = 5):
    """Temps d'approche de l'équilibre et fraction RÉELLEMENT atteinte après n demi-vies.

    Renvoie le triplet (temps = n·t½, n_demi_vies, fraction = 1 − 2^(−n)). La fraction est la valeur EXACTE :
    à n=5 demi-vies on atteint 1 − 2^(−5) = 0.96875 (96,875 %), JAMAIS « 100 % ». t½ ≤ 0 ou n < 1 -> ValueError."""
    th = _exige_positif(demi_vie_h, "demi-vie t½")
    n = _exige_entier(n_demi_vies, 1)
    fraction = 1.0 - 2.0 ** (-n)
    return (_sig(n * th), n, _sig(fraction))


# ── (e) DOSE DE CHARGE ────────────────────────────────────────────────────────────────────────────────────────────
def dose_de_charge(concentration_cible: float, Vd: float, biodisponibilite: float = 1.0) -> float:
    """Dose de charge pour atteindre d'emblée C_cible : DC = C_cible·Vd / F.

    C_cible ≤ 0 ou Vd ≤ 0 -> ValueError ; F hors ]0,1] -> ValueError."""
    c = _exige_positif(concentration_cible, "concentration cible")
    vd = _exige_positif(Vd, "volume de distribution Vd")
    F = _exige_biodisponibilite(biodisponibilite)
    return _sig(c * vd / F)


# ── (f) HONNÊTETÉ : la cinétique d'ordre 1 n'est PAS universelle ──────────────────────────────────────────────────
# Médicaments dont la cinétique est SATURABLE (Michaelis-Menten) aux concentrations usuelles/toxiques : le modèle
# linéaire d'ordre 1 est FAUX pour eux (élimination d'ordre 0 ou mixte). Faits pharmacologiques classiques.
_SATURABLES = {
    "ethanol": "éthanol : élimination d'ordre 0 (alcool déshydrogénase saturée) — taux ~constant, pas exponentiel",
    "alcool": "éthanol : élimination d'ordre 0 (alcool déshydrogénase saturée) — taux ~constant, pas exponentiel",
    "phenytoine": "phénytoïne : cinétique de Michaelis-Menten (saturation dose-dépendante) — t½ non constante",
    "aspirine": "aspirine/salicylate à forte dose : métabolisme saturable (ordre mixte 0/1)",
    "salicylate": "salicylate à forte dose : métabolisme saturable (ordre mixte 0/1)",
    "theophylline": "théophylline : cinétique non linéaire aux concentrations thérapeutiques hautes",
}
# Médicaments dont la cinétique d'ordre 1 (linéaire) est un fait établi aux doses thérapeutiques usuelles.
_ORDRE_UN = {
    "gentamicine",
    "amoxicilline",
    "digoxine",
    "vancomycine",
    "penicilline",
}


def _norm_medicament(m: str) -> str:
    if not isinstance(m, str):
        raise ValueError(f"nom de médicament (chaîne) attendu, reçu {m!r}")
    s = m.strip().lower()
    # dé-accentuation minimale des voyelles françaises fréquentes (é/è/ë -> e, etc.)
    table = str.maketrans("áàâäéèêëíìîïóòôöúùûüç", "aaaaeeeeiiiioooouuuuc")
    return s.translate(table)


def verifie_ordre_un(medicament: str) -> bool:
    """Garde d'HONNÊTETÉ : le modèle d'ordre 1 est-il applicable à ce médicament ?

    - Médicament à cinétique SATURABLE connue (éthanol, phénytoïne, aspirine forte dose…) -> ValueError explicite :
      appliquer ce modèle serait un FAUX POSITIF.
    - Médicament dont l'ordre 1 est un fait établi -> True.
    - Médicament inconnu -> ValueError (abstention : on ne DEVINE pas l'ordre cinétique).
    """
    cle = _norm_medicament(medicament)
    if cle in _SATURABLES:
        raise ValueError(
            f"cinétique NON d'ordre 1 (modèle inapplicable) : {_SATURABLES[cle]}")
    if cle in _ORDRE_UN:
        return True
    raise ValueError(
        f"ordre cinétique inconnu pour {medicament!r} (abstention : non catalogué comme ordre 1 établi)")


def catalogue_saturables() -> tuple:
    """Liste triée des clés de médicaments à cinétique saturable connue (le modèle NE s'applique PAS)."""
    return tuple(sorted(set(_SATURABLES)))
