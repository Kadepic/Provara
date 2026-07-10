"""
INGESTION P8283 — élargir l'ALIGNEMENT ISCO, le levier commun des chaînes métier (mandat « traiter tout le
backlog », 2026-07-12, après l'ouverture des 5 axes : la frontière n'est plus les sources, c'est
l'alignement — chaque métier gagné ici débloque rémunération, outils ET risques d'un coup).

LA PROPRIÉTÉ, ET LE PIÈGE DE MILLÉSIME PAYÉ POUR L'APPRENDRE. Wikidata a DEUX propriétés de code ISCO :
  • **P952 = ISCO-88** (l'ancienne nomenclature). Sondée d'abord : « acteur de cinéma -> 2455 »,
    « acrobate -> 3474 » — des codes ISCO-88. Les injecter dans la chaîne BLS (crosswalk ISCO-08→SOC)
    aurait été un FAUX SYSTÉMATIQUE silencieux : mêmes formes à 4 chiffres, sens différents.
  • **P8283 = ISCO-08**. C'est elle, et elle seule, qu'on ingère (937 items typés occupation).
Vérifié aux ancres : acteur de cinéma -> 2655, agent immobilier -> 3334, agent de voyages -> 4221 (ISCO-08).

LA JOINTURE EST PAR QID, PAS PAR LIBELLÉ : l'oracle `est_metier` porte le(s) QID de chaque libellé — aucun
appariement de chaînes, aucune variante, aucun flou. C'est l'alignement le plus direct du projet.

FAUX=0 — les gardes (chacune a son faux mesuré) :
  1. GARDE DE TYPE : la même que l'oracle (`P31/P279* Q28640`, patronymes et prénoms exclus).
  2. **MONO-QID SEULEMENT.** Un libellé porté par PLUSIEURS QID est un homonyme : le code peut venir du
     MAUVAIS sens. Mesuré : « compositeur » (musique, ISCO 2652) prenait 7321 (« compositeur »
     typographe) parce que seul l'item typographie porte P8283. 25 homonymes écartés.
  3. MULTI-GROUPES : un item dont les codes P8283 pointent plusieurs groupes à 4 chiffres est écarté.
  4. HORS-ESCO SEULEMENT : les métiers déjà dans `code_isco_metier` (ESCO) n'y entrent pas — une seule
     source par métier, le désaccord éventuel est géré par le LECTEUR de chaîne (`_isco_du_store`,
     désaccord -> métier écarté et compté ; 25 conflits ESCO/P8283 mesurés sur le chevauchement, dont
     des homonymies et des classements défendables des deux côtés : au doute, HORS).

UNE RELATION : `code_isco_p8283_metier` — métier -> groupe ISCO-08 (4 chiffres). Consommée par
`ingere_bls_oes._isco_du_store()` en FUSION avec la table ESCO ; re-publier ensuite OES, O*NET et SOII.

Usage :
    python3 ingestion/ingere_isco_wikidata.py moissonne    # 1 requête QLever
    python3 ingestion/ingere_isco_wikidata.py publie       # hors ligne, depuis le snapshot
"""
from __future__ import annotations

import collections
import json
import os
import re
import sys
import time
import urllib.parse
import urllib.request

from ingere_wikidata import RAW, charge_raw_json, publie, snapshot_brut

ENDPOINT = "https://qlever.dev/api/wikidata"
UA = "Provara/1.0 (https://github.com/Provara-IA/Provara) offline-knowledge-ingestion"
SNAPSHOT = os.path.join(RAW, "isco_p8283.json")

# La MÊME garde de type que l'oracle est_metier. P8283 = ISCO-08 ; P952 (ISCO-88) est un PIÈGE.
_REQUETE = ("PREFIX wdt: <http://www.wikidata.org/prop/direct/> "
            "PREFIX wd: <http://www.wikidata.org/entity/> "
            "SELECT ?o ?code WHERE { ?o wdt:P8283 ?code . ?o wdt:P31/wdt:P279* wd:Q28640 . "
            "FILTER NOT EXISTS { ?o wdt:P31 wd:Q101352 } FILTER NOT EXISTS { ?o wdt:P31 wd:Q202444 } }")

SRC = ("Wikidata/QLever — P8283 (code ISCO-08 ; JAMAIS P952, qui est l'ISCO-88 : « acteur -> 2455 » y est "
       "un code 88, l'injecter dans une chaîne ISCO-08 serait un faux silencieux), items typés occupation "
       "(P31/P279* Q28640). Jointure par QID via l'oracle est_metier — aucun appariement de libellés. "
       "MONO-QID seulement : un libellé homonyme peut tenir son code du mauvais sens (mesuré : "
       "« compositeur » musique prenait le 7321 du compositeur-typographe). Groupe à 4 chiffres.")


