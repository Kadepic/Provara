"""
INGESTION BANDE DESSINÉE — série -> auteur/créateur  -> datasets/lecteur/auteur_bd.jsonl (OFFLINE).

SOURCE : histoire de la BD de référence. Faits STABLES et CERTAINS (paternité non contestée).
FAUX=0 : créateurs NON CONTESTÉS. série -> UN créateur principal = fonctionnel. Clés FR minuscules.
"""
from __future__ import annotations
from ingere_wikidata import publie

_BD = [
    ("tintin", "Hergé"),
    ("astérix", "René Goscinny et Albert Uderzo"),
    ("lucky luke", "Morris"),
    ("gaston lagaffe", "André Franquin"),
    ("les schtroumpfs", "Peyo"),
    ("spirou et fantasio", "Franquin"),
    ("blake et mortimer", "Edgar P. Jacobs"),
    ("corto maltese", "Hugo Pratt"),
    ("largo winch", "Jean Van Hamme"),
    ("thorgal", "Jean Van Hamme et Grzegorz Rosinski"),
    ("titeuf", "Zep"),
    ("boule et bill", "Jean Roba"),
    ("xiii", "Jean Van Hamme et William Vance"),
    ("les tuniques bleues", "Raoul Cauvin et Willy Lambil"),
    ("achille talon", "Greg"),
    ("gai-luron", "Marcel Gotlib"),
    ("iznogoud", "René Goscinny et Jean Tabary"),
    ("calvin et hobbes", "Bill Watterson"),
    ("mafalda", "Quino"),
    ("garfield", "Jim Davis"),
]

def ingere():
    print(f"== BANDE DESSINÉE — série -> auteur ({len(_BD)}) ==")
    publie("auteur_bd", "convention", "histoire de la BD de référence (série -> créateur)", _BD)

if __name__ == "__main__":
    ingere()
