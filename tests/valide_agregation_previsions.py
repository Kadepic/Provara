"""
VALIDATION de l'AGRÉGATION DE PRÉVISIONS (agregation_previsions.py) — jugée par calibration.py.
(1) Prévisionnistes à information INDÉPENDANTE : la moyenne des probabilités est SOUS-CONFIANTE (ECE élevé ; dans le bac
    très confiant, la justesse DÉPASSE la confiance) ; l'extrémisation apprise recalibre (ECE chute) et améliore le Brier.
(2) Garde-fou SUR-CONFIANCE : sur des prévisionnistes CORRÉLÉS, extrémiser à l'aveugle par a=nombre-de-prévisionnistes
    SUR-CONFIE ; le facteur a APPRIS (borné) reste calibré.
(3) Antécédents : un prévisionniste pire que le hasard reçoit un poids ≈ 0 ; le Brier pondéré ≤ Brier équipondéré.
"""
from __future__ import annotations

import math
import random

from garde_ressources import borne
import agregation_previsions as AG
from agregation_previsions import ESTIMATION, ABSTENTION, _sigmoid, _logit
import calibration as CAL
from calibration import SURCONFIANT

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


def brier(ps, ys):
    return sum((ps[i] - ys[i]) ** 2 for i in range(len(ys))) / len(ys)


# ---------- (1) Information INDÉPENDANTE ----------
SIG = 1.3
def gen_independant(rng, n):
    prev, ys = [], []
    for _ in range(n):
        s = [rng.gauss(0, SIG) for _ in range(3)]
        y = 1 if rng.random() < _sigmoid(sum(s)) else 0      # vérité = somme des signaux
        prev.append([_sigmoid(si) for si in s]); ys.append(float(y))
    return prev, ys


rng = random.Random(1)
prev, ys = gen_independant(rng, 4000)
hist = [[(prev[i][j], ys[i]) for i in range(len(prev))] for j in range(3)]
mid = 2000
st, info, _ = AG.calibre_agregateur(prev[:mid], ys[:mid], hist)
poids, a = info["poids"], info["a"]
print(f"=== (1) Info indépendante : a appris = {a:.2f} (théorie ≈ 3) ===")
check("extrémisation apprise a > 1.5 (la moyenne était sous-confiante)", a > 1.5)

p_naive = [AG.moyenne_naive(prev[i]) for i in range(mid, len(prev))]
p_ext = [AG.agrege(prev[i], poids, a) for i in range(mid, len(prev))]
yt = ys[mid:]
vN, iN = CAL.est_calibre(p_naive, yt, n_bins=12)
vE, iE = CAL.est_calibre(p_ext, yt, n_bins=12)
print(f"   naïve : ECE={iN['ece']:.3f} ({vN}) ; extrémisée : ECE={iE['ece']:.3f} ({vE})")
check("moyenne naïve MAL calibrée (ECE > 0.1)", iN["ece"] > 0.10)
check("extrémisée bien calibrée (ECE < 0.05) et NON sur-confiante", iE["ece"] < 0.05 and vE != SURCONFIANT)
check("extrémisation améliore le Brier", brier(p_ext, yt) < brier(p_naive, yt))

# sous-confiance directe : dans le bac très confiant, justesse > confiance
conf_haut = [(p_naive[i], yt[i]) for i in range(len(yt)) if p_naive[i] > 0.75]
if conf_haut:
    cmoy = sum(p for p, _ in conf_haut) / len(conf_haut)
    acc = sum(y for _, y in conf_haut) / len(conf_haut)
    print(f"   bac naïf >0.75 : confiance={cmoy:.3f} vs justesse={acc:.3f}")
    check("moyenne naïve SOUS-confiante (justesse > confiance dans le bac confiant)", acc > cmoy + 0.02)
else:
    check("(pas de bac confiant — ignoré)", True)

# ---------- (2) Garde-fou SUR-CONFIANCE sur prévisionnistes CORRÉLÉS ----------
def gen_correle(rng, n):
    prev, ys = [], []
    for _ in range(n):
        c = rng.gauss(0, 1.2)                                # signal COMMUN
        y = 1 if rng.random() < _sigmoid(c) else 0           # vérité = signal commun seul
        prev.append([_sigmoid(c + rng.gauss(0, 0.25)) for _ in range(3)]); ys.append(float(y))
    return prev, ys


