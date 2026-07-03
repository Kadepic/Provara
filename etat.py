"""
ÉTATS & VARIABLES — brique Vague 1. Socle de la SIMULATION et de la PLANIFICATION.

POURQUOI : un système (physique, procédé, artefact) a un ÉTAT = l'affectation de ses variables à un instant. Le faire
évoluer (transitions) est le préalable pour simuler un design proposé et pour planifier une suite d'actions vers un but.

MODÈLE : un `EspaceEtats` déclare des variables typées — soit à DOMAINE FINI (ensemble de valeurs admises), soit
CONTINUES (une Dimension : la valeur doit être une grandeur.Grandeur de cette dimension). Un `Etat` est une affectation
IMMUABLE validée contre l'espace ; `avec(**changements)` produit un nouvel état (transition), re-validé.

FAUX=0 :
  • Une valeur HORS domaine (ou de mauvaise dimension) est REFUSÉE (ValeurHorsDomaine) — jamais un état incohérent.
  • Interroger une variable non affectée -> None (jamais une valeur inventée).
  • Immuable : une transition crée un NOUVEL état, n'écrase jamais le passé (traçable).
Stdlib pur, déterministe, souverain. Optionnellement typé par dimensions.py (variables continues).
"""
from __future__ import annotations

from grandeur import Grandeur


class ValeurHorsDomaine(Exception):
    """Une valeur n'appartient pas au domaine / n'a pas la dimension déclarée de sa variable — rejet FAUX=0."""


class Variable:
    __slots__ = ("nom", "domaine", "dimension")

    def __init__(self, nom, domaine=None, dimension=None):
        if (domaine is None) == (dimension is None):
            raise ValueError("une variable a SOIT un domaine fini SOIT une dimension continue (exactement un)")
        self.nom = nom
        self.domaine = set(domaine) if domaine is not None else None
        self.dimension = dimension

    def admet(self, valeur) -> bool:
        if self.domaine is not None:
            return valeur in self.domaine
        return isinstance(valeur, Grandeur) and valeur.dim == self.dimension

    def __repr__(self):
        t = f"domaine={sorted(self.domaine, key=repr)}" if self.domaine is not None else f"dim={self.dimension.formule()}"
        return f"Variable({self.nom}, {t})"


class Etat:
    """Affectation immuable variable -> valeur, validée contre un EspaceEtats."""

    __slots__ = ("_espace", "_vals")

    def __init__(self, espace, vals):
        self._espace = espace
        self._vals = dict(vals)

    def valeur(self, nom):
        """Valeur d'une variable, ou None si non affectée (jamais inventée)."""
        return self._vals.get(nom)

    def avec(self, **changements):
        """Nouvel état où certaines variables changent (transition). Re-valide ; ValeurHorsDomaine si invalide."""
        nouveau = dict(self._vals)
        nouveau.update(changements)
        return self._espace.etat(**nouveau)

    def complet(self) -> bool:
        return set(self._vals) == set(self._espace.variables)

    def variables_affectees(self) -> set:
        return set(self._vals)

    def __eq__(self, autre):
        return isinstance(autre, Etat) and self._vals == autre._vals

    def __hash__(self):
        return hash(tuple(sorted((k, repr(v)) for k, v in self._vals.items())))

    def __repr__(self):
        return "Etat(" + ", ".join(f"{k}={v!r}" for k, v in sorted(self._vals.items())) + ")"


class EspaceEtats:
    __slots__ = ("variables",)

    def __init__(self):
        self.variables: dict = {}        # nom -> Variable

    def variable(self, nom, domaine=None, dimension=None):
        if nom in self.variables:
            raise ValueError(f"variable déjà déclarée : {nom!r}")
        self.variables[nom] = Variable(nom, domaine, dimension)
        return self

    def etat(self, **valeurs) -> Etat:
        """Construit et VALIDE un état. Variable inconnue ou valeur hors domaine/dimension -> refus FAUX=0."""
        for nom, val in valeurs.items():
            v = self.variables.get(nom)
            if v is None:
                raise ValeurHorsDomaine(f"variable inconnue : {nom!r}")
            if not v.admet(val):
                raise ValeurHorsDomaine(f"valeur {val!r} hors du domaine de {nom!r} ({v})")
        return Etat(self, valeurs)
