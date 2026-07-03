"""
POLITIQUE D'ABSTENTION UNIFIÉE — brique Vague 7 (le capstone de l'honnêteté). Un seul point de décision VERIFIE/ABSTENTION/HORS.

POURQUOI : tout le projet repose sur « au doute, HORS ». Dispersé, ce principe se relâche. Cette brique centralise
la décision : quand AFFIRMER (VERIFIE), quand dire « je ne sais pas » (ABSTENTION), quand dire « c'est impossible/
contradictoire » (HORS). Le DÉFAUT est l'abstention ; on n'affirme que si la barre est franchie.

MODÈLE : `decide(preuve, confiance, seuil, contradiction, impossible)` :
  • impossible (viole une loi/borne) OU contradiction non résolue -> HORS.
  • pas de preuve, ou confiance < seuil -> ABSTENTION.
  • preuve présente, pas de contradiction, confiance ≥ seuil -> VERIFIE.

FAUX=0 :
  • L'abstention est le DÉFAUT : toute information manquante penche vers ABSTENTION, jamais vers VERIFIE.
  • Une confiance None (inconnue) ne franchit JAMAIS un seuil -> ABSTENTION (l'ignorance n'est pas de la confiance).
  • HORS domine (impossibilité/contradiction avant tout).
Stdlib pur, déterministe, souverain.
"""
from __future__ import annotations

VERIFIE = "verifie"
ABSTENTION = "abstention"
HORS = "hors"


def decide(preuve: bool = False, confiance: float = None, seuil: float = 0.5,
           contradiction: bool = False, impossible: bool = False):
    """Décision d'honnêteté unifiée. Renvoie VERIFIE / ABSTENTION / HORS. Défaut = ABSTENTION."""
    if impossible or contradiction:
        return HORS                              # impossibilité physique / contradiction -> HORS (domine)
    if not preuve:
        return ABSTENTION                        # aucune preuve -> on ne sait pas
    if confiance is None:
        return ABSTENTION                        # confiance inconnue != confiance haute -> abstention
    if confiance < seuil:
        return ABSTENTION                        # sous le seuil -> abstention (pas de sur-confiance)
    return VERIFIE                               # preuve + pas de contradiction + confiance suffisante


def affirme_ou_abstient(reponse, preuve=False, confiance=None, seuil=0.5, contradiction=False, impossible=False):
    """Renvoie `reponse` seulement si la décision est VERIFIE ; sinon le statut (ABSTENTION/HORS). Ne laisse jamais
    passer une réponse non justifiée."""
    d = decide(preuve, confiance, seuil, contradiction, impossible)
    return reponse if d == VERIFIE else d
