"""VALIDE mecanismes_reactionnels.py — held-out ADVERSE, FAUX=0. Ancres = règles de chimie organique
ÉTABLIES (manuels) : classifications canoniques SN1/SN2/E1/E2, cinétique unimoléculaire/bimoléculaire,
stéréochimie connue + SOUNDNESS exhaustive (vocabulaire inconnu / régime non déterminant / élimination
impossible -> ValueError, JAMAIS un faux) + déterminisme.
"""
import mecanismes_reactionnels as M

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


# ── SUBSTITUTION : cas canoniques établis ────────────────────────────────────────────────────────────────────────
check(M.type_substitution("tertiaire", "faible", "polaire_protique") == "SN1",
      "tertiaire + faible + protique -> SN1")
check(M.type_substitution("primaire", "fort", "polaire_aprotique") == "SN2",
      "primaire + fort + aprotique -> SN2")
check(M.type_substitution("methyle", "fort", "polaire_aprotique") == "SN2",
      "méthyle + fort + aprotique -> SN2 (méthyle ne fait jamais de SN1)")
# alias non ambigus
check(M.type_substitution("3aire", "faible", "protique") == "SN1", "alias substrat/solvant -> SN1")
check(M.type_substitution("Primaire", "Fort", "Polaire_Aprotique") == "SN2", "casse insensible -> SN2")

# ── SUBSTITUTION : ABSTENTION sur régimes non déterminants (FAUX=0) ──────────────────────────────────────────────
check(leve(M.type_substitution, "secondaire", "fort", "polaire_aprotique"),
      "secondaire = borderline -> abstention")
check(leve(M.type_substitution, "secondaire", "faible", "polaire_protique"),
      "secondaire = borderline -> abstention (2)")
check(leve(M.type_substitution, "tertiaire", "fort", "polaire_aprotique"),
      "tertiaire + fort + aprotique : facteurs en conflit (régime E2) -> abstention")
check(leve(M.type_substitution, "primaire", "faible", "polaire_protique"),
      "primaire + faible + protique : pas de SN1 possible, conditions non SN2 -> abstention")
check(leve(M.type_substitution, "tertiaire", "faible", "polaire_aprotique"),
      "SN1 exige protique : solvant aprotique -> abstention")
check(leve(M.type_substitution, "primaire", "fort", "polaire_protique"),
      "SN2 exige aprotique : solvant protique -> abstention")
check(leve(M.type_substitution, "tertiaire", "fort", "polaire_protique"),
      "tertiaire + fort + protique : non unanime -> abstention")

# ── SUBSTITUTION : soundness vocabulaire inconnu ─────────────────────────────────────────────────────────────────
check(leve(M.type_substitution, "quaternaire", "faible", "polaire_protique"), "substrat inconnu -> ValueError")
check(leve(M.type_substitution, "tertiaire", "moyen", "polaire_protique"), "force inconnue -> ValueError")
check(leve(M.type_substitution, "tertiaire", "faible", "hexane"), "solvant inconnu -> ValueError")
check(leve(M.type_substitution, 3, "faible", "polaire_protique"), "substrat non textuel -> ValueError")
check(leve(M.type_substitution, "tertiaire", True, "polaire_protique"), "booléen rejeté -> ValueError")
check(leve(M.type_substitution, None, "faible", "polaire_protique"), "None rejeté -> ValueError")

# ── ENCOMBREMENT SN2 ─────────────────────────────────────────────────────────────────────────────────────────────
check(M.sn2_defavorise_par_encombrement("tertiaire") is True, "SN2 défavorisée sur tertiaire encombré")
check(M.sn2_defavorise_par_encombrement("methyle") is False, "SN2 favorisée sur méthyle")
check(M.sn2_defavorise_par_encombrement("primaire") is False, "SN2 favorisée sur primaire")
check(M.sn2_defavorise_par_encombrement("secondaire") is False, "SN2 ralentie mais non bloquée sur secondaire")
check(leve(M.sn2_defavorise_par_encombrement, "benzylique"), "substrat inconnu -> ValueError")

# ── ÉLIMINATION : cas canoniques ─────────────────────────────────────────────────────────────────────────────────
check(M.type_elimination("tertiaire", "faible", "polaire_protique") == "E1",
      "tertiaire + base faible + protique -> E1")
check(M.type_elimination("primaire", "fort", "polaire_aprotique") == "E2",
      "primaire + base forte + aprotique -> E2")
check(M.type_elimination("secondaire", "fort", "polaire_aprotique") == "E2", "secondaire + forte + aprotique -> E2")
check(M.type_elimination("tertiaire", "fort", "polaire_aprotique") == "E2", "tertiaire + forte + aprotique -> E2")

# ── ÉLIMINATION : ABSTENTION / IMPOSSIBILITÉ (FAUX=0) ────────────────────────────────────────────────────────────
check(leve(M.type_elimination, "methyle", "fort", "polaire_aprotique"),
      "méthyle = pas de carbone β -> élimination impossible -> ValueError")
