"""VALIDE classification_surfaces.py — held-out ADVERSE, FAUX=0.
Ancres EXTERNES connues (théorème de classification des surfaces : sphère/tore/bitore,
plan projectif/Klein, formules χ=2-2g et χ=2-k) + SOUNDNESS (surface inexistante -> ValueError)
+ DÉTERMINISME.
"""
import classification_surfaces as M

ok = 0
ko = 0


def check(cond, label):
    global ok, ko
    if cond:
        ok += 1
    else:
        ko += 1
        print(f"  FAIL: {label}")


def leve(fn, *a):
    try:
        fn(*a)
        return False
    except ValueError:
        return True
    except Exception:
        return False


# ── ANCRES ORIENTABLES (χ = 2 - 2g) ──
check(M.classifie_surface(2, True) == "sphère", "χ=2 orientable -> sphère")
check(M.genre(2, True) == 0, "sphère : genre 0")
check(M.classifie_surface(0, True) == "tore", "χ=0 orientable -> tore")
check(M.genre(0, True) == 1, "tore : genre 1")
check(M.classifie_surface(-2, True) == "surface orientable de genre 2", "χ=-2 orientable -> genre 2")
check(M.genre(-2, True) == 2, "bitore : genre 2 (χ=-2)")
check(M.genre(-4, True) == 3, "genre 3 : χ=-4")
check(M.genre(-100, True) == 51, "genre 51 : χ=-100")

# ── ANCRES NON-ORIENTABLES (χ = 2 - k) ──
check(M.classifie_surface(1, False) == "plan projectif", "χ=1 non-orientable -> plan projectif")
check(M.genre(1, False) == 1, "plan projectif : genre non-orientable 1")
check(M.classifie_surface(0, False) == "bouteille de Klein", "χ=0 non-orientable -> bouteille de Klein")
check(M.genre(0, False) == 2, "Klein : genre non-orientable 2")
check(M.classifie_surface(-1, False) == "surface non-orientable de genre 3", "χ=-1 non-or. -> genre 3 (Dyck)")
check(M.genre(-1, False) == 3, "somme de 3 plans projectifs : k=3 (χ=-1)")

# ── est_sphere : ANALOGUE 2D DE POINCARÉ ──
check(M.est_sphere(2, True) is True, "est_sphere(2,True) = vrai (S²)")
check(M.est_sphere(0, True) is False, "est_sphere(tore) = faux")
check(M.est_sphere(-2, True) is False, "est_sphere(bitore) = faux")
check(M.est_sphere(1, False) is False, "est_sphere(plan projectif) = faux")
check(M.est_sphere(0, False) is False, "est_sphere(Klein) = faux")

# ── SOUNDNESS : surfaces INEXISTANTES -> ValueError (jamais de réponse inventée) ──
check(leve(M.genre, 3, True), "χ=3 orientable (impair) -> ValueError")
check(leve(M.genre, 1, True), "χ=1 orientable (impair) -> ValueError")
check(leve(M.genre, -1, True), "χ=-1 orientable (impair) -> ValueError")
check(leve(M.genre, 4, True), "χ=4 orientable (>2, g<0) -> ValueError")
check(leve(M.genre, 2, False), "χ=2 non-orientable (k=0) -> ValueError")
check(leve(M.genre, 3, False), "χ=3 non-orientable (k<1) -> ValueError")
check(leve(M.classifie_surface, 5, True), "χ=5 orientable -> ValueError")
check(leve(M.classifie_surface, 2, False), "χ=2 non-orientable -> ValueError")
check(leve(M.est_sphere, 3, True), "est_sphere χ=3 orientable -> ValueError")
check(leve(M.est_sphere, 2, False), "est_sphere χ=2 non-orientable -> ValueError")

# ── SOUNDNESS : types invalides -> ValueError ──
check(leve(M.genre, 1.5, True), "χ non entier -> ValueError")
check(leve(M.genre, 2.0, True), "χ float (2.0) -> ValueError")
check(leve(M.genre, "2", True), "χ chaîne -> ValueError")
check(leve(M.genre, True, True), "χ booléen -> ValueError")
check(leve(M.genre, 2, 1), "orientable non booléen (1) -> ValueError")
check(leve(M.genre, 2, "oui"), "orientable chaîne -> ValueError")
check(leve(M.classifie_surface, 2, None), "orientable None -> ValueError")

# ── DÉTERMINISME ──
check(M.classifie_surface(-2, True) == M.classifie_surface(-2, True), "déterminisme classifie")
check(M.genre(0, False) == M.genre(0, False), "déterminisme genre")

print(f"\n=== valide_classification_surfaces : {ok}/{ok + ko} ===")
import sys
sys.exit(0 if ko == 0 else 1)
