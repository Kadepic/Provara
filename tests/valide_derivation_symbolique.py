"""
VALIDE derivation_symbolique.py — held-out ADVERSE (FAUX=0).

ANCRES NON CIRCULAIRES (attendu connu INDÉPENDAMMENT de la fonction testée) :
  • Règles UNIVERSELLES de dérivation, écrites À LA MAIN comme arbres attendus et confrontées par ÉVALUATION :
      d/dx(x²)=2x ; d/dx(sin x)=cos x ; d/dx(exp x)=exp x ; d/dx(ln x)=1/x ;
      d/dx(x·sin x)=sin x + x·cos x (Leibniz) ; d/dx(sin(x²))=2x·cos(x²) (chaîne) ; d/dx(x/(x+1))=1/(x+1)² (quotient).
  • VÉRIFICATION NUMÉRIQUE par CHEMIN DE CODE DISTINCT : taux d'accroissement CENTRÉ (f(x+h)−f(x−h))/(2h),
    h=1e-6, sur 8 expressions × 20 points ; la dérivée symbolique évaluée doit coïncider à 1e-4 près.
  • PRIMITIVES confrontées à leurs valeurs classiques : ∫x²=x³/3 ; ∫cos=sin ; ∫1/x=ln|x| ; ∫exp(2x)=exp(2x)/2.
  • BOUCLE FERMÉE : derive(primitive(f)) == f (numériquement) pour toutes les formes du catalogue.
  • ABSTENTION : primitive(exp(−x²)) -> ValueError (pas de primitive élémentaire) ; nœud inconnu ; exposant non
    entier ; const flottant/booléen ; domaine invalide à l'évaluation.
"""
import math

import derivation_symbolique as D
from derivation_symbolique import cst, VAR

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


def egal(x, y, tol=1e-9):
    return x is not None and y is not None and abs(x - y) <= tol


def eq_num(e1, e2, pts):
    """True ssi e1 et e2 s'évaluent identiquement (à 1e-9) sur tous les points pts."""
    for p in pts:
        if not egal(D.evalue(e1, p), D.evalue(e2, p), 1e-9):
            return False
    return True


PTS = [0.2 + 0.04 * i for i in range(20)]   # 0.20 .. 0.96 : < π/2, > 0 (ln, sqrt, tan, /(x+1) tous définis)

# raccourcis d'arbres
X = VAR
X2 = ("^", X, 2)


# ════════════════════════════════════════════════════════════════════════════════════════════════════════════════
# 1) DÉRIVÉES DE BASE — attendu écrit À LA MAIN (ancre universelle), confronté par évaluation
# ════════════════════════════════════════════════════════════════════════════════════════════════════════════════
# d/dx(x²) = 2x  (attendu bâti main : 2·x)
check(eq_num(D.derive(X2), ("*", cst(2), X), PTS), "d/dx(x^2) = 2x")
# structure aussi propre après simplification
check(D.derive(X2) == ("*", ("const", __import__("fractions").Fraction(2)), ("var",)),
      "d/dx(x^2) simplifiée == 2*x (structurel)")

# d/dx(sin x) = cos x
check(D.derive(("sin", X)) == ("cos", X), "d/dx(sin x) = cos x (structurel)")
check(eq_num(D.derive(("sin", X)), ("cos", X), PTS), "d/dx(sin x) = cos x (num)")

# d/dx(exp x) = exp x
check(D.derive(("exp", X)) == ("exp", X), "d/dx(exp x) = exp x (structurel)")

# d/dx(ln x) = 1/x
check(eq_num(D.derive(("ln", X)), ("/", cst(1), X), PTS), "d/dx(ln x) = 1/x")

# d/dx(cos x) = -sin x
check(eq_num(D.derive(("cos", X)), ("*", cst(-1), ("sin", X)), PTS), "d/dx(cos x) = -sin x")

# d/dx(sqrt x) = 1/(2 sqrt x)
check(eq_num(D.derive(("sqrt", X)), ("/", cst(1), ("*", cst(2), ("sqrt", X))), PTS), "d/dx(sqrt x) = 1/(2 sqrt x)")

