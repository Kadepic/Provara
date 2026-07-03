"""
retraite.py — Pension de retraite : MÉCANISME de calcul d'un régime par annuités (proratisation).

Mécanismes EXACTS / définitions normatives ÉTABLIES (régime de retraite « par annuités », tel que décrit
par l'OIT et appliqué p.ex. au régime général français — CNAV/INSEE) : chaque sortie est une opération
arithmétique exacte sur des grandeurs observées (salaire, taux, durées d'assurance). AUCUNE valeur-pays
n'est codée en dur (ni durée requise, ni taux plein, ni taux de décote d'un pays donné) : SEUL le calcul
générique est implémenté, les paramètres réglementaires sont FOURNIS par l'appelant. Aucune estimation,
aucune heuristique, aucun nombre inventé.

FORMULES (mécanisme générique du régime par annuités) :

  • pension(salaire_reference, taux_liquidation, duree_assurance, duree_requise)
        = salaire_reference · taux_liquidation · (duree_assurance / duree_requise)

      C'est la pension d'un régime par annuités : un salaire de référence, multiplié par un TAUX DE
      LIQUIDATION (le « taux plein » du régime), PRORATISÉ par le rapport entre la durée d'assurance
      effective et la durée requise pour le taux plein. Le coefficient (duree_assurance / duree_requise)
      est le « coefficient de proratisation ».
        - TAUX PLEIN : si duree_assurance == duree_requise, le coefficient vaut 1 -> pension = salaire·taux.
        - PRORATA : une durée incomplète réduit proportionnellement la pension (½ de la durée -> ½ pension).
      Mécanisme GÉNÉRIQUE, NON plafonné : on calcule la formule littérale (un régime particulier peut
      plafonner le coefficient à 1, mais ce plafond est une règle-pays que l'appelant applique s'il le veut).

  • taux_remplacement(pension, dernier_salaire) = pension / dernier_salaire · 100   (en %)
      Part du dernier salaire que remplace la pension. Ex. pension 1000 / salaire 2000 = 50 %.

  • decote(trimestres_manquants, taux_decote_par_trimestre) = trimestres_manquants · taux_decote_par_trimestre
      DÉCOTE PROPORTIONNELLE : taux de minoration total = nombre de trimestres manquants multiplié par le
      taux de décote par trimestre (un taux de réduction, fraction par trimestre). Ex. 8 trimestres ·
      0.0125 = 0.10 (soit 10 % de décote). Mécanisme générique, NON plafonné (un régime peut limiter le
      nombre de trimestres pris en compte : règle-pays laissée à l'appelant).

ABSTENTION STRUCTURELLE (faux positif INTERDIT, jamais un faux -> ValueError) :
  • duree_assurance <= 0 ou duree_requise <= 0 (durée nulle/négative -> proratisation indéfinie) -> ValueError.
  • taux hors [0, 1] (taux_liquidation, taux_decote_par_trimestre : un taux est une fraction) -> ValueError.
  • montant négatif (salaire_reference, pension) -> ValueError.
  • dernier_salaire <= 0 (dénominateur du taux de remplacement nul) -> ValueError.
  • trimestres_manquants négatif ou non entier (un trimestre est une unité de compte entière) -> ValueError.
  • valeur non finie (NaN/inf) / non numérique / booléen -> ValueError.

Sorties arrondies à 6 décimales. stdlib uniquement, fonctions pures déterministes.
"""
from __future__ import annotations

import math

_PRECISION = 6


def _reel_fini(x, nom):
    """Convertit en float fini, sinon ValueError (abstention). Le booléen est refusé (1/0 déguisé)."""
    if isinstance(x, bool):
        raise ValueError(f"{nom} booléen refusé : {x!r}")
    try:
        v = float(x)
    except (TypeError, ValueError):
        raise ValueError(f"{nom} non numérique : {x!r}")
    if not math.isfinite(v):
        raise ValueError(f"{nom} non fini : {x!r}")
    return v


def _montant(x, nom):
    """Montant monétaire : float fini >= 0, sinon ValueError."""
    v = _reel_fini(x, nom)
    if v < 0.0:
        raise ValueError(f"{nom} doit être >= 0 (montant) : {v}")
    return v


def _duree_positive(x, nom):
    """Durée d'assurance/requise : float fini strictement > 0, sinon ValueError."""
    v = _reel_fini(x, nom)
    if v <= 0.0:
        raise ValueError(f"{nom} doit être > 0 (durée) : {v}")
    return v


def _taux_unitaire(x, nom):
    """Taux : float fini dans [0, 1], sinon ValueError (un taux est une fraction)."""
    v = _reel_fini(x, nom)
    if not (0.0 <= v <= 1.0):
        raise ValueError(f"{nom} hors [0, 1] : {v}")
    return v


def _trimestres(x, nom):
    """Nombre de trimestres : entier (ou flottant à valeur entière) fini >= 0, sinon ValueError."""
    v = _reel_fini(x, nom)
    if v < 0.0:
        raise ValueError(f"{nom} doit être >= 0 : {v}")
    if v != math.floor(v):
        raise ValueError(f"{nom} doit être entier (trimestres) : {v}")
    return v


def coefficient_proratisation(duree_assurance, duree_requise):
    """Coefficient de proratisation = duree_assurance / duree_requise (1 au taux plein). Non plafonné."""
    da = _duree_positive(duree_assurance, "duree_assurance")
    dr = _duree_positive(duree_requise, "duree_requise")
    return round(da / dr, _PRECISION)


def pension(salaire_reference, taux_liquidation, duree_assurance, duree_requise):
    """Pension d'un régime par annuités = salaire · taux · (duree_assurance / duree_requise)."""
    sal = _montant(salaire_reference, "salaire_reference")
    taux = _taux_unitaire(taux_liquidation, "taux_liquidation")
    da = _duree_positive(duree_assurance, "duree_assurance")
    dr = _duree_positive(duree_requise, "duree_requise")
    return round(sal * taux * (da / dr), _PRECISION)


def taux_remplacement(pension, dernier_salaire):
    """Taux de remplacement = pension / dernier_salaire * 100 (en %)."""
    p = _montant(pension, "pension")
    sal = _montant(dernier_salaire, "dernier_salaire")
    if sal <= 0.0:
        raise ValueError("dernier_salaire doit être > 0 (taux de remplacement indéfini sinon)")
    return round(p / sal * 100.0, _PRECISION)


def decote(trimestres_manquants, taux_decote_par_trimestre):
    """Décote proportionnelle = trimestres_manquants * taux_decote_par_trimestre (taux de minoration total)."""
    n = _trimestres(trimestres_manquants, "trimestres_manquants")
    t = _taux_unitaire(taux_decote_par_trimestre, "taux_decote_par_trimestre")
    return round(n * t, _PRECISION)
