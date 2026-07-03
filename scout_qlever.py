"""
SCOUT D'INGESTION QLever — automatise la DILIGENCE FAUX=0 sur un LOT de relations candidates « X -> pays »
(mandat Yohan 2026-06-25 : « avancer le plus efficacement possible »). Le goulot des nuits d'ingestion n'est
pas l'écriture (3 fabriques génériques le font déjà) mais la MESURE manuelle qui précède chaque `publie` :
densité réelle, valeurs distinctes, taux fonctionnel, ajustement à l'ensemble fermé des pays, échantillon à
l'œil, anti-collision. Ce module FAIT cette mesure pour N candidats d'un coup et rend un VERDICT par candidat
-> on concentre le jugement humain sur la shortlist au lieu d'écrire une requête de sonde à la main par relation.

CE QU'IL NE FAIT PAS (par sûreté, FAUX=0 inchangé) : il N'INGÈRE RIEN et NE CACHE RIEN sous le nom de la
relation (les sondes vont dans `datasets/_scout/`, jamais dans `datasets/_raw/` que lit l'ingestion réelle ->
zéro risque de publier une sonde tronquée). La décision d'accepter reste un jugement ; l'ingestion réelle passe
ensuite par `ingere_qlever._ingere_x_vers_pays` (données COMPLÈTES) puis `valide_lecteur` + la gate = les juges.

LEÇONS ENCODÉES (de REPRISE.MD / [[project-ia-ingestion-sources]]) :
  • « LE COUNT MENT » : une classe peut être dense mais MENSONGÈRE (Q14745 « réacteur » = retables d'église,
    Q1311670 « dépôt » = villages). -> on n'affiche pas qu'un compte : on montre un ÉCHANTILLON déterministe ET
    la fraction des valeurs qui sont de VRAIS pays (closed-set fit). Une classe mensongère a un fit BAS.
  • « HOMONYMES » : un libellé portant >1 pays -> `fonctionnel` le met en HORS (voulu). On mesure le taux
    fonctionnel pour anticiper combien on perd.
  • « ANTI-COLLISION » : avant tout domaine, `grep` le nom de relation dans *.py (ne pas écraser une table).
"""
from __future__ import annotations

import json
import os
import subprocess
import sys
import urllib.parse
import urllib.request

# AUTONOME (2026-06-26) : on N'importe PLUS ingere_qlever au niveau module — sa chaîne d'import
# (ingere_qlever -> ingere_wikidata -> `import lecteur`) charge ~19 M faits / ~3,4 Go À L'IMPORT, ce qui
# rend un simple scout RÉSEAU lourd et lent sous charge CPU (cause des timeouts du 2026-06-26). Le scout
# n'a besoin que de ces constantes/helpers, dont aucun ne touche le lecteur. (qlever() reste importé
# paresseusement dans decouvre() seulement.) ENDPOINT migré vers qlever.dev (l'ancien hôte fait un 308
# que urllib ne suit pas).
import re

ENDPOINT = "https://qlever.dev/api/wikidata"
PREFIXES = ("PREFIX wdt: <http://www.wikidata.org/prop/direct/>\n"
            "PREFIX wd: <http://www.wikidata.org/entity/>\n"
            "PREFIX rdfs: <http://www.w3.org/2000/01/rdf-schema#>\n")
UA = "VERAX/1.0 (https://github.com/Verax-IA/Verax) offline-knowledge-ingestion"


def val(row: dict, cle: str) -> str:
    return (row.get(cle, {}) or {}).get("value", "").strip()


def _est_qid(label: str) -> bool:
    """Label = Q-ID nu (entité sans libellé FR) -> inutilisable comme nom français."""
    return bool(re.fullmatch(r"Q\d+", label or ""))

_SCOUT = os.path.join(os.path.dirname(os.path.abspath(__file__)), "datasets", "_scout")
_HARN = os.path.dirname(os.path.abspath(__file__))


