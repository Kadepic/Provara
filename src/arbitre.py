"""
ARBITRE DE CONTRADICTION (runtime) — brique Vague 7. Tranche quand fait / loi / simulation se contredisent.

POURQUOI : au fil d'un raisonnement, plusieurs sources donnent des valeurs différentes pour une même grandeur. Une
machine honnête ne choisit pas au hasard : elle tranche par la FIABILITÉ des sources SI l'une domine clairement,
sinon elle S'ABSTIENT. C'est le gardien anti-sur-confiance au niveau de l'agrégation.

MODÈLE : des propositions (valeur, source) + une table de fiabilités (source -> poids ≥ 0). On somme la fiabilité par
valeur distincte ; la valeur au poids STRICTEMENT maximal gagne ; égalité au sommet -> abstention.

FAUX=0 :
  • CONSENSUS si toutes les sources s'accordent.
  • Sinon la valeur gagnante doit avoir un poids STRICTEMENT supérieur ; en cas d'ÉGALITÉ au sommet -> ABSTENTION
    (jamais un choix silencieux entre ex æquo).
  • Source de fiabilité inconnue -> poids 0 (ne tranche pas toute seule) ; aucune valeur inventée.
Stdlib pur, déterministe, souverain.
"""
from __future__ import annotations

CONSENSUS = "consensus"
TRANCHE = "tranché"
ABSTENTION = "abstention"


def arbitre(propositions, fiabilites: dict = None):
    """`propositions` = liste de (valeur, source) ; `fiabilites` = {source: poids}. Renvoie
    (statut, valeur|None, detail). statut ∈ CONSENSUS / TRANCHE / ABSTENTION."""
    fiabilites = fiabilites or {}
    if not propositions:
        return (ABSTENTION, None, {"raison": "aucune proposition"})
    # regroupe par valeur distincte, somme les fiabilités
    poids = {}
    repr_val = {}
    for valeur, source in propositions:
        k = repr(valeur)
        repr_val[k] = valeur
        poids[k] = poids.get(k, 0.0) + max(0.0, float(fiabilites.get(source, 0.0)))
    if len(poids) == 1:
        return (CONSENSUS, repr_val[next(iter(poids))], {"raison": "toutes les sources concordent"})
    # contradiction : la valeur au poids strictement maximal l'emporte, sinon abstention
    ordonne = sorted(poids.items(), key=lambda kv: kv[1], reverse=True)
    (k1, p1), (k2, p2) = ordonne[0], ordonne[1]
    if p1 > p2:
        return (TRANCHE, repr_val[k1], {"raison": "fiabilité strictement supérieure", "poids": p1, "second": p2})
    return (ABSTENTION, None, {"raison": "égalité de fiabilité au sommet (contradiction non résolue)",
                               "candidats": [repr_val[k1], repr_val[k2]]})


def valeur_arbitree(propositions, fiabilites=None):
    """Raccourci : la valeur retenue (CONSENSUS/TRANCHE) ou None (ABSTENTION)."""
    statut, valeur, _ = arbitre(propositions, fiabilites)
    return valeur if statut in (CONSENSUS, TRANCHE) else None
