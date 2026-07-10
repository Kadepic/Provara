"""
VALIDE cinematique_uniformement_acceleree.py — held-out ADVERSE.

ANCRES EXTERNES NON CIRCULAIRES (valeurs connues INDÉPENDAMMENT, PAS recalculées par la formule testée) :
  • CHUTE LIBRE, g = 9.80665 m/s² (valeur normalisée CGPM 1901) : après 1 s depuis le repos,
    v = 9.80665 m/s (g·1, trivial) et x = 4.903325 m (½·9.80665·1² = 4.903325, calcul À LA MAIN).
    Après 2 s : v = 19.6133 m/s (9.80665·2 à la main) et x = 19.6133 m (½·9.80665·4 = 19.6133 à la main).
  • VOITURE 0 -> 100 km/h (= 27.77778 m/s) en 5 s : a = 27.77778/5 = 5.555556 m/s² (division à la main).
    Donc temps_pour_vitesse(0, 27.77778, 5.555556) = 5 s et vitesse_finale(0, 5.555556, 5) = 27.77778 m/s.
  • CAS ENTIER À LA MAIN : v0=3, a=2, t=4 -> v = 3 + 2·4 = 11 ; Δx = 3·4 + ½·2·16 = 12 + 16 = 28 ;
    Torricelli : v² = 3² + 2·2·28 = 9 + 112 = 121 = 11² (arithmétique entière posée ici, pas la formule).
  • temps_pour_position : x0=0, v0=0, a=2, x=25 -> ½·2·t² = 25 -> t² = 25 -> t = 5 (racine carrée à la main).
    Deux racines : v0=10, a=−2, x=16 -> t² − 10t + 16 = 0 -> (t−2)(t−8)=0 -> t ∈ {2, 8}, plus petit = 2
    (factorisation à la main ; contrôle : 10·2 + ½·(−2)·4 = 20 − 4 = 16 ✓).
  • COHÉRENCE CROISÉE NON CIRCULAIRE : v² = v0² + 2·a·Δx (Torricelli, SANS le temps) doit redonner la même
    vitesse que v = v0 + a·t (AVEC le temps) pour le même mouvement — deux chemins de code distincts.

  • STABILITÉ NUMÉRIQUE (forme Citardauq) : x0=0, v0=1, a=1e-300, x=10 -> le terme ½·a·t² ≈ 5e-299 est
    NÉGLIGEABLE devant v0·t, donc t = x/v0 = 10 s (raisonnement à la main ; la forme naïve (−v0+√D)/a
    rendait 0.0). x0=0, v0=1e8, a=1, x=1 -> t = 2/(1e8+√(1e16+2)) ; √(1e16+2) = 1e8·√(1+2e-16) =
    1e8 + 1e-8 (série binomiale à la main), donc t = 2/(2e8+1e-8) = 1e-8·(1−5e-17) -> 1.0e-08 à
    10 chiffres (la forme naïve rendait 1.490116119e-08, 49 % d'erreur).
    x0=0, v0=1000, a=0.001, x=0.5 -> t = 1/(1000+√1000000.001) ; √1000000.001 = 1000·√(1+1e-9) =
    1000.0000005 (série à la main), t = 1/2000.0000005 = 0.000499999999875 -> 0.0004999999999 à
    10 chiffres (la forme naïve rendait 0.0005000000556, faux dès le 8e chiffre).

SOUNDNESS : t<0, a=0 (formules dégénérées), discriminant<0, aucune racine ≥ 0, v²<0,
bool/str/NaN/inf/complexe -> ValueError ; DÉBORDEMENT (résultat/discriminant non fini) -> ValueError
(le module refusait inf en entrée mais l'émettait en sortie : corrigé, prouvé ici).
DÉTERMINISME : double appel, égalité exigée.
"""
import math

import cinematique_uniformement_acceleree as C

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


def proche(x, attendu, tol=1e-6):
    return x is not None and abs(x - attendu) <= tol


