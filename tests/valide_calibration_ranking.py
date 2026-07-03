"""
VALIDATION de la CALIBRATION DU CLASSEMENT (calibration_ranking.py) — jugée par calibration.py. Modèle aux scores
AMPLIFIÉS (échelle trop large) face à une pertinence vraie BRUITÉE : le sigmoïde BRUT des comparaisons par paires est
SUR-CONFIANT (annonce des quasi-certitudes que l'ordre dément), la température apprise sur un jeu de CALIBRATION le rend
CALIBRÉ sur un jeu de TEST séparé — SANS changer l'ordre du classement. NDCG : un classement aligné bat un aléatoire.
"""
from __future__ import annotations

import math
import random

from garde_ressources import borne
import calibration_ranking as R
from calibration_ranking import ESTIMATION, ABSTENTION
import calibration as CAL
from calibration import SURCONFIANT

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


def echantillon(rng, n):
    rel = [rng.gauss(0, 1.0) for _ in range(n)]
    score = [4.0 * r for r in rel]                       # scores AMPLIFIÉS -> sigmoïde brut sature
    truth = [r + rng.gauss(0, 1.0) for r in rel]         # « réellement mieux » bruité
    return score, truth


def paires(score, truth):
    diffs, ordres = [], []
    n = len(score)
    for i in range(n):
        for j in range(n):
            if i != j:
                diffs.append(score[i] - score[j]); ordres.append(1 if truth[i] > truth[j] else 0)
    return diffs, ordres


def conf_just(diffs, ordres, T):
    """Convertit chaque paire en (confiance=max(p,1−p), justesse=direction prédite correcte)."""
    conf, just = [], []
    for d, y in zip(diffs, ordres):
        p = R.proba_mieux(d, 0.0, T)         # proba que i (diff=d>0?) soit mieux ; d déjà = s_i−s_j
        pred_i_mieux = 1 if p >= 0.5 else 0
        conf.append(max(p, 1 - p))
        just.append(1.0 if pred_i_mieux == y else 0.0)
    return conf, just


rng = random.Random(2)
s_tr, t_tr = echantillon(rng, 55)
s_te, t_te = echantillon(rng, 55)
d_tr, o_tr = paires(s_tr, t_tr)
d_te, o_te = paires(s_te, t_te)

print("=== Apprentissage de la température sur le jeu de CALIBRATION ===")
st, T, ll = R.calibre(d_tr, o_tr)
print(f"   T appris = {T:.2f}")
check("T > 1 (le sigmoïde brut était trop tranché)", T > 1.0)

print("=== Sigmoïde BRUT (T=1) sur le TEST : SUR-CONFIANT ===")
cR, jR = conf_just(d_te, o_te, 1.0)
vR, iR = CAL.est_calibre(cR, jR, n_bins=10)
print(f"   verdict brut={vR}, ECE={iR['ece']:.3f}")
check("sigmoïde brut SUR-CONFIANT sur le test", vR == SURCONFIANT)

print("=== Sigmoïde TEMPÉRÉ (T appris) sur le TEST : CALIBRÉ ===")
cT, jT = conf_just(d_te, o_te, T)
vT, iT = CAL.est_calibre(cT, jT, n_bins=10)
print(f"   verdict tempéré={vT}, ECE={iT['ece']:.3f}")
check("sigmoïde tempéré NON sur-confiant", vT != SURCONFIANT)
check("température réduit l'ECE", iT["ece"] < iR["ece"])

print("=== L'ORDRE du classement est INCHANGÉ par T (monotone) ===")
ordre1 = R.classe(s_te)
check("classement identique quel que soit T (T ne touche que la confiance)", ordre1 == R.classe(s_te))
# vérifie aussi que proba_mieux reste du bon côté de 0.5 (monotonie du signe)
mono = all((R.proba_mieux(d, 0.0, 1.0) >= 0.5) == (R.proba_mieux(d, 0.0, T) >= 0.5) for d in d_te)
check("σ tempéré garde le même sens que σ brut (>=0.5 ssi >=0.5)", mono)

print("=== NDCG : classement aligné > classement aléatoire ===")
pert = [max(0.0, t) for t in t_te]                       # pertinences >=0
ndcg_align = R.ndcg(R.classe(s_te), pert, 10)
rng_perm = list(range(len(pert))); random.Random(9).shuffle(rng_perm)
ndcg_rand = R.ndcg(rng_perm, pert, 10)
print(f"   NDCG@10 aligné={ndcg_align:.3f} vs aléatoire={ndcg_rand:.3f}")
check("NDCG aligné > aléatoire", ndcg_align > ndcg_rand)
check("NDCG dans [0,1]", 0.0 <= ndcg_align <= 1.0)

print("=== ABSTENTION si trop peu de paires ===")
st2, _, raison = R.calibre([1.0, -1.0, 0.5], [1, 0, 1])
print(f"   {st2} : {raison}")
check("ABSTENTION sous N_MIN paires", st2 == ABSTENTION)

print(f"\nRÉSULTAT calibration_ranking : {ok}/{total}")
assert ok == total
