"""
PONT D'INGESTION REST (NON-SPARQL) — datasets/lecteur/*.jsonl via l'API MediaWiki/Wikidata.

POURQUOI : QLever ET WDQS (les deux endpoints SPARQL) peuvent être en outage/saturation simultanée. Le RÉSEAU,
lui, reste bon : l'API REST Wikidata répond en ~0,5 s. Ce module est la SOURCE DE SECOURS, factuelle (Wikidata
réel, pas une devinette), qui n'utilise PAS SPARQL :

  1. action=query&list=search&srsearch=haswbstatement:P31=Qxxx  -> les Q-ID d'une classe (CirrusSearch, paginé).
  2. action=wbgetentities&ids=...(<=50/lot)&props=labels|claims&languages=fr -> labels FR + claims (faits).

AUTONOME ET LÉGER : ce module n'importe PAS le lecteur (dont l'import charge 16 M faits / 622 Mo). Il ne dépend
que de base_faits (_sans_articles, pur). Il réimplémente `fonctionnel` + l'écriture jsonl à l'identique de
ingere_wikidata. Pas de réconciliation amorce : on n'ingère par ce pont que des relations NEUVES (l'amorce
canonique ne les contient pas -> 0 conflit possible).

SOUNDNESS (patron DATE, FAUX=0) :
  (a) claim de précision >= 9 (année) — on ne devine pas une année depuis un siècle/décennie ;
  (b) entité à >1 année DISTINCTE pour la même propriété -> HORS (fonctionnel) ;
  (c) PLAGE historique [ymin, ymax] ;
  (d) filtre d'honnêteté de libellé (dates/années nues -> HORS) ;
  (e) ANCRES vérité-terrain dans valide_lecteur (non circulaire).

OFFLINE : chaque fetch est snapshoté dans datasets/_raw_rest/<relation>.json (liste [label_fr, annee]).
La republication se fait ENSUITE 100 % offline depuis ce snapshot (republie_date_rest).

Limite : CirrusSearch plafonne sroffset à ~10 000. Au-delà, DÉCOUPER par sous-filtre (ex. + P17=<pays>) ;
toute troncature est JOURNALISÉE (jamais de cap silencieux).
"""
from __future__ import annotations

import json
import lzma
import os
import re
import tempfile
import time
import urllib.parse
import urllib.request

from base_faits import _sans_articles  # pur (regex/normalisation) — n'importe PAS le lecteur

API = "https://www.wikidata.org/w/api.php"
UA = "Provara/1.0 (https://github.com/Provara-IA/Provara) base-perso ; ingestion factuelle Wikidata"
_ICI = os.path.dirname(os.path.abspath(__file__))
DOSSIER = os.path.join(_ICI, "datasets", "lecteur")
RAW_REST = os.path.join(_ICI, "datasets", "_raw_rest")

# --- filtre d'honnêteté de libellé (dupliqué de ingere_t8 pour rester autonome/léger) -----------------
_MOIS_CALENDRIER = {
    "janvier", "février", "mars", "avril", "mai", "juin", "juillet", "août",
    "septembre", "octobre", "novembre", "décembre",
    "farvardin", "ordibehesht", "khordad", "tir", "mordad", "shahrivar",
    "mehr", "aban", "azar", "dey", "bahman", "esfand",
    "tishri", "tichri", "heshvan", "marheshvan", "kislev", "tevet", "tévet", "shevat", "chevat",
    "adar", "nisan", "iyar", "iyyar", "sivan", "tammuz", "tamouz", "av", "elul", "eloul",
}
_JOUR_MOIS_AN = re.compile(r"^\d{1,2}(?:er)?\s+(\S+)\s+\d{3,4}$")
_MOIS_AN = re.compile(r"^(\S+)\s+\d{3,4}$")
_ANNEE_NUE = re.compile(r"^-?\d{1,4}$")


def est_date_nue(libelle: str) -> bool:
    """True si le libellé est une DATE/ANNÉE nue (pas un événement/entité nommé)."""
    s = libelle.strip()
    if _ANNEE_NUE.match(s):
        return True
    m = _JOUR_MOIS_AN.match(s)
    if m and m.group(1).casefold() in _MOIS_CALENDRIER:
        return True
    m = _MOIS_AN.match(s)
    if m and m.group(1).casefold() in _MOIS_CALENDRIER:
        return True
    return False


