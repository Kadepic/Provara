"""
VALIDATION de la DÉCISION INFO-GAP (info_gap.py). Vérifie : la robustesse α̂ est une GARANTIE EXACTE (∀u∈U(α̂),
récompense ≥ r_c : 0 violation, et rupture juste au-delà), le RENVERSEMENT de préférence (la meilleure perf nominale
n'est pas la plus robuste), le CROISEMENT des courbes α̂(r_c) (classement dépend de r_c), et DÉMASQUE le mode
d'échec : déployer la décision de meilleure performance nominale est SUR-CONFIANT (elle casse l'exigence sous une
déviation de modèle qu'une décision plus robuste absorbe). Pur Python, léger (pas de lecteur).
"""
from __future__ import annotations

import random

from garde_ressources import borne
import info_gap as IG
from info_gap import ROBUSTE, ABSTENTION

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


R_A = lambda u: 100 * u           # agressif, meilleur nominal (=100), fragile
R_B = lambda u: 40 + 30 * u       # conservateur, plancher (=70 nominal), robuste
U = 1.0

# ─── 1. α̂ correspond à la forme close (à la résolution de grille près) ───
print("=== α̂ vs forme close ===")
aA = IG.robustesse(R_A, U, 50.0)   # 100(1-α)≥50 -> 0.5
aB = IG.robustesse(R_B, U, 50.0)   # 70-30α≥50 -> 2/3
print(f"   α̂_A(50)={aA:.4f} (exact 0.5) ; α̂_B(50)={aB:.4f} (exact 0.6667)")
check("α̂_A(50) ≈ 0.5", abs(aA - 0.5) < 6e-3)
check("α̂_B(50) ≈ 0.6667", abs(aB - 2/3) < 6e-3)
check("α̂ est conservateur (≤ valeur exacte, jamais au-dessus)", aA <= 0.5 + 1e-9 and aB <= 2/3 + 1e-9)

# ─── 2. GARANTIE EXACTE : ∀u∈U(α̂), récompense ≥ r_c (0 violation) + rupture au-delà ───
print("=== Garantie exacte de robustesse ===")
rng = random.Random(53)
viol = 0
for _ in range(20000):
    u = rng.uniform(U - aB, U + aB)
    if R_B(u) < 50.0 - 1e-9:
        viol += 1
check("∀u∈U(α̂_B), R_B(u) ≥ r_c (0 violation / 20000)", viol == 0)
pire_au_dela = IG.pire_cas(R_B, U, aB + 0.05)
print(f"   pire-cas à α̂+0.05 = {pire_au_dela:.3f} (< 50 attendu)")
check("juste au-delà de α̂, le pire-cas CASSE r_c (tightness)", pire_au_dela < 50.0)

# ─── 3. Renversement de préférence : meilleur nominal ≠ plus robuste ───
print("=== Renversement de préférence (nominal vs robuste) ===")
st, gagnant, table = IG.choisis({"A": R_A, "B": R_B}, U, 50.0)
nominal_best = max(table, key=lambda n: table[n][1])
print(f"   nominal le meilleur = {nominal_best} (={table[nominal_best][1]:g}) ; plus robuste @r_c=50 = {gagnant}")
check("la meilleure perf nominale est A", nominal_best == "A")
check("la décision la plus robuste @r_c=50 est B (≠ nominal)", st == ROBUSTE and gagnant == "B")

# ─── 4. Croisement : le classement dépend de r_c ───
print("=== Croisement des courbes α̂(r_c) ===")
aA65 = IG.robustesse(R_A, U, 65.0)   # 0.35
aB65 = IG.robustesse(R_B, U, 65.0)   # 0.1667
print(f"   r_c=65 : α̂_A={aA65:.3f} > α̂_B={aB65:.3f} (A redevient le plus robuste)")
check("à r_c=50 : B plus robuste que A", aB > aA)
check("à r_c=65 : A plus robuste que B (croisement)", aA65 > aB65)

# ─── 5. DÉMASQUE : déployer le nominal-optimal (A) est SUR-CONFIANT ───
print("=== Mode d'échec : le nominal-optimal casse sous une déviation que le robuste absorbe ===")
alpha_vrai = 0.60   # déviation réelle (inconnue a priori), entre α̂_A(0.5) et α̂_B(0.667)
pireA = IG.pire_cas(R_A, U, alpha_vrai)
pireB = IG.pire_cas(R_B, U, alpha_vrai)
print(f"   horizon réel α={alpha_vrai} : pire-cas A={pireA:.1f}  B={pireB:.1f}  (exigence r_c=50)")
check("nominal-optimal A ÉCHOUE r_c sous α réel (sur-confiance démasquée)", pireA < 50.0)
check("robuste B TIENT r_c sous le même α réel", pireB >= 50.0)
# le choix info-gap (B) aurait évité l'échec
check("le choix info-gap (B) garantissait r_c jusqu'à α̂_B > α réel", aB > alpha_vrai)

# ─── 6. α̂ non-croissant en r_c (plus on exige, moins on est immunisé) ───
print("=== α̂ décroît avec l'exigence r_c ===")
seq = [IG.robustesse(R_B, U, rc) for rc in (40, 50, 60, 69)]
print(f"   α̂_B pour r_c=40,50,60,69 : {[round(x,3) for x in seq]}")
check("α̂(r_c) non-croissant", all(seq[i] >= seq[i+1] - 1e-9 for i in range(len(seq)-1)))
check("α̂=0 quand r_c > récompense nominale (B, r_c=80>70)", IG.robustesse(R_B, U, 80.0) == 0.0)

# ─── 7. Opportunité β̂ : compromis inverse (A plus opportun) ───
print("=== Opportunité (windfall) : compromis inverse ===")
bA = IG.opportunite(R_A, U, 120.0)   # 100(1+β)≥120 -> 0.2
bB = IG.opportunite(R_B, U, 120.0)   # 70+30β≥120 -> 1.667
print(f"   β̂_A(120)={bA:.4f} (exact 0.2) ; β̂_B(120)={bB:.4f}")
check("β̂_A(120) ≈ 0.2", abs(bA - 0.2) < 6e-3)
check("A plus OPPORTUN que B (β̂ plus petit) — il achète l'opportunité contre la robustesse", bA < bB)

# ─── 8. ABSTENTION quand aucune décision ne garantit r_c même au nominal ───
print("=== ABSTENTION si incertitude trop sévère (nominal échoue) ===")
st2, g2, _ = IG.choisis({"A": R_A, "B": R_B}, U, 200.0)
print(f"   r_c=200 -> {st2}")
check("r_c au-dessus de tous les nominaux → ABSTENTION", st2 == ABSTENTION and g2 is None)

print(f"\nRÉSULTAT info_gap : {ok}/{total}")
assert ok == total
