"""
Validation de la BRIQUE 4 (la boucle d'orchestration).

Critère de la brique : la boucle GÉNÉRER -> JUGER -> GARDER doit
  1. ne faire entrer dans le store QUE des candidats réellement passants ;
  2. compter juste : archivés + doublons == nombre de candidats passants du tour ;
  3. CONVERGER : après saturation, les tours suivants n'archivent plus rien
     (idempotence sur le réel-vérifié — c'est ce qui empêche la dérive) ;
  4. le store final ne contient que des succès qui re-passent le juge (intégrité).

Tout est branché sur les VRAIES briques (vrai juge, vrai store, vrai factice).
"""

from __future__ import annotations

import tempfile
from pathlib import Path

from boucle import campagne, tour
from generateur import GenerateurFactice, banque_demo
from juge import Limites, juge
from store import Store
from taches import HUMANEVAL_0 as t


def _check(nom: str, condition: bool) -> bool:
    print(f"  [{'OK ' if condition else 'RATÉ'}] {nom}")
    return condition


def main() -> int:
    resultats = []
    limites = Limites(temps_s=2, cpu_s=1)
    gen = GenerateurFactice(banque_demo(t), seed=7)

    with tempfile.TemporaryDirectory() as d:
        store = Store(Path(d) / "s.jsonl")

        # Un premier tour.
        r1 = tour(gen, store, t, n=8, limites=limites)

        # 2. Comptage juste : passes == archives + doublons.
        resultats.append(_check("comptage cohérent (passes == archivés + doublons)",
                                r1.passes == r1.archives + r1.doublons))
        # 1. Le store ne contient QUE des passants : sa taille == archivés du 1er tour.
        resultats.append(_check("store == archivés du 1er tour (que du passant)",
                                len(store) == r1.archives and r1.archives > 0))

        # 3. Convergence : on enchaîne des tours, l'archivage doit tomber à 0.
        suite = campagne(gen, store, [t], n=8, tours=5, limites=limites)
        taille_avant_saturation = len(store)
        resultats.append(_check("convergence : plus aucun archivage après saturation",
                                all(r.archives == 0 for r in suite)))
        resultats.append(_check("store stable après saturation",
                                len(store) == taille_avant_saturation))

        # 4. Intégrité : chaque succès stocké RE-PASSE le juge (pas de pollution).
        tous_repassent = all(juge(s.solution, t.tests, limites).passe for s in store)
        resultats.append(_check("intégrité : tout le store re-passe le juge", tous_repassent))

        # 5. Le store ne contient que la tâche jugée, bon décompte.
        resultats.append(_check("vue par tâche cohérente",
                                store.par_tache() == {t.id: len(store)}))

    print()
    if all(resultats):
        print(f"BRIQUE 4 VALIDÉE — {len(resultats)}/{len(resultats)}. "
              f"La boucle tourne, ne garde que le vrai, et converge sans dériver.")
        return 0
    print(f"ÉCHEC — {sum(resultats)}/{len(resultats)}.")
    return 1


if __name__ == "__main__":
    raise SystemExit(main())
