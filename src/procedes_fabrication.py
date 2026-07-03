"""
PROCÉDÉS DE FABRICATION — classification CONVENTIONNELLE + rendement matière (mandat Yohan : couvrir le borné,
sujet « Procédés de fabrication »). FAUX=0 ABSOLU.

Posture (la réalité/convention juge, jamais un faux) :
  • La CLASSIFICATION des procédés par familles (soustractif / additif / formage / assemblage) est une
    CONVENTION D'INGÉNIERIE établie — c'est un fait SOURCÉ et CERTAIN, pas une opinion. Le référentiel est
    un ENSEMBLE FERMÉ : tout procédé hors du référentiel connu -> ValueError (abstention), JAMAIS une
    classe inventée.
  • Le RENDEMENT MATIÈRE est une définition EXACTE : masse_finale / masse_initiale, borné [0, 1]. Le mécanisme
    (la division) est garanti ; un rendement > 1 est physiquement IMPOSSIBLE (création de matière) -> ValueError.

GARANTIES (vérifiées en adverse par `valide_procedes_fabrication.py`) :
  - procédé INCONNU -> ValueError : jamais une famille devinée ;
  - masse <= 0, non finie, ou booléenne -> ValueError : on ne calcule pas sur une entrée absurde ;
  - masse_finale > masse_initiale (rendement > 1, matière créée) -> ValueError ;
  - déterministe ; conservateur (abstention tolérée, faux POSITIF interdit).
"""
from __future__ import annotations

import math
import unicodedata

# ── FAMILLES DE PROCÉDÉS (convention d'ingénierie) ──────────────────────────────────────────────────────────────
SOUSTRACTIF = "soustractif"   # enlèvement de matière (usinage)
ADDITIF = "additif"           # ajout de matière couche par couche
FORMAGE = "formage"           # mise en forme par déformation / solidification, sans enlèvement
ASSEMBLAGE = "assemblage"     # réunion de plusieurs pièces

# Référentiel FERMÉ : clé normalisée -> famille. Hors de ce dictionnaire -> abstention (ValueError).
_FAMILLE = {
    # soustractif (usinage par enlèvement de copeaux)
    "fraisage": SOUSTRACTIF,
    "tournage": SOUSTRACTIF,
    "percage": SOUSTRACTIF,        # « perçage »
    # additif (fabrication additive)
    "impression_3d": ADDITIF,
    "frittage": ADDITIF,
    # formage (déformation plastique / solidification, conservation de la matière)
    "moulage": FORMAGE,
    "forgeage": FORMAGE,
    "estampage": FORMAGE,
    # assemblage (réunion de pièces)
    "soudage": ASSEMBLAGE,
    "collage": ASSEMBLAGE,
}


def _normalise(nom: str) -> str:
    """Normalise un libellé de procédé : minuscules, sans accents, séparateurs -> '_'. Pur, déterministe."""
    if not isinstance(nom, str):
        raise ValueError(f"procédé non textuel : {type(nom).__name__}")
    s = nom.strip().lower()
    if not s:
        raise ValueError("procédé vide")
    # retire les accents (perçage -> percage)
    s = unicodedata.normalize("NFKD", s)
    s = "".join(c for c in s if not unicodedata.combining(c))
    # uniformise les séparateurs (espace, tiret -> underscore) et compacte les répétitions
    out = []
    prev_us = False
    for c in s:
        if c in " -_\t":
            if not prev_us:
                out.append("_")
                prev_us = True
        else:
            out.append(c)
            prev_us = False
    return "".join(out).strip("_")


def type_procede(nom: str) -> str:
    """Famille d'un procédé de fabrication (convention d'ingénierie).

    'fraisage/tournage/perçage' -> soustractif ; 'impression_3d/frittage' -> additif ;
    'moulage/forgeage/estampage' -> formage ; 'soudage/collage' -> assemblage.
    Procédé hors du référentiel connu -> ValueError (abstention, jamais une classe inventée).
    """
    cle = _normalise(nom)
    if cle not in _FAMILLE:
        raise ValueError(f"procédé inconnu (hors référentiel) : {nom!r}")
    return _FAMILLE[cle]


def _verifie_masse(x, label: str) -> float:
    if isinstance(x, bool):
        raise ValueError(f"{label} booléenne")
    if not isinstance(x, (int, float)):
        raise ValueError(f"{label} non numérique : {type(x).__name__}")
    v = float(x)
    if not math.isfinite(v):
        raise ValueError(f"{label} non finie")
    if v <= 0.0:
        raise ValueError(f"{label} <= 0 : {v}")
    return v


def rendement_matiere(masse_finale, masse_initiale) -> float:
    """Rendement matière = masse_finale / masse_initiale, borné [0, 1].

    Un procédé SOUSTRACTIF perd de la matière (rendement < 1) ; un procédé ADDITIF la conserve (≈ 1).
    Masses <= 0 / non finies / booléennes -> ValueError. masse_finale > masse_initiale (rendement > 1,
    création de matière) -> ValueError.
    """
    mf = _verifie_masse(masse_finale, "masse_finale")
    mi = _verifie_masse(masse_initiale, "masse_initiale")
    r = mf / mi
    if r > 1.0:
        raise ValueError(f"rendement > 1 (matière créée) : {r}")
    return r
