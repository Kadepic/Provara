"""valide_propagande.py — validation ADVERSARIALE de propagande.py.

Ancres : les 7 techniques de l'Institute for Propaganda Analysis + la
trichotomie mis-/dis-/mal-information (Wardle & Derakhshan, Conseil de
l'Europe 2017). Soundness : technique/type hors catalogue -> ValueError.
Déterminisme : appels répétés identiques.
"""

import propagande as M

ok = 0
ko = 0


def check(cond, label):
    global ok, ko
    if cond:
        ok += 1
    else:
        ko += 1
        print("  KO:", label)


def _leve(fn, *args, **kw):
    try:
        fn(*args, **kw)
        return False
    except ValueError:
        return True
    except Exception:
        return False


# --- Ancres : les 7 techniques existent et sont définies --------------------
for cle in ("name_calling", "generalites_creuses", "transfert", "temoignage",
            "homme_du_peuple", "card_stacking", "bandwagon"):
    check(isinstance(M.technique(cle), str) and len(M.technique(cle)) > 0,
          "technique definie: " + cle)

check(len(M.liste_techniques()) == 7, "exactement 7 techniques (IPA)")
check(M.liste_techniques() == sorted(set(M.liste_techniques())),
      "catalogue techniques trie et sans doublon")

# --- Ancre CAS imposé : bandwagon = 'tout le monde le fait' -----------------
check("tout le monde" in M.technique("bandwagon").lower(),
      "bandwagon = 'tout le monde le fait'")
check("tout le monde" in M.technique("train en marche").lower(),
      "alias train en marche -> bandwagon (tout le monde)")

# --- Aliases : chaque slash du libellé pointe vers la meme technique --------
check(M.technique("diabolisation") == M.technique("name_calling"),
      "alias diabolisation == name_calling")
check(M.technique("carte biaisee") == M.technique("card_stacking"),
      "alias carte biaisee == card_stacking")
check(M.technique("carte biaisée") == M.technique("card_stacking"),
      "alias accentue carte biaisée == card_stacking")
check(M.technique("Transfer") == M.technique("transfert"),
      "alias anglais Transfer == transfert (casse ignoree)")
check(M.technique("plain folks") == M.technique("homme_du_peuple"),
      "alias plain folks == homme_du_peuple")
check(M.technique("testimonial") == M.technique("temoignage"),
      "alias testimonial == temoignage")
check(M.technique("glittering generalities") == M.technique("generalites_creuses"),
      "alias glittering generalities == generalites_creuses")

# Contenu attendu (faits) : témoignage évoque une caution/célébrité.
check("celebrite" in M.technique("temoignage").translate(M._ACCENTS).lower()
      or "respectee" in M.technique("temoignage").translate(M._ACCENTS).lower(),
      "definition temoignage = caution d'une personne respectee/celebre")

# --- Ancres : taxonomie mis-/dis-/mal-information ---------------------------
check(M.est_intentionnel("disinformation") is True,
      "disinformation = intentionnelle")
check(M.est_intentionnel("misinformation") is False,
      "misinformation = erreur involontaire (non intentionnelle)")
check(M.est_intentionnel("malinformation") is True,
      "malinformation = intention de nuire")

check(M.est_faux("misinformation") is True, "misinformation = info fausse")
check(M.est_faux("disinformation") is True, "disinformation = info fausse")
check(M.est_faux("malinformation") is False,
      "malinformation = info VRAIE detournee")

# La distinction misinfo vs disinfo tient au seul axe intention (les deux fausses).
check(M.est_faux("misinformation") == M.est_faux("disinformation")
      and M.est_intentionnel("misinformation")
      != M.est_intentionnel("disinformation"),
      "misinfo vs disinfo = meme faussete, intention opposee")

d = M.type_desinformation("misinformation")
check(d["intention_de_nuire"] is False and d["faux"] is True
      and isinstance(d["definition"], str) and len(d["definition"]) > 0,
      "structure type_desinformation(misinformation)")

check(len(M.liste_types_desinformation()) == 3, "exactement 3 types")
check(M.liste_types_desinformation()
      == ["disinformation", "malinformation", "misinformation"],
      "liste des 3 types triee")

# Copie défensive : muter le retour ne corrompt pas le catalogue.
d2 = M.type_desinformation("disinformation")
d2["intention_de_nuire"] = "CORROMPU"
check(M.est_intentionnel("disinformation") is True,
      "copie defensive : le catalogue reste intact")

# --- Soundness : abstention sur entrées hors catalogue ----------------------
check(_leve(M.technique, "lavage_de_cerveau"),
      "soundness: technique inventee -> ValueError")
check(_leve(M.technique, "gaslighting"),
      "soundness: gaslighting hors catalogue IPA -> ValueError")
check(_leve(M.technique, ""), "soundness: technique vide")
check(_leve(M.technique, None), "soundness: technique None")
check(_leve(M.technique, 42), "soundness: technique non textuelle")
check(_leve(M.type_desinformation, "fake_news"),
      "soundness: fake_news hors taxonomie -> ValueError")
check(_leve(M.type_desinformation, "propagande"),
      "soundness: propagande n'est pas un type -> ValueError")
check(_leve(M.type_desinformation, ""), "soundness: type vide")
check(_leve(M.est_intentionnel, "rumeur"),
      "soundness: est_intentionnel type inconnu -> ValueError")
check(_leve(M.est_faux, "xyz"), "soundness: est_faux type inconnu -> ValueError")

# --- Déterminisme -----------------------------------------------------------
check(M.technique("bandwagon") == M.technique("bandwagon"),
      "determinisme technique")
check(M.type_desinformation("disinformation")
      == M.type_desinformation("disinformation"),
      "determinisme type_desinformation")
check(M.liste_techniques() == M.liste_techniques(), "determinisme liste tech")
check(M.liste_types_desinformation() == M.liste_types_desinformation(),
      "determinisme liste types")

print(f"\n=== valide_propagande : {ok}/{ok+ko} ===")
import sys
sys.exit(0 if ko == 0 else 1)
