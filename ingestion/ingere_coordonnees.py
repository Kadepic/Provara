"""
INGESTION COORDONNÉES GÉOGRAPHIQUES (Wikidata/QLever P625) -> datasets/lecteur/*.jsonl (ONLINE, à la main).

BUT : ACTIVER le moteur mort `navigation.py` (haversine / cap orthodromique), qui tourne À VIDE faute de
coordonnées ingérées. Une coordonnée d'un LIEU est un fait BORNÉ (la réalité fixe sa position). On la stocke
en DEUX relations SCALAIRES atomiques (latitude / longitude, degrés décimaux) plutôt qu'un couple opaque :
chaque scalaire est un fait propre, réutilisable et vérifiable indépendamment.

SOUNDNESS (FAUX=0, identique au reste du projet) :
  - CYCLE 1 = CAPITALES d'états souverains (Q3624078 -> P36 -> capitale -> P625). Choix délibéré : densité
    d'ancres maximale (Paris, Tokyo, Washington…) et noms quasi uniques -> risque d'homonyme négligeable.
  - `fonctionnel()` (COUNT=1) : toute entité à coordonnées MULTIPLES divergentes est REJETÉE (jamais tranchée).
  - WKT `POINT(lon lat)` parsé strictement (ordre lon PUIS lat) ; latitude ∈ [-90,90], longitude ∈ [-180,180]
    validées via navigation._valide_coord — hors bornes -> REJET (jamais « corrigé »).
  - libellé = Q-ID nu -> rejeté (pas de nom FR).
  - snapshot brut offline (`datasets/_raw/`) -> rejeu 100 % offline, non-régression sans réseau.

La DISTANCE entre deux lieux N'EST PAS stockée : elle est DÉRIVÉE à la demande par `ia.distance_lieux`
(orthodromie sphérique R=6371 km, portée explicite) — un fait dérivé exact du modèle, pas une donnée.

Usage : python3 ingere_coordonnees.py        puis non-reg OFFLINE.
"""
from __future__ import annotations

import re

import navigation
from ingere_qlever import _charge_ou_fetch, val
from ingere_wikidata import publie

SRC = "Wikidata/QLever — coordonnées P625 (WKT POINT lon lat -> degrés décimaux)"

# POINT(lon lat) ; tolère espaces multiples, altitude finale ignorée, casse libre.
_WKT = re.compile(r"POINT\s*\(\s*(-?\d+(?:\.\d+)?)\s+(-?\d+(?:\.\d+)?)", re.IGNORECASE)


def _parse_wkt(wkt: str):
    """WKT `POINT(lon lat)` -> (lat, lon) VALIDÉS, ou None si malformé / hors bornes (FAUX=0 : jamais deviné)."""
    m = _WKT.search(wkt or "")
    if not m:
        return None
    lon, lat = float(m.group(1)), float(m.group(2))
    try:
        navigation._valide_coord(lat, lon)          # bornes lat/lon ; ValueError -> rejet
    except ValueError:
        return None
    return lat, lon


def ingere_capitales():
    print("== COORDONNÉES DES CAPITALES (Wikidata/QLever P625) ==")
    q = """SELECT ?capLabel ?coord WHERE {
      ?c wdt:P31 wd:Q3624078 ; wdt:P36 ?cap .
      ?cap wdt:P625 ?coord .
      ?cap rdfs:label ?capLabel . FILTER(lang(?capLabel)="fr")
    }"""
    rows = _charge_ou_fetch("coord_capitales", q)
    print(f"  {len(rows)} lignes brutes.")
    lats, lons, rejets = [], [], 0
    for r in rows:
        nom = val(r, "capLabel")
        if not nom or re.fullmatch(r"Q\d+", nom):
            rejets += 1
            continue
        parsed = _parse_wkt(val(r, "coord"))
        if parsed is None:
            rejets += 1
            continue
        lat, lon = parsed
        lats.append((nom, f"{lat:.6f}"))
        lons.append((nom, f"{lon:.6f}"))
    print(f"  {len(lats)} coordonnées valides, {rejets} rejets (Q-ID nu / WKT malformé / hors bornes).")
    publie("latitude_capitale", "physique", SRC, lats)
    publie("longitude_capitale", "physique", SRC, lons)


if __name__ == "__main__":
    ingere_capitales()
