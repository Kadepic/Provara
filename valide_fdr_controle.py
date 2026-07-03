"""
VALIDATION du CONTRÔLE DU FDR (fdr_controle.py) — jugé par calibration.py. K=200 tests (m1=30 vrais effets, signal z~N(μ,1) ;
170 nuls z~N(0,1)), tirages répétés. Le seuil NAÏF α voit son FDR EXPLOSER (parmi ses découvertes, la proportion réelles
< 1−q → SUR-CONFIANT sur les résultats) ; BENJAMINI-HOCHBERG garde le FDR ≤ q (proportion réelles ≥ 1−q) avec PLUS de
puissance que Bonferroni.
"""
from __future__ import annotations

import math
import random

from garde_ressources import borne
import fdr_controle as F
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


def _Phi(z):
    return 0.5 * (1 + math.erf(z / math.sqrt(2)))


K = 200
M1 = 30
MU = 3.0
Q = 0.10
N_REP = 400


def jeu(rng):
    pv, vrai = [], []
    for j in range(K):
        if j < M1:
            z = rng.gauss(MU, 1.0); vrai.append(True)
        else:
            z = rng.gauss(0.0, 1.0); vrai.append(False)
        pv.append(1 - _Phi(z))           # p-valeur unilatérale
    return pv, vrai


rng = random.Random(4)
fdr_naif, fdr_bh = [], []
pow_bh, pow_bonf = [], []
conf_naif, just_naif, conf_bh, just_bh = [], [], [], []
for _ in range(N_REP):
    pv, vrai = jeu(rng)
    dn = F.naif(pv, Q)
    db = F.benjamini_hochberg(pv, Q)
    dbf = F.bonferroni(pv, Q)
    if dn:
        fp = sum(1 for i in dn if not vrai[i]); fdr_naif.append(fp / len(dn))
        for i in dn:
            conf_naif.append(1 - Q); just_naif.append(1.0 if vrai[i] else 0.0)
    if db:
        fp = sum(1 for i in db if not vrai[i]); fdr_bh.append(fp / len(db))
        for i in db:
            conf_bh.append(1 - Q); just_bh.append(1.0 if vrai[i] else 0.0)
    pow_bh.append(sum(1 for i in db if vrai[i]) / M1)
    pow_bonf.append(sum(1 for i in dbf if vrai[i]) / M1)

m_fdr_naif = sum(fdr_naif) / len(fdr_naif)
m_fdr_bh = sum(fdr_bh) / len(fdr_bh)
print(f"=== FDR moyen (q={Q}) ===")
print(f"   naïf={m_fdr_naif:.3f} ; Benjamini-Hochberg={m_fdr_bh:.3f}")
check("seuil naïf : FDR moyen >> q (sur-confiance sur les découvertes)", m_fdr_naif > Q + 0.05)
check("Benjamini-Hochberg : FDR moyen contrôlé ≤ q (+petite marge)", m_fdr_bh <= Q + 0.03)

print("=== Jugement calibration.py : précision des découvertes (justesse vs confiance 1−q) ===")
vNa, iNa = CAL.est_calibre(conf_naif, just_naif, n_bins=5)
vBh, iBh = CAL.est_calibre(conf_bh, just_bh, n_bins=5)
print(f"   naïf : précision={sum(just_naif)/len(just_naif):.3f} ({vNa}) ; BH : précision={sum(just_bh)/len(just_bh):.3f} ({vBh})")
check("découvertes naïves SUR-CONFIANTES (précision < 1−q)", vNa == SURCONFIANT)
check("découvertes BH NON sur-confiantes (précision ≥ 1−q)", vBh != SURCONFIANT)

print("=== Puissance : BH détecte plus de vrais effets que Bonferroni ===")
mp_bh = sum(pow_bh) / len(pow_bh)
mp_bonf = sum(pow_bonf) / len(pow_bonf)
print(f"   puissance moyenne : BH={mp_bh:.3f} vs Bonferroni={mp_bonf:.3f}")
check("BH plus puissant que Bonferroni (à FDR maîtrisé)", mp_bh > mp_bonf + 0.05)

print("=== Sous le NUL complet (aucun vrai effet) : BH ne découvre presque rien ===")
rng2 = random.Random(11)
faux_decouvertes = 0
for _ in range(200):
    pv = [rng2.random() for _ in range(K)]
    faux_decouvertes += len(F.benjamini_hochberg(pv, Q))
print(f"   découvertes BH totales sous H0 complet (200 jeux) = {faux_decouvertes}")
check("BH quasi muet sous le nul complet (≤ q·K·jeux en moyenne)", faux_decouvertes <= Q * K * 200 * 0.5)

print("=== ABSTENTION si aucune p-valeur ===")
st, _, raison = F.decouvre([], Q, "bh")
print(f"   {st} : {raison}")
check("ABSTENTION si liste vide", st == "abstention")

print(f"\nRÉSULTAT fdr_controle : {ok}/{total}")
assert ok == total
