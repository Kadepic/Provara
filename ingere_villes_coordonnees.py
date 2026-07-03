"""
INGESTION COORDONNÉES DES LOCALITÉS (Wikidata/QLever P625, CYCLE 2) -> latitude_localite / longitude_localite.

BUT : étendre la navigation (`ia.coordonnees_lieu` / `distance_lieux` / `cap_lieux`) au-delà des 203 capitales —
villes, communes, villages : toute LOCALITÉ (lieu habité) au nom NON AMBIGU.

GARDE ANTI-HOMONYME (conception FAUX=0 arrêtée au cycle 1, cf. ETAT_REEL) : le SEUL garde sain = pull sur TOUTE
la portée habitée (Q486972 « human settlement » + sous-classes, PAS seulement Q515 « ville » — sinon « Brest »
(France, commune) contre « Brest » (Biélorussie, ville) passerait) puis UNICITÉ GLOBALE DU NOM : un nom porté par
≥ 2 localités distinctes, ou une localité à ≥ 2 coordonnées divergentes -> HORS (jamais tranché). Un filtre de
population seul ne protège PAS (il peut sélectionner le mauvais homonyme). L'unicité est poussée CÔTÉ SERVEUR
(GROUP BY nom, HAVING COUNT(DISTINCT ?v)=1 && COUNT(DISTINCT ?coord)=1 — méthode T6 « HAVING serveur ») ;
`fonctionnel()` de publie() re-vérifie côté client (double garde). RÉSIDUEL DOCUMENTÉ : l'unicité est jugée sur
les libellés FRANÇAIS (= la clé de lookup) ; un homonyme étranger SANS libellé FR est invisible à ce crible —
même résiduel que la conception arrêtée au cycle 1 (la clé servie reste vraie pour la localité qu'elle nomme).

SOUNDNESS : WKT POINT(lon lat) parsé STRICTEMENT + bornes lat/lon (navigation._valide_coord) ; libellé Q-ID nu
rejeté ; capitales ambiguës (« Paris » vs Paris, Texas) : ABSENTES d'ici mais toujours servies par
latitude_capitale (portée capitale = non ambiguë) — `ia.coordonnees_lieu` balaie les deux paires de relations.

OFFLINE : le flux TSV est SNAPSHOTTÉ ligne à ligne dans datasets/_raw/coord_localites.tsv (rejeu 100 % offline).

Usage : python3 ingere_villes_coordonnees.py        puis non-reg OFFLINE.
"""
from __future__ import annotations

import os
import re

from ingere_coordonnees import _parse_wkt
from ingere_t6 import _stream_paires_tsv
from ingere_wikidata import publie

RAW = os.path.join(os.path.dirname(os.path.abspath(__file__)), "datasets", "_raw")
_SNAP = os.path.join(RAW, "coord_localites.tsv")

SRC = ("Wikidata/QLever — localités (Q486972+sous-classes) au NOM GLOBALEMENT UNIQUE, coordonnées P625 "
       "(unicité nom ET coordonnée imposée côté serveur ; WKT POINT lon lat -> degrés décimaux)")

_Q = """SELECT ?nom (SAMPLE(?coord) AS ?c) WHERE {
  ?v wdt:P31/wdt:P279* wd:Q486972 ; wdt:P625 ?coord ; rdfs:label ?nom .
  FILTER(lang(?nom) = "fr")
} GROUP BY ?nom HAVING(COUNT(DISTINCT ?v) = 1 && COUNT(DISTINCT ?coord) = 1)"""


def _paires_source():
    """Rejoue le snapshot TSV s'il existe (OFFLINE), sinon streame QLever EN ÉCRIVANT le snapshot au fil de l'eau."""
    if os.path.isfile(_SNAP):
        print(f"  [snapshot réutilisé : {os.path.basename(_SNAP)} — offline]")
        with open(_SNAP, encoding="utf-8") as fh:
            for ligne in fh:
                ligne = ligne.rstrip("\n")
                if not ligne:
                    continue
                parts = ligne.split("\t")
                if len(parts) == 2:
                    yield parts[0], parts[1]
        return
    os.makedirs(RAW, exist_ok=True)
    tmp = _SNAP + ".tmp"
    n = 0
    with open(tmp, "w", encoding="utf-8") as out:
        for nom, coord in _stream_paires_tsv(_Q, timeout=1800):
            out.write(f"{nom}\t{coord}\n")
            n += 1
            yield nom, coord
    os.replace(tmp, _SNAP)                          # snapshot scellé ATOMIQUEMENT en fin de flux complet
    print(f"  [snapshot écrit : {n} lignes]")


def ingere_localites():
    print("== COORDONNÉES DES LOCALITÉS AU NOM UNIQUE (Wikidata/QLever P625, portée Q486972) ==")
    lats, lons, rejets = [], [], 0
    for nom, coord in _paires_source():
        if not nom or re.fullmatch(r"Q\d+", nom) or len(nom) > 80:
            rejets += 1
            continue
        parsed = _parse_wkt(coord)
        if parsed is None:
            rejets += 1
            continue
        lat, lon = parsed
        lats.append((nom, f"{lat:.6f}"))
        lons.append((nom, f"{lon:.6f}"))
    print(f"  {len(lats)} localités valides, {rejets} rejets (Q-ID nu / WKT malformé / hors bornes / nom aberrant).")
    publie("latitude_localite", "physique", SRC, lats)
    publie("longitude_localite", "physique", SRC, lons)


if __name__ == "__main__":
    ingere_localites()
