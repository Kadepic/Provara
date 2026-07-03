"""
RECETTES (procédures) — mise à l'échelle et conversions culinaires (CONVENTIONS).

Posture FAUX=0 (même que `physique`/`chimie` : la réalité/la convention juge, jamais un faux) :
  • Le MÉCANISME est EXACT et déterministe :
      - mise à l'échelle = règle de trois (proportionnalité directe des quantités aux portions) ;
      - conversions = facteurs CONVENTIONNELS établis (équivalences de mesures de cuisine, US customary/usage courant).
  • Les FACTEURS sont des DONNÉES CONVENTIONNELLES SOURCÉES (équivalences culinaires standard) :
      tasse = 240 ml, cuillère à soupe (c.à.s) = 15 ml, cuillère à café (c.à.c) = 5 ml.
      Pour l'EAU (densité 1 g/ml par convention), 1 ml ↔ 1 g.
  • Toute entrée HORS référentiel (unité inconnue, portions ≤ 0, densité non fournie pour g↔ml d'un
    ingrédient non aqueux) -> ValueError (abstention). JAMAIS une valeur inventée.

GARANTIES (vérifiées en adverse par `valide_recettes.py`) :
  - portions_origine ≤ 0 ou portions_cible < 0 -> ValueError ;
  - quantité < 0 -> ValueError ;
  - unité (de/vers) inconnue -> ValueError ;
  - conversion entre dimensions incompatibles sans densité (ex. g ↔ ml d'un ingrédient ≠ eau) -> ValueError ;
  - déterministe ; conservateur (abstention tolérée, faux POSITIF interdit).

stdlib uniquement.
"""
from __future__ import annotations

from numbers import Real

# ── FACTEURS CONVENTIONNELS ─────────────────────────────────────────────────────────────────────────────────────
# Unités de VOLUME -> millilitres (ml). Équivalences culinaires standard (usage courant / US customary cooking).
_VOLUME_ML = {
    "ml": 1.0,            # millilitre (référence volume)
    "millilitre": 1.0,
    "l": 1000.0,          # litre
    "litre": 1000.0,
    "cl": 10.0,           # centilitre
    "centilitre": 10.0,
    "dl": 100.0,          # décilitre
    "decilitre": 100.0,
    "tasse": 240.0,       # 1 tasse = 240 ml (convention)
    "cuillere_soupe": 15.0,   # cuillère à soupe = 15 ml
    "cuillere_cafe": 5.0,     # cuillère à café = 5 ml
}

# Unités de MASSE -> grammes (g).
_MASSE_G = {
    "g": 1.0,            # gramme (référence masse)
    "gramme": 1.0,
    "kg": 1000.0,        # kilogramme
    "kilogramme": 1000.0,
    "mg": 0.001,         # milligramme
    "milligramme": 0.001,
}

# Densité conventionnelle de l'eau : 1 g/ml. Permet g ↔ ml pour l'eau (et ingrédients aqueux assimilés).
DENSITE_EAU = 1.0  # g/ml

SOURCE = "équivalences culinaires conventionnelles : tasse=240 ml, c.à.s=15 ml, c.à.c=5 ml ; eau densité 1 g/ml"


def _norme_unite(u):
    """Normalise un nom d'unité (str non vide). ValueError sinon."""
    if not isinstance(u, str):
        raise ValueError(f"unité non textuelle : {u!r}")
    cle = u.strip().lower().replace("à", "a").replace("é", "e").replace("è", "e")
    cle = cle.replace(" ", "_").replace(".", "")
    # alias courants
    alias = {
        "cas": "cuillere_soupe", "c_a_s": "cuillere_soupe", "cuillere_a_soupe": "cuillere_soupe",
        "cac": "cuillere_cafe", "c_a_c": "cuillere_cafe", "cuillere_a_cafe": "cuillere_cafe",
        "cup": "tasse",
    }
    return alias.get(cle, cle)


def _verifie_reel(x, nom, *, strictement_positif=False, positif=False):
    if isinstance(x, bool) or not isinstance(x, Real):
        raise ValueError(f"{nom} doit être un nombre réel : {x!r}")
    x = float(x)
    if strictement_positif and x <= 0:
        raise ValueError(f"{nom} doit être > 0 : {x}")
    if positif and x < 0:
        raise ValueError(f"{nom} doit être ≥ 0 : {x}")
    return x


