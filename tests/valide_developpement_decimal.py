"""
VALIDE developpement_decimal.py — held-out ADVERSE.

ANCRES EXTERNES NON CIRCULAIRES (valeurs classiques écrites EN DUR, jamais recalculées par le code testé) :
  • 1/2 = 0.5 (fini) ; 3/8 = 0.375 (fini) ; 1/4 = 0.25 ; 1/20 = 0.05 (préfixe '05').
  • 1/3 = 0.(3) période 1 ; 1/7 = 0.(142857) période 6 (142857 = nombre cyclique bien connu) ;
    1/6 = 0.1(6) ; 22/7 = 3.(142857) ; 1/11 = 0.(09) période 2 ; 1/13 = 0.(076923) période 6 ;
    1/17 = 0.(0588235294117647) période 16 (période maximale, 10 racine primitive mod 17) ;
    1/9 = 0.(1) ; 1/37 = 0.(027) période 3 (27·37 = 999, calcul à la main) ;
    1/101 = 0.(0099) période 4 (99·101 = 9999, calcul à la main) ; 7/12 = 0.58(3).
  • ANCRE EN BOUCLE FERMÉE (second chemin de code) : reconstruit() somme la série géométrique
    entier + prefixe/10^s + periode/((10^t−1)·10^s), chemin INVERSE indépendant de la division
    euclidienne du chemin direct -> reconstruit(developpement(p,q)) == Fraction(p,q) sur > 50 couples.

SOUNDNESS : q=0, bool, float, str, None, Fraction en entrée, q≤0 pour les fonctions de dénominateur,
dicts mal formés pour reconstruit -> ValueError. DÉTERMINISME : double appel identique.
"""
from fractions import Fraction

import developpement_decimal as DD

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


# ── 1) ANCRES FINIES (valeurs décimales connues de tous, en dur) ──
d = DD.developpement(1, 2)
check(d == {'signe': '+', 'entier': 0, 'prefixe': '5', 'periode': '', 'fini': True},
      "1/2 = 0.5 fini")
d = DD.developpement(3, 8)
check(d == {'signe': '+', 'entier': 0, 'prefixe': '375', 'periode': '', 'fini': True},
      "3/8 = 0.375 fini")
d = DD.developpement(1, 4)
check(d == {'signe': '+', 'entier': 0, 'prefixe': '25', 'periode': '', 'fini': True},
      "1/4 = 0.25 fini")
d = DD.developpement(1, 20)
check(d == {'signe': '+', 'entier': 0, 'prefixe': '05', 'periode': '', 'fini': True},
      "1/20 = 0.05 (préfixe '05', zéro de tête conservé)")
d = DD.developpement(5, 1)
check(d == {'signe': '+', 'entier': 5, 'prefixe': '', 'periode': '', 'fini': True},
      "5/1 = 5 (entier pur)")
d = DD.developpement(0, 7)
check(d == {'signe': '+', 'entier': 0, 'prefixe': '', 'periode': '', 'fini': True},
      "0/7 = 0 (signe '+', tout vide)")

# ── 2) ANCRES PÉRIODIQUES (périodes classiques, en dur) ──
d = DD.developpement(1, 3)
check(d == {'signe': '+', 'entier': 0, 'prefixe': '', 'periode': '3', 'fini': False},
      "1/3 = 0.(3)")
d = DD.developpement(1, 7)
check(d == {'signe': '+', 'entier': 0, 'prefixe': '', 'periode': '142857', 'fini': False},
      "1/7 = 0.(142857) — nombre cyclique classique")
d = DD.developpement(1, 6)
check(d == {'signe': '+', 'entier': 0, 'prefixe': '1', 'periode': '6', 'fini': False},
      "1/6 = 0.1(6) : préfixe '1', période '6'")
d = DD.developpement(22, 7)
check(d == {'signe': '+', 'entier': 3, 'prefixe': '', 'periode': '142857', 'fini': False},
      "22/7 = 3.(142857) : partie entière 3")
d = DD.developpement(1, 11)
check(d == {'signe': '+', 'entier': 0, 'prefixe': '', 'periode': '09', 'fini': False},
      "1/11 = 0.(09) : zéro de tête de période conservé")
d = DD.developpement(1, 13)
check(d == {'signe': '+', 'entier': 0, 'prefixe': '', 'periode': '076923', 'fini': False},
      "1/13 = 0.(076923)")
d = DD.developpement(1, 17)
check(d == {'signe': '+', 'entier': 0, 'prefixe': '', 'periode': '0588235294117647', 'fini': False},
      "1/17 = 0.(0588235294117647) : période 16 (maximale)")
d = DD.developpement(1, 9)
check(d == {'signe': '+', 'entier': 0, 'prefixe': '', 'periode': '1', 'fini': False},
      "1/9 = 0.(1)")
d = DD.developpement(7, 12)
check(d == {'signe': '+', 'entier': 0, 'prefixe': '58', 'periode': '3', 'fini': False},
      "7/12 = 0.58(3) : préfixe '58', période '3'")
