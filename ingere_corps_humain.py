"""
INGESTION CORPS HUMAIN — organe -> appareil/système -> datasets/lecteur/systeme_organe.jsonl  (OFFLINE).

SOURCE : anatomie de référence (niveau scolaire/encyclopédique), faits STABLES et CERTAINS.

FAUX=0 — discipline :
  * UNIQUEMENT les organes à appartenance NON AMBIGUË (un seul système). On ÉCARTE pancréas (digestif
    ET endocrinien), diaphragme (musculaire ET respiratoire), rate (lymphatique discutable) -> exclus.
  * Valeur = nom du système/appareil sous forme normalisée (adjectif) : digestif, respiratoire,
    circulatoire, urinaire, nerveux, musculaire, squelettique, reproducteur, endocrinien, tégumentaire.
  * Chaque organe -> UN système = fonctionnel. Clés = noms FR singulier minuscules.

Usage : python3 ingere_corps_humain.py    (puis non-reg OFFLINE).
"""
from __future__ import annotations

from ingere_wikidata import publie

_PAR_SYSTEME = {
    "circulatoire": ["cœur", "artère", "veine", "capillaire", "aorte"],
    "respiratoire": ["poumon", "trachée", "bronche", "larynx", "alvéole", "pharynx"],
    "digestif": ["estomac", "intestin", "foie", "œsophage", "côlon", "duodénum",
                 "rectum", "vésicule biliaire"],
    "urinaire": ["rein", "vessie", "uretère", "urètre"],
    "nerveux": ["cerveau", "moelle épinière", "cervelet", "nerf", "neurone"],
    "musculaire": ["muscle", "biceps", "triceps", "quadriceps"],
    "squelettique": ["os", "fémur", "tibia", "crâne", "vertèbre", "côte", "clavicule",
                     "rotule", "sternum", "mandibule", "humérus", "radius"],
    "reproducteur": ["utérus", "ovaire", "testicule", "prostate", "vagin"],
    "endocrinien": ["thyroïde", "hypophyse", "surrénale"],
    "tégumentaire": ["peau", "ongle", "cheveu", "poil"],
}

SRC = "anatomie de référence (organe -> système/appareil) — faits certains"


def ingere():
    paires = [(o, syst) for syst, organes in _PAR_SYSTEME.items() for o in organes]
    print(f"== CORPS HUMAIN — organe -> système ({len(paires)} organes, {len(_PAR_SYSTEME)} systèmes) ==")
    publie("systeme_organe", "convention", SRC, paires)


if __name__ == "__main__":
    ingere()
