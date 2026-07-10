"""
VALIDE conductivite_materiaux.py — held-out ADVERSE.

ANCRES EXTERNES NON CIRCULAIRES (valeurs connues INDÉPENDAMMENT des formules testées) :
  • ORDRE physique connu : l'argent est le meilleur conducteur thermique ET électrique des métaux
    courants (k=429 > cuivre 401 ; ρ=1.59e-8 < cuivre 1.68e-8) ; l'air est le pire conducteur
    thermique du catalogue (c'est pour ça que les isolants emprisonnent de l'air).
  • FOURIER à la main : k=401 (cuivre), A=0.01 m², ΔT=100 K, L=0.5 m
        -> Φ = 401 × 0.01 × 100 / 0.5 = 401 / 0.5 = 802 W          (calcul posé ici, pas par le code).
  • POUILLET à la main : fil de cuivre L=100 m, A=1e-6 m² (1 mm²)
        -> R = 1.68e-8 × 100 / 1e-6 = 1.68e-6 / 1e-6 = 1.68 Ω      (à la main).
  • CONDUCTIVITÉ du cuivre : σ = 1/1.68e-8 = 5.952380952e7 S/m — la valeur de référence connue est
    ≈ 5.96e7 S/m (IACS ~5.8e7 pour le cuivre recuit) : on exige σ à ±1% de 5.96e7 (table indépendante).
  • WIEDEMANN-FRANZ (ancre FORTE) : pour le cuivre à 293 K, k/(σ·T) = 401×1.68e-8/293 doit tomber à
    ±15% du nombre de Lorenz théorique 2.44e-8 W·Ω·K⁻². Les DEUX tables (k thermique, ρ électrique)
    viennent de mesures INDÉPENDANTES ; c'est une loi physique qui les contraint l'une par l'autre.
    Vérifié aussi sur argent, or, aluminium, fer (métaux purs).
  • SECOND CHEMIN : Φ = ΔT / R_th (deux fonctions distinctes doivent se recouper).

SOUNDNESS : matériau hors catalogue, non-métal pour Lorenz, ρ non tabulée (eau/bois/air), T hors
plage, k/A/L/ΔT/ρ/T ≤ 0, bool/str/NaN/inf -> ValueError. DÉTERMINISME : double appel identique.
"""
import math

import conductivite_materiaux as C

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
    """True ssi fn(*a) lève ValueError (abstention structurelle)."""
    try:
        fn(*a)
        return False
    except ValueError:
        return True


def proche(x, attendu, rel=1e-9):
    return x is not None and abs(x - attendu) <= rel * abs(attendu) + 1e-30


# ── 1) ANCRE D'ORDRE : l'argent, meilleur conducteur thermique ET électrique des métaux courants ──
check(C.conductivite_thermique("argent") > C.conductivite_thermique("cuivre"),
      "k argent (429) > k cuivre (401)")
check(C.conductivite_thermique("cuivre") > C.conductivite_thermique("or"),
      "k cuivre (401) > k or (317)")
check(C.conductivite_thermique("or") > C.conductivite_thermique("aluminium"),
      "k or (317) > k aluminium (237)")
check(C.conductivite_thermique("aluminium") > C.conductivite_thermique("fer"),
      "k aluminium (237) > k fer (80.4)")
check(C.resistivite_electrique("argent") < C.resistivite_electrique("cuivre"),
      "ρ argent (1.59e-8) < ρ cuivre (1.68e-8)")
check(C.resistivite_electrique("cuivre") < C.resistivite_electrique("or"),
      "ρ cuivre < ρ or (2.44e-8)")
check(C.resistivite_electrique("or") < C.resistivite_electrique("aluminium"),
      "ρ or < ρ aluminium (2.65e-8)")
# L'air est le pire conducteur thermique du catalogue (raison d'être des isolants à air emprisonné).
check(min(C.conductivite_thermique(m) for m in C.materiaux()) == C.conductivite_thermique("air"),
      "l'air (0.026) est le minimum thermique du catalogue")
