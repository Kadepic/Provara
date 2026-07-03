"""
BILAN DE CONSERVATION — brique Vague 3 (ancrage physique). Dépend de grandeur.py + dimensions.py.

POURQUOI : c'est un juge de faisabilité universel. Une grandeur CONSERVÉE (énergie, masse, charge, quantité de
mouvement) obéit à : Σ entrées = Σ sorties + accumulation. Un design proposé qui SORT plus qu'il n'ENTRE (sans source
ni réservoir) viole ce bilan — c'est une machine à mouvement perpétuel, à REJETER sans discussion. C'est le filtre qui
empêche la machine d'« inventer » de l'énergie gratuite.

FAUX=0 :
  • Tous les termes doivent avoir la MÊME dimension (une grandeur conservée) — sinon None (HORS) : on ne mélange pas
    des énergies et des masses dans un bilan.
  • Le déséquilibre est calculé exactement ; `conserve=False` DÉTECTE la violation (sortie > entrée + accumulation),
    jamais tolérée comme un « gain ».
  • Aucun terme inventé ; liste vide -> HORS.
Stdlib pur, déterministe, souverain.
"""
from __future__ import annotations

from grandeur import Grandeur


def _meme_dimension(termes):
    """Renvoie la dimension commune des Grandeur, ou None si liste vide / dimensions hétérogènes / type invalide."""
    if not termes:
        return None
    d = termes[0].dim if isinstance(termes[0], Grandeur) else None
    if d is None:
        return None
    for g in termes:
        if not isinstance(g, Grandeur) or g.dim != d:
            return None
    return d


def bilan(entrees, sorties, accumulation=None, tol_rel: float = 1e-9):
    """Vérifie Σ entrées = Σ sorties + accumulation pour une grandeur conservée. `entrees`/`sorties` = listes de
    Grandeur (même dimension) ; `accumulation` = variation du stock (Grandeur de même dimension) ou None (=0).
    Renvoie un dict {conserve, entree_totale, sortie_totale, accumulation, desequilibre} ou None (HORS) si les
    dimensions ne concordent pas ou si aucun terme n'est fourni."""
    entrees = list(entrees)
    sorties = list(sorties)
    tous = entrees + sorties + ([accumulation] if accumulation is not None else [])
    dim = _meme_dimension(tous)
    if dim is None:
        return None                              # dimensions incohérentes ou vide -> HORS

    def somme(lst):
        acc = Grandeur(0, dim)
        for g in lst:
            acc = acc + g                        # + exige déjà la même dimension (garanti ci-dessus)
        return acc

    e = somme(entrees)
    s = somme(sorties)
    a = accumulation if accumulation is not None else Grandeur(0, dim)
    desequilibre = e.valeur - (s.valeur + a.valeur)
    echelle = max(abs(e.valeur), abs(s.valeur), abs(a.valeur), 1.0)
    conserve = abs(desequilibre) <= tol_rel * echelle
    return {
        "conserve": conserve,
        "entree_totale": e,
        "sortie_totale": s,
        "accumulation": a,
        "desequilibre": Grandeur(desequilibre, dim),   # >0 : entrée en excès ; <0 : sortie créée du néant
    }


def viole_conservation(entrees, sorties, accumulation=None, tol_rel: float = 1e-9) -> bool:
    """True ssi le système SORT plus qu'il n'entre (+ accumulation) au-delà de la tolérance — création de quantité
    à partir de rien = physiquement IMPOSSIBLE. None-safe : dimensions incohérentes -> False (rien à conclure)."""
    b = bilan(entrees, sorties, accumulation, tol_rel)
    if b is None:
        return False
    return b["desequilibre"].valeur < -tol_rel * max(abs(b["sortie_totale"].valeur), 1.0)


def rendement(utile: Grandeur, fourni: Grandeur):
    """Rendement = utile / fourni (sans dimension, mêmes dimensions requises). None (HORS) si dimensions
    différentes ou fourni nul. Un rendement > 1 pour une simple CONVERSION (sans source additionnelle) signale
    une incohérence — à confronter à un bilan complet."""
    if not isinstance(utile, Grandeur) or not isinstance(fourni, Grandeur) or utile.dim != fourni.dim:
        return None
    if fourni.valeur == 0:
        return None
    return utile.valeur / fourni.valeur
