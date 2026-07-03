"""
CAS-LIMITES / ASYMPTOTES / SYMÉTRIES — brique Vague 6 (vérification par les bords).

POURQUOI : une loi ou un design se trahit souvent aux LIMITES (comportement en 0, en +∞, sous signe négatif) et par
ses SYMÉTRIES attendues. Un moyen puissant et bon marché de tester une formule : vérifier qu'elle fait ce qu'il faut
aux bords (une énergie cinétique doit s'annuler à vitesse nulle et croître ; une probabilité rester dans [0,1]).

MODÈLE : des vérificateurs génériques sur une fonction f d'un réel : valeur/limite en un point, monotonie sur un
échantillon, bornes (image dans un intervalle), parité (paire/impaire), homogénéité d'échelle f(k·x)=k^p·f(x).

FAUX=0 :
  • Chaque test renvoie True/False FACTUEL (le comportement observé sur l'échantillon), jamais une supposition.
  • Un test non concluant (ex. valeur non finie) -> False (échec de la propriété), pas un « ça passe » optimiste.
  • Déterministe (échantillon fixe) ; ne prétend pas à la preuve analytique — c'est un CRIBLE (réfute ou corrobore).
Stdlib pur, souverain.
"""
from __future__ import annotations

import math


def _echantillon(a, b, n):
    if n < 2:
        return [a, b]
    pas = (b - a) / (n - 1)
    return [a + i * pas for i in range(n)]


def limite_en(f, x0, attendue, tol: float = 1e-6, approche: float = 1e-6) -> bool:
    """f(x0±approche) tend-il vers `attendue` ? True ssi les valeurs de part et d'autre sont finies et ≈ attendue."""
    try:
        g = f(x0 + approche)
        d = f(x0 - approche) if x0 - approche else g
    except Exception:
        return False
    return all(v is not None and math.isfinite(v) and abs(v - attendue) <= tol * max(abs(attendue), 1.0)
               for v in (g, d))


def monotone(f, a, b, croissante=True, n: int = 50) -> bool:
    """f est-elle monotone (croissante/décroissante) sur [a,b] (échantillon) ? Valeur non finie -> False."""
    xs = _echantillon(a, b, n)
    try:
        ys = [f(x) for x in xs]
    except Exception:
        return False
    if any(y is None or not math.isfinite(y) for y in ys):
        return False
    for i in range(1, len(ys)):
        if croissante and ys[i] < ys[i - 1] - 1e-12:
            return False
        if not croissante and ys[i] > ys[i - 1] + 1e-12:
            return False
    return True


def bornee(f, a, b, bas=None, haut=None, n: int = 50) -> bool:
    """L'image de f sur [a,b] reste-t-elle dans [bas, haut] ? (ex. une probabilité dans [0,1]). Non fini -> False."""
    xs = _echantillon(a, b, n)
    try:
        ys = [f(x) for x in xs]
    except Exception:
        return False
    for y in ys:
        if y is None or not math.isfinite(y):
            return False
        if bas is not None and y < bas - 1e-12:
            return False
        if haut is not None and y > haut + 1e-12:
            return False
    return True


def parite(f, paire=True, points=(0.5, 1.0, 2.0, 3.7), tol: float = 1e-9) -> bool:
    """Vérifie f(-x) = f(x) (paire) ou f(-x) = -f(x) (impaire) sur quelques points."""
    try:
        for x in points:
            fx, fmx = f(x), f(-x)
            if fx is None or fmx is None or not math.isfinite(fx) or not math.isfinite(fmx):
                return False
            cible = fx if paire else -fx
            if abs(fmx - cible) > tol * max(abs(cible), 1.0):
                return False
        return True
    except Exception:
        return False


def homogene_degre(f, p, k: float = 2.0, points=(1.0, 2.0, 3.0), tol: float = 1e-9) -> bool:
    """f(k·x) = k^p · f(x) (homogénéité de degré p) — signe d'une loi de puissance x^p. Sur quelques points."""
    try:
        for x in points:
            gauche = f(k * x)
            droite = (k ** p) * f(x)
            if gauche is None or droite is None or not math.isfinite(gauche):
                return False
            if abs(gauche - droite) > tol * max(abs(droite), 1.0):
                return False
        return True
    except Exception:
        return False
