"""VALIDE stoechiometrie.py — ADVERSE, FAUX=0. Réactions CONNUES (combustions, redox) + CONSERVATION des atomes
re-vérifiée indépendamment (parse des coefficients rendus) + minimalité (pgcd=1) + SOUNDNESS (équation impossible /
formule invalide -> ValueError)."""
from math import gcd

import chimie
import stoechiometrie as S

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


def conserve(reactifs, produits, coeffs):
    """Vérifie INDÉPENDAMMENT que chaque élément est conservé avec ces coefficients."""
    esp = list(reactifs) + list(produits)
    nr = len(reactifs)
    bilan = {}
    for j, f in enumerate(esp):
        _, comp = chimie.composition(f)
        signe = 1 if j < nr else -1
        for el, k in comp.items():
            bilan[el] = bilan.get(el, 0) + signe * coeffs[j] * k
    return all(v == 0 for v in bilan.values())


# RÉACTIONS CONNUES — coefficients attendus
CAS = [
    (["H2", "O2"], ["H2O"], [2, 1, 2]),
    (["CH4", "O2"], ["CO2", "H2O"], [1, 2, 1, 2]),
    (["Fe", "O2"], ["Fe2O3"], [4, 3, 2]),
    (["C2H6", "O2"], ["CO2", "H2O"], [2, 7, 4, 6]),
    (["C3H8", "O2"], ["CO2", "H2O"], [1, 5, 3, 4]),       # combustion du propane
    (["Al", "HCl"], ["AlCl3", "H2"], [2, 6, 2, 3]),
    (["N2", "H2"], ["NH3"], [1, 3, 2]),                    # Haber
    (["KMnO4", "HCl"], ["KCl", "MnCl2", "H2O", "Cl2"], [2, 16, 2, 2, 8, 5]),
]
for r, p, attendu in CAS:
    c = S.equilibre(r, p)
    check(c == attendu, f"{'+'.join(r)} -> {'+'.join(p)} : {c} (attendu {attendu})")
    check(conserve(r, p, c), f"conservation atomes : {'+'.join(r)} -> {'+'.join(p)}")

# MINIMALITÉ : pgcd des coefficients = 1
for r, p, _ in CAS:
    c = S.equilibre(r, p)
    g = 0
    for x in c:
        g = gcd(g, x)
    check(g == 1, f"coefficients minimaux (pgcd=1) : {'+'.join(r)}")

# texte rendu
check(S.equation_equilibree(["H2", "O2"], ["H2O"]) == "2 H2 + O2 -> 2 H2O", "rendu texte correct")

# SOUNDNESS — équations impossibles / formules invalides
check(leve(S.equilibre, ["H2"], ["O2"]), "H2 -> O2 (éléments incompatibles) -> ValueError")
check(leve(S.equilibre, ["CO2"], ["CO"]), "CO2 -> CO non équilibrable -> ValueError")
check(leve(S.equilibre, ["Xx2"], ["Yy"]), "formule invalide -> ValueError")
check(leve(S.equilibre, [], ["H2O"]), "réactifs vides -> ValueError")
check(leve(S.equilibre, ["h2o"], ["H2O"]), "formule minuscule invalide -> ValueError")

# DÉTERMINISME
check(S.equilibre(["CH4", "O2"], ["CO2", "H2O"]) == S.equilibre(["CH4", "O2"], ["CO2", "H2O"]), "déterminisme")

print(f"\n=== valide_stoechiometrie : {ok}/{ok + ko} ===")
import sys
sys.exit(0 if ko == 0 else 1)
