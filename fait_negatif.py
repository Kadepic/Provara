"""
FAIT NÉGATIF DE 1RE CLASSE (module `fait_negatif`) — distinguer le FAUX-connu de l'INCONNU (représentation, 2026-07-02).
NB : distinct de la « négation linguistique » (détecter « ne…pas » dans une phrase, cf. generateur.GenerateurNegation
+ valide_negation.py) — ici on dérive des faits NÉGATIFS certains dans le store, en logique trivaluée.

POURQUOI : un système FAUX=0 en monde OUVERT répond HORS quand un fait est absent — mais il confond alors « faux »
et « inconnu ». Or certains négatifs sont CERTAINS : si `capitale(France)=Paris` et que la relation `capitale` est
FONCTIONNELLE (une entité a AU PLUS une capitale), alors `capitale(France)=Berlin` est CERTAINEMENT FAUX. Ce module
dérive ces négatifs certains, en logique TRIVALUÉE (VRAI / FAUX / INCONNU).

FAUX=0 — la ligne rouge (piège de la clôture du monde) :
  • On ne conclut FAUX que pour une relation DÉCLARÉE FONCTIONNELLE (au plus une valeur). Le caractère fonctionnel est
    fourni par l'appelant (ou mesuré ailleurs, ex. schema_relations) — JAMAIS supposé du seul fait qu'une valeur est
    stockée (une relation multi-valuée stockée mono ne prouve pas la fonctionnalité). Sur une relation NON fonctionnelle,
    une valeur différente reste INCONNU (elle pourrait AUSSI être vraie).
  • Absence de valeur connue -> INCONNU (monde ouvert : absence ≠ fausseté). Jamais de CWA aveugle sur le corpus.
Stdlib pur, déterministe, souverain.
"""
from __future__ import annotations

VRAI = "vrai"
FAUX = "faux"
INCONNU = "inconnu"


def statut_fait(valeur_demandee, valeur_connue, fonctionnelle: bool) -> str:
    """Statut trivalué de « (relation, entité) = valeur_demandee », sachant `valeur_connue` (la valeur stockée, ou
    None si absente) et si la relation est FONCTIONNELLE. VRAI si égale ; FAUX si fonctionnelle + différente connue ;
    INCONNU sinon (absence, ou relation multi-valuée où d'autres valeurs peuvent coexister)."""
    if valeur_connue is None:
        return INCONNU                              # monde ouvert : absence -> inconnu, jamais faux
    if valeur_demandee == valeur_connue:
        return VRAI
    if fonctionnelle:
        return FAUX                                 # une seule valeur possible -> toute autre est CERTAINEMENT fausse
    return INCONNU                                  # multi-valuée : la valeur demandée pourrait aussi être vraie


def negatifs_certains(valeur_connue, domaine_valeurs, fonctionnelle: bool) -> set:
    """Sous-ensemble de `domaine_valeurs` CERTAINEMENT faux pour l'entité, sachant `valeur_connue`. Non vide UNIQUEMENT
    si la relation est fonctionnelle ET une valeur est connue (sinon monde ouvert -> aucun négatif certain)."""
    if not fonctionnelle or valeur_connue is None:
        return set()
    return {v for v in domaine_valeurs if v != valeur_connue}


def coherent(faits_positifs: dict, fonctionnelles: set) -> bool:
    """Un ensemble de faits {(relation, entité): valeur} est-il cohérent avec les contraintes de fonctionnalité ?
    (Toujours True ici car un dict a une valeur par clé ; expose l'invariant pour les consommateurs qui agrègent
    plusieurs sources.) FAUX=0 : sert de garde avant de dériver des négatifs — on ne dérive un négatif certain que
    depuis une base cohérente."""
    return isinstance(faits_positifs, dict)
