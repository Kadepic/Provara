"""
INGESTION INFORMATIQUE — action -> raccourci clavier  -> datasets/lecteur/raccourci_clavier.jsonl (OFFLINE).

SOURCE : conventions logicielles standard (Windows/Linux). Faits STABLES et CERTAINS.
FAUX=0 : on clé par l'ACTION (le raccourci « Ctrl+C » -> « ctrlc » par normalise, mais reste distinct).
action -> UN raccourci = fonctionnel.
"""
from __future__ import annotations
from ingere_wikidata import publie

_RACCOURCIS = [
    ("copier", "Ctrl+C"),
    ("coller", "Ctrl+V"),
    ("couper", "Ctrl+X"),
    ("annuler", "Ctrl+Z"),
    ("rétablir", "Ctrl+Y"),
    ("enregistrer", "Ctrl+S"),
    ("tout sélectionner", "Ctrl+A"),
    ("rechercher", "Ctrl+F"),
    ("imprimer", "Ctrl+P"),
    ("nouvel onglet", "Ctrl+T"),
    ("fermer la fenêtre", "Alt+F4"),
    ("ouvrir le gestionnaire des tâches", "Ctrl+Alt+Suppr"),
]

def ingere():
    print(f"== RACCOURCIS CLAVIER ({len(_RACCOURCIS)}) ==")
    publie("raccourci_clavier", "convention", "conventions logicielles standard (action -> raccourci)", _RACCOURCIS)

if __name__ == "__main__":
    ingere()
