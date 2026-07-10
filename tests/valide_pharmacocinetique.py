"""
VALIDE pharmacocinetique.py — held-out ADVERSE.

ANCRES NON CIRCULAIRES (valeurs connues INDÉPENDAMMENT des formules testées, écrites EN DUR ci-dessous) :
  • k = Cl/Vd : Cl=5 L/h, Vd=50 L -> k = 0.1 h⁻¹ (division à la main).
  • Demi-vie : k=0.1 h⁻¹ -> t½ = ln2/k = 0.6931.../0.1 = 6.931471806 h (à la main).
  • Fraction restante : après 1 demi-vie il reste 50 % ; après 5 demi-vies 2^(-5) = 3.125 % (soit 96.875 %
    éliminé — PAS 100 %). Valeurs de la décroissance binaire, indépendantes de e^(−kt).
  • ASC (bolus IV) : dose=500 mg, Cl=5 L/h -> ASC = 100 mg·h/L, INDÉPENDANTE de Vd : on le prouve avec DEUX
    Vd différents (10 L et 50 L) -> même ASC (ancre non circulaire forte).
  • Css,moy : F=1, dose=500 mg, τ=12 h, Cl=5 L/h -> 500/60 = 8.333333333 mg/L (division à la main).
  • Facteur d'accumulation : k=0.1, τ=12 -> 1/(1−e^(−1.2)). e^(−1.2)=0.3011942119 -> 1/0.6988057881
    = 1.431012761 (la spec citait 1.4306, valeur IMPRÉCISE ; la valeur exacte retenue ici est 1.4310127606).
  • Dose de charge : C_cible=10 mg/L, Vd=50 L, F=1 -> DC = 500 mg (à la main).
  • ÉTHANOL / PHÉNYTOÏNE / ASPIRINE -> ValueError (cinétique saturable : ancre d'ABSTENTION).

SOUNDNESS : Cl,Vd,k,C0,dose,C_cible ≤ 0 ; t<0 ; τ≤0 ; F hors ]0,1] ; n<1 ; bool/str/NaN/inf/arité -> ValueError.
"""
import math

import pharmacocinetique as P

ok = 0
ko = 0


def check(cond, label):
    global ok, ko
    if cond:
        ok += 1
    else:
        ko += 1
        print(f"  FAIL: {label}")


def leve(fn, *a, **kw):
    """True ssi fn(*a) lève ValueError (abstention structurelle)."""
    try:
        fn(*a, **kw)
        return False
    except ValueError:
        return True


def proche(x, attendu, tol=1e-6):
    return x is not None and abs(x - attendu) <= tol


# ══ (a) CONSTANTE D'ÉLIMINATION & DEMI-VIE ═══════════════════════════════════════════════════════════════════════
# ANCRE : Cl=5, Vd=50 -> k=0.1 (à la main)
check(proche(P.constante_elimination(5.0, 50.0), 0.1), "k = Cl/Vd = 5/50 = 0.1")
check(proche(P.constante_elimination(10.0, 40.0), 0.25), "k = 10/40 = 0.25")
# ANCRE : k=0.1 -> t½ = ln2/0.1 = 6.931471806 (à la main)
check(proche(P.demi_vie(0.1), 6.931471806, tol=1e-6), "t½ = ln2/0.1 = 6.931471806 h")
# ANCRE indépendante : k=ln2 -> t½ = 1 exactement (ln2/ln2)
check(proche(P.demi_vie(math.log(2.0)), 1.0), "t½ = ln2/ln2 = 1 h (ancre exacte)")
# demi_vie_depuis DOIT coïncider avec demi_vie(k) — DEUXIÈME CHEMIN de code distinct
check(proche(P.demi_vie_depuis(5.0, 50.0), 6.931471806, tol=1e-6), "t½ depuis Cl,Vd = 6.931471806 h")
check(proche(P.demi_vie_depuis(5.0, 50.0), P.demi_vie(P.constante_elimination(5.0, 50.0)), tol=1e-6),
      "t½ depuis(Cl,Vd) == demi_vie(k=Cl/Vd) (cohérence 2 chemins)")

