"""
INGESTION `est_metier` — L'ORACLE DE MÉTIER QUI MANQUAIT.

POURQUOI CE FICHIER EXISTE (faux de MESURE, trouvé le 2026-07-12).

`outils/genere_sujets.py` peuplait l'ANNEXE M en prenant **chaque valeur distincte** de la table
`occupation_personne` pour un métier. Deux familles de valeurs n'en sont pas :

  1. LES ÉNUMÉRATIONS FABRIQUÉES. `ingestion/ingere_celebres.py` réécrit la table pour les personnalités
     célèbres et joint leurs occupations : « Einstein -> physicien, professeur d'université et philosophe ».
     Le FAIT est vrai (Einstein fut bien les trois). Mais la VALEUR n'est pas un métier : c'est une liste de
     métiers. Mesuré : 2 207 valeurs composées, dont aucune n'est un libellé Wikidata (vérifié : la requête
     `?item rdfs:label "acteur ou actrice de cinéma, acteur ou actrice de théâtre et acteur ou actrice de
     genre"@fr` ne rend AUCUN item).

  2. LE BRUIT DE P106. Wikidata range sous P106 des valeurs qui ne sont pas des occupations : « Abogado »
     (nom de famille), « Anime », « Armée de l'air ». `ingere_metiers.py` le documente déjà et conclut :
     « ces entrées restent NON TRAITÉES ». C'est la mauvaise conclusion. Un nom de famille ne pourra
     JAMAIS être traité : ni sa définition, ni ses gestes, ni ses risques professionnels n'existent.
     Le compter comme sujet à traiter fabrique du backlog structurellement inépuisable — donc une MESURE
     FAUSSE. Un sujet faux est aussi grave qu'un fait faux : il ment sur ce qui reste à faire.

`ingere_metiers.py` prenait `occupation_personne` pour « la table qui dit quels libellés sont VRAIMENT des
métiers ». Cet oracle contenait précisément les deux familles ci-dessus. Seule sa garde de TYPE le sauvait.
Ce script publie l'oracle sain, une fois pour toutes.

UNE RELATION : `est_metier` — entité « <libellé fr> » -> le(s) QID(s) d'occupation qui le portent.

FAUX=0 — la définition est celle de la garde de type, et RIEN d'autre :
    ?o wdt:P31/wdt:P279* wd:Q28640      (instance d'une sous-classe de « profession »)
    NOT EXISTS { ?o wdt:P31 wd:Q101352 }   (nom de famille)
    NOT EXISTS { ?o wdt:P31 wd:Q202444 }   (prénom)

  • ON NE FILTRE PAS L'HOMONYMIE ICI. « professeur » est porté par plusieurs QID : c'est quand même un
    métier. L'homonymie interdit d'en publier LA définition (garde 3 d'`ingere_metiers`), elle n'interdit
    pas d'en faire un sujet. Les QID sont joints, triés : la valeur est fidèle à l'ensemble.

  • ON N'INVENTE AUCUNE DÉCOMPOSITION. Une énumération fabriquée n'est pas « réparée » en la découpant :
    découper « acteur ou actrice, basketteur ou basketteuse et athlète professionnel » supposerait que la
    virgule sépare toujours des métiers — or « Employés de réception, guichetiers et assimilés » est UN
    libellé CITP unique. Au doute, on ne coupe pas : on demande à la source si le libellé existe.

  • CE SCRIPT N'EFFACE RIEN. `occupation_personne` garde ses valeurs (elles sont vraies). C'est la
    GÉNÉRATION DES SUJETS qui filtrera, par lookup dans `est_metier`.

Usage : LECTEUR_DATASETS_DIR=... PYTHONPATH=src:ingestion python3 ingestion/ingere_metiers_attestes.py
"""
from __future__ import annotations

import collections
import json
import time
import urllib.error
import urllib.parse
import urllib.request

from ingere_wikidata import publie, snapshot_brut

ENDPOINT = "https://qlever.dev/api/wikidata"
UA = "Provara/1.0 (https://github.com/Provara-IA/Provara) offline-knowledge-ingestion"
PREFIXES = ("PREFIX wdt: <http://www.wikidata.org/prop/direct/> "
            "PREFIX wd: <http://www.wikidata.org/entity/> "
            "PREFIX rdfs: <http://www.w3.org/2000/01/rdf-schema#> ")

