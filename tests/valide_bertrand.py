"""
VALIDATION du PARADOXE DE BERTRAND (bertrand.py). Vérifie : chaque méthode converge vers sa probabilité théorique
(1/3, 1/2, 1/4) ; les trois réponses DIFFÈRENT réellement (question mal posée sans mécanisme) ; chaque méthode est
internement cohérente et reproductible (déterminée une fois le protocole fixé — pas de nihilisme) ; l'ABSTENTION quand
la méthode n'est pas spécifiée. Pur Python, rng seedé.
"""
from __future__ import annotations

import random

from garde_ressources import borne
import bertrand as B
from bertrand import ABSTENTION, ANALYSE

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


# ─── 1. Chaque méthode converge vers sa théorie ───
print("=== Chaque méthode → sa probabilité théorique ===")
res = {}
for meth in B.METHODES:
    p = B.probabilite(meth, 400000, random.Random(hash(meth) % 1000))
    res[meth] = p
    print(f"   {meth:10s}: sim={p:.3f} ; théorie={B.P_THEORIQUE[meth]:.3f}")
    check(f"{meth} : simulation ≈ théorie", abs(p - B.P_THEORIQUE[meth]) < 0.01)

# ─── 2. Les trois réponses DIFFÈRENT (la question est mal posée) ───
print("=== Les trois réponses diffèrent ===")
check("extrémités (1/3) ≠ rayon (1/2)", abs(res["extremites"] - res["rayon"]) > 0.1)
check("rayon (1/2) ≠ milieu (1/4)", abs(res["rayon"] - res["milieu"]) > 0.2)
check("extrémités (1/3) ≠ milieu (1/4)", abs(res["extremites"] - res["milieu"]) > 0.05)
check("les trois valeurs théoriques sont distinctes", len(set(B.P_THEORIQUE.values())) == 3)

# ─── 3. Question non spécifiée → ABSTENTION (réponse honnête) ───
print("=== Question mal posée → ABSTENTION ===")
st_none, raison = B.analyse(None)
print(f"   methode=None → {raison[:60]}…")
check("« corde aléatoire » sans mécanisme → ABSTENTION", st_none == ABSTENTION)
check("méthode inconnue → ABSTENTION", B.analyse("autre", rng=random.Random(0))[0] == ABSTENTION)

# ─── 4. Une fois le protocole fixé, la probabilité est DÉTERMINÉE (pas de nihilisme) ───
print("=== Protocole fixé → probabilité déterminée et reproductible ===")
p1 = B.probabilite("milieu", 300000, random.Random(42))
p2 = B.probabilite("milieu", 300000, random.Random(42))
check("même méthode + même graine → résultat identique (déterminé)", p1 == p2)
st, info = B.analyse("rayon", 200000, random.Random(7))
check("une méthode spécifiée donne ANALYSE (réponse définie)", st == ANALYSE)
check("formule signale la sur-confiance de « la » probabilité", "sur-confiant" in B.formule((st, info)))

print(f"\nRÉSULTAT bertrand : {ok}/{total}")
assert ok == total