G = 9.80665  # m/s², pesanteur normalisée (CGPM 1901) — constante EXTERNE, pas issue du module

# ── 1) ANCRE : CHUTE LIBRE depuis le repos ──
check(proche(C.vitesse_finale(0.0, G, 1.0), 9.80665), "chute libre 1 s : v = 9.80665 m/s (g·1)")
check(proche(C.position(0.0, 0.0, G, 1.0), 4.903325), "chute libre 1 s : x = 4.903325 m (½·9.80665 à la main)")
check(proche(C.vitesse_finale(0.0, G, 2.0), 19.6133), "chute libre 2 s : v = 19.6133 m/s (9.80665·2 à la main)")
check(proche(C.position(0.0, 0.0, G, 2.0), 19.6133), "chute libre 2 s : x = 19.6133 m (½·9.80665·4 à la main)")
# décalage d'origine : x0 = 100 m -> x = 104.903325 m (addition à la main)
check(proche(C.position(100.0, 0.0, G, 1.0), 104.903325), "chute libre 1 s depuis x0=100 : x = 104.903325 m")
# Torricelli sur la même chute : v² après Δx = 4.903325 m = 2·9.80665·4.903325 = 96.1703842225
# (= 9.80665² posé à la main : 96.04 + 0.13034 + 0.0000442225) -> v = 9.80665 m/s
check(proche(C.vitesse_carre(0.0, G, 4.903325), 96.1703842225, tol=1e-6),
      "Torricelli chute libre : v² = 96.1703842225 (9.80665² à la main)")
check(proche(math.sqrt(C.vitesse_carre(0.0, G, 4.903325)), 9.80665),
      "Torricelli chute libre : √(v²) = 9.80665 m/s")

# ── 2) ANCRE : VOITURE 0 -> 100 km/h (27.77778 m/s) en 5 s, a = 5.555556 m/s² ──
check(proche(C.vitesse_finale(0.0, 5.555556, 5.0), 27.77778, tol=1e-5),
      "voiture : v(5 s) = 27.77778 m/s (5.555556·5 à la main)")
check(proche(C.temps_pour_vitesse(0.0, 27.77778, 5.555556), 5.0, tol=1e-5),
      "voiture : t(0->27.77778 m/s) = 5 s (27.77778/5.555556 à la main)")
# distance parcourue pendant ces 5 s : ½·5.555556·25 = 69.44445 m (multiplication à la main)
check(proche(C.position(0.0, 0.0, 5.555556, 5.0), 69.44445, tol=1e-4),
      "voiture : x(5 s) = 69.44445 m (½·5.555556·25 à la main)")

# ── 3) ANCRE : cas entier posé à la main (v0=3, a=2, t=4) ──
check(proche(C.vitesse_finale(3.0, 2.0, 4.0), 11.0), "v0=3,a=2,t=4 : v = 11 (3+8 à la main)")
check(proche(C.position(0.0, 3.0, 2.0, 4.0), 28.0), "v0=3,a=2,t=4 : Δx = 28 (12+16 à la main)")
check(proche(C.vitesse_carre(3.0, 2.0, 28.0), 121.0), "Torricelli : v² = 121 (9+112 à la main)")
check(proche(C.temps_pour_vitesse(3.0, 11.0, 2.0), 4.0), "t(3->11, a=2) = 4 s ((11−3)/2 à la main)")
check(proche(C.temps_pour_position(0.0, 3.0, 2.0, 28.0), 4.0), "t(Δx=28) = 4 s (racine du trinôme, contrôle main)")

# ── 4) COHÉRENCE CROISÉE NON CIRCULAIRE : Torricelli (sans t) vs v = v0 + a·t (avec t) ──
for (v0, a, t) in ((0.0, G, 1.0), (3.0, 2.0, 4.0), (5.0, -1.5, 2.0), (12.0, 0.25, 8.0)):
    v_temporelle = C.vitesse_finale(v0, a, t)                    # chemin 1 : v = v0 + a·t
    dx = C.position(0.0, v0, a, t)                               # Δx du même mouvement
    v_torricelli = math.sqrt(C.vitesse_carre(v0, a, dx))         # chemin 2 : v² = v0² + 2·a·Δx
    check(proche(v_torricelli, abs(v_temporelle), tol=1e-6),
          f"cohérence croisée Torricelli vs v0+at (v0={v0}, a={a}, t={t})")

