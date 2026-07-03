"""
VALIDE polymeres.py — held-out ADVERSE. Exactitude des relations (ancrées sur des polymères CONNUS : polyéthylène
M0=28 → DP=1000 ; PET M0=192.17 → DP=100 ; polystyrène M0=104.15 → DP=1000 ; dispersité de la distribution la plus
probable Đ=2 ; Carothers p=0.99 → DP=100, p=0.999 → DP=1000) + réciprocité (DP↔Mn, Carothers↔conversion) +
SOUNDNESS : masse ≤ 0 / DP < 1 / Mw < Mn / conversion ∉ [0,1[ -> ValueError (jamais un faux). Déterminisme.
Aucune de ces ancres n'est codée en dur dans polymeres.py.
"""
import polymeres as P

ok = 0
ko = 0


def check(cond, label):
    global ok, ko
    if cond:
        ok += 1
    else:
        ko += 1
        print(f"  FAIL: {label}")


def approx(v, attendu, tol=1e-6):
    return v is not None and abs(v - attendu) <= tol * (1 + abs(attendu))


def leve(fn, *a):
    try:
        fn(*a)
        return False
    except ValueError:
        return True
    except Exception:
        return False


# ── 1) ANCRES EXTERNES — degré de polymérisation de polymères connus ──
check(approx(P.degre_polymerisation(28000, 28), 1000), "PE : DP = 28000/28 = 1000")
check(approx(P.degre_polymerisation(19217, 192.17), 100), "PET : DP = 19217/192.17 = 100")
check(approx(P.degre_polymerisation(104150, 104.15), 1000), "PS : DP = 104150/104.15 = 1000")
check(approx(P.degre_polymerisation(62500, 62.5), 1000), "PVC : DP = 62500/62.5 = 1000")
check(approx(P.degre_polymerisation(28.05, 28.05), 1), "DP minimal = 1 (Mn = M0)")

# ── 2) RÉCIPROQUE — masse molaire du polymère / du monomère ──
check(approx(P.masse_molaire_polymere(1000, 28), 28000), "PE : Mn = 1000·28 = 28000")
check(approx(P.masse_molaire_polymere(100, 192.17), 19217), "PET : Mn = 100·192.17 = 19217")
check(approx(P.masse_molaire_monomere(28000, 1000), 28), "PE : M0 = 28000/1000 = 28")
check(approx(P.masse_molaire_monomere(19217, 100), 192.17), "PET : M0 = 19217/100 = 192.17")

# ── 3) INDICE DE POLYMOLÉCULARITÉ (dispersité Đ) ──
check(approx(P.indice_polymolecularite(20000, 10000), 2.0), "Đ = Mw/Mn = 2 (distribution la plus probable)")
check(approx(P.indice_polymolecularite(15000, 15000), 1.0), "Đ = 1 (monodisperse)")
check(approx(P.indice_polymolecularite(11000, 10000), 1.1), "Đ = 1.1 (polymère contrôlé)")

# ── 4) ÉQUATION DE CAROTHERS (polycondensation) ──
check(approx(P.degre_polymerisation_carothers(0.99), 100), "Carothers : p=0.99 → DP=100")
check(approx(P.degre_polymerisation_carothers(0.999), 1000), "Carothers : p=0.999 → DP=1000")
check(approx(P.degre_polymerisation_carothers(0.5), 2), "Carothers : p=0.5 → DP=2")
check(approx(P.degre_polymerisation_carothers(0.0), 1), "Carothers : p=0 → DP=1 (pas de réaction)")
check(approx(P.taux_conversion(100), 0.99), "réciproque : DP=100 → p=0.99")
check(approx(P.taux_conversion(2), 0.5), "réciproque : DP=2 → p=0.5")
check(approx(P.taux_conversion(P.degre_polymerisation_carothers(0.95)), 0.95), "aller-retour Carothers ↔ conversion")

# ── 5) DÉTERMINISME ──
check(P.degre_polymerisation(28000, 28) == P.degre_polymerisation(28000, 28), "déterministe (DP)")
check(P.indice_polymolecularite(20000, 10000) == P.indice_polymolecularite(20000, 10000), "déterministe (Đ)")

# ── 6) SOUNDNESS — domaine invalide -> ValueError (jamais un faux) ──
check(leve(P.degre_polymerisation, 0, 28), "masse polymère = 0 -> ValueError")
check(leve(P.degre_polymerisation, 28000, 0), "masse monomère = 0 -> ValueError")
check(leve(P.degre_polymerisation, -28000, 28), "masse polymère < 0 -> ValueError")
check(leve(P.degre_polymerisation, 10, 28), "DP < 1 (Mn < M0) -> ValueError")
check(leve(P.degre_polymerisation, 28000, True), "bool comme masse -> ValueError")
check(leve(P.masse_molaire_polymere, 0.5, 28), "DP = 0.5 < 1 -> ValueError")
check(leve(P.masse_molaire_polymere, 1000, 0), "M0 = 0 -> ValueError")
check(leve(P.masse_molaire_polymere, 1000, -28), "M0 < 0 -> ValueError")
check(leve(P.masse_molaire_monomere, 28000, 0.5), "DP < 1 (monomère) -> ValueError")
check(leve(P.masse_molaire_monomere, 0, 1000), "Mn = 0 (monomère) -> ValueError")
check(leve(P.indice_polymolecularite, 9000, 10000), "Mw < Mn -> ValueError (Đ ≥ 1)")
check(leve(P.indice_polymolecularite, 10000, 0), "Mn = 0 (Đ) -> ValueError")
check(leve(P.indice_polymolecularite, 0, 10000), "Mw = 0 (Đ) -> ValueError")
check(leve(P.degre_polymerisation_carothers, 1.0), "Carothers p=1 (divergence) -> ValueError")
check(leve(P.degre_polymerisation_carothers, 1.5), "Carothers p>1 -> ValueError")
check(leve(P.degre_polymerisation_carothers, -0.1), "Carothers p<0 -> ValueError")
check(leve(P.taux_conversion, 0.5), "taux_conversion DP<1 -> ValueError")
check(leve(P.taux_conversion, "x"), "taux_conversion non numérique -> ValueError")

print(f'\n=== valide_polymeres : {ok}/{ok+ko} ===')
import sys
sys.exit(0 if ko == 0 else 1)
