"""
VALIDE entropie_source.py — held-out ADVERSE.

ANCRES NON CIRCULAIRES (valeurs connues INDÉPENDAMMENT de la formule testée) :
  • Source UNIFORME sur 2 symboles -> H = 1 bit exactement (log2 2). Sur 4 symboles -> 2 bits (log2 4).
  • Source DÉTERMINISTE (un seul symbole) -> H = 0 (aucune surprise).
  • Pile-ou-face BIAISÉ p=0.9 -> H(0.9,0.1) ≈ 0.4689955936 bits (valeur classique de l'entropie binaire).
  • MARKOV, ancre forte : P = [[0.9,0.1],[0.1,0.9]] -> stationnaire (1/2,1/2) (matrice symétrique doublement
    stochastique), entropie stationnaire = 1 bit, mais TAUX D'ENTROPIE = H(0.9,0.1) ≈ 0.4690 bit,
    STRICTEMENT INFÉRIEUR à 1 : la mémoire réduit l'incertitude.
  • MARKOV asymétrique P = [[0.5,0.5],[0.25,0.75]] -> stationnaire (1/3,2/3), résolue À LA MAIN
    (π0 = 0.5π0 + 0.25π1, Σ=1 => π1 = 2π0 => π0 = 1/3). Taux = 1/3·H(.5,.5) + 2/3·H(.25,.75) ≈ 0.874187.
  • BIAIS : 20 tirages ~uniformes dans un alphabet de 8 -> entropie plug-in < 3 bits (biais vers le bas),
    et fiable(...) rend False (20 < 5·8 = 40).
  • CONDITIONNEL empirique : séquence strictement alternée -> taux d'ordre 1 = 0 (transitions déterministes) ;
    séquence 'a a b a a b' -> taux d'ordre 1 = 0.8 (calcul à la main écrit ci-dessous).

SOUNDNESS : séquence vide, symbole non hashable, alphabet vide, matrice non carrée / non stochastique / bool /
str / NaN / inf / hors [0,1], distribution fournie invalide, distribution NON stationnaire (πP≠π), ordre non
entier ≥ 1, séquence trop courte -> ValueError (abstention). Déterminisme exigé.
"""
import math
from fractions import Fraction

import entropie_source as E

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


# valeurs de référence calculées À LA MAIN (indépendantes du module) :
H_09 = -0.9 * math.log2(0.9) - 0.1 * math.log2(0.1)      # ≈ 0.4689955936 (entropie binaire p=0.9)
H_stat_13 = -(1 / 3) * math.log2(1 / 3) - (2 / 3) * math.log2(2 / 3)   # H(1/3,2/3) ≈ 0.9182958
H_25 = -0.25 * math.log2(0.25) - 0.75 * math.log2(0.75)  # H(0.25,0.75) ≈ 0.8112781

# ── 1) ENTROPIE EMPIRIQUE = ancres uniformes / déterministe / biaisée ──
h2, n2 = E.entropie_empirique(["a", "b", "a", "b"])       # 2 symboles équiprobables
check(proche(h2, 1.0), "uniforme 2 symboles -> H = 1 bit")
check(n2 == 4, "N observations = 4 rendu")
h4, n4 = E.entropie_empirique(["a", "b", "c", "d"] * 5)   # 4 symboles équiprobables
check(proche(h4, 2.0), "uniforme 4 symboles -> H = 2 bits")
check(n4 == 20, "N observations = 20 rendu")
h1, n1 = E.entropie_empirique(["z", "z", "z", "z"])       # 1 seul symbole
check(proche(h1, 0.0), "source déterministe -> H = 0")
check(n1 == 4, "N observations = 4 (déterministe)")
h9, n9 = E.entropie_empirique(["a"] * 9 + ["b"])          # fréquences 0.9 / 0.1
check(proche(h9, H_09, tol=1e-3), "biaisé p=0.9 -> H ≈ 0.4690 bit")
check(proche(h9, 0.4689955936, tol=1e-6), "biaisé p=0.9 -> H ≈ 0.4689955936 (valeur classique)")

# ── 2) FIABILITÉ : N ≥ 5·|alphabet| ──
alpha4 = ["a", "b", "c", "d"]
check(E.fiable(["a", "b", "c", "d"] * 5, alpha4) is True, "20 obs / alphabet 4 (>=20) -> fiable True")
check(E.fiable(["a", "b"], alpha4) is False, "2 obs / alphabet 4 -> fiable False")
alpha8 = list(range(8))
seq20 = [0, 1, 2, 3, 4, 5, 6, 7, 0, 1, 2, 3, 4, 5, 6, 7, 0, 1, 2, 3]   # 20 tirages ~uniformes sur 8
check(E.fiable(seq20, alpha8) is False, "20 obs / alphabet 8 -> fiable False (20 < 40)")

