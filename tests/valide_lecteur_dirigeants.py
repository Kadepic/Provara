# -*- coding: utf-8 -*-
"""VALIDATION DIRIGEANTS PAR PAYS-ANNÉE (Route 4 temporelle). FAUX=0 INVIOLABLE.

Relations : chef_etat_pays_annee / chef_gouvernement_pays_annee — statements P39 des fonctions OFFICIELLES du
pays (P1906/P1313), mandats TERMINÉS seulement, dépliés par année, transitions chronologiques (« X puis Y »),
bornes d'entrée/sortie dites quand l'année n'est pas pleine.

  1. FORME   : entité = « <pays> <année> » (année bornée [-700, 2026]) ; valeur = libellé(s) non vides,
               jamais de Q-ID nu, jamais une date fuitée.
  2. ANCRES  : vérifiées À LA MAIN (indépendantes du code) — de Gaulle 1962, Kennedy puis Johnson 1963,
               Chamberlain puis Churchill 1940, Craxi 1985 (le piège « maire » sous-classe de chef de
               gouvernement est mort), Juan Carlos 1975 AVEC borne de prise de fonction.
  3. ADVERSE : année hors couverture / pays non souverain actuel / mandat en cours -> ABSENT (HORS), jamais
               une devinette.

EXIT 0 = tout passe. Tourne sur l'échantillon embarqué (sous-ensemble 6 pays) COMME sur la base complète."""
from __future__ import annotations

import json
import os
import re
import sys

DOSSIER = os.environ.get("LECTEUR_DATASETS_DIR") or os.path.join(
    os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "datasets", "lecteur")

ok = ko = 0


def check(c, label):
    global ok, ko
    if c:
        ok += 1
    else:
        ko += 1
        print("  FAIL: " + label)


_RE_ENTITE = re.compile(r"^(.+)\s(-?\d{1,4})$")


def lit(rel):
    d = {}
    with open(os.path.join(DOSSIER, rel + ".jsonl"), encoding="utf-8") as fh:
        for l in fh:
            o = json.loads(l)
            if "_relation" not in o:
                d[o["entite"]] = o["valeur"]
    return d


for rel in ("chef_etat_pays_annee", "chef_gouvernement_pays_annee"):
    t = lit(rel)
    check(len(t) > 500, "%s : volume plausible (%d)" % (rel, len(t)))
    formes = annees = qid = vides = 0
    for e, v in t.items():
        m = _RE_ENTITE.match(e)
        if not m:
            formes += 1
            continue
        if not (-700 <= int(m.group(2)) <= 2026):
            annees += 1
        if re.fullmatch(r"Q\d+", str(v).strip()):
            qid += 1
        if not str(v).strip():
            vides += 1
    check(formes == 0, "%s : toutes les entités = « pays année » (%d en défaut)" % (rel, formes))
    check(annees == 0, "%s : toutes les années dans [-700, 2026] (%d hors plage)" % (rel, annees))
    check(qid == 0 and vides == 0, "%s : aucune valeur Q-ID nue / vide" % rel)

CE = lit("chef_etat_pays_annee")
CG = lit("chef_gouvernement_pays_annee")

# — ANCRES chef d'État (vérité historique indépendante) —
check(CE.get("France 1962") == "Charles de Gaulle", "ANCRE France 1962 -> Charles de Gaulle")
check(CE.get("France 1969") == "Charles de Gaulle puis Alain Poher puis Georges Pompidou",
      "ANCRE France 1969 -> transitions chronologiques réelles (de Gaulle, Poher, Pompidou)")
check(CE.get("États-Unis 1963") == "John Fitzgerald Kennedy puis Lyndon B. Johnson",
      "ANCRE États-Unis 1963 -> Kennedy puis Johnson (assassinat = transition dans l'année)")
check(CE.get("Royaume-Uni 1952") == "George VI puis Élisabeth II", "ANCRE Royaume-Uni 1952 -> George VI puis Élisabeth II")
check(CE.get("Allemagne 1962") == "Heinrich Lübke", "ANCRE Allemagne 1962 -> Heinrich Lübke")
v = CE.get("Espagne 1975") or ""
check(v.startswith("Juan Carlos") and "prise de fonction" in v,
      "ANCRE Espagne 1975 -> Juan Carlos AVEC borne honnête (Franco = autre fonction, année non pleine)")

# — ANCRES chef de gouvernement —
check(CG.get("Royaume-Uni 1940") == "Neville Chamberlain puis Winston Churchill",
      "ANCRE Royaume-Uni 1940 -> Chamberlain puis Churchill")
check(CG.get("Italie 1985") == "Bettino Craxi",
      "ANCRE Italie 1985 -> Craxi SEUL (pollution « maire » sous-classe Q2285706 éliminée par P1313)")
check(CG.get("France 1962") == "Michel Debré puis Georges Pompidou", "ANCRE France 1962 -> Debré puis Pompidou")
check(CG.get("Allemagne 1962") == "Konrad Adenauer", "ANCRE Allemagne 1962 -> Adenauer")

# — ADVERSE : hors couverture -> ABSENT (jamais deviné) —
check("URSS 1950" not in CE, "URSS (état disparu, non souverain actuel) -> HORS")
check("France 2035" not in CE, "année future -> HORS")
check("Atlantide 1900" not in CE, "pays fictif -> HORS")
check("France 2025" not in CE, "mandat en cours (vérité datée) -> HORS : jamais figé en base froide")

print("=== valide_lecteur_dirigeants : %d/%d ===" % (ok, ok + ko))
sys.exit(1 if ko else 0)
