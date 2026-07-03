"""
PROPRIÉTÉS DES MATÉRIAUX (mesurables) — loi de Hooke & élasticité linéaire (mandat Yohan : couvrir le borné).

Même posture FAUX=0 que `physique` / `chimie` (la réalité juge, jamais un faux) :
  • Le MÉCANISME (les formules de la mécanique des matériaux) est EXACT — garantie structurelle.
      - contrainte normale      σ = F / A            [Pa = N/m²]
      - déformation relative     ε = ΔL / L0          [sans dimension]
      - loi de Hooke             σ = E · ε            (E = module de Young, domaine élastique linéaire)
      - module de Young          E = σ / ε            [Pa]
      - allongement              ΔL = F · L0 / (A · E) [m]  (combinaison directe des trois relations ci-dessus)
  • Les valeurs renvoyées sont ARRONDIES à 10 chiffres significatifs — précision HONNÊTE (nettoie le bruit flottant
    sans prétendre à une exactitude au-delà des entrées fournies par l'appelant).
  • Aucune constante matériau n'est codée en dur : E (210 GPa pour l'acier, etc.) est une DONNÉE fournie par
    l'appelant, pas une invention du module.

ABSTENTION STRUCTURELLE (vérifiée en adverse par `valide_proprietes_materiaux.py`) :
  - aire A ≤ 0                       -> ValueError (une section physique est strictement positive)
  - longueur initiale L0 ≤ 0         -> ValueError (une longueur de référence est strictement positive)
  - module de Young E ≤ 0            -> ValueError (un module élastique est strictement positif)
  - déformation ε = 0 dans E = σ/ε   -> ValueError (division par zéro : E indéterminé)
  - argument non numérique / booléen -> ValueError
  La force F et l'allongement ΔL peuvent être de signe quelconque (traction > 0 / compression < 0).

Conservateur : faux négatif (abstention) toléré, faux POSITIF interdit. Déterministe. Stdlib uniquement.
"""
from __future__ import annotations

_CHIFFRES_SIGNIFICATIFS = 10


def _sig(x: float, n: int = _CHIFFRES_SIGNIFICATIFS) -> float:
    """Arrondit à n chiffres significatifs (précision honnête, indépendante de la magnitude)."""
    if x == 0:
        return 0.0
    return float(f"{x:.{n}g}")


def _num(x) -> float:
    """Exige un nombre réel fini (rejette bool, str, None, NaN, inf) -> sinon ValueError."""
    if isinstance(x, bool) or not isinstance(x, (int, float)):
        raise ValueError("argument non numérique")
    f = float(x)
    if f != f or f in (float("inf"), float("-inf")):
        raise ValueError("argument non fini")
    return f


def _pos(x, nom: str) -> float:
    """Exige un nombre strictement positif -> sinon ValueError."""
    f = _num(x)
    if f <= 0:
        raise ValueError(f"{nom} doit être strictement positif")
    return f


def contrainte(F, A) -> float:
    """Contrainte normale σ = F / A  [Pa]. A (aire de section) doit être > 0 ; F de signe quelconque."""
    f = _num(F)
    a = _pos(A, "aire A")
    return _sig(f / a)


def deformation(dL, L0) -> float:
    """Déformation relative ε = ΔL / L0  [sans unité]. L0 doit être > 0 ; ΔL de signe quelconque."""
    d = _num(dL)
    l0 = _pos(L0, "longueur L0")
    return _sig(d / l0)


def module_young(contrainte_val, deformation_val) -> float:
    """Module de Young E = σ / ε  [Pa]. ε = 0 -> ValueError (E indéterminé)."""
    s = _num(contrainte_val)
    e = _num(deformation_val)
    if e == 0:
        raise ValueError("déformation nulle : module de Young indéterminé")
    return _sig(s / e)


def hooke_contrainte(E, deformation_val) -> float:
    """Loi de Hooke : σ = E · ε  [Pa]. E (module de Young) doit être > 0 ; ε de signe quelconque."""
    e_mod = _pos(E, "module de Young E")
    eps = _num(deformation_val)
    return _sig(e_mod * eps)


def hooke_deformation(contrainte_val, E) -> float:
    """Loi de Hooke inverse : ε = σ / E  [sans unité]. E doit être > 0 ; σ de signe quelconque."""
    s = _num(contrainte_val)
    e_mod = _pos(E, "module de Young E")
    return _sig(s / e_mod)


def allongement(F, L0, A, E) -> float:
    """Allongement ΔL = F · L0 / (A · E)  [m]. A>0, L0>0, E>0 ; F de signe quelconque."""
    f = _num(F)
    l0 = _pos(L0, "longueur L0")
    a = _pos(A, "aire A")
    e_mod = _pos(E, "module de Young E")
    return _sig(f * l0 / (a * e_mod))
