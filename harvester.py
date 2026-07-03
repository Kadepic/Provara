"""
HARVESTER — industrialise la DÉCOUVERTE+CLASSIFICATION FAUX=0 des veines d'ingestion (Levier 3, nuit 2026-06-29).

Le scout (`scout_qlever`) mesure déjà closed-fit/fonctionnel/ratio/échantillon d'un LOT. La pièce qui manquait =
l'AIGUILLEUR : étant donné une propriété Wikidata, router AUTOMATIQUEMENT vers le bon PROFIL de soundness +
la bonne FABRIQUE, via `wikibase:propertyType` (gratuit côté serveur) croisé au ratio du scout. On concentre
alors le jugement humain (relecture d'échantillon + ANCRES non-circulaires) sur la SHORTLIST prête à ingérer.

CE QU'IL NE FAIT PAS (FAUX=0 inchangé) : il N'INGÈRE RIEN, n'écrit PAS d'ancres (les ancres = vérité-terrain
non-circulaire, jugement humain obligatoire), ne touche PAS au lecteur. Il propose ; la gate reste le juge.

LÉGER : n'importe ni `ingere_qlever` ni `lecteur` au niveau module (chaîne lourde) -> utilisable pendant une gate.
Réutilise `scout_qlever.sonde_generique` (urllib pur) pour la mesure closed-set ; sa propre requête pour le type.
"""
from __future__ import annotations

import json
import os
import subprocess
import urllib.parse
import urllib.request

import scout_qlever as S

_HARN = os.path.dirname(os.path.abspath(__file__))


def _prop_deja_ingere(prop: str) -> list[str]:
    """Fichiers ingere_*.py utilisant DÉJÀ cette propriété Wikidata. DÉDUP PAR PROPRIÉTÉ (bien plus robuste
    que par nom de relation : la même prop est souvent ré-ingérée sous un autre nom -> faux « PROPRE »).
    LEÇON nuit 2026-06-29 : ~25 candidats scoutés, presque tous déjà faits sous un autre nom (closed-set épuisé)."""
    try:
        pat = f"\"{prop}\"|'{prop}'"
        out = subprocess.run(["grep", "-rlE", pat, _HARN, "--include=ingere_*.py"],
                             capture_output=True, text=True, timeout=30).stdout
    except (OSError, subprocess.SubprocessError):
        return []
    return sorted(os.path.basename(x) for x in out.split() if x)

ENDPOINT = "https://qlever.dev/api/wikidata"
PREFIXES = ("PREFIX wdt: <http://www.wikidata.org/prop/direct/>\n"
            "PREFIX wd: <http://www.wikidata.org/entity/>\n"
            "PREFIX wikibase: <http://wikiba.se/ontology#>\n"
            "PREFIX rdfs: <http://www.w3.org/2000/01/rdf-schema#>\n")
UA = S.UA

# propertyType Wikidata -> (profil de soundness, fabrique recommandée dans ingere_qlever / patron de couloir).
_ROUTE = {
    "WikibaseItem":   ("ferme|lieu",  "_ingere_x_vers_entite (closed-set) OU _ingere_x_vers_lieu (vocab ouvert+ancres)"),
    "Quantity":       ("numerique",   "patron T7 _pull_<unite> (valeur+unité->float, plage+tolérance+ancres)"),
    "Time":           ("date",        "patron T8 date/année (P580/P582 qualif. si fonction) "),
    "String":         ("code",        "_ingere_x_vers_code (motif regex de forme)"),
    "ExternalId":     ("code",        "_ingere_x_vers_code (identifiant externe, motif)"),
    "Monolingualtext":("texte",       "table texte (rare ; vérifier unicité+langue fr)"),
    "Url":            ("rejet",       "URL : non bornable proprement -> HORS"),
    "CommonsMedia":   ("rejet",       "média : non un fait textuel -> HORS"),
    "GlobeCoordinate":("geo",         "coordonnées (lat/lon) -> patron géo dédié"),
}


def _q(query: str, timeout: int = 90) -> list[dict]:
    """GET QLever JSON, urllib pur (PAS d'import ingere_qlever/lecteur -> léger, OK pendant une gate)."""
    url = ENDPOINT + "?action=json_export&query=" + urllib.parse.quote(PREFIXES + query)
    req = urllib.request.Request(url, headers={"User-Agent": UA, "Accept": "application/sparql-results+json"})
    with urllib.request.urlopen(req, timeout=timeout) as r:
        return json.loads(r.read())["results"]["bindings"]


def type_propriete(props: list[str]) -> dict[str, str]:
    """{Pxxx: 'WikibaseItem'|'Quantity'|'Time'|'String'|'ExternalId'|...} en UNE requête (VALUES). L'entrée
    AUTOMATIQUE du routeur : le type est déclaré côté Wikidata, gratuit, fiable."""
    if not props:
        return {}
    vals = " ".join(f"wd:{p}" for p in props)
    out = {}
    for r in _q(f"SELECT ?p ?t WHERE {{ VALUES ?p {{ {vals} }} ?p wikibase:propertyType ?t }}"):
        p = S.val(r, "p").rsplit("/", 1)[-1]
        t = S.val(r, "t").rsplit("#", 1)[-1]
        out[p] = t
    return out


