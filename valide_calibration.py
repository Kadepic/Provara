"""
VALIDATION de l'INSTRUMENT DE CALIBRATION (calibration.py) — le juge du Palier 2 se juge LUI-MÊME par MONTE-CARLO.

Preuve par simulation d'un monde CONNU : on FABRIQUE des forecasters dont on connaît la vraie justesse, puis on
vérifie que l'instrument NOMME correctement leur honnêteté :
  • un forecaster CALIBRÉ (confiance c -> juste à Bernoulli(c))            -> verdict CALIBRE, ECE faible.
  • un forecaster SUR-CONFIANT (confiance gonflée vers 1, justesse inchangée) -> verdict SURCONFIANT (LIGNE ROUGE).
  • un forecaster SOUS-CONFIANT (confiance écrasée vers 0.5)               -> verdict SOUSCONFIANT (prudent).
  • trop peu de cas                                                        -> ABSTENTION (pas de faux jugement).
Plus : Brier propre (calibré < sur-confiant), monotonie ECE/MCE, conversion depuis_probas, et — pont vital —
l'instrument JUGE le vrai estimateur d'intervalle de incertitude.py (estime_proportion) et le déclare CALIBRE,
tandis qu'un intervalle DÉLIBÉRÉMENT trop étroit est démasqué SURCONFIANT.

LIGNE ROUGE de CE module : si l'instrument laissait passer un sur-confiant comme « calibré », il serait aussi
inutile qu'un FAUX en P1. Le test ci-dessous l'INTERDIT.
"""
from __future__ import annotations

import random

from garde_ressources import borne
import calibration as CAL
from calibration import (CALIBRE, SURCONFIANT, SOUSCONFIANT, ABSTENTION)
import incertitude as INC

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


def fabrique_confiances(transforme, n, graine):
    """Fabrique n couples (confiance annoncée, justesse 0/1) : on tire une confiance VRAIE c ∈ [0.5,1], la réponse
    est juste à Bernoulli(c) (réalité), puis on ANNONCE transforme(c). transforme=identité -> calibré."""
    rng = random.Random(graine)
    conf, just = [], []
    for _ in range(n):
        c_vrai = 0.5 + 0.5 * rng.random()
        juste = 1 if rng.random() < c_vrai else 0
        conf.append(max(0.0, min(1.0, transforme(c_vrai))))
        just.append(juste)
    return conf, just


print("=== FORECASTER CALIBRÉ -> CALIBRE (l'honnête passe) ===")
c, j = fabrique_confiances(lambda x: x, 4000, graine=1)
v, infos = CAL.est_calibre(c, j)
print("   ", CAL.formule((v, infos), "forecast"))
check(f"calibré -> verdict CALIBRE (ece={infos['ece']:.3f})", v == CALIBRE)
check(f"calibré : ECE faible ({infos['ece']:.3f} <= 0.03)", infos["ece"] <= 0.03)
check(f"calibré : écart signé ≈ 0 (|{infos['ecart_signe']:.3f}| <= 0.03)", abs(infos["ecart_signe"]) <= 0.03)

print("=== FORECASTER SUR-CONFIANT -> SURCONFIANT (LA LIGNE ROUGE : le menteur est démasqué) ===")
c, j = fabrique_confiances(lambda x: x + 0.6 * (1 - x), 4000, graine=2)   # gonfle la confiance vers 1
v, infos = CAL.est_calibre(c, j)
print("   ", CAL.formule((v, infos), "forecast"))
check("sur-confiant -> verdict SURCONFIANT", v == SURCONFIANT)
check(f"sur-confiant : écart signé > 0 ({infos['ecart_signe']:.3f} > 0.05)", infos["ecart_signe"] > 0.05)
check(f"sur-confiant : ECE élevé ({infos['ece']:.3f} > 0.05)", infos["ece"] > 0.05)

print("=== FORECASTER SOUS-CONFIANT -> SOUSCONFIANT (le prudent est nommé, mais NON ROUGE) ===")
c, j = fabrique_confiances(lambda x: 0.5 + 0.4 * (x - 0.5), 4000, graine=3)  # écrase vers 0.5
v, infos = CAL.est_calibre(c, j)
print("   ", CAL.formule((v, infos), "forecast"))
check("sous-confiant -> verdict SOUSCONFIANT", v == SOUSCONFIANT)
check(f"sous-confiant : écart signé < 0 ({infos['ecart_signe']:.3f} < -0.05)", infos["ecart_signe"] < -0.05)

print("=== ABSTENTION (trop peu de cas -> pas de faux jugement) ===")
c, j = fabrique_confiances(lambda x: x, 20, graine=4)
check(f"n=20 < {CAL.N_MIN_CAL} -> ABSTENTION", CAL.est_calibre(c, j)[0] == ABSTENTION)
c, j = fabrique_confiances(lambda x: x, CAL.N_MIN_CAL, graine=5)
check(f"n={CAL.N_MIN_CAL} -> verdict émis (pas d'abstention)", CAL.est_calibre(c, j)[0] != ABSTENTION)

