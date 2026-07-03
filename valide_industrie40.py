"""valide_industrie40.py — validation adversariale de industrie40.py (TRS/OEE).

Ancres connues (faits OEE/TPM établis) + soundness (abstention) + déterminisme.
"""

import industrie40 as M

ok = 0
ko = 0


def check(cond, label):
    global ok, ko
    if cond:
        ok += 1
    else:
        ko += 1
        print(f"  KO: {label}")


def leve_v(fn, *a):
    """True ssi fn(*a) lève ValueError (abstention attendue)."""
    try:
        fn(*a)
        return False
    except ValueError:
        return True
    except Exception:
        return False


TOL = 1e-9

# --- Ancres : facteurs ratios ---------------------------------------------
check(abs(M.disponibilite(0.0, 100.0) - 0.0) < TOL, "disponibilite 0/100 = 0")
check(abs(M.disponibilite(57.0, 60.0) - 0.95) < TOL, "disponibilite 57/60 = 0.95")
check(abs(M.disponibilite(60.0, 60.0) - 1.0) < TOL, "disponibilite 60/60 = 1")
check(abs(M.performance(950.0, 1000.0) - 0.95) < TOL, "performance 950/1000 = 0.95")
check(abs(M.qualite(990.0, 1000.0) - 0.99) < TOL, "qualite 990/1000 = 0.99")
check(abs(M.qualite(1.0, 4.0) - 0.25) < TOL, "qualite 1/4 = 0.25")

# --- Ancre canonique : OEE(0.9, 0.95, 0.99) ~= 0.846 -----------------------
v = M.oee(0.9, 0.95, 0.99)
check(abs(v - 0.846450) < 1e-6, "oee(0.9,0.95,0.99) ~= 0.846450")
check(abs(v - 0.846) < 1e-3, "oee(0.9,0.95,0.99) ~= 0.846 (3 décimales)")

# --- OEE parfait = 1 -------------------------------------------------------
check(abs(M.oee(1.0, 1.0, 1.0) - 1.0) < TOL, "oee parfait = 1")
# --- OEE nul si un facteur nul --------------------------------------------
check(abs(M.oee(0.0, 1.0, 1.0) - 0.0) < TOL, "oee avec D=0 -> 0")

# --- TRS alias = OEE -------------------------------------------------------
check(abs(M.trs(0.9, 0.95, 0.99) - M.oee(0.9, 0.95, 0.99)) < TOL, "trs == oee")

# --- Cohérence chaîne complète : ratios -> oee ----------------------------
d = M.disponibilite(54.0, 60.0)
p = M.performance(950.0, 1000.0)
q = M.qualite(990.0, 1000.0)
check(abs(M.oee(d, p, q) - 0.846450) < 1e-6, "chaîne ratios -> oee 0.846450")

# --- Classe mondiale (seuil établi 0.85) ----------------------------------
check(M.est_classe_mondiale(0.85) is True, "0.85 = classe mondiale (seuil inclus)")
check(M.est_classe_mondiale(0.90) is True, "0.90 classe mondiale")
check(M.est_classe_mondiale(0.846450) is False, "0.846 < 0.85 non classe mondiale")
check(M.est_classe_mondiale(1.0) is True, "1.0 classe mondiale")

# --- SOUNDNESS : facteurs hors [0,1] -> ValueError ------------------------
check(leve_v(M.oee, 1.1, 0.5, 0.5), "oee D>1 -> ValueError")
check(leve_v(M.oee, -0.1, 0.5, 0.5), "oee D<0 -> ValueError")
check(leve_v(M.oee, 0.5, 2.0, 0.5), "oee P>1 -> ValueError")
check(leve_v(M.oee, 0.5, 0.5, -0.001), "oee Q<0 -> ValueError")
check(leve_v(M.est_classe_mondiale, 1.5), "est_classe_mondiale(1.5) -> ValueError")

# --- SOUNDNESS : dénominateurs nuls/négatifs -> ValueError ----------------
check(leve_v(M.disponibilite, 10.0, 0.0), "disponibilite den=0 -> ValueError")
check(leve_v(M.disponibilite, 10.0, -5.0), "disponibilite den<0 -> ValueError")
check(leve_v(M.performance, 10.0, 0.0), "performance den=0 -> ValueError")
check(leve_v(M.qualite, 5.0, 0.0), "qualite den=0 -> ValueError")

# --- SOUNDNESS : ratio > 1 (num > den) -> ValueError ----------------------
check(leve_v(M.disponibilite, 70.0, 60.0), "disponibilite 70/60 -> ValueError")
check(leve_v(M.qualite, 1001.0, 1000.0), "qualite num>den -> ValueError")
check(leve_v(M.performance, -1.0, 100.0), "performance num<0 -> ValueError")

# --- SOUNDNESS : non numérique / non fini / bool -> ValueError ------------
check(leve_v(M.oee, "0.9", 0.95, 0.99), "oee facteur str -> ValueError")
check(leve_v(M.disponibilite, None, 100.0), "disponibilite None -> ValueError")
check(leve_v(M.oee, float("nan"), 0.5, 0.5), "oee NaN -> ValueError")
check(leve_v(M.oee, float("inf"), 0.5, 0.5), "oee inf -> ValueError")
check(leve_v(M.oee, True, 0.5, 0.5), "oee bool -> ValueError")

# --- DÉTERMINISME ---------------------------------------------------------
check(M.oee(0.8, 0.9, 0.95) == M.oee(0.8, 0.9, 0.95), "oee déterministe")
check(M.disponibilite(3.0, 4.0) == M.disponibilite(3.0, 4.0), "disponibilite déterministe")

print(f"\n=== valide_industrie40 : {ok}/{ok+ko} ===")
import sys
sys.exit(0 if ko == 0 else 1)
