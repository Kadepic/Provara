"""
VALIDE redox.py — held-out ADVERSE. Ancres EXTERNES connues (n.o. de référence des manuels, NON re-calculés
par la même expression) + SOUNDNESS (abstention par ValueError sur peroxyde/superoxyde/hydrure/inconnues
multiples/élément absent/formule invalide/non-entier) + déterminisme. Aucun de ces cas n'est en dur dans redox.py.
"""
import redox as R

ok = 0
ko = 0


def check(cond, label):
    global ok, ko
    if cond:
        ok += 1
    else:
        ko += 1
        print(f"  FAIL: {label}")


def leve(fn, *a):
    """True ssi fn(*a) lève ValueError (abstention conservatrice)."""
    try:
        fn(*a)
        return False
    except ValueError:
        return True
    except Exception:
        return False


# ── 1) ANCRES IMPOSÉES PAR LE SUJET (valeurs de manuel connues) ──
check(R.nombre_oxydation("H2SO4", "S") == 6, "S dans H2SO4 = +6")
check(R.nombre_oxydation("H2S", "S") == -2, "S dans H2S = -2")
check(R.nombre_oxydation("KMnO4", "Mn") == 7, "Mn dans KMnO4 = +7")
check(R.nombre_oxydation("K2Cr2O7", "Cr") == 6, "Cr dans K2Cr2O7 = +6")
check(R.nombre_oxydation("HNO3", "N") == 5, "N dans HNO3 = +5")
check(R.nombre_oxydation("CO2", "C") == 4, "C dans CO2 = +4")

# ── 2) ANCRES SUPPLÉMENTAIRES (autres composés à n.o. connu) ──
check(R.nombre_oxydation("H2O", "O") == -2, "O dans H2O = -2")
check(R.nombre_oxydation("H2O", "H") == 1, "H dans H2O = +1")
check(R.nombre_oxydation("Na2O", "O") == -2, "O dans Na2O = -2 (Na fixé)")
check(R.nombre_oxydation("SO2", "S") == 4, "S dans SO2 = +4")
check(R.nombre_oxydation("SO3", "S") == 6, "S dans SO3 = +6")
check(R.nombre_oxydation("NH3", "N") == -3, "N dans NH3 = -3")
check(R.nombre_oxydation("CH4", "C") == -4, "C dans CH4 = -4")
check(R.nombre_oxydation("Al2O3", "Al") == 3, "Al dans Al2O3 = +3")
check(R.nombre_oxydation("P4O10", "P") == 5, "P dans P4O10 = +5")
check(R.nombre_oxydation("HClO4", "Cl") == 7, "Cl dans HClO4 = +7")
check(R.nombre_oxydation("Cl2O7", "Cl") == 7, "Cl dans Cl2O7 = +7")
check(R.nombre_oxydation("MnO2", "Mn") == 4, "Mn dans MnO2 = +4")
check(R.nombre_oxydation("Fe2O3", "Fe") == 3, "Fe dans Fe2O3 = +3")
check(R.nombre_oxydation("V2O5", "V") == 5, "V dans V2O5 = +5")
check(R.nombre_oxydation("WO3", "W") == 6, "W dans WO3 = +6")
check(R.nombre_oxydation("N2O5", "N") == 5, "N dans N2O5 = +5")
check(R.nombre_oxydation("N2O3", "N") == 3, "N dans N2O3 = +3")

# n.o. nul d'un élément seul (corps simple)
check(R.nombre_oxydation("O2", "O") == 0, "O dans O2 = 0")
check(R.nombre_oxydation("Cl2", "Cl") == 0, "Cl dans Cl2 = 0")

# Éléments « durs » renvoyés directement (toujours justes en composé neutre)
check(R.nombre_oxydation("NaCl", "Na") == 1, "Na dans NaCl = +1")
check(R.nombre_oxydation("NaCl", "Cl") == -1, "Cl dans NaCl = -1 (résolu)")
check(R.nombre_oxydation("CaF2", "Ca") == 2, "Ca dans CaF2 = +2")
check(R.nombre_oxydation("CaF2", "F") == -1, "F dans CaF2 = -1 (dur)")
check(R.nombre_oxydation("KMnO4", "K") == 1, "K dans KMnO4 = +1")

