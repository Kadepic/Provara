#!/usr/bin/env python3
"""
VALIDATION de induction_horn.py — induction de règles de Horn validée par exemples. FAUX=0 : une règle qui dérive
un exemple NÉGATIF est REJETÉE ; sans négatifs, aucune règle n'est adoptée (non_refutable) ; une règle validée
couvre des positifs sans violer de négatif. Léger (stdlib pur, pas de lecteur).
"""
from __future__ import annotations

import sys

import induction_horn as H


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

    # ── derive : mécanique structurelle exacte ────────────────────────────────────────────────
    check("derive TRANSITIVITE : (a,b),(b,c) -> (a,c)",
          (("a", "c") in H.derive(H.TRANSITIVITE, {("a", "b"), ("b", "c")})))
    check("derive SYMETRIE : (a,b) -> (b,a)", H.derive(H.SYMETRIE, {("a", "b")}) == {("b", "a")})
    check("derive REFLEXIVITE : couvre chaque élément",
          H.derive(H.REFLEXIVITE, {("a", "b")}) == {("a", "a"), ("b", "b")})

    # ── Relation TRANSITIVE (ex. 'ancêtre') : la transitivité est CONSISTANTE ─────────────────
    anc_pos = {("a", "b"), ("b", "c"), ("a", "c"), ("b", "d"), ("c", "d"), ("a", "d")}
    anc_neg = {("d", "a"), ("c", "a")}                # descendants ne sont pas ancêtres
    r = H.induit(anc_pos, anc_neg)
    types_valides = {t for t, _s, _n in r["validees"]}
    check("ANCÊTRE : transitivité VALIDÉE (couvre des positifs, ne viole aucun négatif)",
          H.TRANSITIVITE in types_valides)
    check("ANCÊTRE : symétrie REJETÉE (dériverait (b,a) qui est négatif ou absent)",
          H.SYMETRIE in {t for t, _e in r["rejetees"]})

    # ── Relation NON transitive (ex. 'parent') : la transitivité VIOLE un négatif -> REJET ────
    par_pos = {("a", "b"), ("b", "c")}                # a parent de b, b parent de c
    par_neg = {("a", "c")}                            # a n'est PAS parent de c (c'est grand-parent)
    r2 = H.induit(par_pos, par_neg)
    check("PARENT : transitivité REJETÉE (dérive (a,c) qui est un négatif connu = FAUX=0)",
          H.TRANSITIVITE in {t for t, _e in r2["rejetees"]})
    check("PARENT : le négatif dérivé est bien (a,c)",
          any(e == ("a", "c") for t, e in r2["rejetees"] if t == H.TRANSITIVITE))

    # ── Relation SYMÉTRIQUE (ex. 'conjoint') : symétrie validée ───────────────────────────────
    conj_pos = {("a", "b"), ("b", "a"), ("c", "d"), ("d", "c")}
    conj_neg = {("a", "c")}
    r3 = H.induit(conj_pos, conj_neg)
    check("CONJOINT : symétrie VALIDÉE", H.SYMETRIE in {t for t, _s, _n in r3["validees"]})

    # ── FAUX=0 : sans exemples négatifs, AUCUNE règle adoptée (monde ouvert) ───────────────────
    r4 = H.induit(anc_pos, set())
    check("FAUX=0 : sans négatifs -> validees vide (rien d'adopté)", r4["validees"] == [])
    check("FAUX=0 : sans négatifs -> règles marquées 'non_refutable' (abstention honnête)",
          H.TRANSITIVITE in r4["non_refutables"] and H.SYMETRIE in r4["non_refutables"])

    # ── Les faits 'nouveaux' (généralisation) sont RAPPORTÉS comme incertains, pas certains ───
    ev = H.evalue(H.TRANSITIVITE, {("x", "y"), ("y", "z")}, {("z", "x")})
    check("Généralisation : (x,z) dérivé, hors exemples, rapporté dans 'nouveaux'",
          ("x", "z") in ev["nouveaux"] and ev["consistante"])

    # ── PINS D'ATTAQUE 2026-07-02 : point fixe + forme des exemples ────────────────────────────
    # Négatif atteignable SEULEMENT à profondeur ≥ 2 : une validation à 1 application le manquait.
    chaine = {("a", "b"), ("b", "c"), ("c", "d"), ("d", "e"), ("a", "c")}
    rpf = H.induit(chaine, {("a", "e")})
    check("POINT FIXE : transitivité REJETÉE (négatif (a,e) dérivable à profondeur 3)",
          H.TRANSITIVITE in {t for t, _e in rpf["rejetees"]})
    check("POINT FIXE : 'nouveaux' = inventaire complet (contient (b,e) profondeur 2)",
          ("b", "e") in H.evalue(H.TRANSITIVITE, chaine, {("z", "z")})["nouveaux"])
    # Support = UNE application (preuve réelle) : l'aller-retour du point fixe ne compte pas comme preuve.
    ev_sym = H.evalue(H.SYMETRIE, chaine, {("e", "a")})
    check("SUPPORT honnête : symétrie sur une chaîne asymétrique -> support 0 (pas d'artefact point-fixe)",
          ev_sym["support"] == 0)
    # Forme des exemples : un couple NU / une chaîne désarmeraient la réfutation en silence.
    for brut in [("c", "b"), "cb"]:
        try:
            H.induit({("b", "c"), ("c", "b")}, brut)
            check(f"negatifs malformé {brut!r} -> ValueError", False)
        except ValueError:
            check(f"negatifs malformé {brut!r} -> ValueError", True)
    try:
        H.induit({("a", "b")}, {("a", "b")})
        check("exemples contradictoires (positif ET négatif) -> ValueError", False)
    except ValueError:
        check("exemples contradictoires (positif ET négatif) -> ValueError", True)
    # Générateur : matérialisé UNE fois, tous les candidats le voient (plus de perte silencieuse).
    rg = H.induit((c for c in [("a", "b"), ("b", "a")]), {("a", "c")})
    check("positifs GÉNÉRATEUR : symétrie encore validée (plus d'épuisement au 1er candidat)",
          H.SYMETRIE in {t for t, _s, _n in rg["validees"]})

    # ── CÂBLAGE ia.py : induction + orchestrateurs de raisonnement (anti-orphelin) ────────────
    import ia
    ri = ia.induit_regles(anc_pos, anc_neg)
    check("CÂBLAGE ia.induit_regles : transitivité validée pour 'ancêtre'",
          H.TRANSITIVITE in {t for t, _s, _n in ri["validees"]})
    mr = ia.moteur_raisonnement()
    check("CÂBLAGE ia.moteur_raisonnement : instancie un moteur chaîné", hasattr(mr, "observe") and hasattr(mr, "verdict"))
    reg = ia.registre_identite()
    check("CÂBLAGE ia.registre_identite : distinct par défaut (2 labels non fusionnés)",
          reg.enregistre("Alpha") != reg.enregistre("Beta") and not reg.meme("Alpha", "Beta"))
    import ancres
    ba = ia.banque_ancres()
    ba.ajoute("capitale_france", "Paris", "source_A")
    check("CÂBLAGE ia.banque_ancres : source indépendante CONFIRME, même source CIRCULAIRE (anti-auto-corroboration)",
          ba.verifie("capitale_france", "Paris", "source_B") == ancres.CONFIRME
          and ba.verifie("capitale_france", "Paris", "source_A") == ancres.CIRCULAIRE)

    print(f"\n=== valide_induction_horn : {ok}/{ok + len(fails)} ===")
    if fails:
        print("ÉCHECS :", ", ".join(fails))
    return 0 if not fails else 1


if __name__ == "__main__":
    sys.exit(main())
