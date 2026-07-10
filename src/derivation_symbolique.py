"""
DÉRIVATION & PRIMITIVATION SYMBOLIQUES des fonctions ÉLÉMENTAIRES — FAUX=0 (PARTIE I, B-NEC).

Complément de `calcul_infinitesimal` (qui dérive/intègre EXACTEMENT mais les POLYNÔMES seulement, et qu'on ne
MODIFIE PAS). Ici on manipule un ARBRE d'expression des fonctions élémentaires :

    ('const', Fraction|int) | ('var',) | ('+', a, b) | ('-', a, b) | ('*', a, b) | ('/', a, b)
    | ('^', a, n)  (n entier)  | ('sin', a) | ('cos', a) | ('tan', a) | ('exp', a) | ('ln', a) | ('sqrt', a)
    | ('atan', a)

NB : `atan` (arctangente) est AJOUTÉ à la liste minimale de l'énoncé, faute de quoi ∫ 1/(1+x²) = arctan(x)
— pourtant exigée au catalogue — ne serait PAS représentable ; l'ajouter est la seule façon HONNÊTE de tenir
la boucle fermée derive(primitive(1/(1+x²))) == 1/(1+x²).

MÉCANISME (théorèmes EXACTS, jamais une corrélation) :
  • `derive` : règles UNIVERSELLES de dérivation — linéarité, règle de Leibniz (produit), règle du quotient,
    règle de la chaîne, règle de la puissance (n entier), dérivées des fonctions de base. Résultat = un arbre.
  • `simplifie` : réductions SÛRES seulement (0+x=x, x+0=x, x−0=x, 0·x=0, 1·x=x, x/1=x, 0/x=0, x^1=x, x^0=1,
    const∘const par calcul exact en Fraction). AUCUNE réécriture douteuse (pas de factorisation, pas
    d'identités trigonométriques : elles pourraient introduire un faux hors du domaine).
  • `vers_texte` : rendu lisible.
  • `evalue(expr, x)` : évaluation flottante — le résultat est APPROCHÉ (double précision IEEE-754, marqué tel).
    Abstention de DOMAINE : ln d'un réel ≤ 0, division par zéro, sqrt d'un négatif, tan là où cos=0 -> ValueError.
  • `primitive` : intégration symbolique sur un CATALOGUE FERMÉ de formes reconnues (constante, x, x^n, 1/x,
    1/(ax+b), exp(ax+b), sin/cos(ax+b), 1/(1+x²)) + LINÉARITÉ + facteur constant + substitution AFFINE u=ax+b.
    Toute forme HORS catalogue -> ValueError explicite : on n'INVENTE JAMAIS une primitive (l'intégration
    élémentaire générale exige l'algorithme de Risch, non implémenté). C'est l'abstention centrale FAUX=0.

GARANTIES (vérifiées en adverse par `valide_derivation_symbolique.py`) :
  - dérivées de base confrontées à leurs valeurs UNIVERSELLES connues (d/dx sin = cos, etc.) ;
  - dérivée symbolique confrontée, sur 20 points × plusieurs expressions, au taux d'accroissement CENTRÉ
    (chemin de code indépendant) — coïncidence exigée à 1e-4 près ;
  - primitives confrontées à leurs valeurs classiques ET boucle fermée derive(primitive(f)) == f ;
  - abstentions : nœud inconnu, exposant non entier, const flottant/booléen, domaine invalide à l'évaluation,
    et primitive(exp(−x²)) (qui n'a PAS de primitive élémentaire) -> ValueError ;
  - fonctions PURES et DÉTERMINISTES ; stdlib uniquement (math, fractions) ; faux négatif toléré, faux POSITIF interdit.
"""
from __future__ import annotations

import math
from fractions import Fraction

SOURCE = "règles de dérivation (Leibniz, chaîne, quotient) + table des primitives élémentaires (analyse classique)"

_MSG_PRIM = ("primitive non trouvée : cette forme n'est pas au catalogue ; l'intégration symbolique générale "
             "exige l'algorithme de Risch, non implémenté — cf. integrale_elementaire")

_UNAIRES = ("sin", "cos", "tan", "exp", "ln", "sqrt", "atan")
_BINAIRES = ("+", "-", "*", "/")


