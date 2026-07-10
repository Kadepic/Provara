"""
INGESTION MÉTIERS — les AXES de l'ANNEXE M (mandat « traiter tout le backlog des sujets », 2026-07-10 nuit).

SOURCE : Wikidata via QLever. DEUX relations, toutes deux au service de l'AXE « définition et périmètre » :
  • `definition_metier`  — la description française de l'occupation ;
  • `surclasse_metier`   — la (les) sur-classe(s) P279 (« un forgeron de lames est une sorte de forgeron ») :
                           c'est le PÉRIMÈTRE attesté, et il couvre des métiers dont la description manque.

AXE « outils, machines et logiciels » : **NON INGÉRÉ, DÉLIBÉRÉMENT**. La propriété Wikidata P2283 (« uses »)
est sémantiquement trop lâche pour cet axe : mesuré sur les 192 lignes produites par une version antérieure,
elle donne « soliste -> solo », « relieur -> atelier de reliure », « souffleur de verre -> cristallerie »
(un solo n'est pas un outil ; un atelier n'est pas un outil). Publier cela aurait été un FAUX. Au doute :
HORS. L'axe reste NON TRAITÉ et `couverture_borne` le dit. Source réelle à ingérer : ESCO / ROME.

FAUX=0 — CINQ gardes, dans cet ordre. Chacune a attrapé un FAUX RÉEL, mesuré sur le disque (les trois
premières versions de ce script ont produit des faits faux : ils sont documentés ici pour qu'on ne les
réintroduise pas) :

  1. GARDE D'ATTESTATION (la plus importante). On n'ingère QUE les libellés réellement attestés comme
     valeur de `occupation_personne` (donc de P106). SANS elle, la requête typée fait remonter des
     ENTREPRISES et des OBJETS que Wikidata range sous « profession » par conflation de sa propre
     hiérarchie : mesuré, « A.B.C. motorcycles » -> « constructeur britannique de motocyclettes »,
     « 9ff » -> « préparateur automobile », « 4 miséricordes de stalles au Fidelaire » -> « stalles
     monument historique ». Aucun des trois n'est une valeur de P106 : la garde les élimine tous.

  2. GARDE DE TYPE. L'item doit être une occupation (`P31/P279* wd:Q28640`, instance d'une sous-classe de
     « profession »), et n'être ni un nom de famille (Q101352) ni un prénom (Q202444). SANS elle, le store
     fait remonter « Abogado » -> « nom de famille », « Anime », « Armée de l'air » : des valeurs de P106
     qui ne sont PAS des métiers. Ces entrées restent NON TRAITÉES, et `couverture_borne` le DIT.
     (Ne PAS ajouter d'exclusion « organisation » : elle perd « avocat ou avocate », mesuré — la garde 1
     suffit déjà à écarter les entreprises.)

  3. GARDE ANTI-HOMONYME. Un libellé français porté par PLUSIEURS QID d'occupation est REJETÉ (mesuré :
     « intendant », « bâtonnier », « chevalier »). On ne choisit jamais entre deux sens.

  4. GARDE ANTI-DÉFINITION VIDE. Une description qui se réduit à « profession » / « métier » / « occupation »
     ne DÉFINIT rien (mesuré : 226 entrées). Elle est écartée : le métier retombe sur sa sur-classe, et s'il
     n'en a pas, il reste NON TRAITÉ. Refuser une non-réponse vaut mieux que gonfler un compteur.

  5. GARDE DE FONCTIONNALITÉ (héritée de `publie`) : une entité, une valeur. Les sur-classes multiples sont
     rendues comme la LISTE TRIÉE ET JOINTE des valeurs attestées — représentation FIDÈLE de l'ensemble,
     jamais un choix arbitraire parmi elles.

PORTÉE : elle est MESURÉE à chaque rejeu et imprimée ; elle n'est pas promise ici. Les métiers non couverts
restent NON TRAITÉS, entité par entité (`couverture_borne` juge par LOOKUP, jamais par axe en bloc).

Usage : LECTEUR_DATASETS_DIR=... PYTHONPATH=src:ingestion python3 ingestion/ingere_metiers.py
"""
from __future__ import annotations

import collections
import json
import os
import time
import urllib.error
import urllib.parse
import urllib.request

from ingere_wikidata import publie, snapshot_brut

ENDPOINT = "https://qlever.dev/api/wikidata"
UA = "Provara/1.0 (https://github.com/Provara-IA/Provara) offline-knowledge-ingestion"
PREFIXES = ("PREFIX wdt: <http://www.wikidata.org/prop/direct/> "
            "PREFIX wd: <http://www.wikidata.org/entity/> "
            "PREFIX rdfs: <http://www.w3.org/2000/01/rdf-schema#> "
            "PREFIX schema: <http://schema.org/> ")

_GARDE_TYPE = ("?o wdt:P31/wdt:P279* wd:Q28640 . "
               "FILTER NOT EXISTS { ?o wdt:P31 wd:Q101352 } "
               "FILTER NOT EXISTS { ?o wdt:P31 wd:Q202444 } ")

