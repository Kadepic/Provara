"""VALIDE automates.py — ADVERSE, FAUX=0. Langages réguliers CONNUS (parité du nombre de 1 ; multiples de 3 en
binaire) vérifiés sur de nombreux mots + SOUNDNESS (DFA mal formé / symbole hors alphabet -> ValueError)."""
import automates as A

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


# DFA 1 : nombre PAIR de 1
PARITE = {
    "etats": {"pair", "impair"}, "alphabet": {"0", "1"},
    "transitions": {("pair", "0"): "pair", ("pair", "1"): "impair",
                    ("impair", "0"): "impair", ("impair", "1"): "pair"},
    "initial": "pair", "acceptants": {"pair"},
}
for m in ["", "0", "00", "11", "101", "1010", "111000"]:
    check(A.accepte(PARITE, m) == (m.count("1") % 2 == 0), f"parité-1 « {m or 'ε'} »")
for m in ["1", "111", "10", "01110"]:
    check(A.accepte(PARITE, m) == (m.count("1") % 2 == 0), f"parité-1 (impair) « {m} »")

# DFA 2 : multiples de 3 (valeur binaire ≡ 0 mod 3) — δ(r,b) = (2r+b) mod 3
MUL3 = {
    "etats": {0, 1, 2}, "alphabet": {"0", "1"},
    "transitions": {(r, b): (2 * r + int(b)) % 3 for r in (0, 1, 2) for b in ("0", "1")},
    "initial": 0, "acceptants": {0},
}
for m in ["0", "11", "110", "1001", "1100", "0", "10", "111", "101"]:
    attendu = (int(m, 2) % 3 == 0)
    check(A.accepte(MUL3, m) == attendu, f"mult-3 « {m} » (={int(m, 2)})")
check(A.accepte(MUL3, "") is True, "ε -> 0 divisible par 3")

# états accessibles
check(A.etats_accessibles(PARITE) == {"pair", "impair"}, "2 états accessibles (parité)")

# SOUNDNESS
incomplet = {"etats": {"q"}, "alphabet": {"0", "1"}, "transitions": {("q", "0"): "q"},
             "initial": "q", "acceptants": {"q"}}
check(leve(A.accepte, incomplet, "0"), "δ incomplète -> ValueError")
check(leve(A.accepte, PARITE, "012"), "symbole hors alphabet -> ValueError")
mauvais_init = dict(PARITE, initial="zzz")
check(leve(A.accepte, mauvais_init, "0"), "état initial hors états -> ValueError")
mauvais_acc = dict(PARITE, acceptants={"zzz"})
check(leve(A.accepte, mauvais_acc, "0"), "acceptant hors états -> ValueError")

# DÉTERMINISME
check(A.accepte(MUL3, "1001") == A.accepte(MUL3, "1001"), "déterminisme")

print(f"\n=== valide_automates : {ok}/{ok + ko} ===")
import sys
sys.exit(0 if ko == 0 else 1)
