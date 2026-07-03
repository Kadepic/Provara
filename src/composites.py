"""COMPOSITES — loi des mélanges (rule of mixtures), primitives EXACTES directement appelables, FAUX=0
(mission formule/concept 2026-06-29).

Posture identique à `physique`/`chimie`/`maths_discretes` : le MÉCANISME est une formule EXACTE de mécanique des
matériaux composites, et l'abstention est STRUCTURELLE — toute entrée hors domaine lève `ValueError`
(jamais un résultat faux). Conservateur : faux négatif (abstention) toléré, faux POSITIF interdit.

MÉCANISME (matériau biphasé fibre + matrice, fraction volumique de fibre Vf ∈ [0,1]) :
  • module_young_composite(Vf, Ef, Em) = Vf·Ef + (1−Vf)·Em
        → borne SUPÉRIEURE de Voigt (chargement PARALLÈLE aux fibres, iso-déformation). Module d'Young effectif.
  • densite_composite(Vf, rho_f, rho_m) = Vf·rho_f + (1−Vf)·rho_m
        → masse volumique effective (additivité volumique exacte, sans porosité).
  • borne_inferieure_reuss(Vf, Ef, Em) = 1 / ( Vf/Ef + (1−Vf)/Em )
        → borne INFÉRIEURE de Reuss (chargement TRANSVERSE aux fibres, iso-contrainte). Moyenne harmonique.

Propriété d'encadrement (vérifiée en adverse) : Reuss ≤ Voigt pour tout Vf ∈ [0,1] (bornes de Voigt–Reuss/HS).
Cas-types : Vf=0 → propriété de la matrice ; Vf=1 → propriété de la fibre.

La sortie est ARRONDIE à 10 chiffres significatifs — précision honnête (les formules sont exactes ; ce sont les
entrées Vf, Ef, Em, rho qui portent l'incertitude expérimentale). Vérifié par `valide_composites.py`
(ancres externes connues + soundness : domaine invalide → ValueError, jamais faux).
"""
from __future__ import annotations

_CHIFFRES_SIGNIFICATIFS = 10


def _r(x: float, n: int = _CHIFFRES_SIGNIFICATIFS) -> float:
    """Arrondit à n chiffres significatifs (précision honnête, indépendante de la magnitude)."""
    if x == 0:
        return 0.0
    return float(f"{x:.{n}g}")


def _num(x) -> bool:
    return isinstance(x, (int, float)) and not isinstance(x, bool)


def _exige_fraction(Vf) -> None:
    if not _num(Vf):
        raise ValueError(f"fraction volumique Vf numérique attendue, reçu {Vf!r}")
    if not (0.0 <= Vf <= 1.0):
        raise ValueError(f"fraction volumique Vf ∈ [0,1] attendue, reçu {Vf!r}")


def _exige_positif(*xs) -> None:
    for x in xs:
        if not _num(x):
            raise ValueError(f"valeur numérique attendue, reçu {x!r}")
        if x <= 0:
            raise ValueError(f"grandeur strictement positive attendue, reçu {x!r}")


def module_young_composite(Vf, Ef, Em) -> float:
    """Module d'Young du composite — loi des mélanges / borne SUPÉRIEURE de Voigt (fibres parallèles, iso-strain).

    E = Vf·Ef + (1−Vf)·Em.  Vf ∈ [0,1] ; Ef (fibre) et Em (matrice) modules strictement positifs (mêmes unités).
    """
    _exige_fraction(Vf)
    _exige_positif(Ef, Em)
    return _r(Vf * Ef + (1.0 - Vf) * Em)


def densite_composite(Vf, rho_f, rho_m) -> float:
    """Masse volumique du composite par additivité volumique : rho = Vf·rho_f + (1−Vf)·rho_m.

    Vf ∈ [0,1] ; rho_f (fibre) et rho_m (matrice) masses volumiques strictement positives (mêmes unités).
    """
    _exige_fraction(Vf)
    _exige_positif(rho_f, rho_m)
    return _r(Vf * rho_f + (1.0 - Vf) * rho_m)


def borne_inferieure_reuss(Vf, Ef, Em) -> float:
    """Borne INFÉRIEURE de Reuss du module (chargement transverse, iso-contrainte) : 1/(Vf/Ef + (1−Vf)/Em).

    Vf ∈ [0,1] ; Ef et Em strictement positifs (le dénominateur est alors toujours > 0, jamais de division par 0).
    """
    _exige_fraction(Vf)
    _exige_positif(Ef, Em)
    return _r(1.0 / (Vf / Ef + (1.0 - Vf) / Em))
