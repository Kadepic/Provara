"""BIO-INFORMATIQUE / SÉQUENÇAGE — primitives EXACTES sur séquences ADN/chaînes, FAUX=0 (mission formule/concept).

Posture (identique à `physique`/`chimie`/`maths_discretes`) : le MÉCANISME est exact (définitions et algorithmes
classiques de comparaison de séquences), et l'abstention est STRUCTURELLE — toute entrée invalide (type, longueurs
incompatibles, base non-ADN, séquence vide pour un ratio) lève `ValueError` (jamais un résultat faux).

Couvre :
  - distance_hamming(s1, s2)  : nombre de positions où deux chaînes de MÊME longueur diffèrent.
  - taux_gc(seq)              : fraction (G+C)/longueur d'une séquence ADN (G/C, donc « contenu GC »).
  - complement_inverse(adn)   : brin complémentaire inverse (reverse complement) — A↔T, C↔G puis renversement.
  - distance_edition(s1, s2)  : distance de Levenshtein (insertion/suppression/substitution, coût 1) par
                                programmation dynamique exacte (arithmétique entière).

Stdlib uniquement, aucun chargement lourd. Vérifié en adverse par `valide_bioinfo.py`
(ancres externes connues + soundness : entrée invalide -> ValueError, jamais faux).
"""
from __future__ import annotations

# Bases ADN canoniques et leurs complémentaires (Watson–Crick).
_COMPLEMENT = {"A": "T", "T": "A", "C": "G", "G": "C"}
_BASES = frozenset(_COMPLEMENT)  # {'A','C','G','T'}


def _normalise_adn(seq) -> str:
    """Renvoie la séquence en majuscules après validation stricte (bases A/C/G/T seulement)."""
    if not isinstance(seq, str):
        raise ValueError(f"séquence ADN attendue (str), reçu {type(seq).__name__}")
    s = seq.upper()
    for base in s:
        if base not in _BASES:
            raise ValueError(f"base ADN invalide : {base!r} (attendu A/C/G/T)")
    return s


def distance_hamming(s1, s2) -> int:
    """Nombre de positions où s1 et s2 (MÊME longueur) diffèrent. Longueurs différentes -> ValueError."""
    if not isinstance(s1, str) or not isinstance(s2, str):
        raise ValueError("deux chaînes attendues")
    if len(s1) != len(s2):
        raise ValueError(f"longueurs différentes : {len(s1)} != {len(s2)} (Hamming non défini)")
    return sum(1 for a, b in zip(s1, s2) if a != b)


def taux_gc(seq) -> float:
    """Contenu GC = (nb G + nb C) / longueur. Base non-ADN -> ValueError ; séquence vide -> ValueError."""
    s = _normalise_adn(seq)
    if not s:
        raise ValueError("séquence vide : taux GC non défini")
    gc = sum(1 for base in s if base in ("G", "C"))
    return gc / len(s)


def complement_inverse(adn) -> str:
    """Brin complémentaire inverse (reverse complement) : complémente chaque base puis renverse l'ordre."""
    s = _normalise_adn(adn)
    return "".join(_COMPLEMENT[base] for base in reversed(s))


def distance_edition(s1, s2) -> int:
    """Distance de Levenshtein (insertion/suppression/substitution, coût unitaire) par programmation dynamique."""
    if not isinstance(s1, str) or not isinstance(s2, str):
        raise ValueError("deux chaînes attendues")
    n, m = len(s1), len(s2)
    if n == 0:
        return m
    if m == 0:
        return n
    # Ligne précédente : transformer "" en s2[:j] coûte j (j insertions).
    prev = list(range(m + 1))
    for i in range(1, n + 1):
        cur = [i] + [0] * m
        ci = s1[i - 1]
        for j in range(1, m + 1):
            cout_sub = 0 if ci == s2[j - 1] else 1
            cur[j] = min(
                prev[j] + 1,        # suppression de s1[i-1]
                cur[j - 1] + 1,     # insertion de s2[j-1]
                prev[j - 1] + cout_sub,  # substitution / coïncidence
            )
        prev = cur
    return prev[m]
