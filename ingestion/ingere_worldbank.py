"""
INGESTION BANQUE MONDIALE -> datasets/lecteur/*.jsonl (ONLINE, lancé à la main). SOUVERAIN (urllib, API sans clé).

BUT : débloquer les moteurs éco/démo qui tournent À VIDE (demographie.densite_population, pib.pib_par_habitant,
taux_dependance…) faute de données-pays. Le premier pivot manquant = `population_pays`.

FAUX=0 / VOLATILITÉ : la population est VOLATILE (l'auteur de la géo l'avait sciemment exclue). On prend la valeur
la PLUS RÉCENTE par pays (paramètre `mrnev=1`) et on TRACE son millésime dans la source — c'est un instantané DATÉ
et provenancé, jamais servi comme « live ». La densité qu'on en dérive évolue lentement (~1 %/an) -> honnête.

ALIGNEMENT DES CLÉS : la Banque mondiale donne la valeur par code ISO-3 ; on la mappe vers le NOM FR via
`code_iso3_pays.jsonl` (mledoze) — donc `population_pays` a EXACTEMENT les mêmes clés que `superficie.jsonl` (même
source de noms) -> `ia.densite_pays` fonctionne. Les agrégats (« Arab World », « Africa Eastern »…) ont un ISO-3
hors mapping -> automatiquement écartés.

Usage : python3 ingere_worldbank.py    puis non-reg OFFLINE (snapshot rejoué).
"""
from __future__ import annotations

import json
import os
import urllib.request

from ingere_wikidata import RAW, charge_raw_json, publie, snapshot_brut

UA = "verax/1.0 (souverain; urllib)"
_URL = "https://api.worldbank.org/v2/country/all/indicator/{ind}?format=json&per_page=400&mrnev=1"
_LECT = os.path.join(os.path.dirname(os.path.abspath(__file__)), "datasets", "lecteur")


def _fetch(indicateur: str, nom_snapshot: str):
    """Rejoue le snapshot offline s'il existe, sinon tape l'API Banque mondiale + snapshot."""
    rows = charge_raw_json(os.path.join(RAW, nom_snapshot + ".json"))
    if rows is not None:
        print(f"  [snapshot réutilisé : {nom_snapshot} — {len(rows)} lignes, offline]")
        return rows
    url = _URL.format(ind=indicateur)
    req = urllib.request.Request(url, headers={"User-Agent": UA})
    donnee = json.loads(urllib.request.urlopen(req, timeout=60).read())
    rows = donnee[1] if isinstance(donnee, list) and len(donnee) > 1 else []
    snapshot_brut(nom_snapshot, rows)
    return rows


def _iso3_vers_fr() -> dict:
    """ISO-3 -> nom FR, depuis code_iso3_pays.jsonl (mledoze) = mêmes noms que superficie.jsonl."""
    d = {}
    chemin = os.path.join(_LECT, "code_iso3_pays.jsonl")
    with open(chemin, encoding="utf-8") as fh:
        for ligne in fh:
            o = json.loads(ligne)
            if "entite" in o and o.get("valeur"):
                d[o["valeur"].strip().upper()] = o["entite"]
    return d


def ingere_population():
    print("== POPULATION PAR PAYS (Banque mondiale SP.POP.TOTL, valeur la plus récente) ==")
    rows = _fetch("SP.POP.TOTL", "wb_population")
    iso2fr = _iso3_vers_fr()
    paires, annees, rejets = [], [], 0
    for x in rows:
        iso3 = (x.get("countryiso3code") or "").strip().upper()
        val = x.get("value")
        nom = iso2fr.get(iso3)
        if nom and val is not None:                    # ISO-3 mappé = vrai pays (agrégats écartés)
            try:
                paires.append((nom, str(int(round(float(val))))))
            except (TypeError, ValueError):
                rejets += 1
                continue
            if x.get("date"):
                annees.append(str(x["date"]))
        else:
            rejets += 1
    millesime = f"{min(annees)}–{max(annees)}" if annees else "récent"
    print(f"  {len(paires)} pays retenus, {rejets} écartés (agrégats / ISO-3 hors mapping / valeur nulle).")
    publie("population_pays", "physique",
           f"Banque mondiale SP.POP.TOTL — valeur la plus récente par pays (millésime {millesime} ; "
           f"valeur VOLATILE, instantané daté, non « live »)",
           paires)


