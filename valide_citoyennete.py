"""
VALIDE citoyennete.py — ADVERSARIAL. Ancres connues (droits/devoirs du citoyen, France/démocratie) + SOUNDNESS
(élément hors catalogue / entrée invalide -> ValueError, jamais une catégorie inventée) + cohérence interne
(est_droit == not est_devoir sur tout le catalogue) + déterminisme. Aucun de ces cas ne figure dans __main__.
"""
import citoyennete as C

ok = 0
ko = 0


def check(cond, label):
    global ok, ko
    if cond:
        ok += 1
    else:
        ko += 1
        print(f"  FAIL: {label}")


def _leve(fn, *a, **k):
    """True ssi fn(*a, **k) lève ValueError (abstention), False sinon."""
    try:
        fn(*a, **k)
        return False
    except ValueError:
        return True
    except Exception:
        return False


# 1) ANCRES DE LA SPÉC (cas exigés explicitement).
check(C.categorie("voter") == "droit_politique", "voter = droit politique")
check(C.categorie("payer l'impôt") == "devoir", "payer l'impôt = devoir")
check(C.categorie("liberté d'expression") == "droit_civil", "liberté d'expression = droit civil")
check(C.age_majorite_civique() == 18, "majorité civique = 18 ans (France)")
check(isinstance(C.age_majorite_civique(), int), "âge = entier")

# 2) DROITS CIVILS — autres ancres du catalogue.
for e in ("propriété", "droit de propriété", "sûreté", "présomption d'innocence",
          "liberté de conscience", "liberté de la presse", "égalité devant la loi",
          "inviolabilité du domicile", "liberté d'association"):
    check(C.categorie(e) == "droit_civil", f"{e} = droit civil")

# 3) DROITS POLITIQUES.
for e in ("droit de vote", "éligibilité", "être élu", "se présenter aux élections",
          "adhérer à un parti politique", "droit de pétition"):
    check(C.categorie(e) == "droit_politique", f"{e} = droit politique")

# 4) DROITS SOCIAUX (Préambule 1946).
for e in ("éducation", "droit à l'éducation", "santé", "droit à la santé", "protection de la santé",
          "droit au travail", "droit de grève", "droit syndical", "protection sociale", "droit au logement"):
    check(C.categorie(e) == "droit_social", f"{e} = droit social")

# 5) DEVOIRS.
for e in ("payer les impôts", "respecter la loi", "respecter les droits d'autrui",
          "être juré", "jury", "défense nationale", "concourir à la défense nationale"):
    check(C.categorie(e) == "devoir", f"{e} = devoir")

# 6) est_droit / est_devoir — partition exacte.
check(C.est_droit("voter") is True, "voter est un droit")
check(C.est_devoir("voter") is False, "voter n'est pas un devoir")
check(C.est_devoir("payer l'impôt") is True, "payer l'impôt est un devoir")
check(C.est_droit("payer l'impôt") is False, "payer l'impôt n'est pas un droit")
check(C.est_droit("liberté d'expression") is True, "liberté d'expression est un droit")
check(C.est_droit("éducation") is True, "éducation (social) est un droit")
check(C.est_droit("droit de vote") is True, "droit de vote (politique) est un droit")
check(C.est_devoir("respecter la loi") is True, "respecter la loi est un devoir")

# 7) COHÉRENCE INTERNE — sur TOUT le catalogue : est_droit XOR est_devoir, et catégorie ∈ CATEGORIES.
for e in C.elements():
    cat = C.categorie(e)
    check(cat in C.CATEGORIES, f"catégorie de « {e} » est valide")
    check(C.est_droit(e) != C.est_devoir(e), f"partition droit/devoir exacte pour « {e} »")
    check(C.est_devoir(e) == (cat == "devoir"), f"est_devoir cohérent avec catégorie pour « {e} »")
    check(C.est_droit(e) == (cat in ("droit_civil", "droit_politique", "droit_social")),
          f"est_droit cohérent avec catégorie pour « {e} »")

# 8) NORMALISATION — casse, espaces, apostrophe typographique, accents pliés (tolérance de saisie, sans inventer).
check(C.categorie("VOTER") == "droit_politique", "casse majuscule normalisée")
check(C.categorie("  voter  ") == "droit_politique", "espaces externes normalisés")
check(C.categorie("liberté   d'expression") == "droit_civil", "espaces internes compactés")
check(C.categorie("liberté d’expression") == "droit_civil", "apostrophe typographique normalisée")
check(C.categorie("liberte d'expression") == "droit_civil", "accents pliés (saisie sans accent)")
check(C.categorie("PAYER L'IMPÔT") == "devoir", "payer l'impôt en majuscules")
check(C.categorie("Éligibilité") == "droit_politique", "casse + accent sur éligibilité")

# 9) SOUNDNESS — élément HORS catalogue -> ValueError (jamais une catégorie devinée).
for e in ("acheter une voiture", "manger", "respirer", "vacances", "conduire vite",
          "droit", "devoir", "citoyen", "défense", "liberté", "impôt", "vote des étrangers aux européennes 2031"):
    check(_leve(C.categorie, e), f"hors catalogue « {e} » -> ValueError")
    check(_leve(C.est_droit, e), f"est_droit hors catalogue « {e} » -> ValueError")
    check(_leve(C.est_devoir, e), f"est_devoir hors catalogue « {e} » -> ValueError")

# 9bis) « défense » SEULE est volontairement HORS catalogue (ambiguë : défense nationale vs droits de la défense).
check(_leve(C.categorie, "défense"), "« défense » seule (ambiguë) -> ValueError")
check(C.categorie("défense nationale") == "devoir", "« défense nationale » (non équivoque) = devoir")

# 10) SOUNDNESS — entrées invalides -> ValueError (abstention, jamais un faux).
check(_leve(C.categorie, ""), "chaîne vide -> ValueError")
check(_leve(C.categorie, "   "), "espaces seuls -> ValueError")
check(_leve(C.categorie, None), "None -> ValueError")
check(_leve(C.categorie, 18), "entier -> ValueError")
check(_leve(C.categorie, ["voter"]), "liste -> ValueError")
check(_leve(C.est_droit, None), "est_droit(None) -> ValueError")
check(_leve(C.est_devoir, 42), "est_devoir(42) -> ValueError")

# 11) DÉTERMINISME — mêmes entrées, mêmes sorties ; constantes stables.
check(C.categorie("voter") == C.categorie("voter"), "déterminisme categorie")
check(C.est_droit("éducation") == C.est_droit("éducation"), "déterminisme est_droit")
check(C.age_majorite_civique() == C.age_majorite_civique() == 18, "déterminisme age_majorite_civique")
check(C.CATEGORIES == ("droit_civil", "droit_politique", "droit_social", "devoir"), "CATEGORIES stable")
check(len(set(C.elements())) == len(C.elements()), "libellés du catalogue uniques")

print(f"\n=== valide_citoyennete : {ok}/{ok + ko} ===")
import sys
sys.exit(0 if ko == 0 else 1)