# ── 3) BIAIS : plug-in < 3 bits, correction Miller-Madow > plug-in ──
h_plugin, _ = E.entropie_empirique(seq20)
check(h_plugin < 3.0, "plug-in sur 20 tirages/8 symboles < 3 bits (biais vers le bas)")
h_mm = E.correction_miller_madow(seq20)
check(h_mm > h_plugin, "Miller-Madow REMONTE l'estimation biaisée (h_MM > h_plugin)")
# ANCRE INDÉPENDANTE (unités) : l'estimateur de Miller & Madow (1955) corrige le plug-in de (K-1)/(2N) NATS.
# Ce module rend l'entropie en BITS (log2), donc la correction en bits = (K-1)/(2N)/ln2.
# K=8 symboles observés, N=20 : (8-1)/(2*20) = 0.175 nats ; 0.175/ln2 = 0.2524716321555686 bits (valeur EN DUR).
CORR_MM_BITS = 0.2524716321555686
check(proche(h_mm - h_plugin, CORR_MM_BITS, tol=1e-9),
      "correction Miller-Madow en bits = (K-1)/(2N)/ln2 = 0.25247 (PAS 0.175 nats)")
check(abs(CORR_MM_BITS - 0.175) > 0.07, "la correction en bits diffère nettement de la valeur en nats (facteur ln2)")

# ── 4) DISTRIBUTION STATIONNAIRE (exacte) ──
pi_sym = E.distribution_stationnaire([[0.9, 0.1], [0.1, 0.9]])
check(pi_sym == [Fraction(1, 2), Fraction(1, 2)], "P symétrique -> stationnaire EXACTE (1/2,1/2)")
pi_asym = E.distribution_stationnaire([[0.5, 0.5], [0.25, 0.75]])
check(pi_asym == [Fraction(1, 3), Fraction(2, 3)], "P asymétrique -> stationnaire EXACTE (1/3,2/3)")
# cas identité-ligne (voie ITÉRÉE : 1/3 flottant ne somme pas exactement à 1)
pi_iter = E.distribution_stationnaire([[1 / 3, 2 / 3], [1 / 3, 2 / 3]])
check(proche(float(pi_iter[0]), 1 / 3, tol=1e-9) and proche(float(pi_iter[1]), 2 / 3, tol=1e-9),
      "voie itérée (rows non exactement normalisées) -> stationnaire ≈ (1/3,2/3)")

# ── 5) TAUX D'ENTROPIE MARKOV < ENTROPIE STATIONNAIRE (l'ancre forte) ──
taux_sym = E.entropie_conditionnelle_markov([[0.9, 0.1], [0.1, 0.9]], [Fraction(1, 2), Fraction(1, 2)])
check(proche(taux_sym, H_09, tol=1e-6), "taux Markov symétrique = H(0.9,0.1) ≈ 0.4690")
check(taux_sym < 1.0 - 1e-6, "taux Markov (0.469) STRICTEMENT < entropie stationnaire (1 bit)")
# taux asymétrique = 1/3·H(.5,.5) + 2/3·H(.25,.75), calculé à la main
taux_asym_main = (1 / 3) * 1.0 + (2 / 3) * H_25          # ≈ 0.874187 (référence indépendante)
taux_asym = E.entropie_conditionnelle_markov([[0.5, 0.5], [0.25, 0.75]], [Fraction(1, 3), Fraction(2, 3)])
check(proche(taux_asym, taux_asym_main, tol=1e-9), "taux Markov asymétrique = 1/3·H(.5,.5)+2/3·H(.25,.75)")
check(taux_asym < H_stat_13 - 1e-6, "taux asymétrique < H stationnaire (conditionnement réduit l'entropie)")

# ── 6) TAUX D'ENTROPIE EMPIRIQUE (conditionnel d'ordre 1) ──
check(proche(E.taux_entropie_empirique(["a", "b"] * 6, 1), 0.0),
      "séquence strictement alternée -> taux d'ordre 1 = 0 (déterministe)")
# 'a a b a a b' : contexte 'a' -> {a:2,b:2} (H=1), contexte 'b' -> {a:1} (H=0) ; poids 4/5 et 1/5
check(proche(E.taux_entropie_empirique(["a", "a", "b", "a", "a", "b"], 1), 0.8, tol=1e-9),
      "'aabaab' -> taux d'ordre 1 = 4/5·1 + 1/5·0 = 0.8 (calcul à la main)")
check(proche(E.taux_entropie_empirique(["a", "a", "a", "a"], 1), 0.0),
      "symbole répété -> taux conditionnel = 0")
# le conditionnel ne dépasse pas le marginal (borne informationnelle)
seq_mix = ["a", "b", "a", "a", "b", "b", "a", "b"]
marg, _ = E.entropie_empirique(seq_mix)
check(E.taux_entropie_empirique(seq_mix, 1) <= marg + 1e-9, "taux conditionnel ≤ entropie marginale")

# ── 7) π NON STATIONNAIRE -> ValueError (abstention, la garde qui rend le taux honnête) ──
# [0.99,0.01] avec P symétrique : πP = [0.892,0.108] ≠ π -> abstention (calcul à la main de πP).
check(leve(E.entropie_conditionnelle_markov, [[0.9, 0.1], [0.1, 0.9]], [0.99, 0.01]),
      "π non stationnaire (πP≠π) -> ValueError")
