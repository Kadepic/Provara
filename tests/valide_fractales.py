"""VALIDE fractales.py — held-out ADVERSE, FAUX=0. Ancres EXTERNES connues (valeurs publiées des dimensions de
Cantor/Koch/Sierpiński/Menger… et dimensions ENTIÈRES des objets pleins, NON recalculées par la même expression)
+ SOUNDNESS : N<1 / facteur≤1 / type invalide -> ValueError (jamais un faux) + déterminisme.
"""
import fractales as F

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


def proche(a, b, tol=1e-9):
    return abs(a - b) <= tol


# ── 1) ANCRES EXTERNES — dimensions fractales PUBLIÉES (référence indépendante, pas re-dérivée ici) ──
check(proche(F.dimension_similarite(2, 3), 0.6309297536), "Cantor ln2/ln3 ≈ 0.6309297536")
check(proche(F.dimension_similarite(4, 3), 1.2618595071), "Koch ln4/ln3 ≈ 1.2618595071")
check(proche(F.dimension_similarite(3, 2), 1.5849625007), "Sierpiński △ ln3/ln2 ≈ 1.5849625007")
check(proche(F.dimension_similarite(8, 3), 1.8927892607), "tapis Sierpiński ln8/ln3 ≈ 1.8927892607")
check(proche(F.dimension_similarite(20, 3), 2.726833028), "éponge Menger ln20/ln3 ≈ 2.726833028")

# ── 2) ANCRES EXACTES — objets pleins de dimension ENTIÈRE (résultat connu sans aucune décimale) ──
check(F.dimension_similarite(2, 2) == 1.0, "segment plein -> 1 exact")
check(F.dimension_similarite(4, 2) == 2.0, "carré plein -> 2 exact")
check(F.dimension_similarite(8, 2) == 3.0, "cube plein -> 3 exact")
check(F.dimension_similarite(9, 3) == 2.0, "courbe de Peano (remplit le plan) -> 2 exact")
check(F.dimension_similarite(27, 3) == 3.0, "27 copies réduites de 3 -> 3 exact")
check(F.dimension_similarite(1, 5) == 0.0, "1 seule copie -> dimension 0 (point)")

# ── 3) PROPRIÉTÉS qualitatives connues ──
# Un fractal a une dimension NON entière strictement comprise entre sa dimension topologique et celle de l'espace.
d_koch = F.dimension_similarite(4, 3)
check(1.0 < d_koch < 2.0, "Koch : 1 < D < 2 (entre courbe et plan)")
d_cantor = F.dimension_similarite(2, 3)
check(0.0 < d_cantor < 1.0, "Cantor : 0 < D < 1 (entre point et segment)")
# Base du logarithme indifférente : (N, f) et (N^k, f^k) ont la MÊME dimension.
check(proche(F.dimension_similarite(3, 2), F.dimension_similarite(9, 4)), "invariance d'échelle ln3/ln2 = ln9/ln4")
check(proche(F.dimension_similarite(2, 3), F.dimension_similarite(4, 9)), "invariance d'échelle ln2/ln3 = ln4/ln9")

# ── 4) REGISTRE de fractals nommés ──
check(proche(F.dimension_connue("cantor"), 0.6309297536), "registre : cantor")
check(F.dimension_connue("carre_plein") == 2.0, "registre : carre_plein -> 2")
check(F.dimension_connue("MENGER_SPONGE") == F.dimension_similarite(20, 3), "registre insensible à la casse")
check(F.fractales_connues() == tuple(sorted(F.fractales_connues())), "noms triés (déterministe)")
check(len(F.fractales_connues()) == 9, "9 fractals au registre")

# ── 5) SOUNDNESS — N < 1 -> ValueError ──
check(leve(F.dimension_similarite, 0, 3), "N=0 -> ValueError")
check(leve(F.dimension_similarite, -2, 3), "N<0 -> ValueError")
check(leve(F.dimension_similarite, 0.5, 3), "0<N<1 -> ValueError")

# ── 6) SOUNDNESS — facteur ≤ 1 -> ValueError ──
check(leve(F.dimension_similarite, 2, 1), "facteur=1 -> ValueError (ln1=0)")
check(leve(F.dimension_similarite, 2, 0.5), "0<facteur<1 -> ValueError")
check(leve(F.dimension_similarite, 2, 0), "facteur=0 -> ValueError")
check(leve(F.dimension_similarite, 2, -3), "facteur<0 -> ValueError")

# ── 7) SOUNDNESS — types invalides / non finis -> ValueError ──
check(leve(F.dimension_similarite, True, 3), "bool n'est pas un nombre -> ValueError")
check(leve(F.dimension_similarite, 2, True), "bool facteur -> ValueError")
check(leve(F.dimension_similarite, "2", 3), "str -> ValueError")
check(leve(F.dimension_similarite, 2, "3"), "str facteur -> ValueError")
check(leve(F.dimension_similarite, float("inf"), 3), "N=inf -> ValueError")
check(leve(F.dimension_similarite, 2, float("nan")), "facteur=NaN -> ValueError")
check(leve(F.dimension_connue, "inconnu"), "fractal inconnu -> ValueError")
check(leve(F.dimension_connue, 42), "nom non-str -> ValueError")

# ── 8) DÉTERMINISME ──
check(F.dimension_similarite(4, 3) == F.dimension_similarite(4, 3), "déterminisme")

print(f"\n=== valide_fractales : {ok}/{ok + ko} ===")
import sys
sys.exit(0 if ko == 0 else 1)
