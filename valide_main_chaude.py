"""
VALIDATION du SOPHISME DU JOUEUR & MAIN CHAUDE (main_chaude.py). Vérifie : (a) l'indépendance réfute le sophisme du joueur
(conditionnelle flux long ≈ p) ; (b) le biais de Miller-Sanjurjo (estimateur naïf sur séquence finie < p), décroissant
avec n ; (c) la détection correcte d'une VRAIE main chaude seulement contre la baseline BIAISÉE (un joueur iid n'est PAS
faussement détecté, un joueur réellement « chaud » l'est) ; (d) le biais persiste avec pièce biaisée ; (e) l'ABSTENTION.
Pur Python, rng seedé.
"""
from __future__ import annotations

import random

from garde_ressources import borne
import main_chaude as MC
from main_chaude import ABSTENTION, ANALYSE

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


rng = random.Random(107)

# ─── 1. Indépendance : le sophisme du joueur est réfuté ───
print("=== Sophisme du joueur réfuté (indépendance) ===")
cond = MC.conditionnelle_flux_long(0.5, 2_000_000, rng)
print(f"   P(succès | succès précédent) sur flux long = {cond:.4f}")
check("la conditionnelle sur flux long ≈ 0.5 (aucun renversement « dû »)", abs(cond - 0.5) < 0.005)

# ─── 2. Biais de Miller-Sanjurjo : estimateur naïf < 0.5 sur séquence finie ───
print("=== Biais de Miller-Sanjurjo (séquence finie) ===")
b4 = MC.biais_miller_sanjurjo(0.5, 4, 300000, rng)
print(f"   E[p̂] sur séquences de n=4 = {b4:.4f}")
check("l'estimateur naïf est biaisé SOUS 0.5 (n=4)", b4 < 0.47)

# ─── 3. Le biais décroît avec la longueur de séquence ───
print("=== Le biais décroît avec n ===")
biais = [MC.biais_miller_sanjurjo(0.5, n, 150000, random.Random(n)) for n in (4, 10, 50, 200)]
print(f"   E[p̂] : {[round(b,4) for b in biais]}")
check("le biais se résorbe quand la séquence s'allonge (→ 0.5)", biais[0] < biais[1] < biais[2] < biais[3] and biais[3] > 0.49)

# ─── 4. Détection d'une vraie main chaude vs la BASELINE BIAISÉE ───
print("=== Détection correcte contre la baseline biaisée ===")
n_seq = 20
baseline = MC.biais_miller_sanjurjo(0.5, n_seq, 200000, random.Random(1))   # baseline iid biaisée

def genere(n, p_base, boost, rng):
    seq = []
    prev = 0
    for _ in range(n):
        p = p_base + (boost if prev == 1 else 0.0)
        x = 1 if rng.random() < p else 0
        seq.append(x)
        prev = x
    return seq

def p_naif_moyen(boost, rng, reps=120000):
    vals = [MC.estimateur_naif(genere(n_seq, 0.5, boost, rng)) for _ in range(reps)]
    vals = [v for v in vals if v is not None]
    return sum(vals) / len(vals)

p_iid = p_naif_moyen(0.0, random.Random(2))        # joueur réellement iid
p_chaud = p_naif_moyen(0.03, random.Random(3))     # joueur avec une PETITE vraie main chaude (boost 0.03)
print(f"   baseline biaisée={baseline:.4f} ; iid={p_iid:.4f} ; petit-chaud={p_chaud:.4f}")
check("un joueur iid n'est PAS faussement détecté (p̂ ≈ baseline biaisée)", abs(p_iid - baseline) < 0.01)
check("un petit effet RÉEL est détecté contre la baseline biaisée (p̂ > baseline)", MC.detecte_main_chaude(0.53, baseline, p_chaud))
check("MAIS comparé à 0.5, ce même effet réel semble nul (p̂ ≈ 0.5) → le débunkeur naïf le RATE", abs(p_chaud - 0.5) < 0.02)

# ─── 5. Le biais persiste avec une pièce biaisée ───
print("=== Pièce biaisée : le biais persiste ===")
bb = MC.biais_miller_sanjurjo(0.6, 5, 200000, random.Random(4))
print(f"   p=0.6, n=5 : E[p̂]={bb:.4f}")
check("l'estimateur naïf reste biaisé sous p même avec pièce biaisée", bb < 0.6)

# ─── 6. Façade & ABSTENTION ───
print("=== Façade & ABSTENTION ===")
st, info = MC.analyse(0.5, 4, 150000, random.Random(5))
check("la façade expose conditionnelle≈0.5 et biais naïf<0.5", abs(info["cond_vraie"] - 0.5) < 0.01 and info["biais_naif"] < 0.47)
check("formule signale les deux sur-confiances", "sur-confiant" in MC.formule((st, info)))
check("rng manquant → ABSTENTION", MC.analyse(0.5, 4, 1000, None)[0] == ABSTENTION)
check("cas valide → ANALYSE", st == ANALYSE)

print(f"\nRÉSULTAT main_chaude : {ok}/{total}")
assert ok == total
