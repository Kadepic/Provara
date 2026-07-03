"""
VALIDATION du JUGE D'INCERTITUDE (incertitude.py) — la SOUNDNESS NON-BORNÉE = la CALIBRATION, vérifiée par
SIMULATION (Monte-Carlo). On ne juge pas une estimation unique ; on vérifie qu'un intervalle « à X% » contient
la VRAIE valeur ~X% du temps sur des milliers de tirages d'un monde CONNU. La réalité (simulation) tranche.
+ abstention honnête (petit échantillon), + monotonie (plus de confiance -> intervalle plus large).
"""
from __future__ import annotations

import random

from garde_ressources import borne
from incertitude import (estime_moyenne, estime_proportion, compare_moyennes, predit_intervalle, formule,
                         est_anormal, tendance,
                         ESTIMATION, ABSTENTION, DIFFERENT, INDETERMINE, ANORMAL, NORMAL, HAUSSE, BAISSE, STABLE)

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


def couverture_proportion(p_vrai, n, conf, M, graine):
    rng = random.Random(graine)
    couvre = 0
    for _ in range(M):
        ech = [1 if rng.random() < p_vrai else 0 for _ in range(n)]
        st, res, _ = estime_proportion(ech, conf)
        if st == ESTIMATION and res[1][0] <= p_vrai <= res[1][1]:
            couvre += 1
    return couvre / M


def couverture_moyenne(tirage, mu_vrai, n, conf, M, graine):
    rng = random.Random(graine)
    couvre = 0
    for t in range(M):
        ech = [tirage(rng) for _ in range(n)]
        st, res, _ = estime_moyenne(ech, conf, n_boot=600, seed=t)
        if st == ESTIMATION and res[1][0] <= mu_vrai <= res[1][1]:
            couvre += 1
    return couvre / M


print("=== CALIBRATION PROPORTION (Wilson, n=40, M=1500) ===")
for p in (0.3, 0.5, 0.75):
    cov = couverture_proportion(p, 40, 0.90, 1500, graine=int(p * 1000))
    check(f"proportion p={p} : couverture 90% = {cov:.3f} ∈ [0.85, 0.95]", 0.85 <= cov <= 0.95)

print("=== CALIBRATION MOYENNE (bootstrap, n=40, M=500) ===")
# loi uniforme [0,10] -> vraie moyenne 5 ; loi « exponentielle-like » asymétrique -> vraie moyenne connue.
cov = couverture_moyenne(lambda r: r.uniform(0, 10), 5.0, 40, 0.90, 500, graine=7)
check(f"moyenne uniforme : couverture 90% = {cov:.3f} ∈ [0.83, 0.95]", 0.83 <= cov <= 0.95)
cov80 = couverture_moyenne(lambda r: r.uniform(0, 10), 5.0, 40, 0.80, 500, graine=7)
check(f"moyenne uniforme : couverture 80% = {cov80:.3f} ∈ [0.74, 0.88]", 0.74 <= cov80 <= 0.88)

print("=== ABSTENTION (petit échantillon) ===")
check("n=3 -> abstention (moyenne)", estime_moyenne([1, 2, 3])[0] == ABSTENTION)
check("n=4 -> abstention (proportion)", estime_proportion([1, 0, 1, 1])[0] == ABSTENTION)
check("n=5 -> estimation (moyenne)", estime_moyenne([1, 2, 3, 4, 5])[0] == ESTIMATION)

print("=== MONOTONIE (plus de confiance -> intervalle plus large) ===")
_, (_, (b90, h90)), _ = estime_proportion([1, 0, 1, 1, 0, 1, 1, 0, 1, 1, 1, 0], 0.90)
_, (_, (b99, h99)), _ = estime_proportion([1, 0, 1, 1, 0, 1, 1, 0, 1, 1, 1, 0], 0.99)
check("intervalle 99% plus large que 90% (proportion)", (h99 - b99) > (h90 - b90))
_, (_, (m80b, m80h)), _ = estime_moyenne([2, 4, 6, 8, 10, 3, 5, 7, 9, 1], 0.80, seed=1)
_, (_, (m95b, m95h)), _ = estime_moyenne([2, 4, 6, 8, 10, 3, 5, 7, 9, 1], 0.95, seed=1)
check("intervalle 95% plus large que 80% (moyenne)", (m95h - m95b) >= (m80h - m80b))

