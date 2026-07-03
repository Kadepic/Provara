"""FABRIQUE_COMPREHENSION — corpus d'entraînement vérifié de TOUTE la compréhension (capstone du mandat).
VÉRIFIÉ : chaque item est confirmé par sa brique-oracle (zéro rejet attendu sur le jeu certifié). COUVERTURE : toutes
les grandes capacités (≥8 capacités). FORMAT : JSONL bien-formé. HONNÊTE : un item FAUX serait rejeté, pas exporté."""
from __future__ import annotations
import json
import tempfile
from pathlib import Path

from fabrique_comprehension import ITEMS, _confirme, fabrique
from generateur import GenerateurInference


def _check(nom, c):
    print(f"  [{'OK ' if c else 'RATÉ'}] {nom}")
    return c


def main() -> int:
    r = []
    with tempfile.TemporaryDirectory() as d:
        sortie = Path(d) / "comprehension.jsonl"
        info = fabrique(sortie)

        r.append(_check(f"VÉRIFIÉ : tous les items confirmés par leur brique-oracle (exportés={info['exportes']}/"
                        f"{len(ITEMS)}, rejets={info['rejetes']})",
                        info["exportes"] == len(ITEMS) and not info["rejetes"]))

        r.append(_check(f"COUVERTURE : {len(info['capacites'])} capacités distinctes (≥8)",
                        len(info["capacites"]) >= 8))

        lignes = [json.loads(l) for l in sortie.read_text(encoding="utf-8").splitlines() if l.strip()]
        bien_forme = all(x.get("instruction", "").strip() and x.get("reponse", "").strip()
                         and x.get("capacite") for x in lignes)
        r.append(_check(f"FORMAT : {len(lignes)} paires JSONL bien-formées (instruction+réponse+capacité)",
                        len(lignes) == info["exportes"] and bien_forme))

        # HONNÊTE : un item FAUX (chat est un oiseau -> 'oui') n'est PAS confirmé -> jamais exporté.
        faux_confirme = _confirme(GenerateurInference, "deduit",
                                  ([("chat", "est", "félin")], "chat", "oiseau"), "oui")
        r.append(_check("HONNÊTE : un item faux (« chat est un oiseau » -> oui) est rejeté par la brique",
                        not faux_confirme))

    print()
    print("FABRIQUE_COMPREHENSION VALIDÉE — 4/4." if all(r) else f"ÉCHEC — {sum(r)}/4.")
    return 0 if all(r) else 1


if __name__ == "__main__":
    raise SystemExit(main())
