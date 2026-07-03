"""
VALIDATION de la CAUSALITÉ (causalite.py) — Vague 1.
FAUX=0 : acyclique, do(x)≠observer(x) (intervention n'affecte que les descendants), aucun lien causal inventé.
"""
from __future__ import annotations

from causalite import GrapheCausal, CycleCausal

ok = 0
total = 0


def check(nom, cond):
    global ok, total
    total += 1
    print(f"  [{'OK ' if cond else 'XXX'}] {nom}", flush=True)
    if cond:
        ok += 1
    else:
        raise AssertionError(nom)


def leve(fn, exc):
    try:
        fn(); return False
    except exc:
        return True


# Graphe classique : arroseur/pluie -> sol_mouillé -> glissant ; saison -> pluie & arroseur.
g = GrapheCausal()
g.ajoute_cause("saison", "pluie")
g.ajoute_cause("saison", "arroseur")
g.ajoute_cause("pluie", "sol_mouillé", mecanisme="dépôt d'eau", signe="+")
g.ajoute_cause("arroseur", "sol_mouillé", signe="+")
g.ajoute_cause("sol_mouillé", "glissant", signe="+")

# ── Structure causale correcte ───────────────────────────────────────────────────────────
check("effets directs de sol_mouillé = {glissant}", g.effets_directs("sol_mouillé") == {"glissant"})
check("causes directes de sol_mouillé = {pluie, arroseur}", g.causes_directes("sol_mouillé") == {"pluie", "arroseur"})
check("descendants(pluie) = {sol_mouillé, glissant}", g.descendants("pluie") == {"sol_mouillé", "glissant"})
check("ancêtres(glissant) = {sol_mouillé, pluie, arroseur, saison}",
      g.ancetres("glissant") == {"sol_mouillé", "pluie", "arroseur", "saison"})
check("cause_de(saison, glissant) via la chaîne", g.cause_de("saison", "glissant"))
check("PAS cause_de(glissant, saison) (sens respecté)", not g.cause_de("glissant", "saison"))

# ── INTERVENIR ≠ OBSERVER (le cœur causal) ───────────────────────────────────────────────
check("do(sol_mouillé) affecte {sol_mouillé, glissant} — PAS pluie ni arroseur",
      g.intervenir("sol_mouillé") == {"sol_mouillé", "glissant"})
check("intervenir NE remonte PAS aux causes (pluie ∉ do(sol_mouillé))", "pluie" not in g.intervenir("sol_mouillé"))
check("OBSERVER sol_mouillé informe AUSSI sur les causes (pluie ∈ observer)",
      "pluie" in g.observer_informe("sol_mouillé"))
check("distinction agir/observer effective", g.intervenir("sol_mouillé") != g.observer_informe("sol_mouillé"))

# ── Chaînes causales (chemins réels) ─────────────────────────────────────────────────────
ch = g.chaines("saison", "glissant")
check("chaînes saison->glissant : 2 chemins (via pluie, via arroseur)", len(ch) == 2)
check("un chemin est saison->pluie->sol_mouillé->glissant",
      ["saison", "pluie", "sol_mouillé", "glissant"] in ch)
check("chaînes vers un nœud non relié = [] (aucun lien inventé)", g.chaines("glissant", "saison") == [])

# ── Leviers d'action pour changer une cible ──────────────────────────────────────────────
check("leviers(glissant) = ses causes actionnables",
      g.leviers("glissant") == {"sol_mouillé", "pluie", "arroseur", "saison"})

# ── Mécanisme porté par l'arête ──────────────────────────────────────────────────────────
check("mécanisme/signe récupérable sur l'arête", g.mecanisme("pluie", "sol_mouillé") == ("dépôt d'eau", "+"))
check("mécanisme d'une arête inexistante = None", g.mecanisme("glissant", "pluie") is None)

# ── FAUX=0 : acyclicité ──────────────────────────────────────────────────────────────────
check("REJET : auto-causalité (X cause X)", leve(lambda: g.ajoute_cause("x", "x"), CycleCausal))
check("REJET : arête fermant un cycle (glissant -> pluie)",
      leve(lambda: g.ajoute_cause("glissant", "pluie"), CycleCausal))
check("après rejet du cycle, structure intacte", g.cause_de("pluie", "glissant") and not g.cause_de("glissant", "pluie"))

print(f"\n=== valide_causalite : {ok}/{total} checks OK ===")
if ok != total:
    raise SystemExit(1)
