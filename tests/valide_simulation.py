"""
VALIDATION de la SIMULATION / FORWARD-MODEL (simulation.py) — Vague 3.
FAUX=0 : déterministe, états validés, conflit de règles détecté, terminant + convergence honnête.
"""
from __future__ import annotations

import dimensions as D
from grandeur import Grandeur
from etat import EspaceEtats
from simulation import Simulateur, ConflitDeRegles

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


# Espace : une population (sans dimension) + un compteur de pas.
E = EspaceEtats()
E.variable("population", dimension=D.SANS)
E.variable("etape", dimension=D.SANS)

# Règles : décroissance exponentielle ×0.9 par pas + incrément du compteur.
decroit = lambda e: {"population": e.valeur("population") * 0.9}
horloge = lambda e: {"etape": e.valeur("etape") + Grandeur(1, D.SANS)}
sim = Simulateur(E, [decroit, horloge])

e0 = E.etat(population=Grandeur(1000, D.SANS), etape=Grandeur(0, D.SANS))
traj = sim.simule(e0, 3, arret_point_fixe=False)
check("trajectoire de 4 états (e0 + 3 pas)", len(traj) == 4)
check("population décroît 1000 -> 900 -> 810 -> 729", abs(traj[3].valeur("population").valeur - 729) < 1e-9)
check("compteur avance 0 -> 3", traj[3].valeur("etape").valeur == 3)
check("état d'origine inchangé (immuabilité à travers la simu)", e0.valeur("population").valeur == 1000)

# ── Déterminisme ─────────────────────────────────────────────────────────────────────────
traj2 = Simulateur(E, [decroit, horloge]).simule(e0, 3, arret_point_fixe=False)
check("déterministe : même trajectoire au re-run",
      [t.valeur("population").valeur for t in traj] == [t.valeur("population").valeur for t in traj2])

# ── Point fixe : convergence vers un équilibre ───────────────────────────────────────────
# règle : x -> (x + 10)/2  (converge vers 10). Sur domaine continu, on s'arrête quand l'état ne bouge plus.
Ex = EspaceEtats()
Ex.variable("x", dimension=D.SANS)
# arrondi pour atteindre un point fixe EXACT (sinon convergence asymptotique infinie) :
relax = lambda e: {"x": Grandeur(round((e.valeur("x").valeur + 10) / 2, 6), D.SANS)}
simx = Simulateur(Ex, [relax])
fin, conv = simx.point_fixe(Ex.etat(x=Grandeur(0, D.SANS)), max_pas=1000)
check("point fixe atteint (convergence honnête)", conv)
check("équilibre ≈ 10", abs(fin.valeur("x").valeur - 10) < 1e-3)

# budget insuffisant -> non convergé HONNÊTEMENT (pas de convergence fabriquée)
_, conv2 = simx.point_fixe(Ex.etat(x=Grandeur(0, D.SANS)), max_pas=1)
check("budget épuisé -> converge=False (honnête)", not conv2)

# ── FAUX=0 : conflit de règles détecté ───────────────────────────────────────────────────
r_a = lambda e: {"x": Grandeur(1, D.SANS)}
r_b = lambda e: {"x": Grandeur(2, D.SANS)}
simc = Simulateur(Ex, [r_a, r_b])
check("deux règles imposant des valeurs différentes -> ConflitDeRegles",
      leve(lambda: simc.pas(Ex.etat(x=Grandeur(0, D.SANS))), ConflitDeRegles))
# deux règles imposant la MÊME valeur = pas de conflit
simok = Simulateur(Ex, [r_a, lambda e: {"x": Grandeur(1, D.SANS)}])
check("deux règles concordantes -> pas de conflit", simok.pas(Ex.etat(x=Grandeur(0, D.SANS))).valeur("x").valeur == 1)

# ── FAUX=0 : une règle produisant un état invalide est refusée ───────────────────────────
from etat import ValeurHorsDomaine
Ed = EspaceEtats()
Ed.variable("phase", domaine={"a", "b"})
simbad = Simulateur(Ed, [lambda e: {"phase": "c"}])   # 'c' hors domaine
check("règle produisant une valeur hors domaine -> refusée (ValeurHorsDomaine)",
      leve(lambda: simbad.pas(Ed.etat(phase="a")), ValeurHorsDomaine))

print(f"\n=== valide_simulation : {ok}/{total} checks OK ===")
if ok != total:
    raise SystemExit(1)
