"""
VALIDE nomenclatures.py — held-out ADVERSE.

ANCRES EXTERNES NON CIRCULAIRES (tables publiées, écrites en dur dans la gate) :
  • ISCO-08 (OIT) : 10 grands groupes. Le grand groupe 2 (« professions intellectuelles et scientifiques »)
    est de niveau de compétence 4 ; le 9 (« professions élémentaires ») de niveau 1 ; le 0 (forces armées)
    en couvre TROIS (1, 2 et 4) et le 1 (directeurs) en couvre DEUX (3 et 4) — un module qui rendrait un
    scalaire serait FAUX. Cardinalités officielles : 10 / 43 / 130 / 436.
  • Le premier chiffre d'un code ISCO EST son grand groupe : « 7512.1 » (boulanger, ingéré d'ESCO) -> « 7 »
    (« métiers qualifiés de l'industrie et de l'artisanat »), ce qui est cohérent avec le métier.
  • Dewey (OCLC) : 510 = Mathématiques, 530 = Physique, 590 = Zoologie.
  • NACE Rév. 2 (Eurostat) : 21 sections, A = agriculture, F = construction, U = extraterritorial.

ANCRE D'HONNÊTETÉ : MSC2020, ACM CCS, CIM-11 et ROME sont CITÉES mais leur contenu n'est PAS embarqué.
`classes()` doit y lever ValueError. Énumérer 63 classes MSC de mémoire produirait des faux plausibles —
c'est exactement ce que la gate interdit.

SOUNDNESS : code hors 0..9, code mal formé, division Dewey hors 500..590, section NACE hors A..U,
classification inconnue, bool/int/None -> ValueError. Déterminisme et invariants vérifiés.
"""
import sys

import nomenclatures as N

ok = 0
ko = 0


def check(cond, label):
    global ok, ko
    if cond:
        ok += 1
    else:
        ko += 1
        print(f"  FAIL: {label}")


def leve(fn, *a, **k):
    try:
        fn(*a, **k)
        return False
    except ValueError:
        return True


# ── 1) ISCO-08 : les 10 grands groupes ──
gg = N.grands_groupes_isco()
check(len(gg) == 10, "ISCO-08 : exactement 10 grands groupes")
check(set(gg) == set("0123456789"), "ISCO-08 : codes '0' à '9'")
check(len(set(gg.values())) == 10, "ISCO-08 : 10 intitulés DISTINCTS")
check("Forces armées" in N.grand_groupe_isco("0"), "grand groupe 0 = forces armées")
check("intellectuelles" in N.grand_groupe_isco("2"), "grand groupe 2 = professions intellectuelles")
check("élémentaires" in N.grand_groupe_isco("9"), "grand groupe 9 = professions élémentaires")
check("artisanat" in N.grand_groupe_isco("7"), "grand groupe 7 = industrie et artisanat")

# ── 2) NIVEAUX DE COMPÉTENCE : un tuple, jamais un scalaire ──
check(N.niveau_competence_isco("2") == (4,), "grand groupe 2 -> niveau 4")
check(N.niveau_competence_isco("9") == (1,), "grand groupe 9 -> niveau 1")
check(N.niveau_competence_isco("1") == (3, 4), "grand groupe 1 -> DEUX niveaux (3 et 4)")
check(N.niveau_competence_isco("0") == (1, 2, 4), "grand groupe 0 -> TROIS niveaux (1, 2 et 4)")
check(all(isinstance(N.niveau_competence_isco(c), tuple) for c in "0123456789"),
      "tous les niveaux sont des tuples (aucune réduction abusive)")
check(all(all(n in (1, 2, 3, 4) for n in N.niveau_competence_isco(c)) for c in "0123456789"),
      "tous les niveaux sont dans 1..4")

# ── 3) CARDINALITÉS OFFICIELLES ──
card = N.cardinalites_isco()
check(card["grands_groupes"] == 10, "10 grands groupes")
check(card["sous_grands_groupes"] == 43, "43 sous-grands groupes")
check(card["sous_groupes"] == 130, "130 sous-groupes")
check(card["groupes_de_base"] == 436, "436 groupes de base")
check(card["grands_groupes"] == len(gg), "cardinalité cohérente avec le contenu (chemin indépendant)")

# ── 4) LE PREMIER CHIFFRE EST LE GRAND GROUPE (propriété de la nomenclature) ──
check(N.grand_groupe_du_code("7512.1") == "7", "code ESCO du boulanger « 7512.1 » -> grand groupe 7")
check("artisanat" in N.grand_groupe_isco(N.grand_groupe_du_code("7512.1")),
      "le boulanger tombe bien dans « industrie et artisanat » (cohérence métier/nomenclature)")
check(N.grand_groupe_du_code("2250.3") == "2", "vétérinaire « 2250.3 » -> professions intellectuelles")
check(N.grand_groupe_du_code("9") == "9", "code d'un seul chiffre accepté")
check(leve(N.grand_groupe_du_code, "X512"), "code ne commençant pas par un chiffre -> ValueError")
check(leve(N.grand_groupe_du_code, ""), "code vide -> ValueError")

