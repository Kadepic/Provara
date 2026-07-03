"""
LOIS MANIPULABLES — brique fondatrice Vague 2 (moteur symbolique/numérique). Dépend de dimensions.py + grandeur.py.

POURQUOI : c'est le passage RAPPEL -> RAISONNEMENT. Une loi n'est plus une constante ni une phrase, mais un objet
qu'on peut ÉVALUER et INVERSER : « résous pour n'importe quelle variable, les autres étant connues ». C'est le
prérequis du calcul de limites théoriques, de la simulation, et du design (« quelle valeur de X atteint la cible Y ? »).

MODÈLE : une Loi = un nom + des VARIABLES typées (chacune une Dimension) + des SOLVEURS (variable -> fonction qui la
calcule, en unités SI de base, à partir des autres). Une loi inversable fournit un solveur PAR variable qu'on veut
pouvoir déduire. `resout(cible, **connues)` rend une Grandeur typée.

FAUX=0 (jamais un nombre fabriqué) :
  • Toute entrée doit être une Grandeur de la BONNE dimension (déclarée) — sinon HORS (None).
  • La cible ne doit pas être fournie ; toutes les autres variables nécessaires doivent l'être — sinon HORS.
  • Pas de solveur pour la cible, ou résultat non fini / solveur qui échoue -> HORS (None), jamais d'invention.
  • `verifie_coherence(exemple)` : sur une affectation COMPLÈTE et cohérente, résoudre chaque variable doit
    REPRODUIRE l'entrée (round-trip) — c'est le garde-fou qui prouve que les solveurs d'une loi sont mutuellement
    sains (une loi mal inversée est détectée, pas tolérée).
Stdlib pur, déterministe, souverain. Le solveur numérique (bisection) est fourni pour les lois non inversées à la main.
"""
from __future__ import annotations

import math

import dimensions as D
from grandeur import Grandeur


class Loi:
    __slots__ = ("nom", "variables", "solveurs", "description", "domaine")

    def __init__(self, nom: str, variables: dict, solveurs: dict, description: str = "", domaine=None):
        self.nom = nom
        self.variables = dict(variables)         # var -> Dimension
        self.solveurs = dict(solveurs)           # var -> fn(**{autres: valeur_SI}) -> valeur_SI
        self.description = description
        # DOMAINE DE VALIDITÉ (opt-in, 2026-07-02) : prédicat callable(**{var: valeur_SI}) -> bool, portant sur
        # l'affectation COMPLÈTE (connues + cible résolue). Une loi ne tient que dans son champ physique (Th>Tc>0
        # pour Carnot, r>0, m>0…) ; hors de ce champ elle rendrait un nombre ABSURDE (COP<0, rendement>1). Le domaine
        # est vérifié AVANT de retourner un résultat -> HORS (None) hors champ. `None` = pas de contrainte (backward-compat).
        self.domaine = domaine

    def dans_domaine(self, **valeurs_si) -> bool:
        """Le domaine de validité est-il satisfait par cette affectation (var -> valeur SI) ? True si aucun domaine
        déclaré (open). FAUX=0 : un domaine qui LÈVE (variable manquante, calcul invalide) est traité comme NON satisfait."""
        if self.domaine is None:
            return True
        try:
            return bool(self.domaine(**valeurs_si))
        except Exception:
            return False                         # domaine non évaluable -> conservateur (hors champ)

    def resout(self, cible: str, **connues):
        """Résout `cible` à partir des `connues` (dict var -> Grandeur). Renvoie une Grandeur typée ou None (HORS)."""
        if cible not in self.variables or cible not in self.solveurs:
            return None                          # variable inconnue ou non inversable -> HORS
        if cible in connues:
            return None                          # la cible ne doit pas être donnée
        besoins = [v for v in self.variables if v != cible]
        vals = {}
        for v in besoins:
            g = connues.get(v)
            if not isinstance(g, Grandeur):
                return None                      # entrée manquante ou non typée -> HORS
            if g.dim != self.variables[v]:
                return None                      # DIMENSION incompatible -> HORS (le filtre)
            vals[v] = g.valeur                   # valeur en SI de base
        try:
            r = self.solveurs[cible](**vals)
        except Exception:
            return None                          # solveur en échec -> HORS (jamais un nombre faux)
        if r is None or not math.isfinite(r):
            return None
        # GARDE DOMAINE DE VALIDITÉ : l'affectation complète (connues + cible résolue) doit être dans le champ
        # physique de la loi ; sinon on s'abstient (le nombre calculé serait hors du domaine où la loi tient).
        if not self.dans_domaine(**{cible: r}, **vals):
            return None
        return Grandeur(r, self.variables[cible])

    def verifie_coherence(self, exemple: dict, tol: float = 1e-9) -> bool:
        """Sur une affectation COMPLÈTE cohérente (var -> Grandeur), résoudre chaque variable inversable doit
        reproduire sa valeur. Prouve la santé mutuelle des solveurs. Faux si un round-trip dévie."""
        if set(exemple) != set(self.variables):
            return False
        for cible in self.solveurs:
            attendu = exemple[cible].valeur
            autres = {v: exemple[v] for v in self.variables if v != cible}
            g = self.resout(cible, **autres)
            if g is None:
                return False
            ecart = abs(g.valeur - attendu)
            echelle = max(abs(attendu), 1.0)
            if ecart / echelle > tol:
                return False
        return True

    def __repr__(self):
        return f"Loi({self.nom}: {', '.join(self.variables)})"


def solveur_numerique(residu, borne_bas: float, borne_haut: float, iters: int = 200):
    """Fabrique un solveur par BISECTION sur `residu(x, **autres)=0` dans [borne_bas, borne_haut]. Pour les lois
    qu'on ne sait pas inverser analytiquement. Renvoie None (HORS) si pas de changement de signe (racine non
    encadrée) — jamais une racine fabriquée. Déterministe."""
    def solve(**autres):
        a, b = borne_bas, borne_haut
        fa = residu(a, **autres)
        fb = residu(b, **autres)
        if fa == 0:
            return a
        if fb == 0:
            return b
        if (fa > 0) == (fb > 0):
            return None                          # racine non encadrée -> HORS
        for _ in range(iters):
            m = (a + b) / 2
            fm = residu(m, **autres)
            if fm == 0:
                return m
            if (fm > 0) == (fa > 0):
                a, fa = m, fm
            else:
                b = m
        return (a + b) / 2
    return solve