# Les isolants électriques du catalogue le sont vraiment (≥ 1e10 Ω·m, ~20 ordres au-dessus du cuivre).
check(C.resistivite_electrique("verre") >= 1e10, "verre isolant : ρ ≥ 1e10 Ω·m")
check(C.resistivite_electrique("polystyrene") > C.resistivite_electrique("verre"),
      "polystyrène (1e16) encore plus isolant que le verre (1e12)")

# ── 2) FOURIER — calculs posés À LA MAIN (pas par le code) ──
# 401 × 0.01 × 100 / 0.5 : 401×0.01=4.01 ; ×100=401 ; /0.5=802 W.
check(proche(C.flux_thermique(401.0, 0.01, 100.0, 0.5), 802.0), "Fourier cuivre : Φ = 802 W (à la main)")
# Vitre : k=1.0, A=2 m², ΔT=15 K, L=6 mm -> 1×2×15/0.006 = 30/0.006 = 5000 W.
check(proche(C.flux_thermique(1.0, 2.0, 15.0, 0.006), 5000.0), "Fourier vitre : Φ = 5000 W (à la main)")
# R_th = 0.5/(401×0.01) = 0.5/4.01 = 0.1246882793... K/W (division posée à la main).
check(proche(C.resistance_thermique(0.5, 401.0, 0.01), 0.1246882793, rel=1e-9),
      "R_th mur cuivre = 0.1246882793 K/W (à la main)")
# SECOND CHEMIN : Φ = ΔT / R_th (deux fonctions distinctes, même physique).
check(proche(C.flux_thermique(401.0, 0.01, 100.0, 0.5),
             100.0 / C.resistance_thermique(0.5, 401.0, 0.01), rel=1e-8),
      "cohérence Φ = ΔT / R_th (second chemin)")
check(proche(C.flux_thermique(0.15, 1.0, 20.0, 0.05),
             20.0 / C.resistance_thermique(0.05, 0.15, 1.0), rel=1e-8),
      "cohérence Φ = ΔT / R_th (bois, second chemin)")

# ── 3) POUILLET — calculs posés À LA MAIN ──
# Fil de cuivre 100 m / 1 mm² : R = 1.68e-8 × 100 / 1e-6 = 1.68e-6/1e-6 = 1.68 Ω.
check(proche(C.resistance_electrique(1.68e-8, 100.0, 1e-6), 1.68), "fil cuivre 100 m/1 mm² : R = 1.68 Ω (à la main)")
# Fil de fer 10 m / 1 mm² : R = 9.71e-8 × 10 / 1e-6 = 0.971 Ω.
check(proche(C.resistance_electrique(9.71e-8, 10.0, 1e-6), 0.971), "fil fer 10 m/1 mm² : R = 0.971 Ω (à la main)")
# σ cuivre = 1/1.68e-8 = 5.952380952e7 S/m (division à la main) — table indépendante : ≈5.96e7 S/m.
check(proche(C.conductivite(1.68e-8), 5.952380952e7, rel=1e-9), "σ cuivre = 5.952380952e7 S/m (à la main)")
check(abs(C.conductivite(1.68e-8) - 5.96e7) <= 0.01 * 5.96e7,
      "σ cuivre à ±1% de la valeur de table 5.96e7 S/m (source indépendante)")

