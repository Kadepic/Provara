"""valide_sophismes.py — validation ADVERSARIALE de sophismes.py.

Ancres : théorèmes de logique classique (modus ponens/tollens valides ;
affirmation du conséquent / négation de l'antécédent invalides) + définitions
de sophismes informels établis. Soundness : entrée non reconnue -> ValueError.
Déterminisme : appels répétés identiques.
"""

import sophismes as M

ok = 0
ko = 0


def check(cond, label):
    global ok, ko
    if cond:
        ok += 1
    else:
        ko += 1
        print("  KO:", label)


def _leve(fn, *args):
    try:
        fn(*args)
        return False
    except ValueError:
        return True
    except Exception:
        return False


# --- Ancres : identification des 4 formes conditionnelles -------------------
check(M.identifie_forme("p->q", "p", "q") == "modus_ponens",
      "p->q, p ⊢ q = modus_ponens")
check(M.identifie_forme("p->q", "q", "p") == "affirmation_consequent",
      "p->q, q ⊢ p = affirmation du consequent")
check(M.identifie_forme("p->q", "~p", "~q") == "negation_antecedent",
      "p->q, ~p ⊢ ~q = negation de l'antecedent")
check(M.identifie_forme("p->q", "~q", "~p") == "modus_tollens",
      "p->q, ~q ⊢ ~p = modus_tollens")

# Variantes de notation (→, ¬, atomes différents) : même mécanisme.
check(M.identifie_forme("a→b", "a", "b") == "modus_ponens",
      "a→b, a ⊢ b = modus_ponens (fleche unicode, autres atomes)")
check(M.identifie_forme("a->b", "¬b", "¬a") == "modus_tollens",
      "a->b, ¬b ⊢ ¬a = modus_tollens (negation unicode)")
check(M.identifie_forme("pluie->mouille", "mouille", "pluie")
      == "affirmation_consequent",
      "atomes mots = affirmation du consequent")

# --- Ancres : validité (faits logiques) -------------------------------------
check(M.est_valide("modus_ponens") is True, "modus_ponens valide")
check(M.est_valide("modus_tollens") is True, "modus_tollens valide")
check(M.est_valide("affirmation_consequent") is False,
      "affirmation_consequent invalide")
check(M.est_valide("negation_antecedent") is False,
      "negation_antecedent invalide")
check(M.est_sophisme("affirmation_consequent") is True,
      "affirmation_consequent = sophisme")
check(M.est_sophisme("negation_antecedent") is True,
      "negation_antecedent = sophisme")
check(M.est_sophisme("modus_ponens") is False, "modus_ponens n'est pas sophisme")

# Cohérence interne : valide <=> non sophisme sur les 4 formes reconnues.
for f in ("modus_ponens", "modus_tollens",
          "affirmation_consequent", "negation_antecedent"):
    check(M.est_valide(f) != M.est_sophisme(f),
          "coherence valide/sophisme: " + f)

# --- Ancres : catalogue de sophismes informels (faits) ----------------------
check("position" in M.definition_sophisme("homme de paille").lower()
      or "caricatur" in M.definition_sophisme("homme de paille").lower(),
      "definition homme de paille")
check(len(M.definition_sophisme("pente glissante")) > 0,
      "definition pente glissante non vide")
check(M.definition_sophisme("ad hominem")
      == M.definition_sophisme("ad_hominem"),
      "alias ad hominem == cle canonique")
check(M.definition_sophisme("attaque personnelle")
      == M.definition_sophisme("ad_hominem"),
      "alias attaque personnelle -> ad_hominem")
check("ad_hominem" in M.liste_sophismes(), "ad_hominem dans le catalogue")
check(len(M.liste_sophismes()) == len(set(M.liste_sophismes())),
      "catalogue sans doublon")

# --- Soundness : abstention sur entrées non reconnues -----------------------
check(_leve(M.identifie_forme, "p->q", "p", "~q"),
      "soundness: p->q, p ⊢ ~q non reconnu")
check(_leve(M.identifie_forme, "p->q", "p", "p"),
      "soundness: p->q, p ⊢ p non reconnu")
check(_leve(M.identifie_forme, "p->q", "r", "s"),
      "soundness: atomes etrangers non reconnus")
check(_leve(M.identifie_forme, "p&q", "p", "q"),
      "soundness: majeure non conditionnelle")
check(_leve(M.identifie_forme, "p->q", "~q", "p"),
      "soundness: ~q ⊢ p (melange) non reconnu")
check(_leve(M.identifie_forme, "p->p", "p", "p"),
      "soundness: antecedent=consequent rejete")
check(_leve(M.identifie_forme, "p->q", "", "q"),
      "soundness: mineure vide")
check(_leve(M.est_valide, "petitio_principii"),
      "soundness: forme inconnue est_valide")
check(_leve(M.est_valide, "modus_morons"),
      "soundness: forme inventee est_valide")
check(_leve(M.est_sophisme, "xyz"), "soundness: forme inconnue est_sophisme")
check(_leve(M.definition_sophisme, "sophisme_invente_xyz"),
      "soundness: sophisme inconnu")
check(_leve(M.definition_sophisme, ""), "soundness: nom vide")

# --- Déterminisme -----------------------------------------------------------
check(M.identifie_forme("p->q", "~q", "~p")
      == M.identifie_forme("p->q", "~q", "~p"),
      "determinisme identifie_forme")
check(M.definition_sophisme("ad hominem")
      == M.definition_sophisme("ad hominem"),
      "determinisme definition_sophisme")
check(M.liste_sophismes() == M.liste_sophismes(), "determinisme liste")

print(f"\n=== valide_sophismes : {ok}/{ok+ko} ===")
import sys
sys.exit(0 if ko == 0 else 1)
