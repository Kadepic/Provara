"""
INGESTION RELIGIONS — religion -> texte sacré, et religion -> lieu de culte  (OFFLINE).

SOURCE : connaissance religieuse de référence. Faits STABLES et CERTAINS (correspondances canoniques).

FAUX=0 — discipline :
  * UNIQUEMENT des correspondances NON CONTESTÉES (texte principal, lieu de culte principal).
  * relation fonctionnelle (une valeur principale par religion). Clés = noms FR minuscules.

Usage : python3 ingere_religions.py    (puis non-reg OFFLINE).
"""
from __future__ import annotations

from ingere_wikidata import publie

# (religion, texte sacré principal, lieu de culte principal)
_RELIGIONS = [
    ("christianisme", "Bible", "église"),
    ("catholicisme", "Bible", "église"),
    ("protestantisme", "Bible", "temple"),
    ("islam", "Coran", "mosquée"),
    ("judaïsme", "Torah", "synagogue"),
    ("hindouisme", "Védas", "temple"),
    ("bouddhisme", "Tripitaka", "temple"),
    ("sikhisme", "Guru Granth Sahib", "gurdwara"),
    ("zoroastrisme", "Avesta", "temple du feu"),
    ("taoisme", "Tao Tö King", "temple"),
]

SRC = "connaissance religieuse de référence — correspondances canoniques"


def ingere():
    print(f"== RELIGIONS — texte sacré + lieu de culte ({len(_RELIGIONS)} religions) ==")
    publie("texte_sacre", "convention", SRC, [(r, t) for r, t, _ in _RELIGIONS])
    publie("lieu_culte", "convention", SRC, [(r, l) for r, _, l in _RELIGIONS])


if __name__ == "__main__":
    ingere()
