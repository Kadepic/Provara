"""
VALIDATION de l'AGRÉGATION D'OPINIONS (opinions.py) — jugée par scores_propres.py. La pondération par fiabilité rend
le pool ROBUSTE à un mauvais expert (poids -> 0) et BAT l'expert moyen ; le pool log est plus tranché que le linéaire.
"""
from __future__ import annotations

import random

from garde_ressources import borne
import opinions as O
import scores_propres as S

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


def clip(p):
    return max(0.02, min(0.98, p))


def jeu(n, graine):
    """Experts : 'bon' (proche de q), 'moyen' (bruité), 'nul' (anti-corrélé/constant). Renvoie (sorties, issues, q)."""
    rng = random.Random(graine)
    sorties = {"bon": [], "moyen": [], "nul": []}
    issues, qs = [], []
    for _ in range(n):
        q = rng.random()
        y = 1 if rng.random() < q else 0
        issues.append(y); qs.append(q)
        sorties["bon"].append(clip(q + rng.gauss(0, 0.08)))
        sorties["moyen"].append(clip(q + rng.gauss(0, 0.25)))
        sorties["nul"].append(clip(1 - q + rng.gauss(0, 0.1)))     # anti-corrélé = nuisible
    return sorties, issues, qs


s_cal, y_cal, _ = jeu(4000, graine=1)
s_test, y_test, _ = jeu(4000, graine=2)
poids = O.poids_fiabilite(s_cal, y_cal)
print(f"=== POIDS DE FIABILITÉ : le nul est écarté ===\n   {dict((k, round(v,3)) for k,v in poids.items())}")
check("poids(bon) > poids(moyen) > poids(nul)", poids["bon"] > poids["moyen"] > poids["nul"])
check("poids(nul) nettement écarté (< moitié du bon)", poids["nul"] < poids["bon"] / 2)

print("=== POOL PONDÉRÉ bat l'expert moyen + le pool UNIFORME (log-loss) ===")
def ll_pool(methode, poids_, sorties):
    p = [O.combine({e: sorties[e][i] for e in sorties}, poids_, methode) for i in range(len(y_test))]
    return S.log_loss(p, y_test)
ll_pondere = ll_pool("lineaire", poids, s_test)
ll_uniforme = ll_pool("lineaire", None, s_test)
ll_bon = S.log_loss(s_test["bon"], y_test)
ll_moyen = S.log_loss(s_test["moyen"], y_test)
print(f"   pondéré={ll_pondere:.3f} ; uniforme={ll_uniforme:.3f} ; bon={ll_bon:.3f} ; moyen={ll_moyen:.3f}")
check(f"pool pondéré ({ll_pondere:.3f}) < uniforme ({ll_uniforme:.3f})", ll_pondere < ll_uniforme)
check(f"pool pondéré ({ll_pondere:.3f}) < expert moyen ({ll_moyen:.3f})", ll_pondere < ll_moyen)

print("=== ROBUSTESSE : ajouter un expert CATASTROPHIQUE ne dégrade quasi pas le pool pondéré ===")
s_cal2 = dict(s_cal)
s_cal2["catastrophe"] = [clip(1 - s_cal["bon"][i]) for i in range(len(y_cal))]    # à contre-courant fort
s_test2 = dict(s_test); s_test2["catastrophe"] = [clip(1 - s_test["bon"][i]) for i in range(len(y_test))]
poids2 = O.poids_fiabilite(s_cal2, y_cal)
ll_pondere2 = ll_pool("lineaire", poids2, s_test2)
ll_uniforme2 = ll_pool("lineaire", None, s_test2)
print(f"   avec catastrophe : pondéré={ll_pondere2:.3f} (sans={ll_pondere:.3f}) ; uniforme={ll_uniforme2:.3f}")
check(f"pondéré quasi inchangé malgré l'expert catastrophe (|Δ|<0.05)", abs(ll_pondere2 - ll_pondere) < 0.05)
check(f"uniforme bien plus dégradé par la catastrophe (pondéré << uniforme)", ll_pondere2 < ll_uniforme2 - 0.05)

print("=== POOL LOG plus TRANCHÉ que le LINÉAIRE sur un consensus ===")
consensus = {"a": 0.8, "b": 0.85, "c": 0.75}
check("log > linéaire quand tous d'accord (>0.5)", O.pool_log(consensus) > O.pool_lineaire(consensus))
consensus_bas = {"a": 0.2, "b": 0.15, "c": 0.25}
check("log < linéaire quand tous d'accord (<0.5)", O.pool_log(consensus_bas) < O.pool_lineaire(consensus_bas))

print("=== bornes + cas limites ===")
check("pool dans [0,1]", 0.0 <= O.pool_lineaire({"a": 0.3, "b": 0.7}) <= 1.0 and 0.0 <= O.pool_log({"a": 0.3, "b": 0.7}) <= 1.0)
check("un seul expert -> son avis (linéaire)", abs(O.pool_lineaire({"a": 0.42}) - 0.42) < 1e-9)
check("poids nuls -> repli uniforme", abs(O.pool_lineaire({"a": 0.2, "b": 0.8}, {"a": 0, "b": 0}) - 0.5) < 1e-9)

print(f"\nOPINIONS VALIDÉ — {ok}/{total}." if ok == total else f"\nÉCHEC {ok}/{total}")
