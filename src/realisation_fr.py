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


# pays / cités-États SANS article défini en français : « Monaco » (pas « le Monaco »), « Cuba », « Malte »… On les
# rend NUS. La plupart sont des îles ou petits États ; « à/de » se disent aussi sans article (« de Monaco »).
_PAYS_SANS_ARTICLE = frozenset(
    "monaco cuba malte chypre madagascar singapour haiti bahrein oman djibouti andorre israel taiwan "
    "saint-marin sri lanka nauru tuvalu kiribati fidji vanuatu samoa tonga palaos maurice".split()
    + ["sri lanka", "saint-marin", "costa rica", "porto rico"])


def sans_article(pays: str) -> bool:
    """Le pays se dit-il SANS article défini ? (« Monaco », « Cuba » — pas « le Monaco »)."""
    return _sa(pays).lower().strip() in _PAYS_SANS_ARTICLE


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
    """« de <pays> » avec le bon article : du Nigéria, de la France, des Pays-Bas, d'Italie, de Monaco (nu)."""
    if sans_article(pays):
        return "de " + pays
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
    if sans_article(pays):                # « Monaco », « Cuba » — jamais « le Monaco »
        return pays
    return article(pays, genre=genre_pays(pays), majuscule=majuscule)


_GENRE_MOT = None       # {mot_normalisé : 'm'|'f'} depuis lexique_fr_pos.jsonl (19k noms) — pour les NOMS COMMUNS


def genre_mot(mot: str):
    """Genre grammatical d'un nom commun ('m'/'f'/None) via le lexique embarqué. Pour « le chat », « la voiture »."""
    global _GENRE_MOT
    if _GENRE_MOT is None:
        import json
        import os
        _GENRE_MOT = {}
        base = os.path.dirname(os.path.abspath(__file__))
        for cand in (os.path.join(base, "lexique_fr_pos.jsonl"),):
            try:
                with open(cand, encoding="utf-8") as fh:
                    for ligne in fh:
                        ligne = ligne.strip()
                        if not ligne:
                            continue
                        try:
                            o = json.loads(ligne)
                        except ValueError:
                            continue
                        m, g = o.get("mot"), o.get("genre")
                        if m and g in ("masculin", "féminin"):
                            _GENRE_MOT.setdefault(_sa(m).lower(), "m" if g == "masculin" else "f")
            except OSError:
                pass
    return _GENRE_MOT.get(_sa(mot).lower())


def genre_maladie(mot: str) -> str:
    """Genre d'un nom de maladie ('m'/'f'). Lexique d'abord, puis suffixes médicaux fiables (grippe→f, paludisme→m,
    amibiase→f, diabète→m). Défaut : -e final → féminin, sinon masculin (heuristique française générale)."""
    g = genre_mot(mot)
    if g:
        return g
    n = _sa(mot).lower().strip()
    if n.endswith(("ite", "ose", "ase", "emie", "algie", "pathie", "plegie", "phobie", "asthenie", "urie",
                   "rrhee", "ectomie", "tomie", "ie", "ade", "ure", "rose", "ole", "elle")):
        return "f"
    if n.endswith(("isme", "ome", "ospasme", "ere", "er", "at", "us", "ma")):
        return "m"
    return "f" if n.endswith("e") else "m"


def un_nom(mot: str) -> str:
    """« un/une <nom commun> » selon le genre du lexique (défaut 'un'). Ex. « un mammifère », « une voiture »."""
    return ("une " if genre_mot(mot) == "f" else "un ") + mot


def le_nom(mot: str, majuscule: bool = False) -> str:
    """« le/la/l' <nom commun> » selon le genre du lexique. Ex. « le chat », « la voiture », « l'oiseau »."""
    return article(mot, genre=genre_mot(mot) or "m", majuscule=majuscule)


def _genre_syntagme(expr: str) -> str:
    """Genre d'un syntagme nominal = genre de sa TÊTE (1er mot), repli masculin."""
    mots = expr.split()
    tete = mots[0] if mots else expr
    return genre_mot(tete) or genre_mot(expr) or "m"


def le_syntagme(expr: str, majuscule: bool = False) -> str:
    """« le/la/l' » devant un SYNTAGME NOMINAL : le genre est porté par la TÊTE (1er mot), pas par l'expression
    entière — « mer Baltique » -> « la mer Baltique », « océan Atlantique » -> « l'océan Atlantique »."""
    return article(expr, genre=_genre_syntagme(expr), majuscule=majuscule)


def de_syntagme(expr: str) -> str:
    """« de X » CONTRACTÉ pour un syntagme : « du Lukna », « de la mer Baltique », « de l'océan Atlantique »."""
    return de(expr, genre=_genre_syntagme(expr))
