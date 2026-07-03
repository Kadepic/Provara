"""
VALIDE budget_personnel.py — held-out ADVERSE.

Ancres CONNUES (arithmétique vérifiée à la main + conventions sourcées, NON circulaires) :
  • solde          : 2000−1500 = 500 (spéc) ; 3000−3000 = 0 ; 1000−1500 = −500 (déficit) ; 2500.50−1200.25 = 1300.25
  • taux_epargne   : 500/2000 = 25 % (spéc) ; 0/2000 = 0 % ; 2000/2000 = 100 % (borne) ; 300/1500 = 20 % ; 750/3000 = 25 %
  • regle_50_30_20 : sur 2000 -> {1000, 600, 400} (spéc) ; sur 3000 -> {1500, 900, 600} ; somme = revenus
  • capacite_emprunt : 2000·0.35 = 700 (spéc, 35 %) ; 3000·0.35 = 1050 ; 3000·0.33 = 990 ; 1000·1.0 = 1000 (borne)
  • reste_a_vivre  : 2000−1500 = 500 ; 2000−800 = 1200 ; 1000−1200 = −200 (déficit)
  • cohérence croisée : besoins+envies+epargne == revenus ; solde(R, dépenses=besoins+envies) == épargne 50/30/20.
SOUNDNESS : revenus <= 0, montant négatif, epargne > revenus, taux_endettement hors ]0,1],
            valeur non finie / non numérique / booléen -> ValueError (jamais un faux).
DÉTERMINISME : mêmes entrées -> mêmes sorties.
"""

import budget_personnel as M

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


# ── 1) solde = revenus − depenses (peut être négatif) ──
check(M.solde(2000, 1500) == 500.0, "solde(2000,1500) = 500 (spéc)")
check(M.solde(3000, 3000) == 0.0, "solde(3000,3000) = 0 (équilibre)")
check(M.solde(1000, 1500) == -500.0, "solde(1000,1500) = −500 (déficit, résultat réel)")
check(approx(M.solde(2500.50, 1200.25), 1300.25), "solde(2500.50,1200.25) = 1300.25")
check(M.solde(2000, 0) == 2000.0, "solde(2000,0) = 2000")

# ── 2) taux_epargne = epargne / revenus * 100 ──
check(M.taux_epargne(500, 2000) == 25.0, "taux_epargne(500,2000) = 25 % (spéc)")
check(M.taux_epargne(0, 2000) == 0.0, "taux_epargne(0,2000) = 0 %")
check(M.taux_epargne(2000, 2000) == 100.0, "taux_epargne(2000,2000) = 100 % (borne)")
check(M.taux_epargne(300, 1500) == 20.0, "taux_epargne(300,1500) = 20 %")
check(M.taux_epargne(750, 3000) == 25.0, "taux_epargne(750,3000) = 25 %")

# ── 3) regle_50_30_20 -> {besoins 0.5R, envies 0.3R, epargne 0.2R} ──
r2000 = M.regle_50_30_20(2000)
check(r2000 == {"besoins": 1000.0, "envies": 600.0, "epargne": 400.0}, "50/30/20 sur 2000 (spéc)")
r3000 = M.regle_50_30_20(3000)
check(r3000 == {"besoins": 1500.0, "envies": 900.0, "epargne": 600.0}, "50/30/20 sur 3000")
check(approx(r2000["besoins"] + r2000["envies"] + r2000["epargne"], 2000.0), "somme 50/30/20 = revenus (2000)")
check(approx(M.regle_50_30_20(5000)["besoins"] + M.regle_50_30_20(5000)["envies"]
             + M.regle_50_30_20(5000)["epargne"], 5000.0), "somme 50/30/20 = revenus (5000)")
check(r2000["besoins"] == 0.5 * 2000, "besoins = 0.5·R")
check(r2000["envies"] == 0.3 * 2000, "envies = 0.3·R")
check(r2000["epargne"] == 0.2 * 2000, "epargne = 0.2·R")

# ── 4) capacite_emprunt = revenus_mensuels · taux_endettement (35 % par défaut) ──
check(M.capacite_emprunt(2000) == 700.0, "capacite_emprunt(2000) = 700 (35 %, spéc)")
check(M.capacite_emprunt(3000) == 1050.0, "capacite_emprunt(3000) = 1050 (35 %)")
check(M.capacite_emprunt(3000, 0.33) == 990.0, "capacite_emprunt(3000, 0.33) = 990")
check(M.capacite_emprunt(1000, 1.0) == 1000.0, "capacite_emprunt(1000, 1.0) = 1000 (borne)")
check(M.capacite_emprunt(4000, 0.35) == 1400.0, "capacite_emprunt(4000, 0.35) = 1400")

