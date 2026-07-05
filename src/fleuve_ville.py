# -*- coding: utf-8 -*-
"""FLEUVES ↔ VILLES TRAVERSÉES — seed curé à la main (fleuve_ville_seed.jsonl).

Les datasets Wikidata n'ont AUCUNE relation ville↔fleuve (vérifié : subdivision_riviere ne contient pas Paris,
pays_riviere donne le pays, bassin_fleuve le bassin). Ce module comble le trou avec des couples géographiques
incontestables (la Seine traverse Paris, le Tibre traverse Rome…), curés comme est_un_seed.jsonl.

FAUX=0 :
- une VILLE du seed est réputée COMPLÈTE pour ses fleuves MAJEURS (Lyon = Rhône + Saône) -> « quel fleuve
  traverse Lyon » répond la liste entière ;
- un FLEUVE n'est PAS exhaustif (la Seine traverse bien plus que Paris et Rouen) -> les réponses inverses
  disent « notamment » ;
- une paire absente n'est JAMAIS niée sèchement : on montre le fait réel connu (« d'après mes données, Paris
  est traversée par la Seine — aucun fait pour la Bièvre ») car un petit cours d'eau absent du seed peut
  réellement traverser la ville.
"""
import json
import os
import unicodedata

_SEED = None      # (par_ville, par_fleuve) — {clé_norm : (affiché, [affichés liés…])}


def _sans_accent(s: str) -> str:
    return "".join(c for c in unicodedata.normalize("NFD", s) if unicodedata.category(c) != "Mn")


def _norm(s: str) -> str:
    """clé de jointure : minuscules, sans accent, sans article de tête (« Le Caire » -> « caire »)."""
    n = _sans_accent(str(s).lower()).strip()
    for art in ("le ", "la ", "les ", "l'", "l’"):
        if n.startswith(art):
            n = n[len(art):]
            break
    return n.strip()


def _seed():
    global _SEED
    if _SEED is None:
        par_ville, par_fleuve = {}, {}
        chemin = os.path.join(os.path.dirname(os.path.abspath(__file__)), "fleuve_ville_seed.jsonl")
        try:
            with open(chemin, encoding="utf-8") as fh:
                for ligne in fh:
                    ligne = ligne.strip()
                    if not ligne:
                        continue
                    try:
                        o = json.loads(ligne)
                    except ValueError:
                        continue
                    f, v = o.get("fleuve"), o.get("ville")
                    if not f or not v or "_relation" in o:
                        continue
                    cv, cf = _norm(v), _norm(f)
                    par_ville.setdefault(cv, (v, []))[1].append(f)
                    par_fleuve.setdefault(cf, (f, []))[1].append(v)
        except OSError:
            pass
        _SEED = (par_ville, par_fleuve)
    return _SEED


def fleuves_de(ville: str):
    """(ville_affichée, [fleuves affichés avec article]) ou None. Liste complète pour les fleuves majeurs."""
    cell = _seed()[0].get(_norm(ville))
    return (cell[0], list(cell[1])) if cell else None


def villes_de(fleuve: str):
    """(fleuve_affiché, [villes affichées]) ou None. NON exhaustif (dire « notamment »)."""
    cell = _seed()[1].get(_norm(fleuve))
    return (cell[0], list(cell[1])) if cell else None


def traverse(fleuve: str, ville: str):
    """True si la paire est un fait curé ; None si inconnue (ne JAMAIS conclure « non » : seed non exhaustif
    côté petits cours d'eau)."""
    cell = _seed()[0].get(_norm(ville))
    if not cell:
        return None
    return True if any(_norm(f) == _norm(fleuve) for f in cell[1]) else None
