"""
VALIDATION de la DÉCISION SOUS AMBIGUÏTÉ (decision_ambiguite.py). Vérifie : maxmin EU = prévision inférieure (pont
Walley) et maximise le PLANCHER ; α-Hurwicz interpole maxmin↔maxmax (monotone) ; le minimax-regret minimise le pire
regret (≥0) ; le paradoxe d'ELLSBERG (A≻B & D≻C) est produit par maxmin et INCOMPATIBLE avec toute proba unique ; et
DÉMASQUE la sur-confiance de l'utilité espérée sous prior unique (son acte a un pire-cas ≤ plancher maxmin, et
sur-promet sa performance). Pur Python, léger (pas de lecteur).
"""
from __future__ import annotations

import itertools
import random

from garde_ressources import borne
import decision_ambiguite as D
from decision_ambiguite import ROBUSTE, ABSTENTION
import prevision_walley as W

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


rng = random.Random(60)
ETATS = ["s1", "s2", "s3"]


def simplexe(rng, n):
    v = [rng.random() + 1e-3 for _ in range(n)]
    s = sum(v)
    return [x / s for x in v]


def credal_acts(rng):
    cr = [dict(zip(ETATS, simplexe(rng, len(ETATS)))) for _ in range(rng.randint(2, 5))]
    acts = {f"a{i}": {s: rng.uniform(0, 10) for s in ETATS} for i in range(rng.randint(2, 4))}
    return cr, acts


# ─── 1. maxmin = prévision inférieure + maximise le plancher ───
print("=== maxmin EU = prévision inférieure (pont Walley) + plancher maximal ===")
pont_ok = floor_ok = True
for _ in range(3000):
    cr, acts = credal_acts(rng)
    for u in acts.values():
        if abs(D.valeur_maxmin(cr, u) - W.lower(cr, u)) > 1e-9:
            pont_ok = False
    st, best, table = D.choisir(cr, acts, "maxmin")
    if any(table[best] < table[a] - 1e-9 for a in acts):
        floor_ok = False
check("valeur maxmin = P̲ (lower prevision de Walley)", pont_ok)
check("l'acte maxmin a le plancher le plus haut", floor_ok)

# ─── 2. α-Hurwicz : α=1→maxmin, α=0→maxmax, monotone décroissant en α ───
print("=== α-Hurwicz interpole maxmin↔maxmax (monotone) ===")
interp_ok = mono_ok = True
for _ in range(3000):
    cr, acts = credal_acts(rng)
    u = next(iter(acts.values()))
    if abs(D.valeur_hurwicz(cr, u, 1.0) - D.valeur_maxmin(cr, u)) > 1e-9 or \
       abs(D.valeur_hurwicz(cr, u, 0.0) - D.valeur_maxmax(cr, u)) > 1e-9:
        interp_ok = False
    vals = [D.valeur_hurwicz(cr, u, a) for a in (0.0, 0.3, 0.7, 1.0)]
    if not all(vals[i] >= vals[i + 1] - 1e-9 for i in range(len(vals) - 1)):
        mono_ok = False
check("α=1→maxmin, α=0→maxmax", interp_ok)
check("valeur de Hurwicz décroissante en α (plus d'aversion = plus prudent)", mono_ok)

# ─── 3. maxmin plancher ≤ EU sous toute proba (garantie conservatrice) ───
print("=== Le plancher maxmin ≤ EU sous n'importe quelle proba ===")
cons_ok = True
for _ in range(2000):
    cr, acts = credal_acts(rng)
    for u in acts.values():
        f = D.valeur_maxmin(cr, u)
        for P in cr:
            if D.eu(P, u) < f - 1e-9:
                cons_ok = False
check("min sur le crédal ≤ E_P pour tout sommet P", cons_ok)

# ─── 4. Minimax regret : pire regret minimal, regret ≥ 0 ───
print("=== Regret minimax : minimise le pire regret (≥ 0) ===")
reg_ok = pos_ok = True
for _ in range(2000):
    cr, acts = credal_acts(rng)
    st, best, table = D.choisir(cr, acts, "regret_minimax")
    if any(table[best] > table[a] + 1e-9 for a in acts):
        reg_ok = False
    if any(table[a] < -1e-9 for a in acts):
        pos_ok = False
check("l'acte regret-minimax a le pire regret le plus faible", reg_ok)
check("le regret est ≥ 0", pos_ok)

