"""
VALIDATION de la RÉGRESSION FALLACIEUSE (regression_fallacieuse.py). Vérifie : deux marches aléatoires INDÉPENDANTES
donnent un taux de faux positif ≫ 5 % en NIVEAUX (régression fallacieuse) avec un R² spuriously élevé ; DIFFÉRENCIER
rétablit ~5 % ; le BRUIT BLANC stationnaire reste correct (~5 %, honnêteté) ; l'ABSTENTION. Pur Python, rng seedé.
"""
from __future__ import annotations

import random

from garde_ressources import borne
import regression_fallacieuse as RF
from regression_fallacieuse import ABSTENTION, ANALYSE

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


st, info = RF.analyse(n=100, T=3000, rng=random.Random(121))

# ─── 1. Niveaux : faux positif massif ───
print("=== Régression de NIVEAUX (marches aléatoires) ===")
print(f"   taux |t|>1.96 = {info['fp_niveaux']:.3f} (attendu 0.05) ; R² moyen = {info['r2_niveaux']:.3f}")
check("le taux de faux positif en niveaux est massif (≫ 5 %)", info["fp_niveaux"] > 0.5)
check("le R² moyen est spuriously élevé pour des séries indépendantes", info["r2_niveaux"] > 0.1)

# ─── 2. Différences : corrigé ───
print("=== Régression de DIFFÉRENCES ===")
print(f"   taux |t|>1.96 = {info['fp_differences']:.3f}")
check("différencier rétablit un taux de faux positif ≈ 5 %", abs(info["fp_differences"] - 0.05) < 0.02)
check("le taux en différences est BIEN inférieur à celui en niveaux", info["fp_differences"] < info["fp_niveaux"] / 5)

# ─── 3. Bruit blanc stationnaire : OLS correct (honnêteté) ───
print("=== Bruit blanc stationnaire : OLS valide ===")
print(f"   taux |t|>1.96 = {info['fp_bruit_blanc']:.3f}")
check("pour des séries STATIONNAIRES, l'inférence OLS est correcte (~5 %)", abs(info["fp_bruit_blanc"] - 0.05) < 0.02)
check("le problème vient de la NON-STATIONNARITÉ, pas de la régression en soi", info["fp_niveaux"] > 10 * info["fp_bruit_blanc"])

# ─── 4. Façade & formule ───
print("=== Façade ===")
check("formule signale la sur-confiance du t/R² sur séries non-stationnaires", "sur-confiant" in RF.formule((st, info)))
# vérif directe : une seule paire de marches donne souvent un t élevé
rng2 = random.Random(5)
X = RF.marche_aleatoire(150, rng2)
Y = RF.marche_aleatoire(150, rng2)
t_niv, r2_niv = RF.t_et_r2(X, Y)
t_dif, _ = RF.t_et_r2(RF._diff(X), RF._diff(Y))
print(f"   exemple : |t| niveaux={t_niv:.2f} (R²={r2_niv:.2f}) ; |t| différences={t_dif:.2f}")
check("sur cet exemple, le t des niveaux dépasse celui des différences", t_niv > t_dif)

# ─── 5. ABSTENTION ───
print("=== ABSTENTION ===")
check("rng manquant → ABSTENTION", RF.analyse(rng=None)[0] == ABSTENTION)
check("série trop courte → ABSTENTION", RF.analyse(n=5, rng=random.Random(0))[0] == ABSTENTION)
check("cas valide → ANALYSE", st == ANALYSE)

print(f"\nRÉSULTAT regression_fallacieuse : {ok}/{total}")
assert ok == total
