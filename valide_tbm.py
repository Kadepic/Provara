"""
VALIDATION du TRANSFERABLE BELIEF MODEL (tbm.py) — jugé par calibration.py. Vérifie : BetP est une probabilité valide
et vit DANS le crédal (Bel ≤ BetP ≤ Pl, 0 violation) ; la règle conjonctive ⊕ accumule le conflit sur ∅, est
commutative, et FERMER LE MONDE après ⊕ redonne la règle de Dempster (pont vers brique 50) ; l'AVERTISSEMENT m(∅)
(monde ouvert) que Dempster jette = sur-confiance démasquée (Zadeh) ; et BetP-comme-vérité sous-couvre (SUR-CONFIANT)
là où [Bel,Pl] tient. Pur Python, léger (pas de lecteur).
"""
from __future__ import annotations

import itertools
import random

from garde_ressources import borne
import tbm as T
from tbm import ABSTENTION, PIGNISTIQUE
import croyance_dempster_shafer as DS
import calibration as CAL
from calibration import SURCONFIANT

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


rng = random.Random(59)
LABELS = ["a", "b", "c", "d"]


def masse_fermee(rng, labels, nf=4):
    """Masse monde FERMÉ (pas de ∅), normalisée."""
    subs = []
    for r in range(1, len(labels) + 1):
        subs += [tuple(c) for c in itertools.combinations(labels, r)]
    ch = rng.sample(subs, min(nf, len(subs)))
    w = {s: rng.random() + 0.05 for s in ch}
    tot = sum(w.values())
    return {s: v / tot for s, v in w.items()}


def proba_credal(rng, masse, labels):
    """P du crédal : alloue chaque masse focale entre ses éléments."""
    P = {l: 0.0 for l in labels}
    for B, m in masse.items():
        B = list(B)
        if not B:
            continue
        coupe = sorted(rng.random() for _ in range(len(B) - 1))
        bornes = [0.0] + coupe + [1.0]
        for i, e in enumerate(B):
            P[e] += m * (bornes[i + 1] - bornes[i])
    return P


# ─── 1. BetP probabilité valide ───
print("=== BetP est une probabilité valide ===")
valid = True
for _ in range(3000):
    m = masse_fermee(rng, LABELS, rng.randint(2, 6))
    betp = T.pignistique(m, LABELS)
    if abs(sum(betp.values()) - 1.0) > 1e-9 or any(v < -1e-12 for v in betp.values()):
        valid = False; break
check("BetP somme à 1 et ≥ 0", valid)

# ─── 2. BetP ∈ [Bel, Pl] (dans le crédal) ───
print("=== BetP(A) ∈ [Bel(A), Pl(A)] pour tout événement ===")
viol = 0
for _ in range(2000):
    m = masse_fermee(rng, LABELS, rng.randint(2, 6))
    betp = T.pignistique(m, LABELS)
    for r in range(1, len(LABELS) + 1):
        for A in itertools.combinations(LABELS, r):
            bp = T.betp_evenement(betp, A)
            if not (T.belief(m, A) - 1e-9 <= bp <= T.plausibilite(m, A) + 1e-9):
                viol += 1
check("Bel(A) ≤ BetP(A) ≤ Pl(A) (0 violation)", viol == 0)

# ─── 3. Conjonctive : commutative, conflit sur ∅, fermeture = Dempster ───
print("=== Règle conjonctive ⊕ : commutative, conflit→∅, fermeture = Dempster ===")
comm_ok = dempster_ok = conflit_ok = True
for _ in range(2000):
    m1 = masse_fermee(rng, LABELS, rng.randint(2, 4))
    m2 = masse_fermee(rng, LABELS, rng.randint(2, 4))
    c12 = T.conjonctive(m1, m2); c21 = T.conjonctive(m2, m1)
    if any(abs(c12.get(k, 0) - c21.get(k, 0)) > 1e-12 for k in set(c12) | set(c21)):
        comm_ok = False
    # conflit sur ∅ = conflit de Dempster
    if abs(c12.get(frozenset(), 0.0) - DS.conflit(m1, m2)) > 1e-9:
        conflit_ok = False
    # fermer le monde après ⊕ = Dempster
    ferme = T.ferme_le_monde(c12)
    demp = DS.combine_dempster(m1, m2)
    if ferme is not None and demp is not None:
        if any(abs(ferme.get(k, 0) - demp.get(k, 0)) > 1e-9 for k in set(ferme) | set(demp)):
            dempster_ok = False
