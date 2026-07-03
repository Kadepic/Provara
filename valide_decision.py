"""
VALIDATION de la DÉCISION SOUS INCERTITUDE (decision.py). On prouve le PONT avec la calibration :
  • VALEUR CALIBRÉE : avec des probas CALIBRÉES, l'utilité espérée ANNONCÉE de l'action choisie = l'utilité moyenne
    RÉELLEMENT obtenue (sur un monde simulé connu).
  • SUR-CONFIANCE -> SUR-PROMESSE : avec des probas sur-confiantes, l'utilité annoncée DÉPASSE la réalisée (la décision
    ment sur sa valeur, comme un « 90 % » qui n'arrive que 70 % du temps).
  • UTILITÉ : la décision coût-sensible (utilité espérée) BAT l'argmax-proba naïf sous coûts asymétriques.
  • ABSTENTION : la marge évite les décisions non robustes (écart d'utilité dans le bruit).
"""
from __future__ import annotations

import random

from garde_ressources import borne
import decision as D
from decision import DECISION, ABSTENTION

borne()
ok = 0
total = 0


def check(nom, cond):
    global ok, total
    total += 1
    print(f"  [{'OK ' if cond else 'XXX'}] {nom}", flush=True)
    if cond:
        ok += 1
    else:
        raise AssertionError(nom)


# dépistage : rater un malade coûte 10, traiter un sain coûte 1 (asymétrie)
UTIL = {"traiter":        {"malade": 0.0,  "sain": -1.0},
        "ne_pas_traiter": {"malade": -10.0, "sain": 0.0}}


def monde(M, graine, durcis=1.0):
    """M exemples : vraie proba de maladie q ~ U(0,0.5) ; issue y ~ Bernoulli(q). Proba ANNONCÉE = durcir(q) vers 0/1
    si durcis<1 (sur-confiance). Renvoie liste de (probas_annoncées, q_vrai, y)."""
    rng = random.Random(graine)
    out = []
    for _ in range(M):
        q = 0.5 * rng.random()
        y = "malade" if rng.random() < q else "sain"
        if durcis < 1.0:                      # durcit la proba (plus extrême) = sur-confiance
            qa = q ** durcis / (q ** durcis + (1 - q) ** durcis)
        else:
            qa = q
        out.append(({"malade": qa, "sain": 1 - qa}, q, y))
    return out


print("=== VALEUR CALIBRÉE : utilité espérée annoncée ≈ utilité réalisée (probas calibrées) ===")
data = monde(20000, graine=1, durcis=1.0)
eu_annoncee, u_realisee = 0.0, 0.0
for (probas, q, y) in data:
    st, a, eu = D.decide(probas, UTIL)
    eu_annoncee += eu[a]
    u_realisee += UTIL[a][y]
eu_annoncee /= len(data); u_realisee /= len(data)
print(f"   EU annoncée = {eu_annoncee:.3f} ; utilité réalisée = {u_realisee:.3f}")
check(f"valeur calibrée : |annoncée − réalisée| = {abs(eu_annoncee-u_realisee):.3f} <= 0.05", abs(eu_annoncee - u_realisee) <= 0.05)

print("=== SUR-CONFIANCE -> SUR-PROMESSE : annoncée > réalisée (la décision ment sur sa valeur) ===")
data_sc = monde(20000, graine=2, durcis=0.3)     # probas durcies = sur-confiantes
eu_a, u_r = 0.0, 0.0
for (probas, q, y) in data_sc:
    st, a, eu = D.decide(probas, UTIL)
    eu_a += eu[a]
    u_r += UTIL[a][y]
eu_a /= len(data_sc); u_r /= len(data_sc)
print(f"   EU annoncée = {eu_a:.3f} ; utilité réalisée = {u_r:.3f}")
check(f"sur-confiance : EU annoncée ({eu_a:.3f}) > réalisée ({u_r:.3f}) (sur-promesse)", eu_a > u_r + 0.03)

print("=== UTILITÉ : décision coût-sensible BAT l'argmax-proba naïf (coûts asymétriques) ===")
u_cout, u_naif = 0.0, 0.0
for (probas, q, y) in data:                     # probas calibrées
    _, a_cout, _ = D.decide(probas, UTIL)
    a_naif = "traiter" if probas["malade"] > 0.5 else "ne_pas_traiter"   # suit la classe la + probable
    u_cout += UTIL[a_cout][y]
    u_naif += UTIL[a_naif][y]
u_cout /= len(data); u_naif /= len(data)
print(f"   utilité coût-sensible = {u_cout:.3f} ; argmax-proba naïf = {u_naif:.3f}")
check(f"coût-sensible ({u_cout:.3f}) > naïf ({u_naif:.3f})", u_cout > u_naif)

print("=== seuil de bascule cohérent avec l'asymétrie (traiter dès q > 1/11 ≈ 0.091) ===")
check("q=0.12 -> traiter", D.decide({"malade": 0.12, "sain": 0.88}, UTIL)[1] == "traiter")
check("q=0.05 -> ne pas traiter", D.decide({"malade": 0.05, "sain": 0.95}, UTIL)[1] == "ne_pas_traiter")

print("=== ABSTENTION : marge sur décision serrée + cas dégénéré ===")
st, _, _ = D.decide({"malade": 0.09, "sain": 0.91}, UTIL, marge_abstention=0.5)
check("décision serrée + marge -> ABSTENTION", st == ABSTENTION)
st2, a2, _ = D.decide({"malade": 0.30, "sain": 0.70}, UTIL, marge_abstention=0.5)
check("décision nette malgré la marge -> DECISION", st2 == DECISION)
check("aucune action -> ABSTENTION", D.decide({"malade": 0.5}, {})[0] == ABSTENTION)

print("=== sur les cas ABSTENUS, l'écart d'utilité est effectivement petit (abstention pertinente) ===")
marge = 0.4
ecarts_abst = []
for (probas, q, y) in data:
    st, a, eu = D.decide(probas, UTIL, marge_abstention=marge)
    vals = sorted(eu.values(), reverse=True)
    if st == ABSTENTION:
        ecarts_abst.append(vals[0] - vals[1])
check(f"tous les écarts d'utilité abstenus < marge {marge} (n={len(ecarts_abst)})",
      all(e < marge for e in ecarts_abst) and len(ecarts_abst) > 0)

print(f"\nDECISION VALIDÉ — {ok}/{total}." if ok == total else f"\nÉCHEC {ok}/{total}")
