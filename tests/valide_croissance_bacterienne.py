"""
VALIDE croissance_bacterienne.py — held-out ADVERSE.

ANCRES NON CIRCULAIRES : valeurs de doublement calculées À LA MAIN (puissances entières de 2), indépendantes
de l'implémentation. SOUNDNESS : N0<=0, g<=0, t<0, Nt<=0, Nt<=N0, booléens, non numériques -> ValueError
(jamais un nombre inventé). DÉTERMINISME. Aucune de ces ancres n'est dans __main__.
"""
import math

import croissance_bacterienne as C

ok = 0
ko = 0


def check(cond, label):
    global ok, ko
    if cond:
        ok += 1
    else:
        ko += 1
        print(f"  FAIL: {label}")


def _leve(fn, *a, **k):
    try:
        fn(*a, **k)
        return False
    except ValueError:
        return True
    except Exception:
        return False


# ── 1) population : ANCRES = puissances entières de 2 (calcul à la main) ───────────────────────────────
# N0=1000, g=20, t=60 -> 2^(60/20)=2^3=8 -> 8000  (CAS de référence E. coli)
check(abs(C.population(1000, 60, 20) - 8000.0) < 1e-6, "population(1000,60,20)=8000")
# N0=1, g=20, t=20 -> 2^1 = 2  (un doublement après 1 génération)
check(abs(C.population(1, 20, 20) - 2.0) < 1e-9, "doublement après 1 g : population(1,20,20)=2")
# N0=100, g=30, t=90 -> 2^3 = 8 -> 800
check(abs(C.population(100, 90, 30) - 800.0) < 1e-6, "population(100,90,30)=800")
# N0=1000, g=20, t=200 -> 2^10 = 1024 -> 1 024 000
check(abs(C.population(1000, 200, 20) - 1_024_000.0) < 1e-3, "population(1000,200,20)=1024000")
# N0=5e6, g=30, t=120 -> 2^4 = 16 -> 8e7
check(abs(C.population(5_000_000, 120, 30) - 80_000_000.0) < 1.0, "population(5e6,120,30)=8e7")
# t=0 -> 2^0 = 1 -> N0 inchangé
check(abs(C.population(1234, 0, 20) - 1234.0) < 1e-9, "population(...,t=0,...)=N0")
# demi-génération : N0=1000, g=20, t=10 -> 1000*sqrt(2) = 1414.2135..., arrondi 6 sig = 1414.21
check(abs(C.population(1000, 10, 20) - 1414.21) < 1e-3, "population(1000,10,20)~1414.21 (6 sig)")

# ── 2) nombre_generations : ANCRES = log2 d'entiers (calcul à la main) ─────────────────────────────────
check(abs(C.nombre_generations(1000, 8000) - 3.0) < 1e-9, "nombre_generations(1000,8000)=3")
check(abs(C.nombre_generations(1, 1024) - 10.0) < 1e-9, "nombre_generations(1,1024)=10")
check(abs(C.nombre_generations(2, 16) - 3.0) < 1e-9, "nombre_generations(2,16)=3")
check(abs(C.nombre_generations(1000, 1_024_000) - 10.0) < 1e-9, "nombre_generations(1000,1024000)=10")
check(abs(C.nombre_generations(500, 500) - 0.0) < 1e-12, "nombre_generations(500,500)=0 (pas de croissance)")

# ── 3) temps_generation : ANCRES inverses (calcul à la main) ───────────────────────────────────────────
# g = t / log2(Nt/N0). t=60, log2(8)=3 -> 20
check(abs(C.temps_generation(1000, 8000, 60) - 20.0) < 1e-6, "temps_generation(1000,8000,60)=20")
# t=100, log2(1024)=10 -> 10
check(abs(C.temps_generation(1, 1024, 100) - 10.0) < 1e-6, "temps_generation(1,1024,100)=10")
# t=90, log2(8)=3 -> 30
check(abs(C.temps_generation(100, 800, 90) - 30.0) < 1e-6, "temps_generation(100,800,90)=30")

