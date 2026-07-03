"""
IDENTITÉ CANONIQUE UNIFIÉE — brique fondatrice Vague 1. Réutilise base_faits.normalise (ne le modifie pas).

POURQUOI : sans identité stable, aucun graphe ni jointure n'est fiable — « moteur Stirling » et « machine de
Stirling » comme deux nœuds distincts font double-compter toute énumération et échouer toute vérification de non-
contradiction. Cette brique fusionne 5 doublons repérés dans la carte (identité en representation + normalisation en
acquisition + résolution en meta). Elle donne : une CLÉ canonique (surface) + des CLASSES D'ÉQUIVALENCE (sameAs).

MODÈLE : union-find sur les libellés (via leur clé normalisée). Deux entités sont la MÊME seulement si (a) même
surface normalisée [« Eau » = « eau »], ou (b) déclarées équivalentes AVEC PREUVE [« H2O » = « eau »].

FAUX=0 — « ne JAMAIS fusionner deux entités réellement distinctes » (le faux positif est la ligne rouge) :
  • DISTINCT PAR DÉFAUT : deux libellés de surface différente ne sont PAS la même entité tant qu'aucune preuve ne
    le dit. `meme(a,b)` renvoie False au doute, jamais un rapprochement deviné par ressemblance de nom.
  • Fusion GATÉE PAR PREUVE : `declare_equivalent(a, b, preuve)` exige une preuve non vide, sinon refus.
  • Représentant DÉTERMINISTE d'une classe (libellé minimal) — canonique stable et reproductible.
  • La désambiguïsation d'HOMOGRAPHES (même surface, entités distinctes : « Paris » ville vs mythologie) est HORS
    périmètre ici (refs qualifiées / resolution.py) : on n'invente aucune scission ni aucune fusion silencieuse.
Stdlib pur, déterministe, souverain.
"""
from __future__ import annotations

from base_faits import normalise


class PreuveRequise(Exception):
    """Fusionner deux entités sans preuve est refusé — le faux positif d'identité est interdit (FAUX=0)."""


class RegistreIdentite:
    __slots__ = ("_parent", "_labels", "_preuves")

    def __init__(self):
        self._parent: dict = {}          # clé -> clé parent (union-find)
        self._labels: dict = {}          # clé -> {libellés de surface vus pour cette clé}
        self._preuves: dict = {}         # frozenset({cléA, cléB}) -> preuve de la fusion

    def _cle(self, x) -> str:
        return normalise(str(x))

    def enregistre(self, label) -> str:
        """Assure que le libellé est connu ; renvoie sa clé canonique de surface."""
        c = self._cle(label)
        if c not in self._parent:
            self._parent[c] = c
            self._labels[c] = set()
        self._labels[c].add(str(label))
        return c

    def _trouve(self, c: str) -> str:
        # union-find avec compression de chemin ; clé inconnue -> auto-enregistrée comme singleton
        if c not in self._parent:
            self._parent[c] = c
            self._labels[c] = set()
        racine = c
        while self._parent[racine] != racine:
            racine = self._parent[racine]
        while self._parent[c] != racine:
            self._parent[c], c = racine, self._parent[c]
        return racine

    def declare_equivalent(self, a, b, preuve: str) -> None:
        """Déclare a et b comme la MÊME entité, JUSTIFIÉ par `preuve` (obligatoire, non vide). Idempotent."""
        if not preuve or not str(preuve).strip():
            raise PreuveRequise(f"fusion {a!r}={b!r} refusée : preuve obligatoire (pas de rapprochement deviné)")
        ca, cb = self.enregistre(a), self.enregistre(b)
        ra, rb = self._trouve(ca), self._trouve(cb)
        if ra == rb:
            return
        # rattache la plus grande clé sous la plus petite -> représentant = min déterministe
        haut, bas = (ra, rb) if ra > rb else (rb, ra)
        self._parent[haut] = bas
        self._preuves[frozenset((ca, cb))] = str(preuve)

    def meme(self, a, b) -> bool:
        """True ssi a et b sont dans la même classe d'équivalence (même surface ou fusion prouvée). Distinct au doute."""
        return self._trouve(self._cle(a)) == self._trouve(self._cle(b))

    def representant(self, x) -> str:
        """Clé canonique DÉTERMINISTE de la classe de x (racine = clé minimale de la classe)."""
        return self._trouve(self._cle(x))

    def libelle_canonique(self, x) -> str:
        """Libellé de surface représentatif (le plus court, puis alphabétique) de la classe — stable."""
        r = self._trouve(self._cle(x))
        labels = set()
        for c in self._parent:
            if self._trouve(c) == r:
                labels |= self._labels.get(c, set())
        return min(labels, key=lambda s: (len(s), s.lower(), s)) if labels else str(x)

    def classe(self, x) -> set:
        """Tous les libellés de surface de la classe de x."""
        r = self._trouve(self._cle(x))
        out = set()
        for c in self._parent:
            if self._trouve(c) == r:
                out |= self._labels.get(c, set())
        return out

    def preuve_de(self, a, b):
        """La preuve enregistrée reliant a et b (arête directe), ou None."""
        return self._preuves.get(frozenset((self._cle(a), self._cle(b))))

    def nb_classes(self) -> int:
        return len({self._trouve(c) for c in self._parent})
