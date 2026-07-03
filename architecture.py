"""ARCHITECTURE DES ORDINATEURS — représentation des nombres, FAUX=0 (mission formule/concept 2026-06-29).

Conversions base 2 / 16, codage en complément à deux (entiers signés sur n bits) et décodage, addition binaire avec
détection de débordement (overflow). Mécanisme EXACT (arithmétique binaire), abstention STRUCTURELLE : valeur hors
de l'intervalle représentable sur n bits -> ValueError (jamais un codage faux silencieux).

Couvre le sujet borné « Architecture des ordinateurs » (volet représentation, calculable).
Vérifié en adverse par `valide_architecture.py` (complément à 2 connu, intervalles, overflow).
"""
from __future__ import annotations


def _bits_ok(bits):
    if not isinstance(bits, int) or isinstance(bits, bool) or bits <= 0:
        raise ValueError("nombre de bits > 0 requis")


def vers_binaire(n: int, bits: int) -> str:
    """Représentation binaire NON signée de n sur `bits` bits. ValueError si n ∉ [0, 2^bits)."""
    _bits_ok(bits)
    if not isinstance(n, int) or isinstance(n, bool) or not (0 <= n < 2 ** bits):
        raise ValueError(f"n ∈ [0, 2^{bits}) requis")
    return format(n, f"0{bits}b")


def vers_hexa(n: int) -> str:
    """Représentation hexadécimale (majuscules, sans préfixe) d'un entier ≥ 0."""
    if not isinstance(n, int) or isinstance(n, bool) or n < 0:
        raise ValueError("entier ≥ 0 requis")
    return format(n, "X")


def depuis_binaire(s: str) -> int:
    """Entier non signé à partir d'une chaîne binaire."""
    if not isinstance(s, str) or not s or any(c not in "01" for c in s):
        raise ValueError("chaîne binaire (0/1) attendue")
    return int(s, 2)


def complement_a_deux(n: int, bits: int) -> int:
    """Codage en complément à deux : entier signé n -> motif binaire (entier non signé) sur `bits` bits.
    Intervalle valide : [−2^(bits−1), 2^(bits−1) − 1]. ValueError sinon."""
    _bits_ok(bits)
    if not isinstance(n, int) or isinstance(n, bool):
        raise ValueError("entier attendu")
    bas, haut = -(2 ** (bits - 1)), 2 ** (bits - 1) - 1
    if not (bas <= n <= haut):
        raise ValueError(f"n ∈ [{bas}, {haut}] requis pour {bits} bits")
    return n & (2 ** bits - 1)


def depuis_complement_a_deux(motif: int, bits: int) -> int:
    """Décodage : motif binaire (entier non signé sur `bits` bits) -> entier signé en complément à deux."""
    _bits_ok(bits)
    if not isinstance(motif, int) or isinstance(motif, bool) or not (0 <= motif < 2 ** bits):
        raise ValueError(f"motif ∈ [0, 2^{bits}) requis")
    if motif >= 2 ** (bits - 1):
        return motif - 2 ** bits
    return motif


def addition_binaire(a: int, b: int, bits: int) -> tuple[int, bool]:
    """Addition de deux entiers signés en complément à deux sur `bits` bits. Renvoie (somme_signée, débordement).
    Le débordement signale que le résultat n'est pas représentable (ex. 127+1 sur 8 bits)."""
    _bits_ok(bits)
    ca, cb = complement_a_deux(a, bits), complement_a_deux(b, bits)
    brut = (ca + cb) & (2 ** bits - 1)
    resultat = depuis_complement_a_deux(brut, bits)
    debordement = (a + b) != resultat
    return (resultat, debordement)


if __name__ == "__main__":
    print("vers_binaire(5, 8) :", vers_binaire(5, 8))
    print("vers_hexa(255) :", vers_hexa(255), "| vers_hexa(4096) :", vers_hexa(4096))
    print("complément à 2 de -1 / 8 bits :", complement_a_deux(-1, 8), "(=", vers_binaire(complement_a_deux(-1, 8), 8), ")")
    print("complément à 2 de -128 / 8 bits :", complement_a_deux(-128, 8))
    print("décodage 255 / 8 bits :", depuis_complement_a_deux(255, 8))
    print("addition 100+50 / 8 bits :", addition_binaire(100, 50, 8), "(débordement !)")
    print("addition 100+20 / 8 bits :", addition_binaire(100, 20, 8))