# d/dx(tan x) = 1/cos^2 x
check(eq_num(D.derive(("tan", X)), ("/", cst(1), ("^", ("cos", X), 2)), PTS), "d/dx(tan x) = 1/cos^2 x")

# d/dx(atan x) = 1/(1+x^2)
check(eq_num(D.derive(("atan", X)), ("/", cst(1), ("+", cst(1), X2)), PTS), "d/dx(atan x) = 1/(1+x^2)")


# ════════════════════════════════════════════════════════════════════════════════════════════════════════════════
# 2) RÈGLES COMPOSÉES — Leibniz, chaîne, quotient (attendus bâtis main)
# ════════════════════════════════════════════════════════════════════════════════════════════════════════════════
# d/dx(x·sin x) = sin x + x·cos x
f_prod = ("*", X, ("sin", X))
att_prod = ("+", ("sin", X), ("*", X, ("cos", X)))
check(eq_num(D.derive(f_prod), att_prod, PTS), "Leibniz : d/dx(x sin x) = sin x + x cos x")

# d/dx(sin(x²)) = 2x·cos(x²)
f_ch = ("sin", X2)
att_ch = ("*", ("*", cst(2), X), ("cos", X2))
check(eq_num(D.derive(f_ch), att_ch, PTS), "chaîne : d/dx(sin(x^2)) = 2x cos(x^2)")

# d/dx(x/(x+1)) = 1/(x+1)²
f_q = ("/", X, ("+", X, cst(1)))
att_q = ("/", cst(1), ("^", ("+", X, cst(1)), 2))
check(eq_num(D.derive(f_q), att_q, PTS), "quotient : d/dx(x/(x+1)) = 1/(x+1)^2")

# d/dx(exp(x²)) = 2x·exp(x²)  (chaîne)
check(eq_num(D.derive(("exp", X2)), ("*", ("*", cst(2), X), ("exp", X2)), PTS),
      "chaîne : d/dx(exp(x^2)) = 2x exp(x^2)")


# ════════════════════════════════════════════════════════════════════════════════════════════════════════════════
# 3) VÉRIF NUMÉRIQUE INDÉPENDANTE — dérivée symbolique vs taux d'accroissement CENTRÉ (chemin distinct)
# ════════════════════════════════════════════════════════════════════════════════════════════════════════════════
H = 1e-6
EXPRS = [
    X2,                       # x²
    ("sin", X),               # sin x
    ("exp", X),               # exp x
    ("ln", X),                # ln x
    ("*", X, ("sin", X)),     # x·sin x
    ("sin", X2),              # sin(x²)
    ("/", X, ("+", X, cst(1))),  # x/(x+1)
    ("sqrt", X),              # √x
]
for e in EXPRS:
    de = D.derive(e)
    tous = True
    for p in PTS:
        symb = D.evalue(de, p)
        centre = (D.evalue(e, p + H) - D.evalue(e, p - H)) / (2 * H)   # DIFFÉRENCE CENTRÉE indépendante
        if abs(symb - centre) > 1e-4:
            tous = False
            break
    check(tous, f"dérivée symbolique ≈ différence centrée sur 20 pts : {D.vers_texte(e)}")


# ════════════════════════════════════════════════════════════════════════════════════════════════════════════════
# 4) PRIMITIVES — valeurs classiques (ancres numériques calculées à la main)
# ════════════════════════════════════════════════════════════════════════════════════════════════════════════════
# ∫x² = x³/3 : en x=2 -> 8/3
check(egal(D.evalue(D.primitive(X2), 2.0), 8.0 / 3.0, 1e-9), "∫x^2 en x=2 = 8/3")
# ∫cos = sin : en x=0.7 -> sin(0.7)
check(egal(D.evalue(D.primitive(("cos", X)), 0.7), math.sin(0.7), 1e-9), "∫cos en x=0.7 = sin(0.7)")
# ∫1/x = ln|x| : en x=2 -> ln 2
check(egal(D.evalue(D.primitive(("/", cst(1), X)), 2.0), math.log(2.0), 1e-9), "∫1/x en x=2 = ln 2")
# ∫exp(2x) = exp(2x)/2 : en x=1 -> e²/2
f_e2 = ("exp", ("*", cst(2), X))
check(egal(D.evalue(D.primitive(f_e2), 1.0), math.exp(2.0) / 2.0, 1e-9), "∫exp(2x) en x=1 = e^2/2")
# ∫1/(1+x²) = atan x : en x=1 -> π/4
check(egal(D.evalue(D.primitive(("/", cst(1), ("+", cst(1), X2))), 1.0), math.pi / 4, 1e-9),
      "∫1/(1+x^2) en x=1 = π/4")


