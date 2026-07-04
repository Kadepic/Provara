# -*- coding: utf-8 -*-
"""APPRENTISSAGE DE PATRONS CONVERSATIONNELS — apprendre des reformulations de l'utilisateur, FAUX=0 (2026-07-03).

POURQUOI (mandat Yohan « apprentissage des patrons depuis les conversations ») : quand Provara ne comprend pas une
formulation (abstention) et que l'utilisateur REFORMULE une question à laquelle Provara répond alors correctement,
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


def _induit_substitution(echec: str, succes: str):
    """INDUCTION DE RÈGLE : si `echec` et `succes` ne diffèrent que par UN mot de contenu (« chef-lieu » vs
    « capitale », tout le reste identique), on induit la substitution mot->mot, qui GÉNÉRALISE au-delà de la
    phrase (« chef-lieu du Japon » profitera de « chef-lieu -> capitale »). Renvoie (avant, apres) ou None.
    Sound : substitution de FORMULATION seulement ; la réponse reste vérifiée par le pipeline."""
    te, ts = _normalise(echec).split(), _normalise(succes).split()
    # mots de CONTENU propres à chacun (dans l'ordre) — le reste (mots-outils, sujet partagé) doit coïncider
    ce = [w for w in te if len(w) >= 3 and w not in _MOTS_OUTILS and w not in ts]
    cs = [w for w in ts if len(w) >= 3 and w not in _MOTS_OUTILS and w not in te]
    if 1 <= len(ce) <= 3 and 1 <= len(cs) <= 2 and ce != cs:
        return " ".join(ce), " ".join(cs)
    return None


def enregistre(echec_texte: str, succes_texte: str) -> bool:
    """Apprend « echec_texte -> succes_texte » SI les deux partagent un mot de contenu (même sujet) et diffèrent.
    Apprend AUSSI, quand c'est net, une RÈGLE DE SUBSTITUTION de mot (généralisable). Sound : ré-aiguillage seul.
    Renvoie True si un alias OU une substitution a été appris."""
    e, s = (echec_texte or "").strip(), (succes_texte or "").strip()
    if not e or not s:
        return False
    ke, ks = _normalise(e), _normalise(s)
    if ke == ks:
        return False
    if not (_mots_contenu(e) & _mots_contenu(s)):     # sujet partagé exigé -> pas d'alias hasardeux
        return False
    d = _charge()
    change = False
    if d.get(ke) != s:
        d[ke] = s
        change = True
    sub = _induit_substitution(e, s)                  # règle généralisable
    if sub:
        subs = d.setdefault("__subs__", {})
        if subs.get(sub[0]) != sub[1]:
            subs[sub[0]] = sub[1]
            change = True
    if change:
        _sauve()
    return change


def alias(texte: str):
    """Reformulation apprise pour `texte` (ou None). D'abord l'alias EXACT (phrase entière), sinon on applique
    une RÈGLE DE SUBSTITUTION apprise (généralise à de nouvelles phrases). Jamais le texte identique."""
    d = _charge()
    k = _normalise(texte or "")
    s = d.get(k)
    if s and _normalise(s) != k:
        return s
    # substitution généralisable : remplace une SÉQUENCE apprise (« chef lieu » -> « capitale ») dans la phrase
    subs = d.get("__subs__") or {}
    for avant, apres in sorted(subs.items(), key=lambda kv: -len(kv[0])):   # séquences longues d'abord
        if avant and (" " + avant + " ") in (" " + k + " "):
            cand = (" " + k + " ").replace(" " + avant + " ", " " + apres + " ").strip()
            if cand != k:
                return cand
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
    n = 0
    if k in d:
        del d[k]
        n += 1
    subs = d.get("__subs__") or {}                    # retire aussi les substitutions dérivées de ce texte (RGPD)
    for avant in [a for a in subs if (" " + a + " ") in (" " + k + " ")]:
        del subs[avant]
        n += 1
    if not subs and "__subs__" in d:
        del d["__subs__"]
    if n:
        _sauve()
    return n


def nombre_appris() -> int:
    """Nombre d'alias de phrase appris (hors table de substitutions)."""
    return sum(1 for k in _charge() if k != "__subs__")


def substitutions_apprises() -> dict:
    """Règles de substitution de mot induites (avant -> après)."""
    return dict(_charge().get("__subs__") or {})
