"""
INGESTION GÉOGRAPHIE PHYSIQUE — fleuve/montagne -> continent -> datasets/lecteur/*.jsonl  (OFFLINE).

SOURCE : géographie de référence. Faits STABLES et CERTAINS (le continent d'un fleuve/sommet ne change pas).
On reste sur le CONTINENT (qualitatif, certain), PAS sur les longueurs/altitudes chiffrées (précision
disputée selon les mesures -> différé). Valeurs de continent ALIGNÉES sur la relation `continent` existante.

FAUX=0 — discipline :
  * On ÉCARTE tout objet à continent ambigu/transfrontalier : Oural, Caucase/Elbrouz/Ararat (frontière
    Europe-Asie disputée), massifs (Atlas) -> exclus. Uniquement le NON CONTESTÉ.
  * fleuve -> continent et montagne -> continent = relations distinctes (fonctionnel, un continent chacun).
  * Clés = noms FR ; le lecteur normalise accents/articles.

Usage : python3 ingere_geo_physique.py    (puis non-reg OFFLINE).
"""
from __future__ import annotations

from ingere_wikidata import publie

# continents EXACTEMENT comme la relation `continent` (mledoze) : Afrique, Asie, Europe,
# Amérique du Nord, Amérique du Sud, Océanie, Antarctique.
_FLEUVES = {
    "Afrique": ["nil", "congo", "niger", "zambèze", "sénégal", "orange", "limpopo", "ogooué"],
    "Amérique du Sud": ["amazone", "paraná", "orénoque", "uruguay", "rio paraguay"],
    "Amérique du Nord": ["mississippi", "missouri", "colorado", "rio grande", "saint-laurent",
                         "yukon", "mackenzie", "columbia"],
    "Asie": ["yangtsé", "fleuve jaune", "mékong", "gange", "indus", "brahmapoutre", "tigre",
             "euphrate", "ob", "ienisseï", "léna", "amour"],
    "Europe": ["volga", "danube", "rhin", "rhône", "seine", "loire", "garonne", "tamise",
               "tage", "èbre", "pô", "elbe", "oder", "dniepr", "meuse", "douro"],
    "Océanie": ["murray", "darling"],
}

_MONTAGNES = {
    "Asie": ["everest", "k2", "kangchenjunga", "annapurna", "lhotse", "makalu", "mont fuji"],
    "Europe": ["mont blanc", "cervin", "mont rose", "mont olympe", "etna", "vésuve", "grossglockner"],
    "Afrique": ["kilimandjaro", "mont kenya", "toubkal", "mont stanley", "ras dashen"],
    "Amérique du Sud": ["aconcagua", "chimborazo", "cotopaxi", "huascarán", "ojos del salado"],
    "Amérique du Nord": ["denali", "mont saint elias", "pic d'orizaba", "mont whitney", "mont rainier"],
    "Océanie": ["mont kosciuszko", "aoraki", "mont wilhelm"],
    "Antarctique": ["mont vinson", "mont erebus"],
}


def ingere():
    f = [(n, cont) for cont, noms in _FLEUVES.items() for n in noms]
    m = [(n, cont) for cont, noms in _MONTAGNES.items() for n in noms]
    print(f"== GÉO PHYSIQUE — {len(f)} fleuves, {len(m)} montagnes -> continent ==")
    publie("continent_fleuve", "physique", "géographie de référence (fleuve -> continent) — certain", f)
    publie("continent_montagne", "physique", "géographie de référence (sommet -> continent) — certain", m)


if __name__ == "__main__":
    ingere()