rng2 = random.Random(3)
prevC, ysC = gen_correle(rng2, 4000)
histC = [[(prevC[i][j], ysC[i]) for i in range(len(prevC))] for j in range(3)]
stC, infoC, _ = AG.calibre_agregateur(prevC[:mid], ysC[:mid], histC)
poidsC, aC = infoC["poids"], infoC["a"]
p_appris = [AG.agrege(prevC[i], poidsC, aC) for i in range(mid, len(prevC))]
p_aveugle = [AG.agrege(prevC[i], poidsC, 3.0) for i in range(mid, len(prevC))]   # extrémise à l'aveugle par a=n
ytC = ysC[mid:]
iAp = CAL.ece(p_appris, ytC, n_bins=12)
iAv = CAL.ece(p_aveugle, ytC, n_bins=12)


def surconfiance_bac_haut(ps, ys, seuil=0.9):
    """Dans le bac très confiant (p>seuil), confiance moyenne − justesse (positif = sur-confiance)."""
    bac = [(ps[i], ys[i]) for i in range(len(ys)) if ps[i] > seuil]
    if not bac:
        return None
    cmoy = sum(p for p, _ in bac) / len(bac)
    acc = sum(y for _, y in bac) / len(bac)
    return cmoy - acc


sc_aveugle = surconfiance_bac_haut(p_aveugle, ytC)
sc_appris = surconfiance_bac_haut(p_appris, ytC)
print(f"=== (2) Corrélés : a appris={aC:.2f} ; aveugle a=3 ===")
print(f"   ECE appris={iAp:.3f} vs aveugle={iAv:.3f} ; sur-confiance bac>0.9 : aveugle={sc_aveugle:.3f}, appris={sc_appris:.3f}")
check("extrémisation aveugle a=3 SUR-CONFIE (confiance > justesse de >0.05 dans le bac confiant)", sc_aveugle > 0.05)
check("facteur appris (borné) NON sur-confiant dans le bac confiant (|écart|<0.05)", abs(sc_appris) < 0.05)
check("extrémisation aveugle dégrade l'ECE vs apprise", iAv > iAp)
check("a appris < 3 quand les prévisionnistes sont corrélés", aC < 3.0)

# ---------- (3) Antécédents (track record) ----------
print("=== (3) Antécédents : mauvais prévisionniste écarté, Brier pondéré <= équipondéré ===")
taus = [0.5, 0.5, 2.5]                                        # le 3ᵉ est très mauvais
rng3 = random.Random(8)
prevT, ysT, histT = [], [], [[], [], []]
for _ in range(800):
    q = rng3.random()
    ps = [_sigmoid(_logit(q) + rng3.gauss(0, t)) for t in taus]
    y = 1.0 if rng3.random() < q else 0.0
    prevT.append(ps); ysT.append(y)
    for i in range(3):
        histT[i].append((ps[i], y))
poidsT = AG.poids_track_record(histT)
print(f"   Brier = {[round(AG.brier(h),3) for h in histT]} ; poids = {[round(w,3) for w in poidsT]}")
check("le prévisionniste pire que le hasard reçoit un poids ≈ 0", poidsT[2] < 0.05)
p_pond = [_sigmoid(AG.moyenne_logit_ponderee(p, poidsT)) for p in prevT]
p_equi = [_sigmoid(AG.moyenne_logit_ponderee(p, [1/3, 1/3, 1/3])) for p in prevT]
check("Brier pondéré <= Brier équipondéré (les antécédents aident)", brier(p_pond, ysT) <= brier(p_equi, ysT))

print("=== ABSTENTION si historique trop court ===")
st4, _, raison = AG.calibre_agregateur([[0.6, 0.5, 0.4]], [1.0], histT)
print(f"   {st4} : {raison}")
check("ABSTENTION sous N_MIN", st4 == ABSTENTION)

print(f"\nRÉSULTAT agregation_previsions : {ok}/{total}")
assert ok == total
