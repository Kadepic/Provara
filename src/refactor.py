"""
REFACTOR PRÉSERVANT LE COMPORTEMENT — adopter une variante plus propre SEULEMENT si elle calcule le même (2026-07-02).

POURQUOI : « code propre » suppose de pouvoir transformer un code en un code ÉQUIVALENT mais meilleur (lisibilité,
simplicité), l'équivalence étant PROUVÉE, pas supposée. C'est le pont entre la synthèse (qui propose des variantes)
et l'adoption sûre. Repose sur equivalence_semantique.

FAUX=0 :
  • Une transformation n'est ADOPTÉE (`adopte=True`) QUE si l'équivalence est PROUVÉE exhaustivement sur un domaine
    FINI. Jamais sur un simple échantillon (« non distingué » ≠ « équivalent »).
  • Une DIFFÉRENCE (contre-exemple) -> REJET, avec le contre-exemple qui distingue les deux (re-vérifiable).
  • Sur échantillon sans domaine fini : renvoie « candidat » (adopte=False, non confirmé) -> on ne régresse jamais.
Stdlib pur, déterministe, souverain.
"""
from __future__ import annotations

import equivalence_semantique as _E


def adopte_refactor(original, candidat, domaine=None, generateur=None, n: int = 500, graine: int = 0) -> dict:
    """Décide d'adopter `candidat` à la place d'`original`. Renvoie
      {adopte: bool, certain: bool, statut, contre_exemple}.
    - domaine fini fourni : adopte=certain=True si EQUIVALENTES ; adopte=False + contre-exemple si DIFFERENTES.
    - échantillon seul : adopte=False TOUJOURS (pas de preuve) ; statut NON_DISTINGUEES (candidat) ou DIFFERENTES."""
    if domaine is not None:
        r = _E.sur_domaine(original, candidat, domaine)
        if r["statut"] == _E.EQUIVALENTES:
            return {"adopte": True, "certain": True, "statut": r["statut"], "contre_exemple": None}
        return {"adopte": False, "certain": True, "statut": r["statut"], "contre_exemple": r["contre_exemple"]}
    if generateur is not None:
        r = _E.par_echantillon(original, candidat, generateur, n=n, graine=graine)
        # NON_DISTINGUEES n'est PAS une preuve -> on n'adopte pas (FAUX=0 : jamais régresser sur un cas non testé)
        return {"adopte": False, "certain": r["statut"] == _E.DIFFERENTES,
                "statut": r["statut"], "contre_exemple": r["contre_exemple"]}
    raise ValueError("fournir un domaine fini (preuve, requis pour adopter) ou un generateur (candidat seulement)")


def meilleur_si_equivalent(original, candidat, cout, domaine) -> dict:
    """Adopte `candidat` SEULEMENT s'il est (a) prouvé équivalent sur `domaine` fini ET (b) strictement moins coûteux
    (`cout(candidat) < cout(original)`). Sinon garde l'original. Renvoie {choisi, adopte, statut}. Ne régresse jamais."""
    dec = adopte_refactor(original, candidat, domaine=domaine)
    if dec["adopte"] and cout(candidat) < cout(original):
        return {"choisi": candidat, "adopte": True, "statut": dec["statut"]}
    return {"choisi": original, "adopte": False, "statut": dec["statut"]}
