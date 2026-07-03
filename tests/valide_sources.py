"""
VALIDATION du REGISTRE DES SOURCES (`sources.py` / datasets/sources/registry.jsonl).

Verrouille les invariants qui rendent le registre EXPLOITABLE par un futur mode en ligne autonome :
  1. STRUCTURE : chaque source porte id (unique), nom, type, une note d'AUTORITÉ (fiabilité) et ≥1 domaine.
  2. URL : toute source ACTIVE a une URL exploitable ; `sources.url(id)` la rend ; id inconnu -> KeyError.
  3. REQUÊTABILITÉ : pour_domaine / pour_relation renvoient les bonnes sources (l'IA sait OÙ apprendre).
  4. COHÉRENCE LECTEUR : les relations annoncées par la source géo active sont RÉELLEMENT chargées dans le
     lecteur -> le registre ne ment pas sur ce qu'il a permis d'apprendre.
"""
from __future__ import annotations

from garde_ressources import borne

import sources as S
import lecteur as L

borne(max_go=4.0, max_cpu_s=900)   # charge tout le lecteur (~10 M faits) : CPU 120s défaut tuait (SIGXCPU)
ok = 0
total = 0


def check(nom, cond):
    global ok, total
    total += 1
    print(f"  [{'OK ' if cond else 'XXX'}] {nom}")
    if cond:
        ok += 1
    else:
        raise AssertionError(nom)


check("registre non vide", len(S.SOURCES) >= 1)

# 1) STRUCTURE
ids = [s.get("id") for s in S.SOURCES]
check("ids tous présents et uniques", all(ids) and len(set(ids)) == len(ids))
for s in S.SOURCES:
    check(f"structure {s.get('id')!r} : nom+type+autorité+≥1 domaine",
          isinstance(s.get("nom"), str) and s.get("nom", "").strip() != ""
          and isinstance(s.get("type"), str) and s.get("type", "").strip() != ""
          and isinstance(s.get("autorite"), str) and len(s.get("autorite", "")) > 10
          and isinstance(s.get("domaines"), list) and len(s.get("domaines", [])) >= 1)

# 2) URL des sources actives + accès par id
for s in S.toutes(actives_seulement=True):
    check(f"source active {s['id']} a une URL", isinstance(s.get("url"), str) and s["url"].startswith("http"))
    check(f"sources.url({s['id']}) == champ url", S.url(s["id"]) == s["url"])
try:
    S.url("source-qui-nexiste-pas")
    check("url(inconnu) -> KeyError", False)
except KeyError:
    check("url(inconnu) -> KeyError", True)

# 3) REQUÊTABILITÉ — l'IA sait où apprendre un domaine / d'où vient une relation.
check("pour_domaine('chimie') inclut wikidata", "wikidata-wdqs" in [s["id"] for s in S.pour_domaine("chimie")])
check("pour_domaine('géographie') inclut mledoze", "mledoze-countries" in [s["id"] for s in S.pour_domaine("géographie")])
check("pour_relation('code_iso_pays') inclut mledoze", "mledoze-countries" in [s["id"] for s in S.pour_relation("code_iso_pays")])
check("pour_domaine(inconnu) -> []", S.pour_domaine("licorne-quantique") == [])
check("domaines() non vide et trié", S.domaines() == sorted(S.domaines()) and len(S.domaines()) >= 1)

# 4) COHÉRENCE LECTEUR — la source géo active a bien fait charger ses relations neutres.
geo = S.source("mledoze-countries")
if geo is not None and geo.get("actif", True):
    for rel in geo.get("relations", []):
        check(f"relation annoncée '{rel}' réellement chargée dans le lecteur", rel in L.LECTEUR.tables)

print(f"\n=== valide_sources : {ok}/{total} ===")
assert ok == total
