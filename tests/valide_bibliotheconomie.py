"""
VALIDE bibliotheconomie.py — held-out ADVERSE.

Ancres CONNUES (non circulaires) :
  • Dewey : les 10 classes principales publiées (000…900) — chacune vérifiée contre
    son libellé établi.
  • ISBN-13 : clés de contrôle d'ouvrages réels valides (K&R, exemples ISO/Wikipédia)
    + cas falsifiés (un chiffre changé) qui DOIVENT être rejetés (False, pas une erreur).
SOUNDNESS : entrée hors référentiel -> ValueError (centaine inexistante, longueur != 13,
caractère non numérique, type invalide). Aucun de ces cas n'est codé en dur dans le module.
DÉTERMINISME : mêmes entrées -> mêmes sorties.
"""
import bibliotheconomie as B

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
    """Vrai si fn(*a, **k) lève ValueError (abstention attendue)."""
    try:
        fn(*a, **k)
        return False
    except ValueError:
        return True
    except Exception:
        return False


# ── 1) DEWEY — les 10 classes principales (ancres établies) ──
check(B.classe_dewey(0) == "informatique/généralités", "Dewey 000 = informatique/généralités")
check(B.classe_dewey(100) == "philosophie", "Dewey 100 = philosophie")
check(B.classe_dewey(200) == "religion", "Dewey 200 = religion")
check(B.classe_dewey(300) == "sciences sociales", "Dewey 300 = sciences sociales")
check(B.classe_dewey(400) == "langues", "Dewey 400 = langues")
check(B.classe_dewey(500) == "sciences", "Dewey 500 = sciences")            # cas du sujet
check(B.classe_dewey(600) == "techniques", "Dewey 600 = techniques")
check(B.classe_dewey(700) == "arts", "Dewey 700 = arts")
check(B.classe_dewey(800) == "littérature", "Dewey 800 = littérature")      # cas du sujet
check(B.classe_dewey(900) == "histoire/géo", "Dewey 900 = histoire/géo")
check(len(B.classes_dewey()) == 10, "10 classes principales au catalogue")

# ── 2) DEWEY — SOUNDNESS : centaine hors {0,100,…,900} -> ValueError ──
check(leve(B.classe_dewey, 1000), "Dewey 1000 hors référentiel -> ValueError")
check(leve(B.classe_dewey, 50), "Dewey 50 (non multiple de 100) -> ValueError")
check(leve(B.classe_dewey, 250), "Dewey 250 (non centaine) -> ValueError")
check(leve(B.classe_dewey, -100), "Dewey -100 négatif -> ValueError")
check(leve(B.classe_dewey, "500"), "Dewey '500' chaîne -> ValueError")
check(leve(B.classe_dewey, 5.0), "Dewey 5.0 float -> ValueError")
check(leve(B.classe_dewey, True), "Dewey True booléen -> ValueError")

# ── 3) ISBN-13 — clés de contrôle d'ouvrages RÉELS valides (ancres) ──
check(B.isbn_valide("978-0-306-40615-7") is True, "ISBN 978-0-306-40615-7 valide (somme=100)")
check(B.isbn_valide("9780306406157") is True, "ISBN sans tirets valide")
check(B.isbn_valide("978-0-13-110362-7") is True, "ISBN K&R 978-0-13-110362-7 valide")
check(B.isbn_valide("978 0 13 110362 7") is True, "ISBN avec espaces valide")
check(B.isbn_valide("9783161484100") is True, "ISBN 978-3-16-148410-0 valide")

# ── 4) ISBN-13 — clés FAUSSES : rejet propre (False), PAS une erreur ──
check(B.isbn_valide("9780306406158") is False, "ISBN clé altérée (…58) -> False")
check(B.isbn_valide("9780131103626") is False, "ISBN K&R clé altérée (…26) -> False")
check(B.isbn_valide("1234567890123") is False, "ISBN 1234567890123 -> False (somme!=0 mod10)")

# ── 5) ISBN-13 — SOUNDNESS : longueur != 13 ou non numérique -> ValueError ──
check(leve(B.isbn_valide, "978030640615"), "ISBN 12 chiffres -> ValueError")
check(leve(B.isbn_valide, "97803064061570"), "ISBN 14 chiffres -> ValueError")
check(leve(B.isbn_valide, "0306406152"), "ISBN-10 (10 chiffres) -> ValueError")
check(leve(B.isbn_valide, "978030640615X"), "ISBN avec lettre X -> ValueError")
check(leve(B.isbn_valide, "978-0-306-4061A-7"), "ISBN avec lettre A -> ValueError")
check(leve(B.isbn_valide, ""), "ISBN vide -> ValueError")
check(leve(B.isbn_valide, "abcdefghijklm"), "ISBN 13 lettres -> ValueError")
check(leve(B.isbn_valide, True), "ISBN booléen -> ValueError")
check(leve(B.isbn_valide, 3.14), "ISBN float -> ValueError")

# ── 6) DÉTERMINISME ──
check(B.classe_dewey(500) == B.classe_dewey(500), "déterminisme Dewey")
check(B.isbn_valide("9780306406157") == B.isbn_valide("9780306406157"), "déterminisme ISBN")

print(f"\n=== valide_bibliotheconomie : {ok}/{ok+ko} ===")
import sys
sys.exit(0 if ko == 0 else 1)
