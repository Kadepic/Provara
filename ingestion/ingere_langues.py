"""
INGESTION LANGUES — « famille et parenté d'une langue » + « nombre de locuteurs » (PARTIE VII).

SOURCE : Wikidata via QLever.

TROIS RELATIONS :
  • `famille_immediate_langue` — la famille IMMÉDIATE (P279 vers un item typé « famille de langues »,
                         Q25295) : « le français est une langue d'oïl ». NOMMÉE AINSI DEPUIS LE 2026-07-12.
                         Elle s'appelait `famille_langue` et ÉCRASAIT SILENCIEUSEMENT la table curée du
                         même nom (`ingere_langues_famille.py`, 81 langues, grandes familles) : même
                         relation, deux sémantiques, `ecrit_jsonl` régénère le fichier -> dernier écrivain
                         gagne. Le store répondait « famille de l'anglais : langues angliques » là où la
                         gate `valide_lecteur` attend « germanique ». Le nom disait plus que le contenu :
                         le péché même que ce fichier dénonce trois lignes plus bas pour `parente_langue`.
  • `locuteurs_langue` — le nombre de locuteurs, **TOUJOURS DATÉ**.

LA PARENTÉ COMPLÈTE N'EST PAS PUBLIÉE, ET C'EST UNE DÉCISION. On voulait la chaîne « français < langue d'oïl
< ... < indo-européen ». Mesuré : Wikidata ne la porte pas de façon exploitable — « langue d'oïl » n'a AUCUN
parent typé famille, et « langues sémitiques » remonte à « langue humaine », un nœud terminal vide de sens
généalogique. Une table nommée `parente_langue` qui ne contiendrait que la famille immédiate serait une
SUR-PROMESSE : le nom dirait plus que le contenu. Elle a été produite (4 446 lignes) puis SUPPRIMÉE.
Le sujet « famille ET parenté d'une langue » reste donc PARTIEL, et `couverture_borne` le dit.

FAUX=0 — deux disciplines distinctes, parce que les deux sujets n'ont pas la même nature :

  A. LA FAMILLE EST UN FAIT STABLE. « Le français descend du latin » ne changera pas. Gardes : une langue
     (P31 wd:Q34770) ; une famille non ambiguë (plusieurs familles pour un même libellé -> REJET, mesuré :
     122 libellés dont « norvégien ») ; libellé français exact.

  B. LE NOMBRE DE LOCUTEURS EST UNE VÉRITÉ DATÉE. Un compte non daté devient FAUX avec le temps : ce serait
     un faux différé, la pire espèce (il passe les tests le jour où on l'écrit). Donc :
       • on n'ingère QUE les déclarations portant un qualificatif de date (pq:P585) — mesuré : 1 055 des
         1 553 déclarations littérales en portent une ; les 498 autres sont ÉCARTÉES, sans regret ;
       • on retient la déclaration la PLUS RÉCENTE ; si deux valeurs distinctes coexistent à la même année
         (critères de comptage différents : locuteurs natifs vs total), on REJETTE la langue — on ne choisit
         pas entre deux définitions ;
       • la valeur publiée PORTE l'année : « 80 000 000 locuteurs (2022) ». Ainsi la donnée reste vraie
         indéfiniment : c'est une mesure datée, pas une prétention au présent.
     Les nœuds blancs Wikidata (valeur « inconnue ») sont écartés : ils ne sont pas des littéraux.

Usage : LECTEUR_DATASETS_DIR=... PYTHONPATH=src:ingestion python3 ingestion/ingere_langues.py
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
            "PREFIX p: <http://www.wikidata.org/prop/> "
            "PREFIX ps: <http://www.wikidata.org/prop/statement/> "
            "PREFIX pq: <http://www.wikidata.org/prop/qualifier/> "
            "PREFIX rdfs: <http://www.w3.org/2000/01/rdf-schema#> ")

_LANGUE = "wd:Q34770"          # langue
_FAMILLE = "wd:Q25295"         # famille de langues

SRC_FAM = "Wikidata/QLever — famille immédiate de la langue (P279 vers un item famille Q25295 ; homonymes rejetés)"
SRC_LOC = ("Wikidata/QLever — nombre de locuteurs P1098, DATÉ par le qualificatif pq:P585 (déclaration la plus "
           "récente ; valeurs concurrentes à la même année rejetées ; valeurs non datées ÉCARTÉES)")


def _qlever(requete: str, timeout: int = 260, essais: int = 6) -> list:
    url = ENDPOINT + "?action=json_export&query=" + urllib.parse.quote(PREFIXES + requete)
    req = urllib.request.Request(url, headers={"User-Agent": UA, "Accept": "application/sparql-results+json"})
    for k in range(essais):
        try:
            with urllib.request.urlopen(req, timeout=timeout) as r:
                return json.loads(r.read())["results"]["bindings"]
        except urllib.error.HTTPError as e:
            if e.code == 429:
                time.sleep(10 * (k + 1))
                continue
            raise
    raise RuntimeError("QLever : 429 persistant")


def familles():
    """famille IMMÉDIATE par langue — libellés FR, familles concurrentes écartées."""
    lignes = _qlever("""SELECT ?lab ?flab WHERE {
      ?l wdt:P31 %s . ?l rdfs:label ?lab . FILTER(lang(?lab) = 'fr')
      ?l wdt:P279 ?f . ?f wdt:P31 %s . ?f rdfs:label ?flab . FILTER(lang(?flab) = 'fr')
    }""" % (_LANGUE, _FAMILLE))
    par_langue = collections.defaultdict(set)
    for b in lignes:
        par_langue[b["lab"]["value"]].add(b["flab"]["value"])
    ambigus = [l for l, f in par_langue.items() if len(f) > 1]
    familles = {l: next(iter(f)) for l, f in par_langue.items() if len(f) == 1}
    print("  langues avec famille : %d | rejetées (familles concurrentes) : %d"
          % (len(familles), len(ambigus)))

    return familles


def locuteurs():
    """Nombre de locuteurs DATÉ : déclaration la plus récente, valeurs concurrentes rejetées."""
    lignes = _qlever("""SELECT ?lab ?v ?d WHERE {
      ?l wdt:P31 %s . ?l rdfs:label ?lab . FILTER(lang(?lab) = 'fr')
      ?l p:P1098 ?st . ?st ps:P1098 ?v . FILTER(isLiteral(?v))
      ?st pq:P585 ?d .
    }""" % _LANGUE)
    par_langue = collections.defaultdict(list)
    for b in lignes:
        try:
            n = int(float(b["v"]["value"]))
            annee = int(b["d"]["value"][:4].lstrip("+").lstrip("-") or 0)
        except (ValueError, KeyError):
            continue
        if n > 0 and 1800 <= annee <= 2100:
            par_langue[b["lab"]["value"]].append((annee, n))

    out, concurrents = [], 0
    for langue, obs in par_langue.items():
        recente = max(a for a, _ in obs)
        valeurs = {n for a, n in obs if a == recente}
        if len(valeurs) != 1:                                    # deux critères de comptage -> on ne tranche pas
            concurrents += 1
            continue
        n = next(iter(valeurs))
        out.append((langue, "%d locuteurs (%d)" % (n, recente)))
    print("  langues avec locuteurs DATÉS : %d | rejetées (valeurs concurrentes) : %d"
          % (len(out), concurrents))
    return sorted(out)


def ingere():
    print("== LANGUES — famille, parenté, locuteurs (datés) ==")
    fam = familles()
    time.sleep(3)
    locs = locuteurs()
    snapshot_brut("langues_axes", [{"familles": len(fam), "locuteurs": len(locs)}])
    publie("famille_immediate_langue", "convention", SRC_FAM, sorted(fam.items()))
    publie("locuteurs_langue", "passe", SRC_LOC, locs)


if __name__ == "__main__":
    ingere()
