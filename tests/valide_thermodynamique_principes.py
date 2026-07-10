"""VALIDE thermodynamique_principes.py — held-out ADVERSE (1er + 2nd principes).

ANCRES EXTERNES NON CIRCULAIRES (valeurs connues/calculées À LA MAIN, JAMAIS via la fonction testée) :
  • 1er principe : Q=100 J, W=30 J (convention thermo, W fourni) -> ΔU = 100 − 30 = 70 J (à la main).
  • Détente isotherme réversible d'1 mol de gaz parfait à 300 K de V à 2V :
        W = 1 × 8.314 × 300 × ln2 = 1728.85 J (calcul à la main) ;
        isotherme + gaz parfait -> ΔU = 0 donc Q = W ;
        ΔS_gaz = 8.314 × ln2 = 5.763 J/K (à la main).
  • ÉCHAUFFEMENT (le manque comblé) : 1 kg d'eau (c=4185) de 300 K à 400 K ->
        ΔS = 4185 × ln(400/300) = 1203.9 J/K (à la main).
  • ANCRE PIÈGE (°C) : la MÊME formule avec 27 → 127 « °C » donnerait 4185×ln(127/27) ≈ 6486 J/K,
        un FAUX d'un facteur ~5 : le module doit REFUSER les °C (T < 100 K -> ValueError).
  • Carnot : Tf=300, Tc=600 -> rendement max = 1 − 300/600 = 0.5 ; un moteur annoncé à 0.6 -> ValueError.
  • Travail isobare : P=1e5 Pa, V 1e-3 → 3e-3 m³ -> W = 1e5 × 2e-3 = 200 J (à la main).
  • Travail adiabatique : n=1, Cv=1.5R=12.471, 300 → 400 K -> W = −12.471 × 100 = −1247.1 J (à la main).
  • Gaz parfait général : n=1, Cv=12.471, 300 → 600 K, V → 2V ->
        ΔS = 1.5R·ln2 + R·ln2 = 2.5 × 8.314 × ln2 = 14.407 J/K (à la main).
  • SECOND CHEMIN indépendant : ΔS d'une détente isotherme = Q/T (module RÉSERVÉ entropie_thermo), Q=W.

SOUNDNESS : T ≤ 0 K, °C ambigus (<100 K), n/m/c/Cv/P/V ≤ 0, Tf ≥ Tc, types (bool/str/NaN/inf) -> ValueError.
DÉTERMINISME : même entrée -> même sortie.
"""
import math

import entropie_thermo
import thermodynamique_principes as T

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


def proche(x, attendu, tol=1e-9):
    return x is not None and abs(x - attendu) <= tol


# ── 1) PREMIER PRINCIPE : ΔU = Q − W (convention thermodynamique) ──
check(proche(T.variation_energie_interne(100, 30), 70.0), "ΔU(Q=100,W=30) = 70 J (à la main)")
check(proche(T.variation_energie_interne(50, 80), -30.0), "ΔU(Q=50,W=80) = −30 J")
check(proche(T.variation_energie_interne(0, 0), 0.0), "ΔU(0,0) = 0")
# Convention thermo vs chimiste : W fourni positif en détente. Compression W=−30 -> ΔU = 100−(−30) = 130.
check(proche(T.variation_energie_interne(100, -30), 130.0), "convention thermo : ΔU(100,−30) = 130 (≠ chimiste 70)")

# ── 2) TRAVAIL ISOTHERME + cohérence 1er principe (ΔU=0 -> Q=W) ──
W_iso = T.travail_isotherme_gaz_parfait(1, 300, 1.0, 2.0)
check(proche(W_iso, 1728.85, tol=1e-2), "W isotherme 1 mol 300K V->2V = 1728.85 J (à la main)")
# isotherme gaz parfait : ΔU = 0, donc Q = W ; on vérifie que ΔU(Q=W, W) = 0.
check(proche(T.variation_energie_interne(W_iso, W_iso), 0.0), "isotherme : ΔU = 0 quand Q = W")
check(T.travail_isotherme_gaz_parfait(1, 300, 2.0, 2.0) == 0.0, "V1==V2 -> W isotherme = 0.0 exact")
# compression (V2 < V1) -> W fourni négatif
check(T.travail_isotherme_gaz_parfait(1, 300, 2.0, 1.0) < 0, "compression -> W isotherme < 0")

