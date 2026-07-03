"""
INGESTION WIKIDATA -> datasets/lecteur/*.jsonl  (ONLINE — lancé À LA MAIN, jamais à l'import du lecteur).

ARCHITECTURE (cf. REPRISE.MD §PHASE INGESTION) : le RÉSEAU ne vit QUE dans ce script. Il télécharge via
SPARQL, filtre, réconcilie avec l'amorce, et ÉCRIT des fichiers `datasets/lecteur/<relation>.jsonl`
self-describing. Le `lecteur.py` les CHARGE ensuite 100 % OFFLINE (auto-découverte). Donc : non-reg et
validateurs tournent sans réseau ; l'ingestion est reproductible (snapshot brut sous datasets/_raw/).

SOUNDNESS (FAUX=0, structurel) :
  • FONCTIONNEL : on ne garde qu'un fait par entité s'il a UNE seule valeur distincte (P36 capitale, P38
    monnaie…). Les entités multivaluées (2 langues officielles, 2 continents…) sont REJETÉES (HORS honnête),
    jamais un choix arbitraire.
  • RÉCONCILIATION AMORCE : une valeur divergente d'une entité DÉJÀ dans l'amorce canonique n'écrase pas et
    n'est PAS chargée — elle part dans `datasets/_conflits/<relation>.jsonl` pour audit humain (souvent une
    simple variante de surface : « dollar des États-Unis » vs « dollar americain »). Idempotent si identique.
  • SOURCE CITÉE : chaque table porte sa source (Wikidata + propriété P…), comme physique.py cite CODATA.
  • ANCRES + SANITÉS : assurées côté `valide_lecteur.py` (échantillon vérifié à la main + invariants
    structurels : codes ISO uniques 2 lettres, Z contigus, etc.).

Usage : `python3 ingere_wikidata.py geo`  (puis relancer la non-reg offline).
"""
from __future__ import annotations

import json
import lzma
import os
import re
import sys
import tempfile
import time
import urllib.error
import urllib.parse
import urllib.request

from base_faits import normalise, _sans_articles
os.environ.setdefault("LECTEUR_AMORCE_SEULE", "1")  # OPTIM T9 : ingestion = amorce seule (cf. lecteur.py) -> import ~instant, RAM~0
import lecteur as L
import sources

UA = "VERAX/1.0 (https://github.com/Verax-IA/Verax) offline-knowledge-ingestion"
DOSSIER = L._DOSSIER_DATASETS                                   # datasets/lecteur/
RACINE = os.path.dirname(DOSSIER)                               # datasets/
RAW = os.path.join(RACINE, "_raw")                             # snapshots bruts (repro/trace)
CONFLITS = os.path.join(RACINE, "_conflits")                  # divergences amorce <-> source (audit)
ENDPOINT = sources.url("wikidata-wdqs")                        # endpoint lu DEPUIS le registre, pas en dur


def sparql(query: str, timeout: int = 180, essais: int = 6) -> list[dict]:
    """Exécute une requête SPARQL, renvoie la liste des bindings. Retry POLI : sur 429 (rate-limit / outage
    WDQS = 1 req/min en ce moment), on attend 65 s ; sinon backoff doux. Le réseau ne vit QUE ici."""
    url = ENDPOINT + "?format=json&query=" + urllib.parse.quote(query)
    req = urllib.request.Request(url, headers={
        "User-Agent": UA, "Accept": "application/sparql-results+json"})
    derniere = None
    for k in range(essais):
        try:
            with urllib.request.urlopen(req, timeout=timeout) as r:
                return json.loads(r.read())["results"]["bindings"]
        except urllib.error.HTTPError as e:
            derniere = e
            attente = 65 if e.code == 429 else 5 * (k + 1)
            print(f"    HTTP {e.code} — attente {attente}s (essai {k+1}/{essais})…", flush=True)
            time.sleep(attente)
        except Exception as e:                                  # noqa: BLE001 (retry réseau)
            derniere = e
            print(f"    erreur réseau {e!r} — retry (essai {k+1}/{essais})…", flush=True)
            time.sleep(5 * (k + 1))
    raise RuntimeError(f"SPARQL échec après {essais} essais : {derniere!r}")


