"""
INGESTION BOTANIQUE — arbre -> type (feuillu / conifère)  -> datasets/lecteur/type_arbre.jsonl (OFFLINE).

SOURCE : botanique de référence. Faits STABLES et CERTAINS. arbre -> UN type = fonctionnel. Clés FR minuscules.
"""
from __future__ import annotations
from ingere_wikidata import publie

_PAR_TYPE = {
    "feuillu": ["chêne", "hêtre", "bouleau", "érable", "peuplier", "platane", "tilleul", "frêne",
                "saule", "marronnier", "châtaignier", "noyer", "orme", "charme", "aulne", "robinier"],
    "conifère": ["sapin", "pin", "épicéa", "cèdre", "mélèze", "if", "cyprès", "séquoia", "genévrier",
                 "douglas", "thuya"],
}

def ingere():
    paires = [(a, t) for t, arbres in _PAR_TYPE.items() for a in arbres]
    print(f"== TYPES D'ARBRES ({len(paires)}) ==")
    publie("type_arbre", "convention", "botanique de référence (arbre -> feuillu/conifère)", paires)

if __name__ == "__main__":
    ingere()
