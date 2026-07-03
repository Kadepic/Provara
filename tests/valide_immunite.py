"""
VALIDE immunite.py — held-out ADVERSE. Exactitude (seuil d'immunité de groupe, Reff, typologie) + soundness
(R0 ≤ 1 / fraction hors [0,1] / entrée non numérique / nom inconnu -> ValueError) + déterminisme. FAUX=0.
Aucune ancre ici n'est codée en dur dans immunite.py (held-out).
"""
import immunite as M

ok = 0
ko = 0


def check(cond, label):
    global ok, ko
    if cond:
        ok += 1
    else:
        ko += 1
        print(f"  FAIL: {label}")


def leve_v(fn, *a, **k) -> bool:
    """True ssi fn(*a, **k) lève ValueError (et rien d'autre)."""
    try:
        fn(*a, **k)
        return False
    except ValueError:
        return True
    except Exception:
        return False


TOL = 1e-12

# ── 1) SEUIL D'IMMUNITÉ DE GROUPE = 1 − 1/R0 (ancres recalculées à la main) ─────────────────────────────────────
# R0=15 : 1 − 1/15 = 14/15 = 0.93333333…  ; R0=2 : 0.5 ; R0=4 : 0.75 ; R0=5 : 0.8 ; R0=1.5 : 1 − 2/3 = 0.33333…
check(abs(M.seuil_immunite_groupe(15) - 14 / 15) < TOL, "seuil R0=15 = 14/15")
check(abs(M.seuil_immunite_groupe(15) - 0.9333333333333333) < 1e-9, "seuil R0=15 ≈ 0.933")
check(abs(M.seuil_immunite_groupe(2) - 0.5) < TOL, "seuil R0=2 = 0.5")
check(abs(M.seuil_immunite_groupe(4) - 0.75) < TOL, "seuil R0=4 = 0.75")
check(abs(M.seuil_immunite_groupe(5) - 0.8) < TOL, "seuil R0=5 = 0.8")
check(abs(M.seuil_immunite_groupe(1.5) - (1.0 - 2.0 / 3.0)) < TOL, "seuil R0=1.5 = 1/3")
check(abs(M.seuil_immunite_groupe(10) - 0.9) < TOL, "seuil R0=10 = 0.9")
# Monotonie : seuil croît avec R0 (plus l'agent est contagieux, plus il faut immuniser).
check(M.seuil_immunite_groupe(20) > M.seuil_immunite_groupe(15) > M.seuil_immunite_groupe(2), "seuil croissant en R0")
# Borne : 0 < seuil < 1 toujours (R0>1).
check(0.0 < M.seuil_immunite_groupe(1.01) < 1.0 and 0.0 < M.seuil_immunite_groupe(1000) < 1.0, "seuil ∈ ]0,1[")

# ── 2) TAUX DE REPRODUCTION EFFECTIF = R0·(1 − f) ──────────────────────────────────────────────────────────────
# R0=15, f=0.95 : 15·0.05 = 0.75  ; R0=2, f=0.5 : 2·0.5 = 1.0 (= seuil exact) ; R0=2, f=0.6 : 2·0.4 = 0.8
check(abs(M.taux_reproduction_effectif(15, 0.95) - 0.75) < 1e-9, "Reff R0=15,f=0.95 = 0.75")
check(abs(M.taux_reproduction_effectif(2, 0.5) - 1.0) < TOL, "Reff R0=2,f=0.5 = 1.0")
check(abs(M.taux_reproduction_effectif(2, 0.6) - 0.8) < TOL, "Reff R0=2,f=0.6 = 0.8")
check(abs(M.taux_reproduction_effectif(15, 0.0) - 15.0) < TOL, "Reff f=0 = R0")
check(abs(M.taux_reproduction_effectif(15, 1.0) - 0.0) < TOL, "Reff f=1 = 0")
check(abs(M.taux_reproduction_effectif(3, 0.5) - 1.5) < TOL, "Reff R0=3,f=0.5 = 1.5")
# Cohérence formelle : à f = seuil, Reff = 1 (au facteur d'arrondi flottant près).
for r0 in (2, 4, 5, 10, 15):
    s = M.seuil_immunite_groupe(r0)
    check(abs(M.taux_reproduction_effectif(r0, s) - 1.0) < 1e-9, f"Reff(R0={r0}, seuil) = 1")

# ── 3) EXTINCTION DE L'ÉPIDÉMIE : Reff < 1 ⟺ f > seuil ─────────────────────────────────────────────────────────
check(M.epidemie_eteinte(15, 0.95) is True, "rougeole f=0.95 > seuil 0.933 -> éteinte")
check(M.epidemie_eteinte(15, 0.90) is False, "rougeole f=0.90 < seuil 0.933 -> non éteinte")
check(M.epidemie_eteinte(2, 0.6) is True, "R0=2 f=0.6 > 0.5 -> éteinte")
check(M.epidemie_eteinte(2, 0.4) is False, "R0=2 f=0.4 < 0.5 -> non éteinte")
# Équivalence f>seuil ⟺ éteinte, testée loin du seuil (évite le bruit flottant au point critique).
for r0 in (2, 3, 5, 15):
    s = M.seuil_immunite_groupe(r0)
    check(M.epidemie_eteinte(r0, min(1.0, s + 0.02)) is True, f"R0={r0} : f juste au-dessus du seuil -> éteinte")
    check(M.epidemie_eteinte(r0, max(0.0, s - 0.02)) is False, f"R0={r0} : f juste sous le seuil -> non éteinte")

