"""
VALIDE formats_locaux.py — held-out ADVERSE.

ANCRES EXTERNES NON CIRCULAIRES (conventions CLDR/ISO publiées, écrites EN DUR, jamais recalculées) :
  • France : décimal ',', milliers espace insécable (U+00A0), date JJ/MM/AAAA, 24 h, semaine commence lundi.
  • États-Unis : décimal '.', milliers ',', date MM/JJ/AAAA, 12 h, semaine commence dimanche.
  • Allemagne : décimal ',', milliers '.'.  • Suisse : milliers apostrophe (1'000'000).
  • Inde (ANCRE PIÈGE FORTE, système lakh/crore) : 1234567 -> « 12,34,567 » ; le groupement occidental
    « 1,234,567 » serait FAUX et doit être REJETÉ au parsing. 1 crore = 10 000 000 -> « 1,00,00,000 ».
  • Japon : date AAAA/MM/JJ, 24 h.  • Canada anglophone : date courte AAAA-MM-JJ (CLDR en-CA).
  • « 03/04/2024 » est AMBIGUË : France = (2024, 4, 3) = 3 avril, États-Unis = (2024, 3, 4) = 4 mars.
  • ISO 8601 « 2024-04-03 » : non ambiguë (une seule lecture possible dans tout le catalogue).
  • Bissextiles (règle grégorienne connue) : 2024 et 2000 OUI, 2023 et 2100 NON -> 29/02 accepté/refusé.
BOUCLE FERMÉE : parse_nombre(formate_nombre(x, pays), pays) == x pour 200+ valeurs × les 11 pays.
SOUNDNESS : pays hors catalogue, bool/str/NaN/±inf, date invalide, groupement faux, texte non parsable
-> ValueError. DÉTERMINISME : deux appels identiques -> résultats identiques.
"""
import math

import formats_locaux as F

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


NBSP = " "       # espace insécable
NNBSP = " "      # espace fine insécable (CLDR moderne fr)
APO_TYPO = "’"   # apostrophe typographique (CLDR de-CH)

# ── 1) ANCRES CATALOGUE — FRANCE (CLDR fr) ──
check(F.separateur_decimal("France") == ",", "FR décimal ','")
check(F.separateur_milliers("France") == NBSP, "FR milliers = espace insécable U+00A0")
check(F.format_date("France") == "JJ/MM/AAAA", "FR date JJ/MM/AAAA")
check(F.format_heure("France") == 24, "FR 24 h")
check(F.premier_jour_semaine("France") == "lundi", "FR semaine commence lundi")
check(F.symbole_monetaire("France") == ("€", "apres"), "FR € après le montant")

# ── 2) ANCRES CATALOGUE — ÉTATS-UNIS (CLDR en-US) ──
check(F.separateur_decimal("États-Unis") == ".", "US décimal '.'")
check(F.separateur_milliers("États-Unis") == ",", "US milliers ','")
check(F.format_date("États-Unis") == "MM/JJ/AAAA", "US date MM/JJ/AAAA")
check(F.format_heure("États-Unis") == 12, "US 12 h")
check(F.premier_jour_semaine("États-Unis") == "dimanche", "US semaine commence dimanche")
check(F.symbole_monetaire("États-Unis") == ("$", "avant"), "US $ avant le montant")

