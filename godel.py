"""GÖDEL — numérotation de Gödel (cœur TECHNIQUE bijectif, exact) + énoncés des théorèmes d'incomplétude comme FAITS.

Posture (identique à `maths_discretes`/`physique`) : le MÉCANISME est EXACT et déterministe (arithmétique entière,
factorisation unique en facteurs premiers — théorème fondamental de l'arithmétique), et l'abstention est STRUCTURELLE :
toute entrée invalide ou hors catalogue lève `ValueError` (jamais un résultat inventé).

Numérotation de Gödel
---------------------
À une suite de symboles [s_0, …, s_{n-1}] on associe l'entier  N = ∏_{i=0}^{n-1} p_i^{code(s_i)}  où p_0=2, p_1=3,
p_2=5, … sont les nombres premiers successifs et code(s) ≥ 1 est le code du symbole dans l'alphabet fixé.
La factorisation unique garantit la BIJECTION entre suites valides et numéros de Gödel valides :
`decode_godel(godel_numero(suite)) == suite`. Deux suites différentes -> deux numéros différents.

Un numéro est VALIDE ssi sa factorisation n'utilise QUE le segment initial des premiers (2,3,5,…,p_{n-1}) sans trou,
et que chaque exposant est le code d'un symbole de l'alphabet — sinon ce n'est pas l'image d'une suite -> ValueError.

Les théorèmes d'incomplétude eux-mêmes sont fournis comme ÉNONCÉS de référence (faits mathématiques établis,
Gödel 1931) via `theoreme(n)` ; tout n hors {1,2} -> abstention.
"""
from __future__ import annotations

# Alphabet fixe d'un langage arithmétique du premier ordre. Codes ≥ 1, uniques.
ALPHABET = {
    '0': 1,    # zéro
    'S': 2,    # successeur
    '+': 3,
    '*': 4,
    '=': 5,
    '(': 6,
    ')': 7,
    ',': 8,
    '¬': 9,    # négation
    '∨': 10,   # disjonction
    '∧': 11,   # conjonction
    '→': 12,   # implication
    '↔': 13,   # équivalence
    '∀': 14,   # quantificateur universel
    '∃': 15,   # quantificateur existentiel
    'x': 16,   # variable
    'y': 17,   # variable
    'z': 18,   # variable
}
# Carte inverse code -> symbole (codes uniques garantis ci-dessous).
_INVERSE = {c: s for s, c in ALPHABET.items()}
assert len(_INVERSE) == len(ALPHABET), "codes d'alphabet non uniques"


def _premiers(m: int) -> list[int]:
    """Liste des m premiers nombres premiers : [2, 3, 5, 7, 11, …]."""
    primes: list[int] = []
    cand = 2
    while len(primes) < m:
        if all(cand % p for p in primes):
            primes.append(cand)
        cand += 1
    return primes


def _factorise(n: int) -> dict[int, int]:
    """Factorisation premier -> exposant (n ≥ 2). Trial division exacte."""
    facteurs: dict[int, int] = {}
    d = 2
    while d * d <= n:
        while n % d == 0:
            facteurs[d] = facteurs.get(d, 0) + 1
            n //= d
        d += 1
    if n > 1:
        facteurs[n] = facteurs.get(n, 0) + 1
    return facteurs


def code_symbole(symbole: str) -> int:
    """Code (≥1) d'un symbole de l'alphabet ; symbole hors alphabet -> ValueError."""
    if symbole not in ALPHABET:
        raise ValueError(f"symbole hors alphabet : {symbole!r}")
    return ALPHABET[symbole]


def godel_numero(suite_symboles) -> int:
    """Numéro de Gödel d'une suite NON VIDE de symboles de l'alphabet.

    N = ∏ p_i^{code(s_i)}. Suite vide ou symbole inconnu -> ValueError.
    """
    if not isinstance(suite_symboles, (list, tuple)):
        raise ValueError("suite_symboles doit être une liste/tuple de symboles")
    if len(suite_symboles) == 0:
        raise ValueError("suite vide : pas de numéro de Gödel")
    primes = _premiers(len(suite_symboles))
    n = 1
    for p, s in zip(primes, suite_symboles):
        if s not in ALPHABET:
            raise ValueError(f"symbole hors alphabet : {s!r}")
        n *= p ** ALPHABET[s]
    return n


def decode_godel(numero) -> list[str]:
    """Inverse de `godel_numero` : reconstruit la suite de symboles.

    numero doit être l'image d'une suite valide : factorisation = segment initial des premiers (sans trou) et chaque
    exposant = code d'un symbole. Sinon (numéro ≤ 1, non entier, trou de premier, code inconnu) -> ValueError.
    """
    if not isinstance(numero, int) or isinstance(numero, bool):
        raise ValueError("numéro entier attendu")
    if numero < 2:
        raise ValueError("numéro de Gödel valide ≥ 2 (1 = suite vide, exclue)")
    facteurs = _factorise(numero)
    primes_utilises = sorted(facteurs)
    attendus = _premiers(len(primes_utilises))
    if primes_utilises != attendus:
        raise ValueError("factorisation non conforme : trou dans le segment initial des premiers")
    suite: list[str] = []
    for p in attendus:
        code = facteurs[p]
        if code not in _INVERSE:
            raise ValueError(f"exposant {code} sur le premier {p} : code hors alphabet")
        suite.append(_INVERSE[code])
    return suite


_THEOREMES = {
    1: ("Premier théorème d'incomplétude (Gödel, 1931) : tout système formel cohérent, effectivement axiomatisable et "
        "assez puissant pour exprimer l'arithmétique élémentaire est incomplet — il existe un énoncé arithmétique vrai "
        "qui n'y est ni démontrable ni réfutable."),
    2: ("Second théorème d'incomplétude (Gödel, 1931) : un tel système cohérent ne peut pas démontrer sa propre "
        "cohérence ; l'énoncé Coh(T) n'est pas un théorème de T."),
}


def theoreme(n: int = 1) -> str:
    """Énoncé de référence du n-ième théorème d'incomplétude (n ∈ {1, 2}). Hors catalogue -> ValueError."""
    if not isinstance(n, int) or isinstance(n, bool) or n not in _THEOREMES:
        raise ValueError("n doit être 1 (premier théorème) ou 2 (second théorème)")
    return _THEOREMES[n]
