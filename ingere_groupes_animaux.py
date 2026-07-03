"""
INGESTION LANGUE/ZOO — animal -> nom du groupe (collectif)  -> datasets/lecteur/nom_groupe_animal.jsonl (OFFLINE).

SOURCE : lexique français de référence. Faits STABLES et CERTAINS (noms collectifs standard).
FAUX=0 : noms collectifs NON CONTESTÉS. animal -> UN nom de groupe = fonctionnel. Clés FR minuscules.
"""
from __future__ import annotations
from ingere_wikidata import publie

_GROUPES = [
    ("loup", "une meute"),
    ("chien", "une meute"),
    ("lion", "une troupe"),
    ("poisson", "un banc"),
    ("oiseau", "une volée"),
    ("vache", "un troupeau"),
    ("mouton", "un troupeau"),
    ("abeille", "un essaim"),
    ("fourmi", "une colonie"),
    ("éléphant", "un troupeau"),
    ("baleine", "un banc"),
    ("corbeau", "une nuée"),
    ("sauterelle", "un nuage"),
    ("cheval", "un troupeau"),
    ("oie", "une volée"),
]

def ingere():
    print(f"== GROUPES D'ANIMAUX ({len(_GROUPES)}) ==")
    publie("nom_groupe_animal", "convention", "lexique français (animal -> nom collectif)", _GROUPES)

if __name__ == "__main__":
    ingere()
