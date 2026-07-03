"""
Validation de la BRIQUE 9 (la session d'entraînement de bout en bout).

On lance une vraie session sur le curriculum curé, avec UN modèle (factice) qui
s'améliore globalement, et l'observatoire anti-triche branché. On exige :

  1. le curriculum PROGRESSE : on part du niveau 1, on atteint le dernier palier ;
  2. la généralisation MONTE : compétence réelle en hausse (pas juste du visible) ;
  3. le store ne contient QUE du vérifié (tout re-passe le juge) ;
  4. générateur honnête -> l'observatoire ne lève AUCUN incident ;
  5. la session se TERMINE proprement (sommet + généralisation haute).

Si tout tient, le pipeline complet est figé : il ne reste qu'à remplacer la pièce
factice (générateur + apprendre) par un vrai modèle local.
"""

from __future__ import annotations

import tempfile
from pathlib import Path

from curateur import CurateurGradue
from exercices import CATALOGUE
from exploits import Inspecteur
from generateur import GenerateurApprenantMulti
from juge import Limites, juge
from session import session
from store import Store

LIM = Limites(temps_s=4, cpu_s=3)


def _check(nom, condition):
    print(f"  [{'OK ' if condition else 'RATÉ'}] {nom}")
    return condition


def main() -> int:
    resultats = []

    curateur = CurateurGradue(CATALOGUE, seuil=0.7, limites=LIM)
    generateur = GenerateurApprenantMulti(CATALOGUE, competence=0.0, seed=5)
    inspecteur = Inspecteur(limites=LIM)

    with tempfile.TemporaryDirectory() as d:
        store = Store(Path(d) / "succes.jsonl")

        print("Session d'entraînement (curriculum curé, modèle factice qui s'améliore) :\n")
        journal = session(generateur, curateur, store, n=8, max_tours=15,
                          n_eval=10, limites=LIM, inspecteur=inspecteur)
        for e in journal:
            print(e.resume())
        print()

        debut, fin = journal[0], journal[-1]

        # 1. Progression du curriculum.
        resultats.append(_check("démarre au niveau 1", debut.niveau == 1))
        niveau_max = max(t.difficulte for t in CATALOGUE)
        resultats.append(_check(f"atteint le dernier palier (niveau {niveau_max})",
                                curateur.niveau == niveau_max))
        resultats.append(_check("au moins 3 montées de palier",
                                sum(1 for e in journal if e.monte) >= 3))

        # 2. La généralisation monte (apprentissage réel).
        resultats.append(_check(f"généralisation monte ({debut.generalisation:.0%} -> {fin.generalisation:.0%})",
                                fin.generalisation >= debut.generalisation + 0.3))

        # 3. Le store ne contient que du vérifié.
        resultats.append(_check("store non vide", len(store) > 0))
        tout_repasse = all(juge(s.solution, _tests_de(s.tache_id), LIM).passe for s in store)
        resultats.append(_check("intégrité : tout le store re-passe le juge", tout_repasse))

        # 4. Générateur honnête -> aucun incident d'exploit.
        resultats.append(_check("aucun incident anti-triche (générateur honnête)",
                                len(inspecteur.journal) == 0))

        # 5. Fin propre.
        resultats.append(_check("session terminée au sommet, généralisation haute",
                                curateur.fini() and fin.generalisation >= 0.95))

    print()
    if all(resultats):
        print(f"BRIQUE 9 VALIDÉE — {len(resultats)}/{len(resultats)}. "
              f"Pipeline complet figé : curateur + boucle + anti-triche + mesure tournent ensemble.")
        return 0
    print(f"ÉCHEC — {sum(resultats)}/{len(resultats)}.")
    return 1


def _tests_de(tache_id: str) -> str:
    for t in CATALOGUE:
        if t.id == tache_id:
            return t.tests
    raise KeyError(tache_id)


if __name__ == "__main__":
    raise SystemExit(main())
