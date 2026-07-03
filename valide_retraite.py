"""
VALIDE retraite.py — held-out ADVERSE.

Ancres CONNUES (mécanisme par annuités + arithmétique vérifiée à la main, NON circulaires) :
  • pension (taux plein, coeff=1)  : 2000 · 0.5 · (160/160) = 1000
  • pension (prorata ½)            : 2000 · 0.5 · (80/160)  = 500
  • pension (prorata ¾)            : 2000 · 0.75 · (120/160) = 1125
  • pension (taux=1, complet)      : 2000 · 1.0 · (166/166) = 2000 (taux plein, taux=100 %)
  • coefficient_proratisation      : 80/160 = 0.5 ; 160/160 = 1.0 ; 166/166 = 1.0
  • taux_remplacement              : 1000/2000 = 50 % ; 1500/2000 = 75 % ; 2000/2000 = 100 %
  • decote                         : 8 · 0.0125 = 0.10 (10 %) ; 0 · x = 0 ; 20 · 0.00625 = 0.125
  • cohérence croisée              : pension puis taux_remplacement vs salaire = taux_liquidation·coeff·100.
SOUNDNESS : durée <= 0, taux hors [0,1], montant < 0, dernier_salaire <= 0, trimestres < 0 ou non entier,
            valeur non finie / non numérique / booléen -> ValueError (jamais un faux).
DÉTERMINISME : mêmes entrées -> mêmes sorties.
"""

import retraite as M

ok = 0
ko = 0


def check(cond, label):
    global ok, ko
    if cond:
        ok += 1
    else:
        ko += 1
        print(f"  FAIL: {label}")


def _leve_v(fn, *a, **k):
    try:
        fn(*a, **k)
        return False
    except ValueError:
        return True
    except Exception:
        return False


def approx(v, attendu, tol=1e-9):
    return v is not None and abs(v - attendu) <= tol


# ── 1) pension — TAUX PLEIN (coefficient = 1) ──
check(approx(M.pension(2000.0, 0.5, 160, 160), 1000.0), "2000·0.5·(160/160) = 1000 (taux plein)")
check(approx(M.pension(2000.0, 1.0, 166, 166), 2000.0), "2000·1.0·(166/166) = 2000 (taux 100 %, complet)")
check(approx(M.pension(3000.0, 0.5, 41.5, 41.5), 1500.0), "durée==requise (années) -> taux plein 1500")

# ── 2) pension — PRORATA (durée incomplète) ──
check(approx(M.pension(2000.0, 0.5, 80, 160), 500.0), "2000·0.5·(80/160) = 500 (½ durée)")
check(approx(M.pension(2000.0, 0.75, 120, 160), 1125.0), "2000·0.75·(120/160) = 1125 (¾ durée)")
check(approx(M.pension(1200.0, 0.5, 100, 160), 375.0), "1200·0.5·(100/160) = 375")
check(approx(M.pension(0.0, 0.5, 80, 160), 0.0), "salaire 0 -> pension 0")
check(approx(M.pension(2000.0, 0.0, 160, 160), 0.0), "taux 0 -> pension 0")

# ── 3) coefficient_proratisation ──
check(approx(M.coefficient_proratisation(80, 160), 0.5), "80/160 = 0.5")
check(approx(M.coefficient_proratisation(160, 160), 1.0), "160/160 = 1.0 (plein)")
check(approx(M.coefficient_proratisation(166, 166), 1.0), "166/166 = 1.0")
check(approx(M.coefficient_proratisation(120, 160), 0.75), "120/160 = 0.75")

# ── 4) taux_remplacement = pension / salaire * 100 ──
check(approx(M.taux_remplacement(1000.0, 2000.0), 50.0), "1000/2000 = 50 % (cas spéc)")
check(approx(M.taux_remplacement(1500.0, 2000.0), 75.0), "1500/2000 = 75 %")
check(approx(M.taux_remplacement(2000.0, 2000.0), 100.0), "2000/2000 = 100 %")
check(approx(M.taux_remplacement(0.0, 2000.0), 0.0), "0/2000 = 0 %")

# ── 5) decote — proportionnelle ──
check(approx(M.decote(8, 0.0125), 0.1), "8·0.0125 = 0.10 (10 %)")
check(approx(M.decote(0, 0.0125), 0.0), "0 trimestre -> décote nulle")
check(approx(M.decote(20, 0.00625), 0.125), "20·0.00625 = 0.125 (12.5 %)")
check(approx(M.decote(4, 0.05), 0.2), "4·0.05 = 0.20")

