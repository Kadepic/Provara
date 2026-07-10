"""
VALIDE equivalences_diplomes.py — held-out ADVERSE.

ANCRES EXTERNES NON CIRCULAIRES (valeurs des cadres PUBLIÉS, écrites EN DUR, PAS recalculées par le module) :
  • CITE/ISCED 2011 a 9 niveaux (codes 0 à 8) ; CEC/EQF en a 8 (codes 1 à 8). Ces nombres DIFFÈRENT :
    un module qui leur donnerait le même nombre serait FAUX.
  • Baccalauréat français = CITE 3 (second cycle du secondaire), et NON CITE 4.
  • Licence = CITE 6 ; master = CITE 7 ; doctorat = CITE 8.
  • Le bachelor's degree américain et la licence française sont TOUS DEUX CITE 6 -> equivalent() les rapproche.
  • DISCRIMINATION CITE vs CEC : le baccalauréat est CITE 3 mais CEC 4 (programmes vs acquis) — les deux
    valeurs DIFFÈRENT ; un module qui les alignerait mécaniquement serait faux.
  • ABSTENTION CAPITALE : reconnaissance_juridique('licence','France','Allemagne') -> ValueError.

SOUNDNESS : diplôme/pays hors catalogue, CITE hors 0..8, CEC hors 1..8, bool, non-chaîne, mauvaise arité,
CEC hors espace UE (États-Unis) -> ValueError.
"""
import equivalences_diplomes as E

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


# ── 1) NOMBRE DE NIVEAUX : CITE=9 (0..8), CEC=8 (1..8), DIFFÉRENTS ──
check(E.nombre_niveaux_cite() == 9, "CITE a 9 niveaux (0..8)")          # ancre UNESCO
check(E.nombre_niveaux_cec() == 8, "CEC a 8 niveaux (1..8)")            # ancre UE 2017/C 189/03
check(E.nombre_niveaux_cite() != E.nombre_niveaux_cec(), "CITE (9) != CEC (8) — cadres distincts")

# ── 2) INTITULÉS CITE aux bornes et pivots (ancres écrites en dur) ──
check("petite enfance" in E.niveau_cite(0).lower(), "CITE 0 = petite enfance")
check("primaire" in E.niveau_cite(1).lower(), "CITE 1 = primaire")
check("cycle court" in E.niveau_cite(5).lower(), "CITE 5 = supérieur de cycle court")
check("doctorat" in E.niveau_cite(8).lower(), "CITE 8 = doctorat")

# ── 3) DESCRIPTEURS CEC fondés sur les ACQUIS ──
check("licence" in E.niveau_cec(6).lower(), "CEC 6 = niveau licence")
check("master" in E.niveau_cec(7).lower(), "CEC 7 = niveau master")
check("doctorat" in E.niveau_cec(8).lower(), "CEC 8 = niveau doctorat")

# ── 4) CATALOGUE FRANCE — niveaux CITE (ancres du cadre) ──
check(E.cite("baccalauréat", "France") == 3, "bac FR = CITE 3")
check(E.cite("baccalauréat", "France") != 4, "bac FR n'est PAS CITE 4")
check(E.cite("BTS", "France") == 5, "BTS FR = CITE 5")
check(E.cite("DUT", "France") == 5, "DUT FR = CITE 5")
check(E.cite("licence", "France") == 6, "licence FR = CITE 6")
check(E.cite("master", "France") == 7, "master FR = CITE 7")
check(E.cite("doctorat", "France") == 8, "doctorat FR = CITE 8")

# ── 5) DISCRIMINATION CITE vs CEC : bac = CITE 3 mais CEC 4 (valeurs DIFFÉRENTES) ──
check(E.cite("baccalauréat", "France") == 3 and E.cec("baccalauréat", "France") == 4,
      "bac : CITE 3 vs CEC 4")
check(E.cec("baccalauréat", "France") != E.cite("baccalauréat", "France"),
      "bac : CEC (4) != CITE (3) — acquis vs programmes")
check(E.cec("BTS", "France") == 5, "BTS FR = CEC 5")

# ── 6) AUTRES PAYS — ancres CITE imposées ──
check(E.cite("Abitur", "Allemagne") == 3, "Abitur DE = CITE 3")
check(E.cite("A-levels", "Royaume-Uni") == 3, "A-levels UK = CITE 3")
check(E.cite("bachelor's degree", "États-Unis") == 6, "bachelor's US = CITE 6")
check(E.cite("high school diploma", "États-Unis") == 3, "high school diploma US = CITE 3")
check(E.cite("Bachillerato", "Espagne") == 3, "Bachillerato ES = CITE 3")
check(E.cite("Diploma di maturità", "Italie") == 3, "maturità IT = CITE 3")

# ── 7) ALIAS / normalisation (accents, casse, apostrophes) ──
check(E.cite("bac", "france") == 3, "alias 'bac' + pays minuscule")
check(E.cite("BACHELOR", "Royaume-Uni") == 6, "alias 'BACHELOR' UK = CITE 6")
check(E.cite("licence", "FRANCE") == 6, "pays en majuscules")
check(E.cite("bachelor's degree", "usa") == 6, "pays alias 'usa'")