# ── 4) WIEDEMANN-FRANZ — ancre non circulaire FORTE (deux tables indépendantes) ──
L0 = 2.44e-8  # nombre de Lorenz théorique, W·Ω·K⁻² (Sommerfeld)
# Cuivre à 293 K : 401×1.68e-8/293 = 6.7368e-6/293 = 2.29925e-8 (posé à la main).
lz_cu = C.nombre_lorenz("cuivre", 293.0)
check(proche(lz_cu, 2.299249147e-8, rel=1e-6), "Lorenz cuivre 293 K = 2.299249e-8 (à la main)")
check(abs(lz_cu - L0) <= 0.15 * L0, "Wiedemann-Franz : cuivre à ±15% de L0=2.44e-8")
check(abs(C.nombre_lorenz("argent", 293.0) - L0) <= 0.15 * L0, "Wiedemann-Franz : argent à ±15% de L0")
check(abs(C.nombre_lorenz("or", 293.0) - L0) <= 0.15 * L0, "Wiedemann-Franz : or à ±15% de L0")
check(abs(C.nombre_lorenz("aluminium", 293.0) - L0) <= 0.15 * L0, "Wiedemann-Franz : aluminium à ±15% de L0")
check(abs(C.nombre_lorenz("fer", 293.0) - L0) <= 0.15 * L0, "Wiedemann-Franz : fer à ±15% de L0")
check(proche(C.NOMBRE_LORENZ_THEORIQUE, 2.44e-8), "constante L0 = 2.44e-8 exposée")

# ── 5) GARDE Wiedemann-Franz : non-métaux REFUSÉS, T hors plage REFUSÉ ──
check(leve(C.nombre_lorenz, "verre", 293.0), "Lorenz('verre') -> ValueError (non-métal)")
check(leve(C.nombre_lorenz, "bois", 293.0), "Lorenz('bois') -> ValueError (non-métal)")
check(leve(C.nombre_lorenz, "air", 293.0), "Lorenz('air') -> ValueError (non-métal)")
check(leve(C.nombre_lorenz, "eau", 293.0), "Lorenz('eau') -> ValueError (non-métal)")
check(leve(C.nombre_lorenz, "polystyrene", 293.0), "Lorenz('polystyrene') -> ValueError (non-métal)")
check(leve(C.nombre_lorenz, "cuivre", 100.0), "Lorenz T=100 K hors plage catalogue -> ValueError")
check(leve(C.nombre_lorenz, "cuivre", 400.0), "Lorenz T=400 K hors plage catalogue -> ValueError")
check(leve(C.nombre_lorenz, "cuivre", 0.0), "Lorenz T=0 -> ValueError")
check(leve(C.nombre_lorenz, "cuivre", -293.0), "Lorenz T<0 -> ValueError")

# ── 6) ABSTENTION catalogue : hors catalogue et ρ non tabulée ──
check(leve(C.conductivite_thermique, "plutonium"), "matériau hors catalogue -> ValueError")
check(leve(C.resistivite_electrique, "beton"), "ρ hors catalogue -> ValueError")
check(leve(C.nombre_lorenz, "titane", 293.0), "Lorenz hors catalogue -> ValueError")
check(leve(C.resistivite_electrique, "eau"), "ρ(eau) non tabulée -> ValueError (abstention)")
check(leve(C.resistivite_electrique, "bois"), "ρ(bois) non tabulée -> ValueError (abstention)")
check(leve(C.resistivite_electrique, "air"), "ρ(air) non tabulée -> ValueError (abstention)")
check(leve(C.conductivite_thermique, 42), "matériau non-str -> ValueError")
check(leve(C.conductivite_thermique, None), "matériau None -> ValueError")
# Normalisation tolérée (casse, accent) : mêmes valeurs, pas de doublon de vérité.
check(C.conductivite_thermique("Cuivre") == C.conductivite_thermique("cuivre"), "casse normalisée")
check(C.conductivite_thermique("polystyrène") == C.conductivite_thermique("polystyrene"), "accent normalisé")

