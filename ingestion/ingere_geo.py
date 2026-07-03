"""
INGESTION GÉOGRAPHIE -> datasets/lecteur/*.jsonl  (ONLINE, lancé à la main).

SOURCE : dataset ouvert `mledoze/countries` (GitHub raw, NON rate-limité ; c'est la base derrière l'ex
REST Countries). 250 pays, noms FRANÇAIS (translations.fra). On y prend en priorité les relations NEUTRES
EN LANGUE / EXACTES (codes ISO, code devise, indicatif, continent) — qualité FR garantie, FAUX=0.

⚠️ CHOIX DE SOUNDNESS LINGUISTIQUE : dans ce dataset, capitale / nom de monnaie / langue sont en ANGLAIS.
Pour une IA francophone, on NE les charge PAS ici (on ne pollue pas avec « Brussels », « US Dollar »…) :
ces relations restent l'amorce FR et seront étendues via Wikidata-FR (P36/P38/P37) quand le service WDQS
sortira de son outage (cf. ingere_wikidata.py, domaine `geo_fr`). Ici = uniquement le sûr et le neutre.

Réconciliation amorce + écriture self-describing : déléguées à ingere_wikidata (helpers génériques).
Usage : python3 ingere_geo.py   (puis non-reg offline).
"""
from __future__ import annotations

import json
import urllib.request

from ingere_wikidata import UA, publie, snapshot_brut
import sources

URL = sources.url("mledoze-countries")          # endpoint lu DEPUIS le registre (datasets/sources), pas en dur

# region/subregion (anglais) -> continent FR (aligné sur l'amorce : Amériques scindées N/S).
_SUBREGION_CONTINENT = {
    "South America": "Amérique du Sud",
    "North America": "Amérique du Nord", "Central America": "Amérique du Nord", "Caribbean": "Amérique du Nord",
}
_REGION_CONTINENT = {
    "Africa": "Afrique", "Asia": "Asie", "Europe": "Europe", "Oceania": "Océanie", "Antarctic": "Antarctique",
}


def _continent(c) -> str:
    sub = c.get("subregion") or ""
    if sub in _SUBREGION_CONTINENT:
        return _SUBREGION_CONTINENT[sub]
    return _REGION_CONTINENT.get(c.get("region") or "", "")


def _indicatif(c) -> str:
    """Indicatif téléphonique = root + suffixe si UN seul suffixe ; sinon root seul (ex. +1 pour les
    pays du NANP). Renvoie sans le « + ». Vide si indéterminé."""
    idd = c.get("idd") or {}
    root = (idd.get("root") or "").lstrip("+")
    suf = idd.get("suffixes") or []
    if not root:
        return ""
    if len(suf) == 1:
        return root + suf[0]
    return root                       # multi-suffixe -> indicatif de base (root)


def _nom_fr(c) -> str:
    return (c.get("translations", {}).get("fra", {}) or {}).get("common", "") or c.get("name", {}).get("common", "")


def ingere_geo():
    print("== GÉOGRAPHIE (mledoze/countries, GitHub — relations neutres/exactes) ==")
    req = urllib.request.Request(URL, headers={"User-Agent": UA})
    data = json.loads(urllib.request.urlopen(req, timeout=90).read())
    snapshot_brut("geo_mledoze", data)
    print(f"  {len(data)} pays reçus.")

    pays = [(c, _nom_fr(c)) for c in data]
    pays = [(c, n) for c, n in pays if n]

    publie("code_iso_pays", "convention", "mledoze/countries — ISO 3166-1 alpha-2 (cca2)",
           [(n, c.get("cca2", "")) for c, n in pays])
    publie("code_iso3_pays", "convention", "mledoze/countries — ISO 3166-1 alpha-3 (cca3)",
           [(n, c.get("cca3", "")) for c, n in pays])
    # code devise : un pays peut avoir plusieurs devises -> fonctionnel rejette les ambigus (sûr).
    paires_dev = []
    for c, n in pays:
        for code in (c.get("currencies") or {}):
            paires_dev.append((n, code))
    publie("code_devise_pays", "convention", "mledoze/countries — code ISO 4217 du pays",
           paires_dev)
    publie("indicatif_telephonique", "convention", "mledoze/countries — indicatif (idd)",
           [(n, _indicatif(c)) for c, n in pays])
    publie("continent", "physique", "mledoze/countries — région -> continent (FR)",
           [(n, _continent(c)) for c, n in pays])
    # --- relations STABLES surgicales (numériques/conventions, language-neutral, FAUX=0) ---
    # superficie en km² (mesure stable, pas de volatilité type population). Vatican 0.44, Russie 17098242.
    publie("superficie", "physique", "mledoze/countries — superficie (km²)",
           [(n, str(c["area"])) for c, n in pays if c.get("area") is not None])
    # sans littoral : booléen géographique stable -> oui/non.
    publie("sans_littoral", "physique", "mledoze/countries — pays sans littoral (landlocked)",
           [(n, "oui" if c.get("landlocked") else "non") for c, n in pays])
    # domaine internet national = ccTLD officiel ISO = PREMIER tld (canonique, déterministe).
    publie("domaine_internet", "convention", "mledoze/countries — ccTLD officiel (ISO, 1er tld)",
           [(n, (c.get("tld") or [""])[0]) for c, n in pays if (c.get("tld") or [""])[0]])
    # gentilé français = nom des habitants (forme masculine = forme de citation). Convention linguistique FR.
    publie("gentile", "convention", "mledoze/countries — gentilé français (forme masculine)",
           [(n, (c.get("demonyms", {}).get("fra", {}) or {}).get("m", "")) for c, n in pays
            if (c.get("demonyms", {}).get("fra", {}) or {}).get("m")])
    # drapeau (emoji indicateurs régionaux) — définitionnel, language-neutral.
    publie("drapeau_emoji", "convention", "mledoze/countries — drapeau (emoji)",
           [(n, c.get("flag", "")) for c, n in pays if c.get("flag")])
    # code olympique CIO/IOC (3 lettres) — définitionnel (attribué par le CIO).
    publie("code_olympique", "convention", "mledoze/countries — code CIO/IOC (cioc)",
           [(n, c.get("cioc", "")) for c, n in pays if c.get("cioc")])


if __name__ == "__main__":
    ingere_geo()
    print("\nFait. Relancer la non-reg OFFLINE :  python3 _nonreg.py --full --jobs 6")
