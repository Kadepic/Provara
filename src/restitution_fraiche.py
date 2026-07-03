"""
RESTITUTION GATÉE PAR LA FRAÎCHEUR — ne jamais servir un fait périmé comme courant (acquisition temporelle, 2026-07-02).

POURQUOI : le store des 71 M faits est ATEMPOREL (capitales, numéros atomiques, taxonomie) — parfait tel quel. Mais
les données VOLATILES (population, dirigeant en poste, prix) PÉRIMENT : servir une vieille valeur comme si elle était
à jour est un faux « mou ». Ce module est la GATE : donné un fait DATÉ (`fraicheur.FaitDate` : valeur + as_of + ttl),
il ne sert la valeur que si elle est FRAÎCHE, sinon HORS (à re-vérifier).

CHOIX DE CONCEPTION (non-invasif) : on n'altère PAS `base_faits.Fait` (qui porte le corpus stable) ; la dimension
temporelle est portée EXPLICITEMENT par `FaitDate`. L'ingestion future de relations volatiles produira des `FaitDate`,
que cette gate restitue de façon sûre. Le cœur atemporel reste inchangé et souverain.

FAUX=0 :
  • Un fait périmé (ou daté-inconnu : as_of/ttl manquant) -> HORS honnête, JAMAIS servi comme courant.
  • `maintenant` est TOUJOURS passé explicitement (pas d'horloge cachée) -> déterministe, testable, reproductible.
  • Atemporel (marqué explicitement) -> toujours servi (ne périme pas).
Stdlib pur, déterministe, souverain. Repose sur fraicheur.py (déjà validé).
"""
from __future__ import annotations

import fraicheur

VERIFIE = "verifie"
HORS = "hors"


def sert_ou_hors(fait_date, maintenant) -> dict:
    """Sert la valeur d'un `FaitDate` SEULEMENT s'il n'est pas périmé à l'instant `maintenant`. Renvoie
    {statut, valeur, raison}. FAUX=0 : périmé/daté-inconnu -> HORS (jamais une valeur périmée présentée comme actuelle)."""
    if fait_date.est_perime(maintenant):
        age = fait_date.age(maintenant)
        return {"statut": HORS, "valeur": None,
                "raison": f"périmé (age={age}, ttl={fait_date.ttl}) — à re-vérifier" if age is not None
                          else "daté-inconnu (as_of/ttl manquant) — à vérifier"}
    return {"statut": VERIFIE, "valeur": fait_date.valeur, "raison": "frais"}


def sert_le_plus_frais(faits_dates, maintenant) -> dict:
    """Parmi plusieurs `FaitDate` d'une même clé (versions successives), sert la plus RÉCENTE non périmée, ou HORS si
    toutes périmées. FAUX=0 : jamais une version périmée ; en cas d'égalité d'as_of, ordre d'entrée (déterministe)."""
    valides = fraicheur.frais(list(faits_dates), maintenant)
    if not valides:
        return {"statut": HORS, "valeur": None, "raison": "toutes les versions sont périmées ou datées-inconnues"}
    meilleur = valides[0]
    for f in valides[1:]:
        if f.as_of is not None and (meilleur.as_of is None or f.as_of > meilleur.as_of):
            meilleur = f
    return {"statut": VERIFIE, "valeur": meilleur.valeur, "raison": f"frais (version as_of={meilleur.as_of})"}


def a_rafraichir(faits_dates, maintenant) -> list:
    """Les clés des faits périmés à re-fetcher (déclencheur de veille — le FETCH lui-même reste hors périmètre/réseau)."""
    return [f.cle for f in fraicheur.a_rafraichir(list(faits_dates), maintenant)]
