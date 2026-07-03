"""VALIDE architecture.py — ADVERSE, FAUX=0. Complément à deux CONNU, intervalles représentables, aller-retour
codage/décodage, débordement d'addition + SOUNDNESS (valeur hors intervalle -> ValueError)."""
import architecture as A

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


# CONVERSIONS
check(A.vers_binaire(5, 8) == "00000101" and A.vers_binaire(255, 8) == "11111111", "binaire 5 et 255")
check(A.vers_hexa(255) == "FF" and A.vers_hexa(4096) == "1000" and A.vers_hexa(0) == "0", "hexa")
check(A.depuis_binaire("00000101") == 5 and A.depuis_binaire("11111111") == 255, "binaire -> entier")

# COMPLÉMENT À DEUX — valeurs connues
check(A.complement_a_deux(-1, 8) == 255, "c2(-1, 8) = 0xFF = 255")
check(A.complement_a_deux(-128, 8) == 128, "c2(-128, 8) = 128 (min)")
check(A.complement_a_deux(127, 8) == 127, "c2(127, 8) = 127 (max)")
check(A.complement_a_deux(0, 8) == 0 and A.complement_a_deux(-2, 8) == 254, "c2(0)=0, c2(-2)=254")
check(A.complement_a_deux(-1, 16) == 65535, "c2(-1, 16) = 0xFFFF")
# décodage = inverse exact
check(A.depuis_complement_a_deux(255, 8) == -1 and A.depuis_complement_a_deux(128, 8) == -128, "décodage")
check(all(A.depuis_complement_a_deux(A.complement_a_deux(n, 8), 8) == n for n in range(-128, 128)), "aller-retour 8 bits complet")

# ADDITION + DÉBORDEMENT
check(A.addition_binaire(100, 20, 8) == (120, False), "100+20 = 120 sans débordement")
check(A.addition_binaire(100, 50, 8)[1] is True, "100+50 -> débordement (>127)")
check(A.addition_binaire(-100, -50, 8)[1] is True, "-100-50 -> débordement (<-128)")
check(A.addition_binaire(-1, 1, 8) == (0, False), "-1+1 = 0")
check(A.addition_binaire(127, -1, 8) == (126, False), "127-1 = 126")

# SOUNDNESS — hors intervalle représentable
check(leve(A.complement_a_deux, 128, 8), "128 hors [−128,127] sur 8 bits -> ValueError")
check(leve(A.complement_a_deux, -129, 8), "−129 hors intervalle -> ValueError")
check(leve(A.vers_binaire, 256, 8), "256 hors [0,255] sur 8 bits -> ValueError")
check(leve(A.vers_binaire, 5, 0), "0 bit -> ValueError")
check(leve(A.depuis_binaire, "012"), "chiffre non binaire -> ValueError")
check(leve(A.vers_hexa, -1), "négatif -> ValueError")

# DÉTERMINISME
check(A.complement_a_deux(-1, 8) == A.complement_a_deux(-1, 8), "déterminisme")

print(f"\n=== valide_architecture : {ok}/{ok + ko} ===")
import sys
sys.exit(0 if ko == 0 else 1)
