#!/usr/bin/env python3
"""
VALIDATION de regles_induites.py — pont induction→déduction. FAUX=0 : seules les règles VALIDÉES entrent au
Datalog (rejetées/non-réfutables JAMAIS) ; un fait dérivé via une règle induite est INCERTAIN, jamais 'verifie' ;
la contamination se propage (une règle certaine appuyée sur un support induit reste incertaine). Léger (stdlib).
"""
from __future__ import annotations

import sys

import induction_horn as H
import regles_induites as RI


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

    # ── clauses_datalog : traduction exacte des 3 règles structurelles ─────────────────────────
    check("clauses TRANSITIVITE : R(X,Z) :- R(X,Y),R(Y,Z)",
          RI.clauses_datalog(H.TRANSITIVITE, "r") == [(("r", "X", "Z"), [("r", "X", "Y"), ("r", "Y", "Z")])])
    check("clauses SYMETRIE : R(Y,X) :- R(X,Y)",
          RI.clauses_datalog(H.SYMETRIE, "r") == [(("r", "Y", "X"), [("r", "X", "Y")])])
    check("clauses REFLEXIVITE : couvre gauche ET droite (2 clauses)",
          len(RI.clauses_datalog(H.REFLEXIVITE, "r")) == 2)
    try:
        RI.clauses_datalog("inconnue", "r")
        check("règle inconnue -> ValueError", False)
    except ValueError:
        check("règle inconnue -> ValueError", True)

    # ── Scénario ANCÊTRE : transitivité validée branchée, symétrie rejetée JAMAIS branchée ────
    m = RI.MoteurInduit()
    for a, b in [("alice", "bob"), ("bob", "carol"), ("alice", "carol"), ("carol", "dan")]:
        m.ajoute_fait("ancetre", a, b, "généalogie")
    r = m.branche_relation("ancetre", negatifs={("bob", "alice")})
    check("ANCÊTRE : transitivité VALIDÉE et branchée",
          H.TRANSITIVITE in {t for t, _s, _n in r["validees"]} and m.induites)
    check("ANCÊTRE : symétrie REJETÉE (dérive le négatif (bob,alice))",
          H.SYMETRIE in {t for t, _e in r["rejetees"]})
    check("fait de BASE -> verifie", m.statut("ancetre", "alice", "bob")[0] == RI.VERIFIE)
    check("généralisation induite (alice,dan) -> INCERTAIN, jamais verifie",
          m.statut("ancetre", "alice", "dan")[0] == RI.INCERTAIN)
    check("généralisation induite (bob,dan) -> INCERTAIN",
          m.statut("ancetre", "bob", "dan")[0] == RI.INCERTAIN)
    check("FAUX=0 : la symétrie rejetée n'a rien dérivé ET (bob,alice) déclaré faux -> REFUTE",
          m.statut("ancetre", "bob", "alice")[0] == RI.REFUTE)
    check("non-dérivable -> HORS", m.statut("ancetre", "dan", "alice")[0] == RI.HORS)
    check("reponses étiquetées : bob/carol verifie, dan incertain",
          m.reponses("ancetre", "alice") == [("bob", RI.VERIFIE), ("carol", RI.VERIFIE), ("dan", RI.INCERTAIN)])

    # ── FAUX=0 : sans négatifs, RIEN n'est branché (monde ouvert, pas de CWA) ──────────────────
    m2 = RI.MoteurInduit()
    for a, b in [("x", "y"), ("y", "z"), ("x", "z")]:
        m2.ajoute_fait("lien", a, b)
    r2 = m2.branche_relation("lien", negatifs=set())
    check("sans négatifs : validees vide, aucune règle induite branchée",
          r2["validees"] == [] and not m2.induites)
    check("sans négatifs : aucune généralisation servie ((y,z)∘? -> rien de neuf)",
          m2.statut("lien", "y", "x")[0] == RI.HORS)

    # ── Contamination : règle CERTAINE appuyée sur un support INDUIT -> incertain (récursif) ──
    m.ajoute_regle_certaine(("descend", "Y", "X"), [("ancetre", "X", "Y")], "inverse_manuelle")
    check("règle certaine sur support de BASE -> verifie",
          m.statut("descend", "bob", "alice")[0] == RI.VERIFIE)
    check("règle certaine sur support INDUIT (alice,dan) -> INCERTAIN (contamination récursive)",
          m.statut("descend", "dan", "alice")[0] == RI.INCERTAIN)

    # ── Rétraction TMS : le support de base part, la généralisation induite tombe aussi ───────
    m.retracte("ancetre", "carol", "dan")
    check("rétraction : (alice,dan) induit tombe -> HORS (TMS sound)",
          m.statut("ancetre", "alice", "dan")[0] == RI.HORS)
    check("rétraction : les faits de base restants tiennent",
          m.statut("ancetre", "alice", "carol")[0] == RI.VERIFIE)

    # ── Déterminisme ───────────────────────────────────────────────────────────────────────────
    def run():
        mm = RI.MoteurInduit()
        for a, b in [("alice", "bob"), ("bob", "carol"), ("alice", "carol"), ("carol", "dan")]:
            mm.ajoute_fait("ancetre", a, b)
        mm.branche_relation("ancetre", negatifs={("bob", "alice")})
        return mm.reponses("ancetre", "alice"), sorted(mm.induites)
    check("déterminisme : 2 runs identiques", run() == run())

    # ══ PINS D'ATTAQUE (vérif adversariale exécutée 2026-07-02 — chaque trou corrigé reste fermé) ═══════════
    # ── Trou FAUX=0 : collision du nom réservé 'base' (une règle 'base' court-circuitait _certain) ─────────
    m4 = run_m = RI.MoteurInduit()
    for a, b in [("alice", "bob"), ("bob", "carol"), ("alice", "carol"), ("carol", "dan")]:
        m4.ajoute_fait("ancetre", a, b)
    m4.branche_relation("ancetre", negatifs={("bob", "alice")})
    try:
        m4.ajoute_regle_certaine(("descend", "Y", "X"), [("ancetre", "X", "Y")], nom="base")
        check("ATTAQUE 'base' : nom réservé refusé (ValueError)", False)
    except ValueError:
        check("ATTAQUE 'base' : nom réservé refusé (ValueError)", True)
    try:
        m4.ajoute_regle_certaine(("descend", "Y", "X"), [("ancetre", "X", "Y")], nom="induit:x:y")
        check("ATTAQUE préfixe 'induit:' : refusé pour une règle certaine (ValueError)", False)
    except ValueError:
        check("ATTAQUE préfixe 'induit:' : refusé pour une règle certaine (ValueError)", True)

    # ── Validation au POINT FIXE : négatif atteignable seulement à profondeur ≥ 2 -> REJET désormais ───────
    m5 = RI.MoteurInduit()
    for a, b in [("a", "b"), ("b", "c"), ("c", "d"), ("d", "e"), ("a", "c")]:
        m5.ajoute_fait("chaine", a, b)
    r5 = m5.branche_relation("chaine", negatifs={("a", "e")})
    check("POINT FIXE : transitivité qui dériverait le négatif (a,e) en profondeur 3 -> REJETÉE",
          H.TRANSITIVITE in {t for t, _e in r5["rejetees"]} and not m5.induites)
    check("POINT FIXE : le négatif déclaré reste refute, jamais dérivable",
          m5.statut("chaine", "a", "e")[0] == RI.REFUTE)

    # ── Négatifs PERSISTÉS : un fait ultérieur rend le négatif dérivable -> refute, jamais incertain ───────
    m6 = RI.MoteurInduit()
    for a, b in [("x", "y"), ("y", "z"), ("x", "z")]:
        m6.ajoute_fait("lien", a, b)
    m6.branche_relation("lien", negatifs={("x", "w")})       # transitivité validée (w hors d'atteinte)
    m6.ajoute_fait("lien", "z", "w")                          # …désormais (x,w) dérivable par la règle induite
    check("GARDE PERSISTANTE : négatif déclaré dérivable APRÈS coup -> REFUTE (pas incertain)",
          m6.statut("lien", "x", "w")[0] == RI.REFUTE)
    try:
        m6.ajoute_fait("lien", "x", "w")
        check("ajoute_fait d'un négatif déclaré -> ValueError (contradiction)", False)
    except ValueError:
        check("ajoute_fait d'un négatif déclaré -> ValueError (contradiction)", True)

    # ── Re-branchement : idempotent (pas de duplication) + une règle réfutée ne survit pas en fantôme ──────
    n_regles = len(m4.moteur.regles)
    m4.branche_relation("ancetre", negatifs={("bob", "alice")})
    check("RE-BRANCHEMENT idempotent : nombre de règles inchangé", len(m4.moteur.regles) == n_regles)
    m7 = RI.MoteurInduit()
    for a, b in [("a", "b"), ("b", "a"), ("c", "d"), ("d", "c")]:
        m7.ajoute_fait("ami", a, b)
    m7.branche_relation("ami", negatifs={("a", "c")})         # symétrie validée
    m7.ajoute_fait("ami", "e", "f")
    r7 = m7.branche_relation("ami", negatifs={("f", "e")})    # symétrie désormais RÉFUTÉE
    check("RÈGLE FANTÔME : réfutée au 2e branchement -> débranchée, (f,e) non dérivable",
          H.SYMETRIE in {t for t, _e in r7["rejetees"]} and not m7.induites
          and m7.statut("ami", "f", "e")[0] == RI.REFUTE and m7.statut("ami", "e", "f")[0] == RI.VERIFIE)

    # ── Négatifs malformés : la réfutation ne peut plus être désarmée en silence ───────────────────────────
    try:
        RI.MoteurInduit().branche_relation("r", negatifs=("c", "b"))     # couple NU au lieu de {couple}
        check("negatifs malformé (couple nu) -> ValueError", False)
    except ValueError:
        check("negatifs malformé (couple nu) -> ValueError", True)

    # ── Profondeur : _certain ITÉRATIF (une provenance linéaire de 5000 ne crashe plus) ────────────────────
    m8 = RI.MoteurInduit()
    m8.moteur.prov = {("r", "a", str(i)): [("regle_certaine", [("r", "a", str(i + 1))])] for i in range(5000)}
    m8.moteur.prov[("r", "a", "5000")] = [("base", "src")]
    check("PROFONDEUR 5000 : _certain itératif répond True sans RecursionError",
          m8._certain(("r", "a", "0")) is True)
    m8.induites.add("regle_certaine")
    check("PROFONDEUR 5000 : contamination induite détectée (False)", m8._certain(("r", "a", "0")) is False)

    # ── explique() après mutation : lazy-matérialisation (plus d'état périmé) ──────────────────────────────
    m4.ajoute_fait("ancetre", "dan", "eve")
    check("explique() après mutation voit le fait de base (lazy re-matérialisation)",
          "[base:" in m4.explique("ancetre", "dan", "eve"))

    # ── CÂBLAGE ia.py (anti-orphelin) ──────────────────────────────────────────────────────────────────────
    import ia
    mi = ia.moteur_induit()
    mi.ajoute_fait("ancetre", "a", "b")
    mi.ajoute_fait("ancetre", "b", "c")
    mi.ajoute_fait("ancetre", "a", "c")
    mi.branche_relation("ancetre", negatifs={("b", "a")})
    check("CÂBLAGE ia.moteur_induit : fabrique le moteur apprendre→valider→raisonner",
          mi.statut("ancetre", "a", "c")[0] == RI.VERIFIE and mi.statut("ancetre", "b", "a")[0] == RI.REFUTE)

    print(f"\n=== valide_regles_induites : {ok}/{ok + len(fails)} ===")
    if fails:
        print("ÉCHECS :", ", ".join(fails))
    return 0 if not fails else 1


if __name__ == "__main__":
    sys.exit(main())
