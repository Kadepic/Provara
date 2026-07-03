"""VALIDATION structure_mapping.py (Vague 4). FAUX=0 : correspondance préserve la structure ; sinon None ; couverture factuelle."""
from __future__ import annotations
from structure_mapping import trouve, couverture

ok = 0; total = 0
def check(nom, cond):
    global ok, total; total += 1
    print(f"  [{'OK ' if cond else 'XXX'}] {nom}", flush=True)
    if cond: ok += 1
    else: raise AssertionError(nom)

# Analogie classique : flux de chaleur ~ flux électrique (mêmes relations de transport).
chaleur = [("cause", "diff_temperature", "flux_chaleur"),
           ("proportionnel", "flux_chaleur", "conductivite_thermique"),
           ("s_oppose", "resistance_thermique", "flux_chaleur")]
elec = [("cause", "diff_potentiel", "flux_courant"),
        ("proportionnel", "flux_courant", "conductivite_elec"),
        ("s_oppose", "resistance_elec", "flux_courant")]

r = trouve(chaleur, elec)
check("analogie chaleur->électricité trouvée", r is not None)
mapping, alignees = r
check("diff_temperature <-> diff_potentiel (structure préservée)", mapping["diff_temperature"] == "diff_potentiel")
check("flux_chaleur <-> flux_courant", mapping["flux_chaleur"] == "flux_courant")
check("les 3 relations sont alignées (systématicité totale)", len(alignees) == 3)
check("couverture = 1.0 (analogie parfaite)", abs(couverture(chaleur, elec) - 1.0) < 1e-9)

# FAUX=0 : deux domaines sans structure commune -> pas d'analogie inventée
sans_rapport = [("aime", "alice", "bob"), ("aime", "bob", "carol")]
autre = [("pese", "pierre", "kg"), ("mesure", "table", "m")]
check("aucune structure commune -> None (pas d'analogie forcée)", trouve(sans_rapport, autre) is None)
check("couverture 0 quand pas d'analogie", couverture(sans_rapport, autre) == 0.0)

# Analogie PARTIELLE : seules certaines relations s'alignent -> couverture < 1
partiel_src = [("cause", "a", "b"), ("proportionnel", "b", "c"), ("special_src", "a", "c")]
partiel_cib = [("cause", "x", "y"), ("proportionnel", "y", "z")]
cp = couverture(partiel_src, partiel_cib)
check("analogie partielle : 0 < couverture < 1 (honnête)", 0 < cp < 1)

# Injectivité : un objet source -> un seul objet cible
check("mapping injectif (pas deux sources sur la même cible)", len(set(mapping.values())) == len(mapping))

print(f"\n=== valide_structure_mapping : {ok}/{total} checks OK ===")
if ok != total: raise SystemExit(1)
