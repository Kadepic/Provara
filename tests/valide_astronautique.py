"""
VALIDE astronautique.py — held-out ADVERSE. Ancres EXTERNES connues (NON recalculées par la même expression) :
  • Δv = 3000·ln2 ≈ 2079.44 m/s (cas classique du sujet) ;
  • vitesse orbitale LEO ~7.67 km/s (valeur de référence aérospatiale) ;
  • vitesse de libération à la surface terrestre = 11.186 km/s (constante physique connue) ;
  • période géostationnaire = jour sidéral ≈ 86164 s (donnée astronomique connue) ;
  • rapport de masse exp(1) = e quand Δv = ve (constante mathématique connue).
+ SOUNDNESS : ve ≤ 0, m0 ≤ mf, mf ≤ 0, dv < 0, M ≤ 0, r ≤ 0, type non numérique -> ValueError (jamais un faux).
+ DÉTERMINISME.
"""
import math

import astronautique as A

ok = 0
ko = 0


def check(cond, label):
    global ok, ko
    if cond:
        ok += 1
    else:
        ko += 1
        print(f"  FAIL: {label}")


def approx(v, attendu, rel=1e-6):
    return v is not None and abs(v - attendu) <= rel * abs(attendu) + 1e-12


def leve(fn, *a):
    try:
        fn(*a)
        return False
    except ValueError:
        return True
    except Exception:
        return False


# ── 1) TSIOLKOVSKY — ancre du sujet : Δv = 3000·ln2 ─────────────────────────────────────────────────────────────
check(approx(A.delta_v(3000, 100, 50), 2079.441541679836), "Δv(3000,100,50) = 3000·ln2 ≈ 2079.44 m/s")
# ratio 100/50 = 2 -> ln(2). Indépendant : on connaît ln2 = 0.69314718055994530942.
check(approx(A.delta_v(3000, 100, 50), 3000 * 0.69314718055994531), "Δv = ve·ln2 (ancre ln2 externe)")
# Δv s'additionne par étages : ve·ln(m0/mf) avec m0/mf=4 vaut 2× le cas ratio 2 (ln4 = 2·ln2).
check(approx(A.delta_v(3000, 100, 25), 2 * A.delta_v(3000, 100, 50)), "ln(4) = 2·ln(2) (cohérence log)")

# ── 2) RAPPORT DE MASSE — réciproque de Tsiolkovsky, ancre e ─────────────────────────────────────────────────────
check(approx(A.rapport_de_masse(3000, 3000), math.e), "Δv=ve -> rapport de masse = e ≈ 2.71828")
check(approx(A.rapport_de_masse(3000, 0), 1.0), "Δv=0 -> rapport de masse = 1 (aucune combustion)")
# Round-trip : pour le Δv du cas 1, le rapport doit redonner 2 (m0/mf = 100/50).
check(approx(A.rapport_de_masse(3000, A.delta_v(3000, 100, 50)), 2.0, rel=1e-9),
      "rapport_de_masse(Δv de 100->50) = 2 (réciproque exacte)")

# ── 3) MASSE FINALE — mf = m0·exp(-Δv/ve) ───────────────────────────────────────────────────────────────────────
check(approx(A.masse_finale(3000, 100, A.delta_v(3000, 100, 50)), 50.0, rel=1e-9),
      "masse_finale(100, Δv 100->50) = 50 kg (réciproque exacte)")
check(approx(A.masse_finale(3000, 100, 0), 100.0), "Δv=0 -> mf = m0")

# ── 4) VITESSE ORBITALE — LEO ~7.67 km/s (tol 2% comme spécifié) ─────────────────────────────────────────────────
v_leo = A.vitesse_orbitale(A.MASSE_TERRE, A.RAYON_TERRE + 400e3)
check(approx(v_leo, 7670.0, rel=2e-2), "vitesse orbitale LEO (400 km) ≈ 7.67 km/s (tol 2%)")
check(approx(v_leo, 7672.490413283604), "vitesse orbitale LEO valeur exacte recalculée à la main")
# Surface : v_orb = √(GM/R). Plus on est haut, plus c'est lent (monotone décroissant en r).
check(A.vitesse_orbitale(A.MASSE_TERRE, A.RAYON_TERRE)
      > A.vitesse_orbitale(A.MASSE_TERRE, A.RAYON_TERRE + 400e3), "v_orb décroît avec l'altitude")

