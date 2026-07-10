"""
VALIDE nomenclature_organique.py — held-out ADVERSE.

ANCRES NON CIRCULAIRES (savoir chimique écrit EN DUR, jamais recalculé par la fonction testée) :
  • Noms d'alcanes 1..12 : méthane, éthane, propane, butane, pentane, hexane, heptane, octane, nonane,
    décane, undécane, dodécane (nomenclature IUPAC classique).
  • Formules brutes de référence : C4H10 (butane), C3H6 (propène), C2H2 (acétylène/éthyne), C2H6O (éthanol),
    C2H4O2 (acide acétique), CH4 (méthane), C3H6O (propanal/propanone).
  • ANCRE D'AMBIGUÏTÉ : C3H6O est à la fois un aldéhyde (propanal) ET une cétone (propanone) — isomères.
    C2H6O est à la fois un alcool (éthanol) ET un éther (diméthyléther). Un module qui n'en rendrait qu'un
    seul serait FAUX. C6H6 (benzène) est cyclique -> hors périmètre -> ValueError.

SOUNDNESS : n hors [1,12], bool/str/float/NaN/inf, famille inconnue, chaîne trop courte pour la fonction,
formule mal formée / élément hors {C,H,O,N} / cyclique -> ValueError. Déterminisme vérifié.
"""
import nomenclature_organique as N

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
    """True ssi fn(*a) lève ValueError (abstention structurelle)."""
    try:
        fn(*a)
        return False
    except ValueError:
        return True


# ── 1) ALCANES 1..12 (ancres non circulaires écrites en dur) ──
ALCANES = [
    (1, "méthane"), (2, "éthane"), (3, "propane"), (4, "butane"),
    (5, "pentane"), (6, "hexane"), (7, "heptane"), (8, "octane"),
    (9, "nonane"), (10, "décane"), (11, "undécane"), (12, "dodécane"),
]
for n, attendu in ALCANES:
    check(N.nom_alcane(n) == attendu, f"nom_alcane({n}) = {attendu}")

# ── 2) INVERSE carbones_depuis_nom : round-trip + indulgence accents ──
for n, nom in ALCANES:
    check(N.carbones_depuis_nom(nom) == n, f"carbones_depuis_nom({nom}) = {n}")
check(N.carbones_depuis_nom("Méthane") == 1, "carbones_depuis_nom insensible à la casse")
check(N.carbones_depuis_nom("methane") == 1, "carbones_depuis_nom indulgent aux accents")
check(leve(N.carbones_depuis_nom, "butène"), "carbones_depuis_nom('butène') (pas un alcane) -> ValueError")
check(leve(N.carbones_depuis_nom, "tridécane"), "carbones_depuis_nom(n=13) -> ValueError")

# ── 3) NOM DE CHAÎNE par famille (ancres chimiques directes) ──
check(N.nom_chaine(2, "alcène") == "éthène", "nom_chaine(2,alcène) = éthène")
check(N.nom_chaine(3, "alcène") == "propène", "nom_chaine(3,alcène) = propène")
check(N.nom_chaine(2, "alcyne") == "éthyne", "nom_chaine(2,alcyne) = éthyne")
check(N.nom_chaine(1, "alcool") == "méthanol", "nom_chaine(1,alcool) = méthanol")
check(N.nom_chaine(2, "alcool") == "éthanol", "nom_chaine(2,alcool) = éthanol")
check(N.nom_chaine(1, "aldéhyde") == "méthanal", "nom_chaine(1,aldéhyde) = méthanal")
check(N.nom_chaine(2, "aldéhyde") == "éthanal", "nom_chaine(2,aldéhyde) = éthanal")
check(N.nom_chaine(3, "cétone") == "propanone", "nom_chaine(3,cétone) = propanone")
check(N.nom_chaine(4, "cétone") == "butanone", "nom_chaine(4,cétone) = butanone")
check(N.nom_chaine(1, "acide carboxylique") == "acide méthanoïque", "nom_chaine(1,acide) = acide méthanoïque")
check(N.nom_chaine(2, "acide carboxylique") == "acide éthanoïque", "nom_chaine(2,acide) = acide éthanoïque")
check(N.nom_chaine(1, "amine") == "méthanamine", "nom_chaine(1,amine) = méthanamine")
check(N.nom_chaine(1, "alcane") == "méthane", "nom_chaine(1,alcane) = méthane (cohérent nom_alcane)")
check(N.nom_chaine(3, "alcane") == N.nom_alcane(3), "nom_chaine alcane == nom_alcane (2e chemin)")
# indulgence aux accents sur la famille
check(N.nom_chaine(2, "alcene") == "éthène", "nom_chaine famille indulgente aux accents")

