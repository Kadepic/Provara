"""Validateur adversarial de procedes_industriels (FAUX=0)."""
import procedes_industriels as M

ok = 0
ko = 0


def check(cond, label):
    global ok, ko
    if cond:
        ok += 1
    else:
        ko += 1
        print(f"  KO: {label}")


def _leve(fn, *a):
    try:
        fn(*a)
        return False
    except ValueError:
        return True
    except Exception:
        return False


# --- Ancres connues : rendement ---
check(abs(M.rendement(90, 100) - 0.9) < 1e-12, "rendement 90/100 = 0.9")
check(abs(M.rendement(100, 100) - 1.0) < 1e-12, "rendement 100/100 = 1.0")
check(abs(M.rendement(0, 50) - 0.0) < 1e-12, "rendement 0/50 = 0.0")
check(abs(M.rendement(45.0, 90.0) - 0.5) < 1e-12, "rendement 45/90 = 0.5")
check(0.0 <= M.rendement(7, 13) <= 1.0, "rendement dans [0,1]")

# --- Ancres connues : bilan_matiere (Lavoisier) ---
check(M.bilan_matiere([100], [100]) is True, "bilan [100]=[100] conserve")
check(M.bilan_matiere([60, 40], [50, 50]) is True, "bilan 60+40 = 50+50")
check(M.bilan_matiere([100], [90, 10]) is True, "bilan 100 = 90+10")
check(M.bilan_matiere([100], [90]) is False, "bilan 100 != 90 non conserve")
check(M.bilan_matiere([100.0], [100.0 + 1e-9]) is True, "bilan conserve a tol pres")
check(M.bilan_matiere([100.0], [100.5]) is False, "bilan ecart 0.5 non conserve")

# --- Ancres connues : debit_production ---
check(abs(M.debit_production(1000, 10) - 100.0) < 1e-12, "debit 1000/10 = 100")
check(abs(M.debit_production(0, 5) - 0.0) < 1e-12, "debit 0/5 = 0")
check(abs(M.debit_production(7.5, 2.5) - 3.0) < 1e-12, "debit 7.5/2.5 = 3.0")

# --- Ancres connues : taux_conversion ---
check(abs(M.taux_conversion(80, 100) - 0.8) < 1e-12, "conversion 80/100 = 0.8")
check(abs(M.taux_conversion(100, 100) - 1.0) < 1e-12, "conversion totale = 1.0")
check(abs(M.taux_conversion(0, 100) - 0.0) < 1e-12, "conversion nulle = 0.0")

# --- Soundness : abstention sur invalide ---
check(_leve(M.rendement, 90, 0), "rendement denominateur nul -> ValueError")
check(_leve(M.rendement, -1, 100), "rendement reel negatif -> ValueError")
check(_leve(M.rendement, 100, -100), "rendement theorique negatif -> ValueError")
check(_leve(M.rendement, 110, 100), "rendement reel>theorique -> ValueError")
check(_leve(M.rendement, "x", 100), "rendement non-nombre -> ValueError")
check(_leve(M.rendement, True, 100), "rendement bool -> ValueError")
check(_leve(M.rendement, float("nan"), 100), "rendement NaN -> ValueError")
check(_leve(M.rendement, float("inf"), 100), "rendement inf -> ValueError")

check(_leve(M.debit_production, 100, 0), "debit temps nul -> ValueError")
check(_leve(M.debit_production, 100, -5), "debit temps negatif -> ValueError")
check(_leve(M.debit_production, -100, 5), "debit quantite negative -> ValueError")

check(_leve(M.taux_conversion, 80, 0), "conversion initial nul -> ValueError")
check(_leve(M.taux_conversion, -1, 100), "conversion consomme negatif -> ValueError")
check(_leve(M.taux_conversion, 120, 100), "conversion consomme>initial -> ValueError")

check(_leve(M.bilan_matiere, [], [100]), "bilan entrees vide -> ValueError")
check(_leve(M.bilan_matiere, [100], []), "bilan sorties vide -> ValueError")
check(_leve(M.bilan_matiere, [-5], [100]), "bilan flux negatif -> ValueError")
check(_leve(M.bilan_matiere, "100", [100]), "bilan non-liste -> ValueError")
check(_leve(M.bilan_matiere, [100], [100], -1), "bilan tol negative -> ValueError")

# --- Determinisme ---
check(M.rendement(90, 100) == M.rendement(90, 100), "rendement deterministe")
check(M.taux_conversion(80, 100) == M.taux_conversion(80, 100), "conversion deterministe")
check(M.bilan_matiere([60, 40], [100]) == M.bilan_matiere([60, 40], [100]), "bilan deterministe")

print(f"\n=== valide_procedes_industriels : {ok}/{ok+ko} ===")
import sys
sys.exit(0 if ko == 0 else 1)
