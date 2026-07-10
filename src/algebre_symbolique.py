"""
ALGÈBRE SYMBOLIQUE — polynômes à UNE variable sur ℚ, manipulation EXACTE, FAUX=0.

Posture (identique à `geometries_non_euclidiennes` / `galois`) : le résultat est une CONSÉQUENCE
EXACTE de l'algèbre des polynômes sur le corps ℚ, jamais une approximation ni une devinette. Tout se
calcule en `fractions.Fraction` — AUCUN flottant n'entre ni ne sort. Au moindre doute -> `ValueError`
(abstention structurelle) ; une identité qui ne se referme pas ne sort JAMAIS (-> `RuntimeError`).

REPRÉSENTATION : un polynôme est une LISTE de coefficients `Fraction`, l'indice = le degré, du plus BAS
au plus haut (lowest-first). Exemple : x² − 1  ->  [-1, 0, 1]. Le polynôme NUL est la liste vide [].
La forme CANONIQUE (`simplifie`) réduit chaque coefficient et supprime les zéros de tête (haut degré).

MÉCANISME (théorèmes exacts) :
  • `developpe(arbre)` : évalue un mini-arbre — ('var',), ('const', c), ('+',a,b), ('-',a,b), ('*',a,b),
    ('^', a, n) avec n entier ≥ 0 — vers le polynôme canonique, par les opérations exactes +, −, ×, ^.
  • `factorise(poly)` : factorisation sur ℚ = extraction des racines RATIONNELLES (théorème des racines
    rationnelles p/q avec p | a₀ et q | aₙ, puis déflation par division synthétique EXACTE) ; le facteur
    résiduel SANS racine rationnelle est rendu TEL QUEL (jamais factorisé de force, aucune racine inventée).
    Renvoie un ARBRE dont le développement REDONNE le polynôme (boucle fermée developpe∘factorise = id).
  • `identite(nom, a, b)` : construit les DEUX membres d'une identité remarquable, les développe, et
    VÉRIFIE leur égalité exacte (sinon `RuntimeError`). Catalogue : carré/cube d'une somme/différence,
    différence de carrés, somme/différence de cubes. Nom hors catalogue -> `ValueError`.
  • `evalue(poly, x)` : schéma de Horner en `Fraction`.

GARANTIES (vérifiées en adverse par `valide_algebre_symbolique.py`) :
  - flottant en entrée (coefficient, borne, x, a, b) -> ValueError (l'exactitude ℚ exige Fraction/int) ;
  - bool en entrée -> ValueError (True n'est pas 1) ; str/complexe -> ValueError ;
  - exposant négatif ou non entier -> ValueError ; nœud d'arbre inconnu / mal formé -> ValueError ;
  - identité hors catalogue -> ValueError ; racines d'un polynôme nul (infinies) -> ValueError ;
  - déterministe, pur, sans état global mutable, sans aléatoire, sans horloge ;
  - conservateur : faux négatif/abstention toléré, faux POSITIF interdit.

Le module n'importe que `math` et `fractions` (stdlib).
"""
from __future__ import annotations

import math
from fractions import Fraction

SOURCE = "algèbre des polynômes sur ℚ : identités remarquables + théorème des racines rationnelles (Gauss)"


# ── VALIDATION DES SCALAIRES ──────────────────────────────────────────────────────────────────────────────────────
def _frac(x) -> Fraction:
    """Coerce un scalaire EXACT en Fraction. bool/float/str/complexe -> ValueError (FAUX=0)."""
    if isinstance(x, bool):
        raise ValueError("booléen refusé : True n'est pas 1 (coefficient exact requis)")
    if isinstance(x, int):
        return Fraction(x)
    if isinstance(x, Fraction):
        return x
    raise ValueError(f"scalaire exact requis (int ou Fraction), reçu {type(x).__name__}: {x!r}")


def _exposant(n) -> int:
    """Exposant : entier ≥ 0 (bool refusé). Négatif ou non entier -> ValueError."""
    if isinstance(n, bool) or not isinstance(n, int):
        raise ValueError(f"exposant entier ≥ 0 requis, reçu {n!r}")
    if n < 0:
        raise ValueError(f"exposant négatif refusé (pas un polynôme) : {n}")
    return n