# ── 3) TRAVAIL ISOBARE : W = P(V2−V1) ──
check(proche(T.travail_isobare(1e5, 1e-3, 3e-3), 200.0, tol=1e-6), "W isobare = 1e5×2e-3 = 200 J (à la main)")
check(T.travail_isobare(1e5, 2e-3, 2e-3) == 0.0, "V1==V2 -> W isobare = 0.0 exact")
check(proche(T.travail_isobare(1e5, 3e-3, 1e-3), -200.0, tol=1e-6), "compression isobare -> −200 J")

# ── 4) TRAVAIL ADIABATIQUE : W = −n·Cv·(T2−T1) (Cv=1.5R monoatomique) ──
check(proche(T.travail_adiabatique(1, 12.471, 300, 400), -1247.1, tol=1e-2),
      "W adiabatique = −12.471×100 = −1247.1 J (à la main)")
check(T.travail_adiabatique(1, 12.471, 300, 300) == 0.0, "T1==T2 -> W adiabatique = 0.0 exact")
# détente adiabatique (refroidissement T2<T1) -> W fourni positif
check(T.travail_adiabatique(1, 12.471, 400, 300) > 0, "détente adiabatique (T baisse) -> W > 0")

# ── 5) ENTROPIE D'ÉCHAUFFEMENT (le manque comblé) ──
check(proche(T.entropie_echauffement(1, 4185, 300, 400), 1203.9, tol=1e-1),
      "ΔS échauffement eau 300->400K = 4185·ln(4/3) = 1203.9 J/K (à la main)")
check(T.entropie_echauffement(1, 4185, 350, 350) == 0.0, "T1==T2 -> ΔS échauffement = 0.0 exact")
# refroidissement (T2<T1) -> ΔS < 0
check(T.entropie_echauffement(1, 4185, 400, 300) < 0, "refroidissement -> ΔS échauffement < 0")

# ── 6) ANCRE PIÈGE : les °C sont REFUSÉS (jamais le FAUX facteur ~5) ──
# 27->127 en °C donnerait 4185·ln(127/27) ≈ 6486 J/K ; la bonne réponse (K) serait ~1204. -> ValueError.
check(leve(T.entropie_echauffement, 1, 4185, 27, 127), "°C (27->127) refusé (T<100K ambigu) -> ValueError")
check(leve(T.entropie_echauffement, 1, 4185, 80, 90), "°C (80,90) refusé (T<100K) -> ValueError")
# preuve que le résultat NON refusé, lui, est bien la valeur kelvin (≈1204, PAS 6486)
val_K = T.entropie_echauffement(1, 4185, 300, 400)
check(1200.0 < val_K < 1210.0 and not (6000.0 < val_K < 7000.0), "valeur retenue = kelvin (~1204), pas °C (~6486)")

# ── 7) ENTROPIE DÉTENTE ISOTHERME + SECOND CHEMIN (entropie_thermo, module réservé) ──
dS_det = T.entropie_detente_isotherme(1, 1.0, 2.0)
check(proche(dS_det, 5.763, tol=1e-3), "ΔS détente V->2V = 8.314·ln2 = 5.763 J/K (à la main)")
# chemin indépendant : ΔS = Q/T avec Q = W (isotherme) -> module RÉSERVÉ entropie_thermo.variation_entropie
dS_via_QsurT = entropie_thermo.variation_entropie(W_iso, 300)
check(proche(dS_det, dS_via_QsurT, tol=1e-2), "ΔS détente == Q/T (second chemin, entropie_thermo)")
check(T.entropie_detente_isotherme(1, 2.0, 2.0) == 0.0, "V1==V2 -> ΔS détente = 0.0 exact")

