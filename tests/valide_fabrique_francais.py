"""FABRIQUE_FRANCAIS — dataset français de FORME, vérifié par accord prof↔brique (le juge tranche).
VÉRIFIÉ : zéro paire fausse exportée. GÉNÉRAL : vocabulaire held-out RÉEL (jamais dans le SEED) reproduit.
HONNÊTE : irréguliers (finir, bal, beau…) EXCLUS, jamais dans le fichier. FORMAT : JSONL bien-formé, prêt QLoRA."""
from __future__ import annotations
import json
import tempfile
from pathlib import Path

import fabrique_francais as F
from fabrique_francais import SEED, _conjug_reguliers, _reproduit, fabrique, resume

# vocabulaire HELD-OUT : de VRAIS mots en portée, ABSENTS du SEED -> prouve que la règle généralise (pas une table).
IN = (
    _conjug_reguliers(["marcher", "fermer"])
    + [("pluriel", ("oiseau",), "oiseaux"), ("pluriel", ("hôpital",), "hôpitaux"),
       ("pluriel", ("voiture",), "voitures"),
       ("feminin", ("dernier",), "dernière"), ("feminin", ("vif",), "vive"),
       ("feminin", ("nerveux",), "nerveuse"), ("feminin", ("noir",), "noire")]
)
# HORS-portée : gold INDÉPENDANT du prof que la brique ne peut PAS reproduire (groupe 2, irréguliers totaux).
HORS = [("conjugaison", ("finir", "present", 0), "finis"), ("conjugaison", ("finir", "present", 3), "finissons"),
        ("pluriel", ("vitrail",), "vitraux"), ("pluriel", ("travail",), "travaux"), ("pluriel", ("œil",), "yeux"),
        ("feminin", ("beau",), "belle"), ("feminin", ("vieux",), "vieille"), ("feminin", ("doux",), "douce")]


def _check(nom, c):
    print(f"  [{'OK ' if c else 'RATÉ'}] {nom}")
    return c


def main() -> int:
    r = []
    seed_mots = {it[1][0] for it in SEED}
    with tempfile.TemporaryDirectory() as d:
        sortie = Path(d) / "francais_forme.jsonl"
        res = fabrique(IN + HORS, sortie)

        # 1. VÉRIFIÉ : exactement les IN exportés, exactement les HORS exclus ; chaque exporté RE-vérifié indépendamment.
        reverif = all(_reproduit(it) for it in IN) and all(not _reproduit(it) for it in HORS)
        r.append(_check("VÉRIFIÉ : tous les IN exportés, tous les HORS exclus, accord prof↔brique re-prouvé",
                        res["exportes"] == len(IN) and res["exclus"] == len(HORS) and reverif))

        # 2. GÉNÉRAL : le vocabulaire IN est ABSENT du SEED -> la fabrique a généralisé la règle à du neuf.
        held_out = all(it[1][0] not in seed_mots for it in IN)
        r.append(_check("GÉNÉRAL : vocabulaire held-out réel (hors SEED) entièrement reproduit et exporté",
                        held_out and res["exportes"] == len(IN)))

        # 3. HONNÊTE : aucun mot HORS ne fuit dans le fichier exporté.
        contenu = sortie.read_text(encoding="utf-8")
        fuite = [it[1][0] for it in HORS if it[1][0] in contenu]
        r.append(_check(f"HONNÊTE : aucun irrégulier exporté (fuites={fuite})", not fuite))

        # 4. FORMAT : JSONL bien-formé, prêt pour QLoRA, et une paire-témoin correcte.
        rs = resume(sortie)
        temoin = any(json.loads(l)["instruction"].startswith("Donne le pluriel du nom « oiseau")
                     and json.loads(l)["reponse"] == "oiseaux" for l in contenu.splitlines() if l.strip())
        r.append(_check(f"FORMAT : JSONL bien-formé ({rs['valides']}/{rs['lignes']}) + paire-témoin oiseau→oiseaux",
                        rs["lignes"] > 0 and rs["mal_formees"] == 0 and rs["lignes"] == rs["valides"] and temoin))

    print()
    print("FABRIQUE_FRANCAIS VALIDÉE — 4/4." if all(r) else f"ÉCHEC — {sum(r)}/4.")
    return 0 if all(r) else 1


if __name__ == "__main__":
    raise SystemExit(main())
