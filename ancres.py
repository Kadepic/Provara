"""
BANQUE D'ANCRES NON-CIRCULAIRE — brique fondatrice Vague 6. Le référentiel de vérité de toute la couche confiance.

POURQUOI : toute vérification (calibration, falsification, auto-sourcing) a besoin d'une VÉRITÉ-TERRAIN. Piège mortel :
si on vérifie un fait par lui-même (ou par une source qui en dérive), FAUX=0 s'auto-valide — la circularité fabrique
de la fausse certitude. Une ancre est un fait tenu pour vrai AVEC une source INDÉPENDANTE, et l'on interdit qu'un fait
serve à se vérifier lui-même.

MODÈLE : chaque ancre = (clé, valeur, source). `verifie(cle, valeur, source_de_la_reponse)` compare une réponse à
l'ancre — mais REFUSE si la source de la réponse est la même que celle de l'ancre (circularité).

FAUX=0 :
  • Une ancre exige une source non vide ; deux ancres contradictoires sur la même clé -> Incoherence (détectée).
  • `verifie` renvoie CONFIRME / CONTREDIT / INCONNU (pas d'ancre) — jamais un verdict inventé.
  • NON-CIRCULARITÉ : si la source de la réponse == source de l'ancre -> CIRCULAIRE (verdict refusé), on ne se
    corrobore pas soi-même.
Stdlib pur, déterministe, souverain.
"""
from __future__ import annotations

CONFIRME = "confirme"
CONTREDIT = "contredit"
INCONNU = "inconnu"
CIRCULAIRE = "circulaire"


class Incoherence(Exception):
    """Deux ancres contradictoires sur la même clé — la vérité-terrain elle-même serait fausse (refus FAUX=0)."""


class BanqueAncres:
    __slots__ = ("_ancres",)

    def __init__(self):
        self._ancres: dict = {}          # cle -> (valeur, source)

    def ajoute(self, cle, valeur, source: str):
        if not source or not str(source).strip():
            raise ValueError("une ancre exige une source indépendante non vide")
        if cle in self._ancres and self._ancres[cle][0] != valeur:
            raise Incoherence(f"ancre contradictoire sur {cle!r} : {self._ancres[cle][0]!r} vs {valeur!r}")
        self._ancres[cle] = (valeur, str(source))
        return self

    def verifie(self, cle, valeur, source_reponse: str = ""):
        """Confronte une réponse (valeur, source) à l'ancre. CONFIRME/CONTREDIT/INCONNU, ou CIRCULAIRE si la
        réponse vient de la MÊME source que l'ancre (auto-corroboration interdite)."""
        if cle not in self._ancres:
            return INCONNU                       # pas d'ancre -> on ne peut rien affirmer
        val_ancre, src_ancre = self._ancres[cle]
        if source_reponse and source_reponse == src_ancre:
            return CIRCULAIRE                    # la réponse dérive de l'ancre -> vérification nulle
        return CONFIRME if valeur == val_ancre else CONTREDIT

    def independante(self, source_reponse: str, cle) -> bool:
        """La source de la réponse est-elle INDÉPENDANTE de l'ancre sur cette clé ? (base d'une vérification valide)."""
        if cle not in self._ancres:
            return True
        return source_reponse != self._ancres[cle][1]

    def __len__(self):
        return len(self._ancres)