# --- réseau (le réseau ne vit QUE ici) ---------------------------------------------------------------
def _get(params: dict, essais: int = 4):
    url = API + "?" + urllib.parse.urlencode({**params, "format": "json"})
    derniere = None
    for k in range(essais):
        try:
            req = urllib.request.Request(url, headers={"User-Agent": UA})
            with urllib.request.urlopen(req, timeout=40) as r:
                return json.loads(r.read())
        except Exception as e:           # noqa: BLE001 — réseau : backoff + retry
            derniere = e
            time.sleep(2 * (k + 1))
    raise RuntimeError(f"API REST échec après {essais} essais : {derniere}")


def cirrus_qids(statement: str, cap: int = 10000) -> list[str]:
    """Q-ID des entités vérifiant `statement` (ex. 'haswbstatement:P31=Q7278'), paginé. JOURNALISE la
    troncature si la classe dépasse ce qu'on récolte (jamais de cap muet)."""
    qids, offset, total = [], 0, None
    while len(qids) < cap:
        d = _get({"action": "query", "list": "search", "srsearch": statement,
                  "srlimit": 500, "sroffset": offset, "srinfo": "totalhits", "srprop": ""})
        if total is None:
            total = d.get("query", {}).get("searchinfo", {}).get("totalhits")
        hits = d.get("query", {}).get("search", [])
        if not hits:
            break
        qids.extend(h["title"] for h in hits)
        cont = d.get("continue", {}).get("sroffset")
        if cont is None:
            break
        offset = cont
    if total is not None and total > len(qids):
        print(f"  [TRONCATURE journalisée] {statement} : {total} entités, {len(qids)} récoltées "
              f"(plafond CirrusSearch/cap). Découper par sous-filtre pour le reste.")
    return qids[:cap]


def _annee_du_temps(time_str: str):
    """'+1854-03-20T00:00:00Z' -> '1854' ; '-0753-01-01T...' -> '-753'. None si non parsable."""
    s = (time_str or "").strip()
    signe = 1
    if s and s[0] in "+-":
        if s[0] == "-":
            signe = -1
        s = s[1:]
    tete = s.split("-", 1)[0]
    if not tete.isdigit():
        return None
    return str(signe * int(tete))


def _annee_fonctionnelle(claims: dict, prop: str, precision_min: int = 9):
    """Année UNIQUE et fiable d'une propriété date, ou None (précision < année, ou >1 année distincte)."""
    annees = set()
    for cl in claims.get(prop, []):
        snak = cl.get("mainsnak", {})
        if snak.get("snaktype") != "value":
            continue
        val = snak.get("datavalue", {}).get("value", {})
        if val.get("precision", 0) < precision_min:
            continue
        an = _annee_du_temps(val.get("time", ""))
        if an is not None:
            annees.add(an)
    return next(iter(annees)) if len(annees) == 1 else None


def _lots(seq, n=50):
    for i in range(0, len(seq), n):
        yield seq[i:i + n]


def qids_par_decoupe(classe_qid, decoupe_prop, decoupe_qids, cap_par=10000):
    """Union des Q-ID de la classe en DÉCOUPANT par (decoupe_prop=chaque decoupe_qid) — contourne le plafond
    CirrusSearch de ~10 000 sur la classe entière (ex. parti politique 23 779 récolté pays par pays via P17)."""
    vus = set()
    for dq in decoupe_qids:
        stmt = f"haswbstatement:P31={classe_qid} haswbstatement:{decoupe_prop}={dq}"
        vus.update(cirrus_qids(stmt, cap=cap_par))
    print(f"  [découpe {decoupe_prop}×{len(decoupe_qids)}] {len(vus)} Q-ID uniques (P31={classe_qid})")
    return sorted(vus)


def collecte_date_rest(relation, classe_qid, prop_date, cap=10000, filtre_extra="", qids=None):
    """Pont -> liste [label_fr, annee] (paires brutes). filtre_extra : statement ANDé (ex. P17=Q142).
    `qids` : si fourni (ex. union d'un découpage), court-circuite CirrusSearch sur la classe entière."""
    if qids is None:
        stmt = f"haswbstatement:P31={classe_qid}" + (f" {filtre_extra}" if filtre_extra else "")
        qids = cirrus_qids(stmt, cap=cap)
    print(f"  {relation}: {len(qids)} Q-ID. Récupération labels+{prop_date} par lots de 50…")
    paires = []
    for lot in _lots(qids, 50):
        d = _get({"action": "wbgetentities", "ids": "|".join(lot),
                  "props": "labels|claims", "languages": "fr"})
        for _q, ent in d.get("entities", {}).items():
            lab = ent.get("labels", {}).get("fr", {}).get("value")
            if not lab:
                continue
            an = _annee_fonctionnelle(ent.get("claims", {}), prop_date)
            if an is not None:
                paires.append([lab, an])
    return paires


