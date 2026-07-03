"""
VALIDATION de la LOI DE GOODHART (goodhart.py). Vérifie : sans pression le proxy fonctionne (corr≈1, sélection = oracle) ;
sous pression la corrélation proxy/objectif S'EFFONDRE ; le métrique MONTE pendant que la qualité livrée des sélectionnés
TOMBE (signature de Goodhart) ; l'oracle (sélection sur l'objectif vrai) domine toujours ; HONNÊTETÉ : sans gameabilité
(λ=0) maximiser le proxy aide encore (distinction d'avec winner_curse) ; l'ABSTENTION. Pur Python, rng seedé.
"""
from __future__ import annotations

import random

from garde_ressources import borne
import goodhart as G
from goodhart import ABSTENTION, ANALYSE

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


rng = random.Random(113)
st, info = G.analyse(pressions=(0.0, 1.0, 3.0), lam=1.0, n=4000, rng=rng)
bas = info["courbe"][0][1]
mid = info["courbe"][1][1]
haut = info["courbe"][2][1]

# ─── 1. Sans pression, le proxy fonctionne ───
print("=== Sans pression : le proxy fonctionne ===")
print(f"   corr={bas['corr_P_U']:.2f} ; qualité_sel={bas['qualite_des_selectionnes']:.2f} ; oracle={bas['qualite_oracle']:.2f}")
check("sans pression, corr(proxy, objectif) ≈ 1", bas["corr_P_U"] > 0.98)
check("sans pression, la sélection par proxy = oracle", abs(bas["qualite_des_selectionnes"] - bas["qualite_oracle"]) < 1e-6)

# ─── 2. Sous pression, la corrélation s'effondre ───
print("=== La corrélation proxy/objectif s'effondre ===")
print(f"   corr : {bas['corr_P_U']:.2f} → {mid['corr_P_U']:.2f} → {haut['corr_P_U']:.2f}")
check("la corrélation proxy/objectif décroît avec la pression", bas["corr_P_U"] > mid["corr_P_U"] > haut["corr_P_U"])
check("sous forte pression, la corrélation est presque détruite", haut["corr_P_U"] < 0.3)

# ─── 3. SIGNATURE : le métrique monte, la qualité livrée tombe ───
print("=== Le métrique monte, la qualité livrée tombe ===")
print(f"   proxy_sel : {bas['proxy_des_selectionnes']:.2f} → {haut['proxy_des_selectionnes']:.2f} ; "
      f"qualité_sel : {bas['qualite_des_selectionnes']:.2f} → {haut['qualite_des_selectionnes']:.2f}")
check("le proxy des sélectionnés MONTE avec la pression", haut["proxy_des_selectionnes"] > bas["proxy_des_selectionnes"])
check("la qualité livrée des sélectionnés TOMBE avec la pression", haut["qualite_des_selectionnes"] < bas["qualite_des_selectionnes"])
check("sous forte pression, la qualité des sélectionnés devient NÉGATIVE (pire que la moyenne nulle)", haut["qualite_des_selectionnes"] < 0)

# ─── 4. L'oracle domine toujours, l'écart se creuse ───
print("=== L'oracle (objectif vrai) domine ===")
ecart_bas = bas["qualite_oracle"] - bas["qualite_des_selectionnes"]
ecart_haut = haut["qualite_oracle"] - haut["qualite_des_selectionnes"]
print(f"   écart oracle − proxy : {ecart_bas:.2f} → {ecart_haut:.2f}")
check("l'oracle livre au moins autant que la sélection par proxy", haut["qualite_oracle"] >= haut["qualite_des_selectionnes"])
check("l'écart oracle − proxy se creuse avec la pression", ecart_haut > ecart_bas + 0.5)

# ─── 5. Honnêteté : sans gameabilité (λ=0), maximiser le proxy aide encore ───
print("=== Honnêteté : sans gameabilité (λ=0) ===")
st0, info0 = G.analyse(pressions=(0.0, 3.0), lam=0.0, n=4000, rng=random.Random(5))
h0 = info0["courbe"][-1][1]
print(f"   λ=0, pression=3 : qualité_sel={h0['qualite_des_selectionnes']:.2f} (reste positive)")
check("sans gameabilité, la qualité des sélectionnés reste élevée (pas de Goodhart)", h0["qualite_des_selectionnes"] > 1.0)
check("formule signale la sur-confiance d'optimiser le proxy", "sur-confiant" in G.formule((st, info)))

# ─── 6. ABSTENTION ───
print("=== ABSTENTION ===")
check("rng manquant → ABSTENTION", G.analyse(rng=None)[0] == ABSTENTION)
check("n trop petit → ABSTENTION", G.analyse(n=50, rng=random.Random(0))[0] == ABSTENTION)
check("cas valide → ANALYSE", st == ANALYSE)

print(f"\nRÉSULTAT goodhart : {ok}/{total}")
assert ok == total
