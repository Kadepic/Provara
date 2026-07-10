"""
INGESTION MIX ÉLECTRIQUE — « mix électrique d'un pays/année » (PARTIE IX, B-FAIT).

Ce sujet était classé NON TRAITÉ, « bloqué sur un corpus externe ». Il ne l'était pas : Our World in Data
publie, sous licence ouverte, la part de l'électricité par source, PAR PAYS et PAR ANNÉE, à partir des
données d'Ember et de l'Energy Institute.

SOURCE : https://ourworldindata.org/grapher/share-elec-by-source.csv (Ember, Energy Institute — CC BY).

UNE RELATION : `mix_electrique` — entité « <pays> (<année>) » -> la répartition, triée par part décroissante.

FAUX=0 — TROIS gardes.

  1. GARDE DE COMPLÉTUDE (celle qui compte). Les parts doivent sommer à 100 %. Mesuré : 684 des 7 887 lignes
     s'en écartent de plus de 2 points — ce sont les ANNÉES ANCIENNES à couverture partielle (« Algérie 1985 :
     somme = 5,26 % », les autres sources n'étant pas renseignées). Les publier laisserait entendre que 95 %
     du mix algérien de 1985 est nucléaire ou inconnu : ce serait un faux par omission. On exige donc
     |somme − 100| <= 0,5 point. Mesuré après application des trois gardes : 5 907 lignes retenues sur
     7 887 (1 310 agrégats, 670 incomplètes). Les couples pays/année écartés ne sont pas traités, et le
     compteur le dit.

  2. GARDE D'ENTITÉ RÉELLE. Une clé qui promet un pays doit contenir un pays. Écarter les lignes sans code
     ne suffit PAS : OWID donne un code à ses AGRÉGATS (« World » -> `OWID_WRL`, « Europe » -> `OWID_EUR`,
     « High-income countries » -> `OWID_HIC`). Mesuré : « World (2023) » entrait dans la table. On rejette
     donc les codes préfixés `OWID_`, à l'exception explicite du **Kosovo** (`OWID_KOS`), qui est un
     territoire réel dépourvu de code ISO-3166 officiel. Une liste d'exception nommée vaut mieux qu'un
     filtre malin qui perdrait un pays sans le dire.

  3. VÉRITÉ DATÉE. L'année est DANS la clé (« France (2023) ») et dans la valeur. Un mix électrique change
     chaque année : une valeur non datée serait un faux différé, vrai le jour de l'écriture et faux ensuite.
     Ainsi formulée, la donnée reste vraie indéfiniment — c'est une mesure datée, pas une prétention au
     présent.

Usage : LECTEUR_DATASETS_DIR=... PYTHONPATH=src:ingestion python3 ingestion/ingere_mix_electrique.py
"""
from __future__ import annotations

import csv
import io
import urllib.request

from ingere_wikidata import publie, snapshot_brut

URL = "https://ourworldindata.org/grapher/share-elec-by-source.csv"
UA = "Provara/1.0 (https://github.com/Provara-IA/Provara) offline-knowledge-ingestion"

# Tolérance sur la somme des parts. 0,5 point : au-delà, la ligne est incomplète, pas imprécise.
TOLERANCE_SOMME = 0.5

# Codes `OWID_` qui désignent un TERRITOIRE RÉEL, et non un agrégat. Tout autre code `OWID_` est rejeté.
_OWID_PAYS = frozenset(("OWID_KOS",))          # Kosovo : pas de code ISO-3166 officiel

# Colonnes -> libellés français. L'ordre de ce dict ne compte pas : la sortie est triée par part.
_SOURCES = {
    "Coal": "charbon",
    "Gas": "gaz",
    "Hydropower": "hydroélectricité",
    "Solar": "solaire",
    "Wind": "éolien",
    "Oil": "pétrole",
    "Nuclear": "nucléaire",
    "Other renewables": "autres renouvelables",
    "Bioenergy": "bioénergie",
}

SRC = ("Our World in Data — part de l'électricité par source (données Ember et Energy Institute, CC BY). "
       "Lignes dont les parts ne somment pas à 100 % (±0,5 pt) ÉCARTÉES : couverture partielle, pas mesure "
       "imprécise. Agrégats non-pays exclus. L'année est dans la clé : la donnée est une mesure DATÉE.")


def _telecharge() -> list:
    req = urllib.request.Request(URL, headers={"User-Agent": UA})
    with urllib.request.urlopen(req, timeout=180) as r:
        texte = r.read().decode("utf-8")
    return list(csv.DictReader(io.StringIO(texte)))


def _somme(ligne: dict) -> float:
    return sum(float(v) for k, v in ligne.items() if k in _SOURCES and v)


def collecte(lignes: list):
    """(paires, comptes) — les trois gardes appliquées, chaque rejet compté et nommé."""
    paires = []
    hors_pays = incompletes = 0
    for ligne in lignes:
        code = ligne.get("Code", "")
        if not code or (code.startswith("OWID_") and code not in _OWID_PAYS):
            hors_pays += 1                              # GARDE 2 : agrégats (« World », « Europe ») écartés
            continue
        total = _somme(ligne)
        if abs(total - 100.0) > TOLERANCE_SOMME:        # GARDE 1 : couverture partielle -> rejet
            incompletes += 1
            continue
        parts = [(_SOURCES[k], float(v)) for k, v in ligne.items() if k in _SOURCES and v and float(v) > 0.0]
        parts.sort(key=lambda x: -x[1])
        valeur = " · ".join("%s %.1f %%" % (nom, part) for nom, part in parts)
        paires.append(("%s (%s)" % (ligne["Entity"], ligne["Year"]), valeur))   # GARDE 3 : année dans la clé
    print("  lignes brutes : %d | agrégats non-pays écartés : %d | incomplètes écartées : %d | retenues : %d"
          % (len(lignes), hors_pays, incompletes, len(paires)))
    return paires


def ingere():
    print("== MIX ÉLECTRIQUE — pays × année (Our World in Data / Ember) ==")
    lignes = _telecharge()
    paires = collecte(lignes)
    snapshot_brut("mix_electrique", [{"lignes": len(lignes), "retenues": len(paires)}])
    publie("mix_electrique", "passe", SRC, sorted(paires))


if __name__ == "__main__":
    ingere()
