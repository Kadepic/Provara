"""
VALIDATION des FONCTIONS DE CROYANCE (croyance_dempster_shafer.py). Démasque la sur-confiance MANUFACTURÉE par la
règle de Dempster sous fort conflit (paradoxe de Zadeh) et montre que YAGER reste honnête (intervalle [Bel, Pl]
large). Vérifie aussi les invariants structurels de la théorie de l'évidence : Bel ≤ Pl, dualité Pl(A)=1−Bel(¬A),
ignorance totale → [0,1], concordance Dempster≈Yager à faible conflit, et l'ABSTENTION sur conflit total / masse
invalide. Pur Python, léger (ne charge pas le lecteur).
"""
from __future__ import annotations

import itertools
import random

from garde_ressources import borne
import croyance_dempster_shafer as DS
from croyance_dempster_shafer import ABSTENTION, COMBINAISON

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


def masse_aleatoire(rng, elements, n_focaux=4):
    """Fonction de masse valide : poids aléatoires sur des sous-ensembles non vides tirés, normalisés."""
    sous_ens = []
    for r in range(1, len(elements) + 1):
        sous_ens += [frozenset(c) for c in itertools.combinations(elements, r)]
    choisis = rng.sample(sous_ens, min(n_focaux, len(sous_ens)))
    poids = {A: rng.random() + 0.05 for A in choisis}
    s = sum(poids.values())
    return {A: v / s for A, v in poids.items()}


# ─── 1. Paradoxe de Zadeh : Dempster fabrique une certitude absurde ───
print("=== Paradoxe de Zadeh : deux médecins en désaccord, tumeur jugée improbable par les deux ===")
m1 = {("meningite",): 0.99, ("tumeur",): 0.01}
m2 = {("commotion",): 0.99, ("tumeur",): 0.01}
K = DS.conflit(m1, m2)
print(f"   conflit K = {K:.4f}")
check("conflit K ≈ 0.9999 (désaccord quasi total)", abs(K - 0.9999) < 1e-6)
d = DS.combine_dempster(m1, m2)
bel_d = DS.belief(d, ("tumeur",))
print(f"   DEMPSTER : Bel(tumeur) = {bel_d:.4f}")
check("Dempster MANUFACTURE la certitude : Bel(tumeur) ≈ 1.0 (mode d'échec démasqué)", bel_d > 0.999)

# ─── 2. Yager : honnête sous le même conflit ───
print("=== Yager reverse le conflit sur l'ignorance ===")
y = DS.combine_yager(m1, m2)
bel_y, pl_y = DS.intervalle_croyance(y, ("tumeur",))
print(f"   YAGER : tumeur ∈ [{bel_y:.4f}, {pl_y:.4f}]")
check("Yager : Bel(tumeur) reste minuscule (n'affirme pas)", bel_y < 0.01)
check("Yager : Pl(tumeur) ≈ 1 → intervalle large = ignorance assumée", pl_y > 0.999)
check("Yager : écart Pl−Bel ≈ 1 (sait qu'il ne sait pas)", (pl_y - bel_y) > 0.99)

# ─── 3. Bel ≤ Pl sur de nombreuses masses/hypothèses aléatoires (invariant structurel) ───
print("=== Bel(A) ≤ Pl(A) sur 4000 cas aléatoires ===")
rng = random.Random(11)
elements = ["a", "b", "c", "d"]
viol = 0
for _ in range(4000):
    m = masse_aleatoire(rng, elements, n_focaux=rng.randint(2, 6))
    r = rng.randint(1, len(elements))
    A = frozenset(rng.sample(elements, r))
    bel, pl = DS.intervalle_croyance(m, A)
    if bel > pl + 1e-9:
        viol += 1
check("aucune violation de Bel ≤ Pl (0/4000)", viol == 0)

