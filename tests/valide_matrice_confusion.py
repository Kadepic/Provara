"""
VALIDATION de la MATRICE DE CONFUSION & TAUX DE BASE (matrice_confusion.py). Vérifie les comptes de confusion, le
PARADOXE DE L'EXACTITUDE (classifieur majoritaire = haute exactitude mais rappel/MCC nuls = sur-confiance démasquée),
la NÉGLIGENCE DU TAUX DE BASE (PPV ≪ fiabilité du test à faible prévalence), que l'exactitude équilibrée/MCC sont
honnêtes, les bornes des métriques, un bon classifieur, et l'ABSTENTION. Pur Python, léger.
"""
from __future__ import annotations

import random

from garde_ressources import borne
import matrice_confusion as MC
from matrice_confusion import ABSTENTION, METRIQUES

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


rng = random.Random(84)

# ─── 1. Comptes de confusion ───
print("=== Comptes de confusion ===")
yv = [1, 1, 0, 0, 1, 0]; yp = [1, 0, 0, 1, 1, 0]
TP, FP, TN, FN = MC.confusion(yv, yp)
check("TP+FP+TN+FN = n", TP + FP + TN + FN == len(yv))
check("TP=2, FP=1, TN=2, FN=1", (TP, FP, TN, FN) == (2, 1, 2, 1))

# ─── 2. PARADOXE DE L'EXACTITUDE : majoritaire = haute exactitude, inutile ───
print("=== Paradoxe de l'exactitude (déséquilibre) ===")
yv = [1] * 20 + [0] * 980          # 2% positifs
yp = [0] * 1000                    # toujours négatif
info = MC.analyse(yv, yp)[1]
print(f"   majoritaire : exactitude={info['exactitude']:.3f} ; rappel={info['rappel']:.3f} ; exact_équil={info['exactitude_equilibree']:.3f} ; MCC={info['mcc']:.3f}")
check("exactitude TRÈS haute (> 0.95)", info["exactitude"] > 0.95)
check("rappel nul (ne détecte aucun positif)", info["rappel"] == 0.0)
check("exactitude équilibrée = 0.5 (inutile)", abs(info["exactitude_equilibree"] - 0.5) < 1e-9)
check("MCC = 0 (aucune valeur, sur-confiance démasquée)", abs(info["mcc"]) < 1e-9)

# ─── 3. NÉGLIGENCE DU TAUX DE BASE ───
print("=== Négligence du taux de base (PPV vs fiabilité) ===")
ppv_rare = MC.ppv_bayes(0.95, 0.95, 0.01)
ppv_freq = MC.ppv_bayes(0.95, 0.95, 0.30)
print(f"   PPV : prévalence 1% → {ppv_rare:.3f} ; 30% → {ppv_freq:.3f} (fiabilité test = 0.95)")
check("PPV ≪ fiabilité du test à faible prévalence (≈0.16 pour 1%)", ppv_rare < 0.25)
check("PPV croît avec la prévalence", ppv_freq > ppv_rare)
check("PPV ≤ 1 et > 0", 0 < ppv_rare < 1)
# monotonie complète
ppvs = [MC.ppv_bayes(0.95, 0.95, pr) for pr in (0.01, 0.05, 0.2, 0.5)]
check("PPV monotone croissant en prévalence", all(ppvs[i] <= ppvs[i+1] + 1e-12 for i in range(len(ppvs)-1)))

# ─── 4. Métriques honnêtes : bon classifieur vs aléatoire ───
print("=== Métriques honnêtes : bon vs aléatoire ===")
# bon classifieur sur données déséquilibrées (détecte bien les positifs)
yv2 = [1] * 100 + [0] * 900
yp2 = [1] * 90 + [0] * 10 + [1] * 30 + [0] * 870   # 90/100 positifs détectés, 30 faux positifs
info2 = MC.analyse(yv2, yp2)[1]
print(f"   bon classifieur : rappel={info2['rappel']:.2f}, précision={info2['precision']:.2f}, MCC={info2['mcc']:.2f}, exact_équil={info2['exactitude_equilibree']:.2f}")
check("bon classifieur : exactitude équilibrée élevée (> 0.85)", info2["exactitude_equilibree"] > 0.85)
check("bon classifieur : MCC élevé (> 0.6)", info2["mcc"] > 0.6)
# parfait -> MCC=1 ; inversé -> MCC=-1
check("classifieur parfait → MCC = 1", abs(MC.mcc([1, 0, 1, 0], [1, 0, 1, 0]) - 1) < 1e-9)
check("classifieur inversé → MCC = −1", abs(MC.mcc([1, 0, 1, 0], [0, 1, 0, 1]) + 1) < 1e-9)

# ─── 5. Bornes des métriques ───
print("=== Bornes des métriques ∈ [0,1] (MCC ∈ [−1,1]) ===")
bornes_ok = True
for _ in range(2000):
    n = rng.randint(5, 40)
    a = [rng.randint(0, 1) for _ in range(n)]; b = [rng.randint(0, 1) for _ in range(n)]
    if not (0 <= MC.exactitude(a, b) <= 1 and 0 <= MC.precision(a, b) <= 1 and 0 <= MC.rappel(a, b) <= 1
            and -1 - 1e-9 <= MC.mcc(a, b) <= 1 + 1e-9):
        bornes_ok = False; break
check("toutes les métriques dans leurs bornes", bornes_ok)

# ─── 6. ABSTENTION ───
print("=== ABSTENTION ===")
st1, _ = MC.analyse([], [])
st2, _ = MC.analyse([1, 0], [1])
check("données vides → ABSTENTION", st1 == ABSTENTION)
check("tailles différentes → ABSTENTION", st2 == ABSTENTION)
st3, _ = MC.analyse([1, 0, 1], [1, 0, 0])
check("cas valide → METRIQUES", st3 == METRIQUES)

print(f"\nRÉSULTAT matrice_confusion : {ok}/{total}")
assert ok == total
