"""VALIDE coordination.py — held-out ADVERSE. Ancres de chimie de coordination (n.o. métal, règle des 18 e⁻,
nombre de coordination par denticité) + SOUNDNESS (ligand/charge/d invalides -> ValueError) + déterminisme.
Aucun de ces cas n'est dans le __main__ du module.
"""
import coordination as M

ok = 0
ko = 0


def check(cond, label):
    global ok, ko
    if cond:
        ok += 1
    else:
        ko += 1
        print(f"  FAIL: {label}")


def leve_v(fn, *a):
    try:
        fn(*a)
        return False
    except ValueError:
        return True
    except Exception:
        return False


# 1) NOMBRE D'OXYDATION DU MÉTAL — ancres de référence (held-out).
#    n.o.(M) = charge_complexe − Σ charges ligands.
check(M.nombre_oxydation_metal(-3, ["CN-"] * 6) == 3, "[Fe(CN)6]3- -> Fe(+3)")
check(M.nombre_oxydation_metal(-4, ["CN-"] * 6) == 2, "[Fe(CN)6]4- -> Fe(+2)")
check(M.nombre_oxydation_metal(3, ["NH3"] * 6) == 3, "[Co(NH3)6]3+ -> Co(+3)")
check(M.nombre_oxydation_metal(2, ["NH3"] * 6) == 2, "[Co(NH3)6]2+ -> Co(+2)")
check(M.nombre_oxydation_metal(2, ["NH3"] * 4) == 2, "[Cu(NH3)4]2+ -> Cu(+2)")
check(M.nombre_oxydation_metal(1, ["NH3"] * 2) == 1, "[Ag(NH3)2]+ -> Ag(+1)")
check(M.nombre_oxydation_metal(-2, ["Cl-"] * 4) == 2, "[PtCl4]2- -> Pt(+2)")
check(M.nombre_oxydation_metal(-2, ["Cl-"] * 6) == 4, "[PtCl6]2- -> Pt(+4)")
check(M.nombre_oxydation_metal(3, ["H2O"] * 6) == 3, "[Fe(H2O)6]3+ -> Fe(+3)")
check(M.nombre_oxydation_metal(-3, ["OH-"] * 6) == 3, "[Cr(OH)6]3- -> Cr(+3)")
check(M.nombre_oxydation_metal(-2, ["OH-"] * 4) == 2, "[Zn(OH)4]2- -> Zn(+2)")
check(M.nombre_oxydation_metal(-1, ["OH-"] * 4) == 3, "[Al(OH)4]- -> Al(+3)")
check(M.nombre_oxydation_metal(-2, ["CN-"] * 4) == 2, "[Ni(CN)4]2- -> Ni(+2)")
check(M.nombre_oxydation_metal(3, ["en"] * 3) == 3, "[Co(en)3]3+ -> Co(+3) (ligand neutre)")
check(M.nombre_oxydation_metal(-3, ["C2O4^2-"] * 3) == 3, "[Cr(C2O4)3]3- -> Cr(+3)")
check(M.nombre_oxydation_metal(-1, ["EDTA^4-"]) == 3, "[Co(EDTA)]- -> Co(+3)")
check(M.nombre_oxydation_metal(2, ["bpy"] * 3) == 2, "[Fe(bpy)3]2+ -> Fe(+2)")
# mélange de ligands : [Co(NH3)5Cl]2+ -> Co: 2 - (5*0 + 1*(-1)) = +3
check(M.nombre_oxydation_metal(2, ["NH3"] * 5 + ["Cl-"]) == 3, "[Co(NH3)5Cl]2+ -> Co(+3)")
# alias acceptés
check(M.nombre_oxydation_metal(-3, ["ox"] * 3) == 3, "alias ox = oxalato")
check(M.charge_ligand("CN-") == -1 and M.charge_ligand("NH3") == 0, "charges ligands de base")
check(M.charge_ligand("C2O4^2-") == -2 and M.charge_ligand("EDTA^4-") == -4, "charges polychargés")

