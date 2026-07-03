"""
INGESTION MINÉRAUX — espèces minérales (Q12089225) -> datasets/lecteur/*.jsonl (ONLINE, lancé à la main).

Couvre le GAP « Roches et minéraux » (SCIENCES DE LA TERRE) par des FAITS BORNÉS textbook d'une espèce
minérale (la classe Q12089225 = espèce minérale reconnue IMA, PROPRE — pas les spécimens/météorites qui
polluaient Q7946/Q8063) :
  • formule_chimique_mineral (P274) : l'espèce -> sa formule brute (quartz-type SiO₂, fluorine CaF₂…). NEUF.
  • systeme_cristallin        (P556) : l'espèce -> son système cristallin (ensemble fermé de 7 : cubique,
    quadratique, orthorhombique, monoclinique, triclinique, trigonal, hexagonal). EXTENSION de la relation
    existante (idempotent : les entrées déjà présentes ne sont pas réécrites ; on n'ajoute que les nouvelles).
  • durete_mohs_mineral      (P1088) : l'espèce -> sa dureté sur l'échelle de Mohs (1..10). NEUF. Les minéraux
    de RÉFÉRENCE de l'échelle sortent exacts (talc 1, gypse 2, fluorine 4, quartz 7, corindon 9, diamant 10).

FAUX=0 (infra ingere_qlever/ingere_wikidata) :
  • `fonctionnel` : une espèce à formule/système MULTIPLE (dimorphe) -> HORS (mesuré : 5685 statements pour
    5679 espèces => 6 dimorphes écartés). La formule d'une espèce IMA est canonique et unique.
  • libellé FR obligatoire ; Q-ID nu écarté ; réconciliation d'amorce (divergence -> `_conflits/`, jamais d'écrasement).
  • formule = chaîne de la nomenclature (indices Unicode ₂/₃ conservés = notation minéralogique de référence).

Vérité-terrain (ancres, vérifiées dans valide_lecteur) : fluorine -> CaF₂ ; sphalérite -> ZnS ; hématite ->
Fe₂O₃ ; béryl -> Be₃Al₂Si₆O₁₈ ; systèmes : fluorine cubique, hématite trigonal.

Usage : python3 ingere_mineraux.py            (fetch online puis publie ; ré-exécution = offline via snapshots)
"""
from __future__ import annotations

import ingere_qlever as IQ
from ingere_wikidata import publie, _est_qid

CLASSE = "Q12089225"       # espèce minérale (reconnaissance IMA) — classe PROPRE, sans les spécimens


def _pull_formule():
    """Espèce -> formule chimique brute (P274, littéral). Écarte les Q-ID nus et les libellés vides."""
    q = f"""SELECT ?eLabel ?f WHERE {{
      ?e wdt:P31 wd:{CLASSE} ; wdt:P274 ?f .
      ?e rdfs:label ?eLabel . FILTER(lang(?eLabel)="fr")
    }}"""
    rows = IQ._charge_ou_fetch("formule_chimique_mineral", q)
    out = []
    for r in rows:
        e, f = IQ.val(r, "eLabel"), IQ.val(r, "f")
        if e and f and not _est_qid(e):
            out.append((e, f))
    return out


def _pull_mohs():
    """Espèce -> dureté de Mohs (P1088, valeur numérique 1..10). Une plage (2 valeurs) -> fonctionnel -> HORS."""
    q = f"""SELECT ?eLabel ?h WHERE {{
      ?e wdt:P31 wd:{CLASSE} ; wdt:P1088 ?h .
      ?e rdfs:label ?eLabel . FILTER(lang(?eLabel)="fr")
    }}"""
    rows = IQ._charge_ou_fetch("durete_mohs_mineral", q)
    out = []
    for r in rows:
        e, h = IQ.val(r, "eLabel"), IQ.val(r, "h")
        if not e or _est_qid(e) or not h:
            continue
        try:                                           # borne de sanité : l'échelle de Mohs est [1,10]
            if 1.0 <= float(h) <= 10.0:
                out.append((e, h))
        except ValueError:
            continue
    return out


def _pull_systeme():
    """Espèce -> système cristallin (P556, libellé FR d'un ensemble fermé). Extension de systeme_cristallin."""
    q = f"""SELECT ?eLabel ?sLabel WHERE {{
      ?e wdt:P31 wd:{CLASSE} ; wdt:P556 ?s .
      ?e rdfs:label ?eLabel . FILTER(lang(?eLabel)="fr")
      ?s rdfs:label ?sLabel . FILTER(lang(?sLabel)="fr")
    }}"""
    rows = IQ._charge_ou_fetch("systeme_cristallin_mineral", q)   # snapshot distinct ; publie sur systeme_cristallin
    out = []
    for r in rows:
        e, s = IQ.val(r, "eLabel"), IQ.val(r, "sLabel")
        if e and s and not _est_qid(e):
            out.append((e, s))
    return out


def ingere_tout():
    stats = []
    stats.append(publie("formule_chimique_mineral", "physique",
                        "Wikidata/QLever — formule chimique brute (P274) d'une espèce minérale IMA (Q12089225)",
                        _pull_formule()))
    stats.append(publie("durete_mohs_mineral", "physique",
                        "Wikidata/QLever — dureté de Mohs (P1088, échelle 1..10) d'une espèce minérale IMA (Q12089225)",
                        _pull_mohs()))
    # EXTENSION de la relation systeme_cristallin existante (même source P556) : idempotent + réconciliation.
    stats.append(publie("systeme_cristallin", "physique",
                        "Wikidata/QLever — système cristallin de l'espèce minérale P556 (ensemble fermé ; dimorphes -> HORS)",
                        _pull_systeme()))
    total = sum(s["ecrits"] for s in stats)
    conflits = sum(s["conflits_amorce"] for s in stats)
    print(f"\n== MINÉRAUX : {total} faits écrits sur {len(stats)} relations, conflits_amorce={conflits} ==")
    return stats


if __name__ == "__main__":
    ingere_tout()
