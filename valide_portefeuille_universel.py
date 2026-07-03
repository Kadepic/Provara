"""
VALIDATION du PORTEFEUILLE UNIVERSEL (portefeuille_universel.py). Vérifie le pumping de volatilité (CRP rééquilibré >>
actifs purs), la borne de regret de Cover (regret log ≤ (m−1)·ln(n+1)), le regret par période → 0, l'encadrement
worst≤univ≤best, le DÉMASQUE (s'engager sur un actif pur = sur-confiant, battu par le CRP optimal sans garantie),
la validité des poids joués, et l'ABSTENTION. Pur Python (déterministe, pas de MC).
"""
from __future__ import annotations

import math

from garde_ressources import borne
import portefeuille_universel as PU
from portefeuille_universel import ABSTENTION, ANALYSE

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


def pumping(n):
    return [(1.0, 2.0) if t % 2 == 0 else (1.0, 0.5) for t in range(n)]


# ─── 1. Pumping de volatilité : le CRP rééquilibré bat largement les actifs purs ───
print("=== Pumping de volatilité : rééquilibrage > actifs purs ===")
rel = pumping(40)
w_stable = PU.richesse_actif_pur(0, rel)
w_osc = PU.richesse_actif_pur(1, rel)
w_best, b_best = PU.meilleur_crp(rel)
print(f"   actif stable={w_stable:.3f}, oscillant={w_osc:.3f}, meilleur CRP={w_best:.3f} (b*={tuple(round(x,2) for x in b_best)})")
check("les deux actifs purs stagnent (≈1)", abs(w_stable - 1) < 1e-9 and abs(w_osc - 1) < 1e-9)
check("le meilleur CRP rééquilibré croît fortement", w_best > 5)
check("le meilleur CRP est ≈ 50/50", abs(b_best[0] - 0.5) < 0.05)

# ─── 2. Borne de regret de Cover : regret log ≤ (m−1)·ln(n+1) ───
print("=== Borne de regret de Cover ===")
st, info = PU.analyse(rel)
borne_cover = (len(rel[0]) - 1) * math.log(len(rel) + 1)
print(f"   regret log={info['regret']:.3f} ; borne (m−1)·ln(n+1)={borne_cover:.3f}")
check("le regret log respecte la borne de Cover", info["regret"] <= borne_cover + 1e-9)
check("le portefeuille universel capte une part majeure du gain du CRP", info["w_univ"] > 1.5 * w_stable)

# ─── 3. Le regret PAR PÉRIODE tend vers 0 quand n grandit ───
print("=== Regret par période → 0 ===")
r20 = PU.analyse(pumping(20))[1]["regret_par_periode"]
r80 = PU.analyse(pumping(80))[1]["regret_par_periode"]
print(f"   regret/période : n=20 → {r20:.4f} ; n=80 → {r80:.4f}")
check("le regret par période décroît avec n (→ 0)", r80 < r20)

# ─── 4. Encadrement : worst CRP ≤ universel ≤ best CRP ───
print("=== Encadrement worst ≤ univ ≤ best ===")
grille = PU._grille_simplexe(2, 200)
ws = [PU.richesse_crp(b, rel) for b in grille]
w_uni = info["w_univ"]
print(f"   worst CRP={min(ws):.3f} ≤ univ={w_uni:.3f} ≤ best CRP={max(ws):.3f}")
check("la richesse universelle est encadrée par worst et best CRP", min(ws) <= w_uni <= max(ws))

# ─── 5. DÉMASQUE : s'engager sur un actif pur = sur-confiant (pas de garantie) ───
print("=== Mode d'échec : engagement sur un actif pur ===")
# séquence où l'actif 1 (qui 'semblait' bon au début) s'effondre ensuite
adverse = [(1.0, 2.0)] * 5 + [(1.0, 0.4)] * 20
w_pur1 = PU.richesse_actif_pur(1, adverse)
st_a, info_a = PU.analyse(adverse)
print(f"   actif 1 (bon au début puis chute) : richesse {w_pur1:.4f} ; universel {info_a['w_univ']:.3f} ; best CRP {info_a['w_best']:.3f}")
check("l'actif pur 'gagnant initial' s'effondre (sur-confiant)", w_pur1 < 0.1)
check("le portefeuille universel reste proche du meilleur CRP (regret borné)", info_a["regret"] <= (len(adverse[0]) - 1) * math.log(len(adverse) + 1) + 1e-9)
check("le portefeuille universel survit là où l'actif pur ruine", info_a["w_univ"] > 10 * w_pur1)
check("formule signale la sur-confiance du pari a posteriori", "sur-confiant" in PU.formule((st, info)))

# ─── 6. Poids joués valides ───
print("=== Validité des poids joués (simplexe) ===")
poids = PU.poids_universels_suivants(rel)
print(f"   poids suivants = {tuple(round(p,3) for p in poids)} (somme={sum(poids):.6f})")
check("les poids joués sont sur le simplexe (≥0, somme 1)", all(p >= -1e-12 for p in poids) and abs(sum(poids) - 1) < 1e-9)
poids0 = PU.poids_universels_suivants([])
check("sans historique, poids = uniforme (1/m)", all(abs(p - 0.5) < 1e-9 for p in poids0))

# ─── 7. ABSTENTION ───
print("=== ABSTENTION ===")
check("séquence trop courte → ABSTENTION", PU.analyse([(1.0, 1.0)])[0] == ABSTENTION)
check("relatif ≤ 0 → ABSTENTION", PU.analyse([(1.0, 2.0), (1.0, 0.0)])[0] == ABSTENTION)
check("cas valide → ANALYSE", st == ANALYSE)

print(f"\nRÉSULTAT portefeuille_universel : {ok}/{total}")
assert ok == total