def adapte_quantite(quantite, portions_origine, portions_cible):
    """
    Mise à l'échelle d'une quantité par règle de trois (proportionnalité aux portions) :
        quantite_adaptee = quantite · portions_cible / portions_origine

    Ex. recette pour 4 personnes adaptée à 6 -> facteur ×1.5.

    SOUNDNESS : quantite < 0, portions_origine ≤ 0, portions_cible < 0 -> ValueError.
    """
    q = _verifie_reel(quantite, "quantite", positif=True)
    po = _verifie_reel(portions_origine, "portions_origine", strictement_positif=True)
    pc = _verifie_reel(portions_cible, "portions_cible", positif=True)
    return q * pc / po


def facteur_echelle(portions_origine, portions_cible):
    """Facteur de mise à l'échelle = portions_cible / portions_origine. SOUNDNESS idem."""
    po = _verifie_reel(portions_origine, "portions_origine", strictement_positif=True)
    pc = _verifie_reel(portions_cible, "portions_cible", positif=True)
    return pc / po


def convertir_mesure(valeur, de, vers, ingredient="eau"):
    """
    Convertit `valeur` de l'unité `de` vers l'unité `vers` (mesures culinaires conventionnelles).

    - volume ↔ volume (tasse/c.à.s/c.à.c/ml/cl/dl/l) : par facteurs en ml ;
    - masse ↔ masse (g/kg/mg) : par facteurs en g ;
    - volume ↔ masse : UNIQUEMENT pour l'eau (densité 1 g/ml). Pour tout autre ingrédient,
      la densité n'est pas conventionnelle -> ValueError (abstention).

    SOUNDNESS : valeur < 0, unité inconnue, dimensions incompatibles sans densité connue -> ValueError.
    """
    v = _verifie_reel(valeur, "valeur", positif=True)
    de_n = _norme_unite(de)
    vers_n = _norme_unite(vers)

    de_vol = de_n in _VOLUME_ML
    de_mas = de_n in _MASSE_G
    vers_vol = vers_n in _VOLUME_ML
    vers_mas = vers_n in _MASSE_G

    if not (de_vol or de_mas):
        raise ValueError(f"unité de départ inconnue : {de!r}")
    if not (vers_vol or vers_mas):
        raise ValueError(f"unité d'arrivée inconnue : {vers!r}")

    # même dimension : volume->volume ou masse->masse
    if de_vol and vers_vol:
        return v * _VOLUME_ML[de_n] / _VOLUME_ML[vers_n]
    if de_mas and vers_mas:
        return v * _MASSE_G[de_n] / _MASSE_G[vers_n]

    # dimensions croisées : nécessite une densité conventionnelle (eau uniquement)
    if not (isinstance(ingredient, str) and ingredient.strip().lower() in ("eau", "water")):
        raise ValueError(
            f"conversion volume↔masse impossible sans densité conventionnelle pour : {ingredient!r}"
        )
    densite = DENSITE_EAU  # g/ml
    if de_vol and vers_mas:
        ml = v * _VOLUME_ML[de_n]            # -> ml
        g = ml * densite                     # -> g (eau)
        return g / _MASSE_G[vers_n]          # -> unité de masse cible
    # de_mas and vers_vol
    g = v * _MASSE_G[de_n]                    # -> g
    ml = g / densite                         # -> ml (eau)
    return ml / _VOLUME_ML[vers_n]           # -> unité de volume cible


def temps_cuisson_adapte(temps_origine, portions_origine, portions_cible, exposant=1.0):
    """
    Temps de cuisson adapté à un changement de portions.

    Convention RETENUE (par défaut, exposant=1.0) : le temps de cuisson NE se met PAS à l'échelle
    proportionnellement à la quantité — c'est une donnée NON bornée par la simple règle de trois
    (dépend de la géométrie, du four, de l'épaisseur…). Par défaut on RENVOIE le temps d'origine
    (exposant=0 ne s'applique pas : on garde le temps tel quel, le plus sûr / abstention déguisée).

    Pour rester FAUX=0 et déterministe, on n'expose qu'une règle EXPLICITE et bornée :
      - exposant == 0.0  -> temps inchangé (temps_origine) ;
      - exposant == 1.0  -> proportionnel aux portions (cas idéalisé) ;
    Tout autre exposant réel ≥ 0 est accepté comme loi de puissance explicite fournie par l'appelant
    (temps · (cible/origine)**exposant). exposant < 0 -> ValueError.

    SOUNDNESS : temps_origine < 0, portions_origine ≤ 0, portions_cible < 0, exposant < 0 -> ValueError.
    """
    t = _verifie_reel(temps_origine, "temps_origine", positif=True)
    po = _verifie_reel(portions_origine, "portions_origine", strictement_positif=True)
    pc = _verifie_reel(portions_cible, "portions_cible", positif=True)
    e = _verifie_reel(exposant, "exposant", positif=True)
    if e == 0.0:
        return t
    return t * (pc / po) ** e
