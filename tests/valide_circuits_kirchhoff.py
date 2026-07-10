"""
VALIDE circuits_kirchhoff.py — held-out ADVERSE.

ANCRES EXTERNES NON CIRCULAIRES (loi d'Ohm calculée À LA MAIN, jamais par le solveur) :
  • SÉRIE : R1=2 Ω, R2=3 Ω, E=10 V dans la boucle -> I = 10/(2+3) = 2 A exactement (Ohm à la main) ;
    chute sur R2 : V = 2·3 = 6 V.
  • PARALLÈLE : R1=R2=4 Ω sous 8 V exactement à leurs bornes -> I_branche = 8/4 = 2 A, I_total = 4 A.
    (Réalisé avec une source RÉELLE E=16 V, Rs=2 Ω : Req = 2+4∥4 = 4 Ω, I_total = 16/4 = 4 A,
    V aux bornes du parallèle = 16 − 4·2 = 8 V — TOUT calculé à la main, indépendamment du solveur.)
  • PONT DE WHEATSTONE À L'ÉQUILIBRE (R1/R2 = 2/4 = R3/R4 = 3/6) : courant EXACTEMENT NUL dans le
    galvanomètre (fait classique, indépendant du solveur) ; à la main : Req = Rs + (2+4)∥(3+6)
    = 1 + 18/5 = 23/5 Ω -> I_total = 10/(23/5) = 50/23 A ; bras gauche 30/23 A, bras droit 20/23 A.
  • DIVISEUR : R1=1 Ω, R2=1 Ω sous 10 V -> 5 V au point milieu (10·1/(1+1), à la main).
  • BATTERIE EN CIRCUIT OUVERT (une seule branche) : I = 0, tension aux bornes = fem (fait classique).
  • DEUX FEM OPPOSÉES 5 V et 3 V dans une boucle de 2 Ω : I = (5−3)/2 = 1 A (à la main).
  • TOUS les courants et potentiels doivent être des fractions.Fraction EXACTES (isinstance).

SOUNDNESS : R≤0, float/NaN/inf/bool/str pour R ou E, nœud invalide, a==b, circuit vide,
circuit non connexe -> ValueError. DÉTERMINISME : deux résolutions identiques.
"""
from fractions import Fraction

import circuits_kirchhoff as CK

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


# ── 1) ANCRE : SÉRIE R1=2, R2=3, E=10 -> I = 2 A (Ohm à la main : 10/5) ──
c = CK.Circuit()
b1 = c.ajoute_branche("P", "Q", 2, 10)     # branche batterie+R1, fem orientée P->Q
b2 = c.ajoute_branche("Q", "P", 3)         # R2
r = c.resout()
check(r["courants"][b1] == Fraction(2), "série : I(branche source) = 2 A exactement")
check(r["courants"][b2] == Fraction(2), "série : I(R2) = 2 A exactement")
check(r["potentiels"]["Q"] == Fraction(6), "série : V(Q) = 2 A × 3 Ω = 6 V (Ohm à la main)")
check(r["potentiels"]["P"] == Fraction(0), "série : masse (1er nœud) à 0 V")
check(isinstance(r["courants"][b1], Fraction), "série : courant = Fraction (exact)")
check(isinstance(r["potentiels"]["Q"], Fraction), "série : potentiel = Fraction (exact)")
check(b1 == 0 and b2 == 1, "ajoute_branche renvoie les indices 0 puis 1")

# ── 2) ANCRE : PARALLÈLE R1=R2=4 sous 8 V -> I_total = 4 A, I_branche = 2 A ──
# source réelle E=16, Rs=2 : à la main Req = 2+2 = 4, I_total = 4, V(parallèle) = 16−8 = 8.
c = CK.Circuit()
bs = c.ajoute_branche("M", "T", 2, 16)     # source réelle
p1 = c.ajoute_branche("T", "M", 4)
p2 = c.ajoute_branche("T", "M", 4)
r = c.resout()
check(r["potentiels"]["T"] == Fraction(8), "parallèle : 8 V exactement aux bornes du couple")
check(r["courants"][bs] == Fraction(4), "parallèle : I_total = 4 A exactement")
check(r["courants"][p1] == Fraction(2), "parallèle : I(branche 1) = 8/4 = 2 A")
check(r["courants"][p2] == Fraction(2), "parallèle : I(branche 2) = 8/4 = 2 A")
check(r["courants"][bs] == r["courants"][p1] + r["courants"][p2], "parallèle : KCL au nœud T (4 = 2+2)")

