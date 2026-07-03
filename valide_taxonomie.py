#!/usr/bin/env python3
"""
VALIDATION de taxonomie.py — taxonomie de types dérivée des DONNÉES (FAUX=0).

Charge le lecteur (LOURD) puis vérifie :
  • les ensembles de référence sont non-vides et de taille plausible (lus des tables) ;
  • les SIGNAUX mesurés séparent bien légitime / homonyme avec marge (fraction, densité, source lexicale) ;
  • `population_compatible` rend les verdicts attendus sur les cas de la campagne de mesure 2026-07-02
    (dont les 2 FAUX+ réels corrigés : altitude_localite[soudan], statut_patrimonial[montserrat]) ;
  • AUDIT D'ÉMERGENCE : les registres pivots (pays/éléments/astres) ÉMERGENT du corpus par hub-mining —
    la sélection des ensembles n'est pas arbitraire, elle est une réalité mesurable des données.
"""
from __future__ import annotations

import sys

import taxonomie


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

    ens = taxonomie.ensembles()
    check("ENSEMBLES : pays ≥ 150 (clés de `continent`)", len(ens["pays"]) >= 150)
    check("ENSEMBLES : capitales ≥ 100 (valeurs de `capitale`)", len(ens["capitales"]) >= 100)
    check("ENSEMBLES : villes ≥ 1000 (clés de `pays_ville`)", len(ens["villes"]) >= 1000)
    check("ENSEMBLES : astres 5-20 (clés de `type_planete`)", 5 <= len(ens["astres"]) <= 20)
    check("ENSEMBLES : éléments ≥ 100 (clés de `numero_atomique`)", len(ens["elements"]) >= 100)

    check("TYPES : france -> pays", "pays" in taxonomie.types_de("france"))
    check("TYPES : paris -> capitale et/ou ville",
          set(taxonomie.types_de("paris")) & {"capitales", "villes"})
    check("TYPES : mercure -> astre ET élément",
          {"astres", "elements"} <= set(taxonomie.types_de("mercure")))
    check("TYPES : entité inconnue -> ()", taxonomie.types_de("xqzwklmpt") == ())

    # SIGNAUX (marges mesurées campagne 2026-07-02 ; les seuils sont SEUIL_FRAC=0.5 / SEUIL_DENS=0.3)
    check("FRAC : population de `capitale` homogène pays (≥ 0.8)", taxonomie.frac_ech("capitale", "pays") >= 0.8)
    check("FRAC : population de `numero_atomique` homogène éléments (≥ 0.9)",
          taxonomie.frac_ech("numero_atomique", "elements") >= 0.9)
    check("FRAC : population de `couleur_film` PAS pays (≤ 0.1)", taxonomie.frac_ech("couleur_film", "pays") <= 0.1)
    check("DENSITÉ : altitude_localite couvre les capitales systématiquement (≥ 0.3)",
          taxonomie.densite("altitude_localite", "capitales") >= 0.3)
    check("DENSITÉ : altitude_localite ne couvre PAS les pays (< 0.3 : villages homonymes)",
          taxonomie.densite("altitude_localite", "pays") < 0.3)
    check("DENSITÉ : annee_creation_organisation couvre les pays (≥ 0.3 : les pays SONT des organisations)",
          taxonomie.densite("annee_creation_organisation", "pays") >= 0.3)
    check("DENSITÉ : sexe_personne ne couvre AUCUN registre (< 0.3 partout : collisions)",
          all(taxonomie.densite("sexe_personne", n) < 0.3 for n in ("pays", "capitales", "villes")))
    check("LEXICAL : pluriel est à source lexicale", taxonomie.source_lexicale_rel("pluriel"))
    check("LEXICAL : couleur_film n'est PAS à source lexicale", not taxonomie.source_lexicale_rel("couleur_film"))

    # VERDICTS population_compatible (le remplaçant mesuré de l'ex-liste _HOMONYME_KW)
    check("COMPAT : capitale ~ pays (frac)", taxonomie.population_compatible("capitale", ("pays",)))
    check("COMPAT : couleur_film !~ pays (homonyme Espagne-film)",
          not taxonomie.population_compatible("couleur_film", ("pays",)))
    check("COMPAT : sexe_personne !~ capitales/villes (homonyme Pâris)",
          not taxonomie.population_compatible("sexe_personne", ("capitales", "villes")))
    check("COMPAT : sexe_personne !~ astres (homonyme dieu Mars ; densité 6/8 NEUTRALISÉE par MIN_E)",
          not taxonomie.population_compatible("sexe_personne", ("astres",)))
    check("COMPAT : altitude_localite ~ capitales (altitude de Paris légitime)",
          taxonomie.population_compatible("altitude_localite", ("capitales",)))
    check("COMPAT : altitude_localite !~ pays (FAUX+ réel corrigé : village Soudan 437 m)",
          not taxonomie.population_compatible("altitude_localite", ("pays",)))
    check("COMPAT : statut_patrimonial_structure !~ pays (FAUX+ réel corrigé : structure Montserrat)",
          not taxonomie.population_compatible("statut_patrimonial_structure", ("pays",)))
    check("COMPAT : pays_code_vehicule ~ pays (168 sur-blocks de l'ex-liste corrigés : codes VRAIS)",
          taxonomie.population_compatible("pays_code_vehicule", ("pays",)))
    check("COMPAT : pluriel ~ pays via source lexicale (pluriel de Chypre légitime)",
          taxonomie.population_compatible("pluriel", ("pays",)))
    check("COMPAT : auteur_oeuvre_ecrite !~ astres (auteur de Mercure = roman, abstention)",
          not taxonomie.population_compatible("auteur_oeuvre_ecrite", ("astres",)))

    # AUDIT D'ÉMERGENCE : les registres utilisés émergent du corpus (hub-mining sur les populations).
    hubs = taxonomie.hubs(min_taille=5, max_taille=512, seuil=0.7, min_score=5)
    noms = {rel for (_s, rel, _t) in hubs}
    check(f"HUBS : le registre PAYS émerge des données (continent parmi {len(hubs)} hubs)", "continent" in noms)
    check("HUBS : le registre ÉLÉMENTS émerge des données (numero_atomique)", "numero_atomique" in noms)
    check("HUBS : le registre ASTRES émerge des données (type_planete)", "type_planete" in noms)
    check("HUBS : les populations OUVERTES n'émergent pas (films/personnes hors registres)",
          not any(("film" in rel or "personne" in rel) for (_s, rel, _t) in hubs))

    print(f"\n=== valide_taxonomie : {ok}/{ok + len(fails)} ===")
    if fails:
        print("ÉCHECS :", ", ".join(fails))
    return 0 if not fails else 1


if __name__ == "__main__":
    sys.exit(main())
