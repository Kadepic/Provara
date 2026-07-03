"""
VALIDATION du P-HACKING (p_hacking.py). Vérifie : la distribution du min-p (Beta(1,m), moyenne 1/(m+1)) et sa CDF
fermée ; le FPR NAÏF d'une sélection ≫ α (mesuré par simulation sous H0) ; l'ajustement sélectif Šidák qui ramène le
Type-I ≈ α (calibré) ; Bonferroni ≥ Šidák ≥ p brut ; la PUISSANCE préservée pour un vrai effet fort ; l'ABSTENTION.
Pur Python, rng seedé.
"""
from __future__ import annotations

import statistics
import random

from garde_ressources import borne
import p_hacking as PH
from p_hacking import ABSTENTION, ANALYSE

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


rng = random.Random(98)
m, alpha = 20, 0.05
REPS = 4000


def tirage_h0(m):
    """m p-values sous H0 globale (stat z ~ N(0,1) → p bilatérale uniforme)."""
    return [PH.p_bilateral(rng.gauss(0, 1)) for _ in range(m)]


# ─── 1. CDF fermée du min-p = 1−(1−t)^m, et FPR naïf ≫ α ───
print("=== Distribution du gagnant (min-p) ===")
mins = [min(tirage_h0(m)) for _ in range(REPS)]
emp_inf_alpha = sum(1 for x in mins if x <= alpha) / REPS
theo = PH.cdf_p_min(alpha, m)
print(f"   P(min-p ≤ α) empirique={emp_inf_alpha:.3f} ; fermée 1−(1−α)^m={theo:.3f} ; α={alpha}")
check("la CDF fermée du min-p colle à l'empirique", abs(emp_inf_alpha - theo) < 0.03)
check("le FPR naïf d'une sélection est très supérieur à α", theo > 10 * alpha)
check("prob_au_moins_un_significatif = la CDF du min en α", abs(PH.prob_au_moins_un_significatif(m, alpha) - theo) < 1e-12)

# ─── 2. min-p ~ Beta(1,m) : moyenne ≈ 1/(m+1) ───
print("=== min-p ~ Beta(1,m) ===")
moy = statistics.mean(mins)
print(f"   E[min-p] empirique={moy:.4f} ; théorique 1/(m+1)={1/(m+1):.4f}")
check("la moyenne du min-p ≈ 1/(m+1) (Beta(1,m))", abs(moy - 1 / (m + 1)) < 0.01)

# ─── 3. Type-I NAÏF ≫ α vs Type-I AJUSTÉ (Šidák) ≈ α ───
print("=== Type-I : naïf ≫ α ; ajusté Šidák ≈ α ===")
naif = aj = 0
for _ in range(REPS):
    ps = tirage_h0(m)
    res = PH.analyse(ps, alpha)[1]
    naif += res["significatif_naif"]
    aj += res["significatif_ajuste"]
t_naif, t_aj = naif / REPS, aj / REPS
print(f"   Type-I naïf={t_naif:.3f} (≈0.64 attendu) ; ajusté Šidák={t_aj:.3f} (≈α={alpha})")
check("le Type-I naïf (p brut du gagnant) explose bien au-dessus de α", t_naif > 0.5)
check("l'ajustement sélectif Šidák ramène le Type-I ≈ α (calibré)", abs(t_aj - alpha) < 0.02)

# ─── 4. Ordre des p ajustés : Bonferroni ≥ Šidák ≥ p brut ───
print("=== Bonferroni ≥ Šidák ≥ p brut ===")
p_min = 0.01
ps_b, ps_s = PH.p_ajuste_bonferroni(p_min, m), PH.p_ajuste_sidak(p_min, m)
print(f"   p_min={p_min} → Šidák={ps_s:.4f}, Bonferroni={ps_b:.4f}")
check("Bonferroni est plus conservateur (≥) que Šidák", ps_b >= ps_s - 1e-12)
check("les deux ajustements gonflent le p brut (plus honnêtes)", ps_s >= p_min and ps_b >= p_min)

# ─── 5. PUISSANCE préservée : un vrai effet FORT reste significatif après ajustement ───
print("=== Puissance : un vrai effet fort survit à l'ajustement ===")
detecte = 0
ESSAIS = 1000
for _ in range(ESSAIS):
    ps = tirage_h0(m - 1)
    ps.append(PH.p_bilateral(rng.gauss(5.0, 1)))           # un chemin avec effet réel fort (z≈5)
    detecte += PH.analyse(ps, alpha)[1]["significatif_ajuste"]
taux = detecte / ESSAIS
print(f"   puissance ajustée sur effet fort (z≈5) = {taux:.3f}")
check("l'ajustement sélectif conserve la puissance sur un vrai effet fort", taux > 0.9)

# ─── 6. ABSTENTION ───
print("=== ABSTENTION ===")
check("< 2 p-values → ABSTENTION", PH.analyse([0.04], alpha)[0] == ABSTENTION)
check("p hors [0,1] → ABSTENTION", PH.analyse([0.04, 1.3], alpha)[0] == ABSTENTION)
st, info = PH.analyse(tirage_h0(m), alpha)
check("cas valide → ANALYSE", st == ANALYSE)
check("formule signale la sur-confiance du p brut du gagnant", "sur-confiant" in PH.formule((st, info)))

print(f"\nRÉSULTAT p_hacking : {ok}/{total}")
assert ok == total
