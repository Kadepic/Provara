"""
PUBLICITÉ / MARKETING (MÉCANISMES) — modèles de persuasion publicitaire ÉTABLIS (mandat Yohan : « tous les
sujets bornés, chirurgical, FAUX=0 »).

Domaine BORNÉ par des référentiels SOURCÉS / consensus établi (pas d'opinion, pas d'invention) :

  1) MODÈLE AIDA. Hiérarchie classique des effets publicitaires (E. St. Elmo Lewis, 1898 ; standard des
     manuels de marketing). Quatre étapes dans un ORDRE FIXE :
            Attention -> Intérêt -> Désir -> Action
     Chaque étape a un rôle/fonction défini et un rang (1..4). L'ordre est canonique : on capte d'abord
     l'attention, on suscite l'intérêt, on crée le désir, puis on déclenche l'action (achat).

  2) SIX PRINCIPES D'INFLUENCE DE CIALDINI (Robert Cialdini, « Influence: The Psychology of Persuasion »,
     1984 ; référentiel établi et largement cité) :
        réciprocité            — on se sent obligé de rendre ce qu'on a reçu ;
        engagement & cohérence — on tend à rester cohérent avec ses engagements antérieurs ;
        preuve sociale         — on suit ce que font les autres (« des milliers de clients ») ;
        autorité               — on obéit aux figures d'expertise / d'autorité ;
        sympathie              — on dit plus facilement « oui » à ceux qu'on apprécie ;
        rareté                 — ce qui est rare/limité paraît plus désirable (« édition limitée »).

Ce sont des CATALOGUES (taxonomies établies), pas des affirmations d'efficacité à trancher : chaque entrée est
un fait de référentiel. Toute entrée HORS référentiel -> abstention (ValueError), JAMAIS d'invention.

GARANTIES (vérifiées en adverse par `valide_marketing_mecanismes.py`) :
  - étape AIDA hors des 4 noms canoniques -> ValueError (jamais une étape devinée) ;
  - principe Cialdini hors des 6 noms canoniques -> ValueError (jamais un 7e principe inventé) ;
  - nom non textuel / vide -> ValueError (abstention) ;
  - l'ORDRE AIDA est exactement A->I->D->A (rangs 1..4) ;
  - déterministe (mêmes entrées -> mêmes sorties).
"""
from __future__ import annotations

from collections import namedtuple

SOURCE_AIDA = "modèle AIDA (hiérarchie des effets publicitaires, E. St. Elmo Lewis 1898 ; manuels de marketing)"
SOURCE_CIALDINI = "R. Cialdini, « Influence: The Psychology of Persuasion » (1984) — 6 principes d'influence"

# Étape AIDA : nom canonique, rang (1..4) et rôle/fonction.
EtapeAIDA = namedtuple("EtapeAIDA", ["nom", "rang", "role"])

# Principe d'influence : nom canonique et définition.
PrincipeCialdini = namedtuple("PrincipeCialdini", ["nom", "definition"])

# --- Catalogue AIDA (ordre canonique A -> I -> D -> A) -----------------------------------------------------
_AIDA = {
    "attention": EtapeAIDA(
        "attention", 1,
        "capter l'attention du prospect (rompre l'indifférence, se faire remarquer)",
    ),
    "interet": EtapeAIDA(
        "interet", 2,
        "susciter l'intérêt en montrant la pertinence du message pour le prospect",
    ),
    "desir": EtapeAIDA(
        "desir", 3,
        "créer le désir pour le produit/service (faire naître l'envie de le posséder)",
    ),
    "action": EtapeAIDA(
        "action", 4,
        "déclencher l'action (achat, contact, conversion)",
    ),
}

# Liste ordonnée des noms d'étapes (rang 1..4) — l'ordre est une donnée du modèle.
_ORDRE_AIDA = ["attention", "interet", "desir", "action"]

# --- Catalogue des 6 principes de Cialdini ----------------------------------------------------------------
_CIALDINI = {
    "reciprocite": PrincipeCialdini(
        "reciprocite",
        "on se sent obligé de rendre une faveur, un cadeau ou une concession reçus",
    ),
    "engagement_coherence": PrincipeCialdini(
        "engagement_coherence",
        "on tend à rester cohérent avec ses engagements et prises de position antérieurs",
    ),
    "preuve_sociale": PrincipeCialdini(
        "preuve_sociale",
        "on imite le comportement des autres, surtout en cas d'incertitude (« des milliers de clients »)",
    ),
    "autorite": PrincipeCialdini(
        "autorite",
        "on tend à suivre les figures d'expertise, de crédibilité ou d'autorité",
    ),
    "sympathie": PrincipeCialdini(
        "sympathie",
        "on accède plus facilement aux demandes des personnes que l'on apprécie",
    ),
    "rarete": PrincipeCialdini(
        "rarete",
        "ce qui est rare, limité ou en passe de disparaître paraît plus désirable (« édition limitée »)",
    ),
}


def _cle(nom: str, quoi: str) -> str:
    """Normalise un nom textuel en clé de catalogue ; lève ValueError si non textuel/vide."""
    if isinstance(nom, bool) or not isinstance(nom, str):
        raise ValueError(f"{quoi} : nom non textuel ({nom!r})")
    cle = nom.strip().lower()
    if not cle:
        raise ValueError(f"{quoi} : nom vide")
    return cle


def etape_aida(nom: str) -> EtapeAIDA:
    """Renvoie l'étape AIDA (nom, rang, rôle) pour un des 4 noms canoniques.

    'attention','interet','desir','action' -> rang et rôle (modèle AIDA, ordre A->I->D->A).
    Étape inconnue ou entrée invalide -> ValueError (abstention, jamais d'invention).
    """
    cle = _cle(nom, "etape_aida")
    if cle not in _AIDA:
        raise ValueError(f"etape_aida : étape AIDA inconnue ({nom!r}) — hors {{{', '.join(_ORDRE_AIDA)}}}")
    return _AIDA[cle]


def ordre_aida() -> list:
    """Renvoie la liste ordonnée des 4 noms d'étapes AIDA (rang 1..4) : A -> I -> D -> A."""
    return list(_ORDRE_AIDA)


def rang_aida(nom: str) -> int:
    """Renvoie le rang (1..4) de l'étape AIDA. Inconnu/invalide -> ValueError."""
    return etape_aida(nom).rang


def principe_cialdini(nom: str) -> PrincipeCialdini:
    """Renvoie le principe d'influence de Cialdini (nom, définition) pour un des 6 noms canoniques.

    'reciprocite','engagement_coherence','preuve_sociale','autorite','sympathie','rarete' -> définition.
    Principe inconnu (ex. un « 7e principe ») ou entrée invalide -> ValueError (abstention, jamais inventé).
    """
    cle = _cle(nom, "principe_cialdini")
    if cle not in _CIALDINI:
        raise ValueError(
            f"principe_cialdini : principe inconnu ({nom!r}) — hors les 6 principes de Cialdini"
        )
    return _CIALDINI[cle]


def definition_cialdini(nom: str) -> str:
    """Renvoie la définition d'un principe de Cialdini. Inconnu/invalide -> ValueError."""
    return principe_cialdini(nom).definition


def principes_cialdini() -> list:
    """Renvoie la liste des 6 noms canoniques des principes de Cialdini (ordre de référence)."""
    return ["reciprocite", "engagement_coherence", "preuve_sociale", "autorite", "sympathie", "rarete"]
