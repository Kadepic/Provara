"""
TRANSPORT MEMBRANAIRE — borné « Membranes, organites » (biologie cellulaire établie).

Même posture que `physique` / `chimie` (la réalité juge, jamais un faux) :
  • Le MÉCANISME est EXACT et établi :
      - tonicité / osmose = définitions canoniques de la biologie cellulaire (le solvant — l'eau — migre
        vers le compartiment le PLUS concentré en soluté ; le qualificatif hypo/hyper/iso décrit la solution
        EXTERNE par rapport à l'intérieur de la cellule) ;
      - diffusion à travers une membrane = 1ʳᵉ loi de Fick (A. Fick, 1855) : J = D·A·Δc/e.
  • La sortie numérique est ARRONDIE à 6 chiffres significatifs — précision honnête.

GARANTIES (vérifiées en adverse par `valide_transport_membranaire.py`) :
  - concentration < 0 -> ValueError (une concentration de soluté est ≥ 0) ;
  - aire ≤ 0, épaisseur ≤ 0, coefficient de diffusion ≤ 0, Δc < 0 -> ValueError ;
  - entrée non numérique / booléenne -> ValueError ;
  - déterministe ; conservateur (abstention/ValueError tolérée, jamais un faux positif).

Conventions de signature : pour `tonicite(c_int, c_ext)` et `sens_osmose(c_int, c_ext)`, le 1ᵉʳ argument est la
concentration en soluté à l'INTÉRIEUR de la cellule, le 2ᵉ celle du milieu EXTÉRIEUR (mêmes unités, p. ex. en %
massique ou en mol/L — seule la comparaison compte). Pour `flux_fick`, les unités SI cohérentes donnent J en mol/s.
"""
from __future__ import annotations

SOURCE = "1ʳᵉ loi de Fick (Fick 1855) ; définitions osmose/tonicité (biologie cellulaire établie)"

_CHIFFRES_SIGNIFICATIFS = 6

# Étiquettes de tonicité (solution EXTERNE vis-à-vis de l'intérieur cellulaire).
HYPOTONIQUE = "hypotonique"      # ext < int  -> entrée d'eau dans la cellule, elle gonfle (turgescence)
HYPERTONIQUE = "hypertonique"    # ext > int  -> sortie d'eau, la cellule se ratatine (plasmolyse)
ISOTONIQUE = "isotonique"        # ext = int  -> pas de flux net d'eau

# Étiquettes de sens de l'osmose (déplacement NET du solvant — l'eau).
ENTREE = "entree"                # l'eau entre dans la cellule (intérieur plus concentré)
SORTIE = "sortie"                # l'eau sort de la cellule (extérieur plus concentré)
EQUILIBRE = "equilibre"          # pas de mouvement net


def _sig(x: float, n: int = _CHIFFRES_SIGNIFICATIFS) -> float:
    """Arrondit à n chiffres significatifs (précision honnête, indépendante de la magnitude)."""
    if x == 0:
        return 0.0
    return float(f"{x:.{n}g}")


def _num(x) -> float:
    """Valide un scalaire numérique réel (rejette bool et non-nombres) -> float, sinon ValueError."""
    if isinstance(x, bool) or not isinstance(x, (int, float)):
        raise ValueError(f"valeur numérique attendue, reçu {x!r}")
    return float(x)


def _conc(x) -> float:
    """Valide une CONCENTRATION (numérique, ≥ 0)."""
    v = _num(x)
    if v < 0:
        raise ValueError(f"concentration négative interdite : {v}")
    return v


def tonicite(c_interieur, c_exterieur) -> str:
    """
    Qualifie la solution EXTERNE par rapport à l'intérieur de la cellule.
      ext < int -> 'hypotonique' (l'eau entre, la cellule gonfle) ;
      ext > int -> 'hypertonique' (l'eau sort, plasmolyse) ;
      ext = int -> 'isotonique'.
    Concentration < 0 -> ValueError.
    """
    ci = _conc(c_interieur)
    ce = _conc(c_exterieur)
    if ce < ci:
        return HYPOTONIQUE
    if ce > ci:
        return HYPERTONIQUE
    return ISOTONIQUE


def sens_osmose(c_interieur, c_exterieur) -> str:
    """
    Sens du flux NET d'eau (osmose) : l'eau migre vers le compartiment le PLUS concentré en soluté.
      int > ext -> 'entree' (l'eau entre dans la cellule) ;
      ext > int -> 'sortie' (l'eau sort vers le milieu hypertonique) ;
      égal       -> 'equilibre'.
    Concentration < 0 -> ValueError.
    """
    ci = _conc(c_interieur)
    ce = _conc(c_exterieur)
    if ci > ce:
        return ENTREE
    if ce > ci:
        return SORTIE
    return EQUILIBRE


def flux_fick(coef_diffusion, aire, gradient_concentration, epaisseur) -> float:
    """
    1ʳᵉ loi de Fick (diffusion passive à travers une membrane) :
        J = D · A · Δc / e
    où D = coefficient de diffusion, A = aire de la membrane, Δc = différence de concentration, e = épaisseur.
    Garde de domaine : D > 0, A > 0, e > 0, Δc ≥ 0 (sinon ValueError). Sortie arrondie à 6 chiffres significatifs.
    """
    d = _num(coef_diffusion)
    a = _num(aire)
    dc = _num(gradient_concentration)
    e = _num(epaisseur)
    if d <= 0:
        raise ValueError(f"coefficient de diffusion ≤ 0 interdit : {d}")
    if a <= 0:
        raise ValueError(f"aire ≤ 0 interdite : {a}")
    if e <= 0:
        raise ValueError(f"épaisseur ≤ 0 interdite : {e}")
    if dc < 0:
        raise ValueError(f"gradient de concentration négatif interdit : {dc}")
    return _sig(d * a * dc / e)