_REQUETE = """SELECT ?o ?l ?d ?sur WHERE {
  %s
  ?o rdfs:label ?l . FILTER(lang(?l) = 'fr')
  OPTIONAL { ?o schema:description ?d . FILTER(lang(?d) = 'fr') }
  OPTIONAL { ?o wdt:P279 ?s . ?s rdfs:label ?sur . FILTER(lang(?sur) = 'fr') }
}""" % _GARDE_TYPE

_ATTESTATION = "occupation_personne"          # la table qui dit quels libellés sont VRAIMENT des métiers

# GARDE 4 : une description qui se réduit à ces mots ne définit RIEN (ce n'est pas un faux, c'est un vide).
_DEFINITIONS_VIDES = frozenset((
    "profession", "métier", "occupation", "activité", "emploi", "travail",
    "métier ou profession", "profession ou métier",
))

SRC_DEF = ("Wikidata/QLever — description française de l'occupation (P31/P279* Q28640 ; patronymes et "
           "prénoms exclus ; homonymes rejetés ; RESTREINT aux métiers attestés par P106 ; descriptions "
           "vides « profession »/« métier » écartées)")
SRC_SUR = ("Wikidata/QLever — sur-classe(s) P279 de l'occupation, périmètre attesté (mêmes gardes ; "
           "valeurs multiples rendues comme liste triée)")


def _qlever(requete: str, timeout: int = 260, essais: int = 6) -> list:
    """QLever avec retry poli sur 429 (rate-limit). Le réseau ne vit QUE dans ce script."""
    url = ENDPOINT + "?action=json_export&query=" + urllib.parse.quote(PREFIXES + requete)
    req = urllib.request.Request(url, headers={"User-Agent": UA,
                                               "Accept": "application/sparql-results+json"})
    for k in range(essais):
        try:
            with urllib.request.urlopen(req, timeout=timeout) as r:
                return json.loads(r.read())["results"]["bindings"]
        except urllib.error.HTTPError as e:
            if e.code == 429:
                time.sleep(10 * (k + 1))
                continue
            raise
    raise RuntimeError("QLever : 429 persistant (rate-limit) — réessayer plus tard")


def metiers_attestes(dossier: str) -> set:
    """GARDE 1 : les libellés RÉELLEMENT attestés comme occupation d'une personne (valeurs de P106)."""
    chemin = os.path.join(dossier, _ATTESTATION + ".jsonl")
    vus = set()
    with open(chemin, encoding="utf-8") as f:
        for ligne in f:
            if ligne.startswith('{"_relation"'):
                continue
            try:
                v = json.loads(ligne)["valeur"]
            except (ValueError, KeyError):
                continue
            if v and "::" not in v and 2 <= len(v) <= 90:
                vus.add(v)
    return vus


def _vide(description: str) -> bool:
    """GARDE 4 : « profession » n'est pas une définition de « peintre décorateur »."""
    return description.strip().lower().rstrip(".") in _DEFINITIONS_VIDES


def collecte(attestes: set):
    """(brut, definitions, surclasses) — les cinq gardes appliquées, tous les comptes imprimés."""
    rows = _qlever(_REQUETE)
    qids = collections.defaultdict(set)
    desc = collections.defaultdict(set)
    sur = collections.defaultdict(set)
    for b in rows:
        lab = b["l"]["value"]
        qids[lab].add(b["o"]["value"])
        if "d" in b:
            desc[lab].add(b["d"]["value"])
        if "sur" in b:
            sur[lab].add(b["sur"]["value"])

    types = set(qids)
    retenus = types & attestes                                   # GARDE 1 : attestation par P106
    non_ambigus = {l for l in retenus if len(qids[l]) == 1}      # GARDE 3 : un libellé, un QID
    print("  occupations typées : %d | attestées P106 : %d | rejetées homonymie : %d"
          % (len(types), len(retenus), len(retenus) - len(non_ambigus)))
    print("  métiers du store NON typés occupation (restent NON TRAITÉS) : %d"
          % len(attestes - types))

    definitions, vides = [], 0
    for l in sorted(non_ambigus):
        if len(desc[l]) != 1:
            continue
        d = next(iter(desc[l]))
        if _vide(d):                                             # GARDE 4 : définition creuse -> écartée
            vides += 1
            continue
        definitions.append((l, d))
    surclasses = [(l, ", ".join(sorted(sur[l]))) for l in sorted(non_ambigus) if sur[l]]
    print("  descriptions VIDES écartées (« profession », « métier »…) : %d" % vides)
    couverts = {l for l, _ in definitions} | {l for l, _ in surclasses}
    print("  AXE « définition et périmètre » couvrable : %d / %d métiers attestés"
          % (len(couverts), len(attestes)))
    return rows, definitions, surclasses


def ingere():
    import lecteur as L
    dossier = L._DOSSIER_DATASETS
    print("== MÉTIERS — définition / sur-classe (5 gardes FAUX=0 ; axe « outils » volontairement NON ingéré) ==")
    attestes = metiers_attestes(dossier)
    print("  métiers attestés (valeurs de P106) : %d" % len(attestes))
    rows, definitions, surclasses = collecte(attestes)
    snapshot_brut("metiers_axes", rows)
    publie("definition_metier", "convention", SRC_DEF, definitions)
    publie("surclasse_metier", "convention", SRC_SUR, surclasses)


if __name__ == "__main__":
    ingere()