check(leve(M.type_elimination, "methyle", "faible", "polaire_protique"),
      "méthyle -> élimination impossible (2) -> ValueError")
check(leve(M.type_elimination, "primaire", "faible", "polaire_protique"),
      "primaire ne fait pas d'E1 (carbocation instable) -> abstention")
check(leve(M.type_elimination, "secondaire", "faible", "polaire_protique"),
      "E1 réservé au tertiaire (conservateur) -> abstention")
check(leve(M.type_elimination, "tertiaire", "fort", "polaire_protique"),
      "fort + protique : facteurs en conflit -> abstention")
check(leve(M.type_elimination, "tertiaire", "faible", "polaire_aprotique"),
      "E1 exige protique : aprotique -> abstention")
check(leve(M.type_elimination, "primaire", "fort", "polaire_protique"),
      "E2 exige aprotique ici : protique -> abstention")
check(leve(M.type_elimination, "ionique", "fort", "polaire_aprotique"), "substrat inconnu -> ValueError")

# ── CINÉTIQUE : ordre établi par la molécularité ─────────────────────────────────────────────────────────────────
check(M.ordre_cinetique("SN1") == 1, "SN1 unimoléculaire -> ordre 1")
check(M.ordre_cinetique("SN2") == 2, "SN2 bimoléculaire -> ordre 2")
check(M.ordre_cinetique("E1") == 1, "E1 unimoléculaire -> ordre 1")
check(M.ordre_cinetique("E2") == 2, "E2 bimoléculaire -> ordre 2")
check(M.ordre_cinetique("sn1") == 1 and M.ordre_cinetique(" e2 ") == 2, "casse/espaces normalisés")
check(leve(M.ordre_cinetique, "SN3"), "mécanisme inexistant SN3 -> ValueError")
check(leve(M.ordre_cinetique, "Diels-Alder"), "hors champ -> ValueError")
check(leve(M.ordre_cinetique, 1), "non textuel -> ValueError")
check(leve(M.ordre_cinetique, True), "booléen -> ValueError")

# ── MÉCANISME : concerté / carbocation / étapes ──────────────────────────────────────────────────────────────────
check(M.concerte("SN2") is True and M.concerte("E2") is True, "SN2/E2 concertés")
check(M.concerte("SN1") is False and M.concerte("E1") is False, "SN1/E1 par étapes")
check(M.passe_par_carbocation("SN1") is True and M.passe_par_carbocation("E1") is True, "SN1/E1 via carbocation")
check(M.passe_par_carbocation("SN2") is False and M.passe_par_carbocation("E2") is False, "SN2/E2 sans carbocation")
check(M.nombre_etapes("SN1") == 2 and M.nombre_etapes("E1") == 2, "SN1/E1 : 2 étapes")
check(M.nombre_etapes("SN2") == 1 and M.nombre_etapes("E2") == 1, "SN2/E2 : 1 étape")
# cohérence interne : unimoléculaire <=> carbocation <=> 2 étapes
check(all((M.ordre_cinetique(m) == 1) == M.passe_par_carbocation(m) == (M.nombre_etapes(m) == 2)
          for m in ("SN1", "SN2", "E1", "E2")), "cohérence ordre/carbocation/étapes")
check(leve(M.concerte, "SN3") and leve(M.passe_par_carbocation, "X") and leve(M.nombre_etapes, ""),
      "mécanismes inconnus -> ValueError")

# ── STÉRÉOCHIMIE établie ─────────────────────────────────────────────────────────────────────────────────────────
check(M.stereochimie("SN2") == "inversion", "SN2 -> inversion de Walden")
check(M.stereochimie("SN1") == "racemisation", "SN1 -> racémisation")
check(M.stereochimie("E2") == "anti-periplanaire", "E2 -> anti-périplanaire")
check(M.stereochimie("E1") == "non-stereospecifique", "E1 -> non stéréospécifique")
check(leve(M.stereochimie, "SN0"), "mécanisme inconnu -> ValueError")

# ── DÉTERMINISME ─────────────────────────────────────────────────────────────────────────────────────────────────
check(M.type_substitution("tertiaire", "faible", "polaire_protique")
      == M.type_substitution("tertiaire", "faible", "polaire_protique"), "type_substitution déterministe")
check(M.type_elimination("primaire", "fort", "polaire_aprotique")
      == M.type_elimination("primaire", "fort", "polaire_aprotique"), "type_elimination déterministe")
check(M.ordre_cinetique("SN1") == M.ordre_cinetique("SN1"), "ordre_cinetique déterministe")
check(M.stereochimie("SN2") == M.stereochimie("SN2"), "stereochimie déterministe")

print(f'\n=== valide_mecanismes_reactionnels : {ok}/{ok+ko} ===')
import sys
sys.exit(0 if ko == 0 else 1)
