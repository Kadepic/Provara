"""VALIDE classes_complexite.py — held-out ADVERSE, FAUX=0. Ancres EXTERNES connues (Cook–Levin 1971,
Karp 1972 « 21 problèmes », AKS 2002, Turing 1936 ; inclusions prouvées P ⊆ NP, NP ⊆ PSPACE) + SOUNDNESS
(entrée hors référentiel -> ValueError, jamais un résultat faux) + DÉTERMINISME. La SEULE question ouverte
(P =? NP) doit rester 'ouvert' — toute résolution serait un FAUX.
"""
import classes_complexite as M

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


# ── 1) CLASSIFICATION CANONIQUE — ancres établies ─────────────────────────────────────────────────────────────
check(M.classe_probleme("SAT") == "NP-complet", "SAT NP-complet (Cook–Levin)")
check(M.classe_probleme("3SAT") == "NP-complet", "3SAT NP-complet (Karp)")
check(M.classe_probleme("tri") == "P", "tri ∈ P (O(n log n))")
check(M.classe_probleme("plus_court_chemin") == "P", "plus court chemin ∈ P (Dijkstra)")
check(M.classe_probleme("primalite") == "P", "primalité ∈ P (AKS 2002)")
check(M.classe_probleme("voyageur_commerce") == "NP-difficile", "TSP optimisation NP-difficile")
check(M.classe_probleme("sac_a_dos") == "NP-complet", "sac à dos NP-complet (Karp)")
check(M.classe_probleme("clique") == "NP-complet", "clique NP-complet (Karp)")
check(M.classe_probleme("cycle_hamiltonien") == "NP-complet", "cycle hamiltonien NP-complet (Karp)")
check(M.classe_probleme("couverture_sommets") == "NP-complet", "vertex cover NP-complet (Karp)")
check(M.classe_probleme("coloration_graphe") == "NP-complet", "3-coloration NP-complet (Karp)")
check(M.classe_probleme("partition") == "NP-complet", "partition NP-complet (Karp)")
check(M.classe_probleme("arret") == "indécidable", "problème de l'arrêt indécidable (Turing)")
check(M.classe_probleme("programmation_lineaire") == "P", "LP ∈ P (Khachiyan)")

# ── 2) ALIAS reconnus -> même classification ──────────────────────────────────────────────────────────────────
check(M.classe_probleme("TSP") == "NP-difficile", "alias TSP -> voyageur_commerce")
check(M.classe_probleme("tsp") == "NP-difficile", "alias tsp -> voyageur_commerce")
check(M.classe_probleme("knapsack") == "NP-complet", "alias knapsack -> sac_a_dos")
check(M.classe_probleme("halting") == "indécidable", "alias halting -> arret")
check(M.classe_probleme("sat") == "NP-complet", "alias sat -> SAT")
check(M.classe_probleme("vertex_cover") == "NP-complet", "alias vertex_cover -> couverture_sommets")

# ── 3) PRÉDICATS — positifs établis ───────────────────────────────────────────────────────────────────────────
check(M.est_np_complet("SAT") is True, "est_np_complet(SAT) True")
check(M.est_np_complet("clique") is True, "est_np_complet(clique) True")
check(M.est_np_complet("tri") is False, "est_np_complet(tri) False (classé P)")
check(M.est_np_complet("voyageur_commerce") is False, "est_np_complet(TSP) False (NP-difficile, non dans NP)")
check(M.est_np_complet("arret") is False, "est_np_complet(arret) False (indécidable)")

check(M.est_np_difficile("SAT") is True, "NP-complet => NP-difficile (SAT)")
check(M.est_np_difficile("voyageur_commerce") is True, "TSP NP-difficile True")
check(M.est_np_difficile("tri") is False, "tri non classé NP-difficile")

check(M.est_dans_p("tri") is True, "est_dans_p(tri) True")
check(M.est_dans_p("primalite") is True, "est_dans_p(primalite) True (AKS)")
check(M.est_dans_p("SAT") is False, "SAT non classé P")

check(M.est_indecidable("arret") is True, "arret indécidable True")
check(M.est_indecidable("correspondance_post") is True, "Post correspondence indécidable True")
check(M.est_indecidable("SAT") is False, "SAT non indécidable")

check(M.dans_np("clique") is True, "clique ∈ NP True (NP-complet ⊆ NP)")
check(M.dans_np("tri") is True, "tri ∈ NP True (P ⊆ NP)")
check(M.dans_np("voyageur_commerce") is False, "TSP optimisation non classé NP")
check(M.dans_np("arret") is False, "arret non dans NP")

# ── 4) VÉRIFICATION POLYNOMIALE (certificat NP) ───────────────────────────────────────────────────────────────
check(M.verification_polynomiale("SAT") is True, "certificat SAT vérifiable en temps poly (NP)")
check(M.verification_polynomiale("clique") is True, "certificat clique vérifiable en temps poly")
check(M.verification_polynomiale("tri") is True, "tri ∈ P ⊆ NP -> vérifiable")
check(M.verification_polynomiale("voyageur_commerce") is False, "TSP optimisation : pas de vérif poly d'optimalité")
check(M.verification_polynomiale("arret") is False, "arret : pas de vérification polynomiale")