# ── 5) DEWEY ──
d = N.divisions_dewey_500()
check(len(d) == 10, "10 divisions dans la classe 500")
check(set(d) == {500, 510, 520, 530, 540, 550, 560, 570, 580, 590}, "divisions 500 à 590 par pas de 10")
check(N.division_dewey(510) == "Mathématiques", "510 = Mathématiques")
check("Physique" in N.division_dewey(530), "530 = Physique")
check("zoologie" in N.division_dewey(590).lower(), "590 = zoologie")
check(leve(N.division_dewey, 515), "515 n'est pas une division -> ValueError")
check(leve(N.division_dewey, 100), "100 est une CLASSE, pas une division du 500 -> ValueError")
check(leve(N.division_dewey, "510"), "division en str -> ValueError")
check(leve(N.division_dewey, True), "bool -> ValueError")
# délégation à bibliotheconomie, sans duplication
check(N.classe_principale_dewey(500) == "sciences", "classe 500 déléguée à bibliotheconomie")
check(leve(N.classe_principale_dewey, 550), "550 n'est pas une centaine -> ValueError (délégué)")

# ── 6) NACE ──
n = N.sections_nace()
check(len(n) == 21, "NACE Rév. 2 : exactement 21 sections")
check(set(n) == set("ABCDEFGHIJKLMNOPQRSTU"), "sections A à U")
check("Agriculture" in N.section_nace("A"), "section A = agriculture")
check(N.section_nace("F") == "Construction", "section F = construction")
check("extraterritoriales" in N.section_nace("U"), "section U = activités extraterritoriales")
check(N.section_nace("a") == N.section_nace("A"), "la casse est tolérée")
check(leve(N.section_nace, "V"), "section V -> ValueError (la NACE s'arrête à U)")
check(leve(N.section_nace, "AA"), "section à deux lettres -> ValueError")

# ── 7) ANCRE D'HONNÊTETÉ : le contenu non ingéré est DIT, jamais inventé ──
cl = N.classifications()
check(cl["ISCO-08"] is True and cl["Dewey"] is True and cl["NACE"] is True, "trois classifications ingérées")
check(cl["MSC2020"] is False and cl["ACM CCS"] is False, "MSC et ACM : contenu NON ingéré")
check(cl["CIM-11"] is False and cl["ROME"] is False, "CIM-11 et ROME : contenu NON ingéré")

for nom in ("MSC2020", "ACM CCS", "CIM-11", "ROME"):
    st = N.structure(nom)
    check(st["contenu_ingere"] is False, f"« {nom} » : structure connue, contenu NON ingéré")
    check(bool(st.get("editeur")), f"« {nom} » : l'éditeur est cité")
    check(leve(N.classes, nom), f"classes('{nom}') -> ValueError (jamais une énumération de mémoire)")

check(N.structure("ISCO-08")["contenu_ingere"] is True, "ISCO-08 : contenu ingéré")
check(N.structure("ISCO-08")["entrees_embarquees"] == 10, "ISCO-08 : 10 entrées embarquées")
check(len(N.classes("ISCO-08")) == 10, "classes('ISCO-08') -> 10")
check(len(N.classes("NACE")) == 21, "classes('NACE') -> 21")
check(len(N.classes("Dewey")) == 10, "classes('Dewey') -> 10 divisions")

# ── 8) SOUNDNESS ──
check(leve(N.grand_groupe_isco, "10"), "grand groupe '10' -> ValueError")
check(leve(N.grand_groupe_isco, "a"), "grand groupe 'a' -> ValueError")
check(leve(N.grand_groupe_isco, 2), "grand groupe en int -> ValueError")
check(leve(N.grand_groupe_isco, ""), "grand groupe vide -> ValueError")
check(leve(N.niveau_competence_isco, "12"), "niveau d'un code inconnu -> ValueError")
check(leve(N.structure, "ISO 9001"), "classification inconnue -> ValueError")
check(leve(N.classes, "CIM-10"), "classification inconnue pour classes() -> ValueError")
check(leve(N.section_nace, True), "bool -> ValueError")
check(leve(N.structure, None), "None -> ValueError")

# ── 9) IMMUTABILITÉ : les tables rendues sont des COPIES ──
gg2 = N.grands_groupes_isco()
gg2["0"] = "saboté"
check(N.grand_groupe_isco("0") != "saboté", "la table interne n'est pas mutable depuis l'extérieur")
d2 = N.divisions_dewey_500()
d2[510] = "saboté"
check(N.division_dewey(510) == "Mathématiques", "les divisions Dewey ne sont pas mutables")

# ── 10) DÉTERMINISME ──
check(N.grands_groupes_isco() == N.grands_groupes_isco(), "déterminisme des grands groupes")
check(N.structure("NACE") == N.structure("NACE"), "déterminisme de structure()")
check(N.grand_groupe_du_code("7512.1") == N.grand_groupe_du_code("7512.1"), "déterminisme du code")

print(f"\n=== valide_nomenclatures : {ok}/{ok+ko} ===")
sys.exit(0 if ko == 0 else 1)