# --- écriture (réimplémente fonctionnel + ecrit_jsonl de ingere_wikidata, à l'identique) --------------
def _fonctionnel(paires):
    vals, surface = {}, {}
    for ent, v in paires:
        ent, v = (ent or "").strip(), (str(v) or "").strip()
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


def _ecrit_jsonl(relation, categorie, source, paires, articles=True):
    os.makedirs(DOSSIER, exist_ok=True)
    lignes = [json.dumps({"_relation": relation, "_categorie": categorie, "_source": source,
                          "_articles": articles}, ensure_ascii=False)]
    for ent, v in paires:
        lignes.append(json.dumps({"entite": ent, "valeur": v}, ensure_ascii=False))
    # Écriture ATOMIQUE (tmp + os.replace) : jamais de .jsonl tronqué ni de table valide détruite en cas de
    # crash/OOM/disque-plein pendant l'écriture. Même motif que le writer central Wikidata.
    fd, tmp = tempfile.mkstemp(dir=DOSSIER, suffix=".tmp")
    with os.fdopen(fd, "w", encoding="utf-8") as fh:
        fh.write("\n".join(lignes) + "\n")
    os.replace(tmp, os.path.join(DOSSIER, relation + ".jsonl"))
    return len(paires)


def _snapshot(relation, paires):
    os.makedirs(RAW_REST, exist_ok=True)
    with open(os.path.join(RAW_REST, relation + ".json"), "w", encoding="utf-8") as fh:
        json.dump(paires, fh, ensure_ascii=False)


def _charge_snapshot(relation):
    # Lit .json.xz (archivage compressé, stdlib lzma) sinon .json sinon None — rejeu offline transparent.
    chemin = os.path.join(RAW_REST, relation + ".json")
    xz = chemin + ".xz"
    if os.path.isfile(xz):
        with lzma.open(xz, "rt", encoding="utf-8") as fh:
            return json.load(fh)
    if not os.path.isfile(chemin):
        return None
    with open(chemin, encoding="utf-8") as fh:
        return json.load(fh)


def _publie_date(relation, paires_brutes, source, ymin, ymax, categorie="passe"):
    gardees, rej_libelle, hors_plage = [], 0, 0
    for lab, an in paires_brutes:
        if est_date_nue(lab):
            rej_libelle += 1
            continue
        if ymin <= int(an) <= ymax:
            gardees.append((lab, an))
        else:
            hors_plage += 1
    fonc, rej_multi = _fonctionnel(gardees)
    n = _ecrit_jsonl(relation, categorie, source, fonc)
    print(f"== {relation} : {len(paires_brutes)} brutes -> {n} écrits "
          f"({rej_libelle} libellé-nu, {hors_plage} hors-plage, {rej_multi} multi-année -> HORS) ==")
    return {"relation": relation, "ecrits": n, "rejets_multivalue": rej_multi,
            "rejets_libelle": rej_libelle, "hors_plage": hors_plage}


def ingere_date_rest(relation, classe_qid, prop_date, source, ymin, ymax, categorie="passe",
                     cap=10000, filtre_extra="", qids=None):
    """ONLINE : pont REST -> snapshot -> publie (puis republiable 100 % offline)."""
    paires = collecte_date_rest(relation, classe_qid, prop_date, cap=cap, filtre_extra=filtre_extra, qids=qids)
    _snapshot(relation, paires)
    return _publie_date(relation, paires, source, ymin, ymax, categorie=categorie)


def republie_date_rest(relation, source, ymin, ymax, categorie="passe"):
    """OFFLINE : republie depuis le snapshot _raw_rest (aucun réseau)."""
    paires = _charge_snapshot(relation)
    if paires is None:
        raise FileNotFoundError(f"pas de snapshot _raw_rest pour {relation}")
    print(f"  [snapshot REST réutilisé : {relation}.json — {len(paires)} paires, offline]")
    return _publie_date(relation, paires, source, ymin, ymax, categorie=categorie)