# ── 5) reste_a_vivre = revenus − charges_fixes (peut être négatif) ──
check(M.reste_a_vivre(2000, 1500) == 500.0, "reste_a_vivre(2000,1500) = 500")
check(M.reste_a_vivre(2000, 800) == 1200.0, "reste_a_vivre(2000,800) = 1200")
check(M.reste_a_vivre(1000, 1200) == -200.0, "reste_a_vivre(1000,1200) = −200 (déficit)")

# ── 6) cohérence croisée ──
check(approx(M.solde(2000, r2000["besoins"] + r2000["envies"]), r2000["epargne"]),
      "solde(R, besoins+envies) = épargne 50/30/20")
check(M.reste_a_vivre(2000, 1500) == M.solde(2000, 1500), "reste_a_vivre == solde quand charges = dépenses")

# ── 7) SOUNDNESS — revenus <= 0 (toutes les fonctions) ──
check(_leve_v(M.solde, 0, 100), "solde revenus = 0 -> ValueError")
check(_leve_v(M.solde, -5, 100), "solde revenus < 0 -> ValueError")
check(_leve_v(M.taux_epargne, 100, 0), "taux_epargne revenus = 0 -> ValueError")
check(_leve_v(M.taux_epargne, 100, -5), "taux_epargne revenus < 0 -> ValueError")
check(_leve_v(M.regle_50_30_20, 0), "regle_50_30_20 revenus = 0 -> ValueError")
check(_leve_v(M.regle_50_30_20, -1), "regle_50_30_20 revenus < 0 -> ValueError")
check(_leve_v(M.capacite_emprunt, 0), "capacite_emprunt revenus = 0 -> ValueError")
check(_leve_v(M.capacite_emprunt, -100), "capacite_emprunt revenus < 0 -> ValueError")
check(_leve_v(M.reste_a_vivre, 0, 100), "reste_a_vivre revenus = 0 -> ValueError")
check(_leve_v(M.reste_a_vivre, -1, 100), "reste_a_vivre revenus < 0 -> ValueError")

# ── 8) SOUNDNESS — montants négatifs ──
check(_leve_v(M.solde, 2000, -1), "solde depenses < 0 -> ValueError")
check(_leve_v(M.reste_a_vivre, 2000, -1), "reste_a_vivre charges_fixes < 0 -> ValueError")
check(_leve_v(M.taux_epargne, -1, 2000), "taux_epargne epargne < 0 -> ValueError")

# ── 9) SOUNDNESS — épargne > revenus (taux > 100 % impossible) ──
check(_leve_v(M.taux_epargne, 2001, 2000), "epargne > revenus -> ValueError")
check(_leve_v(M.taux_epargne, 3000, 2000), "epargne franchement > revenus -> ValueError")

# ── 10) SOUNDNESS — taux_endettement hors ]0, 1] ──
check(_leve_v(M.capacite_emprunt, 2000, 0), "taux_endettement = 0 -> ValueError")
check(_leve_v(M.capacite_emprunt, 2000, -0.1), "taux_endettement < 0 -> ValueError")
check(_leve_v(M.capacite_emprunt, 2000, 1.5), "taux_endettement > 1 -> ValueError")

# ── 11) SOUNDNESS — valeurs non finies / non numériques / booléen ──
check(_leve_v(M.solde, float("nan"), 100), "solde revenus NaN -> ValueError")
check(_leve_v(M.solde, 2000, float("inf")), "solde depenses inf -> ValueError")
check(_leve_v(M.taux_epargne, 100, float("inf")), "taux_epargne revenus inf -> ValueError")
check(_leve_v(M.capacite_emprunt, "deux"), "capacite_emprunt revenus non numérique -> ValueError")
check(_leve_v(M.reste_a_vivre, None, 5), "reste_a_vivre revenus None -> ValueError")
check(_leve_v(M.solde, True, 100), "solde revenus booléen -> ValueError")
check(_leve_v(M.capacite_emprunt, 2000, float("nan")), "capacite_emprunt taux NaN -> ValueError")
check(_leve_v(M.regle_50_30_20, "mille"), "regle_50_30_20 revenus non numérique -> ValueError")

# ── 12) DÉTERMINISME ──
check(M.solde(2000, 1500) == M.solde(2000, 1500), "solde déterministe")
check(M.taux_epargne(500, 2000) == M.taux_epargne(500, 2000), "taux_epargne déterministe")
check(M.regle_50_30_20(2000) == M.regle_50_30_20(2000), "regle_50_30_20 déterministe")
check(M.capacite_emprunt(2000) == M.capacite_emprunt(2000), "capacite_emprunt déterministe")
check(M.reste_a_vivre(2000, 1500) == M.reste_a_vivre(2000, 1500), "reste_a_vivre déterministe")

print(f"\n=== valide_budget_personnel : {ok}/{ok+ko} ===")
import sys
sys.exit(0 if ko == 0 else 1)
