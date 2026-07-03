"""
CROISSANCE BACTÉRIENNE BORNÉE — modèle de croissance exponentielle par doublement, mécanisme EXACT.

Même posture que `physique` / `chimie` (la réalité juge, jamais un faux) :
  • Le MÉCANISME est une identité mathématique EXACTE — le modèle de croissance exponentielle d'une culture
    bactérienne en phase de croissance non limitée : N(t) = N0 · 2^(t/g), où g est le temps de génération
    (temps de doublement). C'est le modèle standard de microbiologie (croissance binaire par fission).
  • Les trois fonctions sont les inversions mutuelles d'une seule identité :
        N(t) = N0 · 2^(t/g)
        g    = t · ln2 / ln(Nt/N0)            (résolu pour g)
        n    = log2(Nt/N0)  = (t/g)           (nombre de générations = doublements)
  • La sortie est ARRONDIE à 6 chiffres significatifs (précision honnête).

GARANTIES (vérifiées en adverse par `valide_croissance_bacterienne.py`) :
  - N0 <= 0 (pas de population initiale)              -> ValueError ;
  - g  <= 0 (temps de génération non physique)        -> ValueError ;
  - t  < 0  (temps négatif)                           -> ValueError ;
  - temps_generation : Nt <= 0, t <= 0, ou Nt <= N0   -> ValueError (hors du modèle de croissance ; sinon
    log(Nt/N0) = 0 -> division par zéro, ou g négatif) ;
  - nombre_generations : Nt <= 0 ou Nt < N0           -> ValueError (générations < 0 hors du modèle) ;
  - entrée non numérique / booléenne / NaN / inf      -> ValueError ;
  - déterministe ; conservateur (abstention/ValueError tolérée, faux POSITIF interdit).
"""
from __future__ import annotations

import math

_LN2 = math.log(2.0)                 # 0.6931471805599453 — base du modèle de doublement
_CHIFFRES_SIGNIFICATIFS = 6


def _sig(x: float, n: int = _CHIFFRES_SIGNIFICATIFS) -> float:
    """Arrondit à n chiffres significatifs (précision honnête, indépendante de la magnitude)."""
    if x == 0:
        return 0.0
    return float(f"{x:.{n}g}")


def _num(x) -> bool:
    """True ssi nombre réel fini, NON booléen (True/False rejetés : ce ne sont pas des grandeurs)."""
    return isinstance(x, (int, float)) and not isinstance(x, bool) and math.isfinite(x)


def population(N0, t, temps_generation):
    """N(t) = N0 · 2^(t/g) — population après un temps t, temps de génération g.

    N0 > 0, temps_generation (g) > 0, t >= 0. Toute autre entrée -> ValueError (abstention).
    """
    if not (_num(N0) and _num(t) and _num(temps_generation)):
        raise ValueError("population : entrées numériques finies non booléennes requises")
    if N0 <= 0:
        raise ValueError("population : N0 doit être > 0 (population initiale)")
    if temps_generation <= 0:
        raise ValueError("population : temps_generation (g) doit être > 0")
    if t < 0:
        raise ValueError("population : t doit être >= 0")
    return _sig(N0 * 2.0 ** (t / temps_generation))


def temps_generation(N0, Nt, t):
    """g = t · ln2 / ln(Nt/N0) — temps de génération déduit de N0 -> Nt en un temps t.

    N0 > 0, Nt > 0, t > 0, Nt > N0 (croissance stricte ; sinon ln(Nt/N0) <= 0). Sinon -> ValueError.
    """
    if not (_num(N0) and _num(Nt) and _num(t)):
        raise ValueError("temps_generation : entrées numériques finies non booléennes requises")
    if N0 <= 0:
        raise ValueError("temps_generation : N0 doit être > 0")
    if Nt <= 0:
        raise ValueError("temps_generation : Nt doit être > 0")
    if t <= 0:
        raise ValueError("temps_generation : t doit être > 0")
    if Nt <= N0:
        raise ValueError("temps_generation : Nt doit être > N0 (modèle de croissance)")
    return _sig(t * _LN2 / math.log(Nt / N0))


def nombre_generations(N0, Nt):
    """n = log2(Nt/N0) — nombre de générations (doublements) pour passer de N0 à Nt.

    N0 > 0, Nt > 0, Nt >= N0 (n >= 0 ; le déclin est hors du modèle). Sinon -> ValueError.
    """
    if not (_num(N0) and _num(Nt)):
        raise ValueError("nombre_generations : entrées numériques finies non booléennes requises")
    if N0 <= 0:
        raise ValueError("nombre_generations : N0 doit être > 0")
    if Nt <= 0:
        raise ValueError("nombre_generations : Nt doit être > 0")
    if Nt < N0:
        raise ValueError("nombre_generations : Nt doit être >= N0 (modèle de croissance, n >= 0)")
    return _sig(math.log2(Nt / N0))


if __name__ == "__main__":
    # CAS de référence : E. coli, N0=1000, g=20 min, t=60 min -> 8000 (3 générations).
    print("population(1000, 60, 20) =", population(1000, 60, 20))          # 8000.0
    print("nombre_generations(1000, 8000) =", nombre_generations(1000, 8000))  # 3.0
    print("temps_generation(1000, 8000, 60) =", temps_generation(1000, 8000, 60))  # 20.0
