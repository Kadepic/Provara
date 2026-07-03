"""
INGESTION AVIATION — modèles d'aéronef (Q15056993) -> datasets/lecteur/*.jsonl (ONLINE, lancé à la main).

Enrichit le couloir transport (T11 a le constructeur des véhicules) par un FAIT BORNÉ d'histoire aéronautique
resté GAP : l'ANNÉE du premier vol d'un MODÈLE d'aéronef. Leçon de classe (2026-07-02) : viser le MODÈLE
(Q15056993 = Boeing 747, Spitfire… labels reconnaissables) et NON l'airframe individuel (Q11436 = D-ABYT…,
immatriculations, premier vol d'un exemplaire précis, sans intérêt encyclopédique).
  • annee_premier_vol_aeronef (P606) : le modèle -> l'année de son premier vol.

FAUX=0 :
  • `fonctionnel` : un modèle à plusieurs dates de premier vol (variantes fusionnées) -> HORS.
  • ANNÉE bornée à [1900, 2035] (avant = pas d'aviation motorisée -> date aberrante -> HORS) ; on ne garde que l'année.
  • libellé FR obligatoire ; Q-ID nu écarté ; réconciliation d'amorce (divergence -> `_conflits/`).

Vérité-terrain (ancres, vérifiées dans valide_lecteur) : Boeing 747 -> 1969 ; Supermarine Spitfire -> 1936 ;
Dassault Mirage 2000 -> 1978.

Usage : python3 ingere_aviation.py            (fetch online puis publie ; ré-exécution = offline via snapshots)
"""
from __future__ import annotations

import re

import ingere_qlever as IQ
from ingere_wikidata import publie, _est_qid

CLASSE = "Q15056993"          # modèle d'aéronef (PAS Q11436 = exemplaire individuel)
_AN_MIN, _AN_MAX = 1900, 2035


def _pull_premier_vol():
    q = f"""SELECT ?eLabel ?d WHERE {{
      ?e wdt:P31 wd:{CLASSE} ; wdt:P606 ?d .
      ?e rdfs:label ?eLabel . FILTER(lang(?eLabel)="fr")
    }}"""
    rows = IQ._charge_ou_fetch("annee_premier_vol_aeronef", q)
    out, hors = [], 0
    for r in rows:
        e, d = IQ.val(r, "eLabel"), IQ.val(r, "d")
        if not e or _est_qid(e):
            continue
        m = re.match(r"(-?\d{3,4})-\d\d-\d\d", d)
        if not m:
            continue
        an = int(m.group(1))
        if _AN_MIN <= an <= _AN_MAX:
            out.append((e, str(an)))
        else:
            hors += 1
    if hors:
        print(f"  [annee_premier_vol_aeronef] {hors} hors-plage[{_AN_MIN},{_AN_MAX}] -> HORS")
    return out


def ingere_tout():
    stats = [publie("annee_premier_vol_aeronef", "passe",
                    "Wikidata/QLever — année du premier vol (P606) d'un modèle d'aéronef (Q15056993)",
                    _pull_premier_vol())]
    print(f"\n== AVIATION : {stats[0]['ecrits']} faits écrits, conflits_amorce={stats[0]['conflits_amorce']} ==")
    return stats


if __name__ == "__main__":
    ingere_tout()
