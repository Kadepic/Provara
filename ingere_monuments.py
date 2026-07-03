"""
INGESTION MONUMENTS — monument -> pays, et monument -> ville  (OFFLINE).

SOURCE : géographie/culture de référence. Faits STABLES et CERTAINS (localisation non contestée).

FAUX=0 — discipline : monuments emblématiques à localisation NON CONTESTÉE. Relations fonctionnelles
(un pays, une ville par monument). Clés = noms FR minuscules ; le lecteur normalise.

Usage : python3 ingere_monuments.py    (puis non-reg OFFLINE).
"""
from __future__ import annotations

from ingere_wikidata import publie

# (monument, pays, ville)
_MONUMENTS = [
    ("tour eiffel", "France", "Paris"),
    ("arc de triomphe", "France", "Paris"),
    ("mont saint-michel", "France", "Le Mont-Saint-Michel"),
    ("château de versailles", "France", "Versailles"),
    ("colisée", "Italie", "Rome"),
    ("tour de pise", "Italie", "Pise"),
    ("basilique saint-pierre", "Vatican", "Cité du Vatican"),
    ("sagrada familia", "Espagne", "Barcelone"),
    ("alhambra", "Espagne", "Grenade"),
    ("big ben", "Royaume-Uni", "Londres"),
    ("tower bridge", "Royaume-Uni", "Londres"),
    ("statue de la liberté", "États-Unis", "New York"),
    ("maison-blanche", "États-Unis", "Washington"),
    ("taj mahal", "Inde", "Agra"),
    ("machu picchu", "Pérou", "Cuzco"),
    ("pyramides de gizeh", "Égypte", "Gizeh"),
    ("grande muraille de chine", "Chine", "Pékin"),
    ("cité interdite", "Chine", "Pékin"),
    ("kremlin", "Russie", "Moscou"),
    ("parthénon", "Grèce", "Athènes"),
    ("acropole d'athènes", "Grèce", "Athènes"),
    ("christ rédempteur", "Brésil", "Rio de Janeiro"),
    ("opéra de sydney", "Australie", "Sydney"),
    ("burj khalifa", "Émirats arabes unis", "Dubaï"),
    ("petra", "Jordanie", "Petra"),
    ("angkor vat", "Cambodge", "Siem Reap"),
    ("brandebourg (porte)", "Allemagne", "Berlin"),
    ("manneken-pis", "Belgique", "Bruxelles"),
    ("atomium", "Belgique", "Bruxelles"),
    ("tour de tokyo", "Japon", "Tokyo"),
]

SRC = "géographie/culture de référence (monument -> localisation) — certain"


def ingere():
    print(f"== MONUMENTS — pays + ville ({len(_MONUMENTS)} monuments) ==")
    publie("pays_monument", "physique", SRC, [(m, p) for m, p, _ in _MONUMENTS])
    publie("ville_monument", "physique", SRC, [(m, v) for m, _, v in _MONUMENTS])


if __name__ == "__main__":
    ingere()
