"""
VALIDE asteroides.py — held-out ADVERSE. Trois fronts :
  (1) EXACTITUDE d'implémentation : la fonction du module == formule canonique RÉ-ÉCRITE ici (1e-12) ;
  (2) RÉALITÉ PHYSIQUE : la formule canonique reproduit les valeurs publiées (Halley T_J≈-0.6, 67P≈2.75) ;
  (3) SOUNDNESS : entrée invalide / orbite non liée / frontière exacte -> ValueError (jamais un faux) + déterminisme.
Aucune des valeurs d'ancrage n'est lue depuis asteroides.py.
"""
import math

import asteroides as A

ok = 0
ko = 0


def check(cond, label):
    global ok, ko
    if cond:
        ok += 1
    else:
        ko += 1
        print(f"  FAIL: {label}")


def leve_v(fn, *a, **k):
    try:
        fn(*a, **k)
        return False
    except ValueError:
        return True
    except Exception:
        return False


# Formule de Tisserand RÉ-ÉCRITE indépendamment (oracle d'exactitude, ne dépend pas du module).
def ref(a, e, i_deg, aJ=5.204):
    return aJ / a + 2.0 * math.cos(math.radians(i_deg)) * math.sqrt((a / aJ) * (1.0 - e ** 2))


# ── 1) EXACTITUDE : module == formule canonique (au flottant près) ──
for (a, e, i) in [(2.7, 0.1, 5.0), (3.46, 0.641, 7.04), (17.8, 0.967, 162.0), (1.0, 0.0, 0.0), (40.0, 0.85, 30.0)]:
    check(abs(A.tisserand(a, e, i) - ref(a, e, i)) <= 1e-12, f"tisserand==ref ({a},{e},{i})")

# Cas circulaire coplanaire à 1 UA de Jupiter (a=aJ, e=0, i=0) -> aJ/aJ + 2·1·√1 = 1+2 = 3 EXACT.
check(abs(A.tisserand(5.204, 0.0, 0.0) - 3.0) <= 1e-12, "a=aJ, e=0, i=0 -> T=3 exact")

# ── 2) RÉALITÉ PHYSIQUE : valeurs publiées (littérature), oracle = ref ──
check(abs(ref(17.8, 0.967, 162.0) - (-0.60)) <= 0.05, "Halley T_J ≈ -0.60 (publié)")
check(abs(ref(3.46, 0.641, 7.04) - 2.75) <= 0.05, "67P T_J ≈ 2.75 (publié)")
check(3.0 < ref(2.7, 0.1, 5.0) < 3.5, "astéroïde ceinture T_J dans (3 ; 3.5)")

# ── 3) CLASSIFICATION sur les trois cas-types ──
check(A.classifie(A.tisserand(2.7, 0.1, 5.0)) == A.ASTEROIDE, "ceinture -> asteroide")
check(A.classifie(A.tisserand(3.46, 0.641, 7.04)) == A.COMETE_FAMILLE_JUPITER, "67P -> JFC")
check(A.classifie(A.tisserand(17.8, 0.967, 162.0)) == A.COMETE_QUASI_ISOTROPE, "Halley -> quasi-isotrope")
# classifie_orbite cohérent avec (tisserand, classifie)
T0, c0 = A.classifie_orbite(17.8, 0.967, 162.0)
check(abs(T0 - A.tisserand(17.8, 0.967, 162.0)) <= 1e-12 and c0 == A.COMETE_QUASI_ISOTROPE, "classifie_orbite cohérent")

# ── 4) SEUILS de classification (valeurs T directes) ──
check(A.classifie(3.5) == A.ASTEROIDE, "T=3.5 -> asteroide")
check(A.classifie(3.0001) == A.ASTEROIDE, "T=3.0001 -> asteroide")
check(A.classifie(2.5) == A.COMETE_FAMILLE_JUPITER, "T=2.5 -> JFC")
check(A.classifie(2.9999) == A.COMETE_FAMILLE_JUPITER, "T=2.9999 -> JFC")
check(A.classifie(2.0001) == A.COMETE_FAMILLE_JUPITER, "T=2.0001 -> JFC")
check(A.classifie(1.9999) == A.COMETE_QUASI_ISOTROPE, "T=1.9999 -> quasi-isotrope")
check(A.classifie(-0.6) == A.COMETE_QUASI_ISOTROPE, "T=-0.6 -> quasi-isotrope")

# ── 5) FRONTIÈRES exactes ambiguës -> abstention ──
check(leve_v(A.classifie, 3.0), "T==3 frontière -> ValueError")
check(leve_v(A.classifie, 2.0), "T==2 frontière -> ValueError")

# ── 6) SOUNDNESS domaine : a≤0, e<0, e≥1 (non elliptique), aJ≤0 -> ValueError ──
check(leve_v(A.tisserand, 0.0, 0.1, 5.0), "a=0 -> ValueError")
check(leve_v(A.tisserand, -2.7, 0.1, 5.0), "a<0 -> ValueError")
check(leve_v(A.tisserand, 2.7, -0.01, 5.0), "e<0 -> ValueError")
check(leve_v(A.tisserand, 2.7, 1.0, 5.0), "e=1 (parabolique) -> ValueError")
check(leve_v(A.tisserand, 2.7, 1.5, 5.0), "e>1 (hyperbolique) -> ValueError")
check(leve_v(A.tisserand, 2.7, 0.1, 5.0, 0.0), "aJ=0 -> ValueError")
check(leve_v(A.tisserand, 2.7, 0.1, 5.0, -5.204), "aJ<0 -> ValueError")
# e juste sous 1 reste valide (orbite très excentrique liée)
check(isinstance(A.tisserand(2.7, 0.9999, 5.0), float), "e=0.9999 (<1) accepté")

# ── 7) SOUNDNESS types : bool / str / None / NaN / inf -> ValueError ──
check(leve_v(A.tisserand, True, 0.1, 5.0), "a=bool -> ValueError")
check(leve_v(A.tisserand, 2.7, "0.1", 5.0), "e=str -> ValueError")
check(leve_v(A.tisserand, 2.7, 0.1, None), "i=None -> ValueError")
check(leve_v(A.tisserand, float("nan"), 0.1, 5.0), "a=NaN -> ValueError")
check(leve_v(A.tisserand, 2.7, 0.1, float("inf")), "i=inf -> ValueError")
check(leve_v(A.classifie, "3.5"), "classifie(str) -> ValueError")
check(leve_v(A.classifie, True), "classifie(bool) -> ValueError")
check(leve_v(A.classifie, float("nan")), "classifie(NaN) -> ValueError")

# ── 8) DÉTERMINISME ──
check(A.tisserand(2.7, 0.1, 5.0) == A.tisserand(2.7, 0.1, 5.0), "déterminisme tisserand")
check(A.classifie(2.5) == A.classifie(2.5), "déterminisme classifie")
check(A.JUPITER_AJ == 5.204, "aJ par défaut = 5.204 UA")

print(f"\n=== valide_asteroides : {ok}/{ok+ko} ===")
import sys
sys.exit(0 if ko == 0 else 1)
