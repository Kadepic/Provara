"""
VALIDATION de l'effet DUNNING-KRUGER comme artefact (dunning_kruger.py). Vérifie : avec une auto-évaluation de PUR BRUIT
(zéro information), le motif DK émerge quand même (bas surestime, haut sous-estime, monotone) ; la pente (auto−réel)/réel
≈ −1 (pur artefact) ; avec connaissance PARFAITE le motif disparaît (pente ≈ 0) ; la pente vaut −(1−info) ; l'ABSTENTION.
Pur Python, rng seedé.
"""
from __future__ import annotations

import random

from garde_ressources import borne
import dunning_kruger as DK
from dunning_kruger import ABSTENTION, ANALYSE

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


# ─── 1. Pur bruit (info=0) : le motif DK émerge ───
print("=== Auto-évaluation = pur bruit : motif DK émerge ===")
st, info = DK.analyse(info=0.0, n=40000, rng=random.Random(130))
quart = info["quartiles"]
ecarts = [d for _, _, d in quart]
print(f"   écarts par quartile : {[round(e) for e in ecarts]}")
check("le quartile du BAS se surestime (écart > 0)", info["surestim_bas"] > 20)
check("le quartile du HAUT se sous-estime (écart < 0)", info["surestim_haut"] < -20)
check("la surestimation décroît monotone du bas vers le haut", ecarts[0] > ecarts[1] > ecarts[2] > ecarts[3])

# ─── 2. Pente ≈ −1 (pur artefact) ───
print("=== Pente (auto−réel)/réel ≈ −1 ===")
print(f"   pente={info['pente']:.3f}")
check("à information nulle, la pente est ≈ −1 (artefact total)", abs(info["pente"] + 1.0) < 0.05)

# ─── 3. Connaissance parfaite : le motif disparaît ───
print("=== Connaissance parfaite : pas de motif ===")
st1, info1 = DK.analyse(info=1.0, n=40000, rng=random.Random(2))
print(f"   pente (info=1)={info1['pente']:.3f} ; écarts={[round(d) for _,_,d in info1['quartiles']]}")
check("avec connaissance parfaite, la pente ≈ 0 (pas de motif DK)", abs(info1["pente"]) < 0.02)
check("avec connaissance parfaite, aucun quartile ne se sur/sous-estime", all(abs(d) < 2 for _, _, d in info1["quartiles"]))

# ─── 4. La pente vaut −(1−info) ───
print("=== Pente = −(1−info) ===")
for inf_niv in (0.25, 0.5, 0.75):
    p = DK.analyse(info=inf_niv, n=40000, rng=random.Random(int(inf_niv * 100)))[1]["pente"]
    print(f"   info={inf_niv} : pente={p:.3f} (attendu {-(1-inf_niv):.2f})")
    check(f"pente ≈ −(1−info) à info={inf_niv}", abs(p + (1 - inf_niv)) < 0.05)

# ─── 5. Même avec un peu d'info, le motif persiste (graphe non concluant) ───
print("=== Le motif persiste avec info partielle ===")
info05 = DK.analyse(info=0.5, n=40000, rng=random.Random(7))[1]
check("à info=0.5, le bas se surestime encore (le graphe ne prouve pas l'incompétence)", info05["surestim_bas"] > 10)
check("formule signale la sur-confiance de l'interprétation DK", "sur-confiant" in DK.formule((st, info)))

# ─── 6. ABSTENTION ───
print("=== ABSTENTION ===")
check("rng manquant → ABSTENTION", DK.analyse(rng=None)[0] == ABSTENTION)
check("n trop petit → ABSTENTION", DK.analyse(n=100, rng=random.Random(0))[0] == ABSTENTION)
check("cas valide → ANALYSE", st == ANALYSE)

print(f"\nRÉSULTAT dunning_kruger : {ok}/{total}")
assert ok == total
