"""
PALIER 2 — EFFET DE CADRAGE / INVARIANCE DE DESCRIPTION : traiter une préférence ÉNONCÉE comme « la » préférence est
sur-confiant (brique 108, 2026-06-27).

Le MÊME choix, reformulé en termes de GAINS ou de PERTES, renverse les préférences (Tversky & Kahneman, « maladie
asiatique ») :
  • Cadre GAIN : programme SÛR « on sauve 200 personnes sur 600 » vs RISQUÉ « 1/3 : on sauve les 600, 2/3 : personne ».
    La plupart choisissent le SÛR (aversion au risque).
  • Cadre PERTE : SÛR « 400 personnes meurent » vs RISQUÉ « 1/3 : personne ne meurt, 2/3 : les 600 meurent ».
    La plupart choisissent le RISQUÉ (recherche de risque).
Or les deux cadres décrivent des loteries IDENTIQUES (« 200 sauvés à coup sûr » = « 400 morts à coup sûr »). Le
renversement viole l'INVARIANCE DE DESCRIPTION — un axiome de rationalité. Une préférence qui dépend d'un habillage
cosmétique est INCOHÉRENTE et EXPLOITABLE (money pump : on facture chaque reformulation).

CAUSE : une fonction de valeur à POINT DE RÉFÉRENCE qui se déplace avec le cadre (concave en gains, convexe en pertes,
aversion aux pertes λ>1). LA CORRECTION : évaluer les CONSÉQUENCES finales par une utilité FRAME-INVARIANTE (référence
fixe) — alors le choix ne dépend plus de l'habillage.

LE MODE D'ÉCHEC DÉMASQUÉ : la « confiance » dans une préférence qui s'inverse sous reformulation est sur-confiante.
Distinct de decision (8, utilité espérée) et variational_preferences (62). ABSTENTION si descriptions non équivalentes.
Pur Python.
"""
from __future__ import annotations

ABSTENTION = "abstention"
ANALYSE = "analyse"

TOTAL = 600
SUR = [(1.0, 200)]                       # 200 sauvés à coup sûr
RISQUE = [(1 / 3, 600), (2 / 3, 0)]      # 1/3 : 600 sauvés, 2/3 : 0 sauvé


def v_prospect(x, ref, alpha=0.88, beta=0.88, lam=2.25):
    """Valeur de prospect (Tversky-Kahneman) relative au point de référence : concave en gains, convexe + λ en pertes."""
    d = x - ref
    return d ** alpha if d >= 0 else -lam * (-d) ** beta


def _esp(dist, f):
    return sum(p * f(x) for p, x in dist)


def choix_prospect(ref, **kw):
    """'sur' ou 'risque' selon la valeur de prospect, point de référence ref (=0 cadre gain, =TOTAL cadre perte)."""
    vs = _esp(SUR, lambda x: v_prospect(x, ref, **kw))
    vr = _esp(RISQUE, lambda x: v_prospect(x, ref, **kw))
    return "sur" if vs >= vr else "risque"


def choix_eu(gamma=0.88):
    """Agent à utilité FRAME-INVARIANTE u(x)=x^γ sur le nombre final de sauvés (référence fixe 0)."""
    us = _esp(SUR, lambda x: x ** gamma)
    ur = _esp(RISQUE, lambda x: x ** gamma)
    return "sur" if us >= ur else "risque"


def money_pump(**kw):
    """Disposition à payer ε pour passer à l'option préférée dans chaque cadre. Si les choix s'inversent, on peut faire
    tourner l'agent : SÛR↔RISQUÉ décrivent les mêmes loteries ⇒ pompe à argent. Renvoie le nb d'étapes 'payantes'."""
    g = choix_prospect(0, **kw)          # cadre gain
    p = choix_prospect(TOTAL, **kw)      # cadre perte
    # exploitable si l'agent veut le SÛR en gain mais le RISQUÉ en perte (ou inversement) — mêmes loteries sous-jacentes
    return 2 if g != p else 0


def analyse(**kw):
    """Façade : choix prospect par cadre vs choix frame-invariant. (ANALYSE, {...}) ou (ABSTENTION)."""
    cg = choix_prospect(0, **kw)
    cp = choix_prospect(TOTAL, **kw)
    return (ANALYSE, {"choix_cadre_gain": cg, "choix_cadre_perte": cp, "renversement": cg != cp,
                      "choix_invariant_gain": choix_eu(), "choix_invariant_perte": choix_eu(),
                      "etapes_money_pump": money_pump(**kw)})


def formule(res) -> str:
    if res[0] == ABSTENTION:
        return f"Pas d'analyse : {res[1]}."
    i = res[1]
    return (f"Cadre GAIN → choix « {i['choix_cadre_gain']} » ; cadre PERTE → choix « {i['choix_cadre_perte']} » "
            f"({'RENVERSEMENT' if i['renversement'] else 'cohérent'}) alors que les loteries sont IDENTIQUES. L'agent "
            f"frame-invariant choisit « {i['choix_invariant_gain']} » dans les deux. Tenir une préférence qui s'inverse "
            f"sous reformulation pour « la » préférence est sur-confiant (incohérent, exploitable par money pump).")


if __name__ == "__main__":
    print("=== EFFET DE CADRAGE / INVARIANCE DE DESCRIPTION (maladie asiatique) ===\n")
    st, info = analyse()
    print(" ", formule((st, info)))
    print(f"\n  étapes de money pump exploitables : {info['etapes_money_pump']}")
