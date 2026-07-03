"""
INGESTION T9 — LEXÈMES Wikidata -> datasets/lecteur/{categorie_lexicale_mot,genre_grammatical_mot}.jsonl (ONLINE).

POURQUOI : le couloir LANGUE avait été sondé sur les ITEMS (P31=Q34770). Mais le LEXIQUE vit sur les LEXÈMES
(L-entities : ontolex:LexicalEntry), une classe JAMAIS sondée -> grosse veine manquée (cf. leçon T10 « ne pas
conclure épuisé trop vite »). QLever indexe 1,53 M lexèmes.

CIBLES :
  • categorie_lexicale_mot : lemme -> catégorie grammaticale (1,64 M lignes, fonctionnel 99-100 %).
  • genre_grammatical_mot  : lemme -> genre grammatical (P5185 ; 700 k lexèmes, fonctionnel 98 %), MULTILINGUE
    (≠ genre_grammatical kaikki = FR seul).

FAUX=0 — la clé « lemme » seule est ambiguë INTER-langues (« chat » FR/EN). On désambiguïse par CLÉ COMPOSÉE
« lemme (langue) ». Le `fonctionnel` de `publie` rejette tout (lemme, langue) à valeurs multiples (homographes).
Nettoyage des valeurs : on ne garde que celles à >= _SEUIL_CAT occurrences hors blacklist (écarte le BRUIT :
labels FR manquants « Plura »/« Noun »/« nom »-comme-genre, non-grammaticaux « A »/« 看 », concepts « couleur »...).
`articles=False` : un lemme n'est pas une entité à articles.

Usage : python3 ingere_t9_lexemes.py [categorie] [genre]   (défaut : les deux ; gate lourde : importe lecteur).
"""
from __future__ import annotations

import collections
import json
import sys
import time
import urllib.parse
import urllib.request

from ingere_wikidata import publie

ENDPOINT = "https://qlever.cs.uni-freiburg.de/api/wikidata"
PREF = ("PREFIX wikibase: <http://wikiba.se/ontology#>\n"
        "PREFIX dct: <http://purl.org/dc/terms/>\n"
        "PREFIX ontolex: <http://www.w3.org/ns/lemon/ontolex#>\n"
        "PREFIX rdfs: <http://www.w3.org/2000/01/rdf-schema#>\n"
        "PREFIX wdt: <http://www.wikidata.org/prop/direct/>\n")
UA = "VERAX/1.0 (https://github.com/Verax-IA/Verax) offline-knowledge-ingestion"

_SEUIL_CAT = 20                                  # une vraie valeur grammaticale a >= 20 occurrences ; la traîne = bruit
_BLACKLIST = {"Plura", "Noun", "Nomina"}         # labels en langue étrangère qui passent le seuil

# Requêtes : ?lemma (lemme), ?ll (libellé FR de la langue), ?vl (libellé FR de la valeur : catégorie ou genre).
_BASE_CAT = ('SELECT ?lemma ?ll ?vl WHERE { ?l a ontolex:LexicalEntry ; wikibase:lemma ?lemma ; '
             'dct:language ?lang ; wikibase:lexicalCategory ?v . '
             '?lang rdfs:label ?ll . FILTER(lang(?ll)="fr") ?v rdfs:label ?vl . FILTER(lang(?vl)="fr") }')
_BASE_GENRE = ('SELECT ?lemma ?ll ?vl WHERE { ?l a ontolex:LexicalEntry ; wikibase:lemma ?lemma ; '
               'dct:language ?lang ; wdt:P5185 ?v . '
               '?lang rdfs:label ?ll . FILTER(lang(?ll)="fr") ?v rdfs:label ?vl . FILTER(lang(?vl)="fr") }')
# Concept du sens (P5137 « item pour ce sens ») : le libellé FR du concept = le SENS du mot (et, pour une langue
# non-FR, sa traduction française). Volume modéré (~316 k sens), fonctionnel 99 %.
_BASE_CONCEPT = ('SELECT ?lemma ?ll ?vl WHERE { ?l a ontolex:LexicalEntry ; wikibase:lemma ?lemma ; '
                 'dct:language ?lang ; ontolex:sense ?s . ?s wdt:P5137 ?v . '
                 '?lang rdfs:label ?ll . FILTER(lang(?ll)="fr") ?v rdfs:label ?vl . FILTER(lang(?vl)="fr") }')