# 2) NOMBRE DE COORDINATION = Σ denticités (held-out).
check(M.nombre_coordination(["CN-"] * 6) == 6, "CN [Fe(CN)6] -> 6")
check(M.nombre_coordination(["NH3"] * 6) == 6, "NH3 [Co(NH3)6] -> 6")
check(M.nombre_coordination(["Cl-"] * 4) == 4, "[PtCl4] -> 4")
check(M.nombre_coordination(["NH3"] * 2) == 2, "[Ag(NH3)2] -> 2")
check(M.nombre_coordination(["en"] * 3) == 6, "[Co(en)3] bidenté -> 6")
check(M.nombre_coordination(["en"] * 2) == 4, "[Cu(en)2] -> 4")
check(M.nombre_coordination(["C2O4^2-"] * 3) == 6, "[Cr(ox)3] -> 6")
check(M.nombre_coordination(["EDTA^4-"]) == 6, "[Co(EDTA)] hexadenté -> 6")
check(M.nombre_coordination(["NH3"] * 5 + ["Cl-"]) == 6, "[Co(NH3)5Cl] -> 6")
check(M.denticite("en") == 2 and M.denticite("Cl-") == 1, "denticités connues")

# 3) RÈGLE DES 18 ÉLECTRONS — compte = d + 2n (held-out).
check(M.compte_electrons_18(6, 6) == 18, "[Co(NH3)6]3+ d6 -> 18")
check(M.compte_electrons_18(6, 6) == 18 and M.respecte_regle_18(6, 6), "Cr(CO)6 d6 -> 18")
check(M.compte_electrons_18(10, 4) == 18, "Ni(CO)4 d10 -> 18")
check(M.compte_electrons_18(8, 5) == 18, "Fe(CO)5 d8 -> 18")
check(M.compte_electrons_18(6, 6) == 18, "ferrocyanure Fe(II) d6 -> 18")
check(M.compte_electrons_18(5, 6) == 17, "ferricyanure Fe(III) d5 -> 17 (exception réelle)")
check(M.compte_electrons_18(8, 4) == 16, "[PtCl4]2- d8 plan-carré -> 16")
check(M.respecte_regle_18(10, 4) is True, "regle_18 vraie Ni(CO)4")
check(M.respecte_regle_18(5, 6) is False, "regle_18 fausse ferricyanure")
check(M.compte_electrons_18(0, 0) == 0, "borne d0 n0 -> 0")
check(M.compte_electrons_18(10, 0) == 10, "d10 sans ligand -> 10")

# 4) SOUNDNESS — entrée invalide/inconnue -> ValueError (jamais de réponse inventée).
check(leve_v(M.nombre_oxydation_metal, 0, ["XYZ"]), "ligand inconnu XYZ -> ValueError")
check(leve_v(M.nombre_oxydation_metal, 0, ["CO3^2-"]), "carbonato (denticité ambiguë, hors catalogue) -> ValueError")
check(leve_v(M.nombre_oxydation_metal, 0, ["NH3", "Inconnu"]), "un ligand inconnu suffit -> ValueError")
check(leve_v(M.nombre_oxydation_metal, 1.5, ["Cl-"]), "charge non entière -> ValueError")
check(leve_v(M.nombre_oxydation_metal, True, ["Cl-"]), "charge bool -> ValueError")
check(leve_v(M.nombre_oxydation_metal, -3, "CN-"), "ligands non liste (str) -> ValueError")
check(leve_v(M.nombre_oxydation_metal, 0, []), "liste vide -> ValueError")
check(leve_v(M.nombre_coordination, ["Zz-"]), "coordination ligand inconnu -> ValueError")
check(leve_v(M.charge_ligand, "Pu-"), "charge_ligand inconnu -> ValueError")
check(leve_v(M.denticite, "???"), "denticite inconnu -> ValueError")
check(leve_v(M.charge_ligand, 42), "charge_ligand non str -> ValueError")
check(leve_v(M.compte_electrons_18, 11, 6), "d=11 hors plage 0..10 -> ValueError")
check(leve_v(M.compte_electrons_18, -1, 6), "d=-1 hors plage -> ValueError")
check(leve_v(M.compte_electrons_18, 6, -1), "n négatif -> ValueError")
check(leve_v(M.compte_electrons_18, 6.0, 6), "d non entier -> ValueError")
check(leve_v(M.compte_electrons_18, 6, True), "n bool -> ValueError")

# 5) DÉTERMINISME — mêmes entrées, mêmes sorties.
check(M.nombre_oxydation_metal(-3, ["CN-"] * 6) == M.nombre_oxydation_metal(-3, ["CN-"] * 6),
      "déterminisme n.o.")
check(M.compte_electrons_18(8, 5) == M.compte_electrons_18(8, 5), "déterminisme 18e")
check(M.nombre_coordination(["en"] * 3) == M.nombre_coordination(["en"] * 3), "déterminisme coordination")

# 6) PREUVE intégrée.
check(M._p_coordination() is True, "_p_coordination() -> True")

print(f"\n=== valide_coordination : {ok}/{ok+ko} ===")
import sys
sys.exit(0 if ko == 0 else 1)
