"""
HÉRALDIQUE — noyau BORNÉ des règles du blason (convention FERMÉE), pur stdlib (2026-07-02).

POURQUOI (sujet borné B-CONV « Héraldique (blasons, règles) ») : l'héraldique est un système de CONVENTIONS établies
et fermées — les émaux (teintures) sont catalogués, et la « règle de contrariété des couleurs » (rule of tincture)
tranche mécaniquement la validité d'un contraste. La réalité (la norme héraldique) fixe la réponse.

FAUX=0 :
  • Catalogue FERMÉ des teintures : 2 métaux (or, argent), 5 couleurs/émaux (gueules, azur, sinople, sable, pourpre),
    fourrures (hermine, contre-hermine, vair, contre-vair). Teinture hors catalogue -> ValueError (jamais devinée).
  • Règle de contrariété EXACTE : ne pas poser métal sur métal ni couleur sur couleur ; les fourrures sont neutres
    (compatibles avec tout). `contraste_valide` renvoie le verdict de la règle, re-dérivable.
Ce module ne juge PAS l'esthétique ni ne blasonne un dessin libre (non-borné) : il applique la CONVENTION. Souverain.
"""
from __future__ import annotations

_METAUX = {"or", "argent"}
_COULEURS = {"gueules", "azur", "sinople", "sable", "pourpre"}
_FOURRURES = {"hermine", "contre-hermine", "vair", "contre-vair"}
_TOUTES = _METAUX | _COULEURS | _FOURRURES

# Couleur moderne indicative (pour restitution), convention usuelle.
_TEINTE = {
    "or": "jaune/doré", "argent": "blanc/argenté", "gueules": "rouge", "azur": "bleu",
    "sinople": "vert", "sable": "noir", "pourpre": "violet",
}


def _norm(t: str) -> str:
    if not isinstance(t, str):
        raise ValueError("teinture : str attendu")
    return t.strip().lower()


def categorie(teinture: str) -> str:
    """'metal' | 'couleur' | 'fourrure'. Hors catalogue -> ValueError."""
    t = _norm(teinture)
    if t in _METAUX:
        return "metal"
    if t in _COULEURS:
        return "couleur"
    if t in _FOURRURES:
        return "fourrure"
    raise ValueError(f"teinture hors catalogue héraldique : {teinture!r}")


def teintes_modernes(teinture: str) -> str:
    """Couleur moderne indicative d'une teinture (métaux/couleurs). Fourrure/inconnu -> ValueError."""
    t = _norm(teinture)
    if t not in _TEINTE:
        raise ValueError(f"pas de teinte moderne conventionnée pour {teinture!r}")
    return _TEINTE[t]


def contraste_valide(fond: str, figure: str) -> bool:
    """Règle de contrariété des couleurs : FAUX si (métal sur métal) ou (couleur sur couleur) ; les fourrures sont
    neutres (toujours valides). Teinture hors catalogue -> ValueError."""
    cf, cg = categorie(fond), categorie(figure)
    if cf == "fourrure" or cg == "fourrure":
        return True
    return cf != cg               # metal/couleur ou couleur/metal = valide ; même catégorie = viole la règle


def teintures() -> dict:
    """Catalogue fermé par catégorie."""
    return {"metaux": sorted(_METAUX), "couleurs": sorted(_COULEURS), "fourrures": sorted(_FOURRURES)}