# ============================================================================================
#  PATRON ENTITÉ -> ENTITÉ (relation fonctionnelle, ex. pays d'un parti P17, forme de gouvernement P122).
#  Garde-fous FAUX=0 : (a) fonctionnel (1 seule valeur Q-ID distincte par entité, sinon HORS) ;
#  (b) la valeur résout en un libellé FR de ≥2 caractères ; (c) anti-auto-référence (entité != valeur) ;
#  (d) ancres dans le validateur. Le label de la valeur (un Q-ID dans le claim) est résolu par un 2e lot.
# ============================================================================================
def _claim_qids(claims: dict, prop: str) -> list[str]:
    """Q-ID des valeurs (entités) d'une propriété (snaktype=value, datatype wikibase-entityid)."""
    out = []
    for cl in claims.get(prop, []):
        snak = cl.get("mainsnak", {})
        if snak.get("snaktype") != "value":
            continue
        qid = snak.get("datavalue", {}).get("value", {}).get("id")
        if qid:
            out.append(qid)
    return out


def collecte_entite_rest(relation, classe_qid, prop, cap=10000, filtre_extra="", qids=None):
    """Pont -> liste [label_source_fr, label_valeur_fr], fonctionnel (1 valeur distincte) + anti-auto-réf.
    `qids` : si fourni, court-circuite CirrusSearch (ex. union d'un découpage par pays)."""
    if qids is None:
        stmt = f"haswbstatement:P31={classe_qid}" + (f" {filtre_extra}" if filtre_extra else "")
        qids = cirrus_qids(stmt, cap=cap)
    print(f"  {relation}: {len(qids)} Q-ID. Lecture {prop} + résolution des libellés…")
    src_label, src_val, val_qids = {}, {}, set()
    for lot in _lots(qids, 50):
        d = _get({"action": "wbgetentities", "ids": "|".join(lot),
                  "props": "labels|claims", "languages": "fr"})
        for q, ent in d.get("entities", {}).items():
            lab = ent.get("labels", {}).get("fr", {}).get("value")
            if not lab:
                continue
            vals = set(_claim_qids(ent.get("claims", {}), prop))
            if len(vals) == 1:                       # fonctionnel : 1 seule valeur distincte
                v = next(iter(vals))
                src_label[q], src_val[q] = lab, v
                val_qids.add(v)
    # 2e passe : résoudre le libellé FR de chaque Q-ID valeur (peu nombreux, batché)
    val_label = {}
    for lot in _lots(sorted(val_qids), 50):
        d = _get({"action": "wbgetentities", "ids": "|".join(lot),
                  "props": "labels", "languages": "fr"})
        for q, ent in d.get("entities", {}).items():
            lab = ent.get("labels", {}).get("fr", {}).get("value")
            if lab:
                val_label[q] = lab
    paires = []
    for q, lab in src_label.items():
        vlab = val_label.get(src_val[q])
        if vlab and len(vlab.strip()) >= 2 and vlab != lab:   # valeur résolue, ≥2 car., anti-auto-réf
            paires.append([lab, vlab])
    return paires


def _publie_entite(relation, paires_brutes, source, categorie="convention"):
    fonc, rej_multi = _fonctionnel(paires_brutes)
    n = _ecrit_jsonl(relation, categorie, source, fonc)
    print(f"== {relation} : {len(paires_brutes)} brutes -> {n} écrits ({rej_multi} multi-valeur -> HORS) ==")
    return {"relation": relation, "ecrits": n, "rejets_multivalue": rej_multi}


def ingere_entite_rest(relation, classe_qid, prop, source, categorie="convention", cap=10000,
                       filtre_extra="", qids=None):
    """ONLINE : pont REST entité->entité -> snapshot -> publie (puis republiable offline)."""
    paires = collecte_entite_rest(relation, classe_qid, prop, cap=cap, filtre_extra=filtre_extra, qids=qids)
    _snapshot(relation, paires)
    return _publie_entite(relation, paires, source, categorie=categorie)


def republie_entite_rest(relation, source, categorie="convention"):
    """OFFLINE : republie depuis le snapshot _raw_rest (aucun réseau)."""
    paires = _charge_snapshot(relation)
    if paires is None:
        raise FileNotFoundError(f"pas de snapshot _raw_rest pour {relation}")
    print(f"  [snapshot REST réutilisé : {relation}.json — {len(paires)} paires, offline]")
    return _publie_entite(relation, paires, source, categorie=categorie)
