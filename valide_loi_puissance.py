"""
VALIDATION des LOIS À QUEUE LOURDE (loi_puissance.py). Vérifie la queue de Pareto, l'estimateur de Hill (recouvre α),
que l'IC du TCL COUVRE pour α>2 mais SOUS-COUVRE pour α∈(1,2] (sur-confiance démasquée), que la moyenne d'échantillon
CROÎT avec n pour α≤1 (pas de convergence), la logique de verdict, et l'ABSTENTION. Pur Python, rng seedé.
"""
from __future__ import annotations

import math
import random
import statistics

from garde_ressources import borne
import loi_puissance as LP
from loi_puissance import ABSTENTION, ANALYSE

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


rng = random.Random(90)


def echantillon(n, alpha, xmin=1.0):
    return [LP.pareto(rng, xmin, alpha) for _ in range(n)]


# ─── 1. Queue de Pareto : P(X>x) ≈ x^{−α} ───
print("=== Queue de Pareto P(X>x) ≈ (xmin/x)^α ===")
ech = echantillon(50000, 2.0)
for x in (2.0, 5.0, 10.0):
    emp = sum(1 for v in ech if v > x) / len(ech)
    theo = (1.0 / x) ** 2.0
    if x == 5.0:
        print(f"   P(X>{x}) emp={emp:.4f} vs théo={theo:.4f}")
check("queue empirique ≈ théorique (Pareto α=2)", abs(sum(1 for v in ech if v > 5) / len(ech) - (1/5) ** 2) < 0.01)

# ─── 2. Estimateur de Hill recouvre α ───
print("=== Estimateur de Hill ===")
for alpha in (2.5, 1.5, 3.5):
    a = LP.hill(echantillon(8000, alpha))
    print(f"   α={alpha} : Hill α̂={a:.2f}")
    check(f"Hill recouvre α={alpha} (±25%)", abs(a - alpha) < 0.25 * alpha)

# ─── 3. α>2 : IC du TCL couvre ≈ nominal ───
print("=== α>2 (variance finie) : IC du TCL valide ===")
mu = LP.moyenne_theorique(1.0, 3.0)
couvre = sum(1 for _ in range(2000) if (lambda lo, hi: lo <= mu <= hi)(*LP.ic_tcl(echantillon(200, 3.0)))) / 2000
print(f"   couverture IC TCL (α=3) = {couvre:.3f}")
check("α>2 : IC du TCL couvre ≈ 0.95", couvre > 0.9)

# ─── 4. DÉMASQUE : α∈(1,2] → IC du TCL SOUS-COUVRE ───
print("=== Mode d'échec : α∈(1,2] (variance infinie) → IC sous-couvre ===")
mu15 = LP.moyenne_theorique(1.0, 1.5)
couvre15 = sum(1 for _ in range(3000) if (lambda lo, hi: lo <= mu15 <= hi)(*LP.ic_tcl(echantillon(200, 1.5)))) / 3000
print(f"   couverture IC TCL (α=1.5, vraie moyenne {mu15:.1f}) = {couvre15:.3f} (≪ 0.95)")
check("α∈(1,2] : l'IC du TCL SOUS-COUVRE (sur-confiance)", couvre15 < 0.9)
check("couverture nettement pire qu'à α>2", couvre15 < couvre - 0.05)

# ─── 5. α≤1 : la moyenne d'échantillon croît avec n (pas de convergence) ───
print("=== α≤1 (moyenne infinie) : la moyenne croît avec n ===")
# médiane des moyennes d'échantillon (robuste : la MOYENNE des moyennes est elle-même infinie pour α<1).
# La moyenne d'échantillon typique croît en n^(1/α−1) → pour α=0.8, ratio ≈ (n2/n1)^0.25.
def med_moyenne(n, alpha, reps=120):
    return statistics.median(LP.moyenne(echantillon(n, alpha)) for _ in range(reps))
m_petit = med_moyenne(200, 0.8)
m_grand = med_moyenne(20000, 0.8)
print(f"   α=0.8 : médiane des moyennes (n=200)≈{m_petit:.1f} ; (n=20000)≈{m_grand:.1f}")
check("la moyenne d'échantillon (typique) CROÎT avec n (ne converge pas)", m_grand > m_petit * 1.5)

# ─── 6. Logique de verdict ───
print("=== Verdict selon α ===")
st_lourd, info_lourd = LP.analyse(echantillon(3000, 1.5))
st_leger, info_leger = LP.analyse(echantillon(3000, 3.5))
check("α∈(1,2] → variance NON finie, TCL NON fiable", not info_lourd["variance_finie"] and not info_lourd["fiable_tcl"])
check("α>2 → variance finie, TCL fiable", info_leger["variance_finie"] and info_leger["fiable_tcl"])
check("formule signale la sur-confiance pour queue lourde", "SOUS-COUVRE" in LP.formule((st_lourd, info_lourd)))

# ─── 7. ABSTENTION ───
print("=== ABSTENTION ===")
st1, _ = LP.analyse([1.0] * 10)
st2, _ = LP.analyse([-1, -2, 0])
check("< 30 données → ABSTENTION", st1 == ABSTENTION)
check("données non positives → ABSTENTION", st2 == ABSTENTION)
st3, _ = LP.analyse(echantillon(200, 2.5))
check("cas valide → ANALYSE", st3 == ANALYSE)

print(f"\nRÉSULTAT loi_puissance : {ok}/{total}")
assert ok == total
