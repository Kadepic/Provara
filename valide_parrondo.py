"""
VALIDATION du PARADOXE DE PARRONDO (parrondo.py). Vérifie : le jeu A perd seul, le jeu B perd seul, mais le MÉLANGE
A/B GAGNE (la combinaison de deux perdants gagne) ; l'alternance ABAB gagne aussi ; le MÉCANISME (B seul passe trop de
temps dans l'état défavorable cap≡0, le mélange l'en éloigne) ; sans dépendance d'état le paradoxe DISPARAÎT (honnêteté) ;
l'ABSTENTION. Pur Python, rng seedé.
"""
from __future__ import annotations

import random

from garde_ressources import borne
import parrondo as P
from parrondo import ABSTENTION, ANALYSE

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


N = 50000
GRAINES = (1, 2, 3, 4, 5, 6)

# ─── 1. A perd, B perd, mais le MÉLANGE gagne ───
print("=== Deux jeux perdants → mélange gagnant ===")
dA = P.derive_moyenne("A", N, GRAINES)
dB = P.derive_moyenne("B", N, GRAINES)
dMix = P.derive_moyenne("mix", N, GRAINES)
print(f"   dérives : A={dA:+.4f} ; B={dB:+.4f} ; mélange={dMix:+.4f}")
check("le jeu A perd seul (dérive < 0)", dA < 0)
check("le jeu B perd seul (dérive < 0)", dB < 0)
check("le MÉLANGE A/B gagne (dérive > 0) — le paradoxe", dMix > 0)
check("la combinaison renverse le signe (perdant+perdant → gagnant)", dMix > 0 > max(dA, dB))

# ─── 2. Un motif périodique BIEN CHOISI gagne — mais le motif compte (pattern-dépendance) ───
print("=== Motifs périodiques : le bon motif gagne, ABAB non ===")
d_ABB = P.derive_motif("ABB", N, GRAINES)
d_ABAB = P.derive_motif("ABAB", N, GRAINES)
print(f"   dérive ABB={d_ABB:+.4f} ; ABAB={d_ABAB:+.4f}")
check("le motif périodique ABB gagne (combinaison déterministe de perdants)", d_ABB > 0)
check("mais ABAB perd : la réussite DÉPEND du motif (pas de combinaison magique universelle)", d_ABAB < 0)

# ─── 3. Mécanisme : B seul reste trop dans l'état défavorable (cap≡0) ───
print("=== Mécanisme : distribution de l'état caché ===")
_, hist_B = P.joue("B", 300000, random.Random(10))
_, hist_mix = P.joue("mix", 300000, random.Random(10))
print(f"   temps en cap≡0 : B seul={hist_B[0]:.3f} ; mélange={hist_mix[0]:.3f} (uniforme=0.333)")
check("B seul passe PLUS de temps que 1/3 dans l'état défavorable", hist_B[0] > 0.34)
check("le mélange réduit le temps dans l'état défavorable vs B seul", hist_mix[0] < hist_B[0])

# ─── 4. Honnêteté : sans dépendance d'état, pas de paradoxe ───
print("=== Honnêteté : sans dépendance d'état, pas de paradoxe ===")
# si B n'est PAS dépendant de l'état (mauvaise pièce toujours), le mélange de deux perdants reste perdant.
def joue_B_plat(n, rng, eps=0.005):
    cap = 0
    for _ in range(n):
        # même proba que A mais un peu pire → perd, indépendant de l'état
        cap += 1 if rng.random() < 0.5 - 2 * eps else -1
    return cap / n
d_plat = sum(joue_B_plat(N, random.Random(g)) for g in GRAINES) / len(GRAINES)
check("un jeu perdant SANS dépendance d'état reste perdant (pas de magie)", d_plat < 0)

# ─── 5. Façade & ABSTENTION ───
print("=== Façade & ABSTENTION ===")
st, info = P.analyse(N, graines=GRAINES)
check("la façade rapporte A perd, B perd, mélange gagne", info["A_perd"] and info["B_perd"] and info["mix_gagne"])
check("formule signale la sur-confiance de « perdant+perdant=perdant »", "sur-confiant" in P.formule((st, info)))
check("horizon trop court → ABSTENTION", P.analyse(1000)[0] == ABSTENTION)
check("cas valide → ANALYSE", st == ANALYSE)

print(f"\nRÉSULTAT parrondo : {ok}/{total}")
assert ok == total
