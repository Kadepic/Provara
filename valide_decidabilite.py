"""VALIDE decidabilite.py — held-out ADVERSE, FAUX=0. Ancres = FAITS ÉTABLIS de calculabilité/complexité
(théorèmes prouvés et sourcés) + SOUNDNESS (problème hors catalogue -> ValueError) + déterminisme.
"""
import decidabilite as M

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


# ── ANCRES : statut établi de chaque problème (théorèmes prouvés) ──
check(M.statut_decidabilite("arret") == "indecidable", "arret INDÉCIDABLE (Turing 1936)")
check(M.est_decidable("arret") is False, "est_decidable(arret) = False")
check(M.statut_decidabilite("SAT") == "decidable", "SAT décidable (NP-complet, Cook)")
check(M.est_decidable("SAT") is True, "est_decidable(SAT) = True")
check(M.statut_decidabilite("satisfiabilite_propositionnelle") == "decidable", "SAT libellé long décidable")
check(M.statut_decidabilite("primalite") == "decidable", "primalité décidable (AKS, P)")
check(M.est_decidable("primalite") is True, "est_decidable(primalite) = True")
check(M.statut_decidabilite("PCP") == "indecidable", "PCP indécidable (Post 1946)")
check(M.est_decidable("PCP") is False, "est_decidable(PCP) = False")
check(M.statut_decidabilite("correspondance_post") == "indecidable", "correspondance de Post indécidable")
check(M.statut_decidabilite("equivalence_machines_turing") == "indecidable", "équivalence MT indécidable (Rice)")
check(M.est_decidable("equivalence_machines_turing") is False, "est_decidable(equiv MT) = False")
check(M.statut_decidabilite("accessibilite_graphe") == "decidable", "accessibilité graphe décidable (P)")
check(M.est_decidable("accessibilite_graphe") is True, "est_decidable(accessibilite_graphe) = True")

# ── CLASSES DE COMPLEXITÉ établies ──
check(M.classe_complexite("SAT") == "NP-complet", "SAT NP-complet (Cook-Levin)")
check(M.classe_complexite("primalite") == "P", "primalité dans P (AKS)")
check(M.classe_complexite("arret").startswith("indecidable"), "arrêt classé indécidable")

# ── ALIAS / synonymes mènent au même fait ──
check(M.est_decidable("sat") == M.est_decidable("satisfiabilite"), "alias SAT cohérents")
check(M.statut_decidabilite("halting") == M.statut_decidabilite("arret"), "alias halting=arret")
check(M.statut_decidabilite("reachability") == "decidable", "alias reachability décidable")
check(M.statut_decidabilite("Primality") == "decidable", "casse/anglais primalité")

# ── COHÉRENCE statut/est_decidable sur tout le catalogue ──
check(all((M.statut_decidabilite(p) == "decidable") == M.est_decidable(p) for p in M.catalogue()),
      "statut_decidabilite cohérent avec est_decidable")
check(set(M.catalogue()) == {"arret", "satisfiabilite_propositionnelle", "primalite",
                             "equivalence_machines_turing", "correspondance_post", "accessibilite_graphe"},
      "catalogue = 6 problèmes établis")

# ── SOUNDNESS : hors catalogue / invalide -> ValueError (abstention, jamais deviné) ──
check(leve(M.statut_decidabilite, "conjecture_de_collatz"), "Collatz hors catalogue -> ValueError")
check(leve(M.est_decidable, "probleme_inexistant"), "inconnu -> ValueError")
check(leve(M.statut_decidabilite, "hypothese_de_riemann"), "Riemann hors catalogue -> ValueError")
check(leve(M.statut_decidabilite, ""), "vide -> ValueError")
check(leve(M.statut_decidabilite, "   "), "blancs -> ValueError")
check(leve(M.est_decidable, None), "None -> ValueError")
check(leve(M.statut_decidabilite, 42), "int -> ValueError")
check(leve(M.classe_complexite, "diophantien"), "Hilbert10 (non listé) -> ValueError")
check(leve(M.reference, "xyz"), "reference inconnu -> ValueError")

# ── DÉTERMINISME ──
check(M.statut_decidabilite("arret") == M.statut_decidabilite("arret"), "déterminisme statut")
check(M.est_decidable("SAT") == M.est_decidable("SAT"), "déterminisme est_decidable")

print(f"\n=== valide_decidabilite : {ok}/{ok + ko} ===")
import sys
sys.exit(0 if ko == 0 else 1)
