"""
INGESTION O*NET JOB ZONES — l'axe « niveau de préparation requise » d'un métier (mandat couverture, 2026-07-12).

Un attribut métier STANDARD qu'aucun des 8 axes existants ne portait : le NIVEAU de préparation (formation +
expérience + apprentissage sur le tas) qu'exige l'accès à l'occupation, sur l'échelle O*NET des Job Zones :
  1 — peu ou pas de préparation      4 — préparation considérable
  2 — préparation légère             5 — préparation extensive
  3 — préparation moyenne
C'est distinct de l'axe « formation, diplômes » (RNCP : des CERTIFICATIONS nommées) : ici c'est le NIVEAU
global, une ordinale comparable entre métiers.

LA CHAÎNE — la même que rémunération/outils/risques (maillons d'`ingere_bls_oes` RÉUTILISÉS) :
  métier -> groupe ISCO-08 (ESCO/P8283, store) -> SOC 2010 -> SOC 2018 -> Job Zone(s) O*NET.

CE QUE LA TABLE AFFIRME : les Job Zones que O*NET attribue aux occupations SOC 2018 du GROUPE ISCO du métier
— granularité DITE (occupation SOC, pas le métier précis). Un groupe couvre plusieurs SOC ; leurs zones
peuvent différer, on les liste toutes (dédoublonnées, triées), avec le libellé du référentiel O*NET. Part
MIX -> PARTIEL : O*NET décrit le marché du travail AMÉRICAIN ; le niveau de préparation d'un métier ailleurs
n'est pas borné par ce seul référentiel.

CACHE : `datasets/_raw/onet_job_zones.xlsx` + `onet_job_zone_reference.xlsx` (db_30_0 O*NET, CC BY 4.0).

Usage :
    python3 ingestion/ingere_onet_jobzones.py moissonne     # 2 fichiers O*NET (~48 Ko)
    python3 ingestion/ingere_onet_jobzones.py publie        # hors ligne, depuis le cache
"""
from __future__ import annotations

import collections
import os
import re
import sys

from ingere_bls_oes import (RAW, _isco_du_store, _telecharge, isco_vers_soc2010, lit_xlsx,
                            soc2010_vers_2018)
from ingere_wikidata import publie

URL_JZ = "https://www.onetcenter.org/dl_files/database/db_30_0_excel/Job%20Zones.xlsx"
URL_JZREF = "https://www.onetcenter.org/dl_files/database/db_30_0_excel/Job%20Zone%20Reference.xlsx"
CACHE_JZ = os.path.join(RAW, "onet_job_zones.xlsx")
CACHE_JZREF = os.path.join(RAW, "onet_job_zone_reference.xlsx")

SRC = ("O*NET 30.0 (US DOL, CC BY 4.0) Job Zones × crosswalks BLS (ISCO-08→SOC 2010→SOC 2018) × "
       "`code_isco_metier`/`code_isco_p8283_metier`. La valeur affirme : le métier relève du groupe ISCO-08 "
       "indiqué ; les niveaux de préparation (échelle O*NET 1-5) listés sont ceux qu'O*NET attribue aux "
       "occupations SOC de ce GROUPE (pas le métier précis — granularité dite), avec le libellé du "
       "référentiel O*NET. Part MIX (marché du travail US).")


def moissonne() -> None:
    os.makedirs(RAW, exist_ok=True)
    print("== MOISSONNAGE O*NET Job Zones + référentiel ==")
    for url, chemin in ((URL_JZ, CACHE_JZ), (URL_JZREF, CACHE_JZREF)):
        _telecharge(url, chemin)
        print("  %s (%.0f Ko)" % (os.path.basename(chemin), os.path.getsize(chemin) / 1e3))


def _exige(chemin: str) -> str:
    if not os.path.exists(chemin):
        raise SystemExit("cache absent : %s — lancer : python3 ingestion/ingere_onet_jobzones.py moissonne"
                         % chemin)
    return chemin


