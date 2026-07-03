"""VALIDE chimie_quantitative.py — ADVERSE, FAUX=0. Ancres connues (combustion CH₄ ≈ −890 kJ/mol, pile Daniell
1.10 V, dilution c₁V₁=c₂V₂) + SOUNDNESS (volume/quantité invalide -> ValueError)."""
import chimie_quantitative as Q

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


# CONCENTRATIONS
check(Q.molarite(0.5, 2) == 0.25, "c = n/V = 0.25 mol/L")
check(Q.molarite(1, 1) == 1.0 and Q.molarite(0, 5) == 0.0, "molarité bords")
check(Q.dilution(2, 0.1, 0.5) == 0.4, "dilution c₂ = 0.4 M")
# loi de dilution vérifiée : c1·v1 = c2·v2
check(proche(2 * 0.1, Q.dilution(2, 0.1, 0.5) * 0.5), "c₁V₁ = c₂V₂")
check(Q.volume_dilution(2, 0.1, 0.25) == 0.8, "V₂ pour atteindre 0.25 M = 0.8 L")
check(Q.concentration_massique(58.5, 1) == 58.5, "concentration massique NaCl")

# THERMOCHIMIE (loi de Hess)
check(proche(Q.enthalpie_reaction([-393.5, 2 * -285.8], [-74.8, 0]), -890.3), "ΔH combustion CH₄ ≈ -890.3 kJ/mol")
check(proche(Q.enthalpie_reaction([-285.8], [0, 0]), -285.8), "ΔH formation H₂O = -285.8")
check(Q.enthalpie_reaction([0], [0]) == 0.0, "corps simples -> ΔH = 0")
check(Q.est_exothermique(-890.3) is True and Q.est_exothermique(180) is False, "exo ssi ΔH<0")

# ÉLECTROCHIMIE
check(proche(Q.potentiel_cellule(0.34, -0.76), 1.10), "pile Daniell Cu/Zn = 1.10 V")
check(proche(Q.potentiel_cellule(0.80, 0.34), 0.46), "pile Ag/Cu = 0.46 V")
check(Q.est_spontanee(1.10) is True and Q.est_spontanee(-0.5) is False, "spontanée ssi E°>0")
# une pile inversée a un potentiel opposé
check(proche(Q.potentiel_cellule(-0.76, 0.34), -Q.potentiel_cellule(0.34, -0.76)), "inversion -> E opposé")

# SOUNDNESS
check(leve(Q.molarite, 0.5, 0), "V=0 -> ValueError")
check(leve(Q.molarite, -1, 2), "moles<0 -> ValueError")
check(leve(Q.dilution, 2, 0.1, 0), "V2=0 -> ValueError")
check(leve(Q.concentration_massique, -5, 1), "masse<0 -> ValueError")
check(leve(Q.enthalpie_reaction, -100, [0]), "ΔH non-liste -> ValueError")
check(leve(Q.potentiel_cellule, "x", 0), "non-numérique -> ValueError")

# DÉTERMINISME
check(Q.potentiel_cellule(0.34, -0.76) == Q.potentiel_cellule(0.34, -0.76), "déterminisme")

print(f"\n=== valide_chimie_quantitative : {ok}/{ok + ko} ===")
import sys
sys.exit(0 if ko == 0 else 1)