# ── 4) TYPOLOGIE DE L'IMMUNITÉ (référentiel fermé) ─────────────────────────────────────────────────────────────
check(M.type_immunite("infection") == M.ACTIVE_NATURELLE, "infection -> active_naturelle")
check(M.type_immunite("maladie") == M.ACTIVE_NATURELLE, "maladie -> active_naturelle")
check(M.type_immunite("vaccin") == M.ACTIVE_ARTIFICIELLE, "vaccin -> active_artificielle")
check(M.type_immunite("vaccination") == M.ACTIVE_ARTIFICIELLE, "vaccination -> active_artificielle")
check(M.type_immunite("anticorps maternels") == M.PASSIVE, "anticorps maternels -> passive")
check(M.type_immunite("serotherapie") == M.PASSIVE, "sérothérapie -> passive")
check(M.type_immunite("immunoglobulines") == M.PASSIVE, "immunoglobulines -> passive")
# Distinction fine ADVERSE : anatoxine (toxoïde = vaccin -> ACTIVE artificielle) ≠ antitoxine (sérum -> PASSIVE).
check(M.type_immunite("anatoxine") == M.ACTIVE_ARTIFICIELLE, "anatoxine (toxoïde) -> active_artificielle")
check(M.type_immunite("antitoxine") == M.PASSIVE, "antitoxine (sérum) -> passive")
check(M.type_immunite("vaccin arnm") == M.ACTIVE_ARTIFICIELLE, "vaccin ARNm -> active_artificielle")
check(M.type_immunite("anticorps monoclonaux") == M.PASSIVE, "anticorps monoclonaux -> passive")
# Normalisation : accents / casse / séparateurs n'affectent pas le résultat.
check(M.type_immunite("Sérothérapie") == M.PASSIVE, "casse+accent : Sérothérapie -> passive")
check(M.type_immunite("  LAIT-MATERNEL ") == M.PASSIVE, "séparateur+casse : LAIT-MATERNEL -> passive")
check(M.type_immunite("Infection Naturelle") == M.ACTIVE_NATURELLE, "infection naturelle -> active_naturelle")

# ── 5) SOUNDNESS — abstention par ValueError (jamais un faux) ──────────────────────────────────────────────────
# R0 ≤ 1 : pas d'épidémie / seuil non défini.
for bad in (1, 0.5, 0, -3, 1.0):
    check(leve_v(M.seuil_immunite_groupe, bad), f"seuil R0={bad} ≤ 1 -> ValueError")
    check(leve_v(M.taux_reproduction_effectif, bad, 0.5), f"Reff R0={bad} ≤ 1 -> ValueError")
    check(leve_v(M.epidemie_eteinte, bad, 0.5), f"épidémie R0={bad} ≤ 1 -> ValueError")
# Fraction hors [0, 1].
for bad in (-0.1, 1.1, 2, -1, 100):
    check(leve_v(M.taux_reproduction_effectif, 15, bad), f"Reff f={bad} hors [0,1] -> ValueError")
    check(leve_v(M.epidemie_eteinte, 15, bad), f"épidémie f={bad} hors [0,1] -> ValueError")
# Entrées non numériques / booléen / NaN / inf.
inf = float("inf")
nan = float("nan")
for bad in ("15", None, [15], True, False, nan, inf, -inf):
    check(leve_v(M.seuil_immunite_groupe, bad), f"seuil R0={bad!r} non réel -> ValueError")
for bad in ("0.5", None, [0.5], True, nan, inf):
    check(leve_v(M.taux_reproduction_effectif, 15, bad), f"Reff f={bad!r} non réel -> ValueError")
# Type d'immunité inconnu / invalide.
for bad in ("inconnu", "covid", "", "   ", "abracadabra", None, 42, ["vaccin"]):
    check(leve_v(M.type_immunite, bad), f"type_immunite {bad!r} -> ValueError")

# ── 6) DÉTERMINISME — mêmes entrées, mêmes sorties (10×) ────────────────────────────────────────────────────────
check(len({M.seuil_immunite_groupe(15) for _ in range(10)}) == 1, "déterminisme seuil")
check(len({M.taux_reproduction_effectif(15, 0.95) for _ in range(10)}) == 1, "déterminisme Reff")
check(len({M.type_immunite("anatoxine") for _ in range(10)}) == 1, "déterminisme type_immunite")

print(f'\n=== valide_immunite : {ok}/{ok+ko} ===')
import sys
sys.exit(0 if ko == 0 else 1)
