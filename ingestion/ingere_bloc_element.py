"""
INGESTION CHIMIE — élément -> bloc du tableau périodique (s/p/d/f)  -> datasets/lecteur/bloc_element.jsonl (OFFLINE).

SOURCE : tableau périodique de référence. Faits STABLES et CERTAINS.
FAUX=0 : UNIQUEMENT les éléments à bloc NON CONTESTÉ. On ÉCARTE lanthane/actinium (d vs f débattu),
hélium (placé groupe 18 mais bloc s -> on le met en s, classique et non contesté). Fonctionnel. Clés FR minuscules.
"""
from __future__ import annotations
from ingere_wikidata import publie

_PAR_BLOC = {
    "s": ["hydrogène", "hélium", "lithium", "béryllium", "sodium", "magnésium", "potassium",
          "calcium", "rubidium", "strontium", "césium", "baryum", "francium", "radium"],
    "p": ["bore", "carbone", "azote", "oxygène", "fluor", "néon", "aluminium", "silicium",
          "phosphore", "soufre", "chlore", "argon", "gallium", "germanium", "arsenic",
          "sélénium", "brome", "krypton", "étain", "iode", "xénon", "plomb"],
    "d": ["scandium", "titane", "vanadium", "chrome", "manganèse", "fer", "cobalt", "nickel",
          "cuivre", "zinc", "argent", "or", "platine", "mercure", "tungstène", "zirconium"],
    "f": ["cérium", "néodyme", "samarium", "europium", "gadolinium", "uranium", "plutonium",
          "thorium", "américium"],
}

def ingere():
    paires = [(e, b) for b, elems in _PAR_BLOC.items() for e in elems]
    print(f"== BLOC DES ÉLÉMENTS ({len(paires)}) ==")
    publie("bloc_element", "physique", "tableau périodique (élément -> bloc s/p/d/f)", paires)

if __name__ == "__main__":
    ingere()
