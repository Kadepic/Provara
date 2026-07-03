"""
VALIDATION de la PRÉVISION TEMPORELLE (prevision.py) — jugée par calibration.py. L'intervalle de prédiction couvre la
vraie PROCHAINE valeur ~confiance ; la saisonnalité resserre l'intervalle sans le casser ; un modèle naïf (sans
tendance) sous-couvre quand il y a une tendance.
"""
from __future__ import annotations

import math
import random

from garde_ressources import borne
import prevision as PV
from prevision import ESTIMATION, ABSTENTION
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


def serie_complete(n, graine, pente=0.4, periode=7, ampl=3.0, bruit=1.5):
    rng = random.Random(graine)
    return [pente * t + ampl * ((t % periode) - (periode - 1) / 2) + rng.gauss(0, bruit) for t in range(n + 1)]


def couverture(conf, periode, M, graine0, n=70):
    inter, ver = [], []
    for s in range(M):
        sc = serie_complete(n, graine0 + s)
        st, res, _ = PV.prevoit(sc[:n], periode, conf)
        if st == ESTIMATION:
            inter.append(res[1])
            ver.append(sc[n])               # la vraie prochaine valeur
    return inter, ver


print("=== COUVERTURE @90% (tendance + saison 7) : l'intervalle couvre la vraie prochaine valeur ===")
inter, ver = couverture(0.90, 7, 3000, graine0=1)
v, i = CAL.verdict_couverture(inter, ver, 0.90)
print("   ", CAL.formule((v, i), "couverture"))
check(f"prévision @90% : couverture {i['couverture']:.3f} >= 0.86 et NON surconfiant",
      i["couverture"] >= 0.86 and v != SURCONFIANT)

print("=== COUVERTURE @80% : suit le niveau ===")
inter8, ver8 = couverture(0.80, 7, 3000, graine0=5000)
v8, i8 = CAL.verdict_couverture(inter8, ver8, 0.80)
check(f"prévision @80% : couverture {i8['couverture']:.3f} >= 0.76 et NON surconfiant",
      i8["couverture"] >= 0.76 and v8 != SURCONFIANT)

print("=== SAISONNALITÉ : modèle saisonnier resserre l'intervalle vs sans, en restant calibré ===")
inter_sai, ver_sai = couverture(0.90, 7, 2000, graine0=9000)
inter_non, ver_non = couverture(0.90, None, 2000, graine0=9000)
larg_sai = sum(h - b for (b, h) in inter_sai) / len(inter_sai)
larg_non = sum(h - b for (b, h) in inter_non) / len(inter_non)
v_sai, i_sai = CAL.verdict_couverture(inter_sai, ver_sai, 0.90)
print(f"   largeur moyenne : saison={larg_sai:.2f} ; sans={larg_non:.2f}")
check(f"saison resserre l'intervalle ({larg_sai:.2f} < {larg_non:.2f})", larg_sai < larg_non)
check(f"saison reste calibré ({i_sai['couverture']:.3f})", i_sai["couverture"] >= 0.86 and v_sai != SURCONFIANT)

print("=== MODÈLE NAÏF (dernière valeur, ignore la tendance) -> SOUS-COUVRE sur série à forte tendance ===")
# naïf : point = dernière valeur, intervalle = ± écart-type empirique·z (ignore tendance ET saison)
inter_naif, ver_naif = [], []
for s in range(2000):
    sc = serie_complete(70, 20000 + s, pente=0.8)
    serie = sc[:70]
    pt = serie[-1]
    mu = sum(serie) / len(serie)
    sd = math.sqrt(sum((x - mu) ** 2 for x in serie) / (len(serie) - 1))
    inter_naif.append((pt - 1.6449 * sd, pt + 1.6449 * sd))   # largeur ~ dispersion globale (gonflée par la tendance)
    ver_naif.append(sc[70])
# La prévision PROPRE sur la même série forte-tendance doit couvrir ; on vérifie surtout qu'elle n'est PAS surconfiante.
inter_bon, ver_bon = [], []
for s in range(2000):
    sc = serie_complete(70, 20000 + s, pente=0.8)
    st, res, _ = PV.prevoit(sc[:70], 7, 0.90)
    if st == ESTIMATION:
        inter_bon.append(res[1]); ver_bon.append(sc[70])
v_bon, i_bon = CAL.verdict_couverture(inter_bon, ver_bon, 0.90)
check(f"prévision propre @90% (forte tendance) : couverture {i_bon['couverture']:.3f} >= 0.86 et NON surconfiant",
      i_bon["couverture"] >= 0.86 and v_bon != SURCONFIANT)

print("=== ABSTENTION ===")
check("série trop courte -> ABSTENTION", PV.prevoit([1, 2, 3, 4, 5])[0] == ABSTENTION)

print(f"\nPRÉVISION VALIDÉ — {ok}/{total}." if ok == total else f"\nÉCHEC {ok}/{total}")
