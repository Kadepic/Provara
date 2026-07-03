"""
VALIDATION de la COMBINAISON BAYÉSIENNE (bayes.py) — la postérieure est-elle CALIBRÉE ? Preuve Monte-Carlo,
JUGÉE PAR L'INSTRUMENT calibration.py (l'architecture voulue : une brique P2 prouvée par le mètre-étalon P2).

Monde connu : H ~ Bernoulli(prior). k indices conditionnellement INDÉPENDANTS, chacun signal ~ Bernoulli(p_si_oui)
si H sinon Bernoulli(p_si_non). On calcule la postérieure avec les VRAIES vraisemblances et on vérifie qu'elle est
calibrée (un « 80 % » s'avère vrai ~80 % du temps). Plus : honnêteté (prior respecté, monotonie, refus du dégénéré)
et le CAVEAT mesuré : des indices CORRÉLÉS rendent la postérieure SUR-CONFIANTE (calibration.py le démasque).
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


def simule(prior, specs, M, graine, correle=False):
    """specs = liste de (p_si_oui, p_si_non). Renvoie (posteriors, verites H). Si correle=True, TOUS les indices
    copient le 1er signal (redondance maximale) -> doit produire de la sur-confiance."""
    rng = random.Random(graine)
    posts, verites = [], []
    for _ in range(M):
        h = 1 if rng.random() < prior else 0
        indices = []
        premier = None
        for (po, pn) in specs:
            p = po if h else pn
            sig = 1 if rng.random() < p else 0
            if correle:
                if premier is None:
                    premier = sig
                sig = premier                      # tous identiques = corrélation parfaite
            indices.append((po, pn, sig))
        st, pp, _ = B.posterior(prior, indices)
        if st == ESTIMATION:
            posts.append(pp)
            verites.append(h)
    return posts, verites


print("=== POSTÉRIEURE CALIBRÉE (indices INDÉPENDANTS, vraisemblances vraies) -> CALIBRE ===")
specs = [(0.8, 0.3), (0.75, 0.25), (0.7, 0.35), (0.9, 0.4)]
posts, verites = simule(0.30, specs, 8000, graine=1)
conf, just = CAL.depuis_probas(posts, verites)
v, infos = CAL.est_calibre(conf, just)
print("   ", CAL.formule((v, infos), "forecast"))
check(f"bayésien indépendant -> CALIBRE (ece={infos['ece']:.3f})", v == CALIBRE)
check(f"ECE faible ({infos['ece']:.3f} <= 0.04)", infos["ece"] <= 0.04)

print("=== couverture par tranche : parmi les ~p% annoncés, ~p% sont vrais (calibration fine) ===")
diag = CAL.diagramme_fiabilite(*CAL.depuis_probas(posts, verites))
pires = [abs(s["conf"] - s["just"]) for s in diag if s["n"] >= 80]
check(f"chaque tranche bien peuplée proche diagonale (max {max(pires):.3f} <= 0.10)", max(pires) <= 0.10)

print("=== PRIOR RESPECTÉ + MONOTONIE + BORNES ===")
check("aucun indice -> postérieure = prior", abs(B.posterior(0.42, [])[1] - 0.42) < 1e-12)
p1 = B.posterior(0.2, [(0.9, 0.2, 1)])[1]
p2 = B.posterior(0.2, [(0.9, 0.2, 1), (0.85, 0.25, 1)])[1]
check("plus d'indices confirmants -> postérieure plus haute (monotonie)", p2 > p1)
pn = B.posterior(0.2, [(0.9, 0.2, 0)])[1]
check("indice infirmant -> postérieure sous le prior", pn < 0.2)
check("postérieure toujours dans (0,1)", all(0.0 < x < 1.0 for x in posts))

print("=== REFUS DU DÉGÉNÉRÉ (anti-fausse-certitude) ===")
check("prior=0 -> ABSTENTION", B.posterior(0.0, [(0.9, 0.2, 1)])[0] == ABSTENTION)
check("prior=1 -> ABSTENTION", B.posterior(1.0, [(0.9, 0.2, 1)])[0] == ABSTENTION)
check("vraisemblance=1 -> ABSTENTION (impossible affirmé)", B.posterior(0.3, [(1.0, 0.2, 1)])[0] == ABSTENTION)
check("vraisemblance=0 -> ABSTENTION", B.posterior(0.3, [(0.0, 0.2, 1)])[0] == ABSTENTION)

print("=== CAVEAT MESURÉ : indices CORRÉLÉS -> SUR-CONFIANT (on l'expose, on ne le cache pas) ===")
# 4 indices redondants (copie du même signal) traités comme indépendants -> over-counting -> sur-confiance.
posts_c, verites_c = simule(0.30, specs, 8000, graine=2, correle=True)
conf_c, just_c = CAL.depuis_probas(posts_c, verites_c)
vc, ic = CAL.est_calibre(conf_c, just_c)
print("   ", CAL.formule((vc, ic), "forecast"))
check(f"indices corrélés traités en indépendants -> SURCONFIANT (démasqué par calibration.py, ece={ic['ece']:.3f})",
      vc == SURCONFIANT)

print("=== maj_log_odds bas-niveau cohérente avec posterior ===")
lr = B.lr_indice(0.9, 0.2, 1)
direct = B.maj_log_odds(0.2, [lr])[1]
via = B.posterior(0.2, [(0.9, 0.2, 1)])[1]
check("maj_log_odds(prior,[lr]) == posterior(prior,[indice])", abs(direct - via) < 1e-12)

print(f"\nBAYES VALIDÉ — {ok}/{total}." if ok == total else f"\nÉCHEC {ok}/{total}")