# ── constructeurs de confort (purs) ──────────────────────────────────────────────────────────────────────────────
VAR = ("var",)


def cst(num, den: int = 1):
    """Feuille constante ('const', Fraction(num, den)). Refuse bool/float pour rester EXACT."""
    if isinstance(num, bool) or isinstance(den, bool):
        raise ValueError("constante booléenne refusée (True n'est pas 1)")
    if not isinstance(num, int) or not isinstance(den, int):
        raise ValueError("constante : entiers requis (les flottants sont refusés — exactitude)")
    if den == 0:
        raise ValueError("dénominateur de constante nul")
    return ("const", Fraction(num, den))


# ── validation / normalisation de l'arbre ────────────────────────────────────────────────────────────────────────
def _as_fraction(v) -> Fraction:
    if isinstance(v, bool) or not isinstance(v, (int, Fraction)):
        raise ValueError(f"valeur de constante invalide : Fraction ou int attendu, reçu {v!r}")
    return Fraction(v)


def _f(node) -> Fraction:
    """Valeur (Fraction) d'un nœud ('const', v)."""
    return _as_fraction(node[1])


def _verifie(expr):
    """Valide RÉCURSIVEMENT la structure de l'arbre ; renvoie expr. Toute anomalie -> ValueError (abstention)."""
    if not isinstance(expr, tuple) or len(expr) == 0 or not isinstance(expr[0], str):
        raise ValueError(f"expression mal formée : tuple non vide (tag, ...) attendu, reçu {expr!r}")
    tag = expr[0]
    if tag == "const":
        if len(expr) != 2:
            raise ValueError("('const', v) attend exactement une valeur")
        _as_fraction(expr[1])  # refuse bool/float/str
        return expr
    if tag == "var":
        if len(expr) != 1:
            raise ValueError("('var',) n'a pas d'argument")
        return expr
    if tag in _BINAIRES:
        if len(expr) != 3:
            raise ValueError(f"opérateur binaire {tag!r} : deux opérandes requis")
        _verifie(expr[1])
        _verifie(expr[2])
        return expr
    if tag == "^":
        if len(expr) != 3:
            raise ValueError("('^', a, n) attend une base et un exposant")
        _verifie(expr[1])
        n = expr[2]
        if isinstance(n, bool) or not isinstance(n, int):
            raise ValueError("exposant non entier : la règle de puissance implémentée exige un exposant ENTIER")
        return expr
    if tag in _UNAIRES:
        if len(expr) != 2:
            raise ValueError(f"fonction {tag!r} : un seul argument requis")
        _verifie(expr[1])
        return expr
    raise ValueError(f"noeud inconnu (abstention) : {tag!r}")


# ── simplification (réductions SÛRES uniquement) ─────────────────────────────────────────────────────────────────
def _is_const(e) -> bool:
    return e[0] == "const"


def _is_val(e, v) -> bool:
    return e[0] == "const" and _f(e) == v


def simplifie(expr):
    """Réductions sûres seulement (voir docstring de module). Aucune réécriture douteuse."""
    expr = _verifie(expr)
    tag = expr[0]
    if tag in ("const", "var"):
        return expr
    if tag == "^":
        a = simplifie(expr[1])
        n = expr[2]
        if n == 1:
            return a
        if n == 0:
            return ("const", Fraction(1))
        if _is_const(a):
            base = _f(a)
            if base == 0 and n < 0:
                return ("^", a, n)  # 0^négatif indéfini : laissé tel quel, `evalue` s'abstiendra
            return ("const", base ** n)
        return ("^", a, n)
    if tag in _UNAIRES:
        return (tag, simplifie(expr[1]))
    # binaires
    a = simplifie(expr[1])
    b = simplifie(expr[2])
    if tag == "+":
        if _is_val(a, 0):
            return b
        if _is_val(b, 0):
            return a
        if _is_const(a) and _is_const(b):
            return ("const", _f(a) + _f(b))
        return ("+", a, b)
    if tag == "-":
        if _is_val(b, 0):
            return a
        if _is_const(a) and _is_const(b):
            return ("const", _f(a) - _f(b))
        return ("-", a, b)
    if tag == "*":
        if _is_val(a, 0) or _is_val(b, 0):
            return ("const", Fraction(0))
        if _is_val(a, 1):
            return b
        if _is_val(b, 1):
            return a
        if _is_const(a) and _is_const(b):
            return ("const", _f(a) * _f(b))
        return ("*", a, b)
    # tag == "/"
    if _is_val(a, 0):
        if not (_is_const(b) and _f(b) == 0):
            return ("const", Fraction(0))  # 0/b = 0 sur son domaine (b ≠ 0)
        return ("/", a, b)                  # 0/0 : laissé tel quel
    if _is_val(b, 1):
        return a
    if _is_const(a) and _is_const(b):
        if _f(b) == 0:
            return ("/", a, b)              # division par 0 : laissée à l'évaluation
        return ("const", _f(a) / _f(b))
    return ("/", a, b)