# ————————————————— EXTENSION ÉCO/SOCIAL (nuit 2026-07-03) : mêmes garde-fous que la population —————————————————
# Chaque indicateur = valeur la plus récente par pays (mrnev=1), mappé ISO-3 -> nom FR (agrégats écartés),
# millésime tracé dans la source (VOLATILE = instantané daté, jamais « live »). Débloque les moteurs à vide :
# pib.py (pib_par_habitant), chomage.py, inflation.py (taux fournis), mesures_sociales.py (Gini).
_INDICATEURS = [
    # (code Banque mondiale, snapshot, relation lecteur, format valeur, libellé de source)
    ("NY.GDP.MKTP.CD", "wb_pib", "pib_pays",
     lambda v: str(int(round(float(v)))), "PIB en dollars US courants"),
    ("NY.GDP.PCAP.CD", "wb_pib_hab", "pib_par_habitant_pays",
     lambda v: f"{float(v):.2f}", "PIB par habitant en dollars US courants"),
    ("SL.UEM.TOTL.ZS", "wb_chomage", "taux_chomage_pays",
     lambda v: f"{float(v):.2f}", "taux de chômage en % de la population active (estimation OIT)"),
    ("FP.CPI.TOTL.ZG", "wb_inflation", "taux_inflation_pays",
     lambda v: f"{float(v):.2f}", "inflation annuelle des prix à la consommation en %"),
    ("SP.DYN.LE00.IN", "wb_esperance_vie", "esperance_vie_pays",
     lambda v: f"{float(v):.1f}", "espérance de vie à la naissance en années"),
    ("SI.POV.GINI", "wb_gini", "indice_gini_pays",
     lambda v: f"{float(v):.1f}", "indice de Gini (0-100, inégalités de revenu)"),
]


def ingere_indicateur(indicateur, snapshot, relation, fmt, libelle):
    """Ingestion GÉNÉRIQUE d'un indicateur Banque mondiale -> relation par pays (recette population_pays)."""
    print(f"== {relation} (Banque mondiale {indicateur}, valeur la plus récente) ==")
    rows = _fetch(indicateur, snapshot)
    iso2fr = _iso3_vers_fr()
    paires, annees, rejets = [], [], 0
    for x in rows:
        iso3 = (x.get("countryiso3code") or "").strip().upper()
        val = x.get("value")
        nom = iso2fr.get(iso3)
        if nom and val is not None:                    # ISO-3 mappé = vrai pays (agrégats écartés)
            try:
                paires.append((nom, fmt(val)))
            except (TypeError, ValueError):
                rejets += 1
                continue
            if x.get("date"):
                annees.append(str(x["date"]))
        else:
            rejets += 1
    millesime = f"{min(annees)}–{max(annees)}" if annees else "récent"
    print(f"  {len(paires)} pays retenus, {rejets} écartés (agrégats / ISO-3 hors mapping / valeur nulle).")
    publie(relation, "physique",
           f"Banque mondiale {indicateur} — {libelle} ; valeur la plus récente par pays "
           f"(millésime {millesime} ; valeur VOLATILE, instantané daté, non « live »)",
           paires)


def ingere_economie():
    for indicateur, snapshot, relation, fmt, libelle in _INDICATEURS:
        ingere_indicateur(indicateur, snapshot, relation, fmt, libelle)


if __name__ == "__main__":
    ingere_population()
    ingere_economie()