def reference() -> dict:
    """niveau '1'..'5' -> libellé (« Little or No Preparation Needed »…)."""
    lignes = lit_xlsx(_exige(CACHE_JZREF))
    col = {v: k for k, v in lignes[0].items()}
    if "Job Zone" not in col or "Name" not in col:
        raise SystemExit("colonnes du référentiel Job Zone absentes de %s — format O*NET changé" % CACHE_JZREF)
    ref = {}
    for r in lignes[1:]:
        z = (r.get(col["Job Zone"]) or "").strip()
        nom = (r.get(col["Name"]) or "").strip()
        # « Job Zone One: Little or No Preparation Needed » -> « Little or No Preparation Needed »
        court = nom.split(":", 1)[1].strip() if ":" in nom else nom
        if z in {"1", "2", "3", "4", "5"} and court:
            ref[z] = court
    if len(ref) != 5:
        raise SystemExit("référentiel Job Zone incomplet (%d/5) dans %s" % (len(ref), CACHE_JZREF))
    return ref


def zones_par_soc(chemin: str) -> dict:
    """code SOC 2018 (tronqué de l'O*NET-SOC) -> {niveaux '1'..'5'}."""
    lignes = lit_xlsx(_exige(chemin))
    col = {v: k for k, v in lignes[0].items()}
    if "O*NET-SOC Code" not in col or "Job Zone" not in col:
        raise SystemExit("colonnes attendues absentes de %s — format O*NET changé" % chemin)
    table = collections.defaultdict(set)
    for r in lignes[1:]:
        code = (r.get(col["O*NET-SOC Code"]) or "")[:7]
        z = (r.get(col["Job Zone"]) or "").strip()
        if re.fullmatch(r"\d{2}-\d{4}", code) and z in {"1", "2", "3", "4", "5"}:
            table[code].add(z)
    return table


def valeur_jobzone(groupe: str, socs: list, zones: dict, ref: dict):
    """La valeur du métier, ou None si aucune occupation du groupe n'a de Job Zone."""
    niveaux = sorted(set().union(*[zones.get(s, set()) for s in socs])) if socs else []
    if not niveaux:
        return None
    corps = " ; ".join("niveau %s (%s)" % (z, ref[z]) for z in niveaux)
    return ("groupe ISCO-08 %s ; niveau de préparation requise (échelle O*NET Job Zones 1-5) attribué par "
            "O*NET 30.0 aux occupations SOC 2018 de ce groupe (granularité : occupation SOC, pas le métier "
            "précis) : %s" % (groupe, corps))


def publie_depuis_cache() -> None:
    print("== O*NET Job Zones — axe « niveau de préparation requise » (part US, MIX) ==")
    ref = reference()
    zones = zones_par_soc(CACHE_JZ)
    if len(zones) < 500:
        raise ValueError("Job Zones tronqué : %d SOC — refus de publier" % len(zones))
    print("  O*NET : %d SOC avec Job Zone · référentiel %d niveaux" % (len(zones), len(ref)))

    i2s, s18, isco = isco_vers_soc2010(), soc2010_vers_2018(), _isco_du_store()
    sys.path.insert(0, os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "outils"))
    from genere_sujets import metiers_de_la_carte
    metiers, _, _ = metiers_de_la_carte()

    paires, sans = [], 0
    for m in metiers:
        g = isco.get(m)
        if not g:
            continue
        socs = sorted({b for a in i2s.get(g, ()) for b in s18.get(a, ())})
        v = valeur_jobzone(g, socs, zones, ref)
        if v is None:
            sans += 1
            continue
        paires.append((m, v))
    if len(paires) < 300:
        raise ValueError("chaîne suspecte : %d métiers — maillons à réauditer" % len(paires))
    print("  métiers publiés : %d | groupe sans Job Zone (restent non traités) : %d" % (len(paires), sans))
    publie("niveau_preparation_soc_metier", "convention", SRC, sorted(paires))


if __name__ == "__main__":
    mode = sys.argv[1] if len(sys.argv) > 1 else "publie"
    if mode == "moissonne":
        moissonne()
    elif mode == "publie":
        publie_depuis_cache()
    else:
        raise SystemExit("usage : ingere_onet_jobzones.py [moissonne|publie]")