# ── dérivation symbolique ────────────────────────────────────────────────────────────────────────────────────────
def derive(expr):
    """Dérivée symbolique EXACTE (arbre). Règles universelles ; résultat simplifié par réductions sûres."""
    expr = _verifie(expr)
    tag = expr[0]
    if tag == "const":
        return ("const", Fraction(0))
    if tag == "var":
        return ("const", Fraction(1))
    if tag == "+":
        return simplifie(("+", derive(expr[1]), derive(expr[2])))
    if tag == "-":
        return simplifie(("-", derive(expr[1]), derive(expr[2])))
    if tag == "*":                                   # Leibniz : (uv)' = u'v + uv'
        a, b = expr[1], expr[2]
        return simplifie(("+", ("*", derive(a), b), ("*", a, derive(b))))
    if tag == "/":                                   # quotient : (u/v)' = (u'v − uv')/v²
        a, b = expr[1], expr[2]
        num = ("-", ("*", derive(a), b), ("*", a, derive(b)))
        return simplifie(("/", num, ("^", b, 2)))
    if tag == "^":                                   # puissance + chaîne : (a^n)' = n·a^(n−1)·a'
        a, n = expr[1], expr[2]
        return simplifie(("*", ("*", ("const", Fraction(n)), ("^", a, n - 1)), derive(a)))
    # fonctions de base (chaîne : ·a')
    a = expr[1]
    da = derive(a)
    if tag == "sin":
        return simplifie(("*", ("cos", a), da))
    if tag == "cos":
        return simplifie(("*", ("const", Fraction(-1)), ("*", ("sin", a), da)))
    if tag == "tan":                                 # (tan)' = 1/cos²
        return simplifie(("*", ("/", ("const", Fraction(1)), ("^", ("cos", a), 2)), da))
    if tag == "exp":
        return simplifie(("*", ("exp", a), da))
    if tag == "ln":                                  # (ln a)' = a'/a
        return simplifie(("/", da, a))
    if tag == "sqrt":                                # (√a)' = a'/(2√a)
        return simplifie(("/", da, ("*", ("const", Fraction(2)), ("sqrt", a))))
    if tag == "atan":                                # (atan a)' = a'/(1+a²)
        return simplifie(("/", da, ("+", ("const", Fraction(1)), ("^", a, 2))))
    raise ValueError(f"noeud non dérivable (abstention) : {tag!r}")  # inatteignable après _verifie


# ── rendu texte ──────────────────────────────────────────────────────────────────────────────────────────────────
def vers_texte(expr) -> str:
    """Chaîne lisible représentant l'arbre (parenthésée, sans réécriture)."""
    expr = _verifie(expr)
    tag = expr[0]
    if tag == "const":
        v = _f(expr)
        return str(v.numerator) if v.denominator == 1 else f"{v.numerator}/{v.denominator}"
    if tag == "var":
        return "x"
    if tag == "^":
        return f"({vers_texte(expr[1])})^{expr[2]}"
    if tag in _UNAIRES:
        return f"{tag}({vers_texte(expr[1])})"
    return f"({vers_texte(expr[1])} {tag} {vers_texte(expr[2])})"


