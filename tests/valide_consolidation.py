"""
Validation de la CONSOLIDATION : l'utilité évolutive câblée dans la session.

Deux parties :

  A. WIRING + COHÉRENCE — une vraie session, avec la selection branchée, produit
     une « meilleure logique » par tâche : chaque meilleur est un vrai succès
     vérifié (re-passe le juge), il généralise, et le curriculum progresse comme
     avant (B9 préservé). Le store reste le journal brut, la selection la sélection.

  B. ÉVOLUTION DANS LA BOUCLE — quand le générateur produit « de mieux en mieux »,
     la selection SUPPLANTE l'ancienne logique en cours de boucle. La logique
     gardée s'améliore toute seule, à l'intérieur de la session.
"""

from __future__ import annotations

import tempfile
from pathlib import Path

from curateur import CurateurGradue
from exercices import CATALOGUE, COMPTE_PAIRS as CP
from exploits import Inspecteur
from generateur import GenerateurAmeliorant, GenerateurApprenantMulti
from juge import Limites, juge
from session import session
from boucle import tour
from store import Store
from utilite import Selection

LIM = Limites(temps_s=4, cpu_s=3)

VERBEUX = ("def compte_pairs(*args, **kwargs):\n"
           "    total = 0\n"
           "    for x in args[0]:\n"
           "        if x % 2 == 0:\n"
           "            total += 1\n"
           "    return total\n")
CONCIS = "def compte_pairs(*args, **kwargs):\n    return sum(1 for x in args[0] if x % 2 == 0)\n"


def _check(nom, condition):
    print(f"  [{'OK ' if condition else 'RATÉ'}] {nom}")
    return condition


def _tests_de(tache_id):
    return next(t.tests for t in CATALOGUE if t.id == tache_id)


def main() -> int:
    resultats = []

    # --- A. Session complète avec selection branchée -----------------------
    print("A. Session complète, utilité évolutive branchée :\n")
    curateur = CurateurGradue(CATALOGUE, seuil=0.7, limites=LIM)
    gen = GenerateurApprenantMulti(CATALOGUE, competence=0.0, seed=5)
    insp = Inspecteur(limites=LIM)
    sel = Selection(limites=LIM)

    with tempfile.TemporaryDirectory() as d:
        store = Store(Path(d) / "s.jsonl")
        journal = session(gen, curateur, store, n=8, max_tours=15, n_eval=10,
                          limites=LIM, inspecteur=insp, selection=sel)
        for e in journal:
            print(e.resume())
        print()

        populees = [t.id for t in CATALOGUE if sel.meilleur(t.id)]
        resultats.append(_check(f"la selection est peuplée par la session ({len(populees)} tâches)",
                                len(populees) >= 1))
        # Chaque meilleur gardé est un VRAI succès vérifié (re-passe le juge).
        vrais = all(juge(sel.meilleur(tid), _tests_de(tid), LIM).passe for tid in populees)
        resultats.append(_check("chaque meilleur gardé re-passe le juge (vérifié)", vrais))
        # Et il généralise (qualité : pas un hard-coder).
        generalisent = all(sel.utilite(tid).generalise for tid in populees)
        resultats.append(_check("chaque meilleur gardé généralise (qualité)", generalisent))
        # Curriculum préservé : la session a progressé (B9 intact).
        a_progresse = curateur.niveau > 1 or any(e.monte for e in journal)
        resultats.append(_check("curriculum préservé : la session progresse", a_progresse))
        # Selection ⊆ store : la selection est un raffinement du journal brut.
        store_ids = {s.tache_id for s in store}
        resultats.append(_check("selection ⊆ store (raffinement, pas une source parallèle)",
                                set(populees) <= store_ids))

    # --- B. Évolution dans la boucle : supplantation en cours de session ----
    print("\nB. La logique gardée s'améliore DANS la boucle :\n")
    with tempfile.TemporaryDirectory() as d:
        store_b = Store(Path(d) / "b.jsonl")
        sel_b = Selection(limites=LIM)
        gen_b = GenerateurAmeliorant({CP.prompt: [VERBEUX, CONCIS]})

        # Tour 1 : compétence basse -> propose le verbeux.
        tour(gen_b, store_b, CP, n=4, limites=LIM, selection=sel_b)
        best1 = sel_b.meilleur(CP.id)
        gen_b.apprendre()  # le modèle s'améliore
        # Tour 2 : propose le concis -> doit SUPPLANTER.
        tour(gen_b, store_b, CP, n=4, limites=LIM, selection=sel_b)
        best2 = sel_b.meilleur(CP.id)

        print(f"    tour 1 : meilleur = {'verbeux' if best1 == VERBEUX else '?'}")
        print(f"    tour 2 : meilleur = {'concis' if best2 == CONCIS else '?'}  "
              f"(supplantations = {sel_b.supplantations})")
        resultats.append(_check("tour 1 garde le verbeux (seul disponible)", best1 == VERBEUX))
        resultats.append(_check("tour 2 SUPPLANTE par le concis (plus utile)", best2 == CONCIS))
        resultats.append(_check("au moins 1 supplantation dans la boucle", sel_b.supplantations >= 1))

    print()
    if all(resultats):
        print(f"CONSOLIDATION VALIDÉE — {len(resultats)}/{len(resultats)}. La session garde le PLUS "
              f"UTILE, le raffine dans la boucle, et reste révisable. Tout est unifié.")
        return 0
    print(f"ÉCHEC — {sum(resultats)}/{len(resultats)}.")
    return 1


if __name__ == "__main__":
    raise SystemExit(main())
