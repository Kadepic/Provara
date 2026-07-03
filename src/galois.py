"""THÉORIE DE GALOIS — faits ÉTABLIS, mécanisme EXACT, FAUX=0 (mission formule/concept 2026-06-29).

Posture (identique à `physique`/`maths_discretes`) : on n'expose QUE ce qui est démontré et vérifiable :
  • Résolubilité par radicaux du polynôme GÉNÉRAL de degré n (théorème d'Abel-Ruffini + formules de
    Cardan/Ferrari) : résoluble ssi n ≤ 4.
  • Résolubilité du groupe symétrique Sₙ (resp. alterné Aₙ) : Sₙ et Aₙ résolubles ssi n ≤ 4 (A₅ est le plus
    petit groupe simple non abélien).
  • Ordre du groupe de Galois pour des familles closes : extension cyclotomique Q(ζₙ)/Q ≅ (Z/nZ)* d'ordre φ(n) ;
    extension quadratique Q(√d)/Q d'ordre 2.
  • CATALOGUE de polynômes concrets dont le groupe de Galois est un FAIT établi (sourcé, certain) — toute entrée
    HORS du catalogue lève `ValueError` (abstention STRUCTURELLE : on ne devine JAMAIS un groupe de Galois).

L'abstention est structurelle : toute entrée invalide ou inconnue -> `ValueError`, jamais un résultat faux.
Vérifié en adverse par `valide_galois.py` (ancres = théorèmes/valeurs de référence + soundness + déterminisme).
"""
from __future__ import annotations

import math


# ── helpers internes ─────────────────────────────────────────────────────────────────────────────────────────────
def _entier(x, mini=None):
    if not isinstance(x, int) or isinstance(x, bool):
        raise ValueError(f"entier attendu, reçu {x!r}")
    if mini is not None and x < mini:
        raise ValueError(f"entier ≥ {mini} attendu, reçu {x}")
    return x


def _factorielle(n: int) -> int:
    r = 1
    for k in range(2, n + 1):
        r *= k
    return r


# ── INDICATRICE D'EULER (mécanisme exact) ────────────────────────────────────────────────────────────────────────
def indicatrice_euler(n: int) -> int:
    """φ(n) = nombre d'entiers de 1..n premiers avec n (ordre de (Z/nZ)*). n ≥ 1."""
    _entier(n, 1)
    r = n
    m = n
    p = 2
    while p * p <= m:
        if m % p == 0:
            while m % p == 0:
                m //= p
            r -= r // p
        p += 1
    if m > 1:
        r -= r // m
    return r


# ── RÉSOLUBILITÉ PAR RADICAUX (polynôme général de degré n) ───────────────────────────────────────────────────────
def resoluble_par_radicaux(degre: int) -> bool:
    """Le polynôme GÉNÉRAL (générique) de degré `degre` est-il résoluble par radicaux ?

    Vrai ssi degre ≤ 4 : degré 1 (trivial), 2 (formule du discriminant), 3 (Cardan), 4 (Ferrari) ;
    degré ≥ 5 : NON (Abel-Ruffini — le groupe de Galois générique Sₙ n'est pas résoluble pour n ≥ 5).
    Concerne le polynôme général : des polynômes PARTICULIERS de degré ≥ 5 peuvent être résolubles
    (cf. `resoluble_polynome`). degre ≥ 1 sinon ValueError.
    """
    _entier(degre, 1)
    return degre <= 4


# ── RÉSOLUBILITÉ DES GROUPES Sₙ / Aₙ ─────────────────────────────────────────────────────────────────────────────
def groupe_symetrique_resoluble(n: int) -> bool:
    """Le groupe symétrique Sₙ est résoluble ssi n ≤ 4. n ≥ 1."""
    _entier(n, 1)
    return n <= 4


def groupe_resoluble(n: int) -> bool:
    """Alias de spécification : Sₙ résoluble ssi n ≤ 4."""
    return groupe_symetrique_resoluble(n)


def groupe_alterne_resoluble(n: int) -> bool:
    """Le groupe alterné Aₙ est résoluble ssi n ≤ 4 (A₅ = plus petit groupe simple non abélien). n ≥ 1."""
    _entier(n, 1)
    return n <= 4


def ordre_groupe_symetrique(n: int) -> int:
    """|Sₙ| = n!. n ≥ 0."""
    _entier(n, 0)
    return _factorielle(n)


def ordre_groupe_alterne(n: int) -> int:
    """|Aₙ| = n!/2 pour n ≥ 2 ; |A₀| = |A₁| = 1. n ≥ 0."""
    _entier(n, 0)
    if n < 2:
        return 1
    return _factorielle(n) // 2


