"""
INGESTION BLS SOII — l'axe « risques professionnels et prévention » s'ouvre par sa part MESURÉE US (mandat
« traiter tout le backlog », 2026-07-12 — DERNIER des 5 axes métier sans source).

LA SOURCE. Survey of Occupational Injuries and Illnesses (BLS), table **R100** 2023-2024 : taux d'incidence
ANNUALISÉS des blessures et maladies professionnelles non mortelles, PAR OCCUPATION SOC détaillée, par
famille d'événements (contacts, chutes/glissades, surmenage/gestes répétitifs, transports, violences,
explosions/incendies, substances nocives…), pour 10 000 équivalents temps plein, industrie privée US.
L'INRS (piste française) ne publie pas de table structurée risque × métier : la part FR reste ouverte.

LA CHAÎNE — la même que rémunération et outils (maillons d'`ingere_bls_oes` RÉUTILISÉS) :
  métier -> groupe ISCO-08 (ESCO, store) -> SOC 2010 -> SOC 2018 -> taux SOII des occupations du groupe.

CE QUE LA TABLE AFFIRME : les taux publiés par le BLS pour les occupations SOC 2018 du GROUPE ISCO du
métier — granularité DITE. On publie le type de cas **DAFW** (cas avec arrêt de travail — days away from
work) et le niveau **famille d'événements** (colonnes « Total » de chaque groupe d'en-tête) : un niveau
COMPLET plutôt qu'un extrait du niveau fin (même choix qu'O*NET et geste_metier). Les intitulés de familles
restent en anglais VERBATIM (traduire serait interpréter) ; les taux sont reformés au dixième publié par le
BLS (le xlsx stocke des flottants binaires : « 4.0999… » EST « 4.1 ») ; « - » (non publié) reste « - ».

Le sujet reste MIX -> PARTIEL, jamais TRAITÉ : une année, un pays, l'industrie privée ; la prévention
(l'autre moitié de l'axe) n'est pas une statistique.

CACHE : `datasets/_raw/soii_r100_2023_2024.xlsx` (stdlib pur en lecture).

Usage :
    python3 ingestion/ingere_bls_soii.py moissonne     # 1 fichier BLS (~0,4 Mo)
    python3 ingestion/ingere_bls_soii.py publie        # hors ligne, depuis le cache
"""
from __future__ import annotations

import collections
import os
import re
import sys

from ingere_bls_oes import RAW, _isco_du_store, _telecharge, isco_vers_soc2010, lit_xlsx, soc2010_vers_2018
from ingere_wikidata import publie

URL_R100 = ("https://www.bls.gov/iif/nonfatal-injuries-and-illnesses-tables/"
            "case-and-demographic-characteristics-table-r100-2023-2024.xlsx")
CACHE_R100 = os.path.join(RAW, "soii_r100_2023_2024.xlsx")
MILLESIME = "2023-2024"

SRC = ("BLS SOII table R100 %s (taux d'incidence annualisés des blessures/maladies professionnelles non "
       "mortelles, par occupation SOC 2018 et famille d'événements, pour 10 000 ETP, industrie privée "
       "États-Unis ; type de cas DAFW = cas avec arrêt de travail) × crosswalks BLS (ISCO-08→SOC 2010→"
       "SOC 2018) × `code_isco_metier` (ESCO). La valeur affirme : le métier relève du groupe ISCO-08 "
       "indiqué ; les taux listés sont ceux que le BLS publie pour les occupations SOC de ce GROUPE (pas "
       "le métier précis — granularité dite), au niveau famille d'événements (colonnes Total). Intitulés "
       "VERBATIM (anglais) ; taux au dixième publié ; « - » = non publié par le BLS. Part États-Unis "
       "seulement — la prévention et la part française restent non couvertes." % MILLESIME)


def moissonne() -> None:
    os.makedirs(RAW, exist_ok=True)
    print("== MOISSONNAGE BLS SOII (table R100 %s) ==" % MILLESIME)
    _telecharge(URL_R100, CACHE_R100)
    print("  %s (%.0f Ko)" % (os.path.basename(CACHE_R100), os.path.getsize(CACHE_R100) / 1e3))


def _exige(chemin: str) -> str:
    if not os.path.exists(chemin):
        raise SystemExit("cache absent : %s — lancer : python3 ingestion/ingere_bls_soii.py moissonne"
                         % chemin)
    return chemin