def _qlever(requete: str, timeout: int = 300, essais: int = 6) -> list:
    url = ENDPOINT + "?action=json_export&query=" + urllib.parse.quote(requete)
    for k in range(essais):
        try:
            req = urllib.request.Request(url, headers={"User-Agent": UA, "Accept": "application/json"})
            with urllib.request.urlopen(req, timeout=timeout) as r:
                charge = json.loads(r.read().decode("utf-8"))
            return charge.get("results", {}).get("bindings", [])
        except (OSError, json.JSONDecodeError):
            if k == essais - 1:
                raise
            time.sleep(4 * (k + 1))
    return []


def moissonne() -> None:
    print("== MOISSONNAGE P8283 (codes ISCO-08 des occupations Wikidata) ==")
    lignes = _qlever(_REQUETE)
    if len(lignes) < 500:
        raise ValueError("P8283 suspect : %d lignes (937 attendues à ±30 %%) — refus de cacher un résultat "
                         "tronqué" % len(lignes))
    brut = [{"qid": r["o"]["value"].rsplit("/", 1)[-1], "code": r["code"]["value"]} for r in lignes]
    snapshot_brut("isco_p8283", brut)
    print("  %d lignes -> %s" % (len(brut), SNAPSHOT))


def groupes_par_qid(brut: list) -> dict:
    """QID -> {groupes ISCO-08 à 4 chiffres}. Un code qui ne COMMENCE pas par 4 chiffres est écarté."""
    table = collections.defaultdict(set)
    for r in brut:
        m = re.match(r"^(\d{4})", (r.get("code") or "").strip())
        if m and r.get("qid"):
            table[r["qid"]].add(m.group(1))
    return table


def aligne(par_qid: dict, lab2qids: dict, metiers: list, deja: set):
    """metier -> groupe, sous les gardes 2-4. Renvoie (appariés, homonymes écartés, multi écartés)."""
    apparie, homonymes, multi = {}, 0, 0
    for m in metiers:
        if m in deja:                                                  # GARDE 4 : une source par métier
            continue
        qids = lab2qids.get(m, [])
        groupes = set().union(*[par_qid.get(q, set()) for q in qids]) if qids else set()
        if not groupes:
            continue
        if len(qids) > 1:                                              # GARDE 2 : homonyme -> mauvais sens
            homonymes += 1
            continue
        if len(groupes) > 1:                                           # GARDE 3
            multi += 1
            continue
        apparie[m] = next(iter(groupes))
    return apparie, homonymes, multi


def publie_depuis_cache() -> None:
    print("== P8283 — élargissement de l'alignement ISCO (jointure par QID) ==")
    brut = charge_raw_json(SNAPSHOT)
    if brut is None:
        raise SystemExit("snapshot absent : %s — lancer : python3 ingestion/ingere_isco_wikidata.py "
                         "moissonne" % SNAPSHOT)
    par_qid = groupes_par_qid(brut)
    print("  %d items occupation avec P8283" % len(par_qid))

    dossier = os.environ.get("LECTEUR_DATASETS_DIR",
                             os.path.join(os.path.expanduser("~"), ".verax", "datasets", "lecteur"))
    lab2qids = {}
    with open(os.path.join(dossier, "est_metier.jsonl"), encoding="utf-8") as fh:
        for ligne in fh:
            if ligne.startswith('{"_relation"'):
                continue
            o = json.loads(ligne)
            lab2qids[o["entite"]] = [q.strip() for q in o["valeur"].split(",")]
    deja = set()
    with open(os.path.join(dossier, "code_isco_metier.jsonl"), encoding="utf-8") as fh:
        for ligne in fh:
            if not ligne.startswith('{"_relation"'):
                deja.add(json.loads(ligne)["entite"])

    sys.path.insert(0, os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "outils"))
    from genere_sujets import metiers_de_la_carte
    metiers, _, _ = metiers_de_la_carte()

    apparie, homonymes, multi = aligne(par_qid, lab2qids, metiers, deja)
    print("  nouveaux métiers alignés : %d | homonymes écartés : %d | multi-groupes écartés : %d"
          % (len(apparie), homonymes, multi))
    if len(apparie) < 200:
        raise ValueError("alignement suspect : %d métiers (347 attendus à ±40 %%) — gardes à réauditer"
                         % len(apparie))
    publie("code_isco_p8283_metier", "convention", SRC, sorted(apparie.items()))


if __name__ == "__main__":
    mode = sys.argv[1] if len(sys.argv) > 1 else "publie"
    if mode == "moissonne":
        moissonne()
    elif mode == "publie":
        publie_depuis_cache()
    else:
        raise SystemExit("usage : ingere_isco_wikidata.py [moissonne|publie]")
