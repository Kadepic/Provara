"""CARDINALITÉ & DÉNOMBRABILITÉ — primitives EXACTES (entiers), FAUX=0 (mission formule/concept 2026-06-29).

Posture (identique à `maths_discretes`/`physique`/`chimie`) : le MÉCANISME est exact (arithmétique entière, aucune
approximation flottante), et l'abstention est STRUCTURELLE — toute entrée invalide lève `ValueError` (jamais un
résultat faux). Conservateur : faux négatif (abstention) toléré, faux POSITIF interdit.

Couvre le sujet borné « Cardinalité, dénombrabilité » :
  • cardinal_ensemble(liste)  — nombre d'éléments DISTINCTS d'un ensemble fini (|S|).
  • cardinal_parties(n)       — |P(S)| = 2^n pour |S|=n (théorème de Cantor, cas fini : l'ensemble des parties est
                                strictement plus grand ; pour n fini c'est exactement 2^n).
  • couple_cantor(i,j)        — fonction de couplage ℕ×ℕ → ℕ : (i+j)(i+j+1)/2 + j. BIJECTIVE → prouve |ℕ×ℕ| = |ℕ|.
  • decouple_cantor(z)        — bijection inverse ℕ → ℕ×ℕ (arithmétique entière exacte via math.isqrt).
  • est_denombrable(nom)      — verdict pour des ensembles CLASSIQUES à cardinalité CERTAINE :
        dénombrables (|·| ≤ ℵ₀) : ℕ, ℤ, ℚ, ℕ×ℕ, ensembles finis → True ;
        non dénombrables (Cantor, argument diagonal) : ℝ, P(ℕ), [0,1], ℂ, irrationnels → False.
    Un nom INCONNU lève ValueError (on ne devine pas la cardinalité d'un ensemble arbitraire).

Vérifié en adverse par `valide_cardinalite.py` (ancres externes + soundness : entrée invalide -> ValueError).
"""
from __future__ import annotations

import math


def _entier_pos(*xs) -> None:
    for x in xs:
        if not isinstance(x, int) or isinstance(x, bool) or x < 0:
            raise ValueError(f"entier >= 0 attendu, recu {x!r}")


# ── CARDINAL FINI ────────────────────────────────────────────────────────────────────────────────────────────────
def cardinal_ensemble(liste) -> int:
    """|S| = nombre d'éléments DISTINCTS de l'itérable `liste` (un ensemble ne compte pas les répétitions).

    Les éléments doivent être hachables (sinon la notion d'« élément distinct » n'est pas décidable ici → abstention).
    """
    try:
        it = iter(liste)
    except TypeError:
        raise ValueError("itérable attendu")
    if isinstance(liste, (str, bytes)):
        # une chaîne est ambiguë (suite de caractères ?) — on refuse plutôt que de deviner.
        raise ValueError("passer une liste/ensemble d'éléments, pas une chaîne")
    vus = set()
    for e in it:
        try:
            vus.add(e)
        except TypeError:
            raise ValueError(f"élément non hachable : {e!r}")
    return len(vus)


def cardinal_parties(n: int) -> int:
    """|P(S)| = 2^n quand |S| = n (théorème de Cantor, cas fini). Entier exact."""
    _entier_pos(n)
    return 1 << n


# ── COUPLAGE DE CANTOR ℕ×ℕ ↔ ℕ (bijection) ────────────────────────────────────────────────────────────────────────
def couple_cantor(i: int, j: int) -> int:
    """π(i,j) = (i+j)(i+j+1)/2 + j. Bijection ℕ×ℕ → ℕ ⇒ ℕ×ℕ est dénombrable. Entier exact."""
    _entier_pos(i, j)
    s = i + j
    return s * (s + 1) // 2 + j


def decouple_cantor(z: int):
    """π⁻¹ : ℕ → ℕ×ℕ, inverse EXACT de couple_cantor (math.isqrt → aucun flottant)."""
    _entier_pos(z)
    w = (math.isqrt(8 * z + 1) - 1) // 2   # numéro de diagonale : plus grand w avec w(w+1)/2 ≤ z
    t = w * (w + 1) // 2
    j = z - t
    i = w - j
    return (i, j)


# ── DÉNOMBRABILITÉ D'ENSEMBLES CLASSIQUES ─────────────────────────────────────────────────────────────────────────
# Verdicts CERTAINS (théorèmes établis). Tout autre nom -> abstention (ValueError).
_DENOMBRABLES = {
    "N", "ℕ", "naturels",
    "Z", "ℤ", "entiers", "entiers_relatifs",
    "Q", "ℚ", "rationnels",
    "N×N", "NxN", "N*N", "ℕ×ℕ", "ℕxℕ",
    "Z×Z", "ZxZ", "ℤ×ℤ",
    "fini", "ensemble_fini",
    "premiers", "P",  # nombres premiers (sous-ensemble de ℕ, infini dénombrable)
}
_NON_DENOMBRABLES = {
    "R", "ℝ", "reels",
    "[0,1]", "[0;1]", "segment_unite",
    "P(N)", "P(ℕ)", "parties_de_N", "2^N", "2^ℕ",
    "C", "ℂ", "complexes",
    "R\\Q", "ℝ\\ℚ", "irrationnels",
    "{0,1}^N", "suites_binaires",
}


def est_denombrable(nom: str) -> bool:
    """True si l'ensemble nommé est dénombrable (|·| ≤ ℵ₀), False sinon. Nom inconnu -> ValueError (abstention)."""
    if not isinstance(nom, str):
        raise ValueError("nom d'ensemble (chaîne) attendu")
    cle = nom.strip()
    if cle in _DENOMBRABLES:
        return True
    if cle in _NON_DENOMBRABLES:
        return False
    raise ValueError(f"cardinalité inconnue pour {nom!r} (ensembles classiques uniquement)")