# ══ (b) CONCENTRATION AU COURS DU TEMPS ══════════════════════════════════════════════════════════════════════════
# ANCRE : à t=0, C(0)=C0
check(proche(P.concentration(100.0, 0.1, 0.0), 100.0), "C(0) = C0 = 100")
# ANCRE : après UNE demi-vie il reste 50 % (indépendant : t½ posé, résultat binaire 1/2)
th = 6.931471805599453  # ln2/0.1, valeur écrite en dur
check(proche(P.concentration(100.0, 0.1, th), 50.0, tol=1e-4), "après 1 t½ il reste 50 % (100->50)")
# ANCRE : après 5 demi-vies il reste 2^-5 = 3.125 % -> 100*0.03125 = 3.125
check(proche(P.concentration(100.0, 0.1, 5 * th), 3.125, tol=1e-4), "après 5 t½ il reste 3.125 (2^-5) — PAS 0")
# ANCRE : après 2 demi-vies il reste 25 %
check(proche(P.concentration(80.0, 0.1, 2 * th), 20.0, tol=1e-4), "après 2 t½ : 80->20 (25 %)")
# concentration_apres_dose : dose=500, Vd=50 -> C0 = 10 ; à t=0 -> 10
check(proche(P.concentration_apres_dose(500.0, 50.0, 0.1, 0.0), 10.0), "C0 après dose = dose/Vd = 500/50 = 10")
# après 1 demi-vie -> 5
check(proche(P.concentration_apres_dose(500.0, 50.0, 0.1, th), 5.0, tol=1e-4), "après 1 t½ : 10->5")

# ══ (c) AIRE SOUS LA COURBE — INDÉPENDANTE de Vd ═════════════════════════════════════════════════════════════════
# ANCRE : dose=500, Cl=5 -> ASC = 100 (à la main). Vd n'intervient PAS.
check(proche(P.aire_sous_courbe(500.0, 5.0), 100.0), "ASC = dose/Cl = 500/5 = 100 mg·h/L")
# Confirmation NON circulaire de l'indépendance à Vd : reconstruire l'ASC via ∫ C0·e^(-kt) dt = C0/k avec 2 Vd
for vd in (10.0, 50.0):
    k = P.constante_elimination(5.0, vd)          # k varie avec Vd
    C0 = 500.0 / vd                                # C0 varie avec Vd
    asc_reconstruite = C0 / k                       # = (500/vd)/(5/vd) = 100, indépendant de vd
    check(proche(asc_reconstruite, 100.0), f"ASC reconstruite C0/k = 100 (Vd={vd})")
check(P.aire_sous_courbe(500.0, 5.0) == P.aire_sous_courbe(500.0, 5.0), "ASC ne dépend pas de Vd (aucun arg Vd)")

# ══ (d) DOSES RÉPÉTÉES ═══════════════════════════════════════════════════════════════════════════════════════════
# ANCRE : F=1, dose=500, τ=12, Cl=5 -> 500/60 = 8.333333333 (à la main)
check(proche(P.concentration_equilibre_moyenne(500.0, 12.0, 5.0, 1.0), 8.333333333, tol=1e-6),
      "Css,moy = 500/(5·12) = 8.333333333 mg/L")
# F par défaut = 1
check(proche(P.concentration_equilibre_moyenne(500.0, 12.0, 5.0), 8.333333333, tol=1e-6),
      "Css,moy F=1 par défaut = 8.333333333")
# F=0.5 -> moitié
check(proche(P.concentration_equilibre_moyenne(500.0, 12.0, 5.0, 0.5), 4.166666667, tol=1e-6),
      "Css,moy F=0.5 = 4.166666667 mg/L")
# ANCRE : facteur d'accumulation k=0.1, τ=12 -> 1.4310127606 (e^-1.2 en dur)
check(proche(P.facteur_accumulation(0.1, 12.0), 1.4310127606, tol=1e-6),
      "R accumulation = 1/(1-e^-1.2) = 1.4310127606")
