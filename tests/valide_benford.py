"""
VALIDATION de la LOI DE BENFORD (benford.py). Vérifie les probabilités de Benford, la forme close du χ² à 8 ddl, que
des données naturelles (invariantes d'échelle) CONFORMENT (type I ≈ α), que des données FABRIQUÉES (chiffres uniformes)
sont DÉTECTÉES, le double démasque (anomalie ≠ preuve de fraude : la réserve est rapportée), le premier chiffre, et
l'ABSTENTION. Pur Python, léger.
"""
from __future__ import annotations

import math
import random

from garde_ressources import borne
import benford as BF
from benford import ABSTENTION, TEST

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


rng = random.Random(88)

# ─── 1. Probabilités de Benford ───
print("=== Probabilités de Benford ===")
check("P(1) ≈ 0.301", abs(BF.proba_benford(1) - 0.30103) < 1e-4)
check("P(9) ≈ 0.046", abs(BF.proba_benford(9) - 0.0458) < 1e-3)
check("somme = 1", abs(sum(BF.proba_benford(d) for d in range(1, 10)) - 1) < 1e-9)
check("décroissant (P(1) > P(2) > … > P(9))", all(BF.proba_benford(d) > BF.proba_benford(d + 1) for d in range(1, 9)))

# ─── 2. Premier chiffre ───
print("=== Premier chiffre ===")
check("premier_chiffre(0.0042)=4", BF.premier_chiffre(0.0042) == 4)
check("premier_chiffre(98765)=9", BF.premier_chiffre(98765) == 9)
check("premier_chiffre(−317)=3", BF.premier_chiffre(-317) == 3)

# ─── 3. Forme close du χ² à 8 ddl ───
print("=== χ²(8 ddl) : forme close ===")
print(f"   P(χ²>15.507) = {BF._chi2_sf_df8(15.507):.4f} (≈ 0.05)")
check("P(χ²>15.507, df=8) ≈ 0.05", abs(BF._chi2_sf_df8(15.507) - 0.05) < 0.005)
check("P(χ²>0) = 1 ; P(χ² grand) → 0", abs(BF._chi2_sf_df8(0) - 1) < 1e-9 and BF._chi2_sf_df8(100) < 1e-6)

# ─── 4. Données naturelles → conformes (type I ≈ α) ───
print("=== Données naturelles (invariantes d'échelle) → conformes ===")
rejets = 0; N = 400
for _ in range(N):
    nat = [10 ** rng.uniform(0, 6) for _ in range(300)]
    if not BF.analyse(nat)[1]["conforme"]:
        rejets += 1
print(f"   taux de rejet (faux positif) = {rejets/N:.3f} (≈ α=0.05)")
check("données Benford : type I ≈ α (peu de faux positifs)", rejets / N < 0.1)

# ─── 5. Données FABRIQUÉES → détectées ───
print("=== Données fabriquées (chiffres uniformes) → détectées ===")
det = 0
for _ in range(200):
    fab = [rng.randint(1, 9) * 10 ** rng.randint(0, 5) for _ in range(300)]
    if not BF.analyse(fab)[1]["conforme"]:
        det += 1
print(f"   puissance (détection de fabrication) = {det/200:.3f}")
check("données fabriquées détectées (puissance > 0.9)", det / 200 > 0.9)

# ─── 6. Double démasque : anomalie ≠ preuve de fraude (réserve rapportée) ───
print("=== Réserve : anomalie ≠ preuve de fraude ===")
fab = [rng.randint(1, 9) * 10 ** rng.randint(0, 5) for _ in range(300)]
msg = BF.formule(BF.analyse(fab))
check("la formule signale l'ANOMALIE", "ANOMALIE" in msg)
check("la formule précise que ce n'est PAS une preuve de fraude (réserve)", "PAS une preuve" in msg)

# ─── 7. ABSTENTION ───
print("=== ABSTENTION ===")
st1, _ = BF.analyse([10 ** rng.uniform(0, 6) for _ in range(20)])    # < 30
st2, _ = BF.analyse([0, 0, 0])
check("< 30 données → ABSTENTION", st1 == ABSTENTION)
check("valeurs nulles (pas de chiffre) → ABSTENTION", st2 == ABSTENTION)
st3, _ = BF.analyse([10 ** rng.uniform(0, 6) for _ in range(100)])
check("cas valide → TEST", st3 == TEST)

print(f"\nRÉSULTAT benford : {ok}/{total}")
assert ok == total
