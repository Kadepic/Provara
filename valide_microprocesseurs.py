"""VALIDE microprocesseurs.py — ADVERSE, FAUX=0. Tables de vérité des portes, additionneur complet, ALU avec
indicateurs (zéro/retenue/débordement signé distingués) + SOUNDNESS (opération/opérande invalide -> ValueError)."""
import microprocesseurs as M

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


# PORTES (tables de vérité complètes)
check([M.porte("et", a, b) for a in (0, 1) for b in (0, 1)] == [0, 0, 0, 1], "table ET")
check([M.porte("ou", a, b) for a in (0, 1) for b in (0, 1)] == [0, 1, 1, 1], "table OU")
check([M.porte("ou-x", a, b) for a in (0, 1) for b in (0, 1)] == [0, 1, 1, 0], "table XOR")
check([M.porte("non-et", a, b) for a in (0, 1) for b in (0, 1)] == [1, 1, 1, 0], "table NAND")
check([M.porte("non-ou", a, b) for a in (0, 1) for b in (0, 1)] == [1, 0, 0, 0], "table NOR")
check(M.porte("non", 0) == 1 and M.porte("non", 1) == 0, "NON")
check([M.porte("ou-x-non", a, b) for a in (0, 1) for b in (0, 1)] == [1, 0, 0, 1], "table XNOR")

# ADDITIONNEUR COMPLET (4 bits de retenue)
check(M.additionneur_complet(0, 0, 0) == (0, 0), "0+0+0 = (0,0)")
check(M.additionneur_complet(1, 0, 0) == (1, 0), "1+0+0 = (1,0)")
check(M.additionneur_complet(1, 1, 0) == (0, 1), "1+1+0 = (0,1) retenue")
check(M.additionneur_complet(1, 1, 1) == (1, 1), "1+1+1 = (1,1)")
check(M.additionneur_complet(0, 1, 1) == (0, 1), "0+1+1 = (0,1)")

# ALU — addition avec retenue (non signée) et débordement (signé) DISTINCTS
r = M.alu("add", 200, 100, 8)
check(r["resultat"] == 44 and r["retenue"] == 1, "200+100 = 44 mod 256, retenue=1")
r = M.alu("add", 100, 28, 8)
check(r["resultat"] == 128 and r["retenue"] == 0 and r["debordement"] is True, "100+28 = 128 : pas de retenue mais débordement SIGNÉ")
r = M.alu("add", 1, 1, 8)
check(r["resultat"] == 2 and r["retenue"] == 0 and r["debordement"] is False, "1+1 = 2 sans flag")
# soustraction + flag zéro
check(M.alu("sub", 50, 50, 8)["zero"] == 1, "50-50 = 0 -> zéro")
check(M.alu("sub", 10, 20, 8)["retenue"] == 1, "10-20 -> emprunt (retenue)")
check(M.alu("sub", 20, 10, 8)["resultat"] == 10, "20-10 = 10")
# logique
check(M.alu("and", 0xF0, 0x0F, 8)["resultat"] == 0, "0xF0 AND 0x0F = 0")
check(M.alu("or", 0xF0, 0x0F, 8)["resultat"] == 0xFF, "0xF0 OR 0x0F = 0xFF")
check(M.alu("xor", 0xFF, 0xFF, 8)["resultat"] == 0, "x XOR x = 0")
check(M.alu("not", 0x00, 0, 8)["resultat"] == 0xFF, "NOT 0 = 0xFF (8 bits)")

# SOUNDNESS
check(leve(M.porte, "xnand", 1, 1), "porte inconnue -> ValueError")
check(leve(M.porte, "et", 2, 1), "entrée non binaire -> ValueError")
check(leve(M.alu, "mul", 2, 2, 8), "opération ALU inconnue -> ValueError")
check(leve(M.alu, "add", 256, 1, 8), "opérande hors plage 8 bits -> ValueError")
check(leve(M.additionneur_complet, 2, 0, 0), "bit invalide -> ValueError")

# DÉTERMINISME
check(M.alu("add", 100, 28, 8) == M.alu("add", 100, 28, 8), "déterminisme")

print(f"\n=== valide_microprocesseurs : {ok}/{ok + ko} ===")
import sys
sys.exit(0 if ko == 0 else 1)
