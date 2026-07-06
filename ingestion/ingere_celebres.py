# -*- coding: utf-8 -*-
"""INGESTION CIBLÉE « CÉLÈBRES » : répare les trous de personnes FAMEUSES dans les grosses relations
(occupation_personne, nationalite_personne, annee_naissance/deces_personne, lieu_naissance/deces).

POURQUOI CE SCRIPT (2026-07-06) : le « fonctionnel » de l'ingestion historique travaille PAR LIBELLÉ —
Isaac Newton (le physicien) était masqué par son PÈRE homonyme (fermier), Marie Curie n'avait ni occupation
(physicienne ET chimiste = multi -> HORS) ni nationalité (Pologne ET France = multi -> HORS). Les personnes
célèbres étaient précisément les plus touchées : plus on est célèbre, plus on a d'homonymes et d'attributs.

MÉTHODE (soundness) :
  • cible = les humains à >= 50 sitelinks Wikipédia (~11 000 personnes mondialement célèbres) via QLever ;
  • DOMINANCE PAR NOTORIÉTÉ : par libellé, l'entité au max de sitelinks n'est retenue que si elle domine la
    2ᵉ d'un facteur >= 8 (Isaac Newton ~200 wikis vs père ~0) — sinon ambiguïté réelle -> on ne touche pas ;
  • valeurs MULTIPLES d'une MÊME entité JOINTES honnêtement (« physicienne et chimiste », « France et
    Pologne ») — occupations triées par fréquence corpus (les informatives d'abord), plafond 3 (nat. 2) ;
  • APPEND si le libellé est absent du fichier, REMPLACEMENT si l'entrée existante est l'homonyme obscur ;
  • passe finale ANTI-COLLISION avec la clé exacte du lecteur (_sans_articles) : toute clé encore
    multi-valeurs est retirée ENTIÈREMENT (abstention honnête) — le lecteur refuse les conflits au chargement.

Usage : LECTEUR_DATASETS_DIR=<base> PYTHONPATH=src python3 ingestion/ingere_celebres.py [seuil_sitelinks]
"""
from __future__ import annotations

import collections
import json
import os
import re
import sys
import unicodedata
import urllib.parse
import urllib.request

sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "src"))
from base_faits import _sans_articles  # noqa: E402

ENDPOINT = "https://qlever.cs.uni-freiburg.de/api/wikidata"
UA = "Provara/ingestion (github.com/Provara-IA/Provara)"
SEUIL_SITELINKS = int(sys.argv[1]) if len(sys.argv) > 1 else 50
RATIO_DOMINANCE = 8.0
BASE = os.environ.get("LECTEUR_DATASETS_DIR") or os.path.join(os.path.expanduser("~"), ".verax", "datasets", "lecteur")

PFX = """PREFIX wdt: <http://www.wikidata.org/prop/direct/>
PREFIX wd: <http://www.wikidata.org/entity/>
PREFIX wikibase: <http://wikiba.se/ontology#>
PREFIX rdfs: <http://www.w3.org/2000/01/rdf-schema#>
"""

#           propriété  fichier                          label?  année?  jointure max
CIBLES = [("P106", "occupation_personne.jsonl",         True,   False,  3),
          ("P27",  "nationalite_personne.jsonl",        True,   False,  2),
          ("P569", "annee_naissance_personne.jsonl",    False,  True,   1),
          ("P570", "annee_deces_personne.jsonl",        False,  True,   1),
          ("P19",  "lieu_naissance.jsonl",              True,   False,  1),
          ("P20",  "lieu_deces.jsonl",                  True,   False,  1)]


def _norm(s: str) -> str:
    return "".join(c for c in unicodedata.normalize("NFD", s.lower()) if unicodedata.category(c) != "Mn").strip()


def _fetch(q: str) -> list:
    url = ENDPOINT + "?" + urllib.parse.urlencode({"query": q})
    req = urllib.request.Request(url, headers={"Accept": "application/sparql-results+json", "User-Agent": UA})
    with urllib.request.urlopen(req, timeout=240) as r:
        return json.load(r)["results"]["bindings"]


