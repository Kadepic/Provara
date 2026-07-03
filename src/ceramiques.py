"""
CÉRAMIQUES BORNÉ — propriétés des céramiques (faits établis + calculs exacts).

Même posture FAUX=0 que `analyse_chimique` / `physique` (la réalité juge, jamais un faux) :
  • Le MÉCANISME (définition géométrique, classification conventionnelle) est EXACT — garantie structurelle.
  • ABSTENTION STRUCTURELLE : toute entrée hors domaine (type, signe, plage, classe inconnue) lève ValueError,
    JAMAIS un résultat inventé. Conservateur : faux négatif (abstention) toléré, faux POSITIF interdit.

COUVERTURE :
  ── Calculs géométriques de mise en œuvre ──
    retrait_cuisson(d_crue, d_cuite) = (d_crue − d_cuite) / d_crue   retrait linéaire de cuisson (fraction ≥ 0)
        la cuisson FAIT RÉTRACTER la pièce : d_cuite ≤ d_crue (retrait négatif = impossible -> ValueError)
        CAS de référence : 100 mm -> 88 mm  =>  12/100 = 0.12 (12 %)
    porosite(v_vides, v_total) = v_vides / v_total                   porosité (fraction du volume occupée par les vides)
        0 ≤ v_vides ≤ v_total, v_total > 0   =>   porosité ∈ [0, 1]
  ── Classification conventionnelle par température de cuisson typique ──
    classe_ceramique(nom) -> température de cuisson typique (°C) pour une famille céramique connue.
        Hiérarchie établie (du moins au plus chaud, du plus poreux au vitrifié) :
            terre cuite ~950 °C  <  faïence ~1000 °C  <  grès ~1250 °C  <  porcelaine ~1300 °C
        terre cuite / faïence : pâtes POREUSES, opaques.   grès / porcelaine : pâtes VITRIFIÉES (porcelaine translucide).
  ── Faits matériaux qualitatifs établis ──
    Les céramiques ont une RÉSISTANCE EN COMPRESSION ÉLEVÉE mais sont FRAGILES (faible ténacité, faible résistance
    en traction) : la rupture est cassante, sans plasticité. -> proprietes_mecaniques() / est_fragile().

GARDES DE DOMAINE (vérifiées en adverse par valide_ceramiques.py) :
  - dimension ≤ 0, volume_total ≤ 0, volume_vides < 0 -> ValueError
  - d_cuite > d_crue (retrait négatif), v_vides > v_total (porosité > 1) -> ValueError
  - type non numérique (ou booléen), valeur non finie -> ValueError
  - nom de classe hors référentiel connu -> ValueError (abstention, jamais une température inventée)
"""
from __future__ import annotations

import math

# ── Classification conventionnelle : température de cuisson typique (°C) ──────────────────────────────────────────
# Valeurs typiques établies (manuels de céramique). La classe est une CONVENTION fondée sur la pâte et la cuisson ;
# l'ordre terre cuite < faïence < grès < porcelaine est l'échelle standard de vitrification.
_TEMPERATURES_C = {
    "terre_cuite": 950.0,
    "faience": 1000.0,
    "gres": 1250.0,
    "porcelaine": 1300.0,
}

# Faits qualitatifs établis par famille : porosité de la pâte et translucidité.
_PROPRIETES = {
    "terre_cuite": {"temperature_cuisson_C": 950.0,  "pate": "poreuse",  "translucide": False},
    "faience":     {"temperature_cuisson_C": 1000.0, "pate": "poreuse",  "translucide": False},
    "gres":        {"temperature_cuisson_C": 1250.0, "pate": "vitrifiee", "translucide": False},
    "porcelaine":  {"temperature_cuisson_C": 1300.0, "pate": "vitrifiee", "translucide": True},
}

# Faits matériaux qualitatifs établis (vrais pour les céramiques techniques et traditionnelles).
_PROPRIETES_MECANIQUES = {
    "resistance_compression": "elevee",   # forte tenue en compression
    "resistance_traction": "faible",      # faible en traction
    "tenacite": "faible",                 # faible ténacité (K_IC bas)
    "fragile": True,                       # rupture cassante, sans plasticité
    "ductile": False,
}