# ── 5) temps_pour_position : discriminant, plus petite racine ≥ 0 ──
check(proche(C.temps_pour_position(0.0, 0.0, 2.0, 25.0), 5.0), "t : ½·2·t²=25 -> t=5 (t²=25 à la main)")
check(proche(C.temps_pour_position(0.0, 10.0, -2.0, 16.0), 2.0),
      "t : t²−10t+16=0 -> racines {2,8}, plus petite = 2 (factorisation à la main)")
# contrôle indépendant de la racine 2 : position(0,10,−2,2) = 20−4 = 16 (à la main)
check(proche(C.position(0.0, 10.0, -2.0, 2.0), 16.0), "contrôle : x(t=2) = 16 m (20−4 à la main)")
# départ décalé : x0=5, v0=0, a=2, x=30 -> ½·2·t²=25 -> t=5
check(proche(C.temps_pour_position(5.0, 0.0, 2.0, 30.0), 5.0), "t avec x0=5 : t=5 (t²=25 à la main)")
# position déjà atteinte à t=0 : x=x0 -> racine t=0 acceptée
check(proche(C.temps_pour_position(7.0, 3.0, 2.0, 7.0), 0.0), "x = x0 -> t = 0 (racine nulle)")

# ── 6) ABSTENTION : discriminant négatif (position jamais atteinte) ──
check(leve(C.temps_pour_position, 0.0, 0.0, -2.0, 5.0), "décélération vers l'arrière, cible avant -> ValueError")
check(leve(C.temps_pour_position, 0.0, 3.0, -2.0, 100.0), "cible au-delà de l'apogée -> ValueError (D<0)")
# apogée du jet v0=3, a=−2 : Δx_max = v0²/(2·|a|) = 9/4 = 2.25 (à la main) ; 2.25 est atteignable, 2.26 non
check(proche(C.temps_pour_position(0.0, 3.0, -2.0, 2.25), 1.5), "apogée Δx=2.25 -> t=1.5 (v0/|a| à la main)")
check(leve(C.temps_pour_position, 0.0, 3.0, -2.0, 2.26), "Δx=2.26 > apogée 2.25 -> ValueError (D<0)")

# ── 7) ABSTENTION : aucune racine ≥ 0 (position atteinte seulement dans le passé) ──
check(leve(C.temps_pour_position, 0.0, 5.0, 2.0, -3.0), "cible derrière, mouvement avant -> ValueError")

# ── 8) ABSTENTION : a = 0 (formules dégénérées) ──
check(leve(C.temps_pour_vitesse, 0.0, 10.0, 0.0), "temps_pour_vitesse a=0 -> ValueError")
check(leve(C.temps_pour_vitesse, 5.0, 5.0, 0.0), "temps_pour_vitesse a=0 (même v) -> ValueError")
check(leve(C.temps_pour_position, 0.0, 2.0, 0.0, 10.0), "temps_pour_position a=0 -> ValueError")

# ── 9) ABSTENTION : v² < 0 (Torricelli sans solution réelle) ──
check(leve(C.vitesse_carre, 0.0, -2.0, 5.0), "v²=0+2·(−2)·5=−20<0 -> ValueError")
check(leve(C.vitesse_carre, 3.0, -2.0, 3.0), "v²=9−12=−3<0 -> ValueError")
check(proche(C.vitesse_carre(3.0, -2.0, 2.25), 0.0), "v²=9−9=0 accepté (arrêt exact, pas négatif)")