# ════════════════════════════════════════════════════════════════════════════════════════════════════════════════
# 5) BOUCLE FERMÉE — derive(primitive(f)) == f (numériquement) pour tout le catalogue
# ════════════════════════════════════════════════════════════════════════════════════════════════════════════════
CATALOGUE = [
    X2,                                # x²
    ("cos", X),                        # cos x
    ("/", cst(1), X),                  # 1/x
    ("exp", ("*", cst(2), X)),         # exp(2x)
    cst(5),                            # constante
    ("^", X, 5),                       # x^5
    ("^", ("+", ("*", cst(2), X), cst(1)), 3),   # (2x+1)^3  (substitution affine)
    ("sin", ("+", ("*", cst(3), X), cst(1))),    # sin(3x+1)
    ("cos", ("*", cst(2), X)),         # cos(2x)
    ("exp", ("-", cst(0), X)),         # exp(-x)
    ("/", cst(1), ("+", cst(1), X2)),  # 1/(1+x²)
    ("/", cst(1), ("+", X, cst(1))),   # 1/(x+1)
    ("+", ("*", cst(3), X2), ("+", ("*", cst(2), X), cst(1))),  # 3x²+2x+1 (linéarité)
]
for f in CATALOGUE:
    P = D.primitive(f)
    check(eq_num(D.derive(P), f, PTS), f"boucle fermée derive(primitive) == f : {D.vers_texte(f)}")


# ════════════════════════════════════════════════════════════════════════════════════════════════════════════════
# 6) SIMPLIFICATION — réductions sûres
# ════════════════════════════════════════════════════════════════════════════════════════════════════════════════
check(D.simplifie(("+", cst(0), X)) == X, "0 + x = x")
check(D.simplifie(("+", X, cst(0))) == X, "x + 0 = x")
check(D.simplifie(("-", X, cst(0))) == X, "x - 0 = x")
check(D.simplifie(("*", cst(0), ("sin", X))) == cst(0), "0 * f = 0")
check(D.simplifie(("*", cst(1), X)) == X, "1 * x = x")
check(D.simplifie(("*", X, cst(1))) == X, "x * 1 = x")
check(D.simplifie(("/", X, cst(1))) == X, "x / 1 = x")
check(D.simplifie(("/", cst(0), X)) == cst(0), "0 / x = 0")
check(D.simplifie(("^", X, 1)) == X, "x^1 = x")
check(D.simplifie(("^", X, 0)) == cst(1), "x^0 = 1")
check(D.simplifie(("+", cst(2), cst(3))) == cst(5), "2 + 3 = 5 (const)")
check(D.simplifie(("*", cst(2), cst(3))) == cst(6), "2 * 3 = 6 (const)")
check(D.simplifie(("/", cst(6), cst(4))) == cst(3, 2), "6/4 = 3/2 (Fraction exacte)")
check(D.simplifie(("^", cst(2), 3)) == cst(8), "2^3 = 8 (const)")


# ════════════════════════════════════════════════════════════════════════════════════════════════════════════════
# 7) VERS_TEXTE
# ════════════════════════════════════════════════════════════════════════════════════════════════════════════════
check(D.vers_texte(X) == "x", "texte var")
check(D.vers_texte(cst(3, 2)) == "3/2", "texte const fraction")
check(D.vers_texte(("sin", X)) == "sin(x)", "texte sin")
check(D.vers_texte(("^", X, 2)) == "(x)^2", "texte puissance")


