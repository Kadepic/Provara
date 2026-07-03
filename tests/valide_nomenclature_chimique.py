"""
VALIDE nomenclature_chimique.py — held-out ADVERSE. FAUX=0.

Ancres = noms IUPAC/traditionnels CONNUS (faits établis, vérifiés à la main, NON recalculés par la même
expression) : composés exigés par la spec + binaires moléculaires systématiques de référence.
Soundness : symbole irréel / formule complexe / hors domaine sûr / valence variable / peroxyde -> ValueError
(jamais un nom inventé). Déterminisme.
"""
import nomenclature_chimique as N

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
    try:
        fn(*a)
        return False
    except ValueError:
        return True
    except Exception:
        return False


def nom(f):
    return N.nom_compose_binaire(f)


# ── 1) CAS EXIGÉS PAR LA SPÉCIFICATION (catalogue de faits établis) ──
check(nom("CO2") == "dioxyde de carbone", "CO2")
check(nom("CO") == "monoxyde de carbone", "CO")
check(nom("H2O") == "eau", "H2O")
check(nom("NaCl") == "chlorure de sodium", "NaCl")
check(nom("CaO") == "oxyde de calcium", "CaO")
check(nom("NH3") == "ammoniac", "NH3")
check(nom("SO2") == "dioxyde de soufre", "SO2")
check(nom("N2O") == "protoxyde d'azote", "N2O")

# ── 2) RÈGLE SYSTÉMATIQUE — binaires moléculaires (noms IUPAC de référence) ──
check(nom("SO3") == "trioxyde de soufre", "SO3 systématique")
check(nom("NO2") == "dioxyde d'azote", "NO2 (élision d')")
check(nom("N2O3") == "trioxyde de diazote", "N2O3")
check(nom("N2O4") == "tétroxyde de diazote", "N2O4 (tétroxyde)")
check(nom("N2O5") == "pentoxyde de diazote", "N2O5 (pentoxyde)")
check(nom("P2O5") == "pentoxyde de diphosphore", "P2O5")
check(nom("CCl4") == "tétrachlorure de carbone", "CCl4")
check(nom("SF6") == "hexafluorure de soufre", "SF6")
check(nom("SF4") == "tétrafluorure de soufre", "SF4")
check(nom("CF4") == "tétrafluorure de carbone", "CF4")
check(nom("PCl3") == "trichlorure de phosphore", "PCl3")
check(nom("PCl5") == "pentachlorure de phosphore", "PCl5")
check(nom("CS2") == "disulfure de carbone", "CS2")
check(nom("SiO2") == "dioxyde de silicium", "SiO2")
check(nom("B2O3") == "trioxyde de dibore", "B2O3")
check(nom("ClO2") == "dioxyde de chlore", "ClO2")
check(nom("Cl2O7") == "heptoxyde de dichlore", "Cl2O7")
check(nom("OF2") == "difluorure d'oxygène", "OF2 (O cation, d'oxygène)")
check(nom("ClF3") == "trifluorure de chlore", "ClF3")
check(nom("BrF5") == "pentafluorure de brome", "BrF5")
check(nom("SCl2") == "dichlorure de soufre", "SCl2")

# ── 3) CATALOGUE — ioniques valence fixe (PAS de préfixes) & y=1 ──
check(nom("NO") == "monoxyde d'azote", "NO")
check(nom("HCl") == "chlorure d'hydrogène", "HCl")
check(nom("H2S") == "sulfure d'hydrogène", "H2S")
check(nom("KBr") == "bromure de potassium", "KBr")
check(nom("CaCl2") == "chlorure de calcium", "CaCl2 (ionique, sans 'di')")
check(nom("MgO") == "oxyde de magnésium", "MgO")
check(nom("Al2O3") == "oxyde d'aluminium", "Al2O3")

# ── 4) PRÉFIXES + NOMS D'ÉLÉMENTS (mécanismes exacts) ──
check(N.prefixe(1) == "mono" and N.prefixe(4) == "tétra" and N.prefixe(7) == "hepta", "préfixes 1/4/7")
check(N.nom_element("O") == "oxygène" and N.nom_element("Na") == "sodium", "noms d'éléments")

# ── 5) SOUNDNESS — abstention (ValueError), JAMAIS un nom inventé ──
check(leve(N.nom_compose_binaire, "XyZ"), "symbole irréel Xy -> ValueError")
check(leve(N.nom_compose_binaire, "Qx2"), "élément inexistant Q -> ValueError")
check(leve(N.nom_compose_binaire, "co2"), "minuscule en tête -> ValueError")
check(leve(N.nom_compose_binaire, "H2O2"), "peroxyde H2O2 -> abstention (pas 'dioxyde de dihydrogène')")
check(leve(N.nom_compose_binaire, "FeCl3"), "valence variable Fe -> abstention")
check(leve(N.nom_compose_binaire, "CuO"), "valence variable Cu -> abstention")
check(leve(N.nom_compose_binaire, "C6H12O6"), "composé complexe (3 éléments) -> abstention")
check(leve(N.nom_compose_binaire, "Ca(OH)2"), "parenthèses (complexe) -> ValueError")
check(leve(N.nom_compose_binaire, "CuSO4·5H2O"), "hydrate (complexe) -> ValueError")
check(leve(N.nom_compose_binaire, "Na+"), "charge -> ValueError")
check(leve(N.nom_compose_binaire, ""), "chaîne vide -> ValueError")
check(leve(N.nom_compose_binaire, "O2"), "élément seul (non binaire) -> abstention")
check(leve(N.nom_compose_binaire, 42), "non-chaîne -> ValueError")
check(leve(N.nom_compose_binaire, "KF2"), "binaire ionique inconnu/incohérent -> abstention")
check(leve(N.prefixe, 0), "préfixe(0) -> ValueError")
check(leve(N.prefixe, 11), "préfixe(11) -> ValueError")
check(leve(N.prefixe, True), "préfixe(bool) -> ValueError")
check(leve(N.nom_element, "Zz"), "nom_element inconnu -> ValueError")

# ── 6) DÉTERMINISME ──
check(nom("CO2") == nom("CO2") and nom("SO3") == nom("SO3"), "déterminisme")

print(f"\n=== valide_nomenclature_chimique : {ok}/{ok+ko} ===")
import sys
sys.exit(0 if ko == 0 else 1)