print("=== COMPARAISON DE GROUPES — taux de faux positifs CONTRÔLÉ (calibration) ===")
def _taux(tirage_a, tirage_b, n, conf, M, graine):
    rng = random.Random(graine)
    cnt = 0
    for t in range(M):
        a = [tirage_a(rng) for _ in range(n)]
        b = [tirage_b(rng) for _ in range(n)]
        if compare_moyennes(a, b, conf, n_boot=500, seed=t)[0] == DIFFERENT:
            cnt += 1
    return cnt / M

# Sous H0 (A et B MÊME loi) : DIFFERENT = FAUX POSITIF. Doit rester <= ~(1-conf)=0.10 (calibration, tolérance MC).
fpr = _taux(lambda r: r.uniform(0, 10), lambda r: r.uniform(0, 10), 30, 0.90, 600, graine=11)
check(f"H0 (même loi) : taux faux positifs = {fpr:.3f} <= 0.15 (faux positifs contrôlés)", fpr <= 0.15)
# Vraie différence (B décalé de +3) : doit DÉTECTER souvent (puissance) — pas un faux, une vraie capacité.
pui = _taux(lambda r: r.uniform(0, 10), lambda r: r.uniform(3, 13), 30, 0.90, 400, graine=12)
check(f"vraie différence (+3) : puissance = {pui:.3f} >= 0.6 (détecte le réel)", pui >= 0.6)
# verdict honnête + abstention
check("compare petit échantillon -> abstention", compare_moyennes([1, 2], [3, 4])[0] == ABSTENTION)
v = compare_moyennes([1, 2, 3, 4, 5], [10, 11, 12, 13, 14])
check("groupes nettement séparés -> DIFFERENT", v[0] == DIFFERENT)

print("=== INTERVALLE DE PRÉDICTION — couverture de la PROCHAINE observation (calibration) ===")
def couverture_prediction(tirage, n, conf, M, graine):
    rng = random.Random(graine)
    couvre = 0
    for _ in range(M):
        ech = [tirage(rng) for _ in range(n)]
        st, res, _ = predit_intervalle(ech, conf)
        futur = tirage(rng)                      # la PROCHAINE observation (hors échantillon)
        if st == ESTIMATION and res[1][0] <= futur <= res[1][1]:
            couvre += 1
    return couvre / M

covp = couverture_prediction(lambda r: r.uniform(0, 10), 60, 0.90, 2000, graine=21)
check(f"prédiction uniforme : couverture 90% = {covp:.3f} ∈ [0.85, 0.95]", 0.85 <= covp <= 0.95)
covp80 = couverture_prediction(lambda r: r.gauss(5, 2), 60, 0.80, 2000, graine=22)
check(f"prédiction gaussienne : couverture 80% = {covp80:.3f} ∈ [0.74, 0.88]", 0.74 <= covp80 <= 0.88)
check("prédiction petit échantillon -> abstention", predit_intervalle([1, 2, 3])[0] == ABSTENTION)
# l'intervalle de PRÉDICTION est PLUS LARGE que l'IC de la moyenne (porte sur un tirage, pas un paramètre)
ech = [r for r in (2, 4, 6, 8, 10, 1, 3, 5, 7, 9, 0, 11)]
_, (_, (pm_b, pm_h)), _ = estime_moyenne(ech, 0.90, seed=3)
_, (_, (pp_b, pp_h)), _ = predit_intervalle(ech, 0.90)
check("intervalle de prédiction plus large que l'IC de la moyenne", (pp_h - pp_b) > (pm_h - pm_b))

