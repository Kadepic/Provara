"""
SOLVEUR DE CONTRAINTES (CSP) — brique fondatrice Vague 2. Débloque le DESIGN, la relaxation et la planification.

POURQUOI : concevoir = trouver une affectation de valeurs qui satisfait un ensemble de contraintes (un design
faisable), ou prouver qu'aucune n'existe (contradiction à résoudre). C'est le moteur générique du versant invention :
« quelles valeurs des paramètres respectent toutes les contraintes ? ». Prérequis de la relaxation (lever une
contrainte pour rouvrir l'espace) et de la planification.

MODÈLE : variables à DOMAINES FINIS + contraintes = prédicats sur un sous-ensemble de variables. Recherche par
backtracking déterministe (variables dans l'ordre d'ajout, valeurs dans l'ordre du domaine) avec vérification
incrémentale des contraintes dont la portée est entièrement affectée.

FAUX=0 (jamais une solution fabriquée) :
  • Toute solution RENDUE est RE-VÉRIFIÉE contre TOUTES les contraintes avant d'être retournée (`satisfait`).
  • Insatisfiable -> None / [] HONNÊTEMENT (jamais une affectation partielle ou inventée).
  • Déterministe (ordre fixe) -> reproductible.
  • La recherche est complète (backtracking) : si une solution existe, elle est trouvée ; sinon UNSAT est certain
    sur des domaines finis.
Stdlib pur, souverain.
"""
from __future__ import annotations


class Contrainte:
    __slots__ = ("portee", "predicat", "nom")

    def __init__(self, portee, predicat, nom=""):
        self.portee = tuple(portee)              # noms de variables concernées
        self.predicat = predicat                 # fn(*valeurs_dans_l_ordre_de_portee) -> bool
        self.nom = nom or "+".join(self.portee)

    def applicable(self, affectees: set) -> bool:
        return all(v in affectees for v in self.portee)

    def verifie(self, affectation: dict) -> bool:
        # valeurs passées POSITIONNELLEMENT dans l'ordre de la portée -> prédicats réutilisables (diff, <, x+y=z…).
        return bool(self.predicat(*(affectation[v] for v in self.portee)))


class CSP:
    __slots__ = ("_ordre", "_domaines", "_contraintes")

    def __init__(self):
        self._ordre: list = []                   # variables dans l'ordre d'ajout (déterminisme)
        self._domaines: dict = {}                # var -> liste de valeurs
        self._contraintes: list = []

    def variable(self, nom, domaine):
        if nom in self._domaines:
            raise ValueError(f"variable déjà déclarée : {nom!r}")
        self._ordre.append(nom)
        self._domaines[nom] = list(domaine)
        return self

    def contrainte(self, portee, predicat, nom=""):
        for v in portee:
            if v not in self._domaines:
                raise ValueError(f"contrainte sur variable inconnue : {v!r}")
        self._contraintes.append(Contrainte(portee, predicat, nom))
        return self

    def satisfait(self, affectation: dict) -> bool:
        """True ssi l'affectation COMPLÈTE respecte TOUTES les contraintes (et couvre toutes les variables)."""
        if set(affectation) != set(self._domaines):
            return False
        return all(c.verifie(affectation) for c in self._contraintes)

    def _coherent_partiel(self, affectation: dict, affectees: set) -> bool:
        # toutes les contraintes DONT la portée est entièrement affectée doivent tenir
        for c in self._contraintes:
            if c.applicable(affectees) and not c.verifie(affectation):
                return False
        return True

    def _backtrack(self, i, affectation, affectees, solutions, limite):
        if len(solutions) >= limite:
            return
        if i == len(self._ordre):
            sol = dict(affectation)
            if self.satisfait(sol):              # RE-VÉRIFICATION finale (FAUX=0)
                solutions.append(sol)
            return
        var = self._ordre[i]
        for val in self._domaines[var]:
            affectation[var] = val
            affectees.add(var)
            if self._coherent_partiel(affectation, affectees):
                self._backtrack(i + 1, affectation, affectees, solutions, limite)
            affectees.discard(var)
            del affectation[var]
            if len(solutions) >= limite:
                return

    def resout(self):
        """Première solution (dict) ou None si INSATISFIABLE. Déterministe."""
        sols = []
        self._backtrack(0, {}, set(), sols, 1)
        return sols[0] if sols else None

    def solutions(self, limite: int = 10 ** 9) -> list:
        """Toutes les solutions (jusqu'à `limite`), dans l'ordre déterministe. [] si UNSAT."""
        sols = []
        self._backtrack(0, {}, set(), sols, limite)
        return sols

    def satisfiable(self) -> bool:
        return self.resout() is not None

    def contraintes_violees(self, affectation: dict) -> list:
        """Noms des contraintes non respectées par une affectation complète (pour la relaxation/diagnostic)."""
        if set(affectation) != set(self._domaines):
            return ["<affectation incomplète>"]
        return [c.nom for c in self._contraintes if not c.verifie(affectation)]
