"""
VALIDE chomage.py — held-out ADVERSE.

Ancres CONNUES (définitions BIT + arithmétique vérifiée à la main, NON circulaires) :
  • population_active : 22.5M + 2.5M = 25M ; 0 + 0 = 0 ; 27 + 3 = 30
  • taux_chomage     : 2.5M/25M = 10 % (cas de la spéc) ; 1/4 = 25 % ; 0/100 = 0 % (plein emploi) ;
                       250/250 = 100 % (borne) ; 3/30 = 10 %
  • taux_activite    : 30/40 = 75 % ; 25M/50M = 50 % ; 40/40 = 100 % (borne)
  • taux_emploi      : 27/40 = 67.5 % ; 13.5M/30M = 45 % ; 30/30 = 100 % (borne)
  • cohérence croisée : active = occupés + chômeurs, puis taux_chomage(chômeurs, active) cohérent.
SOUNDNESS : population_active <= 0, chomeurs < 0, chomeurs > active, effectif < 0, PAT <= 0,
            active > PAT, occupés > PAT, valeur non finie / non numérique -> ValueError (jamais un faux).
DÉTERMINISME : mêmes entrées -> mêmes sorties.
"""

import chomage as M

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


# ── 1) population_active = occupés + chômeurs (identité comptable) ──
check(approx(M.population_active(22.5e6, 2.5e6), 25e6), "22.5M + 2.5M = 25M")
check(approx(M.population_active(0, 0), 0.0), "0 + 0 = 0")
check(approx(M.population_active(27, 3), 30.0), "27 + 3 = 30")
check(approx(M.population_active(1234567, 765433), 2000000.0), "somme exacte")

# ── 2) taux_chomage — CAS de la spéc et ancres connues ──
check(approx(M.taux_chomage(2.5e6, 25e6), 10.0), "2.5M / 25M = 10 % (spéc)")
check(approx(M.taux_chomage(1, 4), 25.0), "1/4 = 25 %")
check(approx(M.taux_chomage(0, 100), 0.0), "0/100 = 0 % (plein emploi)")
check(approx(M.taux_chomage(250, 250), 100.0), "250/250 = 100 % (borne)")
check(approx(M.taux_chomage(3, 30), 10.0), "3/30 = 10 %")

# ── 3) taux_activite ──
check(approx(M.taux_activite(30, 40), 75.0), "30/40 = 75 %")
check(approx(M.taux_activite(25e6, 50e6), 50.0), "25M/50M = 50 %")
check(approx(M.taux_activite(40, 40), 100.0), "40/40 = 100 % (borne)")

# ── 4) taux_emploi ──
check(approx(M.taux_emploi(27, 40), 67.5), "27/40 = 67.5 %")
check(approx(M.taux_emploi(13.5e6, 30e6), 45.0), "13.5M/30M = 45 %")
check(approx(M.taux_emploi(30, 30), 100.0), "30/30 = 100 % (borne)")

# ── 5) COHÉRENCE CROISÉE — active dérivée puis réutilisée ──
act = M.population_active(22.5e6, 2.5e6)              # = 25M
check(approx(M.taux_chomage(2.5e6, act), 10.0), "active=occ+chô puis taux_chomage cohérent = 10 %")
# Identité : taux_emploi + (chômeurs/PAT*100) = taux_activite quand active = occ+chô, PAT donné.
pat = 40e6
te = M.taux_emploi(27e6, pat)                         # 67.5 %
ta = M.taux_activite(M.population_active(27e6, 3e6), pat)  # (30M)/40M = 75 %
check(approx(ta - te, 3e6 / pat * 100.0), "taux_activite − taux_emploi = part chômeurs/PAT")

# ── 6) SOUNDNESS — population active nulle / négative ──
check(_leve_v(M.taux_chomage, 0, 0), "population_active = 0 -> ValueError")
check(_leve_v(M.taux_chomage, 1, -5), "population_active < 0 -> ValueError")

# ── 7) SOUNDNESS — chômeurs incohérents ──
check(_leve_v(M.taux_chomage, -1, 100), "chomeurs < 0 -> ValueError")
check(_leve_v(M.taux_chomage, 101, 100), "chomeurs > active (taux>100 %) -> ValueError")
check(_leve_v(M.population_active, -1, 5), "actifs_occupes < 0 -> ValueError")
check(_leve_v(M.population_active, 5, -1), "chomeurs < 0 (pop active) -> ValueError")

# ── 8) SOUNDNESS — PAT et bornes des taux activité/emploi ──
check(_leve_v(M.taux_activite, 10, 0), "PAT = 0 (activité) -> ValueError")
check(_leve_v(M.taux_emploi, 10, 0), "PAT = 0 (emploi) -> ValueError")
check(_leve_v(M.taux_activite, 41, 40), "active > PAT (taux>100 %) -> ValueError")
check(_leve_v(M.taux_emploi, 41, 40), "occupés > PAT (taux>100 %) -> ValueError")
check(_leve_v(M.taux_activite, -1, 40), "active < 0 -> ValueError")
check(_leve_v(M.taux_emploi, -1, 40), "occupés < 0 -> ValueError")

# ── 9) SOUNDNESS — valeurs non finies / non numériques / booléen (abstention) ──
check(_leve_v(M.taux_chomage, float("nan"), 25e6), "chomeurs NaN -> ValueError")
check(_leve_v(M.taux_chomage, 2.5e6, float("inf")), "active inf -> ValueError")
check(_leve_v(M.taux_chomage, "deux", 25e6), "chomeurs non numérique -> ValueError")
check(_leve_v(M.population_active, None, 5), "actifs_occupes None -> ValueError")
check(_leve_v(M.taux_emploi, True, 40), "booléen refusé -> ValueError")
check(_leve_v(M.taux_activite, 30, float("nan")), "PAT NaN -> ValueError")

# ── 10) DÉTERMINISME ──
check(M.taux_chomage(2.5e6, 25e6) == M.taux_chomage(2.5e6, 25e6), "taux_chomage déterministe")
check(M.population_active(27, 3) == M.population_active(27, 3), "population_active déterministe")
check(M.taux_activite(30, 40) == M.taux_activite(30, 40), "taux_activite déterministe")
check(M.taux_emploi(27, 40) == M.taux_emploi(27, 40), "taux_emploi déterministe")

print(f"\n=== valide_chomage : {ok}/{ok+ko} ===")
import sys
sys.exit(0 if ko == 0 else 1)
