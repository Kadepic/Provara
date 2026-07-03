"""ARITHMÉTIQUE MODULAIRE & CRYPTO — primitives EXACTES (entiers), FAUX=0 (mission formule/concept 2026-06-29).

Briques de la cryptographie mathématique (RSA, Diffie-Hellman) : PGCD, Euclide étendu, inverse modulaire,
exponentiation modulaire (square-and-multiply), test de primalité de Miller-Rabin DÉTERMINISTE (jeu de témoins
prouvé pour n < 3.3·10²⁴). Tout est EXACT (entiers arbitraires Python) ; entrée invalide -> ValueError (jamais un
faux). Conservateur : inverse modulaire inexistant (pgcd≠1) -> ValueError, jamais une valeur inventée.

Couvre le sujet borné « Cryptographie mathématique ».
Vérifié en adverse par `valide_arithmetique_modulaire.py` (ancres connues + soundness + round-trip RSA).
"""
from __future__ import annotations


def _ent(*xs):
    for x in xs:
        if not isinstance(x, int) or isinstance(x, bool):
            raise ValueError(f"entier attendu, reçu {x!r}")


def pgcd(a: int, b: int) -> int:
    """PGCD ≥ 0 (algorithme d'Euclide). pgcd(0,0)=0."""
    _ent(a, b)
    a, b = abs(a), abs(b)
    while b:
        a, b = b, a % b
    return a


def euclide_etendu(a: int, b: int) -> tuple[int, int, int]:
    """Renvoie (g, x, y) tels que a·x + b·y = g = pgcd(a, b) (identité de Bézout)."""
    _ent(a, b)
    vieux_r, r = a, b
    vieux_s, s = 1, 0
    vieux_t, t = 0, 1
    while r:
        q = vieux_r // r
        vieux_r, r = r, vieux_r - q * r
        vieux_s, s = s, vieux_s - q * s
        vieux_t, t = t, vieux_t - q * t
    if vieux_r < 0:                       # normalise g ≥ 0
        vieux_r, vieux_s, vieux_t = -vieux_r, -vieux_s, -vieux_t
    return (vieux_r, vieux_s, vieux_t)


def inverse_modulaire(a: int, n: int) -> int:
    """Inverse de a modulo n : x ∈ [0, n) tel que a·x ≡ 1 (mod n). ValueError si n ≤ 1 ou pgcd(a,n) ≠ 1."""
    _ent(a, n)
    if n <= 1:
        raise ValueError("module n > 1 requis")
    g, x, _ = euclide_etendu(a % n, n)
    if g != 1:
        raise ValueError(f"pas d'inverse : pgcd({a},{n}) = {g} ≠ 1")
    return x % n


def exp_modulaire(base: int, exposant: int, module: int) -> int:
    """base^exposant mod module (square-and-multiply). Exposant ≥ 0, module > 0. Exact."""
    _ent(base, exposant, module)
    if exposant < 0:
        raise ValueError("exposant ≥ 0 requis")
    if module <= 0:
        raise ValueError("module > 0 requis")
    resultat = 1 % module
    base %= module
    e = exposant
    while e > 0:
        if e & 1:
            resultat = (resultat * base) % module
        base = (base * base) % module
        e >>= 1
    return resultat


# Témoins déterministes : suffisants pour tout n < 3 317 044 064 679 887 385 961 981 (Sorenson & Webster).
_TEMOINS = (2, 3, 5, 7, 11, 13, 17, 19, 23, 29, 31, 37)


def est_premier(n: int) -> bool:
    """Primalité par Miller-Rabin DÉTERMINISTE (témoins prouvés pour n < 3.3·10²⁴). Exact dans ce domaine."""
    _ent(n)
    if n < 2:
        return False
    for p in _TEMOINS:
        if n % p == 0:
            return n == p
    d = n - 1
    r = 0
    while d % 2 == 0:
        d //= 2
        r += 1
    for a in _TEMOINS:
        if a >= n:
            continue
        x = pow(a, d, n)
        if x == 1 or x == n - 1:
            continue
        for _ in range(r - 1):
            x = (x * x) % n
            if x == n - 1:
                break
        else:
            return False
    return True


def rsa_chiffre(m: int, e: int, n: int) -> int:
    """Chiffrement RSA c = m^e mod n (0 ≤ m < n)."""
    _ent(m, e, n)
    if not (0 <= m < n):
        raise ValueError("message m hors [0, n)")
    return exp_modulaire(m, e, n)


def rsa_dechiffre(c: int, d: int, n: int) -> int:
    """Déchiffrement RSA m = c^d mod n."""
    _ent(c, d, n)
    return exp_modulaire(c, d, n)


if __name__ == "__main__":
    print("pgcd(48,36) :", pgcd(48, 36))
    print("euclide_etendu(240,46) :", euclide_etendu(240, 46))
    print("inverse de 3 mod 11 :", inverse_modulaire(3, 11))
    print("7^128 mod 13 :", exp_modulaire(7, 128, 13), "(pow:", pow(7, 128, 13), ")")
    print("premiers <30 :", [k for k in range(2, 30) if est_premier(k)])
    print("561 (Carmichael) premier ?", est_premier(561), "| 7919 ?", est_premier(7919))
    # RSA classique : p=61,q=53 -> n=3233, e=17, d=2753
    c = rsa_chiffre(65, 17, 3233)
    print("RSA chiffre(65) :", c, "| déchiffre :", rsa_dechiffre(c, 2753, 3233))
