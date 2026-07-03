"""FRACTALES — dimension d'auto-similarité, primitive EXACTE et directement appelable, FAUX=0
(mission formule/concept 2026-06-29).

Posture identique à `physique`/`maths_discretes` : le MÉCANISME est exact et l'abstention est STRUCTURELLE.

MÉCANISME (dimension de Hausdorff–Besicovitch pour un fractal STRICTEMENT auto-similaire) :
    Si un objet se décompose en N copies de lui-même, chacune réduite d'un facteur de contraction `facteur`
    (le tout couvre l'objet sans recouvrement essentiel), alors sa dimension d'auto-similarité vaut

        D = ln(N) / ln(facteur)

    Justification : à l'échelle 1/facteur on voit N copies ; pour un objet de dimension D la mesure se multiplie
    par facteur^D quand on agrandit d'un facteur `facteur`, donc N = facteur^D, d'où D = log(N)/log(facteur).
    (La base du logarithme s'élimine dans le rapport — résultat indépendant de la base.)

CAS DE RÉFÉRENCE (vérifiés en adverse par `valide_fractales.py`) :
    • Ensemble de Cantor          N=2,  facteur=3  -> ln2/ln3  ≈ 0.6309
    • Flocon/courbe de Koch       N=4,  facteur=3  -> ln4/ln3  ≈ 1.2619
    • Triangle de Sierpiński      N=3,  facteur=2  -> ln3/ln2  ≈ 1.5850
    • Tapis de Sierpiński         N=8,  facteur=3  -> ln8/ln3  ≈ 1.8928
    • Éponge de Menger            N=20, facteur=3  -> ln20/ln3 ≈ 2.7268
    • Segment plein               N=2,  facteur=2  -> 1   (objet de dimension entière 1)
    • Carré plein                 N=4,  facteur=2  -> 2   (objet de dimension entière 2)
    • Cube plein                  N=8,  facteur=2  -> 3   (objet de dimension entière 3)
    • Courbe de Peano (remplit)   N=9,  facteur=3  -> 2

ABSTENTION (jamais un résultat faux) :
    • N < 1            -> ValueError  (il faut au moins une copie)
    • facteur <= 1     -> ValueError  (sans contraction stricte la formule n'a pas de sens : ln(facteur) ≤ 0)
    • type non numérique / booléen / NaN / infini -> ValueError

Sortie ARRONDIE à 10 chiffres significatifs (précision honnête : double précision porte ~15-16 chiffres ;
on n'en revendique que 10). Déterministe. Conservateur : faux négatif (abstention) toléré, faux POSITIF interdit.
"""
from __future__ import annotations

import math

_CHIFFRES_SIGNIFICATIFS = 10


def _sig(x: float, n: int = _CHIFFRES_SIGNIFICATIFS) -> float:
    """Arrondit à n chiffres significatifs (précision honnête, indépendante de la magnitude)."""
    if x == 0:
        return 0.0
    return float(f"{x:.{n}g}")


def _nombre_fini(x) -> bool:
    return (isinstance(x, (int, float)) and not isinstance(x, bool) and math.isfinite(x))


def dimension_similarite(N, facteur) -> float:
    """Dimension d'auto-similarité D = ln(N)/ln(facteur).

    N       : nombre de copies réduites (réel ≥ 1).
    facteur : facteur de contraction linéaire (réel > 1).
    Lève ValueError si N < 1, facteur ≤ 1, ou entrée non numérique/non finie.
    """
    if not _nombre_fini(N) or not _nombre_fini(facteur):
        raise ValueError("N et facteur doivent être des nombres réels finis")
    if N < 1:
        raise ValueError(f"N ≥ 1 attendu (au moins une copie), reçu {N!r}")
    if facteur <= 1:
        raise ValueError(f"facteur > 1 attendu (contraction stricte), reçu {facteur!r}")
    return _sig(math.log(N) / math.log(facteur))


# ── Registre de fractals CONNUS (commodité ; chaque valeur passe par le même mécanisme exact) ────────────────────
FRACTALES_CONNUES = {
    "cantor": (2, 3),
    "koch": (4, 3),
    "sierpinski_triangle": (3, 2),
    "sierpinski_carpet": (8, 3),
    "menger_sponge": (20, 3),
    "peano": (9, 3),
    "segment": (2, 2),
    "carre_plein": (4, 2),
    "cube_plein": (8, 2),
}


def dimension_connue(nom: str) -> float:
    """Dimension d'un fractal nommé du registre. Lève ValueError si le nom est inconnu (abstention)."""
    if not isinstance(nom, str):
        raise ValueError("nom (str) attendu")
    cle = nom.strip().lower()
    if cle not in FRACTALES_CONNUES:
        raise ValueError(f"fractal inconnu : {nom!r}")
    N, facteur = FRACTALES_CONNUES[cle]
    return dimension_similarite(N, facteur)


def fractales_connues() -> tuple:
    """Noms des fractals du registre (triés, déterministe)."""
    return tuple(sorted(FRACTALES_CONNUES))