# La MÊME garde de type que `ingere_metiers.py`. Une seule définition du mot « métier » dans le projet.
_GARDE_TYPE = ("?o wdt:P31/wdt:P279* wd:Q28640 . "
               "FILTER NOT EXISTS { ?o wdt:P31 wd:Q101352 } "
               "FILTER NOT EXISTS { ?o wdt:P31 wd:Q202444 } ")

_REQUETE = """SELECT ?o ?l WHERE {
  %s
  ?o rdfs:label ?l . FILTER(lang(?l) = 'fr')
}""" % _GARDE_TYPE

SRC = ("Wikidata/QLever — libellés français des occupations (P31/P279* Q28640 ; patronymes Q101352 et "
       "prénoms Q202444 exclus). ORACLE de la question « ce libellé est-il un métier ? ». Les valeurs de "
       "P106 qui n'y figurent pas (noms de famille, énumérations jointes par `ingere_celebres`) ne sont "
       "PAS des métiers et ne peuvent donc pas être des sujets-métiers. Homonymie conservée : plusieurs "
       "QID pour un libellé restent un métier.")


def _rangs(charge: dict, variables) -> list:
    """QLever sert DEUX formes selon la version : `res` (lignes brutes, littéraux balisés « "x"@fr ») et le
    SPARQL-JSON standard (`results.bindings`). Mesuré le 2026-07-12 : l'endpoint rend désormais la seconde.
    Lire une seule des deux rend une table VIDE sans lever — le pire des échecs. On lit les deux."""
    if "res" in charge:
        return [[_texte(c) for c in ligne] for ligne in charge["res"]]
    b = charge.get("results", {}).get("bindings", [])
    return [[m.get(v, {}).get("value", "") for v in variables] for m in b]


def _qlever(requete: str, variables, timeout: int = 300, essais: int = 6) -> list:
    url = ENDPOINT + "?action=json_export&query=" + urllib.parse.quote(PREFIXES + requete)
    for k in range(essais):
        try:
            req = urllib.request.Request(url, headers={"User-Agent": UA, "Accept": "application/json"})
            with urllib.request.urlopen(req, timeout=timeout) as r:
                return _rangs(json.loads(r.read().decode("utf-8")), variables)
        except (urllib.error.URLError, urllib.error.HTTPError, TimeoutError,
                ConnectionError, json.JSONDecodeError, OSError):
            if k == essais - 1:
                raise
            time.sleep(4 * (k + 1))
    return []


def _qid(uri: str) -> str:
    return uri.rsplit("/", 1)[-1].strip("<>")


def _texte(litteral: str) -> str:
    """« "boulanger"@fr » -> « boulanger ». La forme `res` de QLever rend les littéraux balisés."""
    s = litteral
    if s.startswith('"'):
        s = s[1:]
        i = s.rfind('"')
        if i >= 0:
            s = s[:i]
    return s


def collecte() -> list:
    lignes = _qlever(_REQUETE, ("o", "l"))
    par_label = collections.defaultdict(set)
    for l in lignes:
        if len(l) < 2 or not l[0] or not l[1]:
            continue
        par_label[l[1]].add(_qid(l[0]))
    paires = [(lab, ", ".join(sorted(q))) for lab, q in par_label.items() if lab and "::" not in lab]
    homonymes = sum(1 for _, v in paires if ", " in v)
    print("  libellés d'occupation attestés : %d (dont %d homonymes multi-QID)" % (len(paires), homonymes))
    return sorted(paires)


def ingere():
    print("== ORACLE DE MÉTIER — libellés attestés (Wikidata P31/P279* Q28640) ==")
    paires = collecte()
    if len(paires) < 1000:
        raise ValueError("oracle suspect : %d libellés seulement — refus de publier une table tronquée "
                         "qui déclarerait « non-métier » des métiers réels" % len(paires))
    snapshot_brut("est_metier", [{"libelles": len(paires)}])
    publie("est_metier", "convention", SRC, paires)


if __name__ == "__main__":
    ingere()