def dominants(prop: str, label_val: bool, annee: bool, joinmax: int) -> dict:
    """{clé_norm: (libellé, valeur_jointe)} des célèbres à dominance établie."""
    ligne_v = '?v rdfs:label ?vLabel . FILTER(lang(?vLabel)="fr")' if label_val else ""
    sel = "?vLabel" if label_val else "?v"
    rows = _fetch(PFX + f"""SELECT ?e ?eLabel ?sl {sel} WHERE {{
  ?e wdt:P31 wd:Q5 ; wikibase:sitelinks ?sl ; wdt:{prop} ?v .
  FILTER(?sl >= {SEUIL_SITELINKS})
  ?e rdfs:label ?eLabel . FILTER(lang(?eLabel)="fr")
  {ligne_v}
}}""")
    par_qid, freq = {}, collections.Counter()
    for b in rows:
        qid = b["e"]["value"].rsplit("/", 1)[1]
        v = (b.get("vLabel") or b.get("v"))["value"]
        if annee:
            m = re.match(r"(-?\d{1,4})-", v)
            if not m:
                continue
            v = str(int(m.group(1)))
        d = par_qid.setdefault(qid, {"label": b["eLabel"]["value"], "sl": int(float(b["sl"]["value"])), "vals": []})
        if v not in d["vals"]:
            d["vals"].append(v)
            freq[v] += 1
    par_label = collections.defaultdict(list)
    for qid, d in par_qid.items():
        par_label[_norm(d["label"])].append(d)
    out = {}
    for cle, lst in par_label.items():
        lst.sort(key=lambda d: -d["sl"])
        if len(lst) > 1 and lst[0]["sl"] < RATIO_DOMINANCE * max(1, lst[1]["sl"]):
            continue                                        # homonymes célèbres tous les deux -> on ne touche pas
        vals = sorted(lst[0]["vals"], key=lambda v: -freq[v])[:joinmax]
        if joinmax == 1 and len(lst[0]["vals"]) > 1:
            continue                                        # valeur unique exigée (années/lieux) -> multi = HORS
        val = " et ".join([", ".join(vals[:-1]), vals[-1]]) if len(vals) > 1 else vals[0]
        out[cle] = (lst[0]["label"], val)
    return out


def applique(fichier: str, dom: dict) -> None:
    tmp = fichier + ".tmp"
    vus, rempl, present = set(), 0, set()
    with open(fichier, encoding="utf-8") as src, open(tmp, "w", encoding="utf-8") as dst:
        for l in src:
            i = l.find('"entite": "')
            if i >= 0:
                j = l.find('"', i + 11)
                cle = _norm(l[i + 11:j])
                d = dom.get(cle)
                if d is not None:
                    present.add(cle)
                    if cle in vus:
                        continue                            # doublon d'homonyme -> une seule ligne dominante
                    vus.add(cle)
                    nl = json.dumps({"entite": d[0], "valeur": d[1]}, ensure_ascii=False) + "\n"
                    rempl += (nl != l)
                    dst.write(nl)
                    continue
            dst.write(l)
        ajouts = 0
        for cle, d in sorted(dom.items()):
            if cle not in present:
                dst.write(json.dumps({"entite": d[0], "valeur": d[1]}, ensure_ascii=False) + "\n")
                ajouts += 1
    os.replace(tmp, fichier)
    print(f"  {os.path.basename(fichier):34s} remplacés={rempl:5d}  ajoutés={ajouts:5d}")


def anticollision(fichier: str) -> None:
    """Toute clé LECTEUR encore multi-valeurs est retirée entièrement (le chargement refuserait le fichier)."""
    vals = collections.defaultdict(set)
    for l in open(fichier, encoding="utf-8"):
        try:
            o = json.loads(l)
        except ValueError:
            continue
        if "entite" in o:
            vals[_sans_articles(str(o["entite"]))].add(str(o["valeur"]))
    conflits = {k for k, s in vals.items() if len(s) > 1}
    if not conflits:
        return
    tmp = fichier + ".tmp"
    drop = 0
    with open(fichier, encoding="utf-8") as src, open(tmp, "w", encoding="utf-8") as dst:
        for l in src:
            try:
                o = json.loads(l)
            except ValueError:
                dst.write(l)
                continue
            if "entite" in o and _sans_articles(str(o["entite"])) in conflits:
                drop += 1
                continue
            dst.write(l)
    os.replace(tmp, fichier)
    print(f"  {os.path.basename(fichier):34s} anti-collision : {len(conflits)} clés ambiguës retirées ({drop} lignes)")


if __name__ == "__main__":
    print(f"== CÉLÈBRES (sitelinks >= {SEUIL_SITELINKS}, dominance >= {RATIO_DOMINANCE:g}x) -> {BASE} ==")
    for prop, nom, label_val, annee, joinmax in CIBLES:
        fichier = os.path.join(BASE, nom)
        if not os.path.exists(fichier):
            print(f"  {nom} ABSENT — sauté")
            continue
        applique(fichier, dominants(prop, label_val, annee, joinmax))
        anticollision(fichier)
    print("Terminé. Relancer les bancs (banc_raisonnement/banc_paraphrases) avant tout commit.")