def val(row: dict, cle: str) -> str:
    return (row.get(cle, {}) or {}).get("value", "").strip()


def fonctionnel(paires) -> tuple[list[tuple[str, str]], int]:
    """Ne garde qu'un fait par entité ssi UNE seule valeur distincte (fonctionnel). Renvoie
    (paires gardées [(surface, valeur)], nb d'entités rejetées pour multivaluation)."""
    vals: dict[str, set[str]] = {}
    surface: dict[str, str] = {}
    for ent, v in paires:
        ent = (ent or "").strip()
        v = (v or "").strip()
        if not ent or not v:
            continue
        cle = _sans_articles(ent)
        vals.setdefault(cle, set()).add(v)
        surface.setdefault(cle, ent)
    gardees, rejets = [], 0
    for cle, s in vals.items():
        if len(s) == 1:
            gardees.append((surface[cle], next(iter(s))))
        else:
            rejets += 1
    gardees.sort(key=lambda p: _sans_articles(p[0]))
    return gardees, rejets


def reconcilie(relation: str, paires, articles: bool = True):
    """Compare à l'AMORCE canonique (lecteur.amorce_cherche, hors datasets auto-chargés -> stable).
    Renvoie (a_ecrire [(surface,val)], conflits [(surface,val_source,val_amorce)])."""
    a_ecrire, conflits = [], []
    for ent, v in paires:
        existant = L.amorce_cherche(relation, ent)
        if existant is None:
            a_ecrire.append((ent, v))
        elif existant.valeur == str(v):
            a_ecrire.append((ent, v))                          # identique : on (ré)écrit, reste idempotent
        else:
            conflits.append((ent, str(v), existant.valeur))
    return a_ecrire, conflits


def ecrit_jsonl(relation: str, categorie: str, source: str, paires, articles: bool = True) -> int:
    """Écrit datasets/lecteur/<relation>.jsonl SELF-DESCRIBING (en-tête + faits). Régénère tout le fichier
    (déterministe depuis le pull). Renvoie le nb de faits écrits."""
    os.makedirs(DOSSIER, exist_ok=True)
    chemin = os.path.join(DOSSIER, relation + ".jsonl")
    lignes = [json.dumps({"_relation": relation, "_categorie": categorie, "_source": source,
                          "_articles": articles}, ensure_ascii=False)]
    for ent, v in paires:
        lignes.append(json.dumps({"entite": ent, "valeur": v}, ensure_ascii=False))
    # Écriture ATOMIQUE : tmp (même dossier) + os.replace. Un crash/OOM/disque-plein en cours d'écriture ne
    # laisse JAMAIS un .jsonl tronqué (le lecteur auto-charge sans try/except) ni ne détruit la table valide
    # précédente (open('w') la tronquerait AVANT d'avoir réécrit). Motif déjà éprouvé dans 24 scripts du projet.
    fd, tmp = tempfile.mkstemp(dir=DOSSIER, suffix=".tmp")
    with os.fdopen(fd, "w", encoding="utf-8") as fh:
        fh.write("\n".join(lignes) + "\n")
    os.replace(tmp, chemin)
    return len(paires)


def ecrit_conflits(relation: str, conflits) -> None:
    if not conflits:
        return
    os.makedirs(CONFLITS, exist_ok=True)
    with open(os.path.join(CONFLITS, relation + ".jsonl"), "w", encoding="utf-8") as fh:
        for ent, vs, va in conflits:
            fh.write(json.dumps({"entite": ent, "valeur_source": vs, "valeur_amorce": va},
                                ensure_ascii=False) + "\n")


