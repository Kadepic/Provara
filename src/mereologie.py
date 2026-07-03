"""
MÉRÉOLOGIE (composition partie-tout) — brique Vague 1. Socle du DESIGN et de la décomposition d'artefacts.

POURQUOI : un système conçu est un ASSEMBLAGE de parties jouant des rôles (une clim = compresseur + condenseur +
détendeur + évaporateur ; un moteur = … ). Sans relation partie-tout structurée, on ne peut ni décomposer un artefact
existant, ni proposer un ré-assemblage (le geste d'invention). Généralise la discipline anti-circulaire déjà appliquée
aux hiérarchies (taxon_parent…) à la composition physique.

MODÈLE : un graphe orienté « partie -> tout » (une part APPARTIENT À un tout), chaque arête portant un RÔLE optionnel
(le rôle de la partie dans le tout) et une multiplicité. Le tout d'un assemblage est lui-même une entité (nesting).

FAUX=0 (invariants structurels vérifiés, jamais supposés) :
  • IRRÉFLEXIVITÉ : rien n'est partie propre de soi-même (rejet de partie(X, X)).
  • ACYCLICITÉ : pas de cycle A⊂B⊂A (une arête qui fermerait un cycle est REFUSÉE). Sinon « contient » n'aurait pas
    de sens et la clôture transitive ne terminerait pas.
  • TRANSITIVITÉ SOUND : `parties(tout)` renvoie la clôture transitive RÉELLE (uniquement des arêtes posées),
    jamais une partie inventée. `contient(a, b)` est décidable et terminant.
Stdlib pur, déterministe, souverain.
"""
from __future__ import annotations


class CycleMereologique(Exception):
    """Ajouter cette arête partie->tout fermerait un cycle (A partie de B partie de A) — rejet FAUX=0."""


class Assemblage:
    """Graphe partie->tout. `ajoute_partie(partie, tout, role=…, multiplicite=…)` sous garde irréflexive+acyclique."""

    __slots__ = ("_vers_tout", "_parties_de", "_roles")

    def __init__(self):
        self._vers_tout: dict = {}      # partie -> set(touts dont elle est partie DIRECTE)
        self._parties_de: dict = {}     # tout -> set(parties DIRECTES)
        self._roles: dict = {}          # (partie, tout) -> (role, multiplicite)

    def ajoute_partie(self, partie, tout, role=None, multiplicite=1):
        """Pose l'arête « partie est une partie de tout ». Refuse l'auto-référence et tout cycle."""
        if partie == tout:
            raise CycleMereologique(f"irréflexif : {partie!r} ne peut être partie de lui-même")
        # une arête partie->tout crée un cycle si `tout` est déjà (transitivement) une partie de `partie`.
        if self.contient(partie, tout):
            raise CycleMereologique(f"cycle refusé : {tout!r} est déjà (transitivement) une partie de {partie!r}")
        self._parties_de.setdefault(tout, set()).add(partie)
        self._vers_tout.setdefault(partie, set()).add(tout)
        self._roles[(partie, tout)] = (role, multiplicite)

    def parties_directes(self, tout) -> set:
        return set(self._parties_de.get(tout, ()))

    def parties(self, tout) -> set:
        """Clôture transitive : toutes les parties (directes et indirectes) de `tout`. Terminant (acyclique)."""
        vus, pile = set(), list(self._parties_de.get(tout, ()))
        while pile:
            p = pile.pop()
            if p in vus:
                continue
            vus.add(p)
            pile.extend(self._parties_de.get(p, ()))
        return vus

    def touts(self, partie) -> set:
        """Clôture transitive montante : tous les touts qui contiennent `partie`."""
        vus, pile = set(), list(self._vers_tout.get(partie, ()))
        while pile:
            t = pile.pop()
            if t in vus:
                continue
            vus.add(t)
            pile.extend(self._vers_tout.get(t, ()))
        return vus

    def contient(self, tout, partie) -> bool:
        """True ssi `partie` est (transitivement) une partie de `tout`. Décidable, terminant."""
        return partie in self.parties(tout)

    def role_de(self, partie, tout):
        """(role, multiplicite) de l'arête directe, ou None si pas d'arête directe."""
        return self._roles.get((partie, tout))

    def racines(self) -> set:
        """Les touts qui ne sont partie de rien (les assemblages de plus haut niveau)."""
        touts = set(self._parties_de)
        return {t for t in touts if not self._vers_tout.get(t)}

    def feuilles(self) -> set:
        """Les parties atomiques (sans sous-partie)."""
        parties = set(self._vers_tout)
        return {p for p in parties if not self._parties_de.get(p)}

    def __len__(self):
        return len(self._roles)
