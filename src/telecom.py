"""TÉLÉCOMMUNICATIONS — capacité de canal et grandeurs, FAUX=0 (mission formule/concept 2026-06-29).

Capacité de Shannon-Hartley (C = B·log₂(1+S/N)), débit de Nyquist (2·B·log₂(M)), gain en décibels (10·log₁₀(P₂/P₁)),
longueur d'onde (λ = c/f). Mécanisme EXACT, sortie 6 chiffres significatifs. Abstention STRUCTURELLE : bande passante
≤ 0, SNR < 0, nombre de niveaux < 2, fréquence ≤ 0 -> ValueError.

Couvre le sujet borné « Télécommunications ».
Vérifié en adverse par `valide_telecom.py` (Shannon B=3000/SNR=7 -> 9000 b/s, gain 20 dB…).
"""
from __future__ import annotations

import math

C_LUMIERE = 299_792_458.0
_SIG = 6


def _sig(x):
    if x == 0:
        return 0.0
    return float(f"{x:.{_SIG}g}")


def _num(*xs):
    for x in xs:
        if isinstance(x, bool) or not isinstance(x, (int, float)):
            raise ValueError(f"nombre attendu, reçu {x!r}")


def capacite_shannon(bande_passante, snr) -> float:
    """Capacité maximale d'un canal bruité : C = B·log₂(1 + S/N) (bits/s). B > 0, SNR (linéaire) ≥ 0."""
    _num(bande_passante, snr)
    if bande_passante <= 0:
        raise ValueError("bande passante > 0 requise")
    if snr < 0:
        raise ValueError("rapport signal/bruit ≥ 0 requis")
    return _sig(bande_passante * math.log2(1 + snr))


def debit_nyquist(bande_passante, niveaux) -> float:
    """Débit binaire maximal sans bruit (Nyquist) : D = 2·B·log₂(M) (bits/s). M ≥ 2 niveaux entiers."""
    _num(bande_passante)
    if bande_passante <= 0:
        raise ValueError("bande passante > 0 requise")
    if not isinstance(niveaux, int) or isinstance(niveaux, bool) or niveaux < 2:
        raise ValueError("nombre de niveaux entier ≥ 2 requis")
    return _sig(2 * bande_passante * math.log2(niveaux))


def gain_db(puissance_sortie, puissance_entree) -> float:
    """Gain en décibels : G = 10·log₁₀(P_sortie/P_entrée). Puissances > 0."""
    _num(puissance_sortie, puissance_entree)
    if puissance_sortie <= 0 or puissance_entree <= 0:
        raise ValueError("puissances > 0 requises")
    return _sig(10 * math.log10(puissance_sortie / puissance_entree))


def longueur_onde(frequence) -> float:
    """Longueur d'onde λ = c/f (m) dans le vide. f > 0."""
    _num(frequence)
    if frequence <= 0:
        raise ValueError("fréquence > 0 requise")
    return _sig(C_LUMIERE / frequence)


def snr_depuis_db(snr_db) -> float:
    """Convertit un SNR en dB vers le rapport linéaire : 10^(dB/10)."""
    _num(snr_db)
    return _sig(10 ** (snr_db / 10))


if __name__ == "__main__":
    print("Shannon B=1000,SNR=1 :", capacite_shannon(1000, 1), "b/s (= B, car log2(2)=1)")
    print("Shannon B=3000,SNR=7 :", capacite_shannon(3000, 7), "b/s")
    print("Nyquist B=3000,M=2 :", debit_nyquist(3000, 2), "| M=16 :", debit_nyquist(3000, 16))
    print("gain 100/1 :", gain_db(100, 1), "dB | 2/1 :", gain_db(2, 1), "dB")
    print("λ FM 100 MHz :", longueur_onde(100e6), "m")
    print("SNR 30 dB -> linéaire :", snr_depuis_db(30))