# ── 7) SOUNDNESS — flux_thermique / resistance_thermique ──
check(leve(C.flux_thermique, 0.0, 0.01, 100.0, 0.5), "k=0 -> ValueError")
check(leve(C.flux_thermique, -401.0, 0.01, 100.0, 0.5), "k<0 -> ValueError")
check(leve(C.flux_thermique, 401.0, 0.0, 100.0, 0.5), "A=0 -> ValueError")
check(leve(C.flux_thermique, 401.0, 0.01, 0.0, 0.5), "ΔT=0 -> ValueError")
check(leve(C.flux_thermique, 401.0, 0.01, -5.0, 0.5), "ΔT<0 -> ValueError")
check(leve(C.flux_thermique, 401.0, 0.01, 100.0, 0.0), "L=0 -> ValueError")
check(leve(C.flux_thermique, 401.0, 0.01, 100.0, -0.5), "L<0 -> ValueError")
check(leve(C.resistance_thermique, 0.0, 401.0, 0.01), "R_th L=0 -> ValueError")
check(leve(C.resistance_thermique, 0.5, 0.0, 0.01), "R_th k=0 -> ValueError")
check(leve(C.resistance_thermique, 0.5, 401.0, -0.01), "R_th A<0 -> ValueError")

# ── 8) SOUNDNESS — resistance_electrique / conductivite ──
check(leve(C.resistance_electrique, 0.0, 100.0, 1e-6), "ρ=0 -> ValueError")
check(leve(C.resistance_electrique, -1.68e-8, 100.0, 1e-6), "ρ<0 -> ValueError")
check(leve(C.resistance_electrique, 1.68e-8, 0.0, 1e-6), "L=0 -> ValueError")
check(leve(C.resistance_electrique, 1.68e-8, 100.0, 0.0), "A=0 -> ValueError")
check(leve(C.conductivite, 0.0), "σ(ρ=0) -> ValueError")
check(leve(C.conductivite, -1.0), "σ(ρ<0) -> ValueError")

# ── 9) SOUNDNESS — types invalides (bool / str / NaN / inf) ──
check(leve(C.flux_thermique, True, 0.01, 100.0, 0.5), "k bool -> ValueError")
check(leve(C.flux_thermique, "401", 0.01, 100.0, 0.5), "k str -> ValueError")
check(leve(C.flux_thermique, float("nan"), 0.01, 100.0, 0.5), "k NaN -> ValueError")
check(leve(C.flux_thermique, float("inf"), 0.01, 100.0, 0.5), "k inf -> ValueError")
check(leve(C.flux_thermique, 401.0, 0.01, float("-inf"), 0.5), "ΔT -inf -> ValueError")
check(leve(C.resistance_electrique, 1.68e-8, float("nan"), 1e-6), "L NaN -> ValueError")
check(leve(C.resistance_electrique, 1.68e-8, True, 1e-6), "L bool -> ValueError")
check(leve(C.conductivite, float("inf")), "σ(inf) -> ValueError")
check(leve(C.conductivite, True), "σ(bool) -> ValueError")
check(leve(C.conductivite, "1.68e-8"), "σ(str) -> ValueError")
check(leve(C.nombre_lorenz, "cuivre", True), "Lorenz T bool -> ValueError")
check(leve(C.nombre_lorenz, "cuivre", float("nan")), "Lorenz T NaN -> ValueError")
check(leve(C.nombre_lorenz, "cuivre", float("inf")), "Lorenz T inf -> ValueError")

# ── 10) DÉTERMINISME (double appel identique) ──
check(C.flux_thermique(401.0, 0.01, 100.0, 0.5) == C.flux_thermique(401.0, 0.01, 100.0, 0.5),
      "déterminisme flux_thermique")
check(C.resistance_electrique(1.68e-8, 100.0, 1e-6) == C.resistance_electrique(1.68e-8, 100.0, 1e-6),
      "déterminisme resistance_electrique")
check(C.nombre_lorenz("cuivre", 293.0) == C.nombre_lorenz("cuivre", 293.0), "déterminisme nombre_lorenz")
check(C.materiaux() == C.materiaux(), "déterminisme materiaux()")
check(len(C.materiaux()) == 11, "catalogue thermique : 11 matériaux")

print(f"\n=== valide_conductivite_materiaux : {ok}/{ok+ko} ===")
import sys; sys.exit(0 if ko == 0 else 1)