# ── 3) SUBTILITÉS RÉSOLUES JUSTE (la cible est calculée, pas devinée) ──
check(R.nombre_oxydation("H2O2", "O") == -1, "O peroxyde H2O2 résolu = -1")
check(R.nombre_oxydation("Na2O2", "O") == -1, "O peroxyde Na2O2 résolu = -1")
check(R.nombre_oxydation("NaH", "H") == -1, "H hydrure NaH résolu = -1")
check(R.nombre_oxydation("CaH2", "H") == -1, "H hydrure CaH2 résolu = -1")
check(R.nombre_oxydation("OF2", "O") == 2, "O dans OF2 = +2 (résolu via F)")

# ── 4) SOUNDNESS — abstention OBLIGATOIRE (ValueError), jamais un faux ──
# peroxyde gonflerait le n.o. de la cible non-cible-O
check(leve(R.nombre_oxydation, "H2O2", "H"), "H2O2/H -> +2 hors plage -> HORS")
check(leve(R.nombre_oxydation, "CrO5", "Cr"), "CrO5/Cr -> +10 hors plage -> HORS")
check(leve(R.nombre_oxydation, "H2SO5", "S"), "H2SO5/S -> +8 > +6 -> HORS")
# superoxyde : n.o. non entier
check(leve(R.nombre_oxydation, "KO2", "O"), "superoxyde KO2/O = -1/2 -> HORS")
# hydrures de métalloïdes : H=+1 non garanti
check(leve(R.nombre_oxydation, "SiH4", "Si"), "SiH4/Si : voisin Si moins EN que H -> HORS")
check(leve(R.nombre_oxydation, "B2H6", "B"), "B2H6/B : voisin B moins EN que H -> HORS")
check(leve(R.nombre_oxydation, "PH3", "P"), "PH3/P : P ambigu (EN ~ H) -> HORS")
# plusieurs inconnues : aucun élément voisin n'a de règle
check(leve(R.nombre_oxydation, "PCl3", "P"), "PCl3/P : Cl sans règle -> HORS")
check(leve(R.nombre_oxydation, "KMnO4", "O"), "KMnO4/O : Mn sans règle -> HORS")
check(leve(R.nombre_oxydation, "K2Cr2O7", "O"), "K2Cr2O7/O : Cr sans règle -> HORS")
# élément absent
check(leve(R.nombre_oxydation, "CO2", "S"), "CO2/S : élément absent -> HORS")
check(leve(R.nombre_oxydation, "H2O", "Na"), "H2O/Na : élément absent -> HORS")
# cible hors référentiel de plage
check(leve(R.nombre_oxydation, "Ag2O", "Ag"), "Ag2O/Ag : Ag hors table de plages -> HORS")
# formule invalide
check(leve(R.nombre_oxydation, "Xx9", "Xx"), "formule invalide -> HORS")
check(leve(R.nombre_oxydation, "h2o", "H"), "minuscule en tête -> HORS")
check(leve(R.nombre_oxydation, "", "H"), "formule vide -> HORS")
check(leve(R.nombre_oxydation, "H2O(", "O"), "parenthèse déséquilibrée -> HORS")
# argument élément invalide
check(leve(R.nombre_oxydation, "H2O", 8), "élément non-str -> HORS")
check(leve(R.nombre_oxydation, "H2O", ""), "élément vide -> HORS")

# ── 5) equilibre_electronique : ancres + soundness ──
check(R.equilibre_electronique(2, 3) == 1, "Fe2+ -> Fe3+ : 1 électron")
check(R.equilibre_electronique(7, 2) == 5, "MnO4- -> Mn2+ : 5 électrons")
check(R.equilibre_electronique(-1, 0) == 1, "Cl- -> 0 : 1 électron")
check(R.equilibre_electronique(0, 0) == 0, "aucun changement : 0 électron")
check(R.equilibre_electronique(-2, 6) == 8, "S -2 -> +6 : 8 électrons")
check(leve(R.equilibre_electronique, 2.5, 3), "n.o. non entier -> HORS")
check(leve(R.equilibre_electronique, "a", 3), "n.o. non-int -> HORS")
check(leve(R.equilibre_electronique, True, 3), "bool n'est pas un n.o. -> HORS")

# ── 6) DÉTERMINISME ──
check(R.nombre_oxydation("KMnO4", "Mn") == R.nombre_oxydation("KMnO4", "Mn"), "déterministe Mn")
check(R.equilibre_electronique(7, 2) == R.equilibre_electronique(7, 2), "déterministe électrons")

print(f"\n=== valide_redox : {ok}/{ok+ko} ===")
import sys
sys.exit(0 if ko == 0 else 1)
