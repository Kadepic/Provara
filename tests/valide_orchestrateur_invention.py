#!/usr/bin/env python3
"""
VALIDATION de orchestrateur_invention.py — le capstone multi-mode. FAUX=0 : n'appelle que des modes sound, abstient
au 1er None, ne rapporte que des sorties re-vérifiées, ne synthétise jamais. Léger (stdlib pur, pas de lecteur).
"""
from __future__ import annotations

import sys

import orchestrateur_invention as O
import causalite


def main() -> int:
    ok, fails = 0, []

    def check(nom, cond):
        nonlocal ok
        if cond:
            ok += 1
            print(f"  [OK ] {nom}")
        else:
            fails.append(nom)
            print(f"  [XX ] {nom}")

    # ── ENCHAÎNEMENT « diagnostiquer puis réparer » : abduction -> plan ────────────────────────
    g = causalite.GrapheCausal()
    g.ajoute_cause("fuite", "odeur")
    g.ajoute_cause("fuite", "alarme")
    orch = O.OrchestrateurInvention()
    op_fermer = O.OrchestrateurInvention  # placeholder pour lisibilité ; on construit l'opérateur ci-dessous
    from invention_divergente import Operateur
    ferme = Operateur("fermer_vanne", pre=["fuite_active"], ajoute=["fuite_stoppee"], retire=["fuite_active"])

    plan = [
        ("diagnostic", "explique_observations", {"graphe": g, "observations": ["odeur", "alarme"]}),
        # l'étape 2 consomme le diagnostic (lit le blackboard) puis planifie une réparation
        ("reparation", "plan_procede",
         lambda self: {"etat_initial": ["fuite_active"], "but": ["fuite_stoppee"], "operateurs": [ferme]}),
    ]
    r = orch.enchaine(plan)
    check("ENCHAÎNEMENT : plan complet (abduction puis planification)", r["complet"] and r["abstenu_a"] is None)
    check("ENCHAÎNEMENT : le diagnostic identifie la cause 'fuite'",
          r["resultats"]["diagnostic"]["hypotheses"] == ["fuite"])
    check("ENCHAÎNEMENT : la réparation est un plan re-joué ([fermer_vanne])",
          r["resultats"]["reparation"] == ["fermer_vanne"])
    check("TRACE : deux gestes appliqués, tous deux ont produit", orch.trace() == [
          ("diagnostic", "explique_observations", True), ("reparation", "plan_procede", True)])

    # ── ENCHAÎNEMENT « apprendre une loi puis lever une contrainte » (data -> loi) ─────────────
    orch2 = O.OrchestrateurInvention()
    r2 = orch2.enchaine([("loi", "apprend_loi", {"donnees": [(1, 2), (2, 4), (3, 6)]})])
    check("MODE apprend_loi via orchestrateur : y=2x (proportionnel)",
          r2["complet"] and r2["resultats"]["loi"]["forme"] == "proportionnel")

    # ── FAUX=0 : un mode qui ABSTIENT (None) arrête l'enchaînement, rien de fabriqué ───────────
    orch3 = O.OrchestrateurInvention()
    plan_abstient = [
        ("loi_impossible", "apprend_loi", {"donnees": [(1, 1), (2, 5), (3, 100)]}),  # aucune loi simple -> None
        ("suite", "arbitre_compromis", {"candidats": [("A", (1,))], "sens": ("min",)}),  # ne doit PAS s'exécuter
    ]
    r3 = orch3.enchaine(plan_abstient)
    check("FAUX=0 : abstention au 1er None (loi impossible) -> complet=False, abstenu_a='loi_impossible'",
          not r3["complet"] and r3["abstenu_a"] == "loi_impossible")
    check("FAUX=0 : l'étape suivante n'a PAS été exécutée (pas de sortie fabriquée)",
          "suite" not in r3["resultats"] and len(orch3.trace()) == 1)
    check("FAUX=0 : rien de non-vérifié n'est posté au blackboard (loi_impossible absente)",
          orch3.lis("loi_impossible") is None)

    # ── FAUX=0 : mode inconnu -> ValueError (jamais un geste inventé) ──────────────────────────
    orch4 = O.OrchestrateurInvention()
    try:
        orch4.applique("x", "mode_bidon", a=1)
        leve = False
    except ValueError:
        leve = True
    check("FAUX=0 : mode inconnu -> ValueError", leve)

    # ── CÂBLAGE ia.py ─────────────────────────────────────────────────────────────────────────
    import ia
    orch_ia = ia.orchestre_invention()
    ri = orch_ia.enchaine([("loi", "apprend_loi", {"donnees": [(1, 3), (2, 6), (3, 9)]})])
    check("CÂBLAGE ia.orchestre_invention : enchaîne un mode et rapporte la sortie vérifiée",
          ri["complet"] and ri["resultats"]["loi"]["forme"] == "proportionnel")

    print(f"\n=== valide_orchestrateur_invention : {ok}/{ok + len(fails)} ===")
    if fails:
        print("ÉCHECS :", ", ".join(fails))
    return 0 if not fails else 1


if __name__ == "__main__":
    sys.exit(main())