# ─── 5. Paradoxe d'Ellsberg : A≻B & D≻C, incompatible avec toute proba unique ───
print("=== Paradoxe d'Ellsberg ===")
credal = [{"R": 1/3, "B": 0.0, "Y": 2/3}, {"R": 1/3, "B": 2/3, "Y": 0.0}]
A = {"R": 1, "B": 0, "Y": 0}; B = {"R": 0, "B": 1, "Y": 0}
C = {"R": 1, "B": 0, "Y": 1}; Dd = {"R": 0, "B": 1, "Y": 1}
check("maxmin : A(R) ≻ B(B)", D.valeur_maxmin(credal, A) > D.valeur_maxmin(credal, B))
check("maxmin : D(B∨Y) ≻ C(R∨Y)", D.valeur_maxmin(credal, Dd) > D.valeur_maxmin(credal, C))
# aucune proba unique ne rationalise A≻B ET D≻C
incompatible = True
for t in range(0, 101):
    pb = (2/3) * t / 100
    P = {"R": 1/3, "B": pb, "Y": 2/3 - pb}
    if D.eu(P, A) > D.eu(P, B) and D.eu(P, Dd) > D.eu(P, C):
        incompatible = False; break
check("AUCUNE proba unique ne rationalise A≻B ET D≻C (échec de l'EU)", incompatible)

# ─── 6. DÉMASQUE : l'EU sous prior unique est plus exposée (pire-cas inférieur) ───
print("=== Mode d'échec : EU sous prior unique ignore l'ambiguïté ===")
expose = 0
viol_mm = 0
sur_promesse_eu = 0
n_eu_diff = 0
for _ in range(3000):
    cr, acts = credal_acts(rng)
    _, a_mm, tbl = D.choisir(cr, acts, "maxmin")
    f_mm = tbl[a_mm]
    P0 = {s: sum(P[s] for P in cr) / len(cr) for s in ETATS}     # centre du crédal
    a_eu = max(acts, key=lambda a: D.eu(P0, acts[a]))
    if D.valeur_maxmin(cr, acts[a_eu]) > f_mm + 1e-9:
        expose += 1                                              # ne doit JAMAIS arriver
    if a_eu != a_mm:
        n_eu_diff += 1
    # vraie proba inconnue P*
    Pstar = {s: 0.0 for s in ETATS}
    wts = simplexe(rng, len(cr))
    for j, P in enumerate(cr):
        for s in ETATS:
            Pstar[s] += wts[j] * P[s]
    if D.eu(Pstar, acts[a_mm]) < f_mm - 1e-9:
        viol_mm += 1                                             # garantie maxmin
    if D.eu(Pstar, acts[a_eu]) < D.eu(P0, acts[a_eu]) - 1e-9:
        sur_promesse_eu += 1
check("l'acte EU n'a JAMAIS un meilleur plancher que le maxmin (0 cas)", expose == 0)
check("garantie maxmin : réalisé ≥ plancher TOUJOURS (0 violation)", viol_mm == 0)
print(f"   EU sur-promet sa performance dans {sur_promesse_eu}/3000 tirages ; EU≠maxmin dans {n_eu_diff}")
check("l'EU sous prior unique sur-promet souvent (sur-confiance, >300 cas)", sur_promesse_eu > 300)

# ─── 7. Maximaux / E-admissibles ───
print("=== Actes maximaux & E-admissibles ===")
maxi_ok = adm_ok = True
for _ in range(1500):
    cr, acts = credal_acts(rng)
    _, a_mm, _ = D.choisir(cr, acts, "maxmin")
    maxi = D.maximaux(cr, acts)
    adm = D.e_admissibles(cr, acts)
    if a_mm not in maxi:
        maxi_ok = False
    if not adm <= maxi:    # E-admissible ⊆ maximal
        adm_ok = False
check("l'acte maxmin est MAXIMAL (non dominé)", maxi_ok)
check("E-admissible ⊆ maximal", adm_ok)

# ─── 8. ABSTENTION ───
print("=== ABSTENTION ===")
st1, _, _ = D.choisir([], {"a": {"s1": 1}}, "maxmin")
st2, _, _ = D.choisir([{"s1": 1.0}], {}, "maxmin")
check("crédal vide → ABSTENTION", st1 == ABSTENTION)
check("actes vides → ABSTENTION", st2 == ABSTENTION)

print(f"\nRÉSULTAT decision_ambiguite : {ok}/{total}")
assert ok == total
