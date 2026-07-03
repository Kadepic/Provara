"""
PALIER 2 — SOPHISME DU COÛT IRRÉCUPÉRABLE (effet Concorde) : intégrer une dépense DÉJÀ engagée dans une décision future
est sur-confiant (brique 111, 2026-06-28).

« J'ai déjà investi S, je dois continuer pour ne pas le gaspiller. » SUR-CONFIANT : S est IRRÉCUPÉRABLE — dépensé quelle
que soit la suite. La décision rationnelle ne compare que les coûts et bénéfices FUTURS marginaux :
    continuer  ⟺  E[V] > C   (V = valeur espérée d'achèvement, C = coût restant à payer),
INDÉPENDAMMENT de S. L'agent « coût irrécupérable » ajoute un terme croissant avec S (aversion à « gâcher » l'investi) :
    continuer  ⟺  E[V] − C + λ·S > 0,
si bien qu'avec un S grand il poursuit des projets où E[V] < C — il « jette l'argent par les fenêtres ». En séquentiel
(effet Concorde / escalade d'engagement), plus on a investi, plus on s'enfonce.

LE MODE D'ÉCHEC DÉMASQUÉ : la « confiance » qu'un gros investissement passé justifie de continuer est sur-confiante et
perd de l'argent en espérance. La décision optimale est INVARIANTE au coût irrécupérable. Distinct de decision (8, utilité
espérée) et risque_conforme (12). ABSTENTION si données incohérentes. Pur Python, rng seedé.
"""
from __future__ import annotations

ABSTENTION = "abstention"
ANALYSE = "analyse"


def continuer_rationnel(valeur_esperee, cout_restant):
    """Décision rationnelle (forward-looking) : continuer ssi E[V] > C. Le coût irrécupérable n'y figure pas."""
    return valeur_esperee > cout_restant


def continuer_cout_irrecuperable(valeur_esperee, cout_restant, sunk, lam=0.5):
    """Agent biaisé : pondère POSITIVEMENT le coût déjà engagé (aversion à gâcher S)."""
    return (valeur_esperee - cout_restant + lam * sunk) > 0


def payoff_forward(continue_, valeur_realisee, cout_restant):
    """Gain réalisé à partir du point de décision (S est déjà dépensé, hors de ce calcul)."""
    return (valeur_realisee - cout_restant) if continue_ else 0.0


def escalade_concorde(stages_ev, cout_par_stage, sunk0, lam=0.5):
    """Décision séquentielle : à chaque étape, E[V] de finir si on continue. Renvoie (stage_arret_rationnel,
    stage_arret_biaise, perte_rationnelle, perte_biaisee). stages_ev[k] = E[V] d'achèvement vu à l'étape k."""
    sunk = sunk0
    arret_rat = arret_biais = None
    paye_rat = paye_biais = 0.0
    for k, ev in enumerate(stages_ev):
        if arret_rat is None and not continuer_rationnel(ev, cout_par_stage):
            arret_rat = k
        if arret_biais is None and not continuer_cout_irrecuperable(ev, cout_par_stage, sunk, lam):
            arret_biais = k
        if arret_biais is None:
            paye_biais += cout_par_stage          # le biaisé continue de payer
        if arret_rat is None:
            paye_rat += cout_par_stage
        sunk += cout_par_stage
    return (arret_rat if arret_rat is not None else len(stages_ev),
            arret_biais if arret_biais is not None else len(stages_ev),
            paye_rat, paye_biais)


def analyse(valeur_esperee, cout_restant, sunk, lam=0.5):
    """Façade : décisions rationnelle vs biaisée pour un projet (E[V], C, S). (ANALYSE, {...}) ou (ABSTENTION)."""
    if cout_restant < 0 or sunk < 0:
        return (ABSTENTION, "coûts négatifs")
    rat = continuer_rationnel(valeur_esperee, cout_restant)
    biais = continuer_cout_irrecuperable(valeur_esperee, cout_restant, sunk, lam)
    return (ANALYSE, {"continuer_rationnel": rat, "continuer_biaise": biais,
                      "valeur_esperee": valeur_esperee, "cout_restant": cout_restant, "sunk": sunk,
                      "erreur_biais": (biais and not rat), "ev_continuation": valeur_esperee - cout_restant})


def formule(res) -> str:
    if res[0] == ABSTENTION:
        return f"Pas d'analyse : {res[1]}."
    i = res[1]
    diag = ("le biais POURSUIT un projet perdant (E[V] − C < 0) à cause du coût irrécupérable"
            if i["erreur_biais"] else "les deux décident pareil ici")
    return (f"E[V]={i['valeur_esperee']:.1f}, coût restant C={i['cout_restant']:.1f}, déjà engagé S={i['sunk']:.1f}. "
            f"Rationnel : {'continuer' if i['continuer_rationnel'] else 'arrêter'} (E[V]−C={i['ev_continuation']:.1f}, "
            f"S hors sujet) ; biaisé : {'continuer' if i['continuer_biaise'] else 'arrêter'} — {diag}. Tenir compte du "
            f"coût irrécupérable est sur-confiant.")


if __name__ == "__main__":
    print("=== SOPHISME DU COÛT IRRÉCUPÉRABLE (effet Concorde) ===\n")
    # projet perdant (E[V]=8 < C=10) mais gros déjà investi (S=20)
    print(" ", formule(analyse(8.0, 10.0, 20.0)))
    # invariance : même projet, S=0
    print(" ", formule(analyse(8.0, 10.0, 0.0)))
    r, b, pr, pb = escalade_concorde([8, 7, 6, 5, 4], 10.0, 20.0)
    print(f"\n  escalade : arrêt rationnel à l'étape {r}, biaisé à {b} ; payé rationnel={pr:.0f}, biaisé={pb:.0f}")