# ── FORME CANONIQUE ───────────────────────────────────────────────────────────────────────────────────────────────
def simplifie(poly) -> list:
    """Forme canonique : coefficients réduits (Fraction), zéros de tête (haut degré) supprimés.

    Le polynôme nul -> []. Entrée = liste/tuple de coefficients exacts (int/Fraction)."""
    if not isinstance(poly, (list, tuple)):
        raise ValueError("polynôme : liste/tuple de coefficients requis")
    coeffs = [_frac(c) for c in poly]
    while coeffs and coeffs[-1] == 0:
        coeffs.pop()
    return coeffs


def degre(poly) -> int:
    """Degré exact ; le polynôme nul a le degré conventionnel -1."""
    s = simplifie(poly)
    return len(s) - 1


def egal(p, q) -> bool:
    """Égalité symbolique EXACTE : mêmes formes canoniques."""
    return simplifie(p) == simplifie(q)


# ── OPÉRATIONS POLYNOMIALES EXACTES ───────────────────────────────────────────────────────────────────────────────
def _add(p: list, q: list) -> list:
    n = max(len(p), len(q))
    r = [Fraction(0)] * n
    for i, c in enumerate(p):
        r[i] += c
    for i, c in enumerate(q):
        r[i] += c
    return simplifie(r)


def _sous(p: list, q: list) -> list:
    return _add(p, [-c for c in q])


def _mul(p: list, q: list) -> list:
    if not p or not q:
        return []
    r = [Fraction(0)] * (len(p) + len(q) - 1)
    for i, a in enumerate(p):
        for j, b in enumerate(q):
            r[i + j] += a * b
    return simplifie(r)


def _puiss(p: list, n: int) -> list:
    r = [Fraction(1)]  # polynôme constant 1
    for _ in range(n):
        r = _mul(r, p)
    return r


# ── DÉVELOPPEMENT D'UN ARBRE ──────────────────────────────────────────────────────────────────────────────────────
_VAR = [Fraction(0), Fraction(1)]  # le polynôme x


def developpe(expr) -> list:
    """Développe un mini-arbre vers le polynôme canonique (lowest-first).

    Nœuds acceptés : ('var',), ('const', c), ('+',a,b), ('-',a,b), ('*',a,b), ('^', a, n≥0).
    Tout autre nœud ou nœud mal formé -> ValueError (abstention)."""
    if not isinstance(expr, tuple) or len(expr) == 0:
        raise ValueError(f"nœud d'arbre invalide : {expr!r}")
    tag = expr[0]
    if tag == "var":
        if len(expr) != 1:
            raise ValueError("nœud ('var',) : arité 1 requise")
        return list(_VAR)
    if tag == "const":
        if len(expr) != 2:
            raise ValueError("nœud ('const', c) : arité 2 requise")
        return simplifie([_frac(expr[1])])
    if tag in ("+", "-", "*"):
        if len(expr) != 3:
            raise ValueError(f"nœud ('{tag}', a, b) : arité 3 requise")
        a = developpe(expr[1])
        b = developpe(expr[2])
        if tag == "+":
            return _add(a, b)
        if tag == "-":
            return _sous(a, b)
        return _mul(a, b)
    if tag == "^":
        if len(expr) != 3:
            raise ValueError("nœud ('^', a, n) : arité 3 requise")
        base = developpe(expr[1])
        n = _exposant(expr[2])
        return _puiss(base, n)
    raise ValueError(f"nœud d'arbre inconnu (abstention) : {tag!r}")


# ── ÉVALUATION (HORNER, EXACT) ────────────────────────────────────────────────────────────────────────────────────
def evalue(poly, x) -> Fraction:
    """Évalue le polynôme en x par le schéma de Horner, en Fraction exacte. x flottant -> ValueError."""
    coeffs = simplifie(poly)
    xf = _frac(x)
    r = Fraction(0)
    for c in reversed(coeffs):
        r = r * xf + c
    return r