# ════════════════════════════════════════════════════════════════════════════════════════════════════════════════
# 8) ABSTENTION — primitives hors catalogue (FAUX=0 : on ne devine JAMAIS)
# ════════════════════════════════════════════════════════════════════════════════════════════════════════════════
check(leve(D.primitive, ("exp", ("*", cst(-1), X2))), "∫exp(-x²) -> ValueError (pas élémentaire)")
check(leve(D.primitive, ("exp", X2)), "∫exp(x²) -> ValueError")
check(leve(D.primitive, ("*", X, ("sin", X))), "∫x·sin x -> ValueError (par parties non implémentée)")
check(leve(D.primitive, ("ln", X)), "∫ln x -> ValueError (hors catalogue)")
check(leve(D.primitive, ("tan", X)), "∫tan x -> ValueError")
check(leve(D.primitive, ("sqrt", X)), "∫sqrt x -> ValueError (exposant non entier)")
check(leve(D.primitive, ("sin", X2)), "∫sin(x²) -> ValueError (argument non affine)")
check(leve(D.primitive, ("/", cst(1), X2)), "∫1/x² via division non affine -> ValueError")


# ════════════════════════════════════════════════════════════════════════════════════════════════════════════════
# 9) ABSTENTION — structure / types invalides
# ════════════════════════════════════════════════════════════════════════════════════════════════════════════════
check(leve(D.derive, ("cosh", X)), "noeud inconnu -> ValueError (derive)")
check(leve(D.derive, ("^", X, 1.5)), "exposant non entier -> ValueError")
check(leve(D.derive, ("^", X, True)), "exposant booléen -> ValueError")
check(leve(D.derive, ("const", 1.5)), "const flottant -> ValueError")
check(leve(D.derive, ("const", True)), "const booléen -> ValueError")
check(leve(D.derive, ("const", "1")), "const chaîne -> ValueError")
check(leve(D.derive, ("+", X)), "arité + insuffisante -> ValueError")
check(leve(D.derive, ("sin", X, X)), "arité sin excédentaire -> ValueError")
check(leve(D.derive, ("var", X)), "var avec argument -> ValueError")
check(leve(D.derive, "x"), "expression non tuple -> ValueError")
check(leve(D.simplifie, ("foo",)), "simplifie noeud inconnu -> ValueError")
check(leve(D.vers_texte, ("bar", X)), "vers_texte noeud inconnu -> ValueError")


# ════════════════════════════════════════════════════════════════════════════════════════════════════════════════
# 10) ABSTENTION — évaluation hors domaine
# ════════════════════════════════════════════════════════════════════════════════════════════════════════════════
check(leve(D.evalue, ("ln", X), -1.0), "ln(-1) -> ValueError")
check(leve(D.evalue, ("ln", X), 0.0), "ln(0) -> ValueError")
check(leve(D.evalue, ("sqrt", X), -2.0), "sqrt(-2) -> ValueError")
check(leve(D.evalue, ("/", cst(1), X), 0.0), "1/0 -> ValueError")
check(leve(D.evalue, ("tan", X), math.pi / 2), "tan(π/2) -> ValueError")
check(leve(D.evalue, ("^", X, -1), 0.0), "0^(-1) -> ValueError")
check(leve(D.evalue, X, True), "x booléen -> ValueError")
check(leve(D.evalue, X, float("nan")), "x = NaN -> ValueError")
check(leve(D.evalue, X, float("inf")), "x = inf -> ValueError")
check(leve(D.evalue, X, "0.5"), "x chaîne -> ValueError")

# cst : garde-fous
check(leve(cst, 1.5), "cst flottant -> ValueError")
check(leve(cst, True), "cst booléen -> ValueError")
check(leve(cst, 1, 0), "cst dénominateur nul -> ValueError")


# ════════════════════════════════════════════════════════════════════════════════════════════════════════════════
# 11) DÉTERMINISME
# ════════════════════════════════════════════════════════════════════════════════════════════════════════════════
check(D.derive(f_prod) == D.derive(f_prod), "déterminisme derive")
check(D.primitive(X2) == D.primitive(X2), "déterminisme primitive")
check(D.evalue(("sin", X), 0.5) == D.evalue(("sin", X), 0.5), "déterminisme evalue")


print(f"\n=== valide_derivation_symbolique : {ok}/{ok+ko} ===")
import sys
sys.exit(0 if ko == 0 else 1)