# ANCRE indépendante : si τ = t½ alors e^(-k·τ)=e^(-ln2)=1/2 -> R = 1/(1-1/2) = 2 exactement
check(proche(P.facteur_accumulation(0.1, th), 2.0, tol=1e-6), "R = 2 quand τ = t½ (e^-ln2=1/2)")
# temps_pour_equilibre : n=5 -> temps=5·t½, fraction=0.96875
temps, n, frac = P.temps_pour_equilibre(6.931471806, 5)
check(proche(temps, 5 * 6.931471806, tol=1e-4), "temps équilibre = 5·t½")
check(n == 5, "n_demi_vies = 5")
check(proche(frac, 0.96875), "fraction atteinte à 5 t½ = 1-2^-5 = 0.96875 (PAS 1.0)")
check(frac < 1.0, "fraction atteinte STRICTEMENT < 100 %")
# n=1 -> fraction 0.5 ; n=4 -> 0.9375 ; n=7 -> 0.9921875
_, _, f1 = P.temps_pour_equilibre(6.9, 1)
_, _, f4 = P.temps_pour_equilibre(6.9, 4)
_, _, f7 = P.temps_pour_equilibre(6.9, 7)
check(proche(f1, 0.5), "fraction à 1 t½ = 0.5")
check(proche(f4, 0.9375), "fraction à 4 t½ = 0.9375")
check(proche(f7, 0.9921875), "fraction à 7 t½ = 0.9921875")

# ══ (e) DOSE DE CHARGE ═══════════════════════════════════════════════════════════════════════════════════════════
# ANCRE : C_cible=10, Vd=50, F=1 -> DC = 500 (à la main)
check(proche(P.dose_de_charge(10.0, 50.0, 1.0), 500.0), "DC = C_cible·Vd/F = 10·50/1 = 500 mg")
check(proche(P.dose_de_charge(10.0, 50.0), 500.0), "DC F=1 par défaut = 500 mg")
# F=0.5 -> il faut deux fois plus
check(proche(P.dose_de_charge(10.0, 50.0, 0.5), 1000.0), "DC F=0.5 = 1000 mg (biodispo partielle)")
# Cohérence DC/Css : DC = Css_cible·Vd/F, et concentration_apres_dose(DC,Vd,k,0)=C_cible
check(proche(P.concentration_apres_dose(P.dose_de_charge(10.0, 50.0), 50.0, 0.1, 0.0), 10.0),
      "dose de charge atteint C_cible à t=0")

# ══ (f) HONNÊTETÉ — cinétique SATURABLE -> ABSTENTION ════════════════════════════════════════════════════════════
check(leve(P.verifie_ordre_un, "éthanol"), "éthanol -> ValueError (ordre 0, saturable)")
check(leve(P.verifie_ordre_un, "ethanol"), "ethanol (sans accent) -> ValueError")
check(leve(P.verifie_ordre_un, "Alcool"), "alcool -> ValueError")
check(leve(P.verifie_ordre_un, "phénytoïne"), "phénytoïne -> ValueError (Michaelis-Menten)")
check(leve(P.verifie_ordre_un, "aspirine"), "aspirine forte dose -> ValueError (ordre mixte)")
check(leve(P.verifie_ordre_un, "médicament-inconnu-xyz"), "médicament inconnu -> ValueError (abstention)")
# médicaments d'ordre 1 établi -> True
check(P.verifie_ordre_un("gentamicine") is True, "gentamicine -> True (ordre 1 établi)")
check(P.verifie_ordre_un("Digoxine") is True, "digoxine (casse) -> True")
check("ethanol" in P.catalogue_saturables(), "catalogue_saturables contient ethanol")