# chaîne trop courte pour la fonction -> abstention
check(leve(N.nom_chaine, 1, "alcène"), "nom_chaine(1,alcène) (méthène inexistant) -> ValueError")
check(leve(N.nom_chaine, 1, "alcyne"), "nom_chaine(1,alcyne) -> ValueError")
check(leve(N.nom_chaine, 2, "cétone"), "nom_chaine(2,cétone) (cétone en C2 inexistante) -> ValueError")
check(leve(N.nom_chaine, 2, "éther"), "nom_chaine(éther) non systématique -> ValueError")

# ── 4) FORMULE BRUTE (ancres imposées) ──
check(N.formule_brute(4, "alcane") == "C4H10", "formule_brute(4,alcane) = C4H10")
check(N.formule_brute(3, "alcène") == "C3H6", "formule_brute(3,alcène) = C3H6")
check(N.formule_brute(2, "alcyne") == "C2H2", "formule_brute(2,alcyne) = C2H2 (acétylène)")
check(N.formule_brute(2, "alcool") == "C2H6O", "formule_brute(2,alcool) = C2H6O (éthanol)")
check(N.formule_brute(2, "acide carboxylique") == "C2H4O2", "formule_brute(2,acide) = C2H4O2 (acide acétique)")
check(N.formule_brute(1, "alcane") == "CH4", "formule_brute(1,alcane) = CH4")
check(N.formule_brute(2, "aldéhyde") == "C2H4O", "formule_brute(2,aldéhyde) = C2H4O (éthanal)")
check(N.formule_brute(3, "cétone") == "C3H6O", "formule_brute(3,cétone) = C3H6O (propanone)")
check(N.formule_brute(1, "acide carboxylique") == "CH2O2", "formule_brute(1,acide) = CH2O2 (acide formique)")
check(N.formule_brute(1, "amine") == "CH5N", "formule_brute(1,amine) = CH5N (méthanamine)")
check(leve(N.formule_brute, 1, "alcène"), "formule_brute(1,alcène) trop court -> ValueError")
check(leve(N.formule_brute, 2, "cétone"), "formule_brute(2,cétone) trop court -> ValueError")

# ── 5) IDENTIFICATION — le point FAUX=0 (LISTE, jamais un composé unique) ──
r_c3h6o = N.identifie("C3H6O")
check("aldéhyde" in r_c3h6o and "cétone" in r_c3h6o,
      "identifie(C3H6O) contient ALDÉHYDE ET CÉTONE (isomères propanal/propanone)")
check(isinstance(r_c3h6o, list), "identifie rend une LISTE")
check("alcool" not in r_c3h6o, "identifie(C3H6O) n'inclut PAS l'alcool (H ne colle pas)")

r_c2h6o = N.identifie("C2H6O")
check("alcool" in r_c2h6o and "éther" in r_c2h6o,
      "identifie(C2H6O) contient ALCOOL ET ÉTHER (éthanol/diméthyléther)")

check(N.identifie("CH4") == ["alcane"], "identifie(CH4) = [alcane] seul")
check(N.identifie("C3H6") == ["alcène"], "identifie(C3H6) = [alcène] (cyclopropane hors périmètre)")
check(N.identifie("C2H4O2") == ["acide carboxylique"], "identifie(C2H4O2) = [acide carboxylique]")
check(N.identifie("CH2O") == ["aldéhyde"], "identifie(CH2O) = [aldéhyde] (méthanal)")
check(N.identifie("CH4O") == ["alcool"], "identifie(CH4O) = [alcool] (méthanol, pas d'éther en C1)")
check("amine" in N.identifie("CH5N"), "identifie(CH5N) contient amine")