print("=== BRIER = RÈGLE DE SCORE PROPRE (le calibré bat le sur-confiant) ===")
c_cal, j_cal = fabrique_confiances(lambda x: x, 4000, graine=6)
c_sur, _ = fabrique_confiances(lambda x: x + 0.6 * (1 - x), 4000, graine=6)   # MÊME justesse, confiance gonflée
b_cal = CAL.brier(c_cal, j_cal)
b_sur = CAL.brier(c_sur, j_cal)
check(f"Brier calibré ({b_cal:.3f}) < Brier sur-confiant ({b_sur:.3f})", b_cal < b_sur)
check("Brier ∈ [0,1] (calibré)", 0.0 <= b_cal <= 1.0)

print("=== ECE <= MCE (cohérence des deux mesures) ===")
c, j = fabrique_confiances(lambda x: x + 0.3 * (1 - x), 3000, graine=7)
e, m = CAL.ece(c, j), CAL.mce(c, j)
check(f"ECE ({e:.3f}) <= MCE ({m:.3f})", e <= m + 1e-9)

print("=== DIAGRAMME DE FIABILITÉ : conf ≈ just sur le calibré, conf > just sur le sur-confiant ===")
c, j = fabrique_confiances(lambda x: x, 6000, graine=8)
diag = CAL.diagramme_fiabilite(c, j)
# tranches bien peuplées : |conf - just| petit
pires = [abs(s["conf"] - s["just"]) for s in diag if s["n"] >= 50]
check(f"calibré : toutes tranches peuplées proches diagonale (max écart {max(pires):.3f} <= 0.10)", max(pires) <= 0.10)

print("=== depuis_probas : conversion forecast binaire -> (confiance, justesse) ===")
# p=0.9 et y=1 -> prédit 1, juste, confiance 0.9 ; p=0.2 et y=0 -> prédit 0, juste, confiance 0.8
conf, just = CAL.depuis_probas([0.9, 0.2, 0.6, 0.1], [1, 0, 0, 1])
check("depuis_probas confiances = [0.9,0.8,0.6,0.9]", conf == [0.9, 0.8, 0.6, 0.9])
check("depuis_probas justesses = [1,1,0,0]", just == [1, 1, 0, 0])
# un forecast de proba calibré reste calibré après conversion
rng = random.Random(9)
P = [rng.random() for _ in range(4000)]
Y = [1 if rng.random() < p else 0 for p in P]
vc, ic = CAL.est_calibre(*CAL.depuis_probas(P, Y))
check(f"forecast proba calibré -> CALIBRE après depuis_probas (ece={ic['ece']:.3f})", vc == CALIBRE)

print("=== PONT : l'instrument JUGE le vrai estimateur d'intervalle de incertitude.py ===")
# estime_proportion (Wilson) sur des échantillons simulés : on collecte (intervalle, vérité p) et on JUGE.
def intervalles_proportion(p_vrai, n, conf, M, graine):
    rng = random.Random(graine)
    inter, ver = [], []
    for _ in range(M):
        ech = [1 if rng.random() < p_vrai else 0 for _ in range(n)]
        st, res, _ = INC.estime_proportion(ech, conf)
        if st == INC.ESTIMATION:
            inter.append(res[1])
            ver.append(p_vrai)
    return inter, ver
inter, ver = intervalles_proportion(0.4, 50, 0.90, 800, graine=10)
v, infos = CAL.verdict_couverture(inter, ver, 0.90)
print("   ", CAL.formule((v, infos), "couverture"))
check(f"estime_proportion @90% jugé CALIBRE par l'instrument (couv={infos['couverture']:.3f})", v == CALIBRE)

print("=== L'instrument DÉMASQUE un intervalle délibérément trop étroit (SURCONFIANT) ===")
# on prend l'intervalle de Wilson et on le RÉTRÉCIT de moitié autour du centre -> doit sous-couvrir.
inter_etroit = []
for (b, h) in inter:
    centre = (b + h) / 2
    inter_etroit.append((centre - (h - b) / 4, centre + (h - b) / 4))
v2, infos2 = CAL.verdict_couverture(inter_etroit, ver, 0.90)
print("   ", CAL.formule((v2, infos2), "couverture"))
check(f"intervalle moitié-largeur @90% -> SURCONFIANT (couv={infos2['couverture']:.3f} < 0.85)", v2 == SURCONFIANT)

print("=== Et un intervalle trop LARGE (prudent) -> SOUSCONFIANT ===")
inter_large = [(b - (h - b), h + (h - b)) for (b, h) in inter]   # triple la largeur
v3, infos3 = CAL.verdict_couverture(inter_large, ver, 0.90)
check(f"intervalle triple-largeur @90% -> SOUSCONFIANT (couv={infos3['couverture']:.3f})", v3 == SOUSCONFIANT)

print(f"\nCALIBRATION VALIDÉ — {ok}/{total}." if ok == total else f"\nÉCHEC {ok}/{total}")
