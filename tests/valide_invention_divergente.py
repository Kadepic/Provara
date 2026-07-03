#!/usr/bin/env python3
"""
VALIDATION de invention_divergente.py — les 6 modes d'invention HORS recombinaison (priorité #1 Yohan),
câblés à ia.py. FAUX=0 : chaque mode délègue à une brique sound (abstention/None sans preuve). On vérifie
(a) chaque mode produit le bon résultat sur un cas jouet, (b) chaque mode ABSTIENT quand rien ne colle,
(c) le câblage ia.* est vivant. Léger (pas de lecteur).
"""
from __future__ import annotations

import sys

import invention_divergente as INV


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

    # ── 1. APPRENDRE UNE LOI (data → f(x)) ──────────────────────────────────────────────────
    loi = INV.apprend_loi([(1, 2), (2, 4), (3, 6), (5, 10)])
    check("LOI : y=2x découverte (proportionnel)", loi is not None and loi["forme"] == "proportionnel"
          and abs(loi["params"]["a"] - 2.0) < 1e-9 and abs(loi["predit"](10) - 20.0) < 1e-9)
    carre = INV.apprend_loi([(1, 1), (2, 4), (3, 9), (4, 16)])
    check("LOI : y=x² découverte (carré)", carre is not None and carre["forme"] == "carré")
    check("LOI FAUX=0 : données sans loi simple -> None (abstention, jamais une loi plaquée)",
          INV.apprend_loi([(1, 1), (2, 5), (3, 100), (4, 7)]) is None)
    check("LOI FAUX=0 : 1 seul point -> None (indéterminé)", INV.apprend_loi([(1, 2)]) is None)

    # ── 2. LEVER UNE CONTRAINTE (TRIZ) ──────────────────────────────────────────────────────
    vars_ = {"x": [0, 1, 2], "y": [0, 1, 2]}
    egal = (("x", "y"), lambda a, b: a == b, "x_egal_y")
    diff = (("x", "y"), lambda a, b: a != b, "x_diff_y")
    r = INV.leve_contrainte(vars_, [egal, diff])          # x==y ET x!=y : sur-contraint
    check("TRIZ : problème sur-contraint -> UNE contrainte à lever, solution vérifiée",
          r is not None and len(r["contraintes_a_relacher"]) == 1
          and r["contraintes_a_relacher"][0] in ("x_egal_y", "x_diff_y") and r["solution"] is not None)
    r2 = INV.leve_contrainte(vars_, [egal])               # déjà satisfiable (x=y=0)
    check("TRIZ : déjà satisfiable -> rien à relâcher ([], solution)",
          r2 is not None and r2["contraintes_a_relacher"] == [] and r2["solution"] is not None)
    vide = INV.leve_contrainte({"x": []}, [])             # domaine vide -> insoluble même tout relâché
    check("TRIZ FAUX=0 : insoluble structurellement (domaine vide) -> None honnête", vide is None)

    # ── 3. TRANSFÉRER UNE STRUCTURE (analogie) ──────────────────────────────────────────────
    source = [("transporte", "chaleur", "gradient_T"), ("cause", "gradient_T", "flux_chaleur")]
    cible = [("transporte", "charge", "gradient_V"), ("cause", "gradient_V", "flux_courant")]
    a = INV.transfere_analogie(source, cible)
    check("ANALOGIE : chaleur↔charge structurellement alignée (couverture=1)",
          a is not None and a["couverture"] == 1.0 and a["mapping"].get("chaleur") == "charge")
    check("ANALOGIE FAUX=0 : structures sans alignement -> None (pas d'analogie forcée)",
          INV.transfere_analogie([("p", "a", "b")], [("q", "c", "d")]) is None)

    # ── 4. ARBITRER DES COMPROMIS (Pareto) ──────────────────────────────────────────────────
    cands = [("A", (1, 1)), ("B", (2, 2)), ("C", (1, 3))]     # minimiser les deux
    fr = INV.arbitre_compromis(cands, ("min", "min"))
    etiq = {e for e, _ in fr}
    check("PARETO : A domine B et C -> front = {A}", etiq == {"A"})
    cands2 = [("X", (1, 5)), ("Y", (5, 1))]                    # compromis : aucun ne domine
    check("PARETO : compromis réel -> les deux au front (aucun ne domine)",
          {e for e, _ in INV.arbitre_compromis(cands2, ("min", "min"))} == {"X", "Y"})

    # ── 5. EXPLIQUER UN PHÉNOMÈNE (abduction) ───────────────────────────────────────────────
    import causalite
    g = causalite.GrapheCausal()
    g.ajoute_cause("fuite_gaz", "odeur")
    g.ajoute_cause("fuite_gaz", "alarme")
    g.ajoute_cause("pile_faible", "bip")
    exp = INV.explique_observations(g, ["odeur", "alarme"])
    check("ABDUCTION : odeur+alarme expliqués par la cause commune 'fuite_gaz'",
          exp is not None and exp["hypotheses"] == ["fuite_gaz"] and exp["couvre"] == {"odeur", "alarme"})
    exp2 = INV.explique_observations(g, ["odeur", "phenomene_inconnu"])
    check("ABDUCTION FAUX=0 : observation sans cause -> signalée inexpliquée (jamais inventée)",
          exp2 is not None and "phenomene_inconnu" in exp2["inexpliquees"])

    # ── 6. PLANIFIER UN PROCÉDÉ (STRIPS) ────────────────────────────────────────────────────
    op1 = INV.Operateur("chauffer", pre=["solide"], ajoute=["liquide"], retire=["solide"])
    op2 = INV.Operateur("bouillir", pre=["liquide"], ajoute=["gaz"], retire=["liquide"])
    p = INV.plan_procede(["solide"], ["gaz"], [op1, op2])
    check("PLAN : solide -> gaz via [chauffer, bouillir]", p == ["chauffer", "bouillir"])
    check("PLAN FAUX=0 : but inatteignable -> None (jamais un plan fabriqué)",
          INV.plan_procede(["solide"], ["plasma"], [op1, op2]) is None)

    # ── CÂBLAGE ia.py (surface additive vivante) ────────────────────────────────────────────
    import ia
    check("CÂBLAGE ia.apprend_loi", ia.apprend_loi([(1, 3), (2, 6), (3, 9)])["forme"] == "proportionnel")
    check("CÂBLAGE ia.leve_contrainte", ia.leve_contrainte(vars_, [egal, diff])["solution"] is not None)
    check("CÂBLAGE ia.transfere_analogie", ia.transfere_analogie(source, cible)["couverture"] == 1.0)
    check("CÂBLAGE ia.arbitre_compromis", {e for e, _ in ia.arbitre_compromis(cands, ("min", "min"))} == {"A"})
    check("CÂBLAGE ia.explique_observations", ia.explique_observations(g, ["bip"])["hypotheses"] == ["pile_faible"])
    check("CÂBLAGE ia.plan_procede", ia.plan_procede(["solide"], ["liquide"], [op1, op2]) == ["chauffer"])

    print(f"\n=== valide_invention_divergente : {ok}/{ok + len(fails)} ===")
    if fails:
        print("ÉCHECS :", ", ".join(fails))
    return 0 if not fails else 1


if __name__ == "__main__":
    sys.exit(main())