check("⊕ commutative", comm_ok)
check("conflit accumulé sur ∅ = conflit de Dempster", conflit_ok)
check("fermer le monde après ⊕ = règle de Dempster (pont brique 50)", dempster_ok)

# ─── 4. Signature monde ouvert : Zadeh → m(∅) alarme, Dempster la jette ───
print("=== Paradoxe de Zadeh : TBM ALERTE (m(∅)), Dempster cache ===")
m1 = {("M",): 0.99, ("T",): 0.01}
m2 = {("C",): 0.99, ("T",): 0.01}
comb = T.conjonctive(m1, m2)
vide = comb.get(frozenset(), 0.0)
belT_dempster = DS.belief(DS.combine_dempster(m1, m2), ("T",))
print(f"   TBM m(∅)={vide:.4f} (alarme) ; Dempster Bel(T)={belT_dempster:.3f} (certitude jetant l'alarme)")
check("TBM met le conflit sur ∅ (m(∅) ≈ 0.9999)", vide > 0.999)
check("Dempster (monde fermé) cache le conflit en fausse certitude", belT_dempster > 0.999)

# ─── 5. DÉMASQUE : BetP-comme-vérité sous-couvre (SUR-CONFIANT) ───
print("=== Mode d'échec : BetP (point de pari) annoncé comme vraie proba ===")
int_cred, int_betp, verites = [], [], []
for _ in range(1500):
    m = masse_fermee(rng, LABELS, rng.randint(2, 5))
    betp = T.pignistique(m, LABELS)
    Pstar = proba_credal(rng, m, LABELS)
    for r in (1, 2):
        for A in itertools.combinations(LABELS, r):
            int_cred.append((T.belief(m, A), T.plausibilite(m, A)))
            bp = T.betp_evenement(betp, A)
            int_betp.append((bp, bp))
            verites.append(sum(Pstar[w] for w in A))
covC = sum(1 for (lo, hi), v in zip(int_cred, verites) if lo - 1e-9 <= v <= hi + 1e-9) / len(verites)
covB = CAL.couverture(int_betp, verites)[0]
vB, iB = CAL.verdict_couverture(int_betp, verites, 0.80)
print(f"   couverture [Bel,Pl]={covC:.3f} ; point BetP={covB:.3f} ({vB})")
check("[Bel,Pl] couvre la proba vraie (=1.0)", covC == 1.0)
check("BetP-comme-vérité est SUR-CONFIANT", vB == SURCONFIANT and covB < 0.7)

# ─── 6. ABSTENTION : conflit total m(∅)=1 ───
print("=== ABSTENTION : conflit total ===")
st, act, raison = T.decide({(): 1.0}, LABELS, {"x": {l: 1.0 for l in LABELS}})
print(f"   m(∅)=1 -> {st} ({raison})")
check("m(∅)=1 → ABSTENTION (impossible de parier)", st == ABSTENTION)
st2, _, _ = T.decide(masse_fermee(rng, LABELS, 3), LABELS,
                      {"x": {l: rng.random() for l in LABELS}, "y": {l: rng.random() for l in LABELS}})
check("masse valide → décision PIGNISTIQUE", st2 == PIGNISTIQUE)

print(f"\nRÉSULTAT tbm : {ok}/{total}")
assert ok == total
