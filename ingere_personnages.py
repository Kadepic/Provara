"""
INGESTION FICTION — personnage -> créateur (auteur)  -> datasets/lecteur/createur_personnage.jsonl (OFFLINE).

SOURCE : littérature/fiction de référence. Faits STABLES et CERTAINS (création non contestée).
FAUX=0 : personnages à créateur NON CONTESTÉ. personnage -> UN créateur = fonctionnel. Clés FR minuscules.
"""
from __future__ import annotations
from ingere_wikidata import publie

_PERSOS = [
    ("sherlock holmes", "Arthur Conan Doyle"),
    ("hercule poirot", "Agatha Christie"),
    ("miss marple", "Agatha Christie"),
    ("james bond", "Ian Fleming"),
    ("tarzan", "Edgar Rice Burroughs"),
    ("d'artagnan", "Alexandre Dumas"),
    ("harry potter", "J. K. Rowling"),
    ("gandalf", "J. R. R. Tolkien"),
    ("frodon", "J. R. R. Tolkien"),
    ("dracula", "Bram Stoker"),
    ("robinson crusoé", "Daniel Defoe"),
    ("pinocchio", "Carlo Collodi"),
    ("peter pan", "James Matthew Barrie"),
    ("le petit prince", "Antoine de Saint-Exupéry"),
    ("cendrillon", "Charles Perrault"),
    ("le petit chaperon rouge", "Charles Perrault"),
    ("oliver twist", "Charles Dickens"),
    ("jean valjean", "Victor Hugo"),
    ("quasimodo", "Victor Hugo"),
    ("gargantua", "François Rabelais"),
    ("frankenstein", "Mary Shelley"),
    ("dorian gray", "Oscar Wilde"),
    ("madame bovary", "Gustave Flaubert"),
]

def ingere():
    print(f"== PERSONNAGES -> CRÉATEUR ({len(_PERSOS)}) ==")
    publie("createur_personnage", "convention", "fiction de référence (personnage -> créateur)", _PERSOS)

if __name__ == "__main__":
    ingere()
