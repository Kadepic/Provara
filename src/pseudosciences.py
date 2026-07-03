"""
PSEUDOSCIENCES — catalogue BORNÉ du STATUT scientifique de validité (consensus établi), pur stdlib (2026-07-02).

POURQUOI (annexe « CANDIDATS NON-BORNÉS à challenger » de Yohan : astrologie, voyance, paranormal, numérologie,
superstitions) : la PRATIQUE elle-même n'est pas bornée, mais la QUESTION « a-t-elle une validité empirique/prédictive
démontrée ? » l'EST — le consensus scientifique la tranche (études contrôlées répétées, méta-analyses). C'est un FAIT
borné sur les CLAIMS, pas un jugement de goût. Même patron FAUX=0 que medecines_alternatives.py.

FAUX=0 :
  • Catalogue FERMÉ, chaque entrée = statut sourcé (aucune / non_demontree) + référence du consensus.
    - « aucune » : validité prédictive/empirique RÉFUTÉE par études contrôlées (ex. astrologie, Carlson 1985, Nature).
    - « non_demontree » : aucune preuve reproductible malgré recherche (ex. perception extra-sensorielle).
  • Hors catalogue -> ValueError (jamais un verdict inventé). Le module n'affirme rien sur des expériences vécues
    (subjectif, non-borné) : il rapporte le STATUT DE PREUVE, pas une vérité métaphysique.
Souverain, offline, stdlib pur.
"""
from __future__ import annotations

# pratique -> (statut, base du consensus)
_CATALOGUE = {
    "astrologie": ("aucune", "Études contrôlées négatives (Carlson 1985, Nature) ; aucun mécanisme ni pouvoir prédictif reproductible."),
    "voyance": ("aucune", "Tests contrôlés (protocoles à l'aveugle) systématiquement négatifs ; effet Barnum/lecture à froid expliquent les 'réussites'."),
    "divination": ("aucune", "Aucune capacité prédictive au-delà du hasard en conditions contrôlées."),
    "tarot_divinatoire": ("aucune", "Interprétation non falsifiable en pratique ; aucune prédiction vérifiée > hasard."),
    "cartomancie": ("aucune", "Idem divination : aucun pouvoir prédictif démontré."),
    "numerologie": ("aucune", "Aucune corrélation nombre-destin établie ; associations arbitraires."),
    "radiesthesie": ("aucune", "Essais en double aveugle (baguettes/pendule) au niveau du hasard (ideomotor)."),
    "chiromancie": ("aucune", "Aucune corrélation lignes de la main / traits ou avenir démontrée."),
    "superstitions": ("aucune", "Corrélations illusoires ; aucun lien causal (ex. chat noir, échelle) démontré."),
    "perception_extra_sensorielle": ("non_demontree", "Méta-analyses (Ganzfeld) contestées, non reproductibles indépendamment ; pas de preuve solide."),
    "telepathie": ("non_demontree", "Aucune démonstration reproductible en conditions contrôlées."),
    "phenomenes_paranormaux": ("non_demontree", "Aucun phénomène (télékinésie, fantômes…) reproduit sous contrôle scientifique."),
}

_ALIAS = {
    "horoscope": "astrologie", "astrologique": "astrologie",
    "cartomancie_tarot": "tarot_divinatoire", "tarot": "tarot_divinatoire",
    "pendule": "radiesthesie", "sourcier": "radiesthesie",
    "esp": "perception_extra_sensorielle", "paranormal": "phenomenes_paranormaux",
    "numerologique": "numerologie", "superstition": "superstitions",
}


def _resoudre(pratique: str) -> str:
    if not isinstance(pratique, str):
        raise ValueError("pratique : str attendu")
    p = pratique.strip().lower().replace(" ", "_").replace("-", "_")
    p = _ALIAS.get(p, p)
    if p not in _CATALOGUE:
        raise ValueError(f"pratique hors catalogue pseudosciences : {pratique!r}")
    return p


def est_catalogue(pratique: str) -> bool:
    try:
        _resoudre(pratique)
        return True
    except ValueError:
        return False


def validite_scientifique(pratique: str) -> str:
    """'aucune' (validité réfutée) ou 'non_demontree' (jamais prouvée). Hors catalogue -> ValueError."""
    return _CATALOGUE[_resoudre(pratique)][0]


def base_consensus(pratique: str) -> str:
    """La justification sourcée du statut."""
    return _CATALOGUE[_resoudre(pratique)][1]


def a_validite_demontree(pratique: str) -> bool:
    """True SEULEMENT si une validité empirique est démontrée. Ici : toujours False sur le catalogue (par construction
    du consensus). Hors catalogue -> ValueError (on n'affirme rien sur l'inconnu)."""
    return False if _resoudre(pratique) else False


def pratiques() -> tuple:
    return tuple(sorted(_CATALOGUE))
