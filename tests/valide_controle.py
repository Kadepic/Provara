"""VALIDE controle.py — ADVERSE, FAUX=0. Stabilité Routh-Hurwitz comparée à l'analyse des racines (cas connus
stables/instables) + comptage des racines instables + SOUNDNESS (cas singulier / coefficient invalide -> ValueError)."""
import controle as C

ok = 0
ko = 0


def check(c, l):
    global ok, ko
    if c:
        ok += 1
    else:
        ko += 1
        print(f"  FAIL: {l}")


def leve(fn, *a):
    try:
        fn(*a)
        return False
    except ValueError:
        return True
    except Exception:
        return False


# STABLES connus (toutes racines à partie réelle < 0)
check(C.est_stable([1, 2, 1]) is True, "s²+2s+1 = (s+1)² stable")
check(C.est_stable([1, 3, 3, 1]) is True, "(s+1)³ stable")
check(C.est_stable([1, 2, 3, 4]) is True, "s³+2s²+3s+4 stable (Routh)")
check(C.est_stable([1, 6, 11, 6]) is True, "(s+1)(s+2)(s+3) stable")
check(C.est_stable([2, 4, 2]) is True, "coefficient dominant ≠ 1, stable")

# INSTABLES connus (au moins une racine à partie réelle ≥ 0)
check(C.est_stable([1, -2, 1]) is False, "s²-2s+1 = (s-1)² instable")
check(C.est_stable([1, 1, 1, 6]) is False, "s³+s²+s+6 instable")
check(C.est_stable([1, -6, 11, -6]) is False, "(s-1)(s-2)(s-3) instable")
check(C.est_stable([1, 2, -3]) is False, "c<0 -> instable (changement de signe)")
# critère du 2e ordre : as²+bs+c stable ssi a,b,c de même signe
check(C.est_stable([1, 5, 6]) is True and C.est_stable([1, -5, 6]) is False, "2e ordre : signes")

# COMPTAGE des racines instables (changements de signe 1ʳᵉ colonne)
check(C.changements_de_signe([1, 1, 1, 6]) == 2, "s³+s²+s+6 : 2 racines instables")
check(C.changements_de_signe([1, 2, 1]) == 0, "stable -> 0 racine instable")
check(C.changements_de_signe([1, -6, 11, -6]) == 3, "(s-1)(s-2)(s-3) : 3 racines instables")

# SOUNDNESS
check(leve(C.est_stable, [1, 0, 1]), "s²+1 (marginal, pôles ±i) -> ValueError (zéro 1ʳᵉ colonne)")
check(leve(C.est_stable, [1]), "degré 0 -> ValueError")
check(leve(C.est_stable, [0, 1, 1]), "coeff dominant 0 -> ValueError")
check(leve(C.est_stable, [1, 1.5, 1]), "coefficient float -> ValueError")

# DÉTERMINISME
check(C.est_stable([1, 2, 3, 4]) == C.est_stable([1, 2, 3, 4]), "déterminisme")

print(f"\n=== valide_controle : {ok}/{ok + ko} ===")
import sys
sys.exit(0 if ko == 0 else 1)