# ── 5) RELATIONS ENTRE CLASSES — faits établis + LA question ouverte ──────────────────────────────────────────
check(M.relation_classes("P", "NP") == "inclus", "P ⊆ NP (établi)")
check(M.relation_classes("NP", "P") == "ouvert", "NP ⊆ P ? = P vs NP (OUVERT)")
check(M.relation_classes("P", "P") == "egal", "P = P")
check(M.relation_classes("NP", "NP") == "egal", "NP = NP")
check(M.relation_classes("NP-complet", "NP") == "inclus", "NP-complet ⊆ NP (par déf)")
check(M.relation_classes("NP-complet", "NP-difficile") == "inclus", "NP-complet ⊆ NP-difficile (par déf)")
check(M.relation_classes("P", "PSPACE") == "inclus", "P ⊆ PSPACE (établi)")
check(M.relation_classes("NP", "PSPACE") == "inclus", "NP ⊆ PSPACE (établi)")
check(M.p_egal_np() == "ouvert", "P =? NP -> ouvert (jamais tranché)")
check(M.p_inclus_np() == "inclus", "P ⊆ NP -> inclus")

# ── 6) DESCRIPTIONS / CATALOGUE ───────────────────────────────────────────────────────────────────────────────
check("NP-complet" in M.decrit_classe("NP-complet") or "NP" in M.decrit_classe("NP-complet"),
      "description NP-complet non vide cohérente")
check(isinstance(M.decrit_classe("P"), str) and len(M.decrit_classe("P")) > 0, "description P non vide")
check(M.classes() == ("P", "NP", "NP-complet", "NP-difficile", "PSPACE", "indécidable"), "6 classes au catalogue")
check("SAT" in M.problemes(), "SAT dans le catalogue de problèmes")
check("arret" in M.problemes(), "arret dans le catalogue de problèmes")
check("TSP" not in M.problemes(), "les alias ne polluent pas problemes()")
check(M.problemes() == tuple(sorted(M.problemes())), "problemes() trié déterministe")

# ── 7) SOUNDNESS — entrée hors référentiel -> ValueError (abstention) ─────────────────────────────────────────
check(leve(M.classe_probleme, "foobar"), "problème inconnu -> ValueError")
check(leve(M.classe_probleme, ""), "chaîne vide -> ValueError")
check(leve(M.classe_probleme, "   "), "blancs seuls -> ValueError")
check(leve(M.classe_probleme, 42), "entier -> ValueError")
check(leve(M.classe_probleme, None), "None -> ValueError")
check(leve(M.classe_probleme, True), "bool -> ValueError")
check(leve(M.est_np_complet, "inconnu"), "est_np_complet inconnu -> ValueError")
check(leve(M.est_np_difficile, "inconnu"), "est_np_difficile inconnu -> ValueError")
check(leve(M.est_dans_p, "inconnu"), "est_dans_p inconnu -> ValueError")
check(leve(M.est_indecidable, "inconnu"), "est_indecidable inconnu -> ValueError")
check(leve(M.dans_np, "inconnu"), "dans_np inconnu -> ValueError")
check(leve(M.verification_polynomiale, "inconnu"), "verification_polynomiale inconnu -> ValueError")
check(leve(M.relation_classes, "XYZ", "NP"), "classe gauche inconnue -> ValueError")
check(leve(M.relation_classes, "P", "XYZ"), "classe droite inconnue -> ValueError")
check(leve(M.relation_classes, "P", "indécidable"), "paire non établie (P/indécidable) -> ValueError")
check(leve(M.relation_classes, "PSPACE", "P"), "paire non établie (PSPACE/P inverse) -> ValueError")
check(leve(M.relation_classes, "NP", "NP-complet"), "NP ⊆ NP-complet non établi -> ValueError")
check(leve(M.relation_classes, "P", "NP-complet"), "P ⊆ NP-complet non établi -> ValueError")
check(leve(M.relation_classes, 1, "NP"), "type non-str -> ValueError")
check(leve(M.decrit_classe, "ABC"), "classe inconnue (decrit) -> ValueError")

# ── 8) DÉTERMINISME ───────────────────────────────────────────────────────────────────────────────────────────
check(M.classe_probleme("SAT") == M.classe_probleme("SAT"), "déterminisme classe_probleme")
check(M.relation_classes("P", "NP") == M.relation_classes("P", "NP"), "déterminisme relation_classes")
check(M.verification_polynomiale("SAT") == M.verification_polynomiale("SAT"), "déterminisme verification_polynomiale")

print(f"\n=== valide_classes_complexite : {ok}/{ok+ko} ===")
import sys
sys.exit(0 if ko == 0 else 1)
