"""
VALIDATION du CONFORME ADAPTATIF (conformal_adaptatif.py) — la couverture tient-elle SOUS DÉRIVE ? Jugé par
calibration.py. Cœur : quand la distribution change dans le temps, le conforme STATIQUE (quantile figé sur le passé)
SOUS-COUVRE le présent (SURCONFIANT), alors que l'ACI ajuste αₜ en ligne et MAINTIENT la couverture visée.
"""
from __future__ import annotations

import random

from garde_ressources import borne
import conformal as CF
import conformal_adaptatif as CA
from conformal_adaptatif import ESTIMATION, ABSTENTION
import calibration as CAL
from calibration import CALIBRE, SURCONFIANT

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


def flux(echelle, n, graine):
    """Flux de (prediction=0, verite) ; `echelle(t, n)` donne l'écart-type du bruit à l'instant t (la dérive)."""
    rng = random.Random(graine)
    return [rng.gauss(0, echelle(t, n)) for t in range(n)]


def evalue(verites, alpha_cible, warmup):
    """Joue le flux ; renvoie (paires_aci, paires_statique) = listes de ((bas,haut), verite) sur t>=warmup.
    STATIQUE = quantile figé sur les `warmup` premiers résidus. ACI = adaptatif en ligne."""
    aci = CA.ConformeAdaptatif(alpha_cible=alpha_cible, gamma=0.05, taille_fenetre=150)
    q0 = None
    paires_aci, paires_stat = [], []
    for t, v in enumerate(verites):
        if t == warmup:
            q0 = CF.quantile_conforme([abs(x) for x in verites[:warmup]], alpha_cible)
        sta = aci.intervalle(0.0)
        if t >= warmup and sta[0] == ESTIMATION and q0 is not None:
            paires_aci.append((sta[1], v))
            paires_stat.append(((-q0, q0), v))
        aci.observe(0.0, v)
    return paires_aci, paires_stat


print("=== STATIONNAIRE (sanité) : ACI couvre la cible ===")
ver = flux(lambda t, n: 1.0, 4000, graine=1)
pa, _ = evalue(ver, 0.10, 300)
inter_a = [p[0] for p in pa]; vt_a = [p[1] for p in pa]
va, ia = CAL.verdict_couverture(inter_a, vt_a, 0.90)
check(f"ACI stationnaire @90% : couverture {ia['couverture']:.3f} -> NON surconfiant", va != SURCONFIANT)

print("=== DÉRIVE (bruit qui ENFLE ×5) : STATIQUE sous-couvre (SURCONFIANT), ACI tient ===")
ver = flux(lambda t, n: 1.0 + 4.0 * t / n, 5000, graine=2)
pa, ps = evalue(ver, 0.10, 300)
inter_a = [p[0] for p in pa]; vt_a = [p[1] for p in pa]
inter_s = [p[0] for p in ps]; vt_s = [p[1] for p in ps]
va, ia = CAL.verdict_couverture(inter_a, vt_a, 0.90)
vs, is_ = CAL.verdict_couverture(inter_s, vt_s, 0.90)
print("   ACI      :", CAL.formule((va, ia), "couverture"))
print("   statique :", CAL.formule((vs, is_), "couverture"))
check(f"ACI sous dérive @90% : couverture {ia['couverture']:.3f} >= 0.86 et NON surconfiant",
      ia["couverture"] >= 0.86 and va != SURCONFIANT)
check(f"STATIQUE sous dérive @90% : SOUS-COUVRE {is_['couverture']:.3f} -> SURCONFIANT (figé sur le passé)",
      vs == SURCONFIANT)

print("=== DÉRIVE BRUSQUE (saut de niveau à mi-parcours) : ACI récupère ===")
ver = flux(lambda t, n: 0.5 if t < n // 2 else 3.0, 5000, graine=3)
pa, ps = evalue(ver, 0.10, 300)
inter_a = [p[0] for p in pa]; vt_a = [p[1] for p in pa]
va, ia = CAL.verdict_couverture(inter_a, vt_a, 0.90)
vs, is_ = CAL.verdict_couverture([p[0] for p in ps], [p[1] for p in ps], 0.90)
check(f"ACI saut @90% : couverture {ia['couverture']:.3f} >= 0.86 et NON surconfiant",
      ia["couverture"] >= 0.86 and va != SURCONFIANT)
check(f"STATIQUE saut @90% : surconfiant ({is_['couverture']:.3f})", vs == SURCONFIANT)

print("=== ABSTENTION : avant le remplissage de la fenêtre ===")
aci = CA.ConformeAdaptatif(alpha_cible=0.10)
check("fenêtre vide -> ABSTENTION", aci.intervalle(0.0)[0] == ABSTENTION)
for _ in range(25):
    aci.observe(0.0, random.Random(9).gauss(0, 1))
check("après remplissage -> ESTIMATION", aci.intervalle(0.0)[0] == ESTIMATION)

print("=== ADAPTATION : une rafale de ratés ÉLARGIT l'intervalle (αₜ baisse) ===")
aci = CA.ConformeAdaptatif(alpha_cible=0.10, gamma=0.1, taille_fenetre=500)
rng = random.Random(4)
for _ in range(300):
    aci.observe(0.0, rng.gauss(0, 1))
larg_avant = aci.intervalle(0.0)[1]
larg_avant = larg_avant[1] - larg_avant[0]
for _ in range(40):
    aci.observe(0.0, 50.0)      # gros ratés répétés
larg_apres = aci.intervalle(0.0)[1]
larg_apres = larg_apres[1] - larg_apres[0]
check(f"intervalle élargi après rafale de ratés ({larg_avant:.2f} -> {larg_apres:.2f})", larg_apres > larg_avant)

print(f"\nCONFORMAL ADAPTATIF VALIDÉ — {ok}/{total}." if ok == total else f"\nÉCHEC {ok}/{total}")
