"""
INGESTION O*NET INTERESTS — l'axe « profil d'intérêt dominant » d'un métier (RIASEC / Holland, 2026-07-12).

Le descripteur d'orientation le plus standard après les attributs durs : le TYPE d'intérêt professionnel
dominant sur le modèle RIASEC de Holland (Realistic, Investigative, Artistic, Social, Enterprising,
Conventional). Universel en orientation de carrière.

POURQUOI C'EST BORNÉ (et pas un seuil arbitraire) : O*NET publie 6 scores d'intérêt par occupation. On ne
seuille RIEN — on prend l'**argmax** (le high-point de Holland), une opération DÉTERMINISTE. Les ex-aequo
sont listés (pas de choix arbitraire). C'est exactement ce que fait l'orientation : « quel est l'intérêt
DOMINANT de ce métier ». Contraste avec Work Context / Work Styles, qui exigeraient un seuil pour dire
« important » -> écartés (arbitraire = HORS).

HONNÊTETÉ : les scores d'intérêt d'O*NET 30.0 sont IMPUTÉS par apprentissage (Domain Source « Machine
Learning »), pas relevés par enquête. Standard et publié, mais soft -> l'axe est MIX (marché US, profil
O*NET), jamais présenté comme un fait dur.

LA CHAÎNE — la même que rémunération/outils/risques/niveau (maillons d'`ingere_bls_oes` réutilisés) :
  métier -> groupe ISCO-08 -> SOC 2010 -> SOC 2018 -> intérêt(s) dominant(s) O*NET.

CACHE : `datasets/_raw/onet_interests.xlsx` (db_30_0 O*NET, CC BY 4.0).

Usage :
    python3 ingestion/ingere_onet_interets.py moissonne
    python3 ingestion/ingere_onet_interets.py publie
"""
from __future__ import annotations

import collections
import os
import re
import sys

from ingere_bls_oes import (RAW, _isco_du_store, _telecharge, isco_vers_soc2010, lit_xlsx,
                            soc2010_vers_2018)
from ingere_wikidata import publie

URL = "https://www.onetcenter.org/dl_files/database/db_30_0_excel/Interests.xlsx"
CACHE = os.path.join(RAW, "onet_interests.xlsx")
_RIASEC = ("Realistic", "Investigative", "Artistic", "Social", "Enterprising", "Conventional")

SRC = ("O*NET 30.0 (US DOL, CC BY 4.0) Interests × crosswalks BLS (ISCO-08→SOC 2010→SOC 2018) × "
       "`code_isco_metier`/`code_isco_p8283_metier`. La valeur affirme : le métier relève du groupe ISCO-08 "
       "indiqué ; l'intérêt (les intérêts) professionnel(s) DOMINANT(s) sur le modèle RIASEC de Holland est "
       "l'ARGMAX (high-point) des 6 scores O*NET, opération déterministe — aucun seuil (ex-aequo listés). "
       "Granularité dite (occupation SOC du groupe). Scores O*NET 30.0 IMPUTÉS par apprentissage (soft) : "
       "axe MIX (marché US).")


def moissonne() -> None:
    os.makedirs(RAW, exist_ok=True)
    print("== MOISSONNAGE O*NET Interests ==")
    _telecharge(URL, CACHE)
    print("  %s (%.0f Ko)" % (os.path.basename(CACHE), os.path.getsize(CACHE) / 1e3))


def _exige(chemin: str) -> str:
    if not os.path.exists(chemin):
        raise SystemExit("cache absent : %s — lancer : python3 ingestion/ingere_onet_interets.py moissonne"
                         % chemin)
    return chemin


def dominant_par_soc(chemin: str) -> dict:
    """code SOC 2018 -> tuple TRIÉ des intérêts RIASEC dominants (argmax des scores OI ; ex-aequo listés)."""
    lignes = lit_xlsx(_exige(chemin))
    col = {v: k for k, v in lignes[0].items()}
    for c in ("O*NET-SOC Code", "Element Name", "Scale ID", "Data Value"):
        if c not in col:
            raise SystemExit("colonne « %s » absente de %s — format O*NET changé" % (c, chemin))
    scores = collections.defaultdict(dict)          # soc -> {interet: score max}
    for r in lignes[1:]:
        if (r.get(col["Scale ID"]) or "") != "OI":  # Occupational Interests (le score RIASEC)
            continue
        code = (r.get(col["O*NET-SOC Code"]) or "")[:7]
        el = (r.get(col["Element Name"]) or "").strip()
        if not re.fullmatch(r"\d{2}-\d{4}", code) or el not in _RIASEC:
            continue
        try:
            val = float(r.get(col["Data Value"]))
        except (TypeError, ValueError):
            continue
        d = scores[code]
        d[el] = max(d.get(el, float("-inf")), val)
    dom = {}
    for code, d in scores.items():
        if not d:
            continue
        mx = max(d.values())
        dom[code] = tuple(sorted(k for k, v in d.items() if abs(v - mx) < 1e-9))
    return dom


def valeur_interet(groupe: str, socs: list, dom: dict):
    """La valeur du métier, ou None si aucune occupation du groupe n'a de profil."""
    lignes = [(s, dom[s]) for s in sorted(socs) if s in dom]
    if not lignes:
        return None
    corps = " ; ".join("%s → %s" % (s, ", ".join(d)) for s, d in lignes)
    return ("groupe ISCO-08 %s ; intérêt(s) professionnel(s) DOMINANT(s) (profil RIASEC de Holland, "
            "high-point O*NET = argmax déterministe des scores, sans seuil) des occupations SOC 2018 de ce "
            "groupe (granularité : occupation SOC, pas le métier précis) : %s" % (groupe, corps))


def publie_depuis_cache() -> None:
    print("== O*NET Interests — axe « profil d'intérêt dominant (RIASEC) » (part US, MIX) ==")
    dom = dominant_par_soc(CACHE)
    if len(dom) < 500:
        raise ValueError("Interests tronqué : %d SOC — refus de publier" % len(dom))
    print("  O*NET : %d SOC avec profil d'intérêt dominant" % len(dom))

    i2s, s18, isco = isco_vers_soc2010(), soc2010_vers_2018(), _isco_du_store()
    sys.path.insert(0, os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "outils"))
    from genere_sujets import metiers_de_la_carte
    metiers, _, _ = metiers_de_la_carte()

    paires, sans = [], 0
    for m in metiers:
        g = isco.get(m)
        if not g:
            continue
        socs = sorted({b for a in i2s.get(g, ()) for b in s18.get(a, ())})
        v = valeur_interet(g, socs, dom)
        if v is None:
            sans += 1
            continue
        paires.append((m, v))
    if len(paires) < 300:
        raise ValueError("chaîne suspecte : %d métiers — maillons à réauditer" % len(paires))
    print("  métiers publiés : %d | groupe sans profil (restent non traités) : %d" % (len(paires), sans))
    publie("interet_dominant_soc_metier", "convention", SRC, sorted(paires))


if __name__ == "__main__":
    mode = sys.argv[1] if len(sys.argv) > 1 else "publie"
    if mode == "moissonne":
        moissonne()
    elif mode == "publie":
        publie_depuis_cache()
    else:
        raise SystemExit("usage : ingere_onet_interets.py [moissonne|publie]")
