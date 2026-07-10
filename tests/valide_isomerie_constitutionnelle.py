"""
VALIDE isomerie_constitutionnelle.py — held-out ADVERSE.

ANCRES EXTERNES NON CIRCULAIRES (valeurs connues, PAS recalculées par le code testé) :
  • Suite OEIS A000602 (nombre d'isomères constitutionnels des alcanes CnH2n+2), valeurs universellement
    tabulées, écrites EN DUR : n=1:1 (méthane), 2:1, 3:1, 4:2 (butane/isobutane), 5:3, 6:5, 7:9, 8:18,
    9:35, 10:75, 11:159, 12:355. Aucune formule close ne les donne — seule une énumération correcte les
    retrouve. C'est l'ancre parfaite pour un dénombrement par énumération.
  • Certificats AHU CALCULÉS À LA MAIN (dérivation écrite ci-dessous, indépendante du code) :
      – n=4, chaîne P4 (butane) : centres = les 2 sommets du milieu ; enraciné en l'un : enfants =
        feuille "()" et chaîne pendante "(())" ; tri lexicographique -> "(())"+"()" -> "((())())".
      – n=4, étoile K1,3 (isobutane) : centre = le moyeu ; 3 feuilles "()" -> "(()()())".
      – n=5, étoile K1,4 (néopentane, degré 4 ATTEINT donc légal) : 4 feuilles -> "(()()()())".
      – n=5, chaîne P5 (pentane) : centre = milieu ; 2 chaînes pendantes "(())" -> "((())(()))".
  • FILTRE DE VALENCE : l'étoile K1,5 (moyeu de degré 5) est un ARBRE à 6 sommets mais PAS un alcane ;
    son certificat "(()()()()())" ne doit PAS apparaître dans squelettes_alcane(6). Idem K1,6 pour n=7.
    (Sans le filtre degré ≤ 4, on compterait A000055 : 11 arbres à 7 sommets au lieu de 9 alcanes.)

SOUNDNESS : n non-int/bool/float/str, n<1, n>12 (budget), formule non alcane (C2H4, C6H6…), formule mal
formée (casse, zéros de tête, espaces, non-str) -> ValueError. DÉTERMINISME : double appel identique.
"""
import isomerie_constitutionnelle as I

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


def message(fn, *a):
    """Le message de la ValueError levée, ou '' si rien n'est levé."""
    try:
        fn(*a)
        return ""
    except ValueError as e:
        return str(e)


# ── 1) ANCRE OEIS A000602 — les 12 valeurs tabulées, EN DUR ──
A000602 = {1: 1, 2: 1, 3: 1, 4: 2, 5: 3, 6: 5, 7: 9, 8: 18, 9: 35, 10: 75, 11: 159, 12: 355}
for n, attendu in A000602.items():
    check(I.nombre_isomeres_alcane(n) == attendu, f"A000602 : n={n} -> {attendu} isomères")

# ── 2) ANCRE via la formule brute (délégation) ──
check(I.nombre_isomeres("CH4") == 1, "CH4 (méthane) -> 1")
check(I.nombre_isomeres("C1H4") == 1, "C1H4 == CH4 -> 1")
check(I.nombre_isomeres("C4H10") == 2, "C4H10 (butane/isobutane) -> 2")
check(I.nombre_isomeres("C5H12") == 3, "C5H12 -> 3")
check(I.nombre_isomeres("C6H14") == 5, "C6H14 -> 5")
check(I.nombre_isomeres("C8H18") == 18, "C8H18 -> 18")
check(I.nombre_isomeres("C10H22") == 75, "C10H22 -> 75")
check(I.nombre_isomeres("C12H26") == 355, "C12H26 -> 355")

# ── 3) ANCRE STRUCTURELLE — certificats AHU dérivés À LA MAIN (cf. docstring) ──
sq4 = I.squelettes_alcane(4)
check(set(sq4) == {"((())())", "(()()())"},
      "n=4 : exactement {chaîne P4, étoile K1,3} (certificats calculés à la main)")
sq5 = I.squelettes_alcane(5)
check("(()()()())" in sq5, "n=5 : néopentane K1,4 présent (degré 4 atteint = légal)")
check("((())(()))" in sq5, "n=5 : pentane P5 présent (certificat calculé à la main)")
check(len(sq5) == 3, "n=5 : 3 squelettes (2-méthylbutane = le troisième)")
check(I.squelettes_alcane(1) == ["()"], "n=1 : le sommet isolé, certificat '()'")
check(I.squelettes_alcane(2) == ["(())"], "n=2 : l'arête unique, certificat '(())'")
check(I.squelettes_alcane(3) == ["(()())"], "n=3 : la chaîne P3, certificat '(()())'")

