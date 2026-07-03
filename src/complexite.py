"""COMPLEXITÉ ALGORITHMIQUE — théorème maître + ordre de croissance asymptotique, EXACTS, FAUX=0
(mission formule/concept 2026-06-29 ; sujet borné « Théorie de la complexité (P, NP, etc.) »).

Même posture que `physique` / `maths_discretes` : le MÉCANISME est exact (théorème maître de
Cormen-Leiserson-Rivest-Stein, hiérarchie standard des classes de croissance), et l'abstention est
STRUCTURELLE — toute entrée invalide (domaine, type, forme non reconnue) lève `ValueError`, JAMAIS un
résultat faux. Conservateur : faux négatif (abstention) toléré, faux POSITIF interdit.

COUVRE deux capacités exactes et directement appelables :

1. THÉORÈME MAÎTRE — pour une récurrence diviser-pour-régner T(n) = a·T(n/b) + Θ(n^d) (a≥1, b>1, d≥0),
   on compare l'exposant du travail local d à l'exposant critique c = log_b(a) :
     • d > c  (la racine domine)     -> Θ(n^d)
     • d = c  (équilibre)            -> Θ(n^d · log n)
     • d < c  (les feuilles dominent)-> Θ(n^c)
   `classe_master(a,b,d)` rend la forme symbolique (str) de Θ ; `regime_master` le régime ;
   `exposant_critique(a,b)` rend c = log_b(a).
   Ancres connues : mergesort a=2,b=2,d=1 -> 'n log n' ; recherche dichotomique a=1,b=2,d=0 -> 'log n' ;
   Karatsuba a=3,b=2,d=1 -> n^log2(3)≈n^1.585 ; Strassen a=7,b=2,d=2 -> n^log2(7)≈n^2.807.

2. ORDRE DE CROISSANCE — `compare_croissance(f, g, n)` dit laquelle de deux fonctions de croissance
   (vocabulaire : 1, log n, log^k n, n, n log n, n^a, n^a log^k n, c^n, n!) DOMINE asymptotiquement
   (n -> ∞). La comparaison est SYMBOLIQUE et exacte sur ce vocabulaire sans facteur constant
   (hiérarchie : 1 ≺ log n ≺ … ≺ n^a ≺ n^a log n ≺ … ≺ c^n ≺ n! ). `n` est le témoin asymptotique
   (entier ≥ 1 requis). Toute forme non reconnue -> ValueError (on ne devine pas).

PRÉCISION HONNÊTE : l'exposant critique est un flottant (log) ; il est rendu à 6 décimales (irrationnel en
général, ex. log2(7)). Le test d/c d'égalité utilise une tolérance ε=1e-9 — convient aux a,b,d simples
(usage canonique) ; on ne prétend pas trancher un d artificiellement à 1e-12 de c.

Vérifié en adverse par `valide_complexite.py` (ancres CLRS + soundness : entrée invalide -> ValueError).
"""
from __future__ import annotations

import math
import re

_EPS = 1e-9


def _reel(x) -> bool:
    return isinstance(x, (int, float)) and not isinstance(x, bool)


# ── formatage des formes polynomiales/logarithmiques (str canonique) ─────────────────────────────────────────────
def _fmt_exp(e: float) -> str:
    """Rend 'e' comme exposant : entier proche -> entier ; sinon 6 décimales (zéros de queue ôtés)."""
    r = round(e)
    if abs(e - r) < 1e-9:
        return str(int(r))
    return f"{e:.6f}".rstrip("0").rstrip(".")


def _poly_str(d: float) -> str:
    """Forme Θ(n^d) : 1 / n / n^d."""
    r = round(d)
    if abs(d - r) < 1e-9:
        di = int(r)
        if di == 0:
            return "1"
        if di == 1:
            return "n"
        return f"n^{di}"
    return f"n^{_fmt_exp(d)}"


def _poly_log_str(d: float) -> str:
    """Forme Θ(n^d · log n) : log n / n log n / n^d log n."""
    r = round(d)
    if abs(d - r) < 1e-9:
        di = int(r)
        if di == 0:
            return "log n"
        if di == 1:
            return "n log n"
        return f"n^{di} log n"
    return f"n^{_fmt_exp(d)} log n"


# ── THÉORÈME MAÎTRE ─────────────────────────────────────────────────────────────────────────────────────────────
def _valide_master(a, b, d) -> None:
    if not (_reel(a) and _reel(b) and _reel(d)):
        raise ValueError("a, b, d doivent être des réels (int/float, pas bool)")
    if a < 1:
        raise ValueError("a ≥ 1 requis (au moins un sous-problème)")
    if b <= 1:
        raise ValueError("b > 1 requis (la taille doit décroître)")
    if d < 0:
        raise ValueError("d ≥ 0 requis (exposant du travail local)")


