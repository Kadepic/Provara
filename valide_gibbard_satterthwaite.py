"""
VALIDATION de GIBBARD-SATTERTHWAITE (gibbard_satterthwaite.py). Vérifie : le profil par défaut est MANIPULABLE (un votant
ment et obtient un gagnant qu'il préfère) ; la manipulation fonctionne réellement (le faux bulletin change le gagnant) ;
la manipulabilité n'est pas isolée (fraction substantielle de profils aléatoires) ; HONNÊTETÉ : la majorité à 2
candidats est NON manipulable (l'impossibilité requiert ≥3) ; l'ABSTENTION. Pur Python, rng seedé.
"""
from __future__ import annotations

import random

from garde_ressources import borne
import gibbard_satterthwaite as GS
from gibbard_satterthwaite import ABSTENTION, ANALYSE

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


cands = ["A", "B", "C"]
st, info = GS.analyse()

# ─── 1. Profil manipulable ───
print("=== Le profil par défaut est manipulable ===")
print(f"   gagnant sincère={info['gagnant_sincere']} ; manipulation={info['manipulation']}")
check("le profil est manipulable (manipulation trouvée)", info["manipulable"])
v, faux, w, sinc = info["manipulation"]
check("le votant manipulateur préfère le gagnant manipulé au gagnant sincère", GS.prefere(info["profil"][v], w, sinc))

# ─── 2. La manipulation fonctionne vraiment ───
print("=== La manipulation change effectivement le gagnant ===")
profil = info["profil"]
p2 = [list(r) for r in profil]
p2[v] = list(faux)
w_recalc = GS.borda(p2, cands)
print(f"   gagnant avec faux bulletin={w_recalc} (≠ sincère {sinc})")
check("le faux bulletin produit bien le gagnant manipulé", w_recalc == w)
check("le faux bulletin diffère du vrai classement (c'est un mensonge)", list(faux) != list(profil[v]))
check("sans manipulation, le gagnant sincère reste celui annoncé", GS.borda(profil, cands) == sinc)

# ─── 3. La manipulabilité n'est pas un cas isolé ───
print("=== Manipulabilité répandue ===")
taux = GS.taux_manipulables(GS.borda, cands, 4, 1500, random.Random(128))
print(f"   fraction de profils manipulables (Borda, 4 votants) = {taux:.2f}")
check("une fraction substantielle des profils est manipulable", taux > 0.2)
# pluralité aussi manipulable
taux_plu = GS.taux_manipulables(GS.pluralite, cands, 5, 1500, random.Random(2))
check("la pluralité est aussi manipulable", taux_plu > 0.05)

# ─── 4. Honnêteté : majorité à 2 candidats NON manipulable ───
print("=== Honnêteté : majorité à 2 candidats strategyproof ===")
taux2 = GS.taux_manipulables(GS.majorite2, ["A", "B"], 5, 2000, random.Random(3))
print(f"   fraction manipulable à 2 candidats = {taux2:.3f}")
check("avec 2 candidats, la majorité n'est JAMAIS manipulable (G-S requiert ≥3)", taux2 == 0.0)
check("formule signale la sur-confiance de prendre les bulletins pour le sincère", "sur-confiant" in GS.formule((st, info)))

# ─── 5. ABSTENTION ───
print("=== ABSTENTION ===")
check("< 3 candidats → ABSTENTION", GS.analyse(cands=["A", "B"])[0] == ABSTENTION)
check("cas valide → ANALYSE", st == ANALYSE)

print(f"\nRÉSULTAT gibbard_satterthwaite : {ok}/{total}")
assert ok == total
