"""
INGESTION MYTHOLOGIE GRECQUE — dieu -> domaine, et dieu grec -> équivalent romain  (OFFLINE).

SOURCE : mythologie classique de référence. Faits STABLES et CERTAINS (attributions canoniques).

FAUX=0 — discipline :
  * Domaine = attribution PRINCIPALE canonique non contestée (Poséidon=mer, Arès=guerre…).
  * Équivalence gréco-romaine = correspondances classiques établies (Zeus=Jupiter, Héra=Junon…).
  * On ÉCARTE les divinités à domaine multiple/contesté de façon ambiguë.
  * Clés = noms FR minuscules ; le lecteur normalise.

Usage : python3 ingere_mythologie.py    (puis non-reg OFFLINE).
"""
from __future__ import annotations

from ingere_wikidata import publie

# (dieu grec, domaine principal, équivalent romain)
_DIEUX = [
    ("zeus", "ciel et roi des dieux", "jupiter"),
    ("héra", "mariage", "junon"),
    ("poséidon", "mer", "neptune"),
    ("déméter", "agriculture", "cérès"),
    ("athéna", "sagesse", "minerve"),
    ("apollon", "arts et lumière", "apollon"),
    ("artémis", "chasse", "diane"),
    ("arès", "guerre", "mars"),
    ("aphrodite", "amour", "vénus"),
    ("héphaïstos", "forge", "vulcain"),
    ("hermès", "messager des dieux", "mercure"),
    ("hestia", "foyer", "vesta"),
    ("hadès", "enfers", "pluton"),
    ("dionysos", "vin", "bacchus"),
    ("cronos", "temps", "saturne"),
    ("éros", "désir", "cupidon"),
    ("perséphone", "enfers et printemps", "proserpine"),
    ("héraclès", "force et héros", "hercule"),
    ("pan", "nature sauvage", "faune"),
    ("nyx", "nuit", "nox"),
    ("hélios", "soleil", "sol"),
    ("séléné", "lune", "luna"),
    ("éos", "aurore", "aurore"),
    ("gaïa", "terre", "tellus"),
]

SRC = "mythologie classique de référence — attributions/équivalences canoniques"


def ingere():
    print(f"== MYTHOLOGIE — {len(_DIEUX)} dieux grecs : domaine + équivalent romain ==")
    publie("domaine_dieu", "convention", SRC, [(d, dom) for d, dom, _ in _DIEUX])
    publie("equivalent_romain", "convention", "équivalence gréco-romaine canonique",
           [(d, rom) for d, _, rom in _DIEUX])


if __name__ == "__main__":
    ingere()
