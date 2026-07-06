"""
FAITS APPRIS DU WEB — mémoire locale PERSISTANTE des faits STRUCTURÉS trouvés en ligne (2026-07-06, demande Yohan
« que mon IA APPRENNE les faits structurés qu'elle trouve en ligne, réutilisables hors-ligne »).

Quand Provara résout un fait sur une source STRUCTURÉE de confiance (Wikidata, extraction SPARQL déterministe via
veille_structure.interroge_nl), il l'APPREND : il le range en local (~/.verax), typé SOURCE + DATE, pour le
resservir sans re-interroger le web — et même hors-ligne.

FRONTIÈRE FAUX=0 (STRICTE, non négociable) :
  • SEULS les faits STRUCTURÉS sont appris (une source déterministe et attribuable les a rendus). Le texte libre
    (Wikipédia, métamoteur) reste « RAPPORTÉ », JAMAIS appris — il n'entre pas ici.
  • Un fait resservi est TOUJOURS attribué ET daté (« appris de Wikidata le 2026-07-06 ») : c'est un INSTANTANÉ
    honnête (le monde peut avoir changé depuis), pas une vérité intemporelle de Provara.
  • On n'apprend jamais une valeur vide ; le dernier apprentissage d'une clé fait foi (rafraîchissement naturel).

Stockage : JSONL append-only dans <VERAX_HOME|~/.verax>/faits_appris.jsonl (une ligne = un fait daté). Lecture
« dernier gagnant » par clé normalisée. Stdlib pur, souverain. Chemin surchargeable (FAITS_APPRIS_PATH) pour les
tests isolés ; horloge injectable (_HORLOGE) pour un test déterministe.
"""
from __future__ import annotations

import json
import os
import time

from base_faits import normalise as _normalise

# Horloge injectable (tests) : rend la date du jour "AAAA-MM-JJ". Défaut = horloge réelle.
_HORLOGE = lambda: time.strftime("%Y-%m-%d")


def _chemin() -> str:
    """Fichier des faits appris. FAITS_APPRIS_PATH surcharge (tests) ; sinon <VERAX_HOME|~/.verax>/…"""
    p = os.environ.get("FAITS_APPRIS_PATH")
    if p:
        return p
    base = os.environ.get("VERAX_HOME") or os.path.join(os.path.expanduser("~"), ".verax")
    try:
        os.makedirs(base, exist_ok=True)
    except OSError:
        pass
    return os.path.join(base, "faits_appris.jsonl")


def _cle(attribut: str, entite: str) -> str:
    """Clé normalisée (sans accents/casse) d'un couple (attribut, entité) — l'unité d'un fait appris."""
    return "%s\x1f%s" % (" ".join(_normalise(attribut).split()), " ".join(_normalise(entite).split()))


def apprend(attribut: str, entite: str, valeur, source: str, date: str | None = None) -> bool:
    """Range un fait STRUCTURÉ vérifié (source attribuable). Append-only : le plus récent d'une clé fait foi.
    N'apprend JAMAIS une valeur vide ni un fait sans source (garde FAUX=0). Renvoie True si écrit."""
    val = "" if valeur is None else str(valeur).strip()
    attribut = (attribut or "").strip()
    entite = (entite or "").strip()
    source = (source or "").strip()
    if not (val and attribut and entite and source):
        return False
    ligne = {"attribut": attribut, "entite": entite, "valeur": val, "source": source,
             "date": date or _HORLOGE()}
    try:
        with open(_chemin(), "a", encoding="utf-8") as f:
            f.write(json.dumps(ligne, ensure_ascii=False) + "\n")
        return True
    except OSError:
        return False


def rappelle(attribut: str, entite: str) -> dict | None:
    """Le fait appris pour (attribut, entité), ou None. « Dernier gagnant » : on lit tout et on garde la
    DERNIÈRE ligne de la clé (rafraîchissement naturel sans réécriture). Robuste aux lignes corrompues."""
    cible = _cle(attribut, entite)
    trouve = None
    try:
        with open(_chemin(), encoding="utf-8") as f:
            for ligne in f:
                ligne = ligne.strip()
                if not ligne:
                    continue
                try:
                    o = json.loads(ligne)
                except ValueError:
                    continue
                if _cle(o.get("attribut", ""), o.get("entite", "")) == cible and o.get("valeur"):
                    trouve = o
    except OSError:
        return None
    return trouve


def rappelle_texte(attribut: str, entite: str) -> str | None:
    """Le fait appris FORMATÉ, attribué et daté (« … — appris de Wikidata le 2026-07-06 »), ou None. La
    provenance et la date sont TOUJOURS montrées : un fait appris est un instantané honnête, pas une vérité
    intemporelle de Provara."""
    o = rappelle(attribut, entite)
    if not o:
        return None
    return "%s  (appris de %s le %s)" % (o["valeur"], o.get("source", "?"), o.get("date", "?"))


def nombre_appris() -> int:
    """Nombre de faits DISTINCTS appris (clés uniques) — pour le diagnostic. 0 si rien/illisible."""
    cles = set()
    try:
        with open(_chemin(), encoding="utf-8") as f:
            for ligne in f:
                ligne = ligne.strip()
                if not ligne:
                    continue
                try:
                    o = json.loads(ligne)
                except ValueError:
                    continue
                if o.get("valeur"):
                    cles.add(_cle(o.get("attribut", ""), o.get("entite", "")))
    except OSError:
        return 0
    return len(cles)
