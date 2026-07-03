"""VALIDE entropie_thermo.py — held-out ADVERSE (deuxième principe / entropie).

ANCRES EXTERNES (valeurs de référence NON recalculées par la même expression du module) :
  • ΔS = Q/T : 100 J à 200 K -> 0.5 J/K ; 100 J à 100 K -> 1.0 ; −100 J à 200 K -> −0.5 (réservoir refroidi).
  • ΔS_univers d'un transfert chaud->froid (100 J, 400 K -> 300 K) = 1/3 − 1/4 = 1/12 = 0.08333333… > 0 (spontané).
  • Transfert froid->chaud (mêmes réservoirs, Q reçu négatif) = −1/12 < 0 (NON spontané, énoncé de Clausius).
  • Réversible (T_chaud = T_froid) -> ΔS_univers = 0 -> NON spontané (équilibre).
SOUNDNESS : T ≤ 0 K, type non numérique (bool/str), valeur non finie (NaN/inf) -> ValueError (jamais un faux).
DÉTERMINISME : même entrée -> même sortie.
"""
import math

import entropie_thermo as E

ok = 0
ko = 0


def check(cond, label):
    global ok, ko
    if cond:
        ok += 1
    else:
        ko += 1
        print(f"  FAIL: {label}")


def approx(v, attendu, tol=1e-9):
    return abs(v - attendu) <= tol


def leve(fn, *a):
    try:
        fn(*a)
        return False
    except ValueError:
        return True


# ── 1) ANCRES — variation_entropie = Q/T (valeurs simples connues) ──
check(E.variation_entropie(100, 200) == 0.5, "ΔS = 100/200 = 0.5 J/K")
check(E.variation_entropie(100, 100) == 1.0, "ΔS = 100/100 = 1.0 J/K")
check(E.variation_entropie(-100, 200) == -0.5, "ΔS = −100/200 = −0.5 J/K (réservoir refroidi)")
check(E.variation_entropie(0, 300) == 0.0, "ΔS = 0/300 = 0 (pas de transfert)")
check(approx(E.variation_entropie(1000, 273.15), 1000 / 273.15), "ΔS = 1000/273.15 (fusion glace réf.)")

# ── 2) ANCRES — entropie_univers (transfert chaud->froid) ──
check(approx(E.entropie_univers(100, 400, 300), 1.0 / 12.0), "ΔS_univers = 1/3−1/4 = 1/12 ≈ 0.0833 > 0")
check(E.entropie_univers(100, 400, 300) > 0, "transfert chaud->froid : ΔS_univers > 0 (spontané)")
# transfert froid->chaud = chaleur REÇUE par le froid négative (le froid cède la chaleur)
check(approx(E.entropie_univers(-100, 400, 300), -1.0 / 12.0), "transfert froid->chaud : ΔS_univers = −1/12 < 0")
check(E.entropie_univers(-100, 400, 300) < 0, "transfert froid->chaud : ΔS_univers < 0 (non spontané)")
check(E.entropie_univers(100, 350, 350) == 0.0, "T_chaud = T_froid : ΔS_univers = 0 (réversible)")
check(approx(E.entropie_univers(500, 600, 300), 500 / 300 - 500 / 600), "ΔS = 500/300 − 500/600 = 0.8333…")

# ── 3) ANCRES — spontane (critère du deuxième principe) ──
check(E.spontane(E.entropie_univers(100, 400, 300)) is True, "ΔS>0 -> spontané")
check(E.spontane(E.entropie_univers(-100, 400, 300)) is False, "ΔS<0 -> non spontané")
check(E.spontane(0.0) is False, "ΔS=0 (réversible) -> non spontané (strict)")
check(E.spontane(1e-12) is True, "ΔS>0 minuscule -> spontané")
check(E.spontane(-3.0) is False, "ΔS<0 -> non spontané")

# ── 4) COHÉRENCE — la chaleur ne remonte pas spontanément (Clausius) ──
# pour Q>0 : ΔS_univers ≥ 0 ssi T_chaud ≥ T_froid ; viser un réservoir plus chaud -> négatif
check(E.entropie_univers(100, 300, 400) < 0, "Q>0 vers un réservoir PLUS chaud -> ΔS<0 (impossible spontanément)")
check(E.spontane(E.entropie_univers(100, 300, 400)) is False, "remontée de chaleur -> non spontané")

# ── 5) SOUNDNESS — domaine : T ≤ 0 K -> ValueError (jamais un faux) ──
check(leve(E.variation_entropie, 100, 0), "T = 0 K -> ValueError")
check(leve(E.variation_entropie, 100, -50), "T < 0 K -> ValueError")
check(leve(E.entropie_univers, 100, 0, 300), "T_chaud = 0 -> ValueError")
check(leve(E.entropie_univers, 100, 400, -10), "T_froid < 0 -> ValueError")
check(leve(E.entropie_univers, 100, -400, -300), "deux T < 0 -> ValueError")

# ── 6) SOUNDNESS — types invalides (bool/str) -> ValueError ──
check(leve(E.variation_entropie, True, 200), "Q bool -> ValueError")
check(leve(E.variation_entropie, 100, True), "T bool -> ValueError")
check(leve(E.variation_entropie, "cent", 200), "Q str -> ValueError")
check(leve(E.entropie_univers, 100, "chaud", 300), "T_chaud str -> ValueError")
check(leve(E.spontane, "oui"), "spontane(str) -> ValueError")
check(leve(E.spontane, True), "spontane(bool) -> ValueError")

# ── 7) SOUNDNESS — valeurs non finies (NaN/inf) -> ValueError ──
check(leve(E.variation_entropie, float("inf"), 200), "Q = inf -> ValueError")
check(leve(E.variation_entropie, 100, float("inf")), "T = inf -> ValueError")
check(leve(E.variation_entropie, float("nan"), 200), "Q = NaN -> ValueError")
check(leve(E.entropie_univers, float("nan"), 400, 300), "Q = NaN (univers) -> ValueError")
check(leve(E.spontane, float("nan")), "spontane(NaN) -> ValueError")

# ── 8) DÉTERMINISME ──
check(E.variation_entropie(100, 200) == E.variation_entropie(100, 200), "déterminisme ΔS")
check(E.entropie_univers(100, 400, 300) == E.entropie_univers(100, 400, 300), "déterminisme ΔS_univers")

print(f"\n=== valide_entropie_thermo : {ok}/{ok+ko} ===")
import sys
sys.exit(0 if ko == 0 else 1)
