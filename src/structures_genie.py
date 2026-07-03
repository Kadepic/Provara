"""STRUCTURES / GÉNIE CIVIL — résistance des matériaux EXACTE (poutres, sections), appel direct, FAUX=0.

Sujet borné « Structures (ponts, bâtiments) ». Posture identique à `physique`/`maths_discretes` : le MÉCANISME
(les formules de la résistance des matériaux, RDM) est EXACT, et l'abstention est STRUCTURELLE — toute entrée
hors domaine (section nulle/négative, dimension ≤ 0, aire ≤ 0, type/NaN/inf) lève `ValueError` (JAMAIS un nombre
faux). Conservateur : un faux négatif (abstention) est toléré, un faux POSITIF est interdit.

Unités SI cohérentes (l'appelant fournit des SI homogènes) :
  • longueurs en mètres (m), forces en newtons (N), moments en N·m, module de Young E en pascals (Pa = N/m²) ;
  • un moment quadratique I est en m⁴, une aire A en m², une contrainte en Pa, une flèche en m.

COUVERTURE (formules classiques, vérifiées en adverse par `valide_structures_genie.py`) :
  - contrainte_flexion(M, I, y) = M·y/I            (contrainte normale de flexion, théorie d'Euler-Bernoulli) ;
  - contrainte_traction(F, A)   = F/A              (contrainte normale de traction/compression simple) ;
  - moment_quadratique_rectangle(b, h) = b·h³/12   (moment quadratique d'une section rectangulaire / axe neutre) ;
  - moment_quadratique_cercle(d)       = π·d⁴/64   (moment quadratique d'une section circulaire pleine) ;
  - module_resistance_rectangle(b, h)  = b·h²/6    (module de flexion W = I/(h/2)) ;
  - fleche_poutre_appuyee_charge_centree(F, L, E, I) = F·L³/(48·E·I)  (flèche au milieu, appuis simples, charge
    ponctuelle centrée) ;
  - flambement_euler(E, I, L) = π²·E·I/L²          (charge critique d'Euler, poteau bi-articulé).

Seule constante : π (math.pi). Sortie arrondie à 10 chiffres significatifs (précision honnête, pas un faux exact).
"""
from __future__ import annotations

import math

_CHIFFRES_SIGNIFICATIFS = 10


def _sig(x: float, n: int = _CHIFFRES_SIGNIFICATIFS) -> float:
    """Arrondit à n chiffres significatifs (précision honnête, indépendante de la magnitude)."""
    if x == 0:
        return 0.0
    return float(f"{x:.{n}g}")


def _fini(*xs) -> None:
    """Exige des nombres réels FINIS (rejette bool, str, None, NaN, ±inf)."""
    for x in xs:
        if not isinstance(x, (int, float)) or isinstance(x, bool):
            raise ValueError(f"nombre réel attendu, reçu {x!r}")
        if not math.isfinite(x):
            raise ValueError(f"valeur non finie interdite, reçu {x!r}")


def _pos(*xs) -> None:
    """Exige des nombres réels finis STRICTEMENT POSITIFS (dimensions, aires, moments quadratiques, module E)."""
    _fini(*xs)
    for x in xs:
        if x <= 0:
            raise ValueError(f"grandeur strictement positive attendue, reçu {x!r}")


# ── CONTRAINTES (Pa) ─────────────────────────────────────────────────────────────────────────────────────────────
def contrainte_flexion(M, I, y) -> float:
    """Contrainte normale de flexion σ = M·y/I (Euler-Bernoulli). M moment (N·m), I moment quadratique (m⁴) > 0,
    y distance à la fibre neutre (m, signée : >0 fibre tendue). I ≤ 0 -> ValueError."""
    _fini(M, y)
    _pos(I)
    return _sig(M * y / I)


def contrainte_traction(F, A) -> float:
    """Contrainte normale de traction/compression σ = F/A. F effort normal (N), A aire de section (m²) > 0.
    A ≤ 0 -> ValueError."""
    _fini(F)
    _pos(A)
    return _sig(F / A)


# ── CARACTÉRISTIQUES GÉOMÉTRIQUES DE SECTION ─────────────────────────────────────────────────────────────────────
def moment_quadratique_rectangle(b, h) -> float:
    """Moment quadratique d'une section rectangulaire autour de son axe neutre : I = b·h³/12 (m⁴).
    b largeur, h hauteur (dans le plan de flexion). Dimension ≤ 0 -> ValueError."""
    _pos(b, h)
    return _sig(b * h ** 3 / 12.0)


def moment_quadratique_cercle(d) -> float:
    """Moment quadratique d'une section circulaire pleine : I = π·d⁴/64 (m⁴). d diamètre. d ≤ 0 -> ValueError."""
    _pos(d)
    return _sig(math.pi * d ** 4 / 64.0)


def module_resistance_rectangle(b, h) -> float:
    """Module de flexion (section modulus) d'un rectangle : W = b·h²/6 = I/(h/2) (m³). σ_max = M/W.
    Dimension ≤ 0 -> ValueError."""
    _pos(b, h)
    return _sig(b * h ** 2 / 6.0)


# ── DÉFORMATION / STABILITÉ ──────────────────────────────────────────────────────────────────────────────────────
def fleche_poutre_appuyee_charge_centree(F, L, E, I) -> float:
    """Flèche au milieu d'une poutre sur appuis simples, charge ponctuelle F centrée : δ = F·L³/(48·E·I) (m).
    F charge (N), L portée (m) > 0, E module de Young (Pa) > 0, I moment quadratique (m⁴) > 0.
    L, E ou I ≤ 0 -> ValueError."""
    _fini(F)
    _pos(L, E, I)
    return _sig(F * L ** 3 / (48.0 * E * I))


def flambement_euler(E, I, L) -> float:
    """Charge critique de flambement d'Euler (poteau bi-articulé) : P_cr = π²·E·I/L² (N).
    E module de Young (Pa) > 0, I moment quadratique (m⁴) > 0, L longueur (m) > 0. Argument ≤ 0 -> ValueError."""
    _pos(E, I, L)
    return _sig(math.pi ** 2 * E * I / L ** 2)


if __name__ == "__main__":
    print("I rectangle (0.1×0.2) :", moment_quadratique_rectangle(0.1, 0.2))
    print("σ flexion (M=1000, I=I_rect, y=0.1) :",
          contrainte_flexion(1000, moment_quadratique_rectangle(0.1, 0.2), 0.1))
    print("σ traction (10000 N / 0.01 m²) :", contrainte_traction(10000, 0.01))
    print("flèche (F=1000, L=2, E=210e9, I=I_rect) :",
          fleche_poutre_appuyee_charge_centree(1000, 2, 210e9, moment_quadratique_rectangle(0.1, 0.2)))
    print("Euler (E=210e9, I=I_rect, L=3) :", flambement_euler(210e9, moment_quadratique_rectangle(0.1, 0.2), 3))
