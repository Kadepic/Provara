"""
INGESTION MUSIQUE — genre musical -> pays/région d'origine  -> datasets/lecteur/pays_genre_musical.jsonl (OFFLINE).

SOURCE : histoire de la musique de référence. Faits STABLES et CERTAINS pour les origines NON CONTESTÉES.
FAUX=0 : genres à origine NON CONTESTÉE. genre -> UN pays = fonctionnel. Clés FR minuscules.
"""
from __future__ import annotations
from ingere_wikidata import publie

_GENRES = [
    ("jazz", "États-Unis"), ("blues", "États-Unis"), ("rock", "États-Unis"),
    ("country", "États-Unis"), ("hip-hop", "États-Unis"), ("soul", "États-Unis"),
    ("reggae", "Jamaïque"), ("ska", "Jamaïque"),
    ("fado", "Portugal"), ("raï", "Algérie"), ("flamenco", "Espagne"),
    ("tango", "Argentine"), ("samba", "Brésil"), ("bossa nova", "Brésil"),
    ("k-pop", "Corée du Sud"), ("merengue", "République dominicaine"),
    ("calypso", "Trinité-et-Tobago"), ("polka", "République tchèque"),
]

def ingere():
    print(f"== GENRES MUSICAUX -> PAYS ({len(_GENRES)}) ==")
    publie("pays_genre_musical", "convention", "histoire de la musique (genre -> pays d'origine)", _GENRES)

if __name__ == "__main__":
    ingere()
