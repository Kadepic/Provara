"""VALIDE statique.py — ADVERSE, FAUX=0. Levier, centre de masse, équilibre des moments, réactions d'appui (avec
conservation R_g + R_d = charge vérifiée indépendamment) + SOUNDNESS (bras/masse/position invalides -> ValueError)."""
import statique as S

ok = 0
ko = 0


def check(c, l):
    global ok, ko
    if c:
        ok += 1
    else:
        ko += 1
        print(f"  FAIL: {l}")


def proche(a, b, rel=1e-4):
    return abs(a - b) <= rel * abs(b) + 1e-9


def leve(fn, *a):
    try:
        fn(*a)
        return False
    except ValueError:
        return True
    except Exception:
        return False


# MOMENT
check(S.moment(5, 2) == 10.0, "M = F·d = 10 N·m")
check(S.moment(10, 0) == 0.0, "bras nul -> moment nul")

# ÉQUILIBRE DES MOMENTS
check(S.equilibre_moments([10, -10]) is True, "moments opposés -> équilibre")
check(S.equilibre_moments([10, -5]) is False, "déséquilibre")
check(S.equilibre_moments([3, -1, -2]) is True, "3 moments équilibrés")
check(S.equilibre_moments([0]) is True, "moment nul -> équilibre")

# LEVIER
check(S.force_levier(100, 1, 4) == 25.0, "levier : effort 25 N (avantage ×4)")
check(S.force_levier(50, 2, 1) == 100.0, "levier défavorable -> 100 N")
# le levier conserve le moment : F_effort·bras_effort = charge·bras_charge
check(proche(S.force_levier(100, 1, 4) * 4, 100 * 1), "conservation du moment au levier")

# CENTRE DE MASSE
check(S.centre_de_masse([1, 1], [0, 2]) == 1.0, "centre de 2 masses égales = milieu")
check(S.centre_de_masse([2, 1], [0, 3]) == 1.0, "centre pondéré")
check(S.centre_de_masse([5], [7]) == 7.0, "masse unique -> sa position")
check(S.centre_de_masse([3, 3, 3], [0, 3, 6]) == 3.0, "3 masses symétriques")

# RÉACTIONS D'APPUI (+ conservation indépendante)
rg, rd = S.reactions_appui(100, 1, 2)
check(rg == 50.0 and rd == 50.0, "charge au milieu -> 50/50")
check(proche(rg + rd, 100), "conservation R_g + R_d = charge (milieu)")
rg2, rd2 = S.reactions_appui(100, 1, 4)
check(rg2 == 75.0 and rd2 == 25.0, "charge à 1/4 -> 75/25")
check(proche(rg2 + rd2, 100), "conservation (1/4)")
rg3, rd3 = S.reactions_appui(100, 4, 4)
check(rg3 == 0.0 and rd3 == 100.0, "charge sur l'appui droit -> 0/100")

# SOUNDNESS
check(leve(S.force_levier, 100, 0, 4), "bras_charge=0 -> ValueError")
check(leve(S.force_levier, -10, 1, 1), "charge<0 -> ValueError")
check(leve(S.centre_de_masse, [0, 0], [1, 2]), "masse totale 0 -> ValueError")
check(leve(S.centre_de_masse, [1], [1, 2]), "listes incohérentes -> ValueError")
check(leve(S.reactions_appui, 100, 5, 4), "position > L -> ValueError")
check(leve(S.reactions_appui, 100, 1, 0), "L=0 -> ValueError")

# DÉTERMINISME
check(S.reactions_appui(100, 1, 4) == S.reactions_appui(100, 1, 4), "déterminisme")

print(f"\n=== valide_statique : {ok}/{ok + ko} ===")
import sys
sys.exit(0 if ko == 0 else 1)
