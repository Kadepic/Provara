"""
POLYMÈRES BORNÉ — grandeurs CALCULABLES par formule exacte (mandat Yohan : couvrir le borné, bloc « FORMULE »).

Même posture que `physique` / `chimie` (la réalité juge, jamais un faux) :
  • Le MÉCANISME (la relation entre masses molaires, degré de polymérisation, conversion, dispersité) est EXACT —
    ce sont des définitions, pas des modèles approchés.
  • La sortie est ARRONDIE à 10 chiffres significatifs (précision HONNÊTE : on supprime le bruit flottant sans
    prétendre à une exactitude au-delà des données fournies).
  • ABSTENTION STRUCTURELLE : toute entrée hors domaine physique (masse molaire ≤ 0, degré < 1, Mw < Mn,
    conversion ∉ [0,1[) lève ValueError. Conservateur : faux négatif (abstention) toléré, faux POSITIF interdit.

DÉFINITIONS COUVERTES (toutes exactes, sans constante mesurée) :
  - degre_polymerisation(Mn, M0)            = Mn / M0          (degré de polymérisation moyen en nombre, DP ≥ 1)
  - masse_molaire_polymere(DP, M0)          = DP · M0          (réciproque : masse molaire du polymère)
  - masse_molaire_monomere(Mn, DP)          = Mn / DP          (réciproque : masse molaire de l'unité monomère)
  - indice_polymolecularite(Mw, Mn)         = Mw / Mn ≥ 1      (dispersité Đ / PDI ; 1 = monodisperse)
  - degre_polymerisation_carothers(p)       = 1 / (1 − p)      (équation de Carothers, polycondensation, 0 ≤ p < 1)
  - taux_conversion(DP)                     = 1 − 1/DP         (réciproque de Carothers : conversion pour atteindre DP)

EXEMPLES BORNÉS (vérifiés en adverse par `valide_polymeres.py`) :
  - Polyéthylène : motif C2H4, M0 = 28 g/mol ; Mn = 28000 → DP = 1000.
  - PET : motif éthylène-téréphtalate C10H8O4, M0 = 192.17 g/mol ; Mn = 19217 → DP = 100.
  - Polystyrène : motif styrène C8H8, M0 = 104.15 g/mol ; Mn = 104150 → DP = 1000.
  - Distribution la plus probable (polycondensation à haute conversion) : Đ = Mw/Mn → 2.
  - Carothers : p = 0.99 → DP = 100 ; p = 0.999 → DP = 1000.
"""
from __future__ import annotations

_CHIFFRES_SIGNIFICATIFS = 10


def _arr(x: float, n: int = _CHIFFRES_SIGNIFICATIFS) -> float:
    """Arrondit à n chiffres significatifs (précision honnête, indépendante de la magnitude)."""
    if x == 0:
        return 0.0
    return float(f"{x:.{n}g}")


def _nb(*xs) -> bool:
    """Vrai ssi tous les arguments sont des nombres réels (pas un bool, pas un complexe, pas NaN/inf)."""
    for x in xs:
        if isinstance(x, bool) or not isinstance(x, (int, float)):
            return False
        if x != x or x in (float("inf"), float("-inf")):
            return False
    return True


def _pos(*xs) -> bool:
    """Vrai ssi tous les arguments sont des nombres réels strictement positifs."""
    return _nb(*xs) and all(x > 0 for x in xs)


def degre_polymerisation(masse_molaire_polymere: float, masse_molaire_monomere: float) -> float:
    """Degré de polymérisation moyen DP = Mn / M0. Masses > 0 et DP ≥ 1, sinon ValueError."""
    if not _pos(masse_molaire_polymere, masse_molaire_monomere):
        raise ValueError("masses molaires strictement positives requises")
    dp = masse_molaire_polymere / masse_molaire_monomere
    if dp < 1:
        raise ValueError("DP < 1 : la masse du polymère est inférieure à celle du monomère (impossible)")
    return _arr(dp)


def masse_molaire_polymere(degre_polymerisation: float, masse_molaire_monomere: float) -> float:
    """Masse molaire du polymère Mn = DP · M0. M0 > 0 et DP ≥ 1, sinon ValueError."""
    if not _pos(masse_molaire_monomere):
        raise ValueError("masse molaire du monomère strictement positive requise")
    if not _nb(degre_polymerisation) or degre_polymerisation < 1:
        raise ValueError("degré de polymérisation ≥ 1 requis")
    return _arr(degre_polymerisation * masse_molaire_monomere)


def masse_molaire_monomere(masse_molaire_polymere: float, degre_polymerisation: float) -> float:
    """Masse molaire de l'unité monomère M0 = Mn / DP. Mn > 0 et DP ≥ 1, sinon ValueError."""
    if not _pos(masse_molaire_polymere):
        raise ValueError("masse molaire du polymère strictement positive requise")
    if not _nb(degre_polymerisation) or degre_polymerisation < 1:
        raise ValueError("degré de polymérisation ≥ 1 requis")
    return _arr(masse_molaire_polymere / degre_polymerisation)


def indice_polymolecularite(masse_molaire_masse: float, masse_molaire_nombre: float) -> float:
    """Indice de polymolécularité (dispersité Đ / PDI) = Mw / Mn ≥ 1. Masses > 0 et Mw ≥ Mn, sinon ValueError."""
    if not _pos(masse_molaire_masse, masse_molaire_nombre):
        raise ValueError("masses molaires strictement positives requises")
    if masse_molaire_masse < masse_molaire_nombre:
        raise ValueError("Mw < Mn : la dispersité ne peut être < 1 (Mw ≥ Mn par définition)")
    return _arr(masse_molaire_masse / masse_molaire_nombre)


def degre_polymerisation_carothers(conversion: float) -> float:
    """Équation de Carothers : DP = 1 / (1 − p) pour une polycondensation. Conversion p ∈ [0, 1[, sinon ValueError."""
    if not _nb(conversion):
        raise ValueError("conversion numérique requise")
    if conversion < 0 or conversion >= 1:
        raise ValueError("conversion hors [0, 1[ : DP diverge ou est non physique")
    return _arr(1.0 / (1.0 - conversion))


def taux_conversion(degre_polymerisation: float) -> float:
    """Réciproque de Carothers : conversion p = 1 − 1/DP nécessaire pour atteindre le degré DP. DP ≥ 1, sinon ValueError."""
    if not _nb(degre_polymerisation) or degre_polymerisation < 1:
        raise ValueError("degré de polymérisation ≥ 1 requis")
    return _arr(1.0 - 1.0 / degre_polymerisation)