# ── 6) COHÉRENCE CROISÉE — pension puis taux de remplacement ──
# taux_remplacement(pension(sal,taux,da,dr), sal) == taux_liquidation · (da/dr) · 100
sal, taux, da, dr = 2500.0, 0.5, 120, 160
p = M.pension(sal, taux, da, dr)
check(approx(M.taux_remplacement(p, sal), taux * (da / dr) * 100.0),
      "taux_remplacement(pension, salaire) = taux·coeff·100")
# au taux plein, le taux de remplacement vaut exactement le taux de liquidation ·100
p_plein = M.pension(sal, taux, 160, 160)
check(approx(M.taux_remplacement(p_plein, sal), taux * 100.0), "taux plein -> remplacement = taux·100")

# ── 7) SOUNDNESS — durées <= 0 ──
check(_leve_v(M.pension, 2000.0, 0.5, 0, 160), "duree_assurance = 0 -> ValueError")
check(_leve_v(M.pension, 2000.0, 0.5, -10, 160), "duree_assurance < 0 -> ValueError")
check(_leve_v(M.pension, 2000.0, 0.5, 160, 0), "duree_requise = 0 -> ValueError")
check(_leve_v(M.pension, 2000.0, 0.5, 160, -160), "duree_requise < 0 -> ValueError")
check(_leve_v(M.coefficient_proratisation, 160, 0), "duree_requise = 0 (coeff) -> ValueError")
check(_leve_v(M.coefficient_proratisation, 0, 160), "duree_assurance = 0 (coeff) -> ValueError")

# ── 8) SOUNDNESS — taux hors [0, 1] ──
check(_leve_v(M.pension, 2000.0, 1.5, 160, 160), "taux_liquidation > 1 -> ValueError")
check(_leve_v(M.pension, 2000.0, -0.1, 160, 160), "taux_liquidation < 0 -> ValueError")
check(_leve_v(M.decote, 8, 1.5), "taux_decote > 1 -> ValueError")
check(_leve_v(M.decote, 8, -0.01), "taux_decote < 0 -> ValueError")

# ── 9) SOUNDNESS — montants / dénominateur ──
check(_leve_v(M.pension, -2000.0, 0.5, 160, 160), "salaire_reference < 0 -> ValueError")
check(_leve_v(M.taux_remplacement, -1.0, 2000.0), "pension < 0 -> ValueError")
check(_leve_v(M.taux_remplacement, 1000.0, 0.0), "dernier_salaire = 0 -> ValueError")
check(_leve_v(M.taux_remplacement, 1000.0, -2000.0), "dernier_salaire < 0 -> ValueError")

# ── 10) SOUNDNESS — trimestres invalides ──
check(_leve_v(M.decote, -8, 0.0125), "trimestres_manquants < 0 -> ValueError")
check(_leve_v(M.decote, 8.5, 0.0125), "trimestres_manquants non entier -> ValueError")

# ── 11) SOUNDNESS — valeurs non finies / non numériques / booléen ──
check(_leve_v(M.pension, float("nan"), 0.5, 160, 160), "salaire NaN -> ValueError")
check(_leve_v(M.pension, 2000.0, float("inf"), 160, 160), "taux inf -> ValueError")
check(_leve_v(M.pension, 2000.0, 0.5, float("nan"), 160), "durée NaN -> ValueError")
check(_leve_v(M.pension, "deux mille", 0.5, 160, 160), "salaire non numérique -> ValueError")
check(_leve_v(M.pension, 2000.0, True, 160, 160), "taux booléen -> ValueError")
check(_leve_v(M.taux_remplacement, None, 2000.0), "pension None -> ValueError")
check(_leve_v(M.decote, True, 0.0125), "trimestres booléen -> ValueError")
check(_leve_v(M.decote, 8, float("nan")), "taux_decote NaN -> ValueError")

# ── 12) DÉTERMINISME ──
check(M.pension(2000.0, 0.5, 80, 160) == M.pension(2000.0, 0.5, 80, 160), "pension déterministe")
check(M.taux_remplacement(1000.0, 2000.0) == M.taux_remplacement(1000.0, 2000.0), "taux_remplacement déterministe")
check(M.decote(8, 0.0125) == M.decote(8, 0.0125), "decote déterministe")
check(M.coefficient_proratisation(80, 160) == M.coefficient_proratisation(80, 160), "coeff déterministe")

print(f"\n=== valide_retraite : {ok}/{ok+ko} ===")
import sys
sys.exit(0 if ko == 0 else 1)
