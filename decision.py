"""
PALIER 2 — DÉCISION SOUS INCERTITUDE CALIBRÉE (brique 8, 2026-06-25). Le capstone : estimer -> calibrer -> DÉCIDER.

Une probabilité calibrée ne sert que si elle guide une ACTION. Quand les actions ont des conséquences ASYMÉTRIQUES
(un faux négatif médical coûte bien plus qu'un faux positif), décider = maximiser l'UTILITÉ ESPÉRÉE, pas suivre la
classe la plus probable :

    EU(action a) = Σ_classe  P(classe) · utilité[a][classe]          ->  on choisit argmax_a EU(a)

LE PONT AVEC LA CALIBRATION (l'invariant) : SI les probabilités sont calibrées, l'utilité espérée ANNONCÉE de
l'action choisie ÉGALE l'utilité moyenne RÉELLEMENT obtenue (preuve : E[u(a,y)] = Σ_c P(c) u(a,c)). Une décision
fondée sur des probas SUR-CONFIANTES SUR-PROMET sa valeur (réalisé < annoncé) — c'est le même mensonge qu'un « 90 % »
qui n'arrive que 70 % du temps, transposé à l'action. La qualité de la décision est donc bornée par la calibration.

ABSTENTION HONNÊTE : si l'écart d'utilité espérée entre la meilleure action et la suivante est sous une MARGE (la
décision n'est pas robuste, on pourrait se tromper d'action), on s'abstient / on demande plus d'information.
"""
from __future__ import annotations

ABSTENTION = "abstention"
DECISION = "decision"


def utilites_attendues(probas, utilites):
    """EU de chaque action. `probas` = dict {classe: proba} ; `utilites` = dict {action: {classe: utilité}}.
    Renvoie dict {action: EU}. Classes manquantes dans une utilité d'action -> utilité 0 pour cette classe."""
    eu = {}
    for a, table in utilites.items():
        eu[a] = sum(p * table.get(c, 0.0) for c, p in probas.items())
    return eu


def decide(probas, utilites, marge_abstention: float = 0.0):
    """Choisit l'action d'utilité espérée MAXIMALE. Renvoie (DECISION, action, eu_dict) si l'écart EU avec la 2ᵉ
    meilleure action ≥ marge_abstention, sinon (ABSTENTION, None, eu_dict) — décision non robuste. eu_dict toujours
    fourni pour la transparence."""
    if not utilites:
        return (ABSTENTION, None, {})
    eu = utilites_attendues(probas, utilites)
    ordre = sorted(eu, key=eu.get, reverse=True)
    meilleure = ordre[0]
    ecart = eu[meilleure] - eu[ordre[1]] if len(ordre) > 1 else float("inf")
    if ecart < marge_abstention:
        return (ABSTENTION, None, eu)
    return (DECISION, meilleure, eu)


def formule(res) -> str:
    statut = res[0]
    if statut == ABSTENTION:
        if not res[2]:
            return "Je ne peux pas décider : aucune action proposée."
        return ("Je préfère m'abstenir : les meilleures actions ont une utilité espérée trop proche — décider "
                "maintenant serait un pari, pas un choix.")
    _, action, eu = res
    return f"Je recommande « {action} » (utilité espérée la plus élevée : {eu[action]:.3g}), sous l'incertitude calibrée."


if __name__ == "__main__":
    print("=== DÉCISION SOUS INCERTITUDE CALIBRÉE ===\n")
    # dépistage : classes {malade, sain} ; actions {traiter, ne_pas_traiter} ; rater un malade coûte très cher
    util = {"traiter":       {"malade": 0.0,  "sain": -1.0},     # traiter à tort : coût modéré
            "ne_pas_traiter": {"malade": -10.0, "sain": 0.0}}    # rater un malade : coût lourd
    # même à 20% de proba de maladie, l'utilité espérée recommande de traiter (asymétrie des coûts)
    print(" ", formule(decide({"malade": 0.20, "sain": 0.80}, util)))
    print(" ", formule(decide({"malade": 0.02, "sain": 0.98}, util)))   # très faible risque -> ne pas traiter
    # décision serrée -> abstention
    print(" ", formule(decide({"malade": 0.09, "sain": 0.91}, util, marge_abstention=0.5)))
