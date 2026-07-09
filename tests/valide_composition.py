# -*- coding: utf-8 -*-
"""VALIDE le raisonnement COMPOSITIONNEL « X de Y de Z » (P1), FAUX=0.

On MOCKE le résolveur factuel (ia.donnee_nl) avec des faits contrôlés pour prouver le MÉCANISME indépendamment
des données : l'inner (Y de Z) est résolu en entité E, puis l'outer (X de E). Chaque maillon = lookup vérifié ;
si un maillon manque -> abstention (None), jamais une composition inventée."""
from __future__ import annotations

import os
import sys

os.environ.setdefault("LECTEUR_AMORCE_SEULE", "1")
_ICI = os.path.dirname(os.path.abspath(__file__)) or "."
sys.path.insert(0, os.path.join(os.path.dirname(_ICI), "interface"))
sys.path.insert(0, os.path.join(os.path.dirname(_ICI), "src"))

import repond

ok = ko = 0


def check(c, label):
    global ok, ko
    if c:
        ok += 1
    else:
        ko += 1
        print("  FAIL: " + label)


# — faits contrôlés (base à 2 sauts) —
class _Fait:
    def __init__(self, v):
        self.valeur = v


_FAITS = {
    "capitale de france": "Paris",
    "population de paris": "2 100 000",
    "pays de paris": "France",
    "continent de france": "Europe",
    "monnaie de france": "euro",
}


class _MockIA:
    def donnee_nl(self, requete):
        import base_faits
        v = _FAITS.get(" ".join(requete.strip().lower().split()))
        return (base_faits.VERIFIE, _Fait(v)) if v else (base_faits.HORS, None)


# injecte le mock dans le cache d'ia de repond
import base_faits
repond._IA = _MockIA()
repond._VERIFIE = base_faits.VERIFIE
repond._ATTR_HEADS_CACHE = {"capitale", "population", "pays", "continent", "monnaie", "langue"}

# (1) composition à 2 sauts qui résout
r = repond._compose_relations("quelle est la population de la capitale de la France ?")
check(r is not None and r.startswith("2 100 000"), "population de la capitale de la France -> composée (2 100 000)")
check(r is not None and "capitale de France = Paris" in r, "la chaîne de dérivation est montrée")

r = repond._compose_relations("quel est le continent du pays de Paris ?")
check(r is not None and r.startswith("Europe"), "continent du pays de Paris -> Europe (composée)")

r = repond._compose_relations("quelle est la monnaie du pays de Paris ?")
check(r is not None and r.startswith("euro"), "monnaie du pays de Paris -> euro (composée)")

# (2) FAUX=0 : un maillon INCONNU -> abstention (None), jamais une invention
check(repond._compose_relations("quelle est la superficie de la capitale de la France ?") is None,
      "maillon outer manquant (superficie de Paris) -> None (abstention)")
check(repond._compose_relations("quelle est la population de la capitale de l'Atlantide ?") is None,
      "maillon inner manquant (capitale d'Atlantide) -> None")

# (3) détection : une question imbriquée est reconnue, une simple ne l'est pas
check(repond._est_relation_imbriquee("population de la capitale de la France"), "détecte l'imbrication")
check(not repond._est_relation_imbriquee("capitale de la France"), "une relation simple n'est PAS imbriquée")

# (4) non-imbriqué -> le composeur ne s'applique pas
check(repond._compose_relations("quelle est la capitale de la France ?") is None, "simple -> composeur inactif (None)")

# (5) ROUTE 4 — RELATIVE ÉVÉNEMENTIELLE « où est né / où est mort » (multi-hop). On mocke _lookup_cell (les
# datasets lieu_naissance/pays_ville sont absents de l'échantillon) pour prouver le MÉCANISME ; le réel est
# prouvé e2e dans le .exe sur la base complète. FAUX=0 : maillon manquant -> None, chaîne montrée sinon.
_CELLS = {("lieu_naissance", "albert einstein"): ("Albert Einstein", "Ulm"),
          ("lieu_deces", "marie curie"): ("Marie Curie", "sanatorium de Sancellemoz"),
          ("pays_ville", "ulm"): ("Ulm", "Allemagne"),
          ("continent", "allemagne"): ("Allemagne", "Europe")}
repond._lookup_cell = lambda rel, ent: _CELLS.get((rel, repond._normalise(str(ent))))

r = repond._resout_relatif("pays où est né Albert Einstein")
check(r is not None and r[0] == "Allemagne" and "pays actuel" in " ".join(r[1]),
      "« pays où est né Einstein » -> Allemagne, honnêteté temporelle DITE (pays actuel)")
r = repond._resout_relatif("la ville où est né Albert Einstein")
check(r is not None and r[0] == "Ulm", "« ville où est né » -> le lieu même (Ulm)")
r = repond._resout_relatif("le continent où est né Albert Einstein")
check(r is not None and r[0] == "Europe" and len(r[1]) == 3, "« continent où est né » -> Europe (3 sauts montrés)")
r = repond._resout_relatif("la ville où est morte Marie Curie")
check(r is not None and "Sancellemoz" in r[0], "« où est morte » (féminin) -> lieu_deces")
check(repond._resout_relatif("le pays où est né Zorglub Introuvable") is None,
      "personne inconnue -> None (jamais deviné)")
check(repond._resout_relatif("le pays où est morte Marie Curie") is None,
      "lieu de décès sans rattachement pays -> None (abstention, pas d'à-peu-près)")
_FAITS["capitale de allemagne"] = "Berlin"
r = repond._compose_relations_n("quelle est la capitale du pays où est né Albert Einstein ?")
check(r is not None and r.startswith("Berlin") and "est né à Ulm" in r and "pays actuel" in r,
      "COMPOSITION COMPLÈTE : capitale du pays où est né Einstein -> Berlin + dérivation entière")
# garde : la relative LOCALISATION existante n'est pas volée par l'événementiel
check(repond._OU_EVT_RE.match("pays où se trouve la tour Eiffel") is None,
      "« où se trouve » ne matche PAS le motif événementiel (chacun sa feuille)")

# (6) CAP DIRECT « dans quel(le) TYPE est né/mort X ? » (vécu e2e : « dans quelle ville est né Einstein ? »
# partait au reverse-liste géographique — villes de la région Est du Cameroun)
r = repond._cap_lieu_evenement("dans quelle ville est né Albert Einstein ?")
check(r == "Albert Einstein est né à Ulm.", "« dans quelle ville est né X » -> le lieu vérifié, phrase directe")
r = repond._cap_lieu_evenement("dans quel pays est né Albert Einstein ?")
check(r is not None and r.startswith("Allemagne") and "pays actuel" in r,
      "« dans quel pays est né X » -> saut pays MONTRÉ (honnêteté temporelle)")
r = repond._cap_lieu_evenement("sur quel continent est né Albert Einstein ?")
check(r is not None and r.startswith("Europe"), "« sur quel continent est né X » -> Europe (dérivation)")
check(repond._cap_lieu_evenement("dans quelle ville est né Zorglub Introuvable ?") is None,
      "personne inconnue -> None (la cascade continue)")
check(repond._cap_lieu_evenement("dans quelle ville est la tour Eiffel ?") is None,
      "« est » sans verbe d'événement -> None (la localisation existante garde sa route)")

print("=== valide_composition : %d/%d ===" % (ok, ok + ko))
sys.exit(0 if ko == 0 else 1)