# ── 3) ANCRES CATALOGUE — autres pays ──
check(F.separateur_decimal("Allemagne") == ",", "DE décimal ','")
check(F.separateur_milliers("Allemagne") == ".", "DE milliers '.'")
check(F.format_date("Allemagne") == "JJ.MM.AAAA", "DE date JJ.MM.AAAA")
check(F.separateur_milliers("Suisse") == "'", "CH milliers apostrophe")
check(F.separateur_decimal("Suisse") == ".", "CH décimal '.'")
check(F.format_date("Japon") == "AAAA/MM/JJ", "JP date AAAA/MM/JJ")
check(F.format_heure("Japon") == 24, "JP 24 h")
check(F.format_date("Canada") == "AAAA-MM-JJ", "CA anglophone date AAAA-MM-JJ (CLDR en-CA)")
check(F.format_date("Royaume-Uni") == "JJ/MM/AAAA", "GB date JJ/MM/AAAA")
check(F.separateur_decimal("Royaume-Uni") == ".", "GB décimal '.'")
check(F.premier_jour_semaine("Royaume-Uni") == "lundi", "GB semaine commence lundi")
check(F.separateur_decimal("Brésil") == ",", "BR décimal ','")
check(F.separateur_milliers("Brésil") == ".", "BR milliers '.'")
check(F.separateur_decimal("Russie") == ",", "RU décimal ','")
check(F.separateur_milliers("Russie") == NBSP, "RU milliers espace insécable")
check(F.format_date("Russie") == "JJ.MM.AAAA", "RU date JJ.MM.AAAA")
check(F.separateur_milliers("Inde") == ",", "IN milliers ','")
check(F.premier_jour_semaine("Inde") == "dimanche", "IN semaine commence dimanche")
check(F.FORMAT_ISO_8601 == "AAAA-MM-JJ", "ISO 8601 exposé = AAAA-MM-JJ")

# Normalisation du nom (accents/casse) — même entrée, jamais un pays deviné
check(F.separateur_decimal("etats-unis") == ".", "alias sans accents accepté (etats-unis)")
check(F.separateur_decimal("FRANCE") == ",", "casse indifférente (FRANCE)")

# ── 4) formate_nombre — valeurs attendues EN DUR (conventions publiées) ──
# ANCRE PIÈGE FORTE (Inde, lakh/crore) : le groupement par 3 donnerait '1,234,567' et serait FAUX.
check(F.formate_nombre(1234567, "Inde") == "12,34,567", "IN 1234567 -> '12,34,567' (lakh/crore)")
check(F.formate_nombre(1234567, "Inde") != "1,234,567", "IN : groupement occidental REFUSÉ en écriture")
check(F.formate_nombre(10000000, "Inde") == "1,00,00,000", "IN 1 crore -> '1,00,00,000' (énoncé)")
check(F.formate_nombre(100000, "Inde") == "1,00,000", "IN 1 lakh -> '1,00,000'")
check(F.formate_nombre(1234, "Inde") == "1,234", "IN 1234 -> '1,234' (premier groupe de 3)")
check(F.formate_nombre(123, "Inde") == "123", "IN 123 -> '123' (pas de séparateur)")
# Suisse : apostrophe (énoncé : 1'000'000)
check(F.formate_nombre(1000000, "Suisse") == "1'000'000", "CH 1000000 -> 1'000'000")
check(F.formate_nombre(1234.5, "Suisse") == "1'234.5", "CH 1234.5 -> 1'234.5")
# Occident standard
check(F.formate_nombre(1234567, "États-Unis") == "1,234,567", "US 1234567 -> '1,234,567'")
check(F.formate_nombre(1234567.89, "États-Unis") == "1,234,567.89", "US décimales '.'")
check(F.formate_nombre(1234567, "Allemagne") == "1.234.567", "DE 1234567 -> '1.234.567'")
check(F.formate_nombre(1234567.89, "France") == "1" + NBSP + "234" + NBSP + "567,89",
      "FR 1234567.89 -> '1 234 567,89' (insécables + virgule)")
check(F.formate_nombre(1234.5, "Brésil") == "1.234,5", "BR 1234.5 -> '1.234,5'")
check(F.formate_nombre(1234567, "Russie") == "1" + NBSP + "234" + NBSP + "567", "RU insécables")
check(F.formate_nombre(-1234, "États-Unis") == "-1,234", "US négatif -> '-1,234'")
check(F.formate_nombre(0.5, "France") == "0,5", "FR 0.5 -> '0,5'")
check(F.formate_nombre(0, "France") == "0", "FR 0 -> '0'")
check(F.formate_nombre(999, "France") == "999", "FR 999 -> '999' (aucun séparateur)")

