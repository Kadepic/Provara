#!/usr/bin/env python3
"""
VALIDATION des 3 briques STRUCTURELLES promues 🟡→🟢 (2026-07-02) sur le VRAI corpus :
  • graphe_monde.py   — graphe relationnel typé navigable (arêtes réelles, chemins re-vérifiables) ;
  • schema_relations.py — méta-modèle mesuré (cardinalité, irréflexivité, inverse, hiérarchie) ;
  • ontologie.py      — subsomption transitive (est-un) sur taxon_parent, monde ouvert.

FAUX=0 vérifié : aucune arête/subsomption affirmée sans fait réel sous-jacent ; contre-exemples =
verdicts CERTAINS, « compatible » ≠ preuve ; terminaison sur cycles ; entité inconnue -> honnête.
Charge le lecteur (LOURD).
"""
from __future__ import annotations

import sys

# ─── GARDE « BASE COMPLÈTE » (2026-07-12) — SKIP propre sur l'échantillon ───
# Gate de classe BASE RÉELLE (72 M). Sur l'échantillon committé (que _nonreg épingle) sa donnée est
# absente et ses ancres tomberaient en FAUX-échec. Marqueur de base réelle : occupation_personne (2,35 M,
# jamais committé). Base réelle vérifiée par la passe manuelle valide_lecteur* (cf. CHANGELOG). Une gate
# honnête SKIPPE quand sa donnée manque, elle ne tombe pas.
import os as _os, sys as _sys
_bc = _os.environ.get("LECTEUR_DATASETS_DIR")
if _bc and not _os.path.exists(_os.path.join(_bc, "occupation_personne.jsonl")):
    print("=== valide_graphe_typé : SKIP — base complète requise (occupation_personne absent de ce store) ===")
    _sys.exit(0)
# ──────────────────────────────────────────────────────