# abstentions d'identification
check(leve(N.identifie, "C6H6"), "identifie(C6H6) benzène cyclique -> ValueError")
check(leve(N.identifie, "CO2"), "identifie(CO2) inorganique -> ValueError")
check(leve(N.identifie, "H2O"), "identifie(H2O) sans carbone -> ValueError")
check(leve(N.identifie, "C13H28"), "identifie(n>12) -> ValueError")
check(leve(N.identifie, "NaCl"), "identifie(NaCl) élément hors CHON -> ValueError")
check(leve(N.identifie, "C2H4Cl2"), "identifie(halogéné) hors CHON -> ValueError")

# COHÉRENCE croisée : identifie(formule_brute(n,fam)) contient fam (2e chemin de code)
for n, fam in [(4, "alcane"), (3, "alcène"), (2, "alcyne"), (2, "alcool"),
               (3, "aldéhyde"), (3, "cétone"), (2, "acide carboxylique"), (1, "amine")]:
    check(fam in N.identifie(N.formule_brute(n, fam)),
          f"cohérence identifie(formule_brute({n},{fam})) contient {fam}")

# ── 6) GROUPE FONCTIONNEL (formules de groupe, ancres directes) ──
check(N.groupe_fonctionnel("alcool") == "-OH", "groupe alcool = -OH")
check(N.groupe_fonctionnel("acide carboxylique") == "-COOH", "groupe acide = -COOH")
check(N.groupe_fonctionnel("amine") == "-NH2", "groupe amine = -NH2")
check(N.groupe_fonctionnel("aldéhyde") == "-CHO", "groupe aldéhyde = -CHO")
check(N.groupe_fonctionnel("cétone") == ">C=O", "groupe cétone = >C=O")
check(N.groupe_fonctionnel("alcène") == "C=C", "groupe alcène = C=C")
check(N.groupe_fonctionnel("alcyne") == "C≡C", "groupe alcyne = C≡C")
check(leve(N.groupe_fonctionnel, "alcane"), "groupe_fonctionnel(alcane) sans groupe -> ValueError")
check(leve(N.groupe_fonctionnel, "ester"), "groupe_fonctionnel famille inconnue -> ValueError")

# ── 7) SOUNDNESS — n hors bornes / types invalides ──
check(leve(N.nom_alcane, 0), "nom_alcane(0) -> ValueError")
check(leve(N.nom_alcane, 13), "nom_alcane(13) -> ValueError")
check(leve(N.nom_alcane, -3), "nom_alcane(-3) -> ValueError")
check(leve(N.nom_alcane, True), "nom_alcane(bool) -> ValueError")
check(leve(N.nom_alcane, 2.0), "nom_alcane(float) -> ValueError")
check(leve(N.nom_alcane, "3"), "nom_alcane(str) -> ValueError")
check(leve(N.nom_alcane, float("nan")), "nom_alcane(NaN) -> ValueError")
check(leve(N.nom_alcane, float("inf")), "nom_alcane(inf) -> ValueError")
check(leve(N.nom_chaine, 3, "inconnue"), "nom_chaine famille inconnue -> ValueError")
check(leve(N.nom_chaine, 3, 5), "nom_chaine famille non-str -> ValueError")
check(leve(N.formule_brute, 13, "alcane"), "formule_brute(13) -> ValueError")
check(leve(N.formule_brute, 3, "ester"), "formule_brute famille inconnue -> ValueError")

# ── 8) SOUNDNESS — formule mal formée ──
check(leve(N.identifie, ""), "identifie('') -> ValueError")
check(leve(N.identifie, "c3h6o"), "identifie(minuscules) mal formée -> ValueError")
check(leve(N.identifie, "C3(H6)O"), "identifie(parenthèses) -> ValueError")
check(leve(N.identifie, "C3H6O+"), "identifie(charge) -> ValueError")
check(leve(N.identifie, 42), "identifie(non-str) -> ValueError")
check(leve(N.identifie, "C0H4"), "identifie(compte nul) -> ValueError")

# ── 9) DÉTERMINISME ──
check(N.nom_alcane(6) == N.nom_alcane(6), "déterminisme nom_alcane")
check(N.identifie("C3H6O") == N.identifie("C3H6O"), "déterminisme identifie")
check(N.formule_brute(5, "alcool") == N.formule_brute(5, "alcool"), "déterminisme formule_brute")

print(f"\n=== valide_nomenclature_organique : {ok}/{ok+ko} ===")
import sys
sys.exit(0 if ko == 0 else 1)