# ── 8) ENTROPIE GAZ PARFAIT (deux termes) ──
check(proche(T.entropie_gaz_parfait(1, 12.471, 300, 600, 1.0, 2.0), 14.407, tol=1e-2),
      "ΔS gaz parfait = 2.5R·ln2 = 14.407 J/K (à la main)")
# T1==T2 -> seul le terme volume subsiste (= détente isotherme)
check(proche(T.entropie_gaz_parfait(1, 12.471, 300, 300, 1.0, 2.0), 5.763, tol=1e-3),
      "gaz parfait T1==T2 -> terme volume seul = 5.763")
# V1==V2 -> seul le terme température subsiste : 1.5R·ln2 = 8.644
check(proche(T.entropie_gaz_parfait(1, 12.471, 300, 600, 2.0, 2.0), 8.644, tol=1e-2),
      "gaz parfait V1==V2 -> terme T seul = 1.5R·ln2 = 8.644")
check(T.entropie_gaz_parfait(1, 12.471, 300, 300, 2.0, 2.0) == 0.0, "T1==T2 et V1==V2 -> ΔS = 0.0 exact")

# ── 9) ENTROPIE UNIVERS + SPONTANÉITÉ ──
check(proche(T.entropie_univers(5.763, -4.0), 1.763), "ΔS_univers = 5.763 + (−4.0) = 1.763 (à la main)")
check(T.spontane(1.763) is True, "ΔS_univers > 0 -> spontané")
check(T.spontane(-1.0) is False, "ΔS_univers < 0 -> non spontané")
check(T.spontane(0.0) is False, "ΔS_univers = 0 -> réversible (non spontané au sens strict)")

# ── 10) BORNE DE CARNOT ──
check(proche(T.rendement_carnot(300, 600), 0.5), "Carnot(Tf=300,Tc=600) = 0.5 (à la main)")
check(proche(T.rendement_carnot(300, 400), 0.25), "Carnot(Tf=300,Tc=400) = 0.25")
check(proche(T.rendement_carnot(273.15, 373.15), 1 - 273.15 / 373.15), "Carnot(273.15,373.15) cohérent")
# verifie_second_principe : conforme -> renvoie le rendement ; dépassement -> ValueError
check(proche(T.verifie_second_principe(0.4, 300, 600), 0.4), "rendement 0.4 ≤ Carnot 0.5 -> renvoyé")
check(proche(T.verifie_second_principe(0.5, 300, 600), 0.5), "rendement = Carnot 0.5 -> conforme")
check(leve(T.verifie_second_principe, 0.6, 300, 600), "rendement 0.6 > Carnot 0.5 -> ValueError")
check(leve(T.verifie_second_principe, 1.2, 300, 600), "rendement 1.2 (>1) -> ValueError")

# ── 11) SOUNDNESS — températures ≤ 0 K ──
check(leve(T.travail_isotherme_gaz_parfait, 1, 0.0, 1.0, 2.0), "T=0 K isotherme -> ValueError")
check(leve(T.travail_isotherme_gaz_parfait, 1, -300.0, 1.0, 2.0), "T<0 K isotherme -> ValueError")
check(leve(T.travail_adiabatique, 1, 12.471, 0.0, 400), "T1=0 K adiabatique -> ValueError")
check(leve(T.rendement_carnot, 0.0, 600), "Tf=0 K Carnot -> ValueError")
check(leve(T.rendement_carnot, -1.0, 600), "Tf<0 K Carnot -> ValueError")

# ── 12) SOUNDNESS — Carnot mal posé (Tf ≥ Tc) ──
check(leve(T.rendement_carnot, 600, 300), "Tf>Tc -> ValueError (aucun travail extractible)")
check(leve(T.rendement_carnot, 400, 400), "Tf==Tc -> ValueError")
check(leve(T.verifie_second_principe, 0.4, 600, 300), "verifie Tf>Tc -> ValueError")

