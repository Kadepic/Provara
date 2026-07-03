"""
REGISTRE DES SOURCES FIABLES — l'IA connaît OÙ apprendre (donnée, pas code).

Charge `datasets/sources/registry.jsonl` : un catalogue des sources autoritatives (URL, type, domaines
couverts, relations alimentées, note de fiabilité, rate-limit, script d'ingestion). But : si un jour l'IA
est connectée à internet, elle peut PARCOURIR ce registre et ré-ingérer chaque source en AUTONOMIE — au lieu
d'avoir les URLs codées en dur. C'est le pendant « source » du lecteur : le lecteur dit CE QU'ELLE SAIT,
le registre dit D'OÙ elle le tient et OÙ aller en (ré)apprendre.

OFFLINE : pur chargement d'un fichier local, aucun accès réseau (comme le reste du lecteur). Les scripts
`ingere_*.py` lisent ici leur endpoint (`source(id).url`) -> une SEULE source de vérité pour les URLs.
"""
from __future__ import annotations

import json
import os

_FICHIER = os.path.join(os.path.dirname(os.path.abspath(__file__)),
                        "datasets", "sources", "registry.jsonl")


def _charge(fichier: str = _FICHIER) -> list[dict]:
    sources = []
    if not os.path.isfile(fichier):
        return sources
    with open(fichier, encoding="utf-8") as fh:
        for brut in fh:
            brut = brut.strip()
            if not brut:
                continue
            obj = json.loads(brut)
            if "_registre" in obj:                 # en-tête du registre
                continue
            sources.append(obj)
    return sources


SOURCES: list[dict] = _charge()
_PAR_ID: dict[str, dict] = {s["id"]: s for s in SOURCES}


def source(id: str) -> dict | None:
    """La source d'identifiant `id` (ou None). Sert aux scripts d'ingestion à lire leur URL ici."""
    return _PAR_ID.get(id)


def url(id: str) -> str:
    s = _PAR_ID.get(id)
    if s is None or not s.get("url"):
        raise KeyError(f"source inconnue ou sans URL : {id!r}")
    return s["url"]


def toutes(actives_seulement: bool = False) -> list[dict]:
    return [s for s in SOURCES if (s.get("actif", True) or not actives_seulement)]


def pour_domaine(domaine: str) -> list[dict]:
    """Les sources qui couvrent un domaine (ex. 'chimie') — « où l'IA irait apprendre ce domaine »."""
    d = domaine.strip().lower()
    return [s for s in SOURCES if any(d in str(x).lower() for x in s.get("domaines", []))]


def pour_relation(relation: str) -> list[dict]:
    """Les sources qui alimentent une relation (ex. 'capitale') — la provenance d'un type de fait."""
    return [s for s in SOURCES if relation in s.get("relations", [])]


def domaines() -> list[str]:
    d = set()
    for s in SOURCES:
        d.update(s.get("domaines", []))
    return sorted(d)


if __name__ == "__main__":
    print(f"=== REGISTRE DES SOURCES ({len(SOURCES)} sources, {len(domaines())} domaines) ===\n")
    for s in SOURCES:
        etat = "actif" if s.get("actif", True) else "réserve"
        print(f"  [{etat:7s}] {s['id']:22s} {s.get('type',''):7s} — {', '.join(s.get('domaines', []))}")
        print(f"            {s.get('url','')}")
    print("\n  Où apprendre la chimie ? ->", [s["id"] for s in pour_domaine("chimie")])
    print("  D'où vient 'capitale' ?  ->", [s["id"] for s in pour_relation("capitale")])