# ── 5) VITESSE DE LIBÉRATION — 11.186 km/s à la surface (constante connue) ──────────────────────────────────────
v_esc = A.vitesse_liberation(A.MASSE_TERRE, A.RAYON_TERRE)
check(approx(v_esc, 11186.0, rel=2e-3), "vitesse de libération terrestre ≈ 11.186 km/s")
# Relation exacte indépendante : v_esc = √2 · v_orb au même rayon.
check(approx(v_esc, math.sqrt(2) * A.vitesse_orbitale(A.MASSE_TERRE, A.RAYON_TERRE), rel=1e-9),
      "v_lib = √2 · v_orb (relation exacte)")

# ── 6) PÉRIODE ORBITALE — géostationnaire = jour sidéral ≈ 86164 s ──────────────────────────────────────────────
T_geo = A.periode_orbitale(A.MASSE_TERRE, 4.2164e7)
check(approx(T_geo, 86164.0, rel=1e-3), "période à r=42164 km ≈ jour sidéral 86164 s (orbite géostationnaire)")
# Kepler : T ∝ r^{3/2}. Quadrupler r multiplie T par 8.
check(approx(A.periode_orbitale(A.MASSE_TERRE, 4 * A.RAYON_TERRE),
             8 * A.periode_orbitale(A.MASSE_TERRE, A.RAYON_TERRE), rel=1e-9),
      "3e loi de Kepler : r×4 -> T×8")

# ── 7) SOUNDNESS — domaine invalide -> ValueError (jamais un faux) ──────────────────────────────────────────────
check(leve(A.delta_v, 0, 100, 50), "ve=0 -> ValueError")
check(leve(A.delta_v, -3000, 100, 50), "ve<0 -> ValueError")
check(leve(A.delta_v, 3000, 50, 100), "m0<mf -> ValueError")
check(leve(A.delta_v, 3000, 50, 50), "m0=mf (ln1=0 mais combustion nulle interdite) -> ValueError")
check(leve(A.delta_v, 3000, 100, 0), "mf=0 -> ValueError")
check(leve(A.delta_v, 3000, 100, -50), "mf<0 -> ValueError")
check(leve(A.rapport_de_masse, 0, 3000), "rapport : ve=0 -> ValueError")
check(leve(A.rapport_de_masse, 3000, -1), "rapport : Δv<0 -> ValueError")
check(leve(A.masse_finale, 3000, 0, 100), "masse_finale : m0=0 -> ValueError")
check(leve(A.vitesse_orbitale, -1, 7e6), "v_orb : M<0 -> ValueError")
check(leve(A.vitesse_orbitale, A.MASSE_TERRE, 0), "v_orb : r=0 -> ValueError")
check(leve(A.vitesse_liberation, A.MASSE_TERRE, -1), "v_lib : r<0 -> ValueError")
check(leve(A.periode_orbitale, 0, 7e6), "T : M=0 -> ValueError")

# ── 8) SOUNDNESS — types non numériques (bool/str/None) -> ValueError ───────────────────────────────────────────
check(leve(A.delta_v, True, 100, 50), "ve=bool -> ValueError")
check(leve(A.delta_v, 3000, "cent", 50), "m0=str -> ValueError")
check(leve(A.vitesse_orbitale, A.MASSE_TERRE, None), "r=None -> ValueError")
check(leve(A.delta_v, 3000, float("inf"), 50), "m0=inf -> ValueError")

# ── 9) DÉTERMINISME ─────────────────────────────────────────────────────────────────────────────────────────────
check(A.delta_v(3000, 100, 50) == A.delta_v(3000, 100, 50), "déterminisme delta_v")
check(A.vitesse_orbitale(A.MASSE_TERRE, 7e6) == A.vitesse_orbitale(A.MASSE_TERRE, 7e6), "déterminisme v_orb")

print(f"\n=== valide_astronautique : {ok}/{ok+ko} ===")
import sys
sys.exit(0 if ko == 0 else 1)
