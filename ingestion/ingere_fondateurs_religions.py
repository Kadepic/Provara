"""
INGESTION RELIGIONS — religion -> fondateur  -> datasets/lecteur/fondateur_religion.jsonl (OFFLINE).

SOURCE : histoire des religions de référence. Faits STABLES et CERTAINS pour les cas NON CONTESTÉS.
FAUX=0 : on ÉCARTE les fondations à attribution disputée (judaïsme, hindouisme = sans fondateur unique).
religion -> UN fondateur = fonctionnel. Clés FR minuscules.
"""
from __future__ import annotations
from ingere_wikidata import publie

_FONDATEURS = [
    ("christianisme", "Jésus-Christ"),
    ("islam", "Mahomet"),
    ("bouddhisme", "Bouddha (Siddhartha Gautama)"),
    ("sikhisme", "Guru Nanak"),
    ("protestantisme", "Martin Luther"),
    ("confucianisme", "Confucius"),
    ("taoisme", "Lao Tseu"),
    ("zoroastrisme", "Zarathoustra"),
    ("jaïnisme", "Mahavira"),
    ("mormonisme", "Joseph Smith"),
]

def ingere():
    print(f"== FONDATEURS DE RELIGIONS ({len(_FONDATEURS)}) ==")
    publie("fondateur_religion", "convention", "histoire des religions (religion -> fondateur) — non contesté", _FONDATEURS)

if __name__ == "__main__":
    ingere()