# ── 8) EQUIVALENT : licence FR ↔ bachelor's US (tous deux CITE 6) ──
eq = E.equivalent("licence", "France", "États-Unis")
check(isinstance(eq, dict) and "meme_niveau_cite" in eq and "avertissement" in eq,
      "equivalent renvoie dict {meme_niveau_cite, avertissement}")
check(eq["niveau_cite"] == 6, "equivalent licence -> niveau CITE 6")
check("bachelor's degree" in eq["meme_niveau_cite"], "licence FR ~ bachelor's US (CITE 6)")
# avertissement DOIT dire que le niveau n'emporte pas reconnaissance
avert = eq["avertissement"].lower()
check("reconnaissance" in avert and "enic" in avert.replace("-", ""),
      "avertissement : niveau != reconnaissance (ENIC-NARIC)")
check("niveau" in avert, "avertissement mentionne la comparabilité de niveau")
# master FR -> master's US (CITE 7), pas bachelor
eq7 = E.equivalent("master", "France", "États-Unis")
check("master's degree" in eq7["meme_niveau_cite"], "master FR ~ master's US (CITE 7)")
check("bachelor's degree" not in eq7["meme_niveau_cite"], "master FR NON ~ bachelor's US")
# bac FR (CITE 3) -> A-levels UK (CITE 3)
eq3 = E.equivalent("baccalauréat", "France", "Royaume-Uni")
check("A-levels" in eq3["meme_niveau_cite"], "bac FR ~ A-levels UK (CITE 3)")

# ── 9) ABSTENTION CAPITALE : reconnaissance_juridique -> TOUJOURS ValueError ──
check(leve(E.reconnaissance_juridique, "licence", "France", "Allemagne"),
      "reconnaissance_juridique(licence,FR,DE) -> ValueError")
check(leve(E.reconnaissance_juridique, "master", "France", "États-Unis"),
      "reconnaissance_juridique(master,FR,US) -> ValueError")
# même avec des entrées valides partout, elle s'abstient
check(leve(E.reconnaissance_juridique, "doctorat", "France", "Italie"),
      "reconnaissance_juridique jamais délivrée")

# ── 10) SOUNDNESS — hors catalogue ──
check(leve(E.cite, "diplome_invente_xyz", "France"), "diplôme inventé -> ValueError")
check(leve(E.cite, "licence", "Atlantide"), "pays hors catalogue -> ValueError")
check(leve(E.cite, "Abitur", "France"), "Abitur en France (mauvais pays) -> ValueError")
check(leve(E.equivalent, "diplome_bidon", "France", "Italie"), "equivalent diplôme bidon -> ValueError")
check(leve(E.equivalent, "licence", "France", "Narnia"), "equivalent pays2 inconnu -> ValueError")
check(leve(E.reconnaissance_juridique, "licence", "France", "Narnia"),
      "reconnaissance pays_accueil inconnu -> ValueError")

# ── 11) SOUNDNESS — CITE hors 0..8, CEC hors 1..8 ──
check(leve(E.niveau_cite, 9), "CITE 9 -> ValueError")
check(leve(E.niveau_cite, -1), "CITE -1 -> ValueError")
check(leve(E.niveau_cec, 0), "CEC 0 -> ValueError (CEC commence à 1)")
check(leve(E.niveau_cec, 9), "CEC 9 -> ValueError")

# ── 12) SOUNDNESS — CEC hors espace UE (États-Unis) -> abstention ──
check(E.cite("bachelor's degree", "États-Unis") == 6, "US a bien un niveau CITE")
check(leve(E.cec, "bachelor's degree", "États-Unis"), "CEC US -> ValueError (hors espace CEC/EQF)")
check(leve(E.cec, "high school diploma", "États-Unis"), "CEC US high school -> ValueError")

# ── 13) SOUNDNESS — types invalides (bool, non-chaîne, mauvaise arité) ──
check(leve(E.niveau_cite, True), "niveau_cite(bool) -> ValueError")
check(leve(E.niveau_cite, "3"), "niveau_cite(str) -> ValueError")
check(leve(E.niveau_cec, True), "niveau_cec(bool) -> ValueError")
check(leve(E.cite, 3, "France"), "cite(diplome non-chaîne) -> ValueError")
check(leve(E.cite, "licence", 42), "cite(pays non-chaîne) -> ValueError")

# ── 14) DÉTERMINISME ──
check(E.cite("licence", "France") == E.cite("licence", "France"), "déterminisme cite")
check(E.equivalent("licence", "France", "États-Unis") == E.equivalent("licence", "France", "États-Unis"),
      "déterminisme equivalent")
check(E.niveau_cite(6) == E.niveau_cite(6), "déterminisme niveau_cite")

# ── 15) CATALOGUE — introspection cohérente ──
check(set(E.catalogue_pays()) == {"France", "Allemagne", "Royaume-Uni", "Espagne", "Italie", "États-Unis"},
      "catalogue_pays = 6 pays")
check("licence" in E.diplomes("France"), "diplomes(France) contient licence")
check(leve(E.diplomes, "Atlantide"), "diplomes(pays inconnu) -> ValueError")

print(f"\n=== valide_equivalences_diplomes : {ok}/{ok+ko} ===")
import sys
sys.exit(0 if ko == 0 else 1)
