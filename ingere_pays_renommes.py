"""
INGESTION GÉO/HISTOIRE — ancien nom de pays -> nom actuel  -> datasets/lecteur/nom_actuel.jsonl (OFFLINE).

SOURCE : géographie historique de référence. Faits STABLES et CERTAINS (renommages officiels).
FAUX=0 : correspondances NON CONTESTÉES. ancien nom -> UN nom actuel = fonctionnel. Clés FR minuscules.
"""
from __future__ import annotations
from ingere_wikidata import publie

_RENOMMES = [
    ("perse", "Iran"),
    ("birmanie", "Myanmar"),
    ("siam", "Thaïlande"),
    ("ceylan", "Sri Lanka"),
    ("abyssinie", "Éthiopie"),
    ("zaïre", "République démocratique du Congo"),
    ("haute-volta", "Burkina Faso"),
    ("rhodésie", "Zimbabwe"),
    ("dahomey", "Bénin"),
    ("formose", "Taïwan"),
    ("nouvelles-hébrides", "Vanuatu"),
    ("côte-de-l'or", "Ghana"),
    ("tanganyika", "Tanzanie"),
    ("kampuchéa", "Cambodge"),
]

def ingere():
    print(f"== PAYS RENOMMÉS ({len(_RENOMMES)}) ==")
    publie("nom_actuel", "convention", "géographie historique (ancien nom -> nom actuel)", _RENOMMES)

if __name__ == "__main__":
    ingere()
