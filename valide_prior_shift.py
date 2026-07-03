"""
VALIDATION de la CORRECTION DE PRIOR / LABEL SHIFT (prior_shift.py) — jugée par calibration.py. Classifieur calibré au
prior d'entraînement 0.5, déployé sur une cible où le positif est RARE (0.1) : les posteriors NAÏFS sont SUR-CONFIANTS
sur la cible, la correction de Saerens (avec π_cible estimé par EM SANS étiquettes) les recalibre. Si les priors sont
égaux, la correction est l'identité (aucun prix). L'EM recouvre la vraie prévalence cible.
"""
from __future__ import annotations

import math
import random

from garde_ressources import borne
import prior_shift as PS
from prior_shift import ESTIMATION, ABSTENTION
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


PI_TRAIN = [0.5, 0.5]
MU1 = 1.5


def p_train_de_score(s):
    L = math.exp(-((s - MU1) ** 2) / 2) / math.exp(-(s ** 2) / 2)
    p1 = PI_TRAIN[1] * L / (PI_TRAIN[1] * L + PI_TRAIN[0])
    return [1 - p1, p1]


def echantillon_cible(rng, n, prevalence):
    posts, labels = [], []
    for _ in range(n):
        y = 1 if rng.random() < prevalence else 0
        s = rng.gauss(MU1 if y else 0.0, 1.0)
        posts.append(p_train_de_score(s)); labels.append(y)
    return posts, labels


def prob_outcome(posts, labels):
    """Calibration de la PROBABILITÉ de la classe positive (forecast p1 vs issue y) — c'est là que le label shift frappe
    (le max-confiance moyenne les deux classes et masque le défaut, conditionnel à la classe)."""
    return [p[1] for p in posts], [float(y) for y in labels]


PREV = 0.10
rng = random.Random(3)
posts, labels = echantillon_cible(rng, 5000, PREV)

print(f"=== EM recouvre la prévalence cible (vraie = {PREV}) ===")
pi_em = PS.estime_prior_cible(posts, PI_TRAIN)
print(f"   π_cible estimé = {[round(x,3) for x in pi_em]}")
check("EM recouvre π_cible (|π1−0.10|<0.03)", abs(pi_em[1] - PREV) < 0.03)

print("=== Proba positive NAÏVE sur la cible : SUR-CONFIANTE ===")
cN, jN = prob_outcome(posts, labels)
vN, iN = CAL.est_calibre(cN, jN, n_bins=12)
print(f"   verdict naïf={vN}, ECE={iN['ece']:.3f}, écart signé={iN['ecart_signe']:.3f}")
check("proba positive naïve SUR-CONFIANTE sur la cible", vN == SURCONFIANT)

print("=== Proba positive CORRIGÉE (Saerens, π_cible par EM) : CALIBRÉE ===")
_, info, _ = PS.adapte(posts, PI_TRAIN)              # π_cible estimé par EM
cC, jC = prob_outcome(info["posteriors"], labels)
vC, iC = CAL.est_calibre(cC, jC, n_bins=12)
print(f"   verdict corrigé={vC}, ECE={iC['ece']:.3f}, écart signé={iC['ecart_signe']:.3f}")
check("posteriors corrigés NON sur-confiants", vC != SURCONFIANT)
check("la correction réduit l'ECE", iC["ece"] < iN["ece"])

print("=== Côté classe RARE (prédits positifs) : le naïf sur-promet, le corrigé non ===")
# parmi les points où le naïf prédit positif, taux réel de positifs vs confiance moyenne
idx_pos = [i for i in range(len(posts)) if posts[i][1] > posts[i][0]]
if idx_pos:
    conf_moy = sum(posts[i][1] for i in idx_pos) / len(idx_pos)
    taux_reel = sum(labels[i] for i in idx_pos) / len(idx_pos)
    print(f"   naïf prédit positif : confiance moyenne={conf_moy:.3f} vs taux réel={taux_reel:.3f}")
    check("naïf sur-promet sur les prédictions positives (confiance > taux réel + 0.05)", conf_moy > taux_reel + 0.05)
else:
    check("(pas de prédiction positive — ignoré)", True)

print("=== Priors ÉGAUX (π_cible = π_train) : la correction est l'IDENTITÉ EXACTE (aucun prix) ===")
rng2 = random.Random(7)
posts2, _ = echantillon_cible(rng2, 2000, 0.5)
ident = all(abs(PS.corrige_posterior(p, PI_TRAIN, PI_TRAIN)[1] - p[1]) < 1e-9 for p in posts2)
check("correction = identité exacte quand π_cible = π_train", ident)
pi_em2 = PS.estime_prior_cible(posts2, PI_TRAIN)
print(f"   π estimé sous priors égaux = {[round(x,3) for x in pi_em2]} (EM ~ 0.5, bruit d'échantillon)")
check("EM ~ prior train quand pas de shift (|π1−0.5|<0.06)", abs(pi_em2[1] - 0.5) < 0.06)

print("=== ABSTENTION si trop peu de données cibles pour l'EM ===")
st, _, raison = PS.adapte([[0.4, 0.6], [0.7, 0.3]], PI_TRAIN)
print(f"   {st} : {raison}")
check("ABSTENTION sous N_MIN sans prior_cible fourni", st == ABSTENTION)

print(f"\nRÉSULTAT prior_shift : {ok}/{total}")
assert ok == total