# ── 5) parse_nombre — l'INVERSE, valeurs EN DUR ──
check(F.parse_nombre("12,34,567", "Inde") == 1234567.0, "IN parse '12,34,567' = 1234567")
check(leve(F.parse_nombre, "1,234,567", "Inde"), "IN parse '1,234,567' (groupement occidental) -> ValueError")
check(F.parse_nombre("12,345", "Inde") == 12345.0, "IN parse '12,345' = 12345 (écriture lakh valide)")
check(F.parse_nombre("1,234,567", "États-Unis") == 1234567.0, "US parse '1,234,567' = 1234567")
# LE MÊME TEXTE '1.234' n'a pas le même sens selon le pays — c'est le pays qui tranche, jamais un défaut :
check(F.parse_nombre("1.234", "Allemagne") == 1234.0, "DE '1.234' = mille deux cent trente-quatre")
check(F.parse_nombre("1.234", "États-Unis") == 1.234, "US '1.234' = un virgule deux trois quatre")
check(F.parse_nombre("1'000'000", "Suisse") == 1000000.0, "CH parse apostrophe ASCII")
check(F.parse_nombre("1" + APO_TYPO + "000" + APO_TYPO + "000", "Suisse") == 1000000.0,
      "CH parse apostrophe typographique U+2019 (CLDR)")
check(F.parse_nombre("1" + NBSP + "234,5", "France") == 1234.5, "FR parse insécable U+00A0")
check(F.parse_nombre("1" + NNBSP + "234,5", "France") == 1234.5, "FR parse fine insécable U+202F")
check(F.parse_nombre("1 234,5", "France") == 1234.5, "FR parse espace clavier (lecture tolérée)")
check(F.parse_nombre("1234567", "France") == 1234567.0, "FR parse sans séparateurs accepté")
check(F.parse_nombre("-1,234", "États-Unis") == -1234.0, "US parse négatif")
check(F.parse_nombre("0,5", "France") == 0.5, "FR parse '0,5'")

# ── 6) parse_nombre — SOUNDNESS (texte non parsable/groupement faux -> ValueError) ──
check(leve(F.parse_nombre, "1,23", "États-Unis"), "US '1,23' : ni millier ni décimal -> ValueError")
check(leve(F.parse_nombre, "12,3456", "États-Unis"), "US groupe de 4 -> ValueError")
check(leve(F.parse_nombre, "1,2,34,567", "Inde"), "IN groupes 1|2 mal placés -> ValueError")
check(leve(F.parse_nombre, "", "France"), "texte vide -> ValueError")
check(leve(F.parse_nombre, "abc", "France"), "texte alphabétique -> ValueError")
check(leve(F.parse_nombre, "1.2.3", "États-Unis"), "US double séparateur décimal -> ValueError")
check(leve(F.parse_nombre, ",5", "France"), "FR ',5' partie entière vide -> ValueError")
check(leve(F.parse_nombre, "1,", "France"), "FR '1,' partie décimale vide -> ValueError")
check(leve(F.parse_nombre, " 1234", "France"), "espace de tête -> ValueError")
check(leve(F.parse_nombre, "+5", "France"), "signe '+' non prévu par l'écriture -> ValueError")
check(leve(F.parse_nombre, "-", "France"), "signe seul -> ValueError")
check(leve(F.parse_nombre, "--5", "France"), "double signe -> ValueError")
check(leve(F.parse_nombre, 1234, "France"), "parse d'un non-texte -> ValueError")

# ── 7) BOUCLE FERMÉE : parse(formate(x)) == x, 200+ valeurs × 11 pays ──
PAYS = ["France", "Allemagne", "Royaume-Uni", "États-Unis", "Canada", "Japon",
        "Chine", "Suisse", "Inde", "Brésil", "Russie"]
VALEURS = (
    list(range(0, 165))                                  # 165 petits entiers
    + [999, 1000, 1001, 9999, 12345, 99999, 123456, 999999, 1000000, 1234567,
       9999999, 10000000, 12345678, 123456789, 1000000000, 999999999]
    + [-1, -12, -999, -1000, -1234567, -123456789]
    + [0.5, -0.5, 0.25, 0.125, 3.14159, 2.71828, 1234.5, -1234.56, 99999.99,
       123456.789, 10.01, 999.999, 1000000.5, -0.125, 7.75, 0.001, 1234567.89]
)
check(len(VALEURS) >= 200, f"corpus boucle fermée >= 200 valeurs (réel : {len(VALEURS)})")
for pays in PAYS:
    check(all(F.parse_nombre(F.formate_nombre(x, pays), pays) == x for x in VALEURS),
          f"boucle fermée parse(formate(x)) == x — {pays} ({len(VALEURS)} valeurs)")

