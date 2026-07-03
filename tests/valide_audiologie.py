"""
VALIDE audiologie.py — held-out ADVERSE.

Ancres = valeurs d'acoustique / d'audiologie CONNUES, posées À LA MAIN (non re-dérivées par le module) :
  • dB SPL : I0 -> 0 dB ; I=1 W/m² -> 120 dB (ordre du seuil de douleur) ; ×10 d'intensité -> +10 dB ;
  • addition : deux sources égales -> +3 dB exactement (10·log10(2)) ; commutativité ; loi d'échelle ;
  • classification OMS aux frontières exactes de la grille (24/25, 39/40, 54/55, 69/70, 89/90, 90, 91) ;
  • plage audible = fait (20, 20000) Hz.
+ SOUNDNESS (intensite ≤ 0, intensite_ref ≤ 0, seuil_db < 0, non numérique/booléen/non fini -> ValueError)
+ DÉTERMINISME.
"""
import math
import audiologie as A

ok = 0
ko = 0


def check(cond, label):
    global ok, ko
    if cond:
        ok += 1
    else:
        ko += 1
        print(f"  FAIL: {label}")


def _leve_v(fn, *a, **k) -> bool:
    """True ssi fn(*a, **k) lève ValueError (abstention), False sinon."""
    try:
        fn(*a, **k)
        return False
    except ValueError:
        return True
    except Exception:
        return False


TOL = 1e-9          # ancres exactes
RTOL = 1e-5         # ancres flottantes (arrondi 6 sig. figs)


def proche(got, exp, rel=RTOL):
    return abs(got - exp) <= abs(exp) * rel + 1e-9


# ── 1) NIVEAU dB SPL — L = 10·log10(I/I0), ancres connues ──
# I = I0 -> rapport 1 -> log10(1) = 0 -> 0 dB (seuil de référence)
check(A.niveau_db(1e-12) == 0.0, "niveau_db(I0) = 0 dB")
check(A.niveau_db(1e-12, 1e-12) == 0.0, "niveau_db(I0, I0) = 0 dB (ref explicite)")
# I = 1e-2 -> rapport 1e10 -> 10·log10(1e10) = 100 dB
check(proche(A.niveau_db(1e-2), 100.0), "niveau_db(1e-2) = 100 dB")
# I = 1 W/m² -> rapport 1e12 -> 120 dB (ordre du seuil de douleur 120-130 dB)
check(proche(A.niveau_db(1.0), 120.0), "niveau_db(1 W/m²) = 120 dB (~seuil de douleur)")
check(A.SEUIL_DOULEUR_DB[0] <= A.niveau_db(1.0) <= A.SEUIL_DOULEUR_DB[1], "120 dB dans la plage seuil de douleur")
# I = 1e-6 -> rapport 1e6 -> 60 dB (conversation)
check(proche(A.niveau_db(1e-6), 60.0), "niveau_db(1e-6) = 60 dB (conversation)")
# I = 1e-13 (sous la référence) -> 10·log10(0.1) = -10 dB
check(proche(A.niveau_db(1e-13), -10.0), "niveau_db(1e-13) = -10 dB (sous le seuil)")
# Loi d'échelle : ×10 d'intensité -> +10 dB (propriété, non circulaire)
check(proche(A.niveau_db(1e-3) - A.niveau_db(1e-4), 10.0), "×10 intensité -> +10 dB")
check(proche(A.niveau_db(2e-12) - A.niveau_db(1e-12), 10.0 * math.log10(2.0)), "×2 intensité -> +3.0103 dB")
# Référence non standard : niveau_db(I, I) = 0 quel que soit I>0
check(A.niveau_db(5.0, 5.0) == 0.0, "niveau_db(I, I) = 0 dB")

# ── 2) ADDITION DE NIVEAUX — L = 10·log10(10^(L1/10)+10^(L2/10)) ──
# Deux sources d'égal niveau -> +3 dB exactement : 10·log10(2) = 3.010299957
plus3 = 10.0 * math.log10(2.0)
check(proche(A.addition_db(60, 60), 60.0 + plus3), "addition 60+60 dB = 63.0103 (+3 dB)")
check(proche(A.addition_db(80, 80), 80.0 + plus3), "addition 80+80 dB = 83.0103 (+3 dB)")
check(proche(A.addition_db(0, 0), plus3), "addition 0+0 dB = 3.0103 dB")
# Propriété sources égales : addition(d,d) - d == 10·log10(2) pour tout d
for d in (10.0, 37.5, 95.0, -5.0):
    check(proche(A.addition_db(d, d) - d, plus3), f"addition({d},{d}) - {d} = +3.0103 dB")
# Commutativité
check(A.addition_db(60, 50) == A.addition_db(50, 60), "addition commutative")
# Une source dominante : 90 + 60 ≈ 90 dB (la faible contribue peu) ; 10·log10(10^9 + 10^6)
check(proche(A.addition_db(90, 60), 10.0 * math.log10(10.0 ** 9 + 10.0 ** 6)), "addition 90+60 ≈ 90.004 dB")
check(A.addition_db(90, 60) > 90.0 and A.addition_db(90, 60) < 90.01, "addition 90+60 entre 90 et 90.01 dB")
# 50 + 50 + ... cohérence : addition est monotone (ajouter une source augmente le total)
check(A.addition_db(70, 40) > 70.0, "addition: ajouter une source augmente le total")