# ── ORDRE DU GROUPE DE GALOIS — familles closes ──────────────────────────────────────────────────────────────────
def ordre_groupe_galois_cyclotomique(n: int) -> int:
    """|Gal(Q(ζₙ)/Q)| = φ(n) (le groupe est isomorphe à (Z/nZ)*). n ≥ 1."""
    _entier(n, 1)
    return indicatrice_euler(n)


def ordre_groupe_galois_quadratique(radicande: int | None = None) -> int:
    """|Gal(Q(√d)/Q)| = 2 pour toute extension quadratique (d non carré parfait).

    Sans argument : renvoie 2. Avec `radicande` d entier : valide que Q(√d) est bien degré 2
    (d ≠ 0 et, si d > 0, d non carré parfait — sinon Q(√d) = Q, extension triviale -> ValueError).
    """
    if radicande is None:
        return 2
    _entier(radicande)
    if radicande == 0:
        raise ValueError("radicande nul -> extension triviale")
    if radicande > 0:
        s = math.isqrt(radicande)
        if s * s == radicande:
            raise ValueError("radicande carré parfait -> Q(√d)=Q (pas une extension quadratique)")
    return 2


def ordre_groupe_galois(famille: str, param: int | None = None) -> int:
    """Ordre du groupe de Galois pour une famille close : "cyclotomique" (param=n -> φ(n)) ou "quadratique" (->2)."""
    if not isinstance(famille, str):
        raise ValueError(f"famille (chaîne) attendue, reçu {famille!r}")
    f = famille.strip().lower()
    if f == "cyclotomique":
        if param is None:
            raise ValueError("famille cyclotomique : paramètre n requis")
        return ordre_groupe_galois_cyclotomique(param)
    if f == "quadratique":
        return ordre_groupe_galois_quadratique(param)
    raise ValueError(f"famille de Galois inconnue (abstention) : {famille!r}")


# ── CATALOGUE de polynômes concrets (FAITS établis, sourcés) ──────────────────────────────────────────────────────
# Pour chaque polynôme : groupe de Galois sur Q de son corps de décomposition, son ordre, et la résolubilité par
# radicaux (équivaut à la résolubilité du groupe). Faits classiques de cours (ex. Dummit & Foote, Stewart "Galois
# Theory"). Toute clé HORS de ce dictionnaire -> abstention (ValueError) : on NE devine PAS un groupe de Galois.
_CATALOGUE = {
    "x^2-2":     {"groupe": "Z/2Z", "ordre": 2,   "resoluble": True},   # Q(√2),    cyclique d'ordre 2
    "x^3-2":     {"groupe": "S3",   "ordre": 6,   "resoluble": True},   # Q(2^1/3,ω), S3 (résoluble)
    "x^4-2":     {"groupe": "D4",   "ordre": 8,   "resoluble": True},   # Q(2^1/4,i), diédral D4 (résoluble)
    "x^5-2":     {"groupe": "F20",  "ordre": 20,  "resoluble": True},   # Q(2^1/5,ζ5), Frobenius F20 (métacyclique)
    "x^5-x-1":   {"groupe": "S5",   "ordre": 120, "resoluble": False},  # groupe S5 (NON résoluble) — Abel-Ruffini
}


def _norm(poly: str) -> str:
    if not isinstance(poly, str):
        raise ValueError(f"polynôme (chaîne) attendu, reçu {poly!r}")
    return "".join(poly.split()).lower()


def _entree_catalogue(poly: str) -> dict:
    cle = _norm(poly)
    if cle not in _CATALOGUE:
        raise ValueError(f"polynôme hors catalogue (abstention) : {poly!r}")
    return _CATALOGUE[cle]


def groupe_galois_polynome(poly: str) -> str:
    """Groupe de Galois (étiquette) du polynôme `poly` sur Q, s'il est au catalogue ; sinon ValueError."""
    return _entree_catalogue(poly)["groupe"]


def ordre_galois_polynome(poly: str) -> int:
    """Ordre du groupe de Galois du polynôme `poly` sur Q, s'il est au catalogue ; sinon ValueError."""
    return _entree_catalogue(poly)["ordre"]


def resoluble_polynome(poly: str) -> bool:
    """Le polynôme `poly` est-il résoluble par radicaux ? Fait catalogué ; entrée inconnue -> ValueError."""
    return _entree_catalogue(poly)["resoluble"]


def catalogue_polynomes() -> tuple:
    """Liste triée des polynômes du catalogue (clés normalisées)."""
    return tuple(sorted(_CATALOGUE))