# ── 4) COHÉRENCE INTERNE (inversions mutuelles, non circulaire vs les ancres ci-dessus) ────────────────
for N0, t, g in [(2500, 75, 15), (10, 240, 17), (1e4, 333, 41)]:
    Nt = C.population(N0, t, g)
    check(abs(C.temps_generation(N0, Nt, t) - C._sig(g)) < 1e-3, f"round-trip g ({N0},{t},{g})")
    check(abs(C.nombre_generations(N0, Nt) - (t / g)) < 1e-3, f"round-trip n ({N0},{t},{g})")

# ── 5) SOUNDNESS population : N0<=0, g<=0, t<0 -> ValueError ───────────────────────────────────────────
check(_leve(C.population, 0, 60, 20), "population N0=0 -> ValueError")
check(_leve(C.population, -1000, 60, 20), "population N0<0 -> ValueError")
check(_leve(C.population, 1000, 60, 0), "population g=0 -> ValueError")
check(_leve(C.population, 1000, 60, -20), "population g<0 -> ValueError")
check(_leve(C.population, 1000, -1, 20), "population t<0 -> ValueError")

# ── 6) SOUNDNESS temps_generation : domaine ───────────────────────────────────────────────────────────
check(_leve(C.temps_generation, 0, 8000, 60), "temps_gen N0=0 -> ValueError")
check(_leve(C.temps_generation, 1000, 0, 60), "temps_gen Nt=0 -> ValueError")
check(_leve(C.temps_generation, 1000, -8000, 60), "temps_gen Nt<0 -> ValueError")
check(_leve(C.temps_generation, 1000, 8000, 0), "temps_gen t=0 -> ValueError")
check(_leve(C.temps_generation, 1000, 8000, -60), "temps_gen t<0 -> ValueError")
check(_leve(C.temps_generation, 1000, 1000, 60), "temps_gen Nt=N0 -> ValueError (div par zéro évitée)")
check(_leve(C.temps_generation, 1000, 500, 60), "temps_gen Nt<N0 -> ValueError (décroissance)")

# ── 7) SOUNDNESS nombre_generations : domaine ─────────────────────────────────────────────────────────
check(_leve(C.nombre_generations, 0, 8000), "nb_gen N0=0 -> ValueError")
check(_leve(C.nombre_generations, -1, 8000), "nb_gen N0<0 -> ValueError")
check(_leve(C.nombre_generations, 1000, 0), "nb_gen Nt=0 -> ValueError")
check(_leve(C.nombre_generations, 1000, -8000), "nb_gen Nt<0 -> ValueError")
check(_leve(C.nombre_generations, 1000, 500), "nb_gen Nt<N0 -> ValueError (n<0 hors modèle)")

# ── 8) SOUNDNESS types : booléens / non numériques / NaN / inf -> ValueError ──────────────────────────
for bad in [True, False, None, "1000", [1000], 1000j]:
    check(_leve(C.population, bad, 60, 20), f"population N0={bad!r} -> ValueError")
    check(_leve(C.nombre_generations, 1000, bad), f"nb_gen Nt={bad!r} -> ValueError")
check(_leve(C.population, float("nan"), 60, 20), "population NaN -> ValueError")
check(_leve(C.population, float("inf"), 60, 20), "population inf -> ValueError")
check(_leve(C.population, 1000, float("inf"), 20), "population t=inf -> ValueError")
check(_leve(C.temps_generation, 1000, float("nan"), 60), "temps_gen NaN -> ValueError")

# ── 9) DÉTERMINISME ───────────────────────────────────────────────────────────────────────────────────
check(C.population(1000, 60, 20) == C.population(1000, 60, 20), "déterminisme population")
check(C.nombre_generations(1000, 8000) == C.nombre_generations(1000, 8000), "déterminisme nb_gen")
check(C.temps_generation(1000, 8000, 60) == C.temps_generation(1000, 8000, 60), "déterminisme temps_gen")

print(f"\n=== valide_croissance_bacterienne : {ok}/{ok+ko} ===")
import sys
sys.exit(0 if ko == 0 else 1)
