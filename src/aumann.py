"""
PALIER 2 — THÉORÈME D'ACCORD D'AUMANN : « convenir d'être en désaccord » est sur-confiant (brique 116, 2026-06-28).

Deux agents BAYÉSIENS partageant le MÊME PRIOR, dotés d'informations privées différentes, calculent chacun leur
probabilité a posteriori d'un même événement E. Aumann (1976) : si ces postérieurs deviennent de CONNAISSANCE COMMUNE
(chacun connaît celui de l'autre, sait que l'autre connaît le sien, etc.), alors ils sont nécessairement ÉGAUX. On ne
peut PAS « convenir d'être en désaccord ».

Le mécanisme (Geanakoplos-Polemarchakis) : annoncer son postérieur est une information. En entendant celui de l'autre,
chacun élimine les états du monde incompatibles avec cette annonce, puis recalcule. En itérant, les annonces CONVERGENT
vers une valeur COMMUNE en un nombre fini de tours — même si les postérieurs INITIAUX divergeaient.

Le prior commun est essentiel : avec des priors DIFFÉRENTS, le théorème tombe et un désaccord peut persister (honnêteté).

LE MODE D'ÉCHEC DÉMASQUÉ : maintenir un postérieur différent de celui d'un pair rationnel qui partage votre prior et dont
vous connaissez le postérieur est SUR-CONFIANT (incohérent). Un désaccord persistant signale priors différents ou
information privée non encore partagée. Distinct de bayes (combinaison) et conversation/mémoire. ABSTENTION si structure
incohérente. Pur Python.
"""
from __future__ import annotations

ABSTENTION = "abstention"
ANALYSE = "analyse"


def _cellule(partition, w):
    for c in partition:
        if w in c:
            return set(c)
    return {w}


def _posterior(S, E, prior):
    den = sum(prior[s] for s in S)
    return sum(prior[s] for s in S if s in E) / den if den > 0 else 0.0


def dialogue(omega_etats, P1, P2, E, omega, prior1=None, prior2=None):
    """Annonces itérées des postérieurs (Geanakoplos-Polemarchakis). prior1/prior2 : priors par agent (communs par
    défaut, uniformes). Renvoie {init1, init2, final1, final2, egaux, rounds}."""
    n = len(omega_etats)
    if prior1 is None:
        prior1 = {s: 1 / n for s in omega_etats}
    if prior2 is None:
        prior2 = prior1
    E = set(E)
    init1 = _posterior(_cellule(P1, omega), E, prior1)
    init2 = _posterior(_cellule(P2, omega), E, prior2)
    K = set(omega_etats)
    rounds = 0
    for _ in range(4 * n + 5):
        a1 = {w: _posterior(_cellule(P1, w) & K, E, prior1) for w in K}
        a2 = {w: _posterior(_cellule(P2, w) & K, E, prior2) for w in K}
        Kn = {w for w in K if abs(a1[w] - a1[omega]) < 1e-9 and abs(a2[w] - a2[omega]) < 1e-9}
        rounds += 1
        if Kn == K:
            break
        K = Kn
    f1 = _posterior(_cellule(P1, omega) & K, E, prior1)
    f2 = _posterior(_cellule(P2, omega) & K, E, prior2)
    return {"init1": init1, "init2": init2, "final1": f1, "final2": f2,
            "egaux": abs(f1 - f2) < 1e-9, "rounds": rounds}


def analyse(omega_etats, P1, P2, E, omega, prior1=None, prior2=None):
    """Façade. (ANALYSE, dialogue(...)) ou (ABSTENTION, raison)."""
    union1 = set().union(*P1) if P1 else set()
    union2 = set().union(*P2) if P2 else set()
    if set(omega_etats) != union1 or set(omega_etats) != union2 or omega not in omega_etats:
        return (ABSTENTION, "partitions ne couvrant pas Ω ou état hors Ω")
    return (ANALYSE, dialogue(omega_etats, P1, P2, E, omega, prior1, prior2))


def formule(res) -> str:
    if res[0] == ABSTENTION:
        return f"Pas d'analyse : {res[1]}."
    i = res[1]
    if i["egaux"]:
        return (f"Postérieurs initiaux ({i['init1']:.2f}, {i['init2']:.2f}) — possiblement différents. Après {i['rounds']} "
                f"tours d'échange, ils CONVERGENT vers la même valeur ({i['final1']:.3f}). « Convenir d'être en désaccord » "
                f"serait sur-confiant : à prior commun, des postérieurs de connaissance commune sont égaux.")
    return (f"Postérieurs finaux ({i['final1']:.3f}, {i['final2']:.3f}) DIFFÉRENTS — possible seulement si les priors "
            f"diffèrent (le théorème d'Aumann requiert un prior commun).")


if __name__ == "__main__":
    Omega = list(range(8))
    P1 = [{0, 1}, {2, 3}, {4, 5}, {6, 7}]
    P2 = [{1, 2}, {3, 4}, {5, 6}, {7, 0}]
    E = {0, 1, 2, 3}
    print("=== THÉORÈME D'ACCORD D'AUMANN ===\n")
    st, info = analyse(Omega, P1, P2, E, omega=0)
    print(" ", formule((st, info)))
    # priors différents (même information) → désaccord persistant : le théorème ne s'applique pas
    Pc = [{0, 4}, {1, 5}, {2, 6}, {3, 7}]              # cellule {0,4} mêle E (0) et non-E (4)
    pr1 = {s: 1 / 8 for s in Omega}
    pr2 = {s: (0.4 if s in E else 0.1) for s in Omega}
    tot = sum(pr2.values()); pr2 = {s: v / tot for s, v in pr2.items()}
    st2, info2 = analyse(Omega, Pc, Pc, E, omega=0, prior1=pr1, prior2=pr2)
    print(" ", formule((st2, info2)))