def publie(relation, categorie, source, paires_brutes, articles=True, garde_multi=False):
    """Pipeline complet d'une relation : fonctionnel -> réconciliation amorce -> écriture + audit.
    Renvoie un dict de stats. `garde_multi` n'est PAS implémenté (toujours fonctionnel) — réservé."""
    fonc, rej_multi = fonctionnel(paires_brutes)
    a_ecrire, conflits = reconcilie(relation, fonc, articles=articles)
    n = ecrit_jsonl(relation, categorie, source, a_ecrire, articles=articles)
    ecrit_conflits(relation, conflits)
    stats = {"relation": relation, "ecrits": n, "rejets_multivalue": rej_multi, "conflits_amorce": len(conflits)}
    print(f"  [{relation:24s}] écrits={n:4d}  rejets_multi={rej_multi:3d}  conflits_amorce={len(conflits):3d}"
          + (f"  -> _conflits/{relation}.jsonl" if conflits else ""))
    return stats


def snapshot_brut(nom: str, rows: list) -> None:
    """Sauve le brut SPARQL (repro/trace)."""
    os.makedirs(RAW, exist_ok=True)
    with open(os.path.join(RAW, nom + ".json"), "w", encoding="utf-8") as fh:
        json.dump(rows, fh, ensure_ascii=False)


def charge_raw_json(chemin_json: str):
    """Lit un snapshot brut _raw en gérant l'ARCHIVAGE COMPRESSÉ : `chemin.json.xz` (lzma, 100 % stdlib) s'il
    existe, sinon `chemin.json` non compressé, sinon None. Compression xz mesurée ×18 (lossless, roundtrip
    vérifié) -> ~5,9 Go récupérés sur les 6,2 Go de _raw ; décompression ~385 Mo/s (rejeu offline rare).
    Transparent pour les pipelines : rejeu identique que le snapshot soit compressé ou non."""
    xz = chemin_json + ".xz"
    if os.path.exists(xz):
        with lzma.open(xz, "rt", encoding="utf-8") as fh:
            return json.load(fh)
    if os.path.exists(chemin_json):
        with open(chemin_json, encoding="utf-8") as fh:
            return json.load(fh)
    return None


# ============================================================================================
#  DOMAINE : GÉOGRAPHIE — états souverains (Q3624078). Une requête, plusieurs relations.
# ============================================================================================
_Q_GEO_FR = """
SELECT ?cLabel ?capLabel ?curLabel ?langLabel WHERE {
  ?c wdt:P31 wd:Q3624078 .
  OPTIONAL { ?c wdt:P36 ?cap . }
  OPTIONAL { ?c wdt:P38 ?cur . }
  OPTIONAL { ?c wdt:P37 ?lang . }
  SERVICE wikibase:label { bd:serviceParam wikibase:language "fr". }
}
"""


def ingere_geo():
    """Complète la géo par les relations qui exigent du FRANÇAIS (capitale, monnaie, langue officielle).
    Les relations neutres en langue (codes ISO, indicatif, continent) sont faites par ingere_geo.py (mledoze)
    -> on NE les réécrit PAS ici (pas de clobber). Wikidata = source des labels FR."""
    print("== GÉOGRAPHIE FR (Wikidata, états souverains Q3624078 — capitale/monnaie/langue) ==")
    rows = sparql(_Q_GEO_FR)
    snapshot_brut("geo_pays_fr", rows)
    print(f"  {len(rows)} lignes brutes (multivaluées) reçues.")
    SRC = "Wikidata (états souverains Q3624078)"
    publie("capitale",          "physique",   SRC + " — capitale P36",            [(val(r, "cLabel"), val(r, "capLabel")) for r in rows])
    publie("monnaie",           "convention", SRC + " — monnaie P38 (label FR)",  [(val(r, "cLabel"), val(r, "curLabel")) for r in rows])
    publie("langue_officielle", "convention", SRC + " — langue officielle P37",   [(val(r, "cLabel"), val(r, "langLabel")) for r in rows])


# ============================================================================================
#  DOMAINE : ÉLÉMENTS CHIMIQUES (Q11344) — numéro atomique (entier exact) + symbole. Étend l'amorce
#  française (43 -> 118 éléments) ; les éléments communs CROISENT l'amorce (idempotent ou conflit audité).
# ============================================================================================
_Q_ELEMENTS = """
SELECT ?eLabel ?z ?sym WHERE {
  ?e wdt:P31 wd:Q11344 ; wdt:P1086 ?z .
  OPTIONAL { ?e wdt:P246 ?sym . }
  SERVICE wikibase:label { bd:serviceParam wikibase:language "fr". }
} ORDER BY xsd:integer(?z)
"""