# ── évaluation flottante (résultat APPROCHÉ) ─────────────────────────────────────────────────────────────────────
def _eval(expr, x: float) -> float:
    tag = expr[0]
    if tag == "const":
        return float(_f(expr))
    if tag == "var":
        return x
    if tag == "+":
        return _eval(expr[1], x) + _eval(expr[2], x)
    if tag == "-":
        return _eval(expr[1], x) - _eval(expr[2], x)
    if tag == "*":
        return _eval(expr[1], x) * _eval(expr[2], x)
    if tag == "/":
        d = _eval(expr[2], x)
        if d == 0.0:
            raise ValueError("évaluation : division par zéro (hors domaine)")
        return _eval(expr[1], x) / d
    if tag == "^":
        base = _eval(expr[1], x)
        n = expr[2]
        if base == 0.0 and n < 0:
            raise ValueError("évaluation : 0 élevé à une puissance négative (hors domaine)")
        try:
            return float(base ** n)
        except OverflowError:
            raise ValueError("évaluation : débordement de puissance")
    arg = _eval(expr[1], x)
    if tag == "sin":
        return math.sin(arg)
    if tag == "cos":
        return math.cos(arg)
    if tag == "tan":
        c = math.cos(arg)
        if abs(c) < 1e-12:
            raise ValueError("évaluation : tan indéfinie (cos = 0, ex. x = π/2)")
        return math.sin(arg) / c
    if tag == "exp":
        try:
            return math.exp(arg)
        except OverflowError:
            raise ValueError("évaluation : débordement de l'exponentielle")
    if tag == "ln":
        if arg <= 0.0:
            raise ValueError("évaluation : ln d'un réel ≤ 0 (hors domaine)")
        return math.log(arg)
    if tag == "sqrt":
        if arg < 0.0:
            raise ValueError("évaluation : sqrt d'un réel < 0 (hors domaine)")
        return math.sqrt(arg)
    if tag == "atan":
        return math.atan(arg)
    raise ValueError(f"noeud non évaluable (abstention) : {tag!r}")


def evalue(expr, x) -> float:
    """Évaluation flottante (APPROCHÉE, double précision) de expr au point réel x.

    Abstention de DOMAINE -> ValueError (ln≤0, /0, sqrt<0, tan où cos=0). x booléen/non fini -> ValueError."""
    expr = _verifie(expr)
    if isinstance(x, bool) or not isinstance(x, (int, float)):
        raise ValueError("point x invalide : un réel fini est requis (bool/str/complexe refusés)")
    if isinstance(x, float) and not math.isfinite(x):
        raise ValueError("point x invalide : NaN/inf refusés")
    return _eval(expr, float(x))


# ── forme affine u = a·x + b (pour la substitution des primitives) ───────────────────────────────────────────────
def _affine(e):
    """Renvoie (a, b) en Fraction si e ≡ a·x + b, sinon None. Base de la substitution affine des primitives."""
    tag = e[0]
    if tag == "const":
        return (Fraction(0), _f(e))
    if tag == "var":
        return (Fraction(1), Fraction(0))
    if tag == "+":
        l, r = _affine(e[1]), _affine(e[2])
        return (l[0] + r[0], l[1] + r[1]) if l and r else None
    if tag == "-":
        l, r = _affine(e[1]), _affine(e[2])
        return (l[0] - r[0], l[1] - r[1]) if l and r else None
    if tag == "*":
        l, r = _affine(e[1]), _affine(e[2])
        if not l or not r:
            return None
        if l[0] == 0:                    # constante · affine
            return (l[1] * r[0], l[1] * r[1])
        if r[0] == 0:                    # affine · constante
            return (r[1] * l[0], r[1] * l[1])
        return None                      # produit de deux termes en x -> non affine
    if tag == "/":
        l, r = _affine(e[1]), _affine(e[2])
        if not l or not r or r[0] != 0 or r[1] == 0:
            return None                  # dénominateur en x ou nul -> non affine
        return (l[0] / r[1], l[1] / r[1])
    if tag == "^":
        if e[2] == 0:
            return (Fraction(0), Fraction(1))
        if e[2] == 1:
            return _affine(e[1])
        return None                      # x², x³, … ne sont pas affines
    return None                          # sin, cos, exp, ln, sqrt, tan, atan : non affines


