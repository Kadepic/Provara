"""
VALIDATION de la PRÉDICTION CONFORME (conformal.py) — la garantie de couverture DISTRIBUTION-FREE, prouvée par
Monte-Carlo et JUGÉE par calibration.py. Le cœur : la couverture tient ≥ 1−α SANS hypothèse de loi, là où un
intervalle paramétrique (gaussien) SOUS-COUVRE sur un bruit asymétrique à queue lourde (et est démasqué SURCONFIANT).

Échangeabilité : à chaque essai on tire un jeu de calibration FRAIS + un point test de la MÊME loi (loi log-normale,
fortement asymétrique). On vérifie que l'intervalle conforme couvre la vérité ~(1−α), JAMAIS moins (au pire un peu plus).
"""
from __future__ import annotations

import math
import random

from garde_ressources import borne
import conformal as CF
from conformal import ESTIMATION, ABSTENTION, ENSEMBLE
import calibration as CAL
from calibration import CALIBRE, SURCONFIANT, SOUSCONFIANT

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


def bruit_asymetrique(rng):
    """Loi log-normale recentrée : asymétrique, à queue lourde à droite."""
    return math.exp(rng.gauss(0, 1)) - 1.0


def bruit_lourd(rng):
    """Loi de Student t(df=3) : symétrique mais à queue LOURDE (plus de masse au-delà de ±1.645σ qu'un gaussien
    -> l'intervalle gaussien mean±z·sd SOUS-COUVRE). t = Z / sqrt((g1²+g2²+g3²)/3)."""
    z = rng.gauss(0, 1)
    w = sum(rng.gauss(0, 1) ** 2 for _ in range(3)) / 3.0
    return z / math.sqrt(w)


# ───── RÉGRESSION CONFORME : couverture distribution-free ─────
def couverture_conforme(loi, n_cal, alpha, M, graine):
    """Modèle non biaisé (prédiction 0) ; vérité ~ `loi` ; résidu = vérité. Renvoie (intervalles_conformes, verites)
    avec un point test FRAIS par essai (couverture marginale, échangeabilité respectée)."""
    rng = random.Random(graine)
    ic, ver = [], []
    for _ in range(M):
        residus = [loi(rng) for _ in range(n_cal)]
        st, inter, _ = CF.intervalle_conforme(residus, 0.0, alpha)
        if st != ESTIMATION:
            continue
        ic.append(inter)
        ver.append(loi(rng))
    return ic, ver


print("=== RÉGRESSION CONFORME @90%, DISTRIBUTION-FREE : couvre pour TOUTES les lois ===")
for nom, loi in [("gaussienne", lambda r: r.gauss(0, 1)), ("asymétrique", bruit_asymetrique), ("queue lourde t3", bruit_lourd)]:
    ic, ver = couverture_conforme(loi, 60, 0.10, 3000, graine=abs(hash(nom)) % 1000)
    v, inf = CAL.verdict_couverture(ic, ver, 0.90)
    check(f"conforme @90% ({nom}) : couverture {inf['couverture']:.3f} >= 0.88, NON surconfiant",
          inf["couverture"] >= 0.88 and v != SURCONFIANT)

print("=== CONTRASTE : faire CONFIANCE à un σ ASSUMÉ (au lieu de le MESURER) -> SURCONFIANT ===")
# Réalité : bruit ~ N(0, 3) (sd=3). Le conforme MESURE l'étalement réel des résidus -> couvre. L'analyste « naïf »
# fait confiance au σ=1 SUPPOSÉ par son modèle (erreur de barres d'erreur optimistes) -> intervalle bien trop étroit.
rng = random.Random(31)
ic_c, ig_n, ver = [], [], []
SIGMA_VRAI, SIGMA_ASSUME, Z = 3.0, 1.0, 1.6449
for _ in range(4000):
    residus = [rng.gauss(0, SIGMA_VRAI) for _ in range(80)]
    st, inter, _ = CF.intervalle_conforme(residus, 0.0, 0.10)
    if st != ESTIMATION:
        continue
    ic_c.append(inter)
    ig_n.append((-Z * SIGMA_ASSUME, Z * SIGMA_ASSUME))     # ± z·σ_assumé (le modèle « croit » son bruit à 1)
    ver.append(rng.gauss(0, SIGMA_VRAI))
