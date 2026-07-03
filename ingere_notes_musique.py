"""
INGESTION MUSIQUE — note (solfège latin) -> notation anglo-saxonne  (OFFLINE).

SOURCE : théorie musicale standard. Faits STABLES et CERTAINS (correspondance do=C…).
FAUX=0 : correspondance FIXE. note -> UNE lettre = fonctionnel. Clés FR minuscules.
"""
from __future__ import annotations
from ingere_wikidata import publie

_NOTES = [
    ("do", "C"), ("ré", "D"), ("mi", "E"), ("fa", "F"),
    ("sol", "G"), ("la", "A"), ("si", "B"),
]

def ingere():
    print(f"== NOTES — solfège -> notation anglo ({len(_NOTES)}) ==")
    # articles=False : « la » (note) ne doit PAS être traité comme l'article « la » (-> "" sinon).
    publie("notation_anglaise_note", "convention", "théorie musicale (do=C…) — correspondance fixe",
           _NOTES, articles=False)

if __name__ == "__main__":
    ingere()