# ── 8) formate_date — valeurs EN DUR (le 3 avril 2024 dans chaque écriture) ──
check(F.formate_date(2024, 4, 3, "France") == "03/04/2024", "FR 3 avril 2024 -> '03/04/2024'")
check(F.formate_date(2024, 4, 3, "États-Unis") == "04/03/2024", "US 3 avril 2024 -> '04/03/2024'")
check(F.formate_date(2024, 4, 3, "Allemagne") == "03.04.2024", "DE -> '03.04.2024'")
check(F.formate_date(2024, 4, 3, "Canada") == "2024-04-03", "CA -> '2024-04-03' (ISO-like)")
check(F.formate_date(2024, 4, 3, "Japon") == "2024/04/03", "JP -> '2024/04/03'")
check(F.formate_date(2024, 4, 3, "Russie") == "03.04.2024", "RU -> '03.04.2024'")
check(F.formate_date_iso(2024, 4, 3) == "2024-04-03", "ISO 8601 -> '2024-04-03'")

# Bissextiles (règle grégorienne, connue indépendamment) : 2024 oui (÷4), 2000 oui (÷400),
# 2023 non, 2100 non (siècle non ÷400).
check(F.formate_date(2024, 2, 29, "France") == "29/02/2024", "29/02/2024 accepté (2024 bissextile)")
check(F.formate_date(2000, 2, 29, "France") == "29/02/2000", "29/02/2000 accepté (règle des 400)")
check(leve(F.formate_date, 2023, 2, 29, "France"), "29/02/2023 -> ValueError (non bissextile)")
check(leve(F.formate_date, 2100, 2, 29, "France"), "29/02/2100 -> ValueError (siècle non ÷400)")
check(leve(F.formate_date, 2024, 4, 31, "France"), "31 avril -> ValueError (avril = 30 jours)")
check(leve(F.formate_date, 2024, 13, 1, "France"), "mois 13 -> ValueError")
check(leve(F.formate_date, 2024, 0, 1, "France"), "mois 0 -> ValueError")
check(leve(F.formate_date, 2024, 6, 0, "France"), "jour 0 -> ValueError")
check(leve(F.formate_date, 0, 1, 1, "France"), "année 0 -> ValueError")

# ── 9) parse_date + AMBIGUÏTÉ '03/04/2024' (l'ancre imposée) ──
check(F.parse_date("03/04/2024", "France") == (2024, 4, 3), "FR '03/04/2024' = 3 avril 2024")
check(F.parse_date("03/04/2024", "États-Unis") == (2024, 3, 4), "US '03/04/2024' = 4 mars 2024")
check(F.parse_date("2024-04-03", "Canada") == (2024, 4, 3), "CA '2024-04-03' = 3 avril 2024")
lectures = F.interpretations_date("03/04/2024")
check(lectures.get("France") == (2024, 4, 3), "interprétations : France lit le 3 avril")
check(lectures.get("États-Unis") == (2024, 3, 4), "interprétations : États-Unis lit le 4 mars")
check(F.date_est_ambigue("03/04/2024") is True, "'03/04/2024' déclarée AMBIGUË (FR vs US)")
# ISO 8601 : la seule écriture non ambiguë
check(F.date_est_ambigue("2024-04-03") is False, "ISO '2024-04-03' NON ambiguë")
check(set(F.interpretations_date("2024-04-03")) == {"Canada"}, "ISO lue par le seul format AAAA-MM-JJ")
# Plusieurs lecteurs mais UNE seule date -> pas d'ambiguïté (le 31 ne peut pas être un mois)
check(F.date_est_ambigue("31/12/2024") is False, "'31/12/2024' : une seule date possible")
check(F.date_est_ambigue("2024/04/03") is False, "'2024/04/03' : Japon et Chine lisent LA MÊME date")
check(all(F.date_est_ambigue(F.formate_date_iso(a, m, j)) is False
          for (a, m, j) in [(2024, 1, 2), (1999, 12, 31), (2026, 7, 10), (2000, 2, 29)]),
      "ISO 8601 jamais ambiguë (échantillon)")