vc2, infc2 = CAL.verdict_couverture(ic_c, ver, 0.90)
vn2, infn2 = CAL.verdict_couverture(ig_n, ver, 0.90)
print("   conforme (mesure)  :", CAL.formule((vc2, infc2), "couverture"))
print("   naïf (σ assumé)    :", CAL.formule((vn2, infn2), "couverture"))
check(f"conforme @90% (σ mesuré) : couverture {infc2['couverture']:.3f} >= 0.88, NON surconfiant",
      infc2["couverture"] >= 0.88 and vc2 != SURCONFIANT)
check(f"naïf @90% (σ assumé trop petit) : SOUS-COUVRE {infn2['couverture']:.3f} -> SURCONFIANT (barres d'erreur optimistes)",
      vn2 == SURCONFIANT)

print("=== RÉGRESSION CONFORME @80% : couverture suit le niveau ===")
ic80, ver80 = couverture_conforme(bruit_asymetrique, 60, 0.20, 3000, graine=2)
v80, inf80 = CAL.verdict_couverture(ic80, ver80, 0.80)
check(f"conforme @80% : couverture {inf80['couverture']:.3f} >= 0.78 et NON surconfiant",
      inf80["couverture"] >= 0.78 and v80 != SURCONFIANT)

print("=== ABSTENTION : trop peu de calibration pour le niveau demandé ===")
check("n=5, alpha=0.01 (exige n>=99) -> ABSTENTION", CF.intervalle_conforme([1, 2, 3, 4, 5], 0.0, 0.01)[0] == ABSTENTION)
check("n=8, alpha=0.10 (exige n>=9) -> ABSTENTION", CF.intervalle_conforme(list(range(8)), 0.0, 0.10)[0] == ABSTENTION)
check("n=9, alpha=0.10 -> ESTIMATION (juste assez)", CF.intervalle_conforme(list(range(9)), 0.0, 0.10)[0] == ESTIMATION)

print("=== MONOTONIE : plus de confiance -> intervalle plus large ===")
rng = random.Random(3)
res = [abs(rng.gauss(0, 1)) for _ in range(300)]
_, (b90, h90), _ = CF.intervalle_conforme(res, 5.0, 0.10)
_, (b99, h99), _ = CF.intervalle_conforme(res, 5.0, 0.01)
check("intervalle 99% plus large que 90%", (h99 - b99) > (h90 - b90))

# ───── CLASSIFICATION CONFORME : le vrai label est dans l'ensemble >= 1-alpha ─────
def simule_classif(n_cal, alpha, M, graine):
    """Chaque instance : prob de la VRAIE classe ~ U(0.3,0.95), reste réparti sur 2 autres classes. On vérifie
    que le vrai label tombe dans l'ensemble conforme >= 1-alpha, et on note la taille moyenne d'ensemble."""
    rng = random.Random(graine)
    def instance():
        p_vrai = 0.3 + 0.65 * rng.random()
        reste = 1.0 - p_vrai
        a = reste * rng.random()
        return {"vrai": p_vrai, "A": a, "B": reste - a}
    couvre, tailles = 0, 0
    for _ in range(M):
        cal = [instance() for _ in range(n_cal)]
        probas_vrai_cal = [c["vrai"] for c in cal]
        t = instance()
        st, ens, _ = CF.ensemble_conforme(probas_vrai_cal, t, alpha)
        if st != ENSEMBLE:
            continue
        if "vrai" in ens:           # la vraie classe est la clé "vrai"
            couvre += 1
        tailles += len(ens)
    return couvre / M, tailles / M

cov_cls, taille = simule_classif(80, 0.10, 3000, graine=4)
print(f"=== CLASSIFICATION CONFORME @90% : vrai label couvert {cov_cls:.3f}, taille moyenne {taille:.2f} ===")
check(f"classif conforme @90% : couverture du vrai label {cov_cls:.3f} >= 0.88", cov_cls >= 0.88)
check("classif conforme : ensemble informatif (taille moyenne < 3 classes)", taille < 3.0)

print("=== quantile_conforme : propriété de base ===")
scores = list(range(1, 201))
check("quantile croît quand alpha décroît (plus de confiance -> seuil plus haut)",
      CF.quantile_conforme(scores, 0.01) >= CF.quantile_conforme(scores, 0.2))
check("n=10, alpha=0.01 (exige n>=99) -> None (abstention au niveau quantile)",
      CF.quantile_conforme([1, 2, 3, 4, 5, 6, 7, 8, 9, 10], 0.01) is None)

print(f"\nCONFORMAL VALIDÉ — {ok}/{total}." if ok == total else f"\nÉCHEC {ok}/{total}")
