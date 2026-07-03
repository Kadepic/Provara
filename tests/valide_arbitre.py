"""VALIDATION arbitre.py (Vague 7). FAUX=0 : consensus/tranché par fiabilité stricte ; égalité au sommet -> ABSTENTION."""
from __future__ import annotations
from arbitre import arbitre, valeur_arbitree, CONSENSUS, TRANCHE, ABSTENTION

ok = 0; total = 0
def check(nom, cond):
    global ok, total; total += 1
    print(f"  [{'OK ' if cond else 'XXX'}] {nom}", flush=True)
    if cond: ok += 1
    else: raise AssertionError(nom)

fiab = {"manuel_officiel": 1.0, "mesure_labo": 0.9, "forum": 0.2, "autre_forum": 0.2}

# Consensus
st, v, _ = arbitre([("Paris", "manuel_officiel"), ("Paris", "mesure_labo")], fiab)
check("toutes les sources concordent -> CONSENSUS", st == CONSENSUS and v == "Paris")

# Tranché : une source plus fiable l'emporte
st2, v2, _ = arbitre([("Paris", "manuel_officiel"), ("Lyon", "forum")], fiab)
check("fiabilité strictement supérieure -> TRANCHE (Paris)", st2 == TRANCHE and v2 == "Paris")

# Égalité au sommet -> ABSTENTION (jamais un choix silencieux)
st3, v3, det = arbitre([("Paris", "forum"), ("Lyon", "autre_forum")], fiab)
check("égalité de fiabilité au sommet -> ABSTENTION", st3 == ABSTENTION and v3 is None)
check("les candidats en conflit sont rapportés", set(det.get("candidats", [])) == {"Paris", "Lyon"})

# Somme de fiabilités : deux sources faibles concordantes peuvent battre une moyenne
st4, v4, _ = arbitre([("A", "forum"), ("A", "autre_forum"), ("B", "mesure_labo")], fiab)  # A:0.4 vs B:0.9
check("B (0.9) bat A (0.2+0.2) -> TRANCHE B", st4 == TRANCHE and v4 == "B")

# Source inconnue -> poids 0 (ne tranche pas seule)
st5, v5, _ = arbitre([("X", "source_inconnue"), ("Y", "manuel_officiel")], fiab)
check("source inconnue (poids 0) perd face à une source fiable", st5 == TRANCHE and v5 == "Y")

# Raccourci
check("valeur_arbitree renvoie la valeur (tranché) ou None (abstention)",
      valeur_arbitree([("Paris", "manuel_officiel"), ("Lyon", "forum")], fiab) == "Paris"
      and valeur_arbitree([("Paris", "forum"), ("Lyon", "autre_forum")], fiab) is None)
check("aucune proposition -> ABSTENTION", arbitre([], fiab)[0] == ABSTENTION)

print(f"\n=== valide_arbitre : {ok}/{total} checks OK ===")
if ok != total: raise SystemExit(1)
