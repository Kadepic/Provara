"""
INGESTION CINÉMA — film -> réalisateur -> datasets/lecteur/realisateur_film.jsonl  (OFFLINE).

SOURCE : histoire du cinéma de référence. Faits STABLES et CERTAINS (réalisateur non contesté).

FAUX=0 — discipline : films célèbres à réalisateur NON CONTESTÉ. film -> UN réalisateur = fonctionnel.
Titres FR de sortie en clé ; le lecteur normalise.

Usage : python3 ingere_cinema.py    (puis non-reg OFFLINE).
"""
from __future__ import annotations

from ingere_wikidata import publie

_FILMS = [
    ("le parrain", "Francis Ford Coppola"),
    ("apocalypse now", "Francis Ford Coppola"),
    ("pulp fiction", "Quentin Tarantino"),
    ("kill bill", "Quentin Tarantino"),
    ("psychose", "Alfred Hitchcock"),
    ("les oiseaux", "Alfred Hitchcock"),
    ("fenêtre sur cour", "Alfred Hitchcock"),
    ("2001, l'odyssée de l'espace", "Stanley Kubrick"),
    ("orange mécanique", "Stanley Kubrick"),
    ("shining", "Stanley Kubrick"),
    ("titanic", "James Cameron"),
    ("avatar", "James Cameron"),
    ("la liste de schindler", "Steven Spielberg"),
    ("jurassic park", "Steven Spielberg"),
    ("e.t. l'extra-terrestre", "Steven Spielberg"),
    ("les dents de la mer", "Steven Spielberg"),
    ("inception", "Christopher Nolan"),
    ("interstellar", "Christopher Nolan"),
    ("le voyage dans la lune", "Georges Méliès"),
    ("citizen kane", "Orson Welles"),
    ("les temps modernes", "Charlie Chaplin"),
    ("le dictateur", "Charlie Chaplin"),
    ("taxi driver", "Martin Scorsese"),
    ("les affranchis", "Martin Scorsese"),
    ("forrest gump", "Robert Zemeckis"),
    ("retour vers le futur", "Robert Zemeckis"),
    ("la guerre des étoiles", "George Lucas"),
    ("alien", "Ridley Scott"),
    ("blade runner", "Ridley Scott"),
    ("le fabuleux destin d'amélie poulain", "Jean-Pierre Jeunet"),
    ("la haine", "Mathieu Kassovitz"),
    ("intouchables", "Olivier Nakache et Éric Toledano"),
]

SRC = "histoire du cinéma de référence (film -> réalisateur) — non contesté"


def ingere():
    print(f"== CINÉMA — film -> réalisateur ({len(_FILMS)}) ==")
    publie("realisateur_film", "convention", SRC, _FILMS)


if __name__ == "__main__":
    ingere()
