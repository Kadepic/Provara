"""
VALIDE codes_normalises.py — held-out ADVERSE.

ANCRES EXTERNES NON CIRCULAIRES (tables publiées, écrites en dur) :
  • ISO 4217 : EUR = 978, USD = 840, JPY = 392, GBP = 826, CHF = 756.
  • DÉCIMALES — le piège central : JPY et KRW ont **0** décimale ; KWD, BHD et TND en ont **3** ;
    la plupart en ont 2. Supposer « 2 » partout fausserait les montants d'un facteur 10 ou 100.
  • E.164 : France +33, Allemagne +49, Japon +81. **+1 est PARTAGÉ** par les États-Unis et le Canada ;
    **+7** par la Russie et le Kazakhstan. Rendre « États-Unis » pour +1 serait un faux silencieux.
  • ISBN-13 : 978-0-306-40615-7 est VALIDE (somme de contrôle publiée). ISBN-10 : 0-306-40615-2 est valide,
    et 0-8044-2957-X aussi (le « X » vaut 10). Changer un chiffre invalide la somme.
  • Plaque française SIV : « AB-123-CD » valide ; les lettres I, O et U sont exclues.

ANCRE D'HONNÊTETÉ : `format_plaque` d'un pays non embarqué lève ValueError. Deviner un format de plaque
serait gratuit et faux — les formats varient par pays et par époque.

SOUNDNESS : code inconnu, pays inconnu, indicatif inconnu, indicatif partagé (pour la fonction « unique »),
bool/int/None -> ValueError. ISBN mal formé -> False (c'est une validation, pas une exception).
"""
import sys

import codes_normalises as C

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


# ── 1) ISO 4217 : codes numériques (valeurs publiées, en dur) ──
check(C.code_numerique("EUR") == 978, "EUR -> 978")
check(C.code_numerique("USD") == 840, "USD -> 840")
check(C.code_numerique("JPY") == 392, "JPY -> 392")
check(C.code_numerique("GBP") == 826, "GBP -> 826")
check(C.code_numerique("CHF") == 756, "CHF -> 756")
check(C.code_numerique("eur") == 978, "la casse est tolérée")
check(C.nom_monnaie("JPY") == "yen", "JPY -> yen")
check("euro" in C.nom_monnaie("EUR"), "EUR -> euro")
check(C.monnaie_depuis_numerique(978) == "EUR", "978 -> EUR (chemin inverse)")
check(C.monnaie_depuis_numerique(392) == "JPY", "392 -> JPY")
# boucle fermée sur toute la table
check(all(C.monnaie_depuis_numerique(C.code_numerique(c)) == c for c in C.monnaies()),
      "boucle fermée alpha <-> numérique sur TOUTES les monnaies")

# ── 2) LE PIÈGE DES DÉCIMALES ──
check(C.decimales("EUR") == 2, "EUR : 2 décimales")
check(C.decimales("USD") == 2, "USD : 2 décimales")
check(C.decimales("JPY") == 0, "JPY : ZÉRO décimale (le yen n'a pas de subdivision)")
check(C.decimales("KRW") == 0, "KRW : zéro décimale")
check(C.decimales("KWD") == 3, "KWD : TROIS décimales (dinar koweïtien)")
check(C.decimales("BHD") == 3, "BHD : trois décimales")
check(C.decimales("TND") == 3, "TND : trois décimales")
check(len({C.decimales(c) for c in C.monnaies()}) == 3, "trois valeurs distinctes de décimales (0, 2, 3)")
check(C.formate_montant(1000, "JPY") == "1000 JPY", "1000 JPY : aucune décimale affichée")
check(C.formate_montant(1000, "EUR") == "1000.00 EUR", "1000 EUR : deux décimales")
check(C.formate_montant(1, "KWD") == "1.000 KWD", "1 KWD : trois décimales")
check(leve(C.formate_montant, True, "EUR"), "montant bool -> ValueError")

# ── 3) E.164 : l'indicatif n'identifie PAS un pays ──
check(C.indicatif("France") == "+33", "France -> +33")
check(C.indicatif("Allemagne") == "+49", "Allemagne -> +49")
check(C.indicatif("Japon") == "+81", "Japon -> +81")
check(C.indicatif("États-Unis") == "+1", "États-Unis -> +1")
check(C.indicatif("Canada") == "+1", "Canada -> +1 (le MÊME)")
check(C.pays_depuis_indicatif("+33") == {"France"}, "+33 -> {France}")
check(C.pays_depuis_indicatif("+1") == {"États-Unis", "Canada"}, "+1 -> ENSEMBLE de deux pays")
check(C.pays_depuis_indicatif("+7") == {"Russie", "Kazakhstan"}, "+7 -> Russie et Kazakhstan")
check(C.pays_depuis_indicatif("33") == {"France"}, "le « + » est optionnel en entrée")
check(C.pays_unique_depuis_indicatif("+33") == "France", "+33 : pays unique")
check(C.pays_unique_depuis_indicatif("+81") == "Japon", "+81 : pays unique")
check(leve(C.pays_unique_depuis_indicatif, "+1"), "+1 PARTAGÉ -> ValueError (jamais « États-Unis »)")
check(leve(C.pays_unique_depuis_indicatif, "+7"), "+7 partagé -> ValueError")
partages = C.indicatifs_partages()
check(set(partages) == {"+1", "+7"}, "exactement deux indicatifs partagés dans la table")
check(all(len(p) > 1 for p in partages.values()), "chaque indicatif partagé a bien plusieurs pays")
check(leve(C.indicatif, "Atlantide"), "pays inconnu -> ValueError")
check(leve(C.pays_depuis_indicatif, "+999"), "indicatif inconnu -> ValueError")