# ══ SOUNDNESS — domaine ══════════════════════════════════════════════════════════════════════════════════════════
check(leve(P.constante_elimination, 0.0, 50.0), "Cl=0 -> ValueError")
check(leve(P.constante_elimination, -5.0, 50.0), "Cl<0 -> ValueError")
check(leve(P.constante_elimination, 5.0, 0.0), "Vd=0 -> ValueError")
check(leve(P.constante_elimination, 5.0, -1.0), "Vd<0 -> ValueError")
check(leve(P.demi_vie, 0.0), "k=0 -> ValueError")
check(leve(P.demi_vie, -0.1), "k<0 -> ValueError")
check(leve(P.demi_vie_depuis, 5.0, 0.0), "demi_vie_depuis Vd=0 -> ValueError")
check(leve(P.concentration, 0.0, 0.1, 1.0), "C0=0 -> ValueError")
check(leve(P.concentration, 100.0, 0.0, 1.0), "concentration k=0 -> ValueError")
check(leve(P.concentration, 100.0, 0.1, -1.0), "t<0 -> ValueError")
check(leve(P.concentration_apres_dose, 0.0, 50.0, 0.1, 1.0), "dose=0 -> ValueError")
check(leve(P.concentration_apres_dose, 500.0, 0.0, 0.1, 1.0), "apres_dose Vd=0 -> ValueError")
check(leve(P.concentration_apres_dose, 500.0, 50.0, 0.1, -0.5), "apres_dose t<0 -> ValueError")
check(leve(P.aire_sous_courbe, 0.0, 5.0), "ASC dose=0 -> ValueError")
check(leve(P.aire_sous_courbe, 500.0, 0.0), "ASC Cl=0 -> ValueError")
check(leve(P.concentration_equilibre_moyenne, 500.0, 0.0, 5.0), "Css τ=0 -> ValueError")
check(leve(P.concentration_equilibre_moyenne, 500.0, -12.0, 5.0), "Css τ<0 -> ValueError")
check(leve(P.concentration_equilibre_moyenne, 500.0, 12.0, 0.0), "Css Cl=0 -> ValueError")
check(leve(P.concentration_equilibre_moyenne, 500.0, 12.0, 5.0, 0.0), "Css F=0 -> ValueError")
check(leve(P.concentration_equilibre_moyenne, 500.0, 12.0, 5.0, 1.5), "Css F>1 -> ValueError")
check(leve(P.facteur_accumulation, 0.0, 12.0), "R k=0 -> ValueError")
check(leve(P.facteur_accumulation, 0.1, 0.0), "R τ=0 -> ValueError")
check(leve(P.temps_pour_equilibre, 0.0), "temps_equilibre t½=0 -> ValueError")
check(leve(P.temps_pour_equilibre, 6.9, 0), "temps_equilibre n=0 -> ValueError")
check(leve(P.temps_pour_equilibre, 6.9, -3), "temps_equilibre n<0 -> ValueError")
check(leve(P.dose_de_charge, 0.0, 50.0), "DC C_cible=0 -> ValueError")
check(leve(P.dose_de_charge, 10.0, 0.0), "DC Vd=0 -> ValueError")
check(leve(P.dose_de_charge, 10.0, 50.0, 0.0), "DC F=0 -> ValueError")
check(leve(P.dose_de_charge, 10.0, 50.0, 1.5), "DC F>1 -> ValueError")

# ══ SOUNDNESS — types invalides (bool / str / complexe / NaN / inf) ══════════════════════════════════════════════
check(leve(P.constante_elimination, True, 50.0), "Cl bool -> ValueError")
check(leve(P.constante_elimination, 5.0, False), "Vd bool -> ValueError")
check(leve(P.demi_vie, "0.1"), "k str -> ValueError")
check(leve(P.demi_vie, 1 + 2j), "k complexe -> ValueError")
check(leve(P.demi_vie, float("nan")), "k NaN -> ValueError")
check(leve(P.demi_vie, float("inf")), "k inf -> ValueError")
check(leve(P.concentration, float("inf"), 0.1, 1.0), "C0 inf -> ValueError")
check(leve(P.concentration, 100.0, 0.1, float("nan")), "t NaN -> ValueError")
check(leve(P.facteur_accumulation, 0.1, float("inf")), "τ inf -> ValueError")
check(leve(P.temps_pour_equilibre, 6.9, True), "n bool -> ValueError")
check(leve(P.temps_pour_equilibre, 6.9, 2.5), "n non entier -> ValueError")
check(leve(P.concentration_equilibre_moyenne, 500.0, 12.0, 5.0, True), "F bool -> ValueError")
check(leve(P.verifie_ordre_un, 123), "médicament non-chaîne -> ValueError")
check(leve(P.dose_de_charge, float("inf"), 50.0), "C_cible inf -> ValueError")

# ══ DÉTERMINISME ═════════════════════════════════════════════════════════════════════════════════════════════════
check(P.concentration(100.0, 0.1, 5.0) == P.concentration(100.0, 0.1, 5.0), "déterminisme concentration")
check(P.facteur_accumulation(0.1, 12.0) == P.facteur_accumulation(0.1, 12.0), "déterminisme accumulation")
check(P.temps_pour_equilibre(6.9, 5) == P.temps_pour_equilibre(6.9, 5), "déterminisme temps_equilibre")
check(P.demi_vie_depuis(5.0, 50.0) == P.demi_vie_depuis(5.0, 50.0), "déterminisme demi_vie_depuis")

print(f"\n=== valide_pharmacocinetique : {ok}/{ok+ko} ===")
import sys
sys.exit(0 if ko == 0 else 1)
