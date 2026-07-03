"""
VALIDE chimie.py — held-out ADVERSE. Exactitude des masses molaires (références externes) + soundness :
élément inconnu / formule malformée -> HORS (jamais une masse inventée). Aucun de ces cas n'est dans __main__.
"""
import chimie as K

ok = 0
ko = 0


def check(cond, label):
    global ok, ko
    if cond:
        ok += 1
    else:
        ko += 1
        print(f"  FAIL: {label}")


# 1) EXACTITUDE — masses molaires de référence (held-out ; tolérance 0.05 g/mol = arrondis de table).
REF = {
    "O2": 31.998, "N2": 28.014, "NH3": 17.031, "CH4": 16.043, "C2H6": 30.069,
    "C2H5OH": 46.069, "HCl": 36.458, "NaOH": 39.997, "KOH": 56.106, "HNO3": 63.012,
    "H3PO4": 97.994, "KMnO4": 158.032, "Al2O3": 101.961, "MgSO4": 120.366,
    "C6H6": 78.114, "NaHCO3": 84.007, "K2Cr2O7": 294.182, "Ca3(PO4)2": 310.174,
    "AgNO3": 169.872, "BaCl2": 208.227,
}
for f, attendu in REF.items():
    st, m = K.masse_molaire(f)
    check(st == K.VERIFIE and m is not None and abs(m - attendu) < 0.05,
          f"masse {f} = {attendu} (obtenu {m})")

# 2) PARENTHÈSES / GROUPES / HYDRATES gérés exactement (held-out).
check(K.masse_molaire("Ca(OH)2")[1] == 74.092, "Ca(OH)2")
check(K.masse_molaire("(NH4)2SO4")[1] == 132.134, "(NH4)2SO4")
check(K.masse_molaire("Fe2(SO4)3")[1] == 399.858, "Fe2(SO4)3")
check(K.masse_molaire("CuSO4.5H2O")[1] == 249.677, "hydrate CuSO4.5H2O (point)")
check(K.masse_molaire("CuSO4*5H2O")[1] == 249.677, "hydrate (*)")
check(K.masse_molaire("CuSO4·5H2O")[1] == 249.677, "hydrate (·)")
check(K.masse_molaire("K4[Fe(CN)6]")[0] == K.VERIFIE, "crochets imbriqués valides")

# 3) NB ATOMES (structurel, mais éléments réels exigés).
check(K.nb_atomes("H2O") == (K.VERIFIE, 3), "atomes H2O=3")
check(K.nb_atomes("(NH4)2SO4") == (K.VERIFIE, 15), "atomes (NH4)2SO4=15")
check(K.nb_atomes("C6H12O6") == (K.VERIFIE, 24), "atomes glucose=24")

# 4) % MASSIQUE.
st, p = K.pourcentage_massique("H2O", "O")
check(st == K.VERIFIE and abs(p - 88.81) < 0.05, f"%O dans H2O ~88.81 (obtenu {p})")
st, p = K.pourcentage_massique("CO2", "C")
check(st == K.VERIFIE and abs(p - 27.29) < 0.1, f"%C dans CO2 ~27.29 (obtenu {p})")
check(K.pourcentage_massique("H2O", "Na")[0] == K.HORS, "%Na dans H2O -> HORS (absent)")
check(K.pourcentage_massique("H2O", "Xx")[0] == K.HORS, "% élément inconnu -> HORS")

# 5) SOUNDNESS — élément INCONNU du référentiel -> HORS (jamais inventé).
for f in ["Xx2", "Zz", "Qq3", "Uue", "AbCd"]:
    check(K.masse_molaire(f)[0] == K.HORS, f"élément inconnu {f} -> HORS")
    check(K.composition(f)[0] == K.HORS, f"composition élément inconnu {f} -> HORS")
    check(K.nb_atomes(f)[0] == K.HORS, f"nb_atomes élément inconnu {f} -> HORS")

# 6) SOUNDNESS — formule MALFORMÉE -> HORS.
for f in ["h2o", "Ca(OH", "Ca(OH))2", "(", ")", "2", "H2..O", "H2*", "*H2O", "C-O", "", "  ", "H 2 O extra!"]:
    check(K.masse_molaire(f)[0] == K.HORS, f"malformé {f!r} -> HORS")

# 7) Entrées non-str -> HORS (robustesse).
for bad in [None, 123, ["H2O"], 3.14]:
    check(K.masse_molaire(bad)[0] == K.HORS, f"non-str {bad!r} -> HORS")

# 8) NL SOUND : extraction VALIDÉE par le parseur (formule invalide -> HORS, jamais un faux).
st, v, fr = K.repond_nl("Quelle est la masse molaire de H2SO4 ?")
check(st == K.VERIFIE and abs(v - 98.072) < 0.05 and fr == "H2SO4", "NL masse molaire H2SO4")
st, v, fr = K.repond_nl("masse molaire de NaCl")
check(st == K.VERIFIE and abs(v - 58.44) < 0.05, "NL NaCl")
check(K.repond_nl("masse molaire de Xx9")[0] == K.HORS, "NL formule inconnue -> HORS")
check(K.repond_nl("quelle heure est-il ?")[0] == K.HORS, "NL hors gabarit -> HORS")
check(K.repond_nl(None)[0] == K.HORS, "NL non-str -> HORS")

# 9) DÉTERMINISME.
check(K.masse_molaire("C6H12O6") == K.masse_molaire("C6H12O6"), "déterminisme")

# 10) Casse d'élément respectée : 'CO' (carbone+oxygène) != 'Co' (cobalt).
mco = K.masse_molaire("CO")[1]
mcobalt = K.masse_molaire("Co")[1]
check(abs(mco - (12.011 + 15.999)) < 0.001, "CO = C+O")
check(abs(mcobalt - 58.933) < 0.001, "Co = cobalt")
check(mco != mcobalt, "CO != Co (casse significative)")

print(f"\n=== valide_chimie : {ok}/{ok+ko} ===")
import sys
sys.exit(0 if ko == 0 else 1)