def exposant_critique(a, b) -> float:
    """c = log_b(a), l'exposant critique du théorème maître. a ≥ 1, b > 1."""
    _valide_master(a, b, 0)
    return round(math.log(a) / math.log(b), 6)


def regime_master(a, b, d) -> str:
    """Régime du théorème maître : 'racine' (d>c), 'equilibre' (d=c) ou 'feuilles' (d<c)."""
    _valide_master(a, b, d)
    c = math.log(a) / math.log(b)
    if d > c + _EPS:
        return "racine"
    if abs(d - c) <= _EPS:
        return "equilibre"
    return "feuilles"


def classe_master(a, b, d) -> str:
    """Théorème maître pour T(n) = a·T(n/b) + Θ(n^d). Rend la forme symbolique de Θ (str).

    a ≥ 1 (sous-problèmes), b > 1 (facteur de division), d ≥ 0 (exposant du travail de recombinaison).
      d > log_b(a) -> n^d ; d = log_b(a) -> n^d·log n ; d < log_b(a) -> n^(log_b a).
    """
    _valide_master(a, b, d)
    c = math.log(a) / math.log(b)
    if d > c + _EPS:                 # la racine domine : Θ(n^d)
        return _poly_str(d)
    if abs(d - c) <= _EPS:           # équilibre : Θ(n^d log n)
        return _poly_log_str(d)
    return _poly_str(c)              # les feuilles dominent : Θ(n^(log_b a))


# ── ORDRE DE CROISSANCE ASYMPTOTIQUE ────────────────────────────────────────────────────────────────────────────
# Clé d'ordre = (rang_factoriel, base_exp, degré_polynomial, puissance_log) ; comparaison lexicographique,
# plus grande clé = domine. C'est l'ordre total exact de la hiérarchie asymptotique standard (sans facteur cst).
def ordre_croissance(expr: str):
    """Clé d'ordre asymptotique d'une forme de croissance. Forme non reconnue -> ValueError."""
    if not isinstance(expr, str):
        raise ValueError("expression de croissance attendue (str)")
    t = expr.strip().lower().replace(" ", "").replace("*", "")
    if t == "":
        raise ValueError("expression vide")
    # facteur constant en tête (asymptotiquement neutre) : '2n' -> 'n', '3n log n' -> 'n log n'.
    # (ne s'applique pas à 'c^n' : le coefficient y est suivi de '^', jamais de 'n'/'log'.)
    mc = re.match(r"(\d+(?:\.\d+)?)(n|log)", t)
    if mc:
        t = t[mc.end(1):]
    # factorielle
    if t == "n!":
        return (1, 0.0, 0.0, 0)
    # exponentielle c^n (base constante > 1)
    m = re.fullmatch(r"(\d+(?:\.\d+)?)\^n", t)
    if m:
        base = float(m.group(1))
        if base <= 1:
            raise ValueError("base exponentielle > 1 requise")
        return (0, base, 0.0, 0)
    # constante pure (1, 5, 3.5…)
    if re.fullmatch(r"\d+(?:\.\d+)?", t):
        return (0, 0.0, 0.0, 0)
    # n^a log^k n
    m = re.fullmatch(r"n\^(\d+(?:\.\d+)?)log\^(\d+)n", t)
    if m:
        return (0, 0.0, float(m.group(1)), int(m.group(2)))
    # n^a log n
    m = re.fullmatch(r"n\^(\d+(?:\.\d+)?)logn", t)
    if m:
        return (0, 0.0, float(m.group(1)), 1)
    # n^a
    m = re.fullmatch(r"n\^(\d+(?:\.\d+)?)", t)
    if m:
        return (0, 0.0, float(m.group(1)), 0)
    # n log^k n
    m = re.fullmatch(r"nlog\^(\d+)n", t)
    if m:
        return (0, 0.0, 1.0, int(m.group(1)))
    # n log n
    if t == "nlogn":
        return (0, 0.0, 1.0, 1)
    # n
    if t == "n":
        return (0, 0.0, 1.0, 0)
    # log^k n
    m = re.fullmatch(r"log\^(\d+)n", t)
    if m:
        return (0, 0.0, 0.0, int(m.group(1)))
    # log n
    if t == "logn":
        return (0, 0.0, 0.0, 1)
    raise ValueError(f"forme de croissance non reconnue : {expr!r}")


def compare_croissance(f: str, g: str, n: int) -> str:
    """Dit laquelle de f, g DOMINE asymptotiquement (n -> ∞). Rend la chaîne dominante, ou 'equivalent'
    si même classe Θ. `n` = témoin asymptotique (entier ≥ 1 requis). Forme non reconnue -> ValueError.
    """
    if not (isinstance(n, int) and not isinstance(n, bool)) or n < 1:
        raise ValueError("n doit être un entier ≥ 1 (témoin asymptotique)")
    kf = ordre_croissance(f)
    kg = ordre_croissance(g)
    if kf == kg:
        return "equivalent"
    return f if kf > kg else g