# ── RACINES RATIONNELLES ──────────────────────────────────────────────────────────────────────────────────────────
def _diviseurs(n: int) -> list:
    n = abs(n)
    if n == 0:
        return []
    ds = set()
    i = 1
    while i * i <= n:
        if n % i == 0:
            ds.add(i)
            ds.add(n // i)
        i += 1
    return sorted(ds)


def _lcm(a: int, b: int) -> int:
    return a * b // math.gcd(a, b)


def _horner_frac(coeffs: list, r: Fraction) -> Fraction:
    acc = Fraction(0)
    for c in reversed(coeffs):
        acc = acc * r + c
    return acc


def _trouve_racine_rationnelle(coeffs: list):
    """Cherche UNE racine rationnelle d'un polynôme (canonique, degré ≥ 1) par le théorème des racines
    rationnelles. Ordre d'énumération FIXE (déterministe). None si aucune racine rationnelle."""
    if coeffs[0] == 0:
        return Fraction(0)  # x=0 est racine ssi le terme constant est nul
    # normalisation en coefficients entiers
    L = 1
    for c in coeffs:
        L = _lcm(L, c.denominator)
    ints = [int(c * L) for c in coeffs]
    a0 = ints[0]
    an = ints[-1]
    ps = _diviseurs(a0)   # a0 ≠ 0 ici
    qs = _diviseurs(an)   # an ≠ 0 (polynôme canonique, leading non nul)
    for p in ps:
        for q in qs:
            for signe in (1, -1):
                r = Fraction(signe * p, q)
                if _horner_frac(coeffs, r) == 0:
                    return r
    return None


def _divise_par_lineaire(coeffs: list, root: Fraction) -> list:
    """Division synthétique EXACTE de `coeffs` par (x − root). Le reste est nul par construction."""
    hi = coeffs[::-1]  # highest-first
    out = [hi[0]]
    for k in range(1, len(hi)):
        out.append(hi[k] + root * out[-1])
    quotient = out[:-1][::-1]  # on retire le reste (=0) et on repasse lowest-first
    return simplifie(quotient)


def racines_rationnelles(poly) -> list:
    """Liste TRIÉE des racines rationnelles (avec multiplicité) du polynôme sur ℚ.

    Polynôme nul (racines infinies) -> ValueError. Aucune racine rationnelle -> []."""
    s = simplifie(poly)
    if not s:
        raise ValueError("racines d'un polynôme nul : indéfini (abstention)")
    racines = []
    current = list(s)
    while len(current) >= 2:
        r = _trouve_racine_rationnelle(current)
        if r is None:
            break
        racines.append(r)
        current = _divise_par_lineaire(current, r)
    return sorted(racines)


# ── FACTORISATION SUR ℚ ───────────────────────────────────────────────────────────────────────────────────────────
def _poly_vers_arbre(coeffs: list):
    """Arbre canonique d'un polynôme (somme de monômes). coeffs = liste Fraction (peut être vide)."""
    termes = []
    for i, c in enumerate(coeffs):
        if c == 0:
            continue
        if i == 0:
            termes.append(("const", c))
        else:
            termes.append(("*", ("const", c), ("^", ("var",), i)))
    if not termes:
        return ("const", Fraction(0))
    arbre = termes[0]
    for t in termes[1:]:
        arbre = ("+", arbre, t)
    return arbre


def factorise(poly):
    """Factorise `poly` sur ℚ. Renvoie un ARBRE dont le développement REDONNE le polynôme.

    Méthode : extraction des racines rationnelles (déflation exacte), le résidu SANS racine rationnelle
    est rendu tel quel (aucune racine inventée). Garantie : developpe(factorise(p)) == simplifie(p)."""
    s = simplifie(poly)
    if not s:
        return ("const", Fraction(0))
    if len(s) == 1:
        return ("const", s[0])
    facteurs = []
    current = list(s)
    while len(current) >= 2:
        r = _trouve_racine_rationnelle(current)
        if r is None:
            break
        facteurs.append(("-", ("var",), ("const", r)))
        current = _divise_par_lineaire(current, r)
    # `current` = résidu (constante non nulle, ou polynôme sans racine rationnelle)
    if current != [Fraction(1)]:
        facteurs.append(_poly_vers_arbre(current))
    if not facteurs:  # ne peut se produire que si tout s'est réduit à 1 (impossible ici), garde-fou
        return ("const", Fraction(1))
    arbre = facteurs[0]
    for f in facteurs[1:]:
        arbre = ("*", arbre, f)
    return arbre


# ── IDENTITÉS REMARQUABLES ────────────────────────────────────────────────────────────────────────────────────────
def _carre_somme(A, B):
    gauche = ("^", ("+", A, B), 2)
    droit = ("+", ("+", ("^", A, 2), ("*", ("const", 2), ("*", A, B))), ("^", B, 2))
    return gauche, droit


def _carre_difference(A, B):
    gauche = ("^", ("-", A, B), 2)
    droit = ("+", ("-", ("^", A, 2), ("*", ("const", 2), ("*", A, B))), ("^", B, 2))
    return gauche, droit


def _difference_carres(A, B):
    gauche = ("-", ("^", A, 2), ("^", B, 2))
    droit = ("*", ("-", A, B), ("+", A, B))
    return gauche, droit


def _cube_somme(A, B):
    gauche = ("^", ("+", A, B), 3)
    # a³ + 3a²b + 3ab² + b³
    t1 = ("^", A, 3)
    t2 = ("*", ("const", 3), ("*", ("^", A, 2), B))
    t3 = ("*", ("const", 3), ("*", A, ("^", B, 2)))
    t4 = ("^", B, 3)
    droit = ("+", ("+", ("+", t1, t2), t3), t4)
    return gauche, droit


def _cube_difference(A, B):
    gauche = ("^", ("-", A, B), 3)
    # a³ − 3a²b + 3ab² − b³
    t1 = ("^", A, 3)
    t2 = ("*", ("const", 3), ("*", ("^", A, 2), B))
    t3 = ("*", ("const", 3), ("*", A, ("^", B, 2)))
    t4 = ("^", B, 3)
    droit = ("-", ("+", ("-", t1, t2), t3), t4)
    return gauche, droit


def _somme_cubes(A, B):
    gauche = ("+", ("^", A, 3), ("^", B, 3))
    # (a + b)(a² − ab + b²)
    droit = ("*", ("+", A, B), ("+", ("-", ("^", A, 2), ("*", A, B)), ("^", B, 2)))
    return gauche, droit


def _difference_cubes(A, B):
    gauche = ("-", ("^", A, 3), ("^", B, 3))
    # (a − b)(a² + ab + b²)
    droit = ("*", ("-", A, B), ("+", ("+", ("^", A, 2), ("*", A, B)), ("^", B, 2)))
    return gauche, droit


_IDENTITES = {
    "carre_somme": _carre_somme,
    "carre_difference": _carre_difference,
    "difference_carres": _difference_carres,
    "cube_somme": _cube_somme,
    "cube_difference": _cube_difference,
    "somme_cubes": _somme_cubes,
    "difference_cubes": _difference_cubes,
}


def identite(nom, a, b):
    """Construit les DEUX membres développés d'une identité remarquable et VÉRIFIE leur égalité exacte.

    `a`, `b` = scalaires exacts (int/Fraction ; flottant/bool -> ValueError). Renvoie (gauche, droite),
    deux polynômes canoniques ÉGAUX. Nom hors catalogue -> ValueError. Non-égalité -> RuntimeError
    (une identité fausse ne sort JAMAIS)."""
    if not isinstance(nom, str):
        raise ValueError(f"nom d'identité (chaîne) requis, reçu {nom!r}")
    cle = nom.strip().lower()
    if cle not in _IDENTITES:
        raise ValueError(f"identité hors catalogue (abstention) : {nom!r}")
    A = ("const", _frac(a))
    B = ("const", _frac(b))
    gauche_arbre, droit_arbre = _IDENTITES[cle](A, B)
    gauche = developpe(gauche_arbre)
    droit = developpe(droit_arbre)
    if gauche != droit:
        raise RuntimeError(f"identité '{nom}' NON vérifiée : {gauche} != {droit} (FAUX=0)")
    return (gauche, droit)


def catalogue_identites() -> tuple:
    """Liste triée des noms d'identités remarquables disponibles."""
    return tuple(sorted(_IDENTITES))
