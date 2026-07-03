"""
INGESTION DISTINCTIONS — prix/récompense -> domaine  -> datasets/lecteur/domaine_prix.jsonl (OFFLINE).

SOURCE : culture générale de référence. Faits STABLES et CERTAINS (domaine du prix).
FAUX=0 : prix à domaine UNIVOQUE (on écarte Nobel = multi-domaines). prix -> UN domaine = fonctionnel.
"""
from __future__ import annotations
from ingere_wikidata import publie

_PRIX = [
    ("palme d'or", "le cinéma"),
    ("oscar", "le cinéma"),
    ("césar", "le cinéma"),
    ("ballon d'or", "le football"),
    ("grammy award", "la musique"),
    ("prix goncourt", "la littérature"),
    ("booker prize", "la littérature"),
    ("médaille fields", "les mathématiques"),
    ("prix turing", "l'informatique"),
    ("molière (prix)", "le théâtre"),
    ("victoires de la musique", "la musique"),
    ("prix pulitzer", "le journalisme et la littérature"),
    ("lion d'or", "le cinéma"),
    ("ours d'or", "le cinéma"),
    ("prix abel", "les mathématiques"),
]

def ingere():
    print(f"== PRIX -> DOMAINE ({len(_PRIX)}) ==")
    publie("domaine_prix", "convention", "culture générale (prix -> domaine)", _PRIX)

if __name__ == "__main__":
    ingere()
