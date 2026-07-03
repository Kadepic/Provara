"""
INGESTION PEINTURE — œuvre -> peintre -> datasets/lecteur/peintre_oeuvre.jsonl  (OFFLINE).

SOURCE : histoire de l'art de référence. Faits STABLES et CERTAINS (attribution non contestée).

FAUX=0 — discipline :
  * UNIQUEMENT des tableaux célèbres à attribution NON CONTESTÉE.
  * œuvre -> UN peintre = fonctionnel. Clés = titres FR minuscules ; le lecteur normalise.

Usage : python3 ingere_peinture.py    (puis non-reg OFFLINE).
"""
from __future__ import annotations

from ingere_wikidata import publie

_OEUVRES = [
    ("la joconde", "Léonard de Vinci"),
    ("la cène", "Léonard de Vinci"),
    ("la nuit étoilée", "Vincent van Gogh"),
    ("les tournesols", "Vincent van Gogh"),
    ("guernica", "Pablo Picasso"),
    ("les demoiselles d'avignon", "Pablo Picasso"),
    ("le cri", "Edvard Munch"),
    ("la persistance de la mémoire", "Salvador Dalí"),
    ("la jeune fille à la perle", "Johannes Vermeer"),
    ("la naissance de vénus", "Sandro Botticelli"),
    ("le baiser", "Gustav Klimt"),
    ("la liberté guidant le peuple", "Eugène Delacroix"),
    ("le radeau de la méduse", "Théodore Géricault"),
    ("impression, soleil levant", "Claude Monet"),
    ("le déjeuner sur l'herbe", "Édouard Manet"),
    ("olympia", "Édouard Manet"),
    ("la ronde de nuit", "Rembrandt"),
    ("les ménines", "Diego Vélasquez"),
    ("le jardin des délices", "Jérôme Bosch"),
    ("american gothic", "Grant Wood"),
    ("la grande vague de kanagawa", "Hokusai"),
    ("le fils de l'homme", "René Magritte"),
    ("la trahison des images", "René Magritte"),
    ("le sacre de napoléon", "Jacques-Louis David"),
    ("la création d'adam", "Michel-Ange"),
    ("la chambre à arles", "Vincent van Gogh"),
    ("le déjeuner des canotiers", "Auguste Renoir"),
    ("les nymphéas", "Claude Monet"),
    ("composition viii", "Vassily Kandinsky"),
    ("la danse", "Henri Matisse"),
]

SRC = "histoire de l'art de référence (tableau -> peintre) — attribution non contestée"


def ingere():
    print(f"== PEINTURE — tableau -> peintre ({len(_OEUVRES)} œuvres) ==")
    publie("peintre_oeuvre", "convention", SRC, _OEUVRES)


if __name__ == "__main__":
    ingere()
