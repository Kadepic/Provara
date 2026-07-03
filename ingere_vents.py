"""
INGESTION MÉTÉO — vent régional -> région/origine  -> datasets/lecteur/origine_vent.jsonl (OFFLINE).

SOURCE : météorologie/géographie de référence. Faits STABLES et CERTAINS (vents nommés non contestés).
FAUX=0 : on garde les vents à origine NON CONTESTÉE. Fonctionnel. Clés FR minuscules.
"""
from __future__ import annotations
from ingere_wikidata import publie

_VENTS = [
    ("mistral", "la vallée du Rhône (sud de la France)"),
    ("tramontane", "le Languedoc-Roussillon"),
    ("sirocco", "le Sahara"),
    ("foehn", "les Alpes"),
    ("harmattan", "l'Afrique de l'Ouest"),
    ("mousson", "l'Asie du Sud"),
    ("chinook", "les montagnes Rocheuses"),
    ("zonda", "les Andes (Argentine)"),
    ("bora", "la mer Adriatique"),
    ("khamsin", "l'Égypte"),
]

def ingere():
    print(f"== VENTS RÉGIONAUX ({len(_VENTS)}) ==")
    publie("origine_vent", "convention", "météorologie de référence (vent -> région d'origine)", _VENTS)

if __name__ == "__main__":
    ingere()
