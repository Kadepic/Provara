"""
VALIDATION de la CALIBRATION PRÉDICTIVE (predictif.py). La PIT démasque le SENS du défaut d'une distribution
prédictive (trop étroite = sur-confiante, trop large = prudente), uniformité quand calibrée, + perte pinball propre.
"""
from __future__ import annotations

import random

from garde_ressources import borne
import predictif as P
from predictif import CALIBRE, SURCONFIANT, SOUSCONFIANT, ABSTENTION

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


def echantillons(mu, sd, n, m, rng):
    return [[rng.gauss(mu, sd) for _ in range(m)] for _ in range(n)]


print("=== PIT démasque le SENS du défaut (Monte-Carlo, vérité ~ N(0,1)) ===")
for nom, sd, attendu in [("calibré", 1.0, CALIBRE), ("trop étroit", 0.5, SURCONFIANT), ("trop large", 2.0, SOUSCONFIANT)]:
    rng = random.Random(hash(nom) % 1000)
    vt = [rng.gauss(0, 1) for _ in range(3000)]
    pits = P.pit_echantillon(echantillons(0, sd, 3000, 200, rng), vt)
    v, i = P.est_calibre_pit(pits)
    print(f"   {nom:12} var(PIT)={i['variance_pit']:.3f} -> {v}")
    check(f"{nom} -> {attendu}", v == attendu)

print("=== UNIFORMITÉ : PIT calibrée -> histogramme plat (chaque casier ≈ attendu) ===")
rng = random.Random(7)
vt = [rng.gauss(0, 1) for _ in range(6000)]
pits = P.pit_echantillon(echantillons(0, 1, 6000, 300, rng), vt)
h = P.histogramme_pit(pits, 10)
attendu = len(pits) / 10
ecart_max = max(abs(c - attendu) for c in h) / attendu
print(f"   écart relatif max par casier = {ecart_max:.3f}")
check(f"histogramme PIT ~plat (écart max {ecart_max:.2f} < 0.15)", ecart_max < 0.15)
check("moyenne PIT ≈ 0.5 (pas de biais)", abs(sum(pits) / len(pits) - 0.5) < 0.02)

print("=== PERTE PINBALL = règle propre orientée quantile (minimisée au vrai quantile) ===")
rng = random.Random(3)
ech = [rng.gauss(5, 2) for _ in range(20000)]
for tau in (0.1, 0.5, 0.9):
    q_vrai = P.quantile_pinball(ech, tau)
    perte_vrai = sum(P.perte_pinball(q_vrai, y, tau) for y in ech) / len(ech)
    perte_decale = sum(P.perte_pinball(q_vrai + 0.5, y, tau) for y in ech) / len(ech)
    check(f"pinball τ={tau} : minimisée au quantile estimé ({perte_vrai:.3f} < décalé {perte_decale:.3f})",
          perte_vrai < perte_decale)
check("quantile_pinball(0.5) ≈ médiane (≈5)", abs(P.quantile_pinball(ech, 0.5) - 5.0) < 0.1)

print("=== pit_cdf passe-plat + ABSTENTION ===")
check("pit_cdf clampe dans [0,1]", P.pit_cdf([-0.1, 0.5, 1.2]) == [0.0, 0.5, 1.0])
check("n<30 -> ABSTENTION", P.est_calibre_pit([0.5] * 10)[0] == ABSTENTION)

print(f"\nPRÉDICTIF VALIDÉ — {ok}/{total}." if ok == total else f"\nÉCHEC {ok}/{total}")