# ── 10) ABSTENTION : temps négatif ──
check(leve(C.vitesse_finale, 0.0, G, -1.0), "vitesse_finale t<0 -> ValueError")
check(leve(C.position, 0.0, 0.0, G, -0.5), "position t<0 -> ValueError")
check(leve(C.temps_pour_vitesse, 10.0, 5.0, 2.0), "t=(5−10)/2<0 -> ValueError (vitesse dans le passé)")

# ── 11) SOUNDNESS — bool refusés (True n'est pas 1) ──
check(leve(C.vitesse_finale, True, 2.0, 1.0), "v0 bool -> ValueError")
check(leve(C.vitesse_finale, 0.0, True, 1.0), "a bool -> ValueError")
check(leve(C.position, 0.0, 0.0, 2.0, True), "t bool -> ValueError")
check(leve(C.vitesse_carre, False, 2.0, 1.0), "v0 False -> ValueError")
check(leve(C.temps_pour_vitesse, 0.0, True, 2.0), "v bool -> ValueError")
check(leve(C.temps_pour_position, True, 0.0, 2.0, 5.0), "x0 bool -> ValueError")

# ── 12) SOUNDNESS — str / NaN / inf refusés ──
check(leve(C.vitesse_finale, "0", 2.0, 1.0), "v0 str -> ValueError")
check(leve(C.vitesse_finale, 0.0, float("nan"), 1.0), "a NaN -> ValueError")
check(leve(C.vitesse_finale, 0.0, 2.0, float("inf")), "t inf -> ValueError")
check(leve(C.position, float("nan"), 0.0, 2.0, 1.0), "x0 NaN -> ValueError")
check(leve(C.position, 0.0, float("-inf"), 2.0, 1.0), "v0 −inf -> ValueError")
check(leve(C.vitesse_carre, 0.0, 2.0, float("nan")), "Δx NaN -> ValueError")
check(leve(C.vitesse_carre, 0.0, "2", 1.0), "a str -> ValueError")
check(leve(C.temps_pour_vitesse, float("inf"), 10.0, 2.0), "v0 inf -> ValueError")
check(leve(C.temps_pour_position, 0.0, 0.0, float("nan"), 5.0), "a NaN (position) -> ValueError")
check(leve(C.temps_pour_position, 0.0, 0.0, 2.0, "25"), "x str -> ValueError")

# ── 13) STABILITÉ NUMÉRIQUE — forme Citardauq (annulation catastrophique tuée) ──
# a quasi nul : x0=0, v0=1, a=1e-300, x=10. ½·a·t² ≈ 5e-299 est négligeable devant v0·t = t,
# donc t = x/v0 = 10 s (à la main). La forme naïve (−v0+√D)/a rendait 0.0 (faux plat).
check(proche(C.temps_pour_position(0.0, 1.0, 1e-300, 10.0), 10.0, tol=1e-9),
      "Citardauq a≈0 : t(x=10, v0=1, a=1e-300) = 10 s (½at² négligeable, à la main)")
# contrôle croisé par un SECOND chemin de code : position(t=10) doit redonner x = 10 m
check(proche(C.position(0.0, 1.0, 1e-300, 10.0), 10.0, tol=1e-9),
      "contrôle croisé : position(t=10, v0=1, a=1e-300) = 10 m")
# |v0| >> √(2aΔx) : x0=0, v0=1e8, a=1, x=1. t = 2/(1e8+√(1e16+2)) ; √(1e16+2) = 1e8+1e-8
# (série binomiale à la main) -> t = 2/(2e8+1e-8) = 1e-8·(1−5e-17) -> 1.0e-08 à 10 chiffres.
# La forme naïve rendait 1.490116119e-08 (49 % d'erreur) : tolérance SERRÉE pour la débusquer.
check(proche(C.temps_pour_position(0.0, 1e8, 1.0, 1.0), 1.0e-08, tol=1e-20),
      "Citardauq v0 dominant : t = 1.0e-08 s (série binomiale à la main)")
