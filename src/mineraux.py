"""
mineraux.py — Échelle de Mohs (dureté des minéraux) : faits établis, déterministes.

L'échelle de Mohs (Friedrich Mohs, 1812) classe la dureté relative des minéraux par
le test de rayure : un minéral raye tout minéral de dureté inférieure. Les dix minéraux
de référence et leurs degrés sont des CONVENTIONS fixées (ordinaux, non linéaires) :

    talc 1, gypse 2, calcite 3, fluorine 4, apatite 5,
    orthose 6, quartz 7, topaze 8, corindon 9, diamant 10.

SOUNDNESS (FAUX=0) : tout nom hors de ce catalogue de référence -> ValueError (abstention).
On ne devine JAMAIS la dureté d'un minéral non référencé. Fonctions pures, déterministes.
"""

# Catalogue de référence de l'échelle de Mohs (les dix minéraux étalons).
_MOHS = {
    "talc": 1,
    "gypse": 2,
    "calcite": 3,
    "fluorine": 4,
    "apatite": 5,
    "orthose": 6,
    "quartz": 7,
    "topaze": 8,
    "corindon": 9,
    "diamant": 10,
}


def _norme(mineral):
    """Normalise un nom de minéral et exige qu'il soit au catalogue, sinon abstention."""
    if not isinstance(mineral, str):
        raise ValueError(f"minéral invalide (type {type(mineral).__name__})")
    cle = mineral.strip().lower()
    if cle not in _MOHS:
        raise ValueError(f"minéral hors catalogue Mohs : {mineral!r}")
    return cle


def durete_mohs(mineral):
    """Degré de dureté Mohs (entier 1..10) du minéral étalon. Hors catalogue -> ValueError."""
    return _MOHS[_norme(mineral)]


def raye(m1, m2):
    """True si m1 raye m2, i.e. durete(m1) > durete(m2). Stricte (égalité -> ne raye pas)."""
    return durete_mohs(m1) > durete_mohs(m2)


def plus_dur(m1, m2):
    """Retourne le nom (normalisé) du plus dur des deux ; égalité -> ValueError (pas de gagnant)."""
    d1 = durete_mohs(m1)
    d2 = durete_mohs(m2)
    if d1 == d2:
        raise ValueError(f"dureté égale : {m1!r} et {m2!r} ne se rayent pas")
    return _norme(m1) if d1 > d2 else _norme(m2)


def catalogue():
    """Copie du catalogue de référence (nom -> degré Mohs)."""
    return dict(_MOHS)


if __name__ == "__main__":
    print("diamant:", durete_mohs("diamant"))
    print("diamant raye quartz:", raye("diamant", "quartz"))
    print("plus dur(quartz, calcite):", plus_dur("quartz", "calcite"))