d = DD.developpement(1, 37)
check(d == {'signe': '+', 'entier': 0, 'prefixe': '', 'periode': '027', 'fini': False},
      "1/37 = 0.(027) car 27·37 = 999 (calcul à la main)")
d = DD.developpement(1, 101)
check(d == {'signe': '+', 'entier': 0, 'prefixe': '', 'periode': '0099', 'fini': False},
      "1/101 = 0.(0099) car 99·101 = 9999 (calcul à la main)")

# ── 3) SIGNE ET RÉDUCTION ──
d = DD.developpement(-22, 7)
check(d == {'signe': '-', 'entier': 3, 'prefixe': '', 'periode': '142857', 'fini': False},
      "-22/7 : signe '-', magnitude 3.(142857)")
d = DD.developpement(22, -7)
check(d['signe'] == '-' and d['entier'] == 3, "22/-7 : signe porté par q")
d = DD.developpement(-22, -7)
check(d['signe'] == '+' and d['entier'] == 3, "-22/-7 : signes opposés s'annulent")
check(DD.developpement(0, -5)['signe'] == '+', "0/-5 : zéro toujours signé '+'")
check(DD.developpement(2, 6) == DD.developpement(1, 3), "2/6 réduit = 1/3 (canonicité)")
check(DD.developpement(50, 100) == DD.developpement(1, 2), "50/100 réduit = 1/2")

# ── 4) LONGUEURS ET FINITUDE (théorème q = 2^a·5^b·q') ──
check(DD.longueur_periode(3) == 1, "période(3) = 1")
check(DD.longueur_periode(7) == 6, "période(7) = 6")
check(DD.longueur_periode(11) == 2, "période(11) = 2")
check(DD.longueur_periode(13) == 6, "période(13) = 6")
check(DD.longueur_periode(17) == 16, "période(17) = 16")
check(DD.longueur_periode(37) == 3, "période(37) = 3")
check(DD.longueur_periode(101) == 4, "période(101) = 4")
check(DD.longueur_periode(2) == 0, "période(2) = 0 (fini)")
check(DD.longueur_periode(1) == 0, "période(1) = 0 (entier)")
check(DD.longueur_periode(6) == 1, "période(6) = période(3) = 1 (facteur 2 sans effet)")
check(DD.longueur_periode(21) == 6, "période(21) = 6 : 1/21 = 0.(047619), ppcm des ordres mod 3 et mod 7")
check(DD.longueur_prefixe(2) == 1, "préfixe(2) = 1")
check(DD.longueur_prefixe(8) == 3, "préfixe(8) = 3 (2^3)")
check(DD.longueur_prefixe(20) == 2, "préfixe(20) = 2 : 20 = 2²·5, max(2,1) = 2")
check(DD.longueur_prefixe(40) == 3, "préfixe(40) = 3 : 40 = 2³·5, max(3,1) = 3")
check(DD.longueur_prefixe(6) == 1, "préfixe(6) = 1 : 6 = 2·3")
check(DD.longueur_prefixe(3) == 0, "préfixe(3) = 0 (purement périodique)")
check(DD.longueur_prefixe(1) == 0, "préfixe(1) = 0")
check(DD.est_fini(2) is True, "est_fini(2)")
check(DD.est_fini(8) is True, "est_fini(8)")
check(DD.est_fini(10) is True, "est_fini(10)")
check(DD.est_fini(25) is True, "est_fini(25)")
check(DD.est_fini(1) is True, "est_fini(1)")
check(DD.est_fini(3) is False, "est_fini(3) faux")
check(DD.est_fini(6) is False, "est_fini(6) faux (facteur 3)")
check(DD.est_fini(7) is False, "est_fini(7) faux")

# ── 5) BOUCLE FERMÉE : reconstruit ∘ developpement = identité (second chemin de code) ──
couples = 0
tous_exacts = True
for q in (1, 2, 3, 4, 6, 7, 8, 9, 11, 12, 13, 14, 15, 17, 20, 21, 24, 37, 41, 97, 101, 700, 999):
    for p in (-23, -1, 0, 1, 5, 22, 355):
        couples += 1
        if DD.reconstruit(DD.developpement(p, q)) != Fraction(p, q):
            tous_exacts = False
            print(f"  FAIL boucle fermée: p={p}, q={q}")
check(tous_exacts, "boucle fermée : reconstruit(developpement(p,q)) == Fraction(p,q) sur tous les couples")
check(couples >= 50, f"au moins 50 couples balayés (vu : {couples})")
# reconstruit sur des dicts écrits À LA MAIN (indépendants de developpement)
check(DD.reconstruit({'signe': '+', 'entier': 0, 'prefixe': '', 'periode': '3', 'fini': False})
      == Fraction(1, 3), "reconstruit(0.(3)) = 1/3 (dict manuel)")