check(leve(F.parse_date, "3/4/2024", "France"), "date non zéro-paddée -> ValueError (écriture stricte)")
check(leve(F.parse_date, "04/31/2024", "États-Unis"), "US 31 avril -> ValueError")
check(leve(F.parse_date, "2024-04-03", "France"), "texte ISO au format FR -> ValueError")
check(leve(F.interpretations_date, "99/99/9999"), "aucun pays ne lit '99/99/9999' -> ValueError")
check(leve(F.date_est_ambigue, "n'importe quoi"), "texte non-date -> ValueError")

# ── 10) SOUNDNESS — pays hors catalogue (JAMAIS un défaut deviné) ──
check(leve(F.format_date, "Espagne"), "format_date pays inconnu -> ValueError")
check(leve(F.separateur_decimal, "Espagne"), "separateur_decimal pays inconnu -> ValueError")
check(leve(F.separateur_milliers, "Italie"), "separateur_milliers pays inconnu -> ValueError")
check(leve(F.formate_nombre, 1234, "Mexique"), "formate_nombre pays inconnu -> ValueError")
check(leve(F.parse_nombre, "1234", "Espagne"), "parse_nombre pays inconnu -> ValueError")
check(leve(F.premier_jour_semaine, "Espagne"), "premier_jour_semaine pays inconnu -> ValueError")
check(leve(F.format_heure, "Espagne"), "format_heure pays inconnu -> ValueError")
check(leve(F.symbole_monetaire, "Espagne"), "symbole_monetaire pays inconnu -> ValueError")
check(leve(F.formate_date, 2024, 4, 3, "Espagne"), "formate_date pays inconnu -> ValueError")
check(leve(F.parse_date, "03/04/2024", "Espagne"), "parse_date pays inconnu -> ValueError")
check(leve(F.format_date, ""), "pays chaîne vide -> ValueError")
check(leve(F.format_date, 42), "pays non-chaîne -> ValueError")
check(leve(F.format_date, True), "pays bool -> ValueError")
check(leve(F.format_date, None), "pays None -> ValueError")

# ── 11) SOUNDNESS — types de valeur (bool refusé, NaN/inf refusés, str refusée) ──
check(leve(F.formate_nombre, True, "France"), "formate_nombre bool -> ValueError (True n'est pas 1)")
check(leve(F.formate_nombre, "1234", "France"), "formate_nombre str -> ValueError")
check(leve(F.formate_nombre, float("nan"), "France"), "formate_nombre NaN -> ValueError")
check(leve(F.formate_nombre, float("inf"), "France"), "formate_nombre +inf -> ValueError")
check(leve(F.formate_nombre, float("-inf"), "France"), "formate_nombre -inf -> ValueError")
check(leve(F.formate_nombre, 1e300, "France"), "float en notation scientifique -> ValueError (abstention)")
check(leve(F.formate_nombre, 1e-7, "France"), "float trop petit (1e-07) -> ValueError (abstention)")
check(leve(F.formate_date, 2024.0, 4, 3, "France"), "année float -> ValueError (entier strict)")
check(leve(F.formate_date, True, 4, 3, "France"), "année bool -> ValueError")
check(leve(F.formate_date, 2024, "04", 3, "France"), "mois str -> ValueError")
check(leve(F.formate_date_iso, 2023, 2, 29), "ISO 29/02/2023 -> ValueError")
check(leve(F.parse_date, 20240403, "Canada"), "parse_date non-texte -> ValueError")

# ── 12) DÉTERMINISME (deux appels -> résultats identiques) ──
check(F.formate_nombre(1234567.89, "Inde") == F.formate_nombre(1234567.89, "Inde"),
      "déterminisme formate_nombre")
check(F.parse_nombre("12,34,567", "Inde") == F.parse_nombre("12,34,567", "Inde"),
      "déterminisme parse_nombre")
check(F.interpretations_date("03/04/2024") == F.interpretations_date("03/04/2024"),
      "déterminisme interpretations_date")
check(F.formate_date(2024, 2, 29, "Japon") == F.formate_date(2024, 2, 29, "Japon"),
      "déterminisme formate_date")

print(f"\n=== valide_formats_locaux : {ok}/{ok+ko} ===")
import sys; sys.exit(0 if ko == 0 else 1)
