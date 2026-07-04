# -*- coding: utf-8 -*-
"""SYSTÈME DE CONFIANCE — l'utilisateur est un JUGE RÉEL, les sources se bannissent, FAUX=0 (2026-07-03).

POURQUOI (mission Yohan « système de confiance ») : au-delà de rapporter des sources, Provara doit (1) tenir pour
AUTORITÉ les corrections de l'utilisateur (« c'est faux, c'est X ») — l'utilisateur est une confrontation à la
réalité, un juge ; (2) BANNIR une source sur ordre (« oublie ce site ») ; (3) s'appuyer sur la CONCORDANCE de
plusieurs sources indépendantes (déléguée à veille_corroboration).

FAUX=0 — invariants :
  • Une correction utilisateur est APPLIQUÉE telle quelle et ATTRIBUÉE (« tu me l'as corrigé »), jamais mélangée
    à une vérité inventée ; elle PRIME sur le web (l'utilisateur juge). Effaçable (RGPD).
  • Le bannissement d'une source la retire des recherches futures — jamais rétabli en douce.
  • Souverain, persistant localement, déterministe.
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


def _fichier():
    base = os.environ.get("VERAX_CONFIANCE_DIR") or os.path.join(os.path.expanduser("~"), ".verax")
    try:
        os.makedirs(base, exist_ok=True)
    except OSError:
        pass
    return os.path.join(base, "confiance.json")


_CACHE = None


def _charge() -> dict:
    global _CACHE
    if _CACHE is not None:
        return _CACHE
    _CACHE = {"corrections": {}, "sources_bannies": []}
    try:
        with open(_fichier(), encoding="utf-8") as f:
            d = json.load(f)
            if isinstance(d, dict):
                _CACHE["corrections"] = d.get("corrections", {}) or {}
                _CACHE["sources_bannies"] = d.get("sources_bannies", []) or []
    except (OSError, ValueError):
        pass
    return _CACHE


def _sauve():
    tmp = _fichier() + ".tmp.%d" % os.getpid()
    try:
        with open(tmp, "w", encoding="utf-8") as f:
            json.dump(_CACHE, f, ensure_ascii=False)
        os.replace(tmp, _fichier())
    except OSError:
        pass


# ————————————————————————— CORRECTIONS UTILISATEUR (exigent une SOURCE) —————————————————————————
# FAUX=0 : une correction NUE (« c'est faux, c'est Toulouse ») ne peut PAS écraser une vérité — sinon
# l'utilisateur injecterait des faussetés. Elle exige une SOURCE (référence citée), et Provara la conserve comme
# provenance : la réponse rendue est ATTRIBUÉE à CETTE source (« d'après la source que tu m'as indiquée »),
# jamais présentée comme la vérité vérifiée de Provara.
def corrige(question: str, valeur: str, source: str) -> bool:
    """Enregistre la correction de l'utilisateur AVEC sa source (obligatoire). `valeur` = la réponse indiquée ;
    `source` = la référence citée (lien/nom). Renvoie True si stockée. Sans source -> refusé."""
    q, v, s = _normalise(question or ""), (valeur or "").strip(), (source or "").strip()
    if not q or not v or not s:
        return False
    d = _charge()
    d["corrections"][q] = {"valeur": v, "source": s}
    _sauve()
    return True


def reponse_autorisee(question: str):
    """Correction SOURCÉE de l'utilisateur pour cette question : {'valeur', 'source'} ou None. La réponse rendue
    est attribuée à la source indiquée (jamais présentée comme la vérité vérifiée de Provara)."""
    e = _charge()["corrections"].get(_normalise(question or ""))
    if isinstance(e, dict) and e.get("valeur") and e.get("source"):
        return dict(e)
    return None


def oublie_correction(question: str | None = None) -> int:
    """Efface une correction (par question) ou TOUTES (question=None). Renvoie le nombre supprimé (RGPD)."""
    d = _charge()
    if question is None:
        n = len(d["corrections"])
        d["corrections"] = {}
        _sauve()
        return n
    k = _normalise(question)
    if k in d["corrections"]:
        del d["corrections"][k]
        _sauve()
        return 1
    return 0


# ————————————————————————— SOURCES BANNIES (« oublie ce site ») —————————————————————————
def _dom(domaine: str) -> str:
    d = (domaine or "").strip().lower()
    for p in ("https://", "http://", "www."):
        if d.startswith(p):
            d = d[len(p):]
    return d.split("/")[0].strip()


def bannis_source(domaine: str) -> bool:
    """Bannit un domaine : il ne sera plus consulté dans les recherches. Renvoie True si nouvellement banni."""
    dom = _dom(domaine)
    if not dom:
        return False
    d = _charge()
    if dom in d["sources_bannies"]:
        return False
    d["sources_bannies"].append(dom)
    _sauve()
    return True


def est_bannie(domaine: str) -> bool:
    """True si le domaine (ou un domaine parent) est banni."""
    dom = _dom(domaine)
    return any(dom == b or dom.endswith("." + b) for b in _charge()["sources_bannies"])


def sources_bannies() -> list:
    return list(_charge()["sources_bannies"])


def retablis_source(domaine: str) -> bool:
    """Ré-autorise un domaine banni. Renvoie True si retiré de la liste."""
    dom = _dom(domaine)
    d = _charge()
    if dom in d["sources_bannies"]:
        d["sources_bannies"].remove(dom)
        _sauve()
        return True
    return False


def oublie(tout: bool = True) -> None:
    """RGPD : efface corrections ET bannissements."""
    d = _charge()
    d["corrections"] = {}
    d["sources_bannies"] = []
    _sauve()
