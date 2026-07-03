"""
cryobiologie.py — Congélation et conservation (cryobiologie).

Capacité FAUX=0 : mécanismes EXACTS et établis, fonctions pures déterministes.
Abstention (ValueError) sur toute entrée physiquement invalide — JAMAIS un faux.

Faits/formules :
  - vitesse_refroidissement(Ti, Tf, temps) = (Ti - Tf)/temps   [°C/min]
  - point_congelation_solution(b, Kf=1.86, i=1) = -Kf*i*b       [°C]
      abaissement cryoscopique de l'eau, Kf = 1.86 °C·kg/mol (loi de Raoult).
  - azote_liquide() = -196 °C                                   (fait, point d'ébullition usuel)

stdlib uniquement, aucune dépendance.
"""

# Constante cryoscopique molale de l'eau (loi de Raoult, abaissement du point
# de congélation). Valeur établie : 1.86 °C·kg/mol.
KF_EAU = 1.86

# Point d'ébullition du diazote liquide à pression atmosphérique : -195.79 °C,
# arrondi usuel en cryobiologie à -196 °C.
T_AZOTE_LIQUIDE = -196.0


def _num(x, nom):
    """Renvoie x en float si c'est un nombre réel fini, sinon ValueError."""
    if isinstance(x, bool) or not isinstance(x, (int, float)):
        raise ValueError(f"{nom} doit etre un nombre reel, recu {x!r}")
    v = float(x)
    if v != v or v in (float("inf"), float("-inf")):
        raise ValueError(f"{nom} doit etre fini, recu {x!r}")
    return v


def vitesse_refroidissement(T_initiale, T_finale, temps_min):
    """Vitesse de refroidissement (°C/min) = (T_initiale - T_finale)/temps_min.

    Soundness : temps_min <= 0 -> ValueError (durée nulle/négative invalide).
    Exemple : refroidir de 20 a -180 en 10 min -> 20.0 °C/min.
    """
    Ti = _num(T_initiale, "T_initiale")
    Tf = _num(T_finale, "T_finale")
    t = _num(temps_min, "temps_min")
    if t <= 0:
        raise ValueError(f"temps_min doit etre > 0, recu {temps_min!r}")
    return (Ti - Tf) / t


def point_congelation_solution(molalite, Kf=KF_EAU, i=1):
    """Point de congélation (°C) d'une solution aqueuse = -Kf * i * molalité.

    molalite : concentration molale (mol de soluté / kg de solvant), >= 0.
    Kf       : constante cryoscopique molale du solvant (eau : 1.86 °C·kg/mol).
    i        : facteur de van't Hoff (nombre de particules par formule), >= 1.

    Soundness : molalite < 0 -> ValueError ; Kf <= 0 -> ValueError ; i < 1 -> ValueError.
    Exemple : NaCl 1 molal (i=2) -> -3.72 °C.
    """
    b = _num(molalite, "molalite")
    k = _num(Kf, "Kf")
    vh = _num(i, "i")
    if b < 0:
        raise ValueError(f"molalite doit etre >= 0, recu {molalite!r}")
    if k <= 0:
        raise ValueError(f"Kf doit etre > 0, recu {Kf!r}")
    if vh < 1:
        raise ValueError(f"i (van't Hoff) doit etre >= 1, recu {i!r}")
    return -k * vh * b


def azote_liquide():
    """Température du diazote liquide à pression atmosphérique : -196 °C (fait)."""
    return T_AZOTE_LIQUIDE
