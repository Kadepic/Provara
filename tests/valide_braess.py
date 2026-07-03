"""
VALIDATION du PARADOXE DE BRAESS (braess.py). Vérifie : l'équilibre sans pont (65) ; AVEC pont l'équilibre EMPIRE (80 >
65) bien qu'on ait ajouté une option ; tout le monde se rue sur le zigzag (piège) ; l'optimum social (65) et le prix de
l'anarchie ; la stabilité de Nash (aucune déviation profitable) ; la régime-dépendance HONNÊTE (à faible trafic le pont
AIDE, pas de fausse alarme) ; l'ABSTENTION. Pur Python déterministe.
"""
from __future__ import annotations

from garde_ressources import borne
import braess as B
from braess import ABSTENTION, ANALYSE

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


# ─── 1. Équilibre sans pont = 65 ───
print("=== Équilibre sans raccourci ===")
st, info = B.analyse(4000)
print(f"   sans pont={info['temps_sans_pont']:.1f} ; avec pont={info['temps_avec_pont']:.1f}")
check("équilibre sans raccourci = 65 (réparti 50/50)", abs(info["temps_sans_pont"] - 65.0) < 1e-6)

# ─── 2. AVEC le pont, l'équilibre EMPIRE (Braess) ───
print("=== Ajouter le raccourci EMPIRE l'équilibre ===")
check("avec raccourci = 80 (tout le monde zigzague)", abs(info["temps_avec_pont"] - 80.0) < 1e-6)
check("le temps de trajet AUGMENTE après ajout de l'option (paradoxe de Braess)", info["temps_avec_pont"] > info["temps_sans_pont"])
check("la façade détecte braess=True", info["braess"])

# ─── 3. Tout le monde se rue sur le zigzag (le piège dominant) ───
print("=== Ruée sur le zigzag ===")
_, assign = B.equilibre_nash(4000, B.AVEC_PONT)
frac_zigzag = sum(1 for p in assign if p == 2) / 4000
print(f"   fraction sur le zigzag = {frac_zigzag:.2f}")
check("≈ tout le monde prend le zigzag à l'équilibre", frac_zigzag > 0.99)

# ─── 4. Optimum social & prix de l'anarchie ───
print("=== Optimum social & prix de l'anarchie ===")
print(f"   optimum social={info['optimum_social']:.1f} ; prix de l'anarchie={info['prix_anarchie']:.3f}")
check("l'optimum social (sans utiliser le pont) reste à 65", abs(info["optimum_social"] - 65.0) < 1e-6)
check("le prix de l'anarchie = 80/65 > 1", abs(info["prix_anarchie"] - 80.0 / 65.0) < 1e-6)

# ─── 5. Stabilité de Nash : aucune déviation profitable ───
print("=== Stabilité de l'équilibre (Nash pur) ===")
flux = B._flux_aretes(assign, B.AVEC_PONT)
def lat_si(i, p):
    s = 0.0
    for e in B.AVEC_PONT[p]:
        x = flux.get(e, 0) + (0 if e in B.AVEC_PONT[assign[i]] else 1)
        s += B._latence_arete(e, x, B.RESEAU)
    return s
stable = all(lat_si(i, assign[i]) <= min(lat_si(i, p) for p in range(len(B.AVEC_PONT))) + 1e-9 for i in range(0, 4000, 50))
check("aucun agent n'a de déviation strictement profitable (Nash pur)", stable)

# ─── 6. Honnêteté : à faible trafic, le raccourci AIDE (pas de fausse alarme) ───
print("=== Honnêteté : à faible trafic le raccourci aide ===")
st2, info2 = B.analyse(1000)
print(f"   N=1000 : sans pont={info2['temps_sans_pont']:.1f} ; avec pont={info2['temps_avec_pont']:.1f}")
check("à faible trafic, ajouter le raccourci AMÉLIORE (braess=False)", not info2["braess"] and info2["temps_avec_pont"] < info2["temps_sans_pont"])
check("formule signale la sur-confiance de la monotonie", "sur-confiant" in B.formule((st, info)))

# ─── 7. ABSTENTION ───
print("=== ABSTENTION ===")
check("réseau trop petit → ABSTENTION", B.analyse(50)[0] == ABSTENTION)
check("cas valide → ANALYSE", st == ANALYSE)

print(f"\nRÉSULTAT braess : {ok}/{total}")
assert ok == total
