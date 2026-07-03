"""
CARDIOLOGIE QUANTITATIVE — formules cliniques ÉTABLIES (mandat Yohan : capacité bornée FAUX=0).

Posture (la réalité juge, jamais un faux) :
  • Le MÉCANISME (la formule clinique) est EXACT — fréquence maximale 220−âge, QTc de Bazett,
    fraction d'éjection VE/VTD·100, seuils de fréquence au repos. Ce sont des définitions / formules
    CONSENSUELLES de la cardiologie clinique, pas des estimations inventées.
  • La SOUNDNESS bloque tout domaine physiologiquement absurde (âge hors [0,120], intervalle RR ≤ 0,
    volumes ≤ 0, fréquence ≤ 0) par ValueError — jamais un nombre faux.
  • Déterministe, fonctions pures.

Conventions : sortie en flottant ; QTc rendu en ms (QT en ms, RR en s) ; FE en pourcentage.
"""
from __future__ import annotations

import math

# ── Bornes physiologiques de soundness ─────────────────────────────────────────────────────────────────────────
_AGE_MIN = 0
_AGE_MAX = 120

# Seuils de fréquence cardiaque au repos (battements/min) — consensus clinique.
_FC_BRADY = 60     # < 60 : bradycardie
_FC_TACHY = 100    # > 100 : tachycardie ; [60, 100] : normal

BRADYCARDIE = "bradycardie"
NORMAL = "normal"
TACHYCARDIE = "tachycardie"


def _nombre(x) -> bool:
    """True si x est un réel utilisable (exclut bool, qui est un int en Python)."""
    return isinstance(x, (int, float)) and not isinstance(x, bool)


def frequence_cardiaque_max(age) -> float:
    """Fréquence cardiaque maximale théorique = 220 − âge (battements/min).

    Soundness : âge hors [0, 120] (ou non numérique) -> ValueError.
    """
    if not _nombre(age):
        raise ValueError("age doit être un nombre")
    if age < _AGE_MIN or age > _AGE_MAX:
        raise ValueError(f"age hors domaine [{_AGE_MIN}, {_AGE_MAX}] : {age!r}")
    return 220.0 - float(age)


def qt_corrige_bazett(qt_ms, intervalle_rr_s) -> float:
    """QT corrigé par la formule de Bazett : QTc = QT / sqrt(RR).

    QT en millisecondes, RR (intervalle R-R) en secondes ; QTc rendu en millisecondes.
    Soundness : RR ≤ 0 (ou non numérique), QT ≤ 0 (ou non numérique) -> ValueError.
    """
    if not _nombre(qt_ms):
        raise ValueError("qt_ms doit être un nombre")
    if not _nombre(intervalle_rr_s):
        raise ValueError("intervalle_rr_s doit être un nombre")
    if intervalle_rr_s <= 0:
        raise ValueError(f"intervalle RR doit être > 0 s : {intervalle_rr_s!r}")
    if qt_ms <= 0:
        raise ValueError(f"QT doit être > 0 ms : {qt_ms!r}")
    return float(qt_ms) / math.sqrt(float(intervalle_rr_s))


def fraction_ejection(volume_ejecte, volume_telediastolique) -> float:
    """Fraction d'éjection (%) = volume éjecté / volume télédiastolique · 100 (normale 50-70 %).

    Soundness : volumes ≤ 0 (ou non numériques) -> ValueError.
    """
    if not _nombre(volume_ejecte):
        raise ValueError("volume_ejecte doit être un nombre")
    if not _nombre(volume_telediastolique):
        raise ValueError("volume_telediastolique doit être un nombre")
    if volume_ejecte <= 0:
        raise ValueError(f"volume éjecté doit être > 0 : {volume_ejecte!r}")
    if volume_telediastolique <= 0:
        raise ValueError(f"volume télédiastolique doit être > 0 : {volume_telediastolique!r}")
    return float(volume_ejecte) / float(volume_telediastolique) * 100.0


def classe_fc_repos(fc) -> str:
    """Classe la fréquence cardiaque au repos : <60 bradycardie, 60-100 normal, >100 tachycardie.

    Soundness : fréquence ≤ 0 (ou non numérique) -> ValueError.
    """
    if not _nombre(fc):
        raise ValueError("fc doit être un nombre")
    if fc <= 0:
        raise ValueError(f"fréquence cardiaque doit être > 0 : {fc!r}")
    if fc < _FC_BRADY:
        return BRADYCARDIE
    if fc > _FC_TACHY:
        return TACHYCARDIE
    return NORMAL
