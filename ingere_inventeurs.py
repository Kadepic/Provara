"""
INGESTION INVENTIONS — invention -> inventeur  -> datasets/lecteur/inventeur.jsonl (OFFLINE).

SOURCE : histoire des techniques. Faits STABLES et CERTAINS pour les attributions NON CONTESTÉES.
FAUX=0 : on ÉCARTE les paternités disputées (téléphone, ampoule, radio, machine à vapeur).
invention -> UN inventeur = fonctionnel. Clés FR minuscules.
"""
from __future__ import annotations
from ingere_wikidata import publie

_INVENTIONS = [
    ("dynamite", "Alfred Nobel"),
    ("montgolfière", "les frères Montgolfier"),
    ("cinématographe", "les frères Lumière"),
    ("braille", "Louis Braille"),
    ("paratonnerre", "Benjamin Franklin"),
    ("stéthoscope", "René Laennec"),
    ("pile électrique", "Alessandro Volta"),
    ("thermomètre à mercure", "Daniel Gabriel Fahrenheit"),
    ("baromètre", "Evangelista Torricelli"),
    ("vaccin contre la rage", "Louis Pasteur"),
    ("presse d'imprimerie", "Johannes Gutenberg"),
    ("locomotive à vapeur", "George Stephenson"),
    ("dirigeable", "Ferdinand von Zeppelin"),
    ("hélicoptère moderne", "Igor Sikorsky"),
    ("téléphone (brevet)", "Alexander Graham Bell"),
    ("dynamo", "Michael Faraday"),
]

def ingere():
    print(f"== INVENTIONS -> INVENTEUR ({len(_INVENTIONS)}) ==")
    publie("inventeur", "convention", "histoire des techniques (invention -> inventeur) — non contesté", _INVENTIONS)

if __name__ == "__main__":
    ingere()
