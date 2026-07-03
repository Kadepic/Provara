"""
VALIDATION du CRITÈRE DE KELLY (kelly.py). Vérifie que f* maximise le taux de croissance log, que SUR-MISER fait
baisser puis rend NÉGATIVE la croissance (ruine), que la fortune médiane à long terme est maximale à Kelly et part en
ruine quand on sur-mise, que MAXIMISER L'ESPÉRANCE (sur-miser) gonfle la moyenne mais ruine la trajectoire TYPIQUE
(sur-confiance), qu'un avantage négatif donne f*≤0 (ne pas parier), et l'ABSTENTION. Pur Python, léger.
"""
from __future__ import annotations

import random
import statistics

from garde_ressources import borne
import kelly as K
from kelly import ABSTENTION, KELLY

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


rng = random.Random(79)
p, b = 0.55, 1.0
fk = K.fraction_kelly(p, b)

# ─── 1. f* maximise G ───
print("=== Kelly f* maximise le taux de croissance log ===")
G = lambda f: K.croissance(f, p, b)
check("f* = (pb−q)/b = 0.10", abs(fk - 0.10) < 1e-9)
grille = [i / 200 for i in range(1, 199)]
fmax = max(grille, key=G)
print(f"   argmax sur grille = {fmax:.3f} (f* = {fk:.3f})")
check("f* ≈ argmax_f G(f) (sur grille fine)", abs(fmax - fk) < 0.01)
check("G(f*) ≥ G(f) pour tout f de la grille", all(G(fk) >= G(f) - 1e-9 for f in grille))

# ─── 2. Sur-miser : croissance baisse puis NÉGATIVE ───
print("=== Sur-miser : croissance ↓ puis négative ===")
print(f"   G(f*)={G(fk):+.4f} ; G(2f*)={G(2*fk):+.4f} ; G(3f*)={G(3*fk):+.4f}")
check("G(2f*) ≈ 0 (seuil de croissance nulle)", abs(G(2 * fk)) < 0.005)
check("G(3f*) < 0 (sur-mise = croissance négative)", G(3 * fk) < 0)
check("la croissance décroît au-delà de f*", G(fk) > G(2 * fk) > G(3 * fk))

# ─── 3. Long terme : fortune médiane maximale à Kelly, ruine si on sur-mise ───
print("=== Fortune médiane (200 coups) : Kelly > sur-mise > agressif (ruine) ===")
def median_fortune(f, reps=3000, T=200):
    return statistics.median(K.fortune_finale(f, p, b, T, rng) for _ in range(reps))
med_k = median_fortune(fk)
med_2k = median_fortune(2 * fk)
med_agr = median_fortune(0.5)
print(f"   médianes : Kelly={med_k:.3g} ; 2×Kelly={med_2k:.3g} ; agressif(0.5)={med_agr:.3g}")
check("Kelly fait croître la fortune typique (médiane > 1)", med_k > 1.5)
check("Kelly > 2×Kelly (sur-miser réduit la fortune typique)", med_k > med_2k)
check("l'agressif ruine la fortune typique (médiane ≪ 1)", med_agr < 0.01)

# ─── 4. DÉMASQUE : maximiser l'espérance gonfle la moyenne mais ruine le typique ───
print("=== Mode d'échec : espérance (moyenne) vs trajectoire typique (médiane) ===")
agr = [K.fortune_finale(0.5, p, b, 200, rng) for _ in range(4000)]
moy_agr = statistics.mean(agr); med_agr2 = statistics.median(agr)
ws_k = [K.fortune_finale(fk, p, b, 200, rng) for _ in range(4000)]
print(f"   agressif : moyenne={moy_agr:.3g} ≫ médiane={med_agr2:.3g} ; Kelly médiane={statistics.median(ws_k):.3g}")
check("l'agressif a une grande MOYENNE mais une médiane ruinée (sur-confiance de l'espérance)", moy_agr > 10 * med_agr2 and med_agr2 < 0.01)
check("Kelly bat l'agressif sur la fortune TYPIQUE (médiane)", statistics.median(ws_k) > med_agr2)

# ─── 5. Avantage négatif → ne pas parier ───
print("=== Avantage négatif → f* ≤ 0 (ne pas parier) ===")
st_neg, info_neg = K.conseille(0.45, 1.0)
print(f"   p=0.45 : f*={info_neg['f_kelly']:.3f}, avantage={info_neg['avantage']:.3f}")
check("avantage négatif → f* ≤ 0", info_neg["f_kelly"] <= 0)
check("formule conseille de NE PAS parier", "NE PAS parier" in K.formule((st_neg, info_neg)))

# ─── 6. ABSTENTION ───
print("=== ABSTENTION ===")
st1, _ = K.conseille(0.0, 1.0)
st2, _ = K.conseille(0.5, 0.0)
check("p∉(0,1) → ABSTENTION", st1 == ABSTENTION)
check("b≤0 → ABSTENTION", st2 == ABSTENTION)
st3, _ = K.conseille(0.6, 2.0)
check("cas valide → KELLY", st3 == KELLY)

print(f"\nRÉSULTAT kelly : {ok}/{total}")
assert ok == total
