"""
INGESTION MYTHOLOGIE — dieu grec -> animal/attribut sacré  -> datasets/lecteur/animal_dieu.jsonl (OFFLINE).

SOURCE : mythologie grecque de référence. Faits STABLES et CERTAINS (animaux attributs canoniques).
FAUX=0 : associations NON CONTESTÉES. dieu -> UN animal = fonctionnel. Clés FR minuscules.
"""
from __future__ import annotations
from ingere_wikidata import publie

_ANIMAUX = [
    ("zeus", "l'aigle"),
    ("athéna", "la chouette"),
    ("aphrodite", "la colombe"),
    ("héra", "le paon"),
    ("poséidon", "le cheval"),
    ("artémis", "la biche"),
    ("dionysos", "la panthère"),
    ("asclépios", "le serpent"),
]

def ingere():
    print(f"== ANIMAUX SACRÉS DES DIEUX ({len(_ANIMAUX)}) ==")
    publie("animal_dieu", "convention", "mythologie grecque (dieu -> animal sacré)", _ANIMAUX)

if __name__ == "__main__":
    ingere()