# ── 4) ISBN-13 ──
check(C.isbn13_valide("978-0-306-40615-7") is True, "ISBN-13 valide (somme de contrôle publiée)")
check(C.isbn13_valide("9780306406157") is True, "ISBN-13 sans tirets")
check(C.isbn13_valide("978-0-306-40615-8") is False, "un chiffre de contrôle faux -> False")
check(C.isbn13_valide("978-0-306-40616-7") is False, "un chiffre du corps modifié -> False")
check(C.isbn13_valide("97803064061") is False, "longueur incorrecte -> False")
check(C.isbn13_valide("978030640615X") is False, "caractère illégal en ISBN-13 -> False")

# ── 5) ISBN-10, et le « X » qui vaut 10 ──
check(C.isbn10_valide("0-306-40615-2") is True, "ISBN-10 valide")
check(C.isbn10_valide("0306406152") is True, "ISBN-10 sans tirets")
check(C.isbn10_valide("0-8044-2957-X") is True, "ISBN-10 dont la clé est « X » (= 10)")
check(C.isbn10_valide("0-306-40615-3") is False, "clé fausse -> False")
check(C.isbn10_valide("X306406152") is False, "« X » ailleurs qu'en dernière position -> False")
check(C.isbn_valide("978-0-306-40615-7") is True, "isbn_valide reconnaît le format 13")
check(C.isbn_valide("0-306-40615-2") is True, "isbn_valide reconnaît le format 10")
check(C.isbn_valide("123") is False, "longueur ni 10 ni 13 -> False")
check(leve(C.isbn_valide, 9780306406157), "ISBN en int -> ValueError")
check(leve(C.isbn_valide, True), "bool -> ValueError")

# ── 6) PLAQUES : seule la France est embarquée ──
check(C.plaque_valide("AB-123-CD") is True, "plaque SIV valide")
check(C.plaque_valide("ab-123-cd") is True, "la casse est tolérée")
check(C.plaque_valide("AB-12-CD") is False, "deux chiffres au lieu de trois -> False")
check(C.plaque_valide("AI-123-CD") is False, "la lettre I est exclue du SIV")
check(C.plaque_valide("AO-123-CD") is False, "la lettre O est exclue")
check(C.plaque_valide("AU-123-CD") is False, "la lettre U est exclue")
check(C.plaque_valide("123-ABC-45") is False, "l'ancien format FNI n'est pas le SIV")
f = C.format_plaque("France")
check(f["format"] == "AA-123-AA", "format français annoncé")
check("SIV" in f["systeme"], "le système est nommé")
check("FNI" in f["note"], "l'ancien système est mentionné, pas confondu")
check("motif" not in f, "le motif interne n'est pas exposé")
check(leve(C.format_plaque, "Allemagne"), "format de plaque non embarqué -> ValueError (jamais deviné)")
check(leve(C.plaque_valide, "AB-123-CD", "Japon"), "validation d'une plaque d'un pays non embarqué -> ValueError")

# ── 7) SOUNDNESS ──
check(leve(C.nom_monnaie, "XYZ"), "code monnaie inconnu -> ValueError")
check(leve(C.decimales, "XYZ"), "décimales d'un code inconnu -> ValueError")
check(leve(C.code_numerique, ""), "code vide -> ValueError")
check(leve(C.code_numerique, 978), "code en int -> ValueError")
check(leve(C.monnaie_depuis_numerique, 999), "code numérique inconnu -> ValueError")
check(leve(C.monnaie_depuis_numerique, "978"), "code numérique en str -> ValueError")
check(leve(C.monnaie_depuis_numerique, True), "bool -> ValueError")
check(leve(C.indicatif, None), "None -> ValueError")

# ── 8) INVARIANTS DE TABLE ──
nums = [C.code_numerique(c) for c in C.monnaies()]
check(len(set(nums)) == len(nums), "codes numériques ISO 4217 tous DISTINCTS")
check(all(len(c) == 3 and c.isalpha() for c in C.monnaies()), "tous les codes alphabétiques font 3 lettres")
check(all(C.decimales(c) in (0, 2, 3) for c in C.monnaies()), "décimales toujours dans {0, 2, 3}")
check(all(C.indicatif(p).startswith("+") for p in ("France", "Japon", "Brésil")), "indicatifs préfixés par +")

# ── 9) IMMUTABILITÉ ET DÉTERMINISME ──
m = C.monnaies()
m["EUR"] = "saboté"
check(C.nom_monnaie("EUR") != "saboté", "la table des monnaies n'est pas mutable de l'extérieur")
check(C.decimales("JPY") == C.decimales("JPY"), "déterminisme des décimales")
check(C.pays_depuis_indicatif("+1") == C.pays_depuis_indicatif("+1"), "déterminisme de la recherche inverse")

print(f"\n=== valide_codes_normalises : {ok}/{ok+ko} ===")
sys.exit(0 if ko == 0 else 1)
