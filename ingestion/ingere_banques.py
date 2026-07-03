"""
INGESTION ÉCONOMIE — monnaie -> banque centrale émettrice  -> datasets/lecteur/banque_centrale.jsonl (OFFLINE).

SOURCE : connaissance économique de référence. Faits STABLES et CERTAINS. Fonctionnel. Clés FR minuscules.
"""
from __future__ import annotations
from ingere_wikidata import publie

_BANQUES = [
    ("euro", "Banque centrale européenne"),
    ("dollar américain", "Réserve fédérale des États-Unis"),
    ("yen", "Banque du Japon"),
    ("livre sterling", "Banque d'Angleterre"),
    ("franc suisse", "Banque nationale suisse"),
    ("yuan", "Banque populaire de Chine"),
    ("rouble", "Banque centrale de Russie"),
    ("roupie indienne", "Banque de réserve de l'Inde"),
]

def ingere():
    print(f"== BANQUES CENTRALES ({len(_BANQUES)}) ==")
    publie("banque_centrale", "convention", "économie de référence (monnaie -> banque centrale)", _BANQUES)

if __name__ == "__main__":
    ingere()