def _pays_ref() -> set[str]:
    """Ensemble fermé de référence des pays (les ~198 états souverains actuels), lu depuis le lecteur déjà chargé
    (table X->pays existante). Sert le test « closed-set fit » : une valeur qui n'est pas un pays connu = suspecte."""
    import lecteur as L
    for rel in ("nationalite_personne", "pays_ville", "pays_lac"):
        t = L.LECTEUR.tables.get(rel)
        if t is not None:
            return set(t._labels) if hasattr(t, "_labels") else {f.valeur for f in t.values()}
    return set()


def _fetch(relation: str, classe_qid: str, prop: str, limite: int) -> list:
    """Sonde QLever « entité (classe_qid) -> pays souverain » AVEC LIMIT (mesure rapide, estimation). Cache dans
    `datasets/_scout/` (PAS dans _raw) -> ne pollue jamais l'ingestion réelle. La requête reflète exactement la
    fabrique `_ingere_x_vers_pays` (mêmes filtres P31/P279*, valeur=Q3624078)."""
    os.makedirs(_SCOUT, exist_ok=True)
    chemin = os.path.join(_SCOUT, f"{relation}.json")
    if os.path.exists(chemin):
        with open(chemin, encoding="utf-8") as fh:
            return json.load(fh)
    q = f"""SELECT ?eLabel ?vLabel WHERE {{
      ?e wdt:P31/wdt:P279* wd:{classe_qid} ; wdt:{prop} ?p .
      ?p wdt:P31 wd:Q3624078 .
      ?p rdfs:label ?vLabel . FILTER(lang(?vLabel)="fr")
      ?e rdfs:label ?eLabel . FILTER(lang(?eLabel)="fr")
    }} LIMIT {limite}"""
    url = ENDPOINT + "?action=json_export&query=" + urllib.parse.quote(PREFIXES + q)
    req = urllib.request.Request(url, headers={"User-Agent": UA, "Accept": "application/sparql-results+json"})
    with urllib.request.urlopen(req, timeout=120) as r:
        rows = json.loads(r.read())["results"]["bindings"]
    with open(chemin, "w", encoding="utf-8") as fh:
        json.dump(rows, fh, ensure_ascii=False)
    return rows


def _qids_deja_faits() -> set[str]:
    """Les QID de classe déjà câblés (lus dans `ingere_qlever.py`) -> exclus de la découverte (anti-redondance).
    Robuste : on prend tout Q\\d+ apparaissant dans une ligne `_ingere_x_vers_pays(...)` ou un appel de fabrique."""
    import re
    qids = set()
    chemin = os.path.join(_HARN, "ingere_qlever.py")
    with open(chemin, encoding="utf-8") as fh:
        for ligne in fh:
            if "pays_" in ligne or "_ingere_x_vers" in ligne or "classe" in ligne:
                qids.update(re.findall(r"\bQ\d+\b", ligne))
    return qids


# Étiquettes de classes GÉNÉRIQUES / administratives à ignorer d'office en découverte (ni bornées proprement,
# ni « X -> pays » à valeur unique : entités multi-pays, méta-pages Wikimédia, types abstraits).
_BRUIT_CLASSE = ("liste", "wikimédia", "wikimedia", "organisation", "entreprise", "bâtiment", "maison",
                 "structure architecturale", "établissement humain", "type de", "fonction", "saison",
                 "patent", "statutory", "épreuve", "essai clinique", "bien culturel", "page de")


def decouvre(prop: str = "P17", valeur_classe: str = "Q3624078", top: int = 60,
             exclure: set[str] | None = None) -> list[tuple[str, str, int]]:
    """DÉCOUVERTE : les classes d'entités les plus NOMBREUSES ayant `prop` -> (instance de `valeur_classe`),
    triées par effectif, MOINS les classes déjà ingérées et le bruit générique. Renvoie [(qid, label, n)].
    C'est le moteur qui fait PROPOSER les filons par la donnée au lieu de deviner des QID."""
    from ingere_qlever import qlever
    exclure = (exclure or set()) | _qids_deja_faits()
    q = f"""SELECT ?c ?cLabel (COUNT(?e) AS ?n) WHERE {{
      ?e wdt:{prop} ?p . ?p wdt:P31 wd:{valeur_classe} .
      ?e wdt:P31 ?c .
      ?c rdfs:label ?cLabel . FILTER(lang(?cLabel)="fr")
    }} GROUP BY ?c ?cLabel ORDER BY DESC(?n) LIMIT {top}"""
    out = []
    for r in qlever(q, timeout=140):
        qid = val(r, "c").rsplit("/", 1)[-1]
        label = val(r, "cLabel")
        n = int(val(r, "n") or 0)
        if qid in exclure or not label:
            continue
        if any(b in label.lower() for b in _BRUIT_CLASSE):
            continue
        out.append((qid, label, n))
    return out


