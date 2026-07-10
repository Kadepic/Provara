"""
DATATION RADIOCARBONE — le problème INVERSE de la décroissance radioactive (archéologie : dater un site).

`physique` calcule la décroissance DIRECTE N(t) depuis N0. Ici on résout l'INVERSE : connaissant la fraction
d'isotope restante, retrouver l'ÂGE. Même posture FAUX=0 (la physique/le théorème juge, jamais un faux) :

  • MÉCANISME EXACT (loi de décroissance exponentielle N(t) = N0·(1/2)^(t/T)) inversé :
      – âge « réel » avec une demi-vie T :   t = T · log2(1/f)      [exact au sens de la loi]
      – ÂGE RADIOCARBONE CONVENTIONNEL (BP) : t = −8033 · ln(f)      [convention de Libby]
        La constante 8033 = 5568 / ln(2) est la vie moyenne associée à la demi-vie de LIBBY (5568 ans).
        C'est la convention des âges radiocarbone PUBLIÉS (Stuiver & Polach 1977), volontairement figée
        même après la révision de la demi-vie — d'où l'écart avec la vraie demi-vie de Cambridge (5730 ans).
      – fraction restante f(t, T) = (1/2)^(t/T)  — l'inverse, pour la BOUCLE FERMÉE.

  • DEUX demi-vies du carbone 14 exposées, et le module DIT laquelle il applique :
      – CAMBRIDGE (Godwin 1962) : 5730 ± 40 ans — la valeur PHYSIQUE réelle (utilisée par age_reel_demi_vie) ;
      – LIBBY (1949) : 5568 ans — la CONVENTION des âges BP publiés (utilisée par age_radiocarbone).

  • L'ABSTENTION LA PLUS IMPORTANTE — la CALIBRATION : l'âge radiocarbone BP n'est PAS un âge CALENDAIRE.
    Le 14C atmosphérique a varié au cours du temps ; convertir un âge BP en date calendaire exige une courbe
    de calibration (IntCal). Cette courbe n'est PAS embarquée : calibration_disponible() -> False et
    age_calendaire(...) lève TOUJOURS ValueError. On refuse plutôt que de rendre une fausse date calendaire.

GARANTIES (vérifiées en adverse par `valide_datation_radiocarbone.py`) :
  - f ≤ 0 ou f > 1 -> ValueError (une fraction restante est dans ]0, 1]) ;
  - demi-vie ≤ 0 -> ValueError ;
  - LIMITE physique ENFORCÉE : au-delà de ~50 000 ans l'âge radiocarbone est hors portée (fraction sous le
    seuil de mesure) -> age_radiocarbone lève ValueError (utiliser K-Ar ou U-Pb) ;
  - age_calendaire -> ValueError TOUJOURS (courbe IntCal non embarquée) ;
  - types invalides (bool, str, NaN, ±inf, mauvaise arité) -> ValueError ;
  - sortie flottante ARRONDIE à 10 chiffres significatifs (précision honnête) ;
  - déterministe ; conservateur (faux négatif/abstention toléré, faux POSITIF interdit).

Toutes les fonctions sont PURES et déterministes ; le module n'importe que `math` (stdlib).
"""
from __future__ import annotations

import math

SOURCE = ("demi-vies : 14C = 5730±40 ans (Godwin 1962, Cambridge) & 5568 ans (convention Libby 1949) ; "
          "K-Ar T½ = 1.248e9 ans, U-238 T½ = 4.468e9 ans ; "
          "âge BP conventionnel −8033·ln(f) (Stuiver & Polach 1977) ; calibration IntCal non embarquée")

_CHIFFRES_SIGNIFICATIFS = 10

# ── DEMI-VIES SOURCÉES (années) ──────────────────────────────────────────────────────────────────────────────────
DEMI_VIE_C14_CAMBRIDGE = 5730.0        # ans — Godwin 1962 (valeur PHYSIQUE réelle, ± 40 ans)
DEMI_VIE_C14_LIBBY = 5568.0            # ans — Libby 1949 (CONVENTION des âges BP publiés)
DEMI_VIE_K_AR = 1.248e9               # ans — potassium-40 -> argon-40
DEMI_VIE_U238 = 4.468e9              # ans — uranium-238

# Vie moyenne τ de la convention Libby : τ = T_Libby / ln(2) = 5568 / 0.693147... ≈ 8033 ans.
# L'âge BP conventionnel est −τ·ln(f) ; on FIGE 8033 (convention publiée), sans le recalculer.
LIBBY_TAU = 8033.0                    # ans — vie moyenne conventionnelle (âge BP = −8033·ln f)