def _taux(brut: str) -> str:
    """« 4.0999999999999996 » -> « 4.1 » (le BLS publie au dixième ; le xlsx stocke un flottant binaire).
    Tout non-numérique (« - » = non publié) reste VERBATIM."""
    try:
        return "%.1f" % float(brut)
    except (TypeError, ValueError):
        return (brut or "").strip()


def colonnes_familles(rangee1: dict, rangee2: dict) -> list:
    """[(lettre, intitulé de famille)] : la colonne « Total » de chaque famille d'événements, ou la colonne
    unique d'une famille sans sous-détail. D (« Total rate ») est repris en tête. Dérivé des DEUX rangées
    d'en-tête, jamais de lettres codées en dur."""
    groupes = collections.Counter(v for k, v in rangee1.items() if k not in "ABC" and v)
    cols = []
    for lettre in sorted(rangee1, key=lambda c: (len(c), c)):
        if lettre in "ABC":
            continue
        g = rangee1.get(lettre) or ""
        if not g:
            continue
        if g == "Total rate" or (rangee2.get(lettre) or "") == "Total" or groupes[g] == 1:
            cols.append((lettre, g))
    return cols


def taux_par_soc(chemin: str) -> tuple:
    """(soc -> (titre, [(famille, taux)]), intitulé du tableau). Lignes DAFW des occupations DÉTAILLÉES
    seulement (code xx-xxxx à dernier chiffre non nul : les agrégats xx-0000/xx-xx00 tombent)."""
    lignes = lit_xlsx(_exige(chemin))
    titre = (lignes[0].get("A") or "").strip()
    if "R100" not in titre:
        raise SystemExit("titre inattendu dans %s — le format SOII a changé" % chemin)
    cols = colonnes_familles(lignes[1], lignes[2])
    if len(cols) < 6:
        raise SystemExit("familles d'événements introuvables dans %s — le format SOII a changé" % chemin)
    table = {}
    for r in lignes[3:]:
        code = (r.get("B") or "").strip()
        if (r.get("C") or "").strip() != "DAFW":
            continue
        if not re.fullmatch(r"\d{2}-\d{3}[1-9]", code):
            continue
        table[code] = ((r.get("A") or "?").strip(),
                       [(fam, _taux(r.get(lettre))) for lettre, fam in cols])
    return table, titre


def valeur_soii(groupe: str, socs: list, taux: dict):
    """La valeur du métier, ou None si AUCUNE occupation du groupe n'est dans R100."""
    connus = [(s, taux[s]) for s in sorted(socs) if s in taux]
    if not connus:
        return None
    corps = " | ".join("%s « %s » : %s" % (s, titre, " ; ".join("%s %s" % (f, v) for f, v in fams))
                       for s, (titre, fams) in connus)
    return ("groupe ISCO-08 %s ; taux d'incidence annualisés des blessures/maladies professionnelles "
            "(BLS SOII %s, industrie privée États-Unis, cas avec arrêt de travail — DAFW, pour 10 000 ETP) "
            "par famille d'événements, pour les occupations SOC 2018 que les crosswalks BLS associent à ce "
            "groupe (granularité : occupation SOC, pas le métier précis ; « - » = non publié) : %s"
            % (groupe, MILLESIME, corps))


def publie_depuis_cache() -> None:
    print("== BLS SOII — axe « risques professionnels » (part mesurée US, MIX) ==")
    taux, titre = taux_par_soc(CACHE_R100)
    if len(taux) < 400:
        raise ValueError("R100 tronqué : %d occupations détaillées DAFW — refus de publier" % len(taux))
    print("  R100 : %d occupations SOC détaillées avec taux DAFW" % len(taux))

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
        v = valeur_soii(g, socs, taux)
        if v is None:
            sans += 1
            continue
        paires.append((m, v))
    if len(paires) < 300:
        raise ValueError("chaîne suspecte : %d métiers seulement — maillons à réauditer" % len(paires))
    print("  métiers publiés : %d | groupe absent de R100 (restent non traités) : %d" % (len(paires), sans))
    publie("risque_professionnel_soc_metier", "convention", SRC, sorted(paires))


if __name__ == "__main__":
    mode = sys.argv[1] if len(sys.argv) > 1 else "publie"
    if mode == "moissonne":
        moissonne()
    elif mode == "publie":
        publie_depuis_cache()
    else:
        raise SystemExit("usage : ingere_bls_soii.py [moissonne|publie]")