# ── 3) ANCRE : PONT DE WHEATSTONE À L'ÉQUILIBRE (2/4 = 3/6) -> I_galvanomètre = 0 ──
c = CK.Circuit()
bsrc = c.ajoute_branche("bas", "haut", 1, 10)      # source réelle E=10, Rs=1
bg1 = c.ajoute_branche("haut", "gauche", 2)        # R1
bg2 = c.ajoute_branche("gauche", "bas", 4)         # R2
bd1 = c.ajoute_branche("haut", "droite", 3)        # R3
bd2 = c.ajoute_branche("droite", "bas", 6)         # R4
bg = c.ajoute_branche("gauche", "droite", 5)       # galvanomètre
r = c.resout()
check(r["courants"][bg] == Fraction(0), "Wheatstone équilibré : courant NUL dans le galvanomètre")
check(r["potentiels"]["gauche"] == r["potentiels"]["droite"],
      "Wheatstone équilibré : V(gauche) = V(droite)")
check(r["courants"][bsrc] == Fraction(50, 23), "Wheatstone : I_total = 50/23 A (Req=23/5 à la main)")
check(r["courants"][bg1] == Fraction(30, 23), "Wheatstone : bras gauche 30/23 A (180/23 V sur 6 Ω)")
check(r["courants"][bg2] == Fraction(30, 23), "Wheatstone : R2 porte le même courant que R1 (galvo nul)")
check(r["courants"][bd1] == Fraction(20, 23), "Wheatstone : bras droit 20/23 A (180/23 V sur 9 Ω)")
check(r["courants"][bd2] == Fraction(20, 23), "Wheatstone : R4 porte le même courant que R3 (galvo nul)")
check(r["courants"][bg1] + r["courants"][bd1] == r["courants"][bsrc],
      "Wheatstone : KCL au nœud haut (30/23 + 20/23 = 50/23)")
check(all(isinstance(i, Fraction) for i in r["courants"].values()),
      "Wheatstone : TOUS les courants sont des Fraction exactes")
check(all(isinstance(v, Fraction) for v in r["potentiels"].values()),
      "Wheatstone : TOUS les potentiels sont des Fraction exactes")
check(set(r["courants"].keys()) == {0, 1, 2, 3, 4, 5}, "Wheatstone : un courant par branche (indices 0..5)")

# pont DÉSÉQUILIBRÉ (R4=7 : 2/4 ≠ 3/7) -> le galvanomètre débite (fait classique)
c = CK.Circuit()
c.ajoute_branche("bas", "haut", 1, 10)
c.ajoute_branche("haut", "gauche", 2)
c.ajoute_branche("gauche", "bas", 4)
c.ajoute_branche("haut", "droite", 3)
c.ajoute_branche("droite", "bas", 7)
bgd = c.ajoute_branche("gauche", "droite", 5)
check(c.resout()["courants"][bgd] != 0, "Wheatstone déséquilibré : courant non nul dans le galvanomètre")

# ── 4) ANCRE : DIVISEUR R1=1, R2=1 sous 10 V -> 5 V au milieu ──
c = CK.Circuit()
d1 = c.ajoute_branche("G", "milieu", 1, 10)
d2 = c.ajoute_branche("milieu", "G", 1)
r = c.resout()
check(r["potentiels"]["milieu"] == Fraction(5), "diviseur : V(milieu) = 5 V exactement")
check(r["courants"][d1] == Fraction(5), "diviseur : I = 10/2 = 5 A (Ohm à la main)")
check(r["courants"][d1] == r["courants"][d2], "diviseur : même courant dans les deux branches (série)")

# ── 5) ANCRE : batterie en CIRCUIT OUVERT (une branche) -> I = 0, V = fem ──
c = CK.Circuit()
bo = c.ajoute_branche("X", "Y", 7, 21)
r = c.resout()
check(r["courants"][bo] == Fraction(0), "circuit ouvert : I = 0 (pas de boucle)")
check(r["potentiels"]["Y"] == Fraction(21), "circuit ouvert : tension aux bornes = fem (21 V)")

# ── 6) ANCRE : deux fem OPPOSÉES 5 V / 3 V dans 2 Ω -> I = (5−3)/2 = 1 A (à la main) ──
c = CK.Circuit()
e1 = c.ajoute_branche("A", "B", 1, 5)
e2 = c.ajoute_branche("A", "B", 1, 3)      # même orientation : les fem s'opposent dans la boucle
r = c.resout()
check(r["courants"][e1] == Fraction(1), "fem opposées : I(branche 5 V) = +1 A")
check(r["courants"][e2] == Fraction(-1), "fem opposées : I(branche 3 V) = −1 A (rebrousse)")
check(r["potentiels"]["B"] == Fraction(4), "fem opposées : V(B) = 5−1·1 = 4 V (loi de branche à la main)")

