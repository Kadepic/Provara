# -*- coding: utf-8 -*-
"""APPRENTISSAGE DE PATRONS CONVERSATIONNELS — apprendre des reformulations de l'utilisateur, FAUX=0 (2026-07-03).

POURQUOI (mandat Yohan « apprentissage des patrons depuis les conversations ») : quand VERAX ne comprend pas une
formulation (abstention) et que l'utilisateur REFORMULE une question à laquelle VERAX répond alors correctement,
la 1re formulation et la 2e portent sur le MÊME sujet. On APPREND l'alias : la formulation ratée -> la formulation
réussie. La prochaine fois, la formulation ratée est re-routée vers celle qui marche.

FAUX=0 — ce que ça garantit :
  • L'alias ne fait que RÉ-ROUTER une formulation vers une autre ; il n'invente JAMAIS un fait (la réponse
    ressort du pipeline normal, vérifiée comme toujours).
  • On n'apprend QUE si la reformulation a RÉELLEMENT réussi (réponse non-abstention) ET si les deux formulations
    PARTAGENT un mot de contenu significatif (même sujet) — sinon on n'apprend rien (pas d'alias hasardeux).
  • Souverain, persistant localement, déterministe. Effaçable (RGPD-friendly).
"""
from __future__ import annotations

import json
import os

try:
    from base_faits import normalise as _normalise
except Exception:
    def _normalise(s):
        import unicodedata
        s = unicodedata.normalize("NFD", str(s).lower())
        return "".join(c for c in s if unicodedata.category(c) != "Mn")

_MOTS_OUTILS = frozenset(
    "quel quelle quels quelles est sont le la les l un une des du de d au aux et en dans sur qui que quoi ou "
    "comment combien pourquoi quand donne moi dis peux tu me ce cette a je j ai avec pour par plus tres bien "
    "veux voudrais aimerais cherche trouve sais connais explique parle raconte".split())


def _mots_contenu(texte: str):
    return {m for m in _normalise(texte).split() if len(m) >= 3 and m not in _MOTS_OUTILS}


def _dossier():
    base = os.environ.get("VERAX_PATRONS_DIR")
    if not base:
        base = os.path.join(os.path.expanduser("~"), ".verax")
    try:
        os.makedirs(base, exist_ok=True)
    except OSError:
        pass
    return os.path.join(base, "patrons_appris.json")


_CACHE = None


def _charge() -> dict:
    global _CACHE
    if _CACHE is not None:
        return _CACHE
    _CACHE = {}
    try:
        with open(_dossier(), encoding="utf-8") as f:
            d = json.load(f)
            if isinstance(d, dict):
                _CACHE = d
    except (OSError, ValueError):
        pass
    return _CACHE


def _sauve():
    tmp = _dossier() + ".tmp.%d" % os.getpid()
    try:
        with open(tmp, "w", encoding="utf-8") as f:
            json.dump(_CACHE, f, ensure_ascii=False)
        os.replace(tmp, _dossier())
    except OSError:
        pass


def enregistre(echec_texte: str, succes_texte: str) -> bool:
    """Apprend « echec_texte -> succes_texte » SI les deux partagent un mot de contenu (même sujet) et diffèrent.
    Renvoie True si un alias a été appris. Sound : on ne stocke qu'un ré-aiguillage de formulation."""
    e, s = (echec_texte or "").strip(), (succes_texte or "").strip()
    if not e or not s:
        return False
    ke, ks = _normalise(e), _normalise(s)
    if ke == ks:
        return False
    if not (_mots_contenu(e) & _mots_contenu(s)):     # sujet partagé exigé -> pas d'alias hasardeux
        return False
    d = _charge()
    if d.get(ke) == s:
        return False
    d[ke] = s
    _sauve()
    return True


def alias(texte: str):
    """Reformulation apprise pour `texte` (ou None). Ne renvoie jamais le texte identique (pas de boucle)."""
    s = _charge().get(_normalise(texte or ""))
    if s and _normalise(s) != _normalise(texte or ""):
        return s
    return None


def oublie(texte: str | None = None) -> int:
    """Efface un alias (par sa clé) ou TOUT (texte=None). Renvoie le nombre d'alias supprimés (RGPD)."""
    d = _charge()
    if texte is None:
        n = len(d)
        d.clear()
        _sauve()
        return n
    k = _normalise(texte)
    if k in d:
        del d[k]
        _sauve()
        return 1
    return 0


def nombre_appris() -> int:
    return len(_charge())
