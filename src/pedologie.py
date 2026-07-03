"""
pedologie.py — Pédologie (science des sols) : texture et porosité (mécanismes établis).

Mécanismes EXACTS / définitions sourcées (science des sols) :

  • classe_texture(pourcent_sable, pourcent_limon, pourcent_argile)
      Classe texturale d'un sol à partir de ses trois fractions granulométriques
      (sable / limon / argile), qui forment une partition de la terre fine et
      DOIVENT donc sommer à 100 % (à tol près). Triangle des textures de l'USDA,
      version SIMPLIFIÉE (3 classes) :
        - argile > 40 %  -> 'argileux'   (clay)
        - sable  > 70 %  -> 'sableux'    (sandy)
        - sinon          -> 'limoneux'   (loamy)
      L'ordre des tests suit la spécification (argile, puis sable, puis sinon).
      Les deux premières conditions sont mutuellement exclusives sur une entrée
      valide : argile>40 ET sable>70 impliquerait une somme > 110 % > 100 %,
      donc rejetée par la contrainte de somme.
      Réf. : USDA Soil Survey Manual, soil texture triangle.

  • porosite(densite_apparente, densite_reelle=2.65) = 1 − da/dr
      Porosité totale d'un sol (fraction du volume occupé par les vides), déduite
      de la densité apparente (bulk density, da) et de la densité réelle des
      particules (particle density, dr). dr ≈ 2.65 g/cm³ pour un sol minéral
      dominé par le quartz (valeur de référence standard en pédologie).
      Ex. da=1.3 -> 1 − 1.3/2.65 ≈ 0.509.

ABSTENTION STRUCTURELLE (faux positif INTERDIT, jamais un faux -> ValueError) :
  • une fraction granulométrique non numérique, non finie, < 0 ou > 100 -> ValueError.
  • somme des trois fractions ≠ 100 (à ±tol) -> ValueError.
  • densite_apparente <= 0 ou densite_reelle <= 0, ou non finies -> ValueError.
  • densite_apparente > densite_reelle (porosité négative, physiquement impossible :
      la densité apparente ne peut excéder la densité des particules) -> ValueError.

stdlib uniquement, fonctions pures déterministes, sortie arrondie à 6 décimales.
"""

import math

__all__ = [
    "classe_texture",
    "porosite",
    "DENSITE_REELLE_REF",
    "SOMME_FRACTIONS",
]

# ── Faits / conventions sourcés (constantes) ──
# Densité réelle (particle density) de référence d'un sol minéral quartzeux.
DENSITE_REELLE_REF = 2.65
# Somme attendue des trois fractions granulométriques (partition en %).
SOMME_FRACTIONS = 100.0


def _reel_fini(x, nom):
    """Convertit en float fini, sinon ValueError."""
    try:
        v = float(x)
    except (TypeError, ValueError):
        raise ValueError(f"{nom} non numérique : {x!r}")
    if not math.isfinite(v):
        raise ValueError(f"{nom} non fini : {x!r}")
    return v


def _fraction(x, nom):
    """Fraction granulométrique en pourcentage : float fini dans [0, 100]."""
    v = _reel_fini(x, nom)
    if v < 0.0 or v > 100.0:
        raise ValueError(f"{nom} hors [0, 100] : {v}")
    return v


def classe_texture(pourcent_sable, pourcent_limon, pourcent_argile, tol=1e-6):
    """
    Classe texturale (USDA simplifiée) d'un sol à partir de ses fractions (%).

    pourcent_sable / pourcent_limon / pourcent_argile : fractions dans [0, 100],
    qui DOIVENT sommer à 100 % (à ±tol près).
    Renvoie 'argileux' (argile>40), 'sableux' (sable>70), sinon 'limoneux'.

    Fraction invalide, somme ≠ 100 (±tol) -> ValueError.
    """
    s = _fraction(pourcent_sable, "pourcent_sable")
    li = _fraction(pourcent_limon, "pourcent_limon")
    a = _fraction(pourcent_argile, "pourcent_argile")
    t = _reel_fini(tol, "tol")
    if t < 0.0:
        raise ValueError(f"tol négatif : {t}")
    somme = s + li + a
    if abs(somme - SOMME_FRACTIONS) > t:
        raise ValueError(f"les fractions ne somment pas à 100 % : {somme}")
    # Ordre de la spécification : argile, puis sable, puis sinon.
    if a > 40.0:
        return "argileux"
    if s > 70.0:
        return "sableux"
    return "limoneux"


def porosite(densite_apparente, densite_reelle=2.65):
    """
    Porosité totale d'un sol = 1 − da/dr.

    densite_apparente (da) : densité apparente (bulk density), > 0.
    densite_reelle    (dr) : densité réelle des particules, > 0 (défaut 2.65).
    Ex. da=1.3 -> 1 − 1.3/2.65 ≈ 0.509434.

    da <= 0, dr <= 0, valeurs non finies, ou da > dr (porosité négative,
    physiquement impossible) -> ValueError.
    """
    da = _reel_fini(densite_apparente, "densite_apparente")
    dr = _reel_fini(densite_reelle, "densite_reelle")
    if da <= 0.0:
        raise ValueError(f"densite_apparente non strictement positive : {da}")
    if dr <= 0.0:
        raise ValueError(f"densite_reelle non strictement positive : {dr}")
    if da > dr:
        raise ValueError(
            f"densite_apparente ({da}) > densite_reelle ({dr}) : porosité négative impossible"
        )
    return round(1.0 - da / dr, 6)
