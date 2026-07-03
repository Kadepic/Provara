"""
INGESTION LINGUISTIQUE — langue -> système d'écriture  -> datasets/lecteur/ecriture_langue.jsonl (OFFLINE).

SOURCE : linguistique de référence. Faits STABLES et CERTAINS. Fonctionnel. Clés FR minuscules.
"""
from __future__ import annotations
from ingere_wikidata import publie

_ECRITURES = [
    ("français", "alphabet latin"), ("anglais", "alphabet latin"), ("espagnol", "alphabet latin"),
    ("allemand", "alphabet latin"), ("italien", "alphabet latin"), ("turc", "alphabet latin"),
    ("russe", "alphabet cyrillique"), ("bulgare", "alphabet cyrillique"), ("serbe", "alphabet cyrillique"),
    ("arabe", "alphabet arabe"), ("persan", "alphabet arabe"),
    ("hébreu", "alphabet hébreu"), ("grec", "alphabet grec"),
    ("chinois", "sinogrammes"), ("japonais", "kanji et kana"), ("coréen", "hangeul"),
    ("hindi", "devanagari"), ("thaï", "alphabet thaï"), ("arménien", "alphabet arménien"),
    ("géorgien", "alphabet géorgien"),
]

def ingere():
    print(f"== ÉCRITURES PAR LANGUE ({len(_ECRITURES)}) ==")
    publie("ecriture_langue", "convention", "linguistique de référence (langue -> système d'écriture)", _ECRITURES)

if __name__ == "__main__":
    ingere()