def _echantillon_det(paires: list[tuple[str, str]], k: int) -> list[tuple[str, str]]:
    """k paires DÉTERMINISTES (reproductibles) : on trie puis on prend k indices régulièrement espacés -> couvre
    tout l'alphabet des entités, pas seulement le début. Sert l'inspection à l'œil (anti-classe-mensongère)."""
    uniq = sorted(set(paires))
    if len(uniq) <= k:
        return uniq
    pas = len(uniq) / k
    return [uniq[int(i * pas)] for i in range(k)]


def collision(relation: str) -> list[str]:
    """Fichiers .py qui mentionnent déjà ce nom de relation (anti-écrasement). Vide = libre."""
    try:
        out = subprocess.run(["grep", "-rln", relation, _HARN, "--include=*.py"],
                             capture_output=True, text=True, timeout=30).stdout
    except (OSError, subprocess.SubprocessError):
        return []
    # on s'exclut soi-même (le LOT de candidats listé dans ce fichier n'est pas une vraie ingestion).
    return [b for b in (os.path.basename(x) for x in out.split() if x) if b != "scout_qlever.py"]


def sonde(relation: str, classe_qid: str, prop: str = "P17", limite: int = 6000, k: int = 6) -> dict:
    """Mesure un candidat « X -> pays » et rend un rapport + verdict. Estimation sur ≤`limite` lignes (l'ingestion
    réelle prendra TOUT). FAUX=0 : ne publie/cache rien d'exploitable par l'ingestion."""
    rows = _fetch(relation, classe_qid, prop, limite)
    paires = [(val(r, "eLabel"), val(r, "vLabel")) for r in rows
              if val(r, "eLabel") and val(r, "vLabel")
              and not _est_qid(val(r, "eLabel")) and not _est_qid(val(r, "vLabel"))]
    # taux fonctionnel : entités à valeur UNIQUE (les multi-valeurs partiront en HORS via `fonctionnel`).
    par_ent: dict[str, set] = {}
    for e, v in paires:
        par_ent.setdefault(e, set()).add(v)
    n_ent = len(par_ent)
    fonctionnels = sum(1 for vs in par_ent.values() if len(vs) == 1)
    valeurs = [v for vs in par_ent.values() for v in vs]
    distinctes = sorted(set(valeurs))
    ref = _pays_ref()
    hors_ref = sorted(set(distinctes) - ref) if ref else []
    closed_fit = (len(distinctes) - len(hors_ref)) / len(distinctes) if distinctes else 0.0
    coll = collision(relation)
    verdict, raisons = "PROPRE", []
    if n_ent < 30:
        verdict, _ = "FAIBLE", raisons.append(f"peu d'entités ({n_ent})")
    if n_ent and fonctionnels / n_ent < 0.80:
        verdict = "FLAG"; raisons.append(f"taux fonctionnel {fonctionnels/max(n_ent,1):.0%} (<80%)")
    if closed_fit < 0.95:
        verdict = "REJET"; raisons.append(f"closed-fit {closed_fit:.0%} : valeurs hors-pays {hors_ref[:5]}")
    if coll:
        verdict = "COLLISION"; raisons.append(f"déjà dans {coll}")
    return {
        "relation": relation, "classe": classe_qid, "prop": prop,
        "n_lignes": len(rows), "n_entites": n_ent, "n_distinctes": len(distinctes),
        "fonctionnel": round(fonctionnels / n_ent, 3) if n_ent else 0.0,
        "closed_fit": round(closed_fit, 3), "hors_ref": hors_ref[:8],
        "echantillon": _echantillon_det(paires, k), "collision": coll,
        "limite_atteinte": len(rows) >= limite, "verdict": verdict, "raisons": raisons,
    }