# ── 7) entrées Fraction exactes acceptées : R=1/2 Ω, E=3 V, R2=1 Ω -> I = 3/(3/2) = 2 A ──
c = CK.Circuit()
f1 = c.ajoute_branche("A", "B", Fraction(1, 2), Fraction(3))
f2 = c.ajoute_branche("B", "A", 1)
r = c.resout()
check(r["courants"][f1] == Fraction(2), "R en Fraction : I = 3/(1/2+1) = 2 A exactement")
check(r["potentiels"]["B"] == Fraction(2), "R en Fraction : V(B) = 2 A × 1 Ω = 2 V")

# ── 8) SOUNDNESS — résistance ──
c = CK.Circuit()
check(leve(c.ajoute_branche, "A", "B", 0), "R=0 -> ValueError")
check(leve(c.ajoute_branche, "A", "B", -2), "R<0 -> ValueError")
check(leve(c.ajoute_branche, "A", "B", Fraction(-1, 3)), "R Fraction négative -> ValueError")
check(leve(c.ajoute_branche, "A", "B", 2.0), "R flottant -> ValueError (exactitude exigée)")
check(leve(c.ajoute_branche, "A", "B", True), "R bool -> ValueError")
check(leve(c.ajoute_branche, "A", "B", "2"), "R str -> ValueError")
check(leve(c.ajoute_branche, "A", "B", float("nan")), "R NaN -> ValueError")
check(leve(c.ajoute_branche, "A", "B", float("inf")), "R inf -> ValueError")

# ── 9) SOUNDNESS — fem ──
check(leve(c.ajoute_branche, "A", "B", 1, 2.5), "E flottant -> ValueError")
check(leve(c.ajoute_branche, "A", "B", 1, True), "E bool -> ValueError")
check(leve(c.ajoute_branche, "A", "B", 1, "10"), "E str -> ValueError")
check(leve(c.ajoute_branche, "A", "B", 1, float("-inf")), "E -inf -> ValueError")
check(leve(c.ajoute_branche, "A", "B", 1, 1 + 2j), "E complexe -> ValueError")

# ── 10) SOUNDNESS — nœuds ──
check(leve(c.ajoute_branche, True, "B", 1), "nœud bool -> ValueError")
check(leve(c.ajoute_branche, 1.5, "B", 1), "nœud flottant -> ValueError")
check(leve(c.ajoute_branche, None, "B", 1), "nœud None -> ValueError")
check(leve(c.ajoute_branche, "", "B", 1), "nœud chaîne vide -> ValueError")
check(leve(c.ajoute_branche, "A", "A", 1), "noeud_a == noeud_b -> ValueError")

# ── 11) SOUNDNESS — circuit vide / non connexe ──
check(leve(CK.Circuit().resout), "circuit vide -> ValueError")
c = CK.Circuit()
c.ajoute_branche("A", "B", 1, 1)
c.ajoute_branche("C", "D", 1)              # composante isolée de la masse
check(leve(c.resout), "circuit non connexe -> ValueError")

# les échecs de validation n'ont RIEN ajouté : le circuit sain reste résoluble après tentatives invalides
c = CK.Circuit()
c.ajoute_branche("P", "Q", 2, 10)
try:
    c.ajoute_branche("P", "Q", -1)
except ValueError:
    pass
c.ajoute_branche("Q", "P", 3)
check(c.resout()["courants"][0] == Fraction(2), "branche rejetée non enregistrée : I série toujours 2 A")

# ── 12) DÉTERMINISME ──
c = CK.Circuit()
c.ajoute_branche("bas", "haut", 1, 10)
c.ajoute_branche("haut", "gauche", 2)
c.ajoute_branche("gauche", "bas", 4)
c.ajoute_branche("haut", "droite", 3)
c.ajoute_branche("droite", "bas", 6)
c.ajoute_branche("gauche", "droite", 5)
r1 = c.resout()
r2 = c.resout()
check(r1["potentiels"] == r2["potentiels"], "déterminisme : potentiels identiques sur deux résolutions")
check(r1["courants"] == r2["courants"], "déterminisme : courants identiques sur deux résolutions")

print(f"\n=== valide_circuits_kirchhoff : {ok}/{ok+ko} ===")
import sys; sys.exit(0 if ko == 0 else 1)
