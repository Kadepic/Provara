"""
VALIDATION de l'ANALYSE DE SURVIE (survie.py) — jugée par calibration.py. Sur une loi exponentielle connue avec
censure indépendante : l'IC de Kaplan-Meier (Greenwood/log-log) COUVRE la vraie survie ~confiance, l'estimateur
NAÏF (censuré = événement) est biaisé bas, et la D-calibration distingue le bon modèle du mauvais.
"""
from __future__ import annotations

import math
import random

from garde_ressources import borne
import survie as S
from survie import ESTIMATION, ABSTENTION
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


LAM, MU = 0.5, 0.3      # durée vraie ~Exp(LAM) ; censure ~Exp(MU) indépendante


def echantillon(rng, n):
    temps, evt = [], []
    for _ in range(n):
        tv = -math.log(1 - rng.random()) / LAM
        c = -math.log(1 - rng.random()) / MU
        temps.append(min(tv, c)); evt.append(1 if tv <= c else 0)
    return temps, evt


def vrai_S(t):
    return math.exp(-LAM * t)


print("=== COUVERTURE de l'IC KM (Greenwood/log-log couvre la vraie S(t)) ===")
T = 1.0
vrai = vrai_S(T)
inter, ver = [], []
rng = random.Random(1)
for k in range(300):
    temps, evt = echantillon(rng, 400)
    st, res, _ = S.km_avec_ic(temps, evt, T, 0.90)
    if st == ESTIMATION:
        inter.append(res[1]); ver.append(vrai)
v, i = CAL.verdict_couverture(inter, ver, 0.90)
print(f"   vrai S({T})={vrai:.3f} ; couverture IC={i['couverture']:.3f} sur {len(inter)} jeux")
check(f"KM @t={T} : couverture {i['couverture']:.3f} >= 0.83 et NON surconfiant", i["couverture"] >= 0.83 and v != SURCONFIANT)

print("=== KM SANS BIAIS vs NAÏF biaisé bas (censuré compté comme événement) ===")
rng = random.Random(2)
err_km, err_naif, naif_vals = [], [], []
for k in range(120):
    temps, evt = echantillon(rng, 500)
    km = S.kaplan_meier(temps, evt)
    for t in (0.5, 1.0, 2.0):
        err_km.append(abs(S.survie_a(km, t) - vrai_S(t)))
        naif = S.km_naif_a(temps, evt, t)
        err_naif.append(abs(naif - vrai_S(t)))
        naif_vals.append((naif, vrai_S(t)))
mk, mn = sum(err_km) / len(err_km), sum(err_naif) / len(err_naif)
biais_naif = sum(a - b for a, b in naif_vals) / len(naif_vals)   # naïf − vrai (attendu < 0)
print(f"   |erreur| moyenne : KM={mk:.4f}  naïf={mn:.4f} ; biais naïf moyen={biais_naif:+.3f}")
check("KM nettement plus juste que le naïf (mk < mn/2)", mk < mn / 2)
check("le naïf est SYSTÉMATIQUEMENT biaisé BAS (biais < −0.05)", biais_naif < -0.05)

print("=== D-CALIBRATION : vrai modèle uniforme, modèle FAUX démasqué ===")
rng = random.Random(3)
temps, evt = echantillon(rng, 2000)
_, chi2_vrai = S.d_calibration(temps, evt, lambda t: math.exp(-LAM * t))
_, chi2_faux = S.d_calibration(temps, evt, lambda t: math.exp(-(LAM * 2.2) * t))   # risque sur-estimé
print(f"   chi2 vrai modèle={chi2_vrai:.2f} (df=9, seuil 5%≈16.9) ; chi2 modèle faux={chi2_faux:.2f}")
check("vrai modèle D-calibré (chi2 < 16.9)", chi2_vrai < 16.9)
check("modèle faux démasqué (chi2_faux > 30 et > 3×chi2_vrai)", chi2_faux > 30 and chi2_faux > 3 * chi2_vrai)

print("=== MÉDIANE de survie proche de la vraie ===")
rng = random.Random(4)
meds = []
for k in range(100):
    temps, evt = echantillon(rng, 600)
    m = S.mediane(S.kaplan_meier(temps, evt))
    if m is not None:
        meds.append(m)
med_moy = sum(meds) / len(meds)
vraie_med = math.log(2) / LAM
print(f"   médiane KM moyenne={med_moy:.3f} ; vraie médiane={vraie_med:.3f}")
check("médiane KM ~ vraie médiane (écart < 0.10)", abs(med_moy - vraie_med) < 0.10)

print("=== ABSTENTION honnête sous trop peu d'événements ===")
st, _, raison = S.km_avec_ic([1.0, 2.0, 3.0, 4.0], [1, 0, 1, 0], 1.0, 0.90)
print(f"   {st} : {raison}")
check("ABSTENTION si moins de N_MIN_EVENTS événements", st == ABSTENTION)

print("=== IC se resserre quand n grandit (plus de données = moins d'incertitude) ===")
rng = random.Random(5)
def largeur_moy(n):
    ls = []
    for k in range(40):
        temps, evt = echantillon(rng, n)
        st, res, _ = S.km_avec_ic(temps, evt, 1.0, 0.90)
        if st == ESTIMATION:
            ls.append(res[1][1] - res[1][0])
    return sum(ls) / len(ls)
l_petit, l_grand = largeur_moy(200), largeur_moy(1600)
print(f"   largeur IC : n=200 -> {l_petit:.4f} ; n=1600 -> {l_grand:.4f}")
check("IC plus étroit avec plus de données", l_grand < l_petit * 0.6)

print(f"\nRÉSULTAT survie : {ok}/{total}")
assert ok == total