# ── 4) FILTRE DE VALENCE (degré ≤ 4) — les étoiles trop branchues sont EXCLUES ──
check("(()()()()())" not in I.squelettes_alcane(6), "n=6 : K1,5 (degré 5) exclue")
check("(()()()()()())" not in I.squelettes_alcane(7), "n=7 : K1,6 (degré 6) exclue")
check(I.nombre_isomeres_alcane(7) == 9, "n=7 : 9 (≠ 11 = A000055 sans filtre de valence)")

# ── 5) COHÉRENCE INTERNE des squelettes (pas une ancre : garde-fous structurels) ──
for n in (4, 6, 8):
    sq = I.squelettes_alcane(n)
    check(len(sq) == I.nombre_isomeres_alcane(n), f"n={n} : len(squelettes) == nombre_isomeres")
    check(len(set(sq)) == len(sq), f"n={n} : certificats tous distincts")
    check(sq == sorted(sq), f"n={n} : liste triée (sortie canonique)")
    check(all(len(c) == 2 * n for c in sq), f"n={n} : chaque certificat a 2n caractères (n paires)")
    check(all(c.count("(") == n and c.count(")") == n for c in sq),
          f"n={n} : parenthésage équilibré (n ouvrantes, n fermantes)")

# ── 6) SOUNDNESS — n hors domaine ou mal typé ──
check(leve(I.nombre_isomeres_alcane, 0), "n=0 -> ValueError")
check(leve(I.nombre_isomeres_alcane, -1), "n=-1 -> ValueError")
check(leve(I.nombre_isomeres_alcane, 13), "n=13 (> budget 12) -> ValueError")
check(leve(I.nombre_isomeres_alcane, True), "n=True (bool) -> ValueError")
check(leve(I.nombre_isomeres_alcane, 4.0), "n=4.0 (float) -> ValueError")
check(leve(I.nombre_isomeres_alcane, float("nan")), "n=NaN -> ValueError")
check(leve(I.nombre_isomeres_alcane, float("inf")), "n=inf -> ValueError")
check(leve(I.nombre_isomeres_alcane, "4"), "n='4' (str) -> ValueError")
check(leve(I.nombre_isomeres_alcane, None), "n=None -> ValueError")
check(leve(I.squelettes_alcane, 0), "squelettes n=0 -> ValueError")
check(leve(I.squelettes_alcane, 13), "squelettes n=13 -> ValueError")
check(leve(I.squelettes_alcane, True), "squelettes n=True -> ValueError")

# ── 7) SOUNDNESS — formules NON alcanes (abstention explicite) ──
check(leve(I.nombre_isomeres, "C2H4"), "C2H4 (éthylène) -> ValueError")
check(leve(I.nombre_isomeres, "C6H6"), "C6H6 (benzène) -> ValueError")
check(leve(I.nombre_isomeres, "C2H2"), "C2H2 (acétylène) -> ValueError")
check(leve(I.nombre_isomeres, "C6H12"), "C6H12 (cyclohexane) -> ValueError")
check(leve(I.nombre_isomeres, "H2O"), "H2O -> ValueError")
check("hors périmètre" in message(I.nombre_isomeres, "C6H6"),
      "message C6H6 contient 'hors périmètre'")
check("hors périmètre" in message(I.nombre_isomeres, "C2H4"),
      "message C2H4 contient 'hors périmètre'")

# ── 8) SOUNDNESS — formules mal formées / mal typées / hors budget ──
check(leve(I.nombre_isomeres, ""), "formule vide -> ValueError")
check(leve(I.nombre_isomeres, "c4h10"), "minuscules -> ValueError")
check(leve(I.nombre_isomeres, "C04H10"), "zéro de tête (C04H10) -> ValueError")
check(leve(I.nombre_isomeres, "C4H010"), "zéro de tête (C4H010) -> ValueError")
check(leve(I.nombre_isomeres, "C0H2"), "C0H2 (n=0) -> ValueError")
check(leve(I.nombre_isomeres, " C4H10"), "espace de tête -> ValueError")
check(leve(I.nombre_isomeres, "C4H10 "), "espace de queue -> ValueError")
check(leve(I.nombre_isomeres, "C13H28"), "C13H28 (alcane mais n>12, budget) -> ValueError")
check(leve(I.nombre_isomeres, 4), "formule=4 (int) -> ValueError")
check(leve(I.nombre_isomeres, None), "formule=None -> ValueError")
check(leve(I.nombre_isomeres, True), "formule=True (bool) -> ValueError")

# ── 9) DÉTERMINISME ──
check(I.nombre_isomeres_alcane(8) == I.nombre_isomeres_alcane(8), "déterminisme nombre (n=8)")
check(I.squelettes_alcane(6) == I.squelettes_alcane(6), "déterminisme squelettes (n=6)")
check(I.nombre_isomeres("C7H16") == I.nombre_isomeres("C7H16"), "déterminisme formule (C7H16)")

print(f"\n=== valide_isomerie_constitutionnelle : {ok}/{ok+ko} ===")
import sys; sys.exit(0 if ko == 0 else 1)