# Portée pratique du radiocarbone : au-delà de ~50 000 ans, f est sous le seuil de mesure.
PORTEE_MAX_ANS = 50_000.0


def _sig(x: float, n: int = _CHIFFRES_SIGNIFICATIFS) -> float:
    """Arrondit à n chiffres significatifs (précision honnête, indépendante de la magnitude)."""
    if x == 0:
        return 0.0
    return float(f"{x:.{n}g}")


def _est_reel(x) -> bool:
    """True ssi x est un réel fini (les bool sont REFUSÉS : True n'est pas une mesure)."""
    return isinstance(x, (int, float)) and not isinstance(x, bool) and math.isfinite(x)


def _exige_fraction(f) -> float:
    """Fraction restante : réel dans ]0, 1]. f ≤ 0 ou f > 1 -> ValueError (jamais une fraction absurde)."""
    if not _est_reel(f) or not (0.0 < f <= 1.0):
        raise ValueError("fraction restante invalide : un réel dans ]0, 1] est requis")
    return float(f)


def _exige_demi_vie(T) -> float:
    if not _est_reel(T) or T <= 0.0:
        raise ValueError("demi-vie invalide : un réel strictement positif est requis")
    return float(T)


def _exige_age(t) -> float:
    if not _est_reel(t) or t < 0.0:
        raise ValueError("âge invalide : un réel ≥ 0 est requis")
    return float(t)


# ── ÂGE RADIOCARBONE CONVENTIONNEL (BP, convention de Libby) ─────────────────────────────────────────────────────
def age_radiocarbone(fraction_c14_restante: float) -> float:
    """Âge radiocarbone conventionnel BP : t = −8033·ln(f)  (convention de Libby, τ = 5568/ln2).

    C'est l'âge PUBLIÉ (« Before Present »), PAS un âge calendaire (voir age_calendaire / calibration).
    f ≤ 0 ou f > 1 -> ValueError. Au-delà de ~50 000 ans -> ValueError (hors portée du radiocarbone)."""
    f = _exige_fraction(fraction_c14_restante)
    age = -LIBBY_TAU * math.log(f)
    if age > PORTEE_MAX_ANS:
        raise ValueError("hors portée du radiocarbone : au-delà de ~50 000 ans, utiliser K-Ar ou U-Pb")
    return _sig(age)


# ── ÂGE « RÉEL » AVEC UNE DEMI-VIE DONNÉE ────────────────────────────────────────────────────────────────────────
def age_reel_demi_vie(fraction_restante: float, demi_vie: float) -> float:
    """Âge selon la loi de décroissance : t = T · log2(1/f)  (T = demi-vie, exact au sens de la loi).

    Générique (14C Cambridge, K-Ar, U-238…). f dans ]0, 1] ; demi_vie > 0. Sinon -> ValueError."""
    f = _exige_fraction(fraction_restante)
    T = _exige_demi_vie(demi_vie)
    age = T * math.log2(1.0 / f)
    return _sig(age)


# ── FRACTION RESTANTE (inverse, pour la BOUCLE FERMÉE) ───────────────────────────────────────────────────────────
def fraction_restante(age: float, demi_vie: float) -> float:
    """Fraction restante f = (1/2)^(age/T) — l'inverse de age_reel_demi_vie (boucle fermée).

    age ≥ 0 ; demi_vie > 0. Sinon -> ValueError."""
    t = _exige_age(age)
    T = _exige_demi_vie(demi_vie)
    f = math.pow(0.5, t / T)
    return _sig(f)


# ── CALIBRATION (abstention structurelle — la plus importante) ───────────────────────────────────────────────────
def calibration_disponible() -> bool:
    """False : la courbe de calibration IntCal n'est PAS embarquée dans ce module."""
    return False


def age_calendaire(age_bp: float) -> float:
    """Convertit un âge BP en âge CALENDAIRE — ABSTENTION STRUCTURELLE : lève TOUJOURS ValueError.

    L'âge radiocarbone BP n'est PAS un âge calendaire : le 14C atmosphérique a varié, une courbe de
    calibration (IntCal) est indispensable. Elle n'est pas embarquée -> on refuse plutôt que de mentir."""
    raise ValueError("courbe IntCal non embarquée : l'âge BP n'est pas un âge calendaire (calibration requise)")