# ─── 4. Dualité Pl(A) = 1 − Bel(complément) ───
print("=== Dualité plausibilité/croyance : Pl(A) = 1 − Bel(¬A) ===")
theta = set(elements)
dual_ok = True
for _ in range(2000):
    m = masse_aleatoire(rng, elements, n_focaux=rng.randint(2, 6))
    A = frozenset(rng.sample(elements, rng.randint(1, 3)))
    comp = frozenset(theta - A)
    if abs(DS.plausibility(m, A) - (1.0 - DS.belief(m, comp))) > 1e-9:
        dual_ok = False
        break
check("Pl(A) = 1 − Bel(¬A) (dualité exacte)", dual_ok)

# ─── 5. Ignorance totale m(Θ)=1 → [Bel,Pl] = [0,1] pour toute hypothèse propre ───
print("=== Ignorance totale (masse vacante sur Θ) → aucune information ===")
vac = {tuple(elements): 1.0}
bel_v, pl_v = DS.intervalle_croyance(vac, ("a",))
print(f"   a ∈ [{bel_v:.3f}, {pl_v:.3f}]")
check("vacant : Bel=0, Pl=1 (ne s'engage sur rien)", bel_v == 0.0 and pl_v == 1.0)
check("Bel(Θ) = 1 (on croit forcément au cadre entier)", abs(DS.belief(vac, elements) - 1.0) < 1e-12)

# ─── 6. Faible conflit : Dempster ≈ Yager et la croyance SE RESSERRE correctement ───
print("=== Évidences concordantes (K petit) : Dempster≈Yager, croyance renforcée ===")
a = {("M",): 0.8, ("M", "C"): 0.2}
b = {("M",): 0.7, ("M", "C"): 0.3}
Kc = DS.conflit(a, b)
bd = DS.belief(DS.combine_dempster(a, b), ("M",))
by = DS.belief(DS.combine_yager(a, b), ("M",))
print(f"   K={Kc:.3f} ; Dempster Bel(M)={bd:.3f} ; Yager Bel(M)={by:.3f}")
check("conflit faible (K < 0.05)", Kc < 0.05)
check("Dempster et Yager s'accordent à faible conflit (|Δ| < 0.02)", abs(bd - by) < 0.02)
check("la croyance en M se RENFORCE au-delà de chaque source (> 0.8)", bd > 0.8)

# ─── 7. Conflit total → ABSTENTION (Dempster indéfini) ───
print("=== Conflit total → ABSTENTION ===")
t1 = {("x",): 1.0}
t2 = {("y",): 1.0}
check("Dempster sur conflit total renvoie None", DS.combine_dempster(t1, t2) is None)
st, _, raison = DS.combine(t1, t2, regle="dempster")
print(f"   combine(dempster) -> {st} ({raison})")
check("façade combine(dempster) → ABSTENTION sur conflit total", st == ABSTENTION)
# Yager, lui, reste défini (tout part en ignorance)
sty, my, infoy = DS.combine(t1, t2, regle="yager")
check("Yager reste défini sur conflit total (COMBINAISON)", sty == COMBINAISON and infoy["conflit"] > 0.999)
bel_xy, pl_xy = DS.intervalle_croyance(my, ("x",))
check("Yager conflit total : x ∈ [0,1] (ignorance totale honnête)", bel_xy < 1e-9 and pl_xy > 0.999)

# ─── 8. Masses invalides → erreur / ABSTENTION (pas de faux silencieux) ───
print("=== Masses invalides rejetées ===")
def leve(m):
    try:
        DS.belief(m, ("a",)); return False
    except ValueError:
        return True
check("masse ne sommant pas à 1 → ValueError", leve({("a",): 0.3, ("b",): 0.3}))
check("masse négative → ValueError", leve({("a",): 1.3, ("b",): -0.3}))
check("masse sur ∅ → ValueError", leve({(): 0.5, ("a",): 0.5}))
stbad, _, _ = DS.combine({("a",): 0.5}, {("b",): 0.7}, regle="yager")
check("façade combine sur masse invalide → ABSTENTION (pas de crash)", stbad == ABSTENTION)
stunk, _, _ = DS.combine(t1, t1, regle="inconnue")
check("règle inconnue → ABSTENTION", stunk == ABSTENTION)

print(f"\nRÉSULTAT croyance_dempster_shafer : {ok}/{total}")
assert ok == total