def sonde_generique(relation: str, classe_qid: str, prop: str, limite: int = 6000, k: int = 8) -> dict:
    """GÉNÉRALISATION de `sonde` au-delà de « X -> pays » : mesure une propriété FONCTIONNELLE À VALEURS FERMÉES
    quelconque (sport, instrument, style, genre…) SANS référence codée en dur. La « fermeture » se détecte DEPUIS
    LA DONNÉE : `ratio = valeurs_distinctes / entités`. Un vrai ensemble fermé (≈quelques centaines de valeurs
    partagées par des milliers d'entités) a un ratio TRÈS BAS ; une propriété à valeur quasi-unique (auteur,
    date…) a un ratio ≈1 -> REJET (pas un set fermé bornable proprement). FAUX=0 : `fonctionnel` rejette les
    multi-valeurs ; on relit TOUJOURS l'échantillon (le ratio ne dit pas si le NOM de relation est honnête)."""
    os.makedirs(_SCOUT, exist_ok=True)
    chemin = os.path.join(_SCOUT, f"{relation}.json")
    if os.path.exists(chemin):
        with open(chemin, encoding="utf-8") as fh:
            rows = json.load(fh)
    else:
        q = f"""SELECT ?eLabel ?vLabel WHERE {{
          ?e wdt:P31/wdt:P279* wd:{classe_qid} ; wdt:{prop} ?o .
          ?o rdfs:label ?vLabel . FILTER(lang(?vLabel)="fr")
          ?e rdfs:label ?eLabel . FILTER(lang(?eLabel)="fr")
        }} LIMIT {limite}"""
        url = ENDPOINT + "?action=json_export&query=" + urllib.parse.quote(PREFIXES + q)
        req = urllib.request.Request(url, headers={"User-Agent": UA, "Accept": "application/sparql-results+json"})
        with urllib.request.urlopen(req, timeout=120) as r:
            rows = json.loads(r.read())["results"]["bindings"]
        with open(chemin, "w", encoding="utf-8") as fh:
            json.dump(rows, fh, ensure_ascii=False)
    paires = [(val(r, "eLabel"), val(r, "vLabel")) for r in rows
              if val(r, "eLabel") and val(r, "vLabel")
              and not _est_qid(val(r, "eLabel")) and not _est_qid(val(r, "vLabel"))]
    par_ent: dict[str, set] = {}
    for e, v in paires:
        par_ent.setdefault(e, set()).add(v)
    n_ent = len(par_ent)
    fonctionnels = sum(1 for vs in par_ent.values() if len(vs) == 1)
    distinctes = {v for vs in par_ent.values() for v in vs}
    ratio = len(distinctes) / n_ent if n_ent else 1.0
    from collections import Counter
    top = Counter(v for vs in par_ent.values() if len(vs) == 1 for v in vs).most_common(8)
    coll = collision(relation)
    verdict, raisons = "PROPRE", []
    if n_ent < 100:
        verdict = "FAIBLE"; raisons.append(f"peu d'entités ({n_ent})")
    if n_ent and fonctionnels / n_ent < 0.80:
        verdict = "FLAG"; raisons.append(f"fonctionnel {fonctionnels/max(n_ent,1):.0%} (<80%)")
    if ratio > 0.15:
        verdict = "REJET"; raisons.append(f"ratio distinct/entités {ratio:.2f} (>0.15 : pas un ensemble fermé)")
    if coll:
        verdict = "COLLISION"; raisons.append(f"déjà dans {coll}")
    return {"relation": relation, "classe": classe_qid, "prop": prop, "n_entites": n_ent,
            "n_distinctes": len(distinctes), "ratio": round(ratio, 3),
            "fonctionnel": round(fonctionnels / n_ent, 3) if n_ent else 0.0,
            "top": [t for t, _ in top], "echantillon": _echantillon_det(paires, k),
            "collision": coll, "limite_atteinte": len(rows) >= limite, "verdict": verdict, "raisons": raisons}