# Étymon (P5191 « dérivé de ») : le mot-source dont dérive ce mot (jointure -> lemma de l'étymon). Fonctionnel 75 %
# (mots multi-étymons -> HORS) ; ~22 k faits mono-étymon. Étymon souvent en grec/latin/akkadien (Unicode OK).
_BASE_ETYMON = ('SELECT ?lemma ?ll ?vl WHERE { ?l a ontolex:LexicalEntry ; wikibase:lemma ?lemma ; '
                'dct:language ?lang ; wdt:P5191 ?e . ?e wikibase:lemma ?vl . '
                '?lang rdfs:label ?ll . FILTER(lang(?ll)="fr") }')


def _q(query, timeout=300):
    url = ENDPOINT + "?action=json_export&query=" + urllib.parse.quote(PREF + query)
    req = urllib.request.Request(url, headers={"User-Agent": UA, "Accept": "application/sparql-results+json"})
    with urllib.request.urlopen(req, timeout=timeout) as r:
        return json.loads(r.read())["results"]["bindings"]


def _collecte(base, nettoyage="seuil"):
    paires, off, STEP = [], 0, 250000
    while True:
        t0 = time.time()
        rows = _q(base + f" LIMIT {STEP} OFFSET {off}")
        for x in rows:
            lem = x.get("lemma", {}).get("value")
            ll = x.get("ll", {}).get("value")
            vl = x.get("vl", {}).get("value")
            if lem and ll and vl:
                paires.append((f"{lem} ({ll})", vl))
        print(f"  offset {off}: +{len(rows)} en {time.time()-t0:.0f}s (cumul {len(paires)})")
        if len(rows) < STEP:
            break
        off += STEP
    avant = len(paires)
    if nettoyage == "seuil":
        # Petit ensemble fermé de valeurs grammaticales : garder celles à >= seuil (la traîne rare = bruit).
        cnt = collections.Counter(v for _, v in paires)
        paires = [(k, v) for k, v in paires if cnt[v] >= _SEUIL_CAT and v not in _BLACKLIST]
        propres = len({v for _, v in paires})
        print(f"  filtre seuil (>= {_SEUIL_CAT} occ, hors {_BLACKLIST}) : {avant} -> {len(paires)} ({propres} valeurs)")
    else:
        # Valeurs DIVERSES (concepts) : pas de seuil ; filtre de PROPRETÉ du libellé (pas de ':' meta, longueur saine).
        def _ok(v):
            return 1 <= len(v) <= 60 and ":" not in v and any(c.isalpha() for c in v)
        paires = [(k, v) for k, v in paires if _ok(v)]
        print(f"  filtre propreté libellé : {avant} -> {len(paires)}")
    return paires


def ingere_categorie():
    publie("categorie_lexicale_mot", "convention",
           "Wikidata/QLever lexèmes — catégorie lexicale du mot (clé « lemme (langue) » ; homographe -> HORS)",
           _collecte(_BASE_CAT), articles=False)


def ingere_genre():
    publie("genre_grammatical_mot", "convention",
           "Wikidata/QLever lexèmes — genre grammatical du mot P5185 (clé « lemme (langue) » ; multilingue ; ambigu -> HORS)",
           _collecte(_BASE_GENRE), articles=False)


def ingere_concept():
    publie("concept_du_mot", "convention",
           "Wikidata/QLever lexèmes — concept du mot (sens P5137, libellé FR ; clé « lemme (langue) » ; polysémie -> HORS)",
           _collecte(_BASE_CONCEPT, nettoyage="propre"), articles=False)


def ingere_etymon():
    publie("etymon_du_mot", "convention",
           "Wikidata/QLever lexèmes — étymon du mot P5191 (mot-source ; clé « lemme (langue) » ; multi-étymon -> HORS)",
           _collecte(_BASE_ETYMON, nettoyage="propre"), articles=False)


_CIBLES = {"categorie": ingere_categorie, "genre": ingere_genre, "concept": ingere_concept, "etymon": ingere_etymon}

if __name__ == "__main__":
    for c in (sys.argv[1:] or list(_CIBLES)):
        if c in _CIBLES:
            _CIBLES[c]()
        else:
            print(f"cible inconnue : {c} (dispo : {sorted(_CIBLES)})")