def _charge_ou_fetch(nom: str, query: str) -> list:
    """Réutilise le snapshot brut datasets/_raw/<nom>.json s'il existe (régénération 100% OFFLINE, ne
    re-tape PAS WDQS rate-limité) ; sinon pull SPARQL + snapshot."""
    chemin = os.path.join(RAW, nom + ".json")
    rows = charge_raw_json(chemin)
    if rows is not None:
        print(f"  [snapshot réutilisé : {nom}.json{'.xz' if os.path.exists(chemin + '.xz') else ''} — {len(rows)} lignes, offline]")
        return rows
    rows = sparql(query)
    snapshot_brut(nom, rows)
    return rows


def _est_qid(label: str) -> bool:
    """Label = Q-ID nu (entité sans libellé FR) -> inutilisable comme nom français, on rejette."""
    return bool(re.fullmatch(r"Q\d+", label or ""))


def ingere_elements():
    print("== ÉLÉMENTS CHIMIQUES (Wikidata Q11344) ==")
    rows = _charge_ou_fetch("elements", _Q_ELEMENTS)
    print(f"  {len(rows)} lignes brutes.")
    # SOUNDNESS : seuls les 118 éléments CONFIRMÉS (Z 1..118). On rejette les éléments hypothétiques non
    # synthétisés (noms systématiques unbibium=122…, Z>118) et les entités sans libellé FR (Q-IDs nus).
    confirmes = [r for r in rows
                 if val(r, "z").isdigit() and 1 <= int(val(r, "z")) <= 118 and not _est_qid(val(r, "eLabel"))]
    publie("numero_atomique", "physique", "Wikidata — numéro atomique P1086 (entier exact, Z≤118 confirmés)",
           [(val(r, "eLabel"), val(r, "z")) for r in confirmes])
    publie("symbole_chimique", "convention", "Wikidata — symbole d'élément P246 (Z≤118 confirmés)",
           [(val(r, "eLabel"), val(r, "sym")) for r in confirmes if val(r, "sym")])


# ============================================================================================
#  DOMAINE : GÉOGRAPHIE PHYSIQUE — point culminant de chaque état souverain (P610). Fait BORNÉ
#  (le sommet le plus haut d'un territoire est fixé par la réalité). Fonctionnel : 1 point/pays.
# ============================================================================================
_Q_SOMMETS = """
SELECT ?cLabel ?sommetLabel WHERE {
  ?c wdt:P31 wd:Q3624078 ; wdt:P610 ?sommet .
  SERVICE wikibase:label { bd:serviceParam wikibase:language "fr". }
}
"""


def ingere_sommets():
    print("== POINTS CULMINANTS PAR PAYS (Wikidata P610) ==")
    rows = _charge_ou_fetch("sommets", _Q_SOMMETS)
    print(f"  {len(rows)} lignes brutes.")
    # on écarte les libellés = Q-ID nu (sommet sans nom FR) -> jamais d'entité illisible.
    paires = [(val(r, "cLabel"), val(r, "sommetLabel")) for r in rows
              if val(r, "sommetLabel") and not _est_qid(val(r, "sommetLabel"))]
    publie("point_culminant", "physique", "Wikidata — point culminant du pays P610", paires)


_DOMAINES = {
    "geo": ingere_geo,
    "elements": ingere_elements,
    "sommets": ingere_sommets,
}


if __name__ == "__main__":
    cibles = sys.argv[1:] or ["geo"]
    for c in cibles:
        if c not in _DOMAINES:
            print(f"domaine inconnu : {c} (dispo : {sorted(_DOMAINES)})")
            continue
        _DOMAINES[c]()
    print("\nFait. Relancer la non-reg OFFLINE :  python3 _nonreg.py --full --jobs 6")