def route(ptype: str, ratio: float | None = None) -> tuple[str, str]:
    """(profil, fabrique) recommandés depuis le type Wikidata (+ ratio scout pour distinguer fermé vs ouvert).
    Pour WikibaseItem : ratio bas (<0.15) = ensemble fermé -> _ingere_x_vers_entite ; sinon vocab ouvert (lieu/
    personne) -> _ingere_x_vers_lieu + ancres. ratio None = type seul."""
    profil, fab = _ROUTE.get(ptype, ("inconnu", f"type {ptype} non routé -> inspecter"))
    if ptype == "WikibaseItem" and ratio is not None:
        if ratio <= 0.15:
            return ("ferme", "_ingere_x_vers_entite (closed-set, ratio bas confirmé)")
        return ("ouvert/lieu", "_ingere_x_vers_lieu (+ ancres) ; vérifier que les valeurs sont des LIEUX/entités nommées")
    return (profil, fab)


def propose(specs: list[tuple], limite: int = 6000, k: int = 8) -> list[dict]:
    """Pour un LOT de (relation, classe_qid, prop) : (1) type Wikidata de chaque prop, (2) pour les WikibaseItem
    on lance la sonde closed-set du scout, (3) on ROUTE + verdict combiné. Imprime une shortlist PRÊTE-À-INGÉRER
    (relation, classe, prop, profil, fabrique) — reste au jugement : relire l'échantillon + écrire les ANCRES."""
    props = sorted({s[2] for s in specs})
    types = type_propriete(props)
    res = []
    for relation, classe, prop in specs:
        pt = types.get(prop, "?")
        rec = {"relation": relation, "classe": classe, "prop": prop, "ptype": pt}
        deja = _prop_deja_ingere(prop)                 # DÉDUP PAR PROPRIÉTÉ (avant tout : économise la sonde réseau)
        if deja:
            rec.update(verdict="COLLISION-PROP", profil=route(pt)[0], deja=deja)
            res.append(rec)
            print(f"\n── {relation}  ({classe}, {prop}) [{pt}] → COLLISION-PROP (prop déjà ingérée via {deja})")
            continue
        if pt in ("WikibaseItem",) or pt == "?":
            try:
                s = S.sonde_generique(relation, classe, prop, limite, k)
            except Exception as e:
                rec.update(verdict="ERREUR", raisons=[str(e)[:120]]); res.append(rec)
                print(f"\n── {relation} ({classe},{prop}) [{pt}] → ERREUR {rec['raisons'][0]}"); continue
            profil, fab = route(pt, s.get("ratio"))
            rec.update(verdict=s["verdict"], profil=profil, fabrique=fab, ratio=s.get("ratio"),
                       n_entites=s.get("n_entites"), fonctionnel=s.get("fonctionnel"),
                       top=s.get("top"), echantillon=s.get("echantillon"),
                       collision=s.get("collision"), limite_atteinte=s.get("limite_atteinte"))
        else:
            profil, fab = route(pt)
            verdict = "ROUTÉ" if profil not in ("rejet",) else "REJET"
            rec.update(verdict=verdict, profil=profil, fabrique=fab,
                       raisons=[] if verdict == "ROUTÉ" else [f"type {pt} non bornable proprement"])
        res.append(rec)
        print(f"\n── {relation}  ({classe}, {prop}) [{pt}] → {rec['verdict']}  profil={rec.get('profil')}")
        print(f"     fabrique : {rec.get('fabrique')}")
        if rec.get("ratio") is not None:
            flag = " ⚠️LIMIT" if rec.get("limite_atteinte") else ""
            print(f"     entités={rec.get('n_entites')} ratio={rec.get('ratio')} fonctionnel={rec.get('fonctionnel')}{flag}")
        if rec.get("collision"):
            print(f"     ⚠️ collision : {rec['collision']}")
        if rec.get("top"):
            print(f"     top : {', '.join(rec['top'][:8])}")
        if rec.get("echantillon"):
            print("     échantillon : " + " | ".join(f"{e}→{v}" for e, v in rec["echantillon"]))
    prets = [r for r in res if r["verdict"] in ("PROPRE", "ROUTÉ")]
    print(f"\n=== PRÊTS À INGÉRER (jugement+ancres ensuite) : {len(prets)}/{len(specs)} → "
          + (", ".join(r["relation"] for r in prets) if prets else "(aucun)"))
    return res


if __name__ == "__main__":
    # Démo : un lot mixte (item fermé / numérique / date / code) — montre le routage automatique.
    LOT = [
        ("genre_litteraire_oeuvre", "Q7725634", "P136"),   # œuvre écrite -> genre (item, attendu fermé)
        ("hauteur_gratte_ciel",     "Q11303",   "P2048"),  # gratte-ciel -> hauteur (Quantity -> T7)
        ("date_fondation_ville",    "Q515",     "P571"),    # ville -> date de fondation (Time -> T8)
        ("code_pays_fifa",          "Q6979593", "P3441"),   # équipe nat. -> code FIFA (String -> code)
    ]
    propose(LOT)
