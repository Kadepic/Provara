"""
INGESTION ESPACE — sondes & véhicules spatiaux (Q26529) -> datasets/lecteur/*.jsonl (ONLINE, lancé à la main).

Couvre le GAP « Satellites, sondes » (ASTRONOMIE & ESPACE). 4 veines de FAITS BORNÉS d'une sonde spatiale,
toutes FONCTIONNELLES (une sonde a UN lanceur, UN opérateur principal, UN fabricant, UNE date de lancement) :
  • lanceur_sonde        (P375) : la sonde -> son véhicule lanceur (Voyager 1 -> Titan IIIE).
  • operateur_sonde      (P137) : la sonde -> l'agence opératrice (Luna 10 -> Union soviétique).
  • fabricant_sonde      (P176) : la sonde -> son constructeur.
  • annee_lancement_sonde (P619) : la sonde -> l'ANNÉE de lancement (date UTC, extraite + bornée [1957,2035]).

FAUX=0 (réutilise l'infra ingere_qlever/ingere_wikidata, mêmes garde-fous que tout le corpus) :
  • `fonctionnel` : toute sonde à valeur MULTIPLE (deux lanceurs, deux opérateurs…) -> HORS.
  • libellé FR obligatoire ; on écarte les Q-ID nus (`_est_qid`).
  • réconciliation d'amorce (conflit divergent -> `datasets/_conflits/`, jamais d'écrasement).
  • ANNÉE : bornée à une plage plausible de l'ère spatiale [1957, 2035] ; hors-plage -> HORS (rejette une date
    aberrante ou une valeur non-datée). On ne garde que l'année (le mois/jour = sur-précision non demandée ici).
  • snapshots offline `datasets/_raw/<rel>.json` (fetch figé -> ré-ingestion offline, résilient réseau).

Vérité-terrain (ancres, vérifiées dans valide_lecteur) : Voyager 1/2 -> Titan IIIE ; Hayabusa -> M-V ;
Luna 10 -> Union soviétique ; Cassini lancé en 1997 ; New Horizons en 2006.

Usage : python3 ingere_espace.py            (fetch online puis publie ; ré-exécution = offline via snapshots)
        python3 ingere_espace.py republie   (offline pur : ré-ingère depuis les snapshots _raw)
"""
from __future__ import annotations

import re
import sys

import ingere_qlever as IQ
from ingere_wikidata import publie, _est_qid

CLASSE_SONDE = "Q26529"                       # engin spatial / sonde spatiale (sous-classes incluses via P279*)
_AN_MIN, _AN_MAX = 1957, 2035                 # Spoutnik-1 (1957) .. horizon proche ; hors plage = date aberrante -> HORS

# (relation, propriété, source, categorie). Les 3 premières = entité->entité ; la 4e = date (traitée à part).
VEINES = [
    ("lanceur_sonde", "P375",
     "Wikidata/QLever — lanceur (P375) d'une sonde/engin spatial (Q26529)", "passe"),
    ("operateur_sonde", "P137",
     "Wikidata/QLever — opérateur (P137) d'une sonde/engin spatial (Q26529)", "passe"),
    ("fabricant_sonde", "P176",
     "Wikidata/QLever — fabricant (P176) d'une sonde/engin spatial (Q26529)", "passe"),
]


def _pull_entite(relation, prop):
    """Sonde -> valeur (libellé FR) pour une propriété entité->entité. Écarte les Q-ID nus."""
    q = f"""SELECT ?eLabel ?vLabel WHERE {{
      ?e wdt:P31/wdt:P279* wd:{CLASSE_SONDE} ; wdt:{prop} ?v .
      ?e rdfs:label ?eLabel . FILTER(lang(?eLabel)="fr")
      ?v rdfs:label ?vLabel . FILTER(lang(?vLabel)="fr")
    }}"""
    rows = IQ._charge_ou_fetch(relation, q)
    out = []
    for r in rows:
        e, v = IQ.val(r, "eLabel"), IQ.val(r, "vLabel")
        if e and v and not _est_qid(e) and not _est_qid(v):
            out.append((e, v))
    return out


def _pull_annee_lancement():
    """Sonde -> ANNÉE de lancement (P619 = date UTC). Extrait l'année, borne à [1957, 2035] (HORS sinon)."""
    q = f"""SELECT ?eLabel ?d WHERE {{
      ?e wdt:P31/wdt:P279* wd:{CLASSE_SONDE} ; wdt:P619 ?d .
      ?e rdfs:label ?eLabel . FILTER(lang(?eLabel)="fr")
    }}"""
    rows = IQ._charge_ou_fetch("annee_lancement_sonde", q)
    out, hors_plage = [], 0
    for r in rows:
        e, d = IQ.val(r, "eLabel"), IQ.val(r, "d")
        if not e or _est_qid(e):
            continue
        m = re.match(r"(-?\d{3,4})-\d\d-\d\d", d)     # ISO datetime : -?AAAA-MM-JJ...
        if not m:
            continue
        an = int(m.group(1))
        if _AN_MIN <= an <= _AN_MAX:
            out.append((e, str(an)))
        else:
            hors_plage += 1
    if hors_plage:
        print(f"  [annee_lancement_sonde] {hors_plage} hors-plage[{_AN_MIN},{_AN_MAX}] -> HORS")
    return out


def ingere_tout():
    stats = []
    for relation, prop, source, categorie in VEINES:
        paires = _pull_entite(relation, prop)
        stats.append(publie(relation, categorie, source, paires))
    paires = _pull_annee_lancement()
    stats.append(publie("annee_lancement_sonde", "passe",
                        "Wikidata/QLever — année de lancement (P619) d'une sonde/engin spatial (Q26529)", paires))
    total = sum(s["ecrits"] for s in stats)
    conflits = sum(s["conflits_amorce"] for s in stats)
    print(f"\n== ESPACE : {total} faits écrits sur {len(stats)} relations, conflits_amorce={conflits} ==")
    return stats


if __name__ == "__main__":
    ingere_tout()      # 'republie' = même chemin : _charge_ou_fetch réutilise les snapshots _raw s'ils existent
