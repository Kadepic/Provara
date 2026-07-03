"""
RAISONNEMENT PAR DÉFAUT — noyau BORNÉ de « cas général vs cas particulier / exception » (B-NEC), pur stdlib (2026-07-02).

POURQUOI (sujet borné « Cas général vs cas particulier / exception ») : une règle générale (« normalement, les X sont
Y ») admet des EXCEPTIONS explicites (« mais ce X-ci est Z »). C'est le raisonnement NON-MONOTONE (par défaut, à la
Reiter) : une conclusion par défaut peut être RÉVISÉE par un cas plus spécifique. La réalité (les faits déclarés) fixe
la réponse ; le mécanisme est réglé donc vérifiable.

FAUX=0 — le piège du non-monotone est d'affirmer trop ; ce module reste SOUND par trois règles strictes :
  • L'EXCEPTION explicite PRIME toujours le défaut (le cas particulier est une vérité-terrain déclarée, pas une
    supposition). Deux exceptions contradictoires sur le même membre -> ValueError (jamais de choix arbitraire).
  • Le défaut n'est conclu QUE pour un membre CONNU de la classe (déclaré) et NON exceptionnel. Pour un membre dont
    l'appartenance est inconnue -> ABSTIENT (jamais « il vole » pour un objet dont on ignore que c'est un oiseau).
  • Aucune fermeture du monde : « pas dérivable » ≠ « faux ». Le module rend un STATUT (DEFAUT/EXCEPTION/ABSTIENT),
    pas une vérité absolue ; il trace la raison.
Souverain, offline, stdlib pur, déterministe. NB : modèle à deux niveaux (défaut + exceptions explicites) ; les
hiérarchies de spécificité multi-niveaux (ornithorynque < mammifère) se composent en chaînant des règles.
"""
from __future__ import annotations

DEFAUT = "defaut"          # conclusion par la règle générale
EXCEPTION = "exception"    # conclusion par un cas particulier déclaré (prime le défaut)
ABSTIENT = "abstient"      # appartenance inconnue -> pas de conclusion (FAUX=0)


class RegleDefaut:
    """Une règle « normalement, les <classe> ont <propriété> = <valeur_defaut> », avec exceptions explicites."""

    def __init__(self, classe: str, propriete: str, valeur_defaut):
        if not isinstance(classe, str) or not classe.strip():
            raise ValueError("classe non vide requise")
        if not isinstance(propriete, str) or not propriete.strip():
            raise ValueError("propriété non vide requise")
        if valeur_defaut is None:
            raise ValueError("valeur par défaut requise (utiliser une valeur sentinelle explicite, pas None)")
        self.classe = classe
        self.propriete = propriete
        self.valeur_defaut = valeur_defaut
        self._membres: set = set()
        self._exceptions: dict = {}

    def ajoute_membre(self, membre) -> "RegleDefaut":
        """Déclare qu'un individu appartient à la classe (condition pour conclure le défaut)."""
        if membre is None:
            raise ValueError("membre None invalide")
        self._membres.add(membre)
        return self

    def sauf(self, membre, valeur) -> "RegleDefaut":
        """Déclare une EXCEPTION explicite : `membre` a la propriété = `valeur` (≠ défaut, sinon inutile mais toléré).
        Un membre exceptionnel est implicitement membre de la classe. Conflit (2 valeurs) -> ValueError."""
        if membre is None:
            raise ValueError("membre None invalide")
        if valeur is None:
            raise ValueError("valeur d'exception requise")
        if membre in self._exceptions and self._exceptions[membre] != valeur:
            raise ValueError(f"exception contradictoire pour {membre!r} : "
                             f"{self._exceptions[membre]!r} vs {valeur!r}")
        self._exceptions[membre] = valeur
        self._membres.add(membre)
        return self

    def conclut(self, membre):
        """(statut, valeur, raison). EXCEPTION prime ; défaut si membre connu non-exceptionnel ; sinon ABSTIENT."""
        if membre in self._exceptions:
            return (EXCEPTION, self._exceptions[membre],
                    f"{membre!r} est une exception déclarée à « {self.classe} -> {self.propriete} »")
        if membre in self._membres:
            return (DEFAUT, self.valeur_defaut,
                    f"{membre!r} est un {self.classe} sans exception -> défaut {self.propriete}={self.valeur_defaut!r}")
        return (ABSTIENT, None,
                f"appartenance de {membre!r} à « {self.classe} » inconnue -> abstention (FAUX=0)")

    def est_exception(self, membre) -> bool:
        return membre in self._exceptions

    def exceptions(self) -> dict:
        return dict(self._exceptions)

    def vaut_en_general(self):
        """La conclusion par défaut de la règle (le « cas général »)."""
        return self.valeur_defaut
