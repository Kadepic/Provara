"""
INGESTION LITTÉRATURE — œuvre -> auteur -> datasets/lecteur/auteur_oeuvre.jsonl  (OFFLINE).

SOURCE : histoire littéraire de référence. Faits STABLES et CERTAINS (paternité non contestée).

FAUX=0 — discipline :
  * UNIQUEMENT des œuvres à auteur NON CONTESTÉ (classiques canoniques).
  * On ÉCARTE les paternités débattues (épopées anonymes incertaines, etc.).
  * œuvre -> UN auteur = fonctionnel. Clés = titres FR minuscules ; le lecteur normalise.

Usage : python3 ingere_litterature.py    (puis non-reg OFFLINE).
"""
from __future__ import annotations

from ingere_wikidata import publie

_OEUVRES = [
    ("les misérables", "Victor Hugo"),
    ("notre-dame de paris", "Victor Hugo"),
    ("germinal", "Émile Zola"),
    ("l'assommoir", "Émile Zola"),
    ("madame bovary", "Gustave Flaubert"),
    ("le rouge et le noir", "Stendhal"),
    ("le comte de monte-cristo", "Alexandre Dumas"),
    ("les trois mousquetaires", "Alexandre Dumas"),
    ("le petit prince", "Antoine de Saint-Exupéry"),
    ("candide", "Voltaire"),
    ("les fleurs du mal", "Charles Baudelaire"),
    ("à la recherche du temps perdu", "Marcel Proust"),
    ("l'étranger", "Albert Camus"),
    ("la peste", "Albert Camus"),
    ("le père goriot", "Honoré de Balzac"),
    ("don quichotte", "Miguel de Cervantès"),
    ("roméo et juliette", "William Shakespeare"),
    ("hamlet", "William Shakespeare"),
    ("macbeth", "William Shakespeare"),
    ("guerre et paix", "Léon Tolstoï"),
    ("anna karénine", "Léon Tolstoï"),
    ("crime et châtiment", "Fiodor Dostoïevski"),
    ("les frères karamazov", "Fiodor Dostoïevski"),
    ("1984", "George Orwell"),
    ("la ferme des animaux", "George Orwell"),
    ("ulysse", "James Joyce"),
    ("le vieil homme et la mer", "Ernest Hemingway"),
    ("cent ans de solitude", "Gabriel García Márquez"),
    ("le procès", "Franz Kafka"),
    ("la métamorphose", "Franz Kafka"),
    ("moby dick", "Herman Melville"),
    ("orgueil et préjugés", "Jane Austen"),
    ("frankenstein", "Mary Shelley"),
    ("dracula", "Bram Stoker"),
    ("les aventures de tom sawyer", "Mark Twain"),
    ("le seigneur des anneaux", "J. R. R. Tolkien"),
    ("le hobbit", "J. R. R. Tolkien"),
    ("harry potter à l'école des sorciers", "J. K. Rowling"),
    ("vingt mille lieues sous les mers", "Jules Verne"),
    ("le tour du monde en quatre-vingts jours", "Jules Verne"),
    ("bel-ami", "Guy de Maupassant"),
    ("le malade imaginaire", "Molière"),
    ("tartuffe", "Molière"),
    ("l'avare", "Molière"),
    ("le cid", "Pierre Corneille"),
    ("phèdre", "Jean Racine"),
    ("le mariage de figaro", "Beaumarchais"),
    ("la divine comédie", "Dante Alighieri"),
    ("faust", "Goethe"),
    ("don juan", "Molière"),
]

SRC = "histoire littéraire de référence (œuvre -> auteur) — paternité non contestée"


def ingere():
    print(f"== LITTÉRATURE — œuvre -> auteur ({len(_OEUVRES)} œuvres) ==")
    publie("auteur_oeuvre", "convention", SRC, _OEUVRES)


if __name__ == "__main__":
    ingere()
