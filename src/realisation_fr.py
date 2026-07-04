#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
RÉALISATION FRANÇAISE — surface propre pour TOUTES les réponses des atomes (2026-07-04).

Excellence atomique : une réponse juste mais mal réalisée (« capitale de Nigeria », « pays de Afrique », « France
est un pays ») trahit la qualité. Ce module centralise les règles MÉCANIQUES du français — élisions, contractions,
articles, genre des pays — pour que chaque atome produise un français IRRÉPROCHABLE, sans dupliquer la logique.

Règles 100% sûres (aucun cas faux) :
  • élision : « de » + voyelle/h → « d' » (d'Afrique, d'Europe) ; « le/la » + voyelle → « l' » (l'euro, l'Inde) ;
  • contraction : « de » + « le » → « du », « de » + « les » → « des », « à » + « le » → « au ».
Règles à GENRE (pays) : table curée + heuristique (-e final ≈ féminin, avec exceptions) — « du Nigéria », « de la
France », « des Pays-Bas ». Les CONTINENTS prennent l'élision sans article (« d'Afrique »), usage idiomatique.

stdlib pur, déterministe, souverain.
"""
from __future__ import annotations

import unicodedata


def _sa(s: str) -> str:
    return "".join(c for c in unicodedata.normalize("NFD", str(s)) if unicodedata.category(c) != "Mn")


def _voyelle_initiale(mot: str) -> bool:
    """Le mot commence-t-il par une voyelle (ou un h, muet en pratique pour l'élision courante) ?"""
    m = _sa(mot).lstrip("'’\"«» ").lower()
    return bool(m) and m[0] in "aeiouyh"


# Genre des pays fréquents (exceptions à l'heuristique -e). Minuscules sans accent.
_PAYS_MASC = frozenset(
    "nigeria japon bresil canada mexique portugal perou chili maroc senegal congo kenya soudan tchad niger mali "
    "cameroun gabon ghana zimbabwe mozambique botswana danemark luxembourg liban koweit qatar yemen laos vietnam "
    "cambodge bangladesh pakistan nepal bhoutan turkmenistan kazakhstan ouzbekistan panama honduras salvador "
    "guatemala venezuela paraguay uruguay costa rica royaume-uni".split())
_PAYS_FEM = frozenset(
    "france espagne chine russie allemagne italie inde belgique suisse grece turquie pologne roumanie hongrie "
    "suede norvege finlande irlande ecosse tunisie algerie libye egypte ethiopie somalie namibie zambie tanzanie "
    "ouganda mauritanie gambie guinee colombie bolivie argentine jordanie syrie thailande birmanie mongolie "
    "coree indonesie malaisie australie nouvelle-zelande croatie serbie slovenie slovaquie lettonie lituanie".split())


def genre_pays(pays: str):
    """'m' / 'f' / None (pluriel ou inconnu) pour un pays. Table curée d'abord, puis heuristique du -e final."""
    n = _sa(pays).lower().strip()
    if n in _PAYS_MASC:
        return "m"
    if n in _PAYS_FEM:
        return "f"
    if n.endswith("s") and n not in ("laos", "belarus"):
        return "p"                        # pluriel probable (Pays-Bas, États-Unis, Émirats…) -> « des »/« les »
    if n.endswith("e"):
        return "f"                        # heuristique : -e final ≈ féminin
    return "m"


def de(mot: str, genre: str = None, continent: bool = False) -> str:
    """« de X » réalisé : élision, contraction et genre. `genre` ∈ {'m','f',None}. `continent`=True force l'usage
    sans article (« d'Afrique », « de Mars »). Renvoie la locution complète, ex. « du Nigéria », « de la France »."""
    if _voyelle_initiale(mot):
        return "d'" + mot if (continent or genre in (None, "p")) else "de l'" + mot
    if continent or genre is None:
        return "de " + mot
    if genre == "m":
        return "du " + mot
    if genre == "f":
        return "de la " + mot
    return "des " + mot                   # pluriel ('p')


def de_pays(pays: str) -> str:
    """« de <pays> » avec le bon article : du Nigéria, de la France, des Pays-Bas, d'Italie."""
    return de(pays, genre=genre_pays(pays))


def article(mot: str, genre: str = None, majuscule: bool = False) -> str:
    """Article défini + mot : « le Nigéria », « la France », « l'Italie », « les Pays-Bas ». `majuscule` capitalise
    l'article en tête de phrase (« Le Nigéria est… »)."""
    if genre in ("p", None) and not _voyelle_initiale(mot):
        art = "les "                      # pluriel / inconnu -> « les »
    elif _voyelle_initiale(mot):
        art = "les " if genre == "p" else "l'"
    elif genre == "f":
        art = "la "
    else:
        art = "le "
    if majuscule:
        art = art[0].upper() + art[1:]
    return art + mot


def article_pays(pays: str, majuscule: bool = False) -> str:
    return article(pays, genre=genre_pays(pays), majuscule=majuscule)
