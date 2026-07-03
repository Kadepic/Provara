"""
VALIDATION de la CONFIDENTIALITÉ DIFFÉRENTIELLE (confidentialite_differentielle.py). Vérifie la borne ε-DP exacte du
Laplace (Δf/b), la garantie empirique (avantage d'un attaquant ≤ (e^ε−1)/(e^ε+1)), le DÉMASQUE (sous-bruiter rend la
perte réelle > ε annoncé → un attaquant distingue mieux que permis = sur-confiance sur la vie privée), le compromis
vie-privée/utilité, la non-biais, la composition, et l'ABSTENTION. Pur Python, léger (pas de lecteur).
"""
from __future__ import annotations

import math
import random

from garde_ressources import borne
import confidentialite_differentielle as DP
from confidentialite_differentielle import ABSTENTION, PRIVE

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


rng = random.Random(75)


def avantage_attaquant(Df, b, N=200000):
    """Avantage empirique d'un attaquant distinguant D (valeur 0) de D' (valeur Δf), seuil à Δf/2."""
    seuil = Df / 2
    pD = sum(1 for _ in range(N) if DP.laplace(rng, b) > seuil) / N            # sous D (vraie valeur 0)
    pDp = sum(1 for _ in range(N) if Df + DP.laplace(rng, b) > seuil) / N      # sous D' (vraie valeur Δf)
    return abs(pDp - pD)


# ─── 1. Borne ε-DP exacte du Laplace : Δf/b ; b=Δf/ε ⇒ ε ───
print("=== Borne ε-DP du Laplace : ratio-log max = Δf/b ===")
exact_ok = True
for _ in range(3000):
    Df = rng.uniform(0.1, 5); eps = rng.uniform(0.1, 3)
    b = DP.echelle_bruit(Df, eps)
    if abs(DP.ratio_log_max(Df, b) - eps) > 1e-9 or abs(DP.perte_confidentialite(Df, b) - eps) > 1e-9:
        exact_ok = False
check("b=Δf/ε ⇒ perte de confidentialité = ε (exact)", exact_ok)

# ─── 2. Garantie empirique : avantage ≤ (e^ε−1)/(e^ε+1) ───
print("=== Garantie empirique : avantage de l'attaquant ≤ borne DP ===")
Df = 1.0
for eps in (0.5, 1.0, 2.0):
    b = DP.echelle_bruit(Df, eps)
    adv = avantage_attaquant(Df, b)
    bound = DP.borne_avantage(eps)
    print(f"   ε={eps}: avantage={adv:.3f} ≤ borne {bound:.3f}")
    check(f"avantage ≤ (e^ε−1)/(e^ε+1) (ε={eps})", adv <= bound + 0.02)

# ─── 3. DÉMASQUE : sous-bruiter = sur-confiance (avantage dépasse la borne ANNONCÉE) ───
print("=== Mode d'échec : sous-bruité, on annonce ε mais on offre moins ===")
eps_annonce = 0.5
b_faible = 0.25                                    # b ≪ Δf/ε = 2.0
res = DP.analyse(Df, eps_annonce, b=b_faible)[1]
adv_faible = avantage_attaquant(Df, b_faible)
bound_annonce = DP.borne_avantage(eps_annonce)
print(f"   b={b_faible} : ε_réel={res['epsilon_reel']:.1f} (annoncé {eps_annonce}) ; avantage={adv_faible:.3f} > borne annoncée {bound_annonce:.3f}")
check("sous-bruité : perte réelle ≫ ε annoncé (non conforme)", res["epsilon_reel"] > eps_annonce and not res["conforme"])
check("l'attaquant distingue MIEUX que ce que ε annoncé permet (sur-confiance démasquée)", adv_faible > bound_annonce)
# bien bruité = conforme
check("bien bruité (b=Δf/ε) → conforme", DP.analyse(Df, eps_annonce)[1]["conforme"])

# ─── 4. Compromis vie-privée / utilité ───
print("=== Compromis : ε petit ⇒ plus de bruit ⇒ moins d'utilité ===")
def erreur_type(eps, reps=20000):
    b = DP.echelle_bruit(1.0, eps)
    return (sum(DP.laplace(rng, b) ** 2 for _ in range(reps)) / reps) ** 0.5
e_petit, e_grand = erreur_type(0.2), erreur_type(5.0)
print(f"   erreur-type : ε=0.2 → {e_petit:.2f} ; ε=5 → {e_grand:.2f}")
check("ε plus petit ⇒ plus d'erreur (moins d'utilité)", e_petit > e_grand)

# ─── 5. Non-biais : E[M(D)] = f(D) ───
print("=== Mécanisme non biaisé ===")
moy = sum(DP.mecanisme(rng, 7.0, 1.0, 1.0) for _ in range(40000)) / 40000
check("E[M(D)] ≈ f(D) (bruit centré)", abs(moy - 7.0) < 0.05)

# ─── 6. Composition : K requêtes ε → Kε (la fuite s'additionne) ───
print("=== Composition basique : Σε_i ===")
check("composition de [0.5,0.5,0.5] = 1.5", abs(DP.composition([0.5, 0.5, 0.5]) - 1.5) < 1e-12)
# l'avantage cumulé croît avec le nombre de requêtes (plus de fuite)
adv1 = avantage_attaquant(1.0, DP.echelle_bruit(1.0, 0.5))
# 3 requêtes indépendantes : un attaquant combine -> distingue mieux (proxy : moyenne de 3 bruits réduit l'écart-type relatif)
def avantage_k(Df, b, k, N=60000):
    seuil = Df / 2
    cD = sum(1 for _ in range(N) if (sum(DP.laplace(rng, b) for _ in range(k)) / k) > seuil) / N
    cDp = sum(1 for _ in range(N) if (Df + sum(DP.laplace(rng, b) for _ in range(k)) / k) > seuil) / N
    return abs(cDp - cD)
a1 = avantage_k(1.0, 2.0, 1); a5 = avantage_k(1.0, 2.0, 5)
print(f"   avantage avec 1 requête={a1:.3f} ; en moyennant 5 requêtes={a5:.3f} (la fuite cumulée augmente)")
check("répéter les requêtes augmente l'avantage de l'attaquant (composition réelle)", a5 > a1 + 0.02)

# ─── 7. ABSTENTION ───
print("=== ABSTENTION ===")
st1, _ = DP.analyse(1.0, 0.0)
st2, _ = DP.analyse(-1.0, 1.0)
check("ε≤0 → ABSTENTION", st1 == ABSTENTION)
check("Δf<0 → ABSTENTION", st2 == ABSTENTION)
st3, _ = DP.analyse(1.0, 0.5)
check("cas valide → PRIVE", st3 == PRIVE)

print(f"\nRÉSULTAT confidentialite_differentielle : {ok}/{total}")
assert ok == total