# CONTRE-EXEMPLE de l'auditeur : P=[[0.5,0.5],[0.25,0.75]] avec π=[0.5,0.5] ; πP=[0.375,0.625]≠π.
# L'ancien invariant 'taux ≤ H(π)' ne l'attrapait PAS (taux≈0.906 ≤ 1). La garde πP=π l'attrape.
check(leve(E.entropie_conditionnelle_markov, [[0.5, 0.5], [0.25, 0.75]], [0.5, 0.5]),
      "contre-exemple auditeur : π=[0.5,0.5] non stationnaire pour P asym -> ValueError (pas un taux faux)")
# le VRAI stationnaire (1/3,2/3) pour cette même P ne lève PAS (garde n'est pas trop stricte) :
check(proche(E.entropie_conditionnelle_markov([[0.5, 0.5], [0.25, 0.75]], [Fraction(1, 3), Fraction(2, 3)]),
             taux_asym_main, tol=1e-9),
      "π stationnaire correct (1/3,2/3) accepté -> taux exact (garde non sur-stricte)")

# ── 8) SOUNDNESS — séquences ──
check(leve(E.entropie_empirique, []), "séquence vide -> ValueError")
check(leve(E.entropie_empirique, "abc"), "str (non liste/tuple) -> ValueError")
check(leve(E.entropie_empirique, [[1], [2]]), "symbole non hashable (liste) -> ValueError")
check(leve(E.correction_miller_madow, []), "MM séquence vide -> ValueError")
check(leve(E.fiable, ["a"], []), "alphabet vide -> ValueError")
check(leve(E.fiable, [], ["a"]), "fiable séquence vide -> ValueError")

# ── 9) SOUNDNESS — matrice de transition ──
check(leve(E.distribution_stationnaire, [[0.9, 0.1], [0.2, 0.9]]), "ligne somme≠1 -> ValueError")
check(leve(E.distribution_stationnaire, [[0.9, 0.1, 0.0], [0.1, 0.9, 0.0]]), "matrice non carrée -> ValueError")
check(leve(E.distribution_stationnaire, [[True, 0.1], [0.1, 0.9]]), "entrée bool -> ValueError")
check(leve(E.distribution_stationnaire, [["x", 0.1], [0.1, 0.9]]), "entrée str -> ValueError")
check(leve(E.distribution_stationnaire, [[float("nan"), 0.1], [0.1, 0.9]]), "entrée NaN -> ValueError")
check(leve(E.distribution_stationnaire, [[float("inf"), 0.1], [0.1, 0.9]]), "entrée inf -> ValueError")
check(leve(E.distribution_stationnaire, [[1.5, -0.5], [0.1, 0.9]]), "entrée hors [0,1] -> ValueError")
check(leve(E.distribution_stationnaire, []), "matrice vide -> ValueError")

# ── 10) SOUNDNESS — distribution fournie / matrice pour le taux ──
check(leve(E.entropie_conditionnelle_markov, [[0.9, 0.1], [0.1, 0.9]], [0.5]), "π taille incompatible -> ValueError")
check(leve(E.entropie_conditionnelle_markov, [[0.9, 0.1], [0.1, 0.9]], [0.6, 0.6]), "π ne somme pas à 1 -> ValueError")
check(leve(E.entropie_conditionnelle_markov, [[0.9, 0.1], [0.1, 0.9]], [1.2, -0.2]), "π négative -> ValueError")
check(leve(E.entropie_conditionnelle_markov, [[0.9, 0.1], [0.2, 0.9]], [0.5, 0.5]), "matrice non stochastique -> ValueError")

# ── 11) SOUNDNESS — ordre / longueur du taux empirique ──
check(leve(E.taux_entropie_empirique, ["a", "b"], 0), "ordre 0 -> ValueError")
check(leve(E.taux_entropie_empirique, ["a", "b"], True), "ordre bool -> ValueError")
check(leve(E.taux_entropie_empirique, ["a", "b"], 1.0), "ordre float -> ValueError")
check(leve(E.taux_entropie_empirique, ["a"], 1), "séquence trop courte pour l'ordre -> ValueError")
check(leve(E.taux_entropie_empirique, [], 1), "taux séquence vide -> ValueError")

# ── 12) DÉTERMINISME ──
check(E.entropie_empirique(["a", "b", "a"]) == E.entropie_empirique(["a", "b", "a"]), "déterminisme entropie_empirique")
check(E.distribution_stationnaire([[0.9, 0.1], [0.1, 0.9]])
      == E.distribution_stationnaire([[0.9, 0.1], [0.1, 0.9]]), "déterminisme stationnaire")
check(E.taux_entropie_empirique(["a", "a", "b", "a", "a", "b"], 1)
      == E.taux_entropie_empirique(["a", "a", "b", "a", "a", "b"], 1), "déterminisme taux empirique")
check(E.correction_miller_madow(seq20) == E.correction_miller_madow(seq20), "déterminisme Miller-Madow")

print(f"\n=== valide_entropie_source : {ok}/{ok+ko} ===")
import sys
sys.exit(0 if ko == 0 else 1)
