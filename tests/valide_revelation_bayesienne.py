"""
VALIDATION de la RÉVÉLATION BAYÉSIENNE (revelation_bayesienne.py). Vérifie : le posterior Monty (animateur → 2/3 changer,
aléatoire → 1/2) confirmé par SIMULATION ; la DÉPENDANCE AU PROTOCOLE (même observation, posteriors différents) ; la
mauvaise calibration du « 50/50 » naïf sous le protocole animateur (Brier/log-loss pires) et sa correction par le
bayésien ; le posterior somme à 1 et exclut la porte ouverte ; l'ABSTENTION si protocole inconnu. Pur Python, rng seedé.
"""
from __future__ import annotations

import math
import random

from garde_ressources import borne
import revelation_bayesienne as RB
from revelation_bayesienne import ABSTENTION, ANALYSE

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


# ─── 1. Posterior théorique confirmé par simulation ───
print("=== Posterior Monty Hall : théorie vs simulation ===")
p_anim = RB.prob_gain_changer("animateur")
p_alea = RB.prob_gain_changer("aleatoire")
sim_anim = RB.simule("animateur", 200000, random.Random(1), changer=True)
sim_alea = RB.simule("aleatoire", 300000, random.Random(2), changer=True)
print(f"   animateur : théorie={p_anim:.3f} sim={sim_anim:.3f} | aléatoire : théorie={p_alea:.3f} sim={sim_alea:.3f}")
check("animateur : changer gagne 2/3 (théorie)", abs(p_anim - 2 / 3) < 1e-9)
check("animateur : simulation confirme ~2/3", abs(sim_anim - 2 / 3) < 0.01)
check("aléatoire : changer gagne 1/2 (théorie)", abs(p_alea - 0.5) < 1e-9)
check("aléatoire : simulation confirme ~1/2", abs(sim_alea - 0.5) < 0.01)

# ─── 2. Dépendance au protocole : MÊME observation, posteriors DIFFÉRENTS ───
print("=== Dépendance au protocole (même observation) ===")
post_anim = RB.posterior("animateur", 0, 2)
post_alea = RB.posterior("aleatoire", 0, 2)
print(f"   joueur=0, porte 2 ouverte → post(animateur)={({k: round(v,3) for k,v in post_anim.items()})} ; post(aléatoire)={({k: round(v,3) for k,v in post_alea.items()})}")
check("le posterior sur la porte fermée diffère selon le protocole", abs(post_anim[1] - post_alea[1]) > 0.1)
check("animateur : porte fermée (1) à 2/3", abs(post_anim[1] - 2 / 3) < 1e-9)
check("aléatoire : porte fermée (1) à 1/2", abs(post_alea[1] - 0.5) < 1e-9)

# ─── 3. Posterior bien formé : somme 1, porte ouverte exclue ───
print("=== Posterior bien formé ===")
check("le posterior somme à 1", abs(sum(post_anim.values()) - 1.0) < 1e-12)
check("la porte ouverte (2) a un posterior nul", post_anim[2] == 0.0)

# ─── 4. Calibration : le « 50/50 » naïf est mal calibré sous animateur ───
print("=== Mauvaise calibration du 50/50 naïf (protocole animateur) ===")
st, info = RB.analyse("animateur")
print(f"   Brier : naïf(0.5)={info['brier_naif']:.4f} ; bayésien={info['brier_bayes']:.4f}")
check("le 50/50 naïf a un Brier pire que le bayésien (sur-confiant)", info["brier_naif"] > info["brier_bayes"] + 1e-6)
# log-loss empirique sur des parties simulées : naïf vs bayésien
def logloss(proto, p_prevu, n, rng):
    s = 0.0
    for _ in range(n):
        voiture = rng.randrange(3)
        autres = [d for d in (0, 1, 2) if d != 0]
        if proto == "animateur":
            chevres = [d for d in autres if d != voiture]
            ouverte = chevres[rng.randrange(len(chevres))]
        else:
            ouverte = autres[rng.randrange(len(autres))]
            if ouverte == voiture:
                continue
        fermee = [d for d in (0, 1, 2) if d != 0 and d != ouverte][0]
        y = 1 if fermee == voiture else 0                    # 'changer gagne'
        p = min(max(p_prevu, 1e-9), 1 - 1e-9)
        s += -(y * math.log(p) + (1 - y) * math.log(1 - p))
    return s
ll_naif = logloss("animateur", 0.5, 60000, random.Random(3))
ll_bayes = logloss("animateur", 2 / 3, 60000, random.Random(3))
print(f"   log-loss : naïf={ll_naif:.0f} ; bayésien={ll_bayes:.0f}")
check("le bayésien a un meilleur log-loss que le 50/50 naïf", ll_bayes < ll_naif)
check("formule signale la sur-confiance du 50/50 sous animateur", "sur-confiant" in RB.formule((st, info)))

# ─── 5. Sous protocole aléatoire, le 50/50 est correct (honnêteté : pas de fausse accusation) ───
print("=== Honnêteté : sous protocole aléatoire le 50/50 est correct ===")
st2, info2 = RB.analyse("aleatoire")
check("aléatoire : Brier naïf = bayésien (50/50 réellement correct)", abs(info2["brier_naif"] - info2["brier_bayes"]) < 1e-9)
check("formule reconnaît que le 50/50 est correct par coïncidence", "coïncidence" in RB.formule((st2, info2)))

# ─── 6. ABSTENTION ───
print("=== ABSTENTION ===")
check("protocole inconnu → ABSTENTION", RB.analyse("inconnu")[0] == ABSTENTION)
check("cas valide → ANALYSE", st == ANALYSE)

print(f"\nRÉSULTAT revelation_bayesienne : {ok}/{total}")
assert ok == total