# miroir en signes (branche v0 < 0 de copysign) : x0=0, v0=−1e8, a=−1, x=−1 -> même t = 1.0e-08
# (même équation multipliée par −1, mêmes grandeurs à la main)
check(proche(C.temps_pour_position(0.0, -1e8, -1.0, -1.0), 1.0e-08, tol=1e-20),
      "Citardauq miroir v0<0 : t = 1.0e-08 s (équation multipliée par −1)")
# magnitudes ORDINAIRES : x0=0, v0=1000, a=0.001, x=0.5. t = 1/(1000+√1000000.001) ;
# √1000000.001 = 1000.0000005 (série à la main) -> t = 1/2000.0000005 = 0.000499999999875,
# arrondi à 10 chiffres = 0.0004999999999. La forme naïve rendait 0.0005000000556 (faux au 8e chiffre).
check(proche(C.temps_pour_position(0.0, 1000.0, 0.001, 0.5), 4.999999999e-4, tol=1e-13),
      "Citardauq magnitudes ordinaires : t = 4.999999999e-4 s (série à la main)")
# racine ÉNORME mais représentable (pas de fausse abstention) : x0=0, v0=0, a=1e-300, x=1e300
# -> t = √(2·x/a) = √(2e600) = √2·1e300 = 1.414213562e300 (√2 = 1.414213562…, valeur classique)
check(proche(C.temps_pour_position(0.0, 0.0, 1e-300, 1e300) / 1e300, 1.414213562, tol=1e-8),
      "racine énorme représentable : t = √2·1e300 (√2 classique)")

# ── 14) ABSTENTION — débordement flottant (inf refusé en SORTIE comme en entrée) ──
# discriminant déborde : v0² = 1e400 > plus grand flottant (~1.8e308) ; le vrai t ≈ 1e-200 est
# incalculable par cette voie -> abstention (l'ancien code rendait inf, un faux plat)
check(leve(C.temps_pour_position, 0.0, 1e200, 1e200, 1.0), "temps_pour_position : D=1e400 déborde -> ValueError")
# racine vraie > plus grand flottant : t = √(2·1.7e308/1e-308) ≈ 1.84e308 > 1.797…e308 -> abstention
check(leve(C.temps_pour_position, 0.0, 0.0, 1e-308, 1.7e308),
      "temps_pour_position : racine ≈ 1.84e308 > max flottant -> ValueError")
check(leve(C.vitesse_carre, 1e200, 1.0, 0.0), "vitesse_carre : v² vrai = 1e400 déborde -> ValueError")
check(leve(C.position, 0.0, 0.0, 1e300, 1e10), "position : ½·1e300·1e20 = 5e319 déborde -> ValueError")
check(leve(C.vitesse_finale, 1e308, 1e308, 1.0), "vitesse_finale : 1e308+1e308 déborde -> ValueError")
check(leve(C.temps_pour_vitesse, -1.7e308, 1.7e308, 1.0),
      "temps_pour_vitesse : v−v0 = 3.4e308 déborde -> ValueError")

# ── 15) DÉTERMINISME — double appel, égalité exigée ──
check(C.vitesse_finale(3.0, 2.0, 4.0) == C.vitesse_finale(3.0, 2.0, 4.0), "déterminisme vitesse_finale")
check(C.position(0.0, 3.0, 2.0, 4.0) == C.position(0.0, 3.0, 2.0, 4.0), "déterminisme position")
check(C.vitesse_carre(3.0, 2.0, 28.0) == C.vitesse_carre(3.0, 2.0, 28.0), "déterminisme vitesse_carre")
check(C.temps_pour_vitesse(3.0, 11.0, 2.0) == C.temps_pour_vitesse(3.0, 11.0, 2.0),
      "déterminisme temps_pour_vitesse")
check(C.temps_pour_position(0.0, 10.0, -2.0, 16.0) == C.temps_pour_position(0.0, 10.0, -2.0, 16.0),
      "déterminisme temps_pour_position")

print(f"\n=== valide_cinematique_uniformement_acceleree : {ok}/{ok+ko} ===")
import sys; sys.exit(0 if ko == 0 else 1)
