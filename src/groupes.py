"""THÉORIE DES GROUPES (finis) — calculs EXACTS, FAUX=0 (mission formule/concept 2026-06-29).

Groupe cyclique ℤ/nℤ (addition mod n), groupe symétrique Sₙ (permutations) : ordre d'un élément, signature,
composition ; validation d'une table de Cayley (clôture, associativité, neutre, inverses) ; vérification du théorème
de Lagrange (l'ordre d'un élément divise l'ordre du groupe). EXACT, déterministe ; entrée invalide -> ValueError.

Couvre le sujet borné « Théorie des groupes ».
Vérifié en adverse par `valide_groupes.py` (ordres connus, signatures, Lagrange, table non-groupe rejetée).
"""
from __future__ import annotations

from math import gcd


def _pgcd_liste(xs):
    r = 0
    for x in xs:
        r = gcd(r, x)
    return r


def _ppcm(a, b):
    return a * b // gcd(a, b) if a and b else 0


def ordre_element_zn(g: int, n: int) -> int:
    """Ordre de g dans (ℤ/nℤ, +) = n / pgcd(g, n) (plus petit k>0 avec k·g ≡ 0 mod n)."""
    if not isinstance(n, int) or isinstance(n, bool) or n <= 0:
        raise ValueError("n entier > 0 requis")
    if not isinstance(g, int) or isinstance(g, bool):
        raise ValueError("g entier requis")
    g %= n
    return n // gcd(g, n) if g != 0 else 1


def _valide_perm(p):
    if not isinstance(p, (list, tuple)) or sorted(p) != list(range(len(p))):
        raise ValueError(f"permutation invalide (doit être une bijection de 0..n-1) : {p!r}")
    return tuple(p)


def compose_permutations(p, q):
    """Composition (p∘q)(i) = p(q(i)). p, q permutations de 0..n-1 de MÊME taille."""
    p, q = _valide_perm(p), _valide_perm(q)
    if len(p) != len(q):
        raise ValueError("permutations de tailles différentes")
    return tuple(p[q[i]] for i in range(len(p)))


def _cycles(p):
    p = _valide_perm(p)
    vus = [False] * len(p)
    longueurs = []
    for i in range(len(p)):
        if vus[i]:
            continue
        lg, j = 0, i
        while not vus[j]:
            vus[j] = True
            j = p[j]
            lg += 1
        longueurs.append(lg)
    return longueurs


def ordre_permutation(p) -> int:
    """Ordre d'une permutation = PPCM des longueurs de ses cycles."""
    longueurs = _cycles(p)
    r = 1
    for lg in longueurs:
        r = _ppcm(r, lg)
    return r


def signature_permutation(p) -> int:
    """Signature ε(p) = (−1)^(n − nombre de cycles) = +1 (paire) ou −1 (impaire)."""
    longueurs = _cycles(p)
    n = sum(longueurs)
    parite = (n - len(longueurs)) % 2
    return -1 if parite else 1


def est_groupe(table) -> bool:
    """Vrai ssi la table de Cayley (matrice n×n d'indices 0..n-1) définit un groupe : clôture (indices valides),
    élément neutre, associativité, inverses. Déterministe, exact."""
    n = len(table)
    if n == 0 or any(len(ligne) != n for ligne in table):
        raise ValueError("table de Cayley : matrice carrée non vide requise")
    for ligne in table:
        for x in ligne:
            if not isinstance(x, int) or isinstance(x, bool) or not (0 <= x < n):
                raise ValueError("table : entrées doivent être des indices 0..n-1 (clôture)")
    # élément neutre e : table[e][x] = x et table[x][e] = x pour tout x
    neutre = None
    for e in range(n):
        if all(table[e][x] == x and table[x][e] == x for x in range(n)):
            neutre = e
            break
    if neutre is None:
        return False
    # inverses : pour tout a, il existe b avec a·b = b·a = e
    for a in range(n):
        if not any(table[a][b] == neutre and table[b][a] == neutre for b in range(n)):
            return False
    # associativité : (a·b)·c = a·(b·c)
    for a in range(n):
        for b in range(n):
            for c in range(n):
                if table[table[a][b]][c] != table[a][table[b][c]]:
                    return False
    return True


def lagrange_divise(ordre_elem: int, ordre_groupe: int) -> bool:
    """Théorème de Lagrange (conséquence) : l'ordre d'un élément divise l'ordre du groupe."""
    if ordre_elem <= 0 or ordre_groupe <= 0:
        raise ValueError("ordres > 0 requis")
    return ordre_groupe % ordre_elem == 0


if __name__ == "__main__":
    print("ordre de 2 dans Z6 :", ordre_element_zn(2, 6), "| de 1 :", ordre_element_zn(1, 6), "| de 3 :", ordre_element_zn(3, 6))
    print("ordre perm (1,2,0) :", ordre_permutation((1, 2, 0)), "| (1,0,3,2) :", ordre_permutation((1, 0, 3, 2)))
    print("signature (1,0,2) :", signature_permutation((1, 0, 2)), "| (1,2,0) :", signature_permutation((1, 2, 0)))
    print("compose (1,2,0)∘(0,2,1) :", compose_permutations((1, 2, 0), (0, 2, 1)))
    z3 = [[0, 1, 2], [1, 2, 0], [2, 0, 1]]
    print("Z3 est un groupe :", est_groupe(z3))
    pas_groupe = [[0, 1, 2], [1, 0, 2], [2, 2, 0]]
    print("table cassée est un groupe :", est_groupe(pas_groupe))
    print("Lagrange : ordre 3 divise 6 :", lagrange_divise(3, 6), "| 4 divise 6 :", lagrange_divise(4, 6))
