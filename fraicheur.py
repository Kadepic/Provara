"""
FRAÎCHEUR / PROVENANCE TEMPORELLE — brique Vague 8. Le cœur TEMPOREL de la veille.

POURQUOI : un fait daté peut PÉRIMER (population, prix, dirigeant en poste). Servir une vieille valeur comme si elle
était à jour = une forme de faux. La veille doit savoir ce qui est FRAIS, ce qui est PÉRIMÉ, et déclencher un
re-fetch. Chaque fait porte donc son instant de validité (as-of) et une durée de vie (TTL).

MODÈLE : un fait daté = (valeur, as_of, ttl). `est_perime(fait, maintenant)` = maintenant - as_of > ttl. Le temps est
TOUJOURS passé explicitement (`maintenant`) -> déterministe et testable (pas d'horloge cachée).

FAUX=0 :
  • Jamais « frais » par défaut : as_of/ttl manquant -> considéré comme À VÉRIFIER (périmé), pas comme frais.
  • ttl None = « pas de péremption connue » -> jamais réputé frais non plus si on demande la fraîcheur stricte ;
    par défaut on le traite comme atemporel (jamais périmé) SEULEMENT si explicitement marqué atemporel.
  • `a_rafraichir` liste honnêtement tout ce qui a dépassé son TTL.
Stdlib pur, déterministe, souverain.
"""
from __future__ import annotations


class FaitDate:
    __slots__ = ("cle", "valeur", "as_of", "ttl", "atemporel")

    def __init__(self, cle, valeur, as_of=None, ttl=None, atemporel=False):
        self.cle = cle
        self.valeur = valeur
        self.as_of = as_of            # instant de validité (nombre, ex. epoch ou année) ou None
        self.ttl = ttl                # durée de vie (même unité que as_of) ou None
        self.atemporel = atemporel    # True = vérité qui ne périme pas (constante physique, date historique)

    def est_perime(self, maintenant) -> bool:
        """True si le fait doit être re-vérifié. Atemporel -> jamais périmé. as_of/ttl manquant -> périmé (à vérifier)."""
        if self.atemporel:
            return False
        if self.as_of is None or self.ttl is None:
            return True               # daté-inconnu -> on ne le réputera pas frais (FAUX=0)
        return (maintenant - self.as_of) > self.ttl

    def age(self, maintenant):
        return None if self.as_of is None else maintenant - self.as_of

    def __repr__(self):
        return f"FaitDate({self.cle!r}={self.valeur!r}, as_of={self.as_of}, ttl={self.ttl}, atemporel={self.atemporel})"


def a_rafraichir(faits, maintenant) -> list:
    """Les faits périmés (à re-fetch), dans l'ordre. Honnête : inclut les datés-inconnus."""
    return [f for f in faits if f.est_perime(maintenant)]


def frais(faits, maintenant) -> list:
    """Les faits encore valides (non périmés)."""
    return [f for f in faits if not f.est_perime(maintenant)]