def _est_1_plus_x2(e) -> bool:
    """True ssi e se simplifie en 1 + x² (dans un ordre ou l'autre)."""
    e = simplifie(e)
    if e[0] != "+":
        return False
    x2 = ("^", ("var",), 2)
    l, r = e[1], e[2]
    return (l == x2 and _is_val(r, 1)) or (r == x2 and _is_val(l, 1))


# ── primitives (catalogue fermé + linéarité + substitution affine) ───────────────────────────────────────────────
def primitive(expr):
    """Primitive symbolique F telle que F' = expr, si expr est au CATALOGUE ; sinon ValueError (abstention).

    Catalogue : constante, x, x^n (n entier), 1/x, 1/(a·x+b), exp(a·x+b), sin/cos(a·x+b), 1/(1+x²) ;
    fermé par LINÉARITÉ (+, −), facteur CONSTANT, et substitution AFFINE u = a·x + b. On n'invente JAMAIS
    une primitive : toute autre forme lève ValueError."""
    expr = simplifie(_verifie(expr))
    tag = expr[0]

    # linéarité
    if tag == "+":
        return simplifie(("+", primitive(expr[1]), primitive(expr[2])))
    if tag == "-":
        return simplifie(("-", primitive(expr[1]), primitive(expr[2])))

    # facteur constant : ∫ c·g = c·∫g
    if tag == "*":
        a, b = expr[1], expr[2]
        if _is_const(a):
            return simplifie(("*", a, primitive(b)))
        if _is_const(b):
            return simplifie(("*", b, primitive(a)))
        raise ValueError(_MSG_PRIM)      # produit non trivial (ex. x·sin x) : intégration par parties non implémentée

    # ∫ c dx = c·x
    if tag == "const":
        return simplifie(("*", expr, ("var",)))

    # ∫ x dx = x²/2
    if tag == "var":
        return ("/", ("^", ("var",), 2), ("const", Fraction(2)))

    # ∫ (a·x+b)^n dx  (couvre x^n via a=1,b=0)
    if tag == "^":
        base, n = expr[1], expr[2]
        aff = _affine(base)
        if aff and aff[0] != 0:
            a, _b = aff
            if n == -1:                  # ∫ (ax+b)^(−1) = ln|ax+b| / a
                return simplifie(("*", ("const", Fraction(1) / a), ("ln", base)))
            return simplifie(("*", ("const", Fraction(1) / (a * (n + 1))), ("^", base, n + 1)))
        raise ValueError(_MSG_PRIM)

    # ∫ (num const)/(dénominateur) dx
    if tag == "/":
        num, den = expr[1], expr[2]
        if _est_1_plus_x2(den):          # ∫ c/(1+x²) = c·arctan(x)
            if _is_const(num):
                return simplifie(("*", num, ("atan", ("var",))))
            raise ValueError(_MSG_PRIM)
        affd = _affine(den)              # ∫ c/(a·x+b) = (c/a)·ln|a·x+b|
        if _is_const(num) and affd and affd[0] != 0:
            a, _b = affd
            return simplifie(("*", ("const", _f(num) / a), ("ln", den)))
        raise ValueError(_MSG_PRIM)

    # ∫ exp(a·x+b) = exp(a·x+b)/a
    if tag == "exp":
        aff = _affine(expr[1])
        if aff and aff[0] != 0:
            return simplifie(("*", ("const", Fraction(1) / aff[0]), ("exp", expr[1])))
        raise ValueError(_MSG_PRIM)      # ex. exp(−x²) : PAS de primitive élémentaire (Risch)

    # ∫ sin(a·x+b) = −cos(a·x+b)/a
    if tag == "sin":
        aff = _affine(expr[1])
        if aff and aff[0] != 0:
            return simplifie(("*", ("const", Fraction(-1) / aff[0]), ("cos", expr[1])))
        raise ValueError(_MSG_PRIM)

    # ∫ cos(a·x+b) = sin(a·x+b)/a
    if tag == "cos":
        aff = _affine(expr[1])
        if aff and aff[0] != 0:
            return simplifie(("*", ("const", Fraction(1) / aff[0]), ("sin", expr[1])))
        raise ValueError(_MSG_PRIM)

    # tan, ln, sqrt, atan en tête : hors catalogue -> abstention
    raise ValueError(_MSG_PRIM)