# ── 13) SOUNDNESS — grandeurs ≤ 0 (n, m, c, Cv, P, V) ──
check(leve(T.travail_isotherme_gaz_parfait, 0, 300, 1.0, 2.0), "n=0 -> ValueError")
check(leve(T.travail_isotherme_gaz_parfait, 1, 300, 0.0, 2.0), "V1=0 -> ValueError")
check(leve(T.travail_isotherme_gaz_parfait, 1, 300, 1.0, -2.0), "V2<0 -> ValueError")
check(leve(T.travail_isobare, 0.0, 1e-3, 3e-3), "P=0 -> ValueError")
check(leve(T.travail_isobare, 1e5, -1e-3, 3e-3), "V1<0 isobare -> ValueError")
check(leve(T.travail_adiabatique, 1, 0.0, 300, 400), "Cv=0 -> ValueError")
check(leve(T.entropie_echauffement, 0, 4185, 300, 400), "m=0 échauffement -> ValueError")
check(leve(T.entropie_echauffement, 1, 0.0, 300, 400), "c=0 échauffement -> ValueError")
check(leve(T.entropie_detente_isotherme, 1, 0.0, 2.0), "V1=0 détente -> ValueError")
check(leve(T.entropie_gaz_parfait, 1, 0.0, 300, 600, 1.0, 2.0), "Cv=0 gaz parfait -> ValueError")
check(leve(T.entropie_gaz_parfait, 1, 12.471, 300, 600, 0.0, 2.0), "V1=0 gaz parfait -> ValueError")

# ── 14) SOUNDNESS — °C dans entropie_gaz_parfait aussi (ln(T2/T1)) ──
check(leve(T.entropie_gaz_parfait, 1, 12.471, 27, 90, 1.0, 2.0), "T<100 K gaz parfait (°C) -> ValueError")

# ── 15) SOUNDNESS — types invalides (bool / str / NaN / inf) ──
NAN = float("nan")
INF = float("inf")
check(leve(T.variation_energie_interne, True, 30), "Q bool -> ValueError")
check(leve(T.variation_energie_interne, 100, "30"), "W str -> ValueError")
check(leve(T.variation_energie_interne, NAN, 30), "Q NaN -> ValueError")
check(leve(T.variation_energie_interne, 100, INF), "W inf -> ValueError")
check(leve(T.travail_isotherme_gaz_parfait, True, 300, 1.0, 2.0), "n bool -> ValueError")
check(leve(T.entropie_echauffement, 1, 4185, NAN, 400), "T NaN échauffement -> ValueError")
check(leve(T.entropie_univers, "a", 1.0), "dS str univers -> ValueError")
check(leve(T.entropie_univers, 1.0, INF), "dS inf univers -> ValueError")
check(leve(T.spontane, "x"), "spontane str -> ValueError")
check(leve(T.verifie_second_principe, NAN, 300, 600), "rendement NaN -> ValueError")
check(leve(T.verifie_second_principe, -0.1, 300, 600), "rendement <0 -> ValueError")

# ── 16) DÉTERMINISME ──
check(T.entropie_echauffement(1, 4185, 300, 400) == T.entropie_echauffement(1, 4185, 300, 400),
      "déterminisme échauffement")
check(T.rendement_carnot(300, 600) == T.rendement_carnot(300, 600), "déterminisme Carnot")
check(T.travail_isotherme_gaz_parfait(1, 300, 1.0, 2.0) == T.travail_isotherme_gaz_parfait(1, 300, 1.0, 2.0),
      "déterminisme travail isotherme")

print(f"\n=== valide_thermodynamique_principes : {ok}/{ok+ko} ===")
import sys
sys.exit(0 if ko == 0 else 1)