def rapport_generique(specs: list[tuple], limite: int = 6000, k: int = 8) -> list[dict]:
    """Sonde un LOT de candidats `(relation, classe_qid, prop)` à valeurs fermées QUELCONQUES (généralise
    `rapport` hors pays). Imprime ratio/fonctionnel/top valeurs/échantillon + shortlist PROPRE."""
    res = []
    for relation, classe, prop in specs:
        try:
            r = sonde_generique(relation, classe, prop, limite, k)
        except Exception as e:
            r = {"relation": relation, "classe": classe, "prop": prop, "verdict": "ERREUR", "raisons": [str(e)[:120]]}
        res.append(r)
        print(f"\n── {relation}  (classe {classe}, {prop})  → {r['verdict']}")
        if r["verdict"] == "ERREUR":
            print(f"     erreur : {r['raisons'][0]}"); continue
        flag = " ⚠️ LIMIT" if r.get("limite_atteinte") else ""
        print(f"     entités={r['n_entites']}  distinctes={r['n_distinctes']}  ratio={r['ratio']}  "
              f"fonctionnel={r['fonctionnel']:.0%}{flag}")
        if r["raisons"]:
            print(f"     raisons : {'; '.join(r['raisons'])}")
        print(f"     top valeurs : {', '.join(r['top'][:8])}")
        print("     échantillon : " + " | ".join(f"{e}→{v}" for e, v in r["echantillon"]))
    propres = [r for r in res if r["verdict"] == "PROPRE"]
    print(f"\n=== SHORTLIST PROPRE : {len(propres)}/{len(specs)} → "
          + (", ".join(r["relation"] for r in propres) if propres else "(aucune)"))
    return res


def rapport(specs: list[tuple], limite: int = 6000, k: int = 6) -> list[dict]:
    """Sonde un LOT de candidats `(relation, classe_qid[, prop])` et imprime un rapport lisible. Renvoie les
    rapports ; la shortlist PROPRE est ce qu'on ingère ensuite (jugement + gate restent les juges FAUX=0)."""
    res = []
    for spec in specs:
        relation, classe = spec[0], spec[1]
        prop = spec[2] if len(spec) > 2 else "P17"
        try:
            r = sonde(relation, classe, prop, limite, k)
        except Exception as e:                       # réseau/parse : on n'interrompt pas le lot
            r = {"relation": relation, "classe": classe, "prop": prop, "verdict": "ERREUR", "raisons": [str(e)[:120]]}
        res.append(r)
        print(f"\n── {relation}  (classe {classe}, {prop})  → {r['verdict']}")
        if r["verdict"] == "ERREUR":
            print(f"     erreur : {r['raisons'][0]}"); continue
        flag = " ⚠️ LIMIT atteint (sous-estimé)" if r.get("limite_atteinte") else ""
        print(f"     entités={r['n_entites']}  valeurs distinctes={r['n_distinctes']}  "
              f"fonctionnel={r['fonctionnel']:.0%}  closed-fit={r['closed_fit']:.0%}{flag}")
        if r["raisons"]:
            print(f"     raisons : {'; '.join(r['raisons'])}")
        print("     échantillon : " + " | ".join(f"{e}→{v}" for e, v in r["echantillon"]))
    propres = [r for r in res if r["verdict"] == "PROPRE"]
    print(f"\n=== SHORTLIST PROPRE : {len(propres)}/{len(specs)} → "
          + (", ".join(r["relation"] for r in propres) if propres else "(aucune)"))
    return res


if __name__ == "__main__":
    # Lot de candidats X->pays NON encore ingérés (classes Wikidata à valeur P17=pays). À ajuster librement.
    LOT = [
        ("pays_gratte_ciel", "Q11303"),       # gratte-ciel
        ("pays_amphitheatre", "Q207694"),     # amphithéâtre (musée? art? -> on verra le fit)
        ("pays_jardin", "Q1107656"),          # jardin
        ("pays_ecole", "Q3914"),              # école
        ("pays_hopital", "Q16917"),           # hôpital
        ("pays_eglise", "Q16970"),            # église (bâtiment)
        ("pays_chateau_fort", "Q23413"),      # château fort
        ("pays_riviere", "Q4022"),            # rivière
    ]
    rapport(LOT)