def _reel(x) -> float:
    """Renvoie x comme float si c'est un nombre réel (pas un booléen, fini), sinon ValueError."""
    if isinstance(x, bool) or not isinstance(x, (int, float)):
        raise ValueError(f"valeur non numérique : {x!r}")
    v = float(x)
    if not math.isfinite(v):
        raise ValueError(f"valeur non finie : {x!r}")
    return v


def _normalise_nom(nom) -> str:
    """Normalise un nom de famille céramique vers une clé canonique ; classe inconnue -> ValueError."""
    if not isinstance(nom, str):
        raise ValueError(f"nom de céramique non textuel : {nom!r}")
    cle = nom.strip().lower()
    # repli des accents et séparateurs vers la forme canonique
    cle = (cle.replace("ï", "i").replace("è", "e").replace("é", "e").replace("ê", "e")
              .replace("-", "_").replace(" ", "_"))
    while "__" in cle:
        cle = cle.replace("__", "_")
    if cle not in _TEMPERATURES_C:
        raise ValueError(f"classe de céramique inconnue : {nom!r} (connues : "
                         f"{', '.join(sorted(_TEMPERATURES_C))})")
    return cle


# ── CALCULS GÉOMÉTRIQUES ─────────────────────────────────────────────────────────────────────────────────────────

def retrait_cuisson(dim_crue, dim_cuite) -> float:
    """Retrait linéaire de cuisson = (d_crue − d_cuite) / d_crue. d > 0, d_cuite ≤ d_crue -> fraction ∈ [0, 1[.

    La cuisson rétracte la pièce ; un agrandissement (d_cuite > d_crue) n'est pas un retrait -> ValueError.
    Ex. : retrait_cuisson(100, 88) = 0.12 (12 %)."""
    dc, dk = _reel(dim_crue), _reel(dim_cuite)
    if dc <= 0:
        raise ValueError("dim_crue doit être > 0")
    if dk <= 0:
        raise ValueError("dim_cuite doit être > 0")
    if dk > dc:
        raise ValueError("dim_cuite ne peut dépasser dim_crue (le retrait de cuisson est >= 0)")
    return (dc - dk) / dc


def porosite(volume_vides, volume_total) -> float:
    """Porosité = volume_vides / volume_total. 0 ≤ v_vides ≤ v_total, v_total > 0 -> fraction ∈ [0, 1]."""
    vv, vt = _reel(volume_vides), _reel(volume_total)
    if vt <= 0:
        raise ValueError("volume_total doit être > 0")
    if vv < 0:
        raise ValueError("volume_vides doit être >= 0")
    if vv > vt:
        raise ValueError("volume_vides ne peut dépasser volume_total (porosité <= 1)")
    return vv / vt


# ── CLASSIFICATION & FAITS ───────────────────────────────────────────────────────────────────────────────────────

def classe_ceramique(nom) -> float:
    """Température de cuisson typique (°C) d'une famille céramique connue.

    porcelaine ~1300, grès ~1250, faïence ~1000, terre cuite ~950.
    Nom hors référentiel -> ValueError (abstention)."""
    return _TEMPERATURES_C[_normalise_nom(nom)]


def proprietes_ceramique(nom) -> dict:
    """Faits établis d'une famille connue : température de cuisson, pâte (poreuse/vitrifiée), translucidité.

    Renvoie une COPIE (immutabilité de la table de faits). Nom inconnu -> ValueError."""
    return dict(_PROPRIETES[_normalise_nom(nom)])


def proprietes_mecaniques() -> dict:
    """Faits matériaux établis des céramiques : compression élevée, traction/ténacité faibles, rupture fragile."""
    return dict(_PROPRIETES_MECANIQUES)


def est_fragile() -> bool:
    """Fait établi : les céramiques sont fragiles (faible ténacité, rupture cassante sans plasticité)."""
    return True


def classes_connues() -> tuple:
    """Familles céramiques du référentiel (clés canoniques), ordonnées par température de cuisson croissante."""
    return tuple(sorted(_TEMPERATURES_C, key=_TEMPERATURES_C.get))