check(DD.reconstruit({'signe': '+', 'entier': 0, 'prefixe': '1', 'periode': '6', 'fini': False})
      == Fraction(1, 6), "reconstruit(0.1(6)) = 1/6 (dict manuel)")
check(DD.reconstruit({'signe': '-', 'entier': 3, 'prefixe': '', 'periode': '142857', 'fini': False})
      == Fraction(-22, 7), "reconstruit(-3.(142857)) = -22/7 (dict manuel)")
check(DD.reconstruit({'signe': '+', 'entier': 0, 'prefixe': '375', 'periode': '', 'fini': True})
      == Fraction(3, 8), "reconstruit(0.375) = 3/8 (dict manuel)")

# ── 6) SOUNDNESS — q = 0 et types invalides pour developpement ──
check(leve(DD.developpement, 1, 0), "q=0 -> ValueError")
check(leve(DD.developpement, 0, 0), "0/0 -> ValueError")
check(leve(DD.developpement, True, 3), "p bool -> ValueError")
check(leve(DD.developpement, 1, True), "q bool -> ValueError")
check(leve(DD.developpement, 1.0, 3), "p float -> ValueError")
check(leve(DD.developpement, 1, 3.0), "q float -> ValueError")
check(leve(DD.developpement, "1", 3), "p str -> ValueError")
check(leve(DD.developpement, 1, "3"), "q str -> ValueError")
check(leve(DD.developpement, None, 3), "p None -> ValueError")
check(leve(DD.developpement, Fraction(1, 3), 1), "p Fraction -> ValueError (entiers stricts)")
check(leve(DD.developpement, float("nan"), 3), "p NaN -> ValueError")
check(leve(DD.developpement, float("inf"), 3), "p inf -> ValueError")
check(leve(DD.developpement, 1, complex(3, 0)), "q complexe -> ValueError")

# ── 7) SOUNDNESS — fonctions du dénominateur seul ──
for fn in (DD.longueur_periode, DD.longueur_prefixe, DD.est_fini):
    nom = fn.__name__
    check(leve(fn, 0), f"{nom}(0) -> ValueError")
    check(leve(fn, -3), f"{nom}(-3) -> ValueError")
    check(leve(fn, True), f"{nom}(bool) -> ValueError")
    check(leve(fn, 3.0), f"{nom}(float) -> ValueError")
    check(leve(fn, "3"), f"{nom}(str) -> ValueError")

# ── 8) SOUNDNESS — reconstruit refuse les dicts mal formés ──
BON = {'signe': '+', 'entier': 0, 'prefixe': '1', 'periode': '6', 'fini': False}
check(DD.reconstruit(BON) == Fraction(1, 6), "dict de référence accepté (sanité)")
check(leve(DD.reconstruit, "0.1(6)"), "reconstruit(str) -> ValueError")
check(leve(DD.reconstruit, None), "reconstruit(None) -> ValueError")
check(leve(DD.reconstruit, {}), "dict vide -> ValueError")
check(leve(DD.reconstruit, {**BON, 'extra': 1}), "clé en trop -> ValueError")
mauvais = dict(BON)
del mauvais['fini']
check(leve(DD.reconstruit, mauvais), "clé manquante -> ValueError")
check(leve(DD.reconstruit, {**BON, 'signe': 'x'}), "signe 'x' -> ValueError")
check(leve(DD.reconstruit, {**BON, 'signe': 1}), "signe non-str -> ValueError")
check(leve(DD.reconstruit, {**BON, 'entier': -1}), "entier négatif (le signe est à part) -> ValueError")
check(leve(DD.reconstruit, {**BON, 'entier': True}), "entier bool -> ValueError")
check(leve(DD.reconstruit, {**BON, 'entier': 1.0}), "entier float -> ValueError")
check(leve(DD.reconstruit, {**BON, 'prefixe': '1a'}), "préfixe non-chiffres -> ValueError")
check(leve(DD.reconstruit, {**BON, 'prefixe': 12}), "préfixe non-str -> ValueError")
check(leve(DD.reconstruit, {**BON, 'periode': '-6'}), "période avec signe -> ValueError")
check(leve(DD.reconstruit, {**BON, 'periode': '٣'}), "période chiffre non-ASCII -> ValueError")
check(leve(DD.reconstruit, {**BON, 'fini': 1}), "fini non-bool (1) -> ValueError")
check(leve(DD.reconstruit, {**BON, 'fini': True}), "fini=True avec période non vide -> ValueError")
check(leve(DD.reconstruit, {**BON, 'periode': '', 'fini': False}), "fini=False sans période -> ValueError")

# ── 9) DÉTERMINISME ──
check(DD.developpement(355, 113) == DD.developpement(355, 113), "déterminisme developpement")
check(DD.longueur_periode(9973) == DD.longueur_periode(9973), "déterminisme longueur_periode")
check(DD.reconstruit(BON) == DD.reconstruit(BON), "déterminisme reconstruit")

print(f"\n=== valide_developpement_decimal : {ok}/{ok+ko} ===")
import sys; sys.exit(0 if ko == 0 else 1)
