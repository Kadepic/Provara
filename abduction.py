"""
ABDUCTION — brique Vague 5 (inférence de la meilleure explication). Dépend de causalite.py.

POURQUOI : face à des observations, la machine doit proposer des HYPOTHÈSES qui les expliqueraient (« qu'est-ce qui,
en amont, produirait ce que j'observe ? ») — étape amont du diagnostic et de l'invention (comprendre un phénomène pour
le reproduire ou l'empêcher). Contrairement à la déduction, l'abduction est faillible : elle propose, elle n'affirme pas.

MODÈLE : sur un graphe causal (causalite.GrapheCausal) et un ensemble d'OBSERVATIONS (effets constatés), une
hypothèse candidate = une cause (nœud) dont les descendants causals couvrent des observations. On cherche le plus
PETIT ensemble d'hypothèses expliquant TOUTES les observations (parcimonie = rasoir d'Ockham).

FAUX=0 :
  • Une hypothèse n'« explique » une observation QUE si un chemin causal RÉEL la relie (via causalite) — jamais une
    explication plaquée.
  • L'explication renvoyée est VÉRIFIÉE : la réunion des effets des hypothèses couvre bien toutes les observations.
  • Aucune observation inexpliquée cachée : si rien ne peut expliquer une observation, c'est signalé (inexpliquees).
  • Proposé, non affirmé : l'abduction retourne des CANDIDATS classés, pas une vérité.
Stdlib pur, déterministe, souverain.
"""
from __future__ import annotations

from itertools import combinations


def explique(graphe, hypothese, observation) -> bool:
    """True ssi `hypothese` est une cause (directe ou transitive) de `observation` dans le graphe (chemin réel)."""
    return observation in graphe.descendants(hypothese)


def hypotheses_possibles(graphe, observations):
    """Nœuds pouvant expliquer AU MOINS une observation (leurs ancêtres causals), triés déterministe."""
    cands = set()
    for o in observations:
        cands |= graphe.ancetres(o)
    return sorted(cands, key=repr)


def meilleure_explication(graphe, observations, taille_max: int = 3):
    """Plus petit ensemble d'hypothèses (causes) expliquant TOUTES les observations. Renvoie
    {hypotheses:[...], couvre:{obs...}, inexpliquees:{obs...}} ou None si aucune explication ne couvre tout.
    Parcimonie : ensembles essayés par taille croissante. Déterministe."""
    obs = set(observations)
    cands = hypotheses_possibles(graphe, obs)
    # observations qu'AUCUNE cause ne peut expliquer (pas d'ancêtre) -> inexplicables, signalées
    inexpliquees = {o for o in obs if not any(explique(graphe, h, o) for h in cands)}
    a_couvrir = obs - inexpliquees
    if not a_couvrir:
        return {"hypotheses": [], "couvre": set(), "inexpliquees": inexpliquees} if inexpliquees else \
               {"hypotheses": [], "couvre": set(), "inexpliquees": set()}
    for k in range(1, min(taille_max, len(cands)) + 1):
        for combo in combinations(cands, k):
            couvertes = set()
            for h in combo:
                couvertes |= {o for o in a_couvrir if explique(graphe, h, o)}
            if couvertes == a_couvrir:           # VÉRIFICATION : couvre bien tout le couvrable (FAUX=0)
                return {"hypotheses": list(combo), "couvre": couvertes, "inexpliquees": inexpliquees}
    return None
