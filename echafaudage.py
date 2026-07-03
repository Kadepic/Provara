"""
G3 — RETIRER L'ÉCHAFAUDAGE ET MESURER (l'ablation).

Principe directeur d'AUTOS (budget d'échafaudage, Décision D) : chaque brique
posée à la main est un aveu que l'émergence n'a pas suffi À CET ENDROIT. Donc on
RETIRE chaque brique et on MESURE : était-elle PORTEUSE (sans elle, on ne
bootstrap plus) ou SUPERFLUE (on couvre pareil sans) ?

Résultat : la DOSE MINIMALE d'échafaudage — le plus petit jeu de briques qui
bootstrap encore la même couverture. Un chiffre dur, falsifiable, pas une intuition.

Ce module n'est pas un générateur : c'est un instrument de mesure sur G2.
"""

from __future__ import annotations

from generateur import GenerateurBriques
from juge import Limites, juge


def _resout(generateur, tache, limites, n: int = 30) -> bool:
    """Vrai si au moins un candidat passe visible ET held-out (un vrai succès)."""
    for code in generateur.propose(tache.prompt, n):
        if juge(code, tache.tests, limites).passe and \
           (not tache.tests_held_out or juge(code, tache.tests_held_out, limites).passe):
            return True
    return False


def couverture(squelettes, remplisseurs, taches, limites) -> set[str]:
    """L'ensemble des tâches qu'une bibliothèque donnée résout à froid."""
    g = GenerateurBriques(seed=0, squelettes=squelettes, remplisseurs=remplisseurs)
    return {t.id for t in taches if _resout(g, t, limites)}


def briques(squelettes, remplisseurs) -> list:
    """Liste identifiable de toutes les briques (squelettes + remplisseurs)."""
    bs = [("sq", None, sq) for sq, _ in squelettes]
    for trou, vals in remplisseurs.items():
        bs += [("rmp", trou, v) for v in vals]
    return bs


def retire(squelettes, remplisseurs, brique):
    """Renvoie (squelettes, remplisseurs) privés de la brique donnée."""
    kind, trou, val = brique
    if kind == "sq":
        sq2 = [(s, h) for (s, h) in squelettes if s != val]
        return sq2, remplisseurs
    rmp2 = {t: [v for v in vals if not (t == trou and v == val)]
            for t, vals in remplisseurs.items()}
    return squelettes, rmp2


def ablation(taches, limites, squelettes=None, remplisseurs=None) -> list:
    """
    Pour chaque brique : la retirer et mesurer la couverture. Renvoie une liste de
    (brique, porteuse: bool, couverture_sans). 'porteuse' = la couverture baisse sans elle.
    """
    g0 = GenerateurBriques()
    squelettes = squelettes if squelettes is not None else g0.squelettes
    remplisseurs = remplisseurs if remplisseurs is not None else g0.remplisseurs

    base = couverture(squelettes, remplisseurs, taches, limites)
    rapport = []
    for b in briques(squelettes, remplisseurs):
        sq, rmp = retire(squelettes, remplisseurs, b)
        cov = couverture(sq, rmp, taches, limites)
        rapport.append((b, cov != base, cov))
    return rapport


def minimal(taches, limites, squelettes=None, remplisseurs=None):
    """
    Échafaudage MINIMAL : on retire gloutonnement toute brique dont l'absence ne
    change pas la couverture. Ce qui reste est porteur. Renvoie (squelettes, remplisseurs).
    """
    g0 = GenerateurBriques()
    sq = list(squelettes if squelettes is not None else g0.squelettes)
    rmp = {t: list(v) for t, v in (remplisseurs if remplisseurs is not None else g0.remplisseurs).items()}

    base = couverture(sq, rmp, taches, limites)
    change = True
    while change:
        change = False
        for b in briques(sq, rmp):
            sq2, rmp2 = retire(sq, rmp, b)
            if couverture(sq2, rmp2, taches, limites) == base:
                sq, rmp = sq2, rmp2     # superflue : on la jette
                change = True
                break
    return sq, rmp
