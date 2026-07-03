"""
VALIDATION de l'AGRÉGATION BAYÉSIENNE CORRÉLÉE (bayes.posterior_correle) — corrige le caveat de la brique 2.
Propriétés EXACTES (ρ=0=indépendant, ρ=1 sur doublons=une seule copie, monotonie) + CALIBRATION RESTAURÉE : là où
l'agrégation naïve d'indices corrélés est SUR-CONFIANTE (démasquée par calibration.py), la version escomptée est CALIBRÉE.
"""
from __future__ import annotations

import random

from garde_ressources import borne
import bayes as B
from bayes import ESTIMATION, ABSTENTION
import calibration as CAL
from calibration import CALIBRE, SURCONFIANT

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


print("=== PROPRIÉTÉS EXACTES ===")
ind = [(0.9, 0.2, 1), (0.8, 0.3, 0), (0.75, 0.35, 1)]
check("ρ=0 identique à posterior indépendant",
      abs(B.posterior_correle(0.2, ind, 0.0)[1] - B.posterior(0.2, ind)[1]) < 1e-12)
dup = (0.85, 0.25, 1)
check("ρ=1 sur 5 doublons == 1 seule copie (pas de sur-comptage)",
      abs(B.posterior_correle(0.3, [dup] * 5, 1.0)[1] - B.posterior(0.3, [dup])[1]) < 1e-12)
ps = [B.posterior_correle(0.3, [dup] * 4, r)[1] for r in (0.0, 0.25, 0.5, 0.75, 1.0)]
check(f"monotone : postérieure décroît avec ρ {[round(x,3) for x in ps]}", all(ps[i] >= ps[i + 1] for i in range(4)))
check("postérieure reste entre prior et la version indépendante", ps[-1] >= 0.3 - 1e-9 and ps[0] >= ps[-1])

print("=== CALIBRATION RESTAURÉE : indices DOUBLONS, naïf SURCONFIANT vs corrélé CALIBRE ===")
specs = [(0.8, 0.3), (0.75, 0.25), (0.7, 0.35), (0.85, 0.4)]   # 4 « capteurs »


def simule_doublons(prior, M, graine):
    """Chaque cas : H~Bernoulli(prior). Les 4 indices reçoivent LE MÊME signal (doublons parfaits, ρ=1).
    Renvoie (postérieurs_naïfs, postérieurs_correlés_ρ1, vérités)."""
    rng = random.Random(graine)
    naif, corr, ver = [], [], []
    for _ in range(M):
        h = 1 if rng.random() < prior else 0
        po, pn = specs[0]
        sig = 1 if rng.random() < (po if h else pn) else 0      # un seul signal, dupliqué
        indices = [(spo, spn, sig) for (spo, spn) in specs]
        sn = B.posterior(prior, indices)
        sc = B.posterior_correle(prior, indices, 1.0)
        if sn[0] == ESTIMATION and sc[0] == ESTIMATION:
            naif.append(sn[1]); corr.append(sc[1]); ver.append(h)
    return naif, corr, ver


naif, corr, ver = simule_doublons(0.30, 8000, graine=1)
vn, in_ = CAL.est_calibre(*CAL.depuis_probas(naif, ver))
vc, ic = CAL.est_calibre(*CAL.depuis_probas(corr, ver))
print("   naïf    :", CAL.formule((vn, in_), "forecast"))
print("   corrélé :", CAL.formule((vc, ic), "forecast"))
check(f"naïf (doublons traités indépendants) -> SURCONFIANT (ece={in_['ece']:.3f})", vn == SURCONFIANT)
check(f"corrélé ρ=1 -> CALIBRE (ece={ic['ece']:.3f})", vc == CALIBRE)
check(f"ECE corrélé ({ic['ece']:.3f}) << ECE naïf ({in_['ece']:.3f})", ic["ece"] < in_["ece"] / 2)

print("=== CORRÉLATION PARTIELLE : ρ estimé empiriquement réduit la sur-confiance ===")
def simule_partiel(prior, p_copie, M, graine):
    """Chaque indice copie un signal maître avec proba p_copie, sinon tire indépendamment (corrélation partielle).
    Renvoie (signaux_historique pour estimer ρ, fonction de rejeu)."""
    rng = random.Random(graine)
    signaux, naif, ver = [], [], []
    cas = []
    for _ in range(M):
        h = 1 if rng.random() < prior else 0
        maitre = None
        vec, indices = [], []
        for (po, pn) in specs:
            if maitre is None or rng.random() >= p_copie:
                s = 1 if rng.random() < (po if h else pn) else 0
                if maitre is None:
                    maitre = s
            else:
                s = maitre
            vec.append(s)
            indices.append((po, pn, s))
        signaux.append(vec)
        cas.append((indices, h))
    return signaux, cas


signaux, cas = simule_partiel(0.30, 0.6, 8000, graine=2)
rho = B.rho_empirique(signaux)
print(f"   ρ estimé = {rho:.3f}")
naif2 = [B.posterior(0.30, ind)[1] for (ind, _) in cas]
corr2 = [B.posterior_correle(0.30, ind, rho)[1] for (ind, _) in cas]
ver2 = [h for (_, h) in cas]
en = CAL.ece(*CAL.depuis_probas(naif2, ver2))
ec = CAL.ece(*CAL.depuis_probas(corr2, ver2))
check(f"0 < ρ estimé < 1 (corrélation partielle détectée) : {rho:.3f}", 0.0 < rho < 1.0)
check(f"ECE corrélé ({ec:.3f}) < ECE naïf ({en:.3f}) (sur-confiance réduite)", ec < en)

print("=== ABSTENTION / garde-fous ===")
check("ρ hors [0,1] -> ABSTENTION", B.posterior_correle(0.3, [dup], 1.5)[0] == ABSTENTION)
check("prior dégénéré -> ABSTENTION", B.posterior_correle(0.0, [dup], 0.5)[0] == ABSTENTION)
check("vraisemblance dégénérée -> ABSTENTION", B.posterior_correle(0.3, [(1.0, 0.2, 1)], 0.5)[0] == ABSTENTION)
check("rho_empirique sur signaux constants = 0", B.rho_empirique([[1, 1], [1, 1], [1, 1]]) == 0.0)

print(f"\nBAYES CORRÉLÉ VALIDÉ — {ok}/{total}." if ok == total else f"\nÉCHEC {ok}/{total}")
