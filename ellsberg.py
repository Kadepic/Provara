"""
PALIER 2 — PARADOXE D'ELLSBERG (aversion à l'ambiguïté / principe de la chose sûre) : supposer qu'un seul prior
probabiliste rationalise les choix est sur-confiant (brique 124, 2026-06-28).

Une urne contient 30 boules ROUGES et 60 boules NOIRES-ou-JAUNES en proportion INCONNUE (total 90). On parie 100 € :
  • Pari A : gagne si ROUGE (probabilité CONNUE 1/3)  vs  Pari B : gagne si NOIR (probabilité AMBIGUË).
  • Pari C : gagne si ROUGE ou JAUNE (ambigu)  vs  Pari D : gagne si NOIR ou JAUNE (= 60/90 CONNU).
La plupart préfèrent A ≻ B (le connu) ET D ≻ C (le connu) — AVERSION À L'AMBIGUÏTÉ. Or, sous un PRIOR UNIQUE avec
P(R)=1/3, P(B)=b, P(Y)=2/3−b :
  A ≻ B ⟺ 1/3 > b   et   D ≻ C ⟺ b > 1/3 — CONTRADICTOIRES. AUCUNE probabilité unique ne rationalise le schéma
d'Ellsberg. C'est aussi une violation du PRINCIPE DE LA CHOSE SÛRE : C et D ajoutent le MÊME événement JAUNE aux paris A
et B ; cette conséquence commune ne devrait pas renverser la préférence.

Un agent AVERSE À L'AMBIGUÏTÉ (maxmin sur l'ensemble crédal b∈[0,2/3]) évalue chaque pari par sa probabilité INFÉRIEURE
(pire cas) : A=1/3 > B=0 et D=2/3 > C=1/3 ⇒ il exhibe le schéma. L'ambiguïté demande des probabilités IMPRÉCISES, pas un
prior unique.

LE MODE D'ÉCHEC DÉMASQUÉ : tenir pour acquis qu'un agent rationnel a un prior unique (probabilités précises) est
SUR-confiant — l'aversion à l'ambiguïté le réfute. Analogue ambiguïté du paradoxe d'Allais (118, risque). Distinct de
decision_ambiguite (60, règle maxmin) et smooth_ambiguity (61). Pur Python, rng seedé.
"""
from __future__ import annotations

ABSTENTION = "abstention"
ANALYSE = "analyse"

P_ROUGE = 1.0 / 3.0
P_NOIR_OU_JAUNE = 2.0 / 3.0


def paris_eu(pB):
    """Probabilités de gain des 4 paris sous un prior unique (P(R)=1/3, P(B)=pB, P(Y)=2/3−pB). Renvoie (A,B,C,D)."""
    pR = P_ROUGE
    pY = P_NOIR_OU_JAUNE - pB
    return pR, pB, pR + pY, pB + pY      # A=rouge, B=noir, C=rouge∨jaune, D=noir∨jaune


def schema_ellsberg(A, B, C, D):
    """True si le schéma d'Ellsberg (A≻B ET D≻C) est présent."""
    return A > B and D > C


def paris_maxmin():
    """Probabilités INFÉRIEURES (pire cas sur l'ensemble crédal b∈[0,2/3]) des 4 paris. Renvoie (A,B,C,D)."""
    A = P_ROUGE                      # rouge : connu 1/3
    B = 0.0                          # noir : pire cas b=0
    C = P_ROUGE                      # rouge∨jaune : pire cas b=2/3 ⇒ pY=0
    D = P_NOIR_OU_JAUNE              # noir∨jaune : connu 2/3
    return A, B, C, D


def analyse(pB=1.0 / 3.0):
    """Façade : un agent EU (prior pB) ne peut pas exhiber Ellsberg ; un agent maxmin (averse à l'ambiguïté) le peut.
    (ANALYSE, {eu_ellsberg, maxmin_ellsberg, ...}) ou (ABSTENTION)."""
    if not (0 <= pB <= P_NOIR_OU_JAUNE):
        return (ABSTENTION, "pB hors [0, 2/3]")
    eu_e = schema_ellsberg(*paris_eu(pB))
    mm_e = schema_ellsberg(*paris_maxmin())
    return (ANALYSE, {"eu_ellsberg": eu_e, "maxmin_ellsberg": mm_e, "pB": pB})


def formule(res) -> str:
    if res[0] == ABSTENTION:
        return f"Pas d'analyse : {res[1]}."
    i = res[1]
    return (f"Un agent à prior UNIQUE n'exhibe JAMAIS le schéma d'Ellsberg (eu_ellsberg={i['eu_ellsberg']}) — il faudrait "
            f"P(noir) à la fois < et > 1/3. Un agent AVERSE À L'AMBIGUÏTÉ (maxmin/probabilités inférieures) le reproduit "
            f"(maxmin_ellsberg={i['maxmin_ellsberg']}). Supposer un prior unique (probabilités précises) est sur-confiant — "
            f"l'ambiguïté exige des probabilités imprécises.")


if __name__ == "__main__":
    print("=== PARADOXE D'ELLSBERG (aversion à l'ambiguïté) ===\n")
    st, info = analyse()
    print(" ", formule((st, info)))