import lecteur
import graphe_monde as G
import ontologie as O
import schema_relations as S
from base_faits import normalise


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

    L = lecteur.LECTEUR

    # ————————————————— GRAPHE NAVIGABLE —————————————————
    check("GRAPHE : 'france' est une entité du corpus", G.est_entite("france"))
    check("GRAPHE : 'xqzwklmpt' n'est PAS une entité (inconnu honnête)", not G.est_entite("xqzwklmpt"))
    sor = G.sortants("france")
    check("GRAPHE : la France a des arêtes sortantes (capitale/continent/…)", len(sor) >= 5)
    # toute arête sortante correspond à un fait RÉEL (re-lookup) — jamais inventée
    arete_reelle = all(L.cherche(rel, "france") is not None for rel, _v, _a in sor)
    check("GRAPHE FAUX=0 : chaque arête sortante = un fait réel (aucune inventée)", arete_reelle)
    # continent de la France = Europe, et Europe est une entité (arête typée vers entité)
    voi = dict((rel, v) for rel, v, _a in G.voisins("france"))
    check("GRAPHE : voisin typé 'continent'->'europe' (valeur = entité)",
          voi.get("continent") == "europe" and G.est_entite("europe"))

    # ————————————————— CHAÎNE + TERMINAISON —————————————————
    # taxon_parent : chaîne réelle depuis un taxon connu
    tp = L.tables.get("taxon_parent")
    if tp is not None:
        depart = next(iter(tp.keys()))
        ch = G.chaine(depart, "taxon_parent", max_prof=50)
        # chaque maillon i+1 = taxon_parent du maillon i (fait réel)
        maillons_ok = True
        cur = depart
        for v in ch:
            f = tp.get(cur)
            if f is None or normalise(str(f.valeur)) != v:
                maillons_ok = False
                break
            cur = v
        check(f"CHAÎNE : taxon_parent depuis '{depart[:24]}' = {len(ch)} maillons réels", maillons_ok and len(ch) >= 1)
    # terminaison garantie même si on force une profondeur énorme (anti-boucle infinie)
    ch2 = G.chaine(depart if tp is not None else "france", "taxon_parent", max_prof=100000)
    check("CHAÎNE : terminaison garantie sur profondeur énorme (cycle/racine coupés)", isinstance(ch2, list))

    # ————————————————— CHEMIN multi-sauts re-vérifiable —————————————————
    ch_fr = G.chemin("france", "europe", max_sauts=2)
    check("CHEMIN : france ->(continent) europe trouvé", ch_fr is not None and ("continent", "europe") in ch_fr)
    check("CHEMIN FAUX=0 : le chemin trouvé se re-vérifie (arêtes réelles)",
          ch_fr is not None and G.verifie_chemin("france", ch_fr))
    # un chemin FABRIQUÉ (arête fausse) est REJETÉ par la re-vérification
    check("CHEMIN FAUX=0 : un chemin falsifié est rejeté",
          not G.verifie_chemin("france", [("continent", "asie")]))
    check("CHEMIN : cible hors d'atteinte bornée -> None honnête",
          G.chemin("france", "xqzwklmpt-inexistant", max_sauts=2) is None)

    # ————————————————— SCHÉMA (méta-modèle mesuré) —————————————————
    p_cap = S.profil("capitale")
    check("SCHÉMA : profil(capitale) mesuré (fonctionnelle, domaine=pays)",
          p_cap is not None and p_cap.fonctionnelle and "pays" in p_cap.types_domaine)
    check("SCHÉMA : capitale quasi-inversible (valeurs distinctes ~1.0)",
          p_cap is not None and p_cap.frac_valeurs_distinctes >= 0.9)
    p_tp = S.profil("taxon_parent")
    check("SCHÉMA : taxon_parent HIÉRARCHIQUE (valeurs sont des clés) et irréflexive non réfutée",
          p_tp is not None and p_tp.hierarchique >= 0.3 and not p_tp.irreflexive_refutee)
    # code_iso_pays <-> pays_du_code : inverses ? (mesuré ; on n'affirme que si non réfuté)
    hubs = S.relations_hierarchiques(seuil=0.5, min_taille=50)
    check("SCHÉMA : au moins une relation hiérarchique émerge (taxon_parent en tête)",
          any(rel == "taxon_parent" for _t, rel, _h in hubs))

    # ————————————————— ONTOLOGIE (subsomption transitive) —————————————————
    if tp is not None:
        # trouver un taxon dont la chaîne a ≥2 maillons pour tester la transitivité réelle
        cible, anc = None, []
        for k in list(tp.keys())[:500]:
            a = O.ancetres(k, "taxon_parent", 60)
            if len(a) >= 2:
                cible, anc = k, a
                break
        if cible is not None:
            check(f"ONTOLOGIE : est_un('{cible[:20]}', ancêtre lointain) transitif VRAI",
                  O.est_un(cible, anc[-1], "taxon_parent"))
            check("ONTOLOGIE FAUX=0 : est_un vers un non-ancêtre -> False (non dérivable)",
                  not O.est_un(cible, "xqzwklmpt-pas-un-ancetre", "taxon_parent"))
            # plus proche commun : cible et son parent direct -> le parent (ancêtre de cible)
            ppc = O.plus_proche_commun(cible, anc[0], "taxon_parent")
            check("ONTOLOGIE : plus_proche_commun(x, parent(x)) == parent(x)", ppc == anc[0])
    check("ONTOLOGIE FAUX=0 : entité inconnue -> est_un False (monde ouvert honnête)",
          not O.est_un("xqzwklmpt-inconnu", "animalia", "taxon_parent"))
    check("ONTOLOGIE : pas de cycle sur un taxon réel (acyclicité des données saines)",
          tp is None or not O.cycle(next(iter(tp.keys())), "taxon_parent"))

    # ————————————————— CÂBLAGE ia.py (surface additive) —————————————————
    import ia
    voi_ia = dict((rel, v) for rel, v, _a in ia.voisins("france"))
    check("CÂBLAGE ia.voisins : france ->(continent) europe", voi_ia.get("continent") == "europe")
    ch_ia = ia.chemin("france", "europe", max_sauts=2)
    check("CÂBLAGE ia.chemin : france -> europe (arête réelle)",
          ch_ia is not None and ("continent", "europe") in ch_ia)
    if tp is not None and cible is not None:
        check("CÂBLAGE ia.est_un : subsomption transitive VRAIE via ia.py",
              ia.est_un(cible, anc[-1], "taxon_parent"))
    check("CÂBLAGE ia.est_un FAUX=0 : entité inconnue -> False", not ia.est_un("xqzwklmpt", "animalia"))

    print(f"\n=== valide_graphe_typé : {ok}/{ok + len(fails)} ===")
    if fails:
        print("ÉCHECS :", ", ".join(fails))
    return 0 if not fails else 1


if __name__ == "__main__":
    sys.exit(main())
