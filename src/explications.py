# -*- coding: utf-8 -*-
"""EXPLICATIONS DE CONCEPTS / PARADOXES — câble au chat les briques pédagogiques du Palier 2 (2026-07-03).

POURQUOI (mandat Yohan « chercher des solutions » pour les fonctions Palier 2 non exprimables en données) :
beaucoup de fonctions de ia.py sont des DÉMONSTRATIONS auto-contenues (paradoxes, sophismes, effets cognitifs)
qui ne demandent AUCUNE donnée utilisateur — elles produisent une leçon exacte avec `phrase=True`. On les rend
accessibles par « explique le paradoxe de X », « qu'est-ce que la loi de Goodhart », « sophisme des coûts
irrécupérables »…

FAUX=0 : chaque explication vient DIRECTEMENT de la brique (calcul honnête), jamais d'une paraphrase inventée.
Concept inconnu -> None (le pipeline continue vers la recherche web).
"""
from __future__ import annotations

import re

# clé (motif normalisé) -> (libellé, appel ia). Uniquement les briques au rendu auto-contenu (défauts sains).
_CONCEPTS = [
    (r"deux enveloppes|two envelopes", "paradoxe des deux enveloppes", lambda ia: ia.deux_enveloppes(phrase=True)),
    (r"parrondo", "paradoxe de Parrondo", lambda ia: ia.jeux_parrondo(phrase=True)),
    (r"braess", "paradoxe de Braess", lambda ia: ia.reseau_braess(phrase=True)),
    (r"allais", "paradoxe d'Allais", lambda ia: ia.paradoxe_allais(phrase=True)),
    (r"ellsberg", "paradoxe d'Ellsberg", lambda ia: ia.paradoxe_ellsberg(phrase=True)),
    (r"no free lunch|pas de repas gratuit|aucun repas gratuit",
     "théorème « no free lunch »", lambda ia: ia.no_free_lunch(phrase=True)),
    (r"saint[- ]?p[ée]tersbourg|petersbourg",
     "paradoxe de Saint-Pétersbourg", lambda ia: ia.prix_loterie_petersbourg(1000, phrase=True)),
    (r"pascal.*mugging|chantage de pascal", "pascal mugging", lambda ia: ia.pascal_mugging(phrase=True)),
    (r"cadrage|framing", "effet de cadrage", lambda ia: ia.effet_de_cadrage(phrase=True)),
    (r"co[ûu]ts? irr[ée]cup[ée]rables?|sunk cost",
     "sophisme des coûts irrécupérables", lambda ia: ia.cout_irrecuperable(100, 20, 80, phrase=True)),
    (r"kelly", "critère de Kelly", lambda ia: ia.mise_kelly(0.6, 2.0, phrase=True)),
]

_DECLENCHE = re.compile(
    r"\b(explique|expliquer|qu['e ]?est[- ]?ce que|c['e ]?est quoi|parle[- ]?moi (?:de|du|des)|d[ée]cris|"
    r"comprendre|paradoxe|sophisme|effet|loi|th[ée]or[èe]me|crit[èe]re)\b", re.I)


def _normalise(s):
    try:
        from base_faits import normalise as _n
        return _n(s)
    except Exception:
        import unicodedata
        s = unicodedata.normalize("NFD", str(s).lower())
        return "".join(c for c in s if unicodedata.category(c) != "Mn")


def explique(texte: str):
    """Explication d'un concept/paradoxe reconnu (str), ou None. Ne se déclenche que si la phrase EXPRIME une
    demande d'explication ET nomme un concept connu -> pas de détournement d'une question factuelle."""
    if not _DECLENCHE.search(texte or ""):
        return None
    bas = _normalise(texte)
    for motif, libelle, appel in _CONCEPTS:
        if re.search(motif, bas):
            try:
                import importlib
                ia = importlib.import_module("ia")
                r = appel(ia)
            except Exception:
                return None
            if not r or "Pas d'analyse" in str(r):
                return None
            return "Le %s : %s" % (libelle, r)
    return None
