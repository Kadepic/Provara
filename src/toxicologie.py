"""
toxicologie.py — Dose-réponse, index thérapeutique et classes de toxicité (DL50).

Mécanismes EXACTS / définitions établies (toxicologie / pharmacologie classique) :

  • index_therapeutique(DL50, DE50) = DL50 / DE50
      Index thérapeutique (marge de sécurité). DL50 = dose létale médiane (tue 50 % de
      la population), DE50 = dose efficace médiane (effet recherché chez 50 %). Rapport
      sans dimension (mêmes unités au numérateur/dénominateur).
      IT > 1 = marge de sécurité (la dose mortelle dépasse la dose efficace) ;
      IT élevé = médicament « sûr », IT proche de 1 = fenêtre thérapeutique étroite.
      Référence : pharmacologie (Goodman & Gilman ; définition standard TI = LD50/ED50).

  • dose_totale(dose_par_kg, masse_kg) = dose_par_kg * masse_kg
      Dose totale administrée pour un dosage pondéral (mg/kg) et une masse corporelle (kg).
      Ex. 10 mg/kg chez un adulte de 70 kg = 700 mg. Arithmétique exacte.

  • marge_securite(DL1, DE99) = DL1 / DE99
      Marge de sécurité « certaine » (certain safety factor). DL1 = dose létale pour 1 %,
      DE99 = dose efficace pour 99 %. Critère plus strict que l'IT : rapporte la plus
      petite dose dangereuse à la plus grande dose nécessaire. > 1 = pas de recouvrement
      entre fin d'efficacité et début de létalité.

  • classe_toxicite_dl50(dl50_mg_kg) : classe de toxicité selon la DL50 orale (mg/kg),
      échelle de notation de toxicité établie (Hodge & Sterner / Gosselin) :
        dl50 < 5            -> 'extrêmement toxique'
        5    <= dl50 < 50   -> 'très toxique'
        50   <= dl50 < 500  -> 'toxique'
        500  <= dl50 < 5000 -> 'modérément'
        dl50 >= 5000        -> 'peu toxique'
      Convention : borne inférieure incluse, supérieure exclue (les valeurs charnières
      5, 50, 500, 5000 vont à la classe MOINS toxique). DL50 plus faible = plus toxique.

ABSTENTION STRUCTURELLE (faux positif INTERDIT, jamais un faux -> ValueError) :
  • dénominateurs de dose efficace (DE50, DE99) <= 0, ou non finis -> ValueError.
  • doses (DL50, DL1, dose_par_kg, dl50_mg_kg) < 0, ou non finies -> ValueError.
  • masse_kg <= 0, ou non finie -> ValueError.
  • toute entrée non numérique ou non finie (NaN, inf) -> ValueError.

stdlib uniquement, fonctions pures déterministes, sorties numériques arrondies à 6 décimales.
"""

import math

__all__ = [
    "index_therapeutique",
    "dose_totale",
    "marge_securite",
    "classe_toxicite_dl50",
    "EXTREMEMENT_TOXIQUE",
    "TRES_TOXIQUE",
    "TOXIQUE",
    "MODEREMENT",
    "PEU_TOXIQUE",
]

# ── Libellés de classe (échelle établie) ──
EXTREMEMENT_TOXIQUE = "extrêmement toxique"
TRES_TOXIQUE = "très toxique"
TOXIQUE = "toxique"
MODEREMENT = "modérément"
PEU_TOXIQUE = "peu toxique"

# Bornes de l'échelle DL50 orale (mg/kg).
_SEUIL_EXTREME = 5.0
_SEUIL_TRES = 50.0
_SEUIL_TOXIQUE = 500.0
_SEUIL_MODERE = 5000.0


def _reel_fini(x, nom):
    """Convertit en float fini, sinon ValueError (abstention)."""
    if isinstance(x, bool):
        raise ValueError(f"{nom} booléen non accepté : {x!r}")
    try:
        v = float(x)
    except (TypeError, ValueError):
        raise ValueError(f"{nom} non numérique : {x!r}")
    if not math.isfinite(v):
        raise ValueError(f"{nom} non fini : {x!r}")
    return v


def _dose_positive_ou_nulle(x, nom):
    """Dose physique >= 0 ; < 0 ou non finie -> ValueError."""
    v = _reel_fini(x, nom)
    if v < 0.0:
        raise ValueError(f"{nom} négative : {v}")
    return v


def _denominateur_strict(x, nom):
    """Dénominateur de dose efficace > 0 ; <= 0 ou non fini -> ValueError."""
    v = _reel_fini(x, nom)
    if v <= 0.0:
        raise ValueError(f"{nom} non strictement positif : {v}")
    return v


def index_therapeutique(DL50, DE50):
    """
    Index thérapeutique IT = DL50 / DE50 (marge de sécurité, sans dimension).

    DL50 : dose létale médiane (>= 0, mêmes unités que DE50).
    DE50 : dose efficace médiane (> 0).
    IT > 1 = marge de sécurité (sûr) ; IT proche de 1 = fenêtre étroite.

    DL50 < 0, DE50 <= 0, ou valeurs non finies -> ValueError.
    """
    dl = _dose_positive_ou_nulle(DL50, "DL50")
    de = _denominateur_strict(DE50, "DE50")
    return round(dl / de, 6)


def dose_totale(dose_par_kg, masse_kg):
    """
    Dose totale = dose_par_kg * masse_kg.

    dose_par_kg : dosage pondéral (ex. mg/kg), >= 0.
    masse_kg    : masse corporelle (kg), > 0.
    Ex. 10 mg/kg * 70 kg = 700 mg.

    dose_par_kg < 0, masse_kg <= 0, ou valeurs non finies -> ValueError.
    """
    d = _dose_positive_ou_nulle(dose_par_kg, "dose_par_kg")
    m = _denominateur_strict(masse_kg, "masse_kg")
    return round(d * m, 6)


def marge_securite(DL1, DE99):
    """
    Marge de sécurité (certain safety factor) = DL1 / DE99.

    DL1  : dose létale pour 1 % de la population (>= 0).
    DE99 : dose efficace pour 99 % de la population (> 0).
    > 1 = aucun recouvrement entre fin d'efficacité et début de létalité.

    DL1 < 0, DE99 <= 0, ou valeurs non finies -> ValueError.
    """
    dl = _dose_positive_ou_nulle(DL1, "DL1")
    de = _denominateur_strict(DE99, "DE99")
    return round(dl / de, 6)


def classe_toxicite_dl50(dl50_mg_kg):
    """
    Classe de toxicité selon la DL50 orale (mg/kg) — échelle établie.

      dl50 < 5            -> 'extrêmement toxique'
      5    <= dl50 < 50   -> 'très toxique'
      50   <= dl50 < 500  -> 'toxique'
      500  <= dl50 < 5000 -> 'modérément'
      dl50 >= 5000        -> 'peu toxique'

    dl50_mg_kg < 0, ou non fini -> ValueError.
    """
    d = _dose_positive_ou_nulle(dl50_mg_kg, "dl50_mg_kg")
    if d < _SEUIL_EXTREME:
        return EXTREMEMENT_TOXIQUE
    if d < _SEUIL_TRES:
        return TRES_TOXIQUE
    if d < _SEUIL_TOXIQUE:
        return TOXIQUE
    if d < _SEUIL_MODERE:
        return MODEREMENT
    return PEU_TOXIQUE
