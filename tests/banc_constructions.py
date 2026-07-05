# -*- coding: utf-8 -*-
"""BANC DE CONSTRUCTIONS APPRISES — l'IA apprend une GRAMMAIRE en dialoguant : une reformulation enseignée sur
UNE entité doit GÉNÉRALISER à d'AUTRES entités jamais vues (construction à trous), tout en gardant FAUX=0 (une
construction apprise ne change JAMAIS l'entité — garde `_alias_change_entite`).

Protocole par cas : on ENSEIGNE (echec sur entité A -> succès canonique sur A), puis on APPLIQUE la construction
sur une entité B DIFFÉRENTE via le pipeline complet, et on vérifie la réponse vérifiée. Dossier d'apprentissage
ISOLÉ (VERAX_PATRONS_DIR temporaire) : aucune pollution, aucun effet sur les patrons réels.

Usage : LECTEUR_DATASETS_DIR=… python3 tests/banc_constructions.py   (base complète ou échantillon)
"""
import os
import sys
import tempfile

os.environ["VERAX_PATRONS_DIR"] = tempfile.mkdtemp()     # isolation AVANT tout import
sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "interface"))
sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "src"))

import apprentissage_patrons as AP     # noqa: E402
import repond as R                     # noqa: E402
import conversation                    # noqa: E402

# (enseignement echec, enseignement succès, application sur entité NEUVE, extrait attendu, refus_motif|None).
# Le refus_motif (si présent) = un motif qui NE DOIT PAS apparaître (garde FAUX=0).
CAS = [
    # construction « chef-lieu » -> « capitale » enseignée sur le Japon, appliquée à l'Espagne/l'Italie
    ("c'est quoi le chef-lieu du Japon ?", "quelle est la capitale du Japon ?",
     "c'est quoi le chef-lieu de l'Espagne ?", "madrid", None),
    ("c'est quoi le chef-lieu du Japon ?", "quelle est la capitale du Japon ?",
     "c'est quoi le chef-lieu de l'Italie ?", "rome", None),
    # construction « la thune » -> « la monnaie » enseignée sur le Japon, appliquée à la Suisse
    ("c'est quoi la thune du Japon ?", "quelle est la monnaie du Japon ?",
     "c'est quoi la thune de la Suisse ?", "franc", None),
]

# GARDE FAUX=0 : une construction NE DOIT PAS pouvoir échanger une entité. Même en enseignant « X du Japon »->
# « Y de la France » (entité changée), l'application ne doit jamais répondre un fait sur une AUTRE entité.
CAS_FAUX = [
    # on tente d'enseigner une substitution qui change l'entité ; le garde doit empêcher tout faux.
    ("population du wakanda", "population de la France",
     "population du mordor", "france", "population de la france"),  # mordor ne doit PAS devenir France
]


def run():
    mem = conversation.MemoireConversation(racine=None)
    ok, echecs = 0, []
    for i, (ens_e, ens_s, appli, attendu, refus) in enumerate(CAS):
        AP.oublie(None)                              # table vierge par cas
        AP.enregistre(ens_e, ens_s)
        rep = R.repond(mem, "constr-%d" % i, appli, pleine=True) or ""
        low = rep.lower()
        good = attendu.lower() in low and (refus is None or refus.lower() not in low)
        if good:
            ok += 1
        else:
            echecs.append(("APPREND %r PUIS %r" % (ens_e, appli), rep.replace("\n", " ")[:80]))
    # garde FAUX=0
    for j, (ens_e, ens_s, appli, jamais, motif) in enumerate(CAS_FAUX):
        AP.oublie(None)
        AP.enregistre(ens_e, ens_s)
        rep = R.repond(mem, "faux-%d" % j, appli, pleine=True) or ""
        if motif.lower() in rep.lower():
            echecs.append(("GARDE FAUX=0 %r" % appli, "A PRODUIT LE FAUX: " + rep.replace("\n", " ")[:70]))
        else:
            ok += 1
    total = len(CAS) + len(CAS_FAUX)
    print("\nCONSTRUCTIONS APPRISES : %d/%d" % (ok, total))
    if echecs:
        print("ÉCHECS :")
        for q, rep in echecs:
            print("  ✗ %s\n      -> %s" % (q, rep))
    return 0 if not echecs else 1


if __name__ == "__main__":
    sys.exit(run())