print("=== LA PAROLE DU NON-BORNÉ — phrases honnêtes (jamais de fausse certitude) ===")
ph_moy = formule(estime_moyenne([2, 4, 6, 8, 10, 3, 5, 7]), "moyenne")
print("  ", ph_moy)
check("phrase moyenne : nuancée (« pas sûr ») + bornes", "pas sûr" in ph_moy and "entre" in ph_moy)
ph_abs = formule(estime_moyenne([1, 2, 3]), "moyenne")
check("phrase abstention : « ne pas me prononcer »", "prononcer" in ph_abs)
ph_cmp = formule(compare_moyennes([1, 2, 3, 4, 5], [8, 9, 10, 11, 12]), "comparaison")
print("  ", ph_cmp)
check("phrase comparaison DIFFERENT : « tromper » (risque assumé)", "tromper" in ph_cmp)
ph_ind = formule(compare_moyennes([1, 2, 3, 4, 5], [1, 2, 3, 4, 5]), "comparaison")
check("phrase INDETERMINE : « ne prouve PAS qu'ils sont identiques »", "prouve" in ph_ind.upper() or "prouve" in ph_ind)
ph_pred = formule(predit_intervalle([2, 4, 6, 8, 10, 1, 3, 5, 7, 9]), "prediction")
check("phrase prédiction : « ne peux pas la garantir »", "garantir" in ph_pred)

print("=== DÉTECTION D'ANOMALIE — fausses alertes CONTRÔLÉES ===")
def taux_fausses_alertes(tirage, n, conf, M, graine):
    rng = random.Random(graine)
    fa = 0
    for _ in range(M):
        ech = [tirage(rng) for _ in range(n)]
        v = tirage(rng)                                # valeur de la MÊME loi -> ne devrait PAS être "anormale"
        if est_anormal(v, ech, conf)[0] == ANORMAL:
            fa += 1
    return fa / M
far = taux_fausses_alertes(lambda r: r.gauss(0, 1), 80, 0.95, 2000, graine=31)
check(f"anomalie : fausses alertes @95% = {far:.3f} <= 0.10 (contrôlées)", far <= 0.10)
check("valeur extrême -> ANORMAL", est_anormal(100, [1, 2, 3, 4, 5, 2, 3, 4, 1, 5], 0.90)[0] == ANORMAL)

print("=== DÉTECTION DE TENDANCE — faux positifs sous H0 + puissance ===")
def fpr_tendance(n, conf, M, graine):
    rng = random.Random(graine)
    fp = 0
    for t in range(M):
        serie = [rng.gauss(0, 1) for _ in range(n)]    # H0 : i.i.d., pas de tendance
        if tendance(serie, conf, n_boot=500, seed=t)[0] in (HAUSSE, BAISSE):
            fp += 1
    return fp / M
fpt = fpr_tendance(25, 0.90, 500, graine=41)
check(f"tendance H0 (sans tendance) : faux positifs = {fpt:.3f} <= 0.20", fpt <= 0.20)
# vraie hausse : x croissant + bruit -> HAUSSE souvent (puissance)
rng = random.Random(5)
det = 0
for t in range(300):
    serie = [i * 0.5 + rng.gauss(0, 1) for i in range(25)]
    if tendance(serie, 0.90, n_boot=500, seed=t)[0] == HAUSSE:
        det += 1
check(f"tendance vraie hausse : puissance = {det/300:.3f} >= 0.7", det / 300 >= 0.7)
check("tendance série courte -> abstention", tendance([1, 2, 3])[0] == ABSTENTION)

print("=== PAROLE (anomalie / tendance) ===")
pa = formule(est_anormal(100, [1, 2, 3, 4, 5, 2, 3, 4, 1, 5], 0.90), "anomalie")
print("  ", pa)
check("phrase anomalie : « anormale » + « hasard »", "anormale" in pa and "hasard" in pa)
pt = formule(tendance([1, 2, 3, 4, 5, 6, 7, 8, 9, 10], 0.90), "tendance")
print("  ", pt)
check("phrase tendance : « monte » + « tromper »", "monte" in pt and "tromper" in pt)

print(f"\nINCERTITUDE VALIDÉ — {ok}/{total}." if ok == total else f"\nÉCHEC {ok}/{total}")