# ── 3) CLASSIFICATION OMS — frontières EXACTES de la grille ──
check(A.classe_perte_auditive(0) == "normale", "0 dB -> normale")
check(A.classe_perte_auditive(24) == "normale", "24 dB -> normale")
check(A.classe_perte_auditive(24.999) == "normale", "24.999 dB -> normale")
check(A.classe_perte_auditive(25) == "légère", "25 dB -> légère (frontière)")
check(A.classe_perte_auditive(39) == "légère", "39 dB -> légère")
check(A.classe_perte_auditive(40) == "moyenne", "40 dB -> moyenne (frontière)")
check(A.classe_perte_auditive(54) == "moyenne", "54 dB -> moyenne")
check(A.classe_perte_auditive(55) == "modérément sévère", "55 dB -> modérément sévère (frontière)")
check(A.classe_perte_auditive(60) == "modérément sévère", "60 dB -> modérément sévère (CAS donné)")
check(A.classe_perte_auditive(69) == "modérément sévère", "69 dB -> modérément sévère")
check(A.classe_perte_auditive(70) == "sévère", "70 dB -> sévère (frontière)")
check(A.classe_perte_auditive(89) == "sévère", "89 dB -> sévère")
check(A.classe_perte_auditive(90) == "sévère", "90 dB -> sévère (90 inclus, grille 70-90)")
check(A.classe_perte_auditive(90.001) == "profonde", "90.001 dB -> profonde")
check(A.classe_perte_auditive(91) == "profonde", "91 dB -> profonde")
check(A.classe_perte_auditive(120) == "profonde", "120 dB -> profonde")
# Toutes les classes sont atteignables et distinctes
classes = {A.classe_perte_auditive(v) for v in (10, 30, 47, 62, 80, 100)}
check(classes == {"normale", "légère", "moyenne", "modérément sévère", "sévère", "profonde"},
      "6 classes OMS distinctes couvertes")

# ── 4) PLAGE AUDIBLE — fait ──
check(A.plage_audible_hz() == (20, 20000), "plage audible = (20, 20000) Hz")
check(A.plage_audible_hz()[0] == 20 and A.plage_audible_hz()[1] == 20000, "bornes 20 Hz / 20 kHz")

# ── 5) SOUNDNESS — entrée invalide -> ValueError (abstention, JAMAIS un faux) ──
check(_leve_v(A.niveau_db, 0.0), "niveau_db intensite=0 -> ValueError")
check(_leve_v(A.niveau_db, -1e-12), "niveau_db intensite<0 -> ValueError")
check(_leve_v(A.niveau_db, 1e-6, 0.0), "niveau_db intensite_ref=0 -> ValueError")
check(_leve_v(A.niveau_db, 1e-6, -1e-12), "niveau_db intensite_ref<0 -> ValueError")
check(_leve_v(A.classe_perte_auditive, -1.0), "classe seuil<0 -> ValueError")
check(_leve_v(A.classe_perte_auditive, -0.001), "classe seuil=-0.001 -> ValueError")
# Non numérique / booléen / non fini -> ValueError
check(_leve_v(A.niveau_db, True), "niveau_db booléen -> ValueError")
check(_leve_v(A.niveau_db, "1e-6"), "niveau_db str -> ValueError")
check(_leve_v(A.niveau_db, None), "niveau_db None -> ValueError")
check(_leve_v(A.niveau_db, float("nan")), "niveau_db NaN -> ValueError")
check(_leve_v(A.niveau_db, float("inf")), "niveau_db inf -> ValueError")
check(_leve_v(A.niveau_db, 1e-6, float("inf")), "niveau_db ref inf -> ValueError")
check(_leve_v(A.classe_perte_auditive, True), "classe booléen -> ValueError")
check(_leve_v(A.classe_perte_auditive, "60"), "classe str -> ValueError")
check(_leve_v(A.classe_perte_auditive, None), "classe None -> ValueError")
check(_leve_v(A.classe_perte_auditive, float("nan")), "classe NaN -> ValueError")
check(_leve_v(A.addition_db, True, 60), "addition booléen -> ValueError")
check(_leve_v(A.addition_db, 60, "60"), "addition str -> ValueError")
check(_leve_v(A.addition_db, float("inf"), 60), "addition inf -> ValueError")
check(_leve_v(A.addition_db, 60, float("nan")), "addition NaN -> ValueError")

# ── 6) DÉTERMINISME — fonctions pures, mêmes entrées -> mêmes sorties ──
check(A.niveau_db(1e-6) == A.niveau_db(1e-6), "niveau_db déterministe")
check([A.addition_db(60, 60) for _ in range(5)] == [A.addition_db(60, 60)] * 5, "addition 5 appels identiques")
check(A.classe_perte_auditive(60) == A.classe_perte_auditive(60), "classe déterministe")
check(A.plage_audible_hz() == A.plage_audible_hz(), "plage déterministe")

print(f"\n=== valide_audiologie : {ok}/{ok+ko} ===")
import sys
sys.exit(0 if ko == 0 else 1)
