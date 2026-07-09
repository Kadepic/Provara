# -*- coding: utf-8 -*-
"""INGESTION — DIRIGEANTS PAR PAYS ET PAR ANNÉE (Route 4 temporelle, 2026-07-09).

POURQUOI : « qui dirigeait la France en 1962 ? » est un fait BORNÉ-historique, mais les veines T8 existantes
(annee_debut/fin_mandat_chef_etat) sont clées par PERSONNE et mono-gardées : tout multi-mandats (De Gaulle,
Churchill…) est HORS — la question par pays+année était donc SANS réponse. Cette veine lit les STATEMENTS P39
complets (fonction + juridiction P1001 + qualificatifs P580/P582) et publie une table clée « <pays> <année> » :
le lookup-ou-HORS natif du lecteur répond alors directement.

RELATIONS PUBLIÉES :
  • chef_etat_pays_annee          : « France 1962 » -> « Charles de Gaulle »
  • chef_gouvernement_pays_annee  : « France 1962 » -> « Georges Pompidou »

FAUX=0 — garde-fous :
  • MANDATS TERMINÉS UNIQUEMENT (P580 ET P582 exigés pour publier une année) : un mandat en cours est une
    VÉRITÉ DATÉE (le vrai d'aujourd'hui peut devenir faux) -> les années récentes sans fin de mandat restent
    HORS, honnêtement. [ymin,ymax] borne les dates absurdes.
  • ANNÉE DE TRANSITION (2+ dirigeants la même année) : valeur chronologique « X puis Y » (ordre P580 réel),
    co-titulaires au même début (co-princes) « X et Y » — jamais un choix silencieux.
  • Juridiction = ÉTAT SOUVERAIN ACTUEL (P1001 -> P31 Q3624078) : pas d'états historiques ambigus en v1.
  • Libellés FR exigés (personne ET pays) ; Q-ID nus rejetés ; année de dépliage bornée à la FIN réelle.
  • `publie` (fonctionnel + réconciliation amorce + audit) inchangé — les paires arrivent déjà fusionnées.

Usage : LECTEUR_DATASETS_DIR=<staging> python3 ingestion/ingere_dirigeants.py
"""
from __future__ import annotations

import re
import sys

import ingere_qlever as IQ
from ingere_wikidata import publie, snapshot_brut

_P_P39 = "<http://www.wikidata.org/prop/P39>"
_PS_P39 = "<http://www.wikidata.org/prop/statement/P39>"
_PQ = "<http://www.wikidata.org/prop/qualifier/%s>"

# (relation, propriété « fonction officielle du pays », libellé humain). P1906 = office held by head of state,
# P1313 = office held by head of government : l'ENSEMBLE FERMÉ national — la sonde par classe (P279* Q2285706)
# ramenait les MAIRES (sous-classe « chef de gouvernement » municipal, P1001 posé au pays -> Italie 1985 pollué).
VEINES = [
    ("chef_etat_pays_annee", "P1906", "chef d'État"),
    ("chef_gouvernement_pays_annee", "P1313", "chef de gouvernement"),
]
YMIN, YMAX = -700, 2026          # bornes de sanité des années (Rome antique -> aujourd'hui)


def _annee(v: str):
    """Année (int) d'un littéral date Wikidata (« 1959-01-08T00:00:00Z », années négatives incluses)."""
    m = re.match(r"^(-?\d{1,4})-", str(v or ""))
    return int(m.group(1)) if m else None


def _pull(prop_fonction: str) -> list:
    """Statements P39 complets (personne, début P580, fin P582) sur les fonctions OFFICIELLES du pays
    (?pays wdt:{P1906|P1313} ?pos) — ensemble fermé national, aucune fonction locale possible."""
    q = f"""SELECT ?paysLabel ?eLabel ?debut ?fin WHERE {{
      ?pays wdt:P31 wd:Q3624078 ; wdt:{prop_fonction} ?pos .
      ?e {_P_P39} ?st .
      ?st {_PS_P39} ?pos ; {_PQ % "P580"} ?debut ; {_PQ % "P582"} ?fin .
      ?e wdt:P31 wd:Q5 .
      ?e rdfs:label ?eLabel . FILTER(lang(?eLabel)="fr")
      ?pays rdfs:label ?paysLabel . FILTER(lang(?paysLabel)="fr")
    }}"""
    return IQ.qlever(q, timeout=300)


def _mandats(rows) -> list:
    """Rows SPARQL -> [(pays, personne, debut_iso, annee_debut, annee_fin)] filtrés (labels FR réels, années
    bornées, fin >= début). `debut_iso` (date complète) sert à ORDONNER les transitions dans l'année."""
    out = []
    for r in rows:
        pays, e = IQ.val(r, "paysLabel"), IQ.val(r, "eLabel")
        brut_d = IQ.val(r, "debut")
        d, f = _annee(brut_d), _annee(IQ.val(r, "fin"))
        if not pays or not e or IQ._est_qid(pays) or IQ._est_qid(e):
            continue
        if d is None or f is None or not (YMIN <= d <= YMAX) or not (YMIN <= f <= YMAX) or f < d:
            continue
        out.append((pays, e, str(brut_d), d, f))
    return sorted(set(out))


def _deplie(mandats) -> list:
    """Dépliage annuel + fusion des transitions : [(« <pays> <année> », « X [puis|et] Y »)].
    Chronologie réelle (ordre P580 à la DATE complète) ; « et » réservé aux co-titulaires au même jour ;
    le même nom n'est jamais répété (mandats contigus d'une même personne).
    HONNÊTETÉ DE BORD : un titulaire UNIQUE dont le mandat commence/finit l'année demandée, sans autre nom
    cette année-là DANS CETTE FONCTION, porte la borne (« Juan Carlos, prise de fonction cette année-là » en
    1975 : Franco, autre fonction, n'est pas dans cette table — sans la borne, la réponse laisserait croire à
    une année pleine)."""
    par_cle: dict = {}
    for pays, e, d_iso, d, f in mandats:
        for an in range(d, f + 1):
            par_cle.setdefault((pays, an), []).append((d_iso, e, d, f))
    paires = []
    for (pays, an), lst in sorted(par_cle.items()):
        lst.sort()
        noms, debuts, bornes = [], [], {}
        for d_iso, e, d, f in lst:
            if e not in noms:
                noms.append(e)
                debuts.append(d_iso)
                bornes[e] = (d, f)
        val = noms[0]
        for i in range(1, len(noms)):
            val += (" et " if debuts[i] == debuts[i - 1] else " puis ") + noms[i]
        if len(noms) == 1:
            d, f = bornes[noms[0]]
            if d == an and f == an:
                val += " (fonction prise et quittée cette année-là)"
            elif d == an:
                val += " (prise de fonction cette année-là)"
            elif f == an:
                val += " (fin de fonction cette année-là)"
        paires.append(("%s %d" % (pays, an), val))
    return paires


def ingere(veines=VEINES):
    stats = []
    for relation, prop, libelle in veines:
        print(f"== {relation} (P39 statements sur la fonction {prop} « {libelle} » des états souverains) ==")
        rows = _pull(prop)
        snapshot_brut(relation, rows)
        mandats = _mandats(rows)
        paires = _deplie(mandats)
        print(f"  {len(rows)} lignes brutes -> {len(mandats)} mandats terminés -> {len(paires)} paires pays-année")
        stats.append(publie(relation, "passe",
                            f"Wikidata/QLever — {libelle} par pays et année (P39 + P1001, qualificatifs "
                            f"P580/P582, mandats terminés seulement)", paires))
    return stats


if __name__ == "__main__":
    ingere()
    sys.exit(0)
