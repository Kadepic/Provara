"""
Validation de G1 — RÉUTILISATION DU STORE (la mémoire).

Trois promesses falsifiables, mesurées par B7 (evalue), contre le plancher G0 (0%) :

  1. HONNÊTE À FROID : store vide -> G1 n'a rien à réutiliser -> 0% (= plancher).
  2. BAT LE PLANCHER : dès qu'un succès vérifié est au store pour une tâche, G1 le
     réutilise -> ~100% sur cette tâche (vs 0% pour G0).
  3. MONTE AVEC LE STORE : on ajoute les succès tâche par tâche, et la couverture
     moyenne de G1 grimpe de façon MONOTONE (0 -> 25 -> 50 -> 75 -> 100 %). C'est
     « ne jamais réoublier ce qu'on a déjà réussi » : chaque acquis reste acquis.
"""

from __future__ import annotations

import tempfile
from pathlib import Path

from exercices import CATALOGUE
from generateur import GenerateurReutilisateur
from juge import Limites, juge
from mesure import evalue
from store import Store

LIM = Limites(temps_s=3, cpu_s=2)


def _check(nom, condition):
    print(f"  [{'OK ' if condition else 'RATÉ'}] {nom}")
    return condition


def main() -> int:
    resultats = []
    taches = CATALOGUE  # 4 tâches graduées

    with tempfile.TemporaryDirectory() as d:
        store = Store(Path(d) / "succes.jsonl")
        # Mémoire PURE pour la courbe de couverture (mutation à 0 = réutilisation exacte).
        g1 = GenerateurReutilisateur(store, seed=0, p_mutation=0.0)

        # 1. Honnête à froid : store vide -> plancher.
        rv0, rg0 = evalue(g1, taches[0], n_essais=8, limites=LIM)
        resultats.append(_check("store vide -> 0% (honnête sur le démarrage à froid)",
                                rv0 == 0.0 and rg0 == 0.0))

        # 2. Monte avec le store : depuis VIDE, on ajoute un succès vérifié par tour,
        #    et on suit la couverture MOYENNE sur les 4 tâches -> croissance monotone
        #    0 -> 25 -> 50 -> 75 -> 100 %.
        print("\nCouverture moyenne de G1 à mesure que le store se remplit :\n")
        couverture = []
        for k in range(len(taches) + 1):
            gens = [evalue(g1, t, n_essais=6, limites=LIM)[1] for t in taches]
            moy = sum(gens) / len(gens)
            couverture.append(moy)
            print(f"  {k}/{len(taches)} tâche(s) au store -> couverture moyenne = {moy:>4.0%}")
            if k < len(taches):
                vk = juge(taches[k].solution_ref, taches[k].tests, LIM)  # succès vérifié (échafaudage)
                store.ajoute(taches[k], taches[k].solution_ref, vk)

        monotone = all(couverture[i] <= couverture[i + 1] + 1e-9 for i in range(len(couverture) - 1))
        resultats.append(_check("part de 0% (store vide)", couverture[0] == 0.0))
        resultats.append(_check("couverture MONOTONE croissante (rien n'est réoublié)", monotone))
        resultats.append(_check("atteint ~100% une fois le store plein", couverture[-1] >= 0.9))

        # 3. Bat le plancher sur une tâche COUVERTE : ~100% vs 0% pour G0.
        _, gen_couvert = evalue(g1, taches[0], n_essais=8, limites=LIM)
        resultats.append(_check(f"bat le plancher sur une tâche couverte ({gen_couvert:.0%} vs 0%)",
                                gen_couvert >= 0.9))

        # 4. Intégrité : G1 réutilise du vérifié -> ça passe AUSSI le held-out.
        cands = g1.propose(taches[0].prompt, 4)
        ok = all(juge(c, taches[0].tests_held_out, LIM).passe for c in cands)
        resultats.append(_check("réutilise du vérifié -> passe aussi le held-out", ok))

    print()
    if all(resultats):
        print(f"G1 VALIDÉ — {len(resultats)}/{len(resultats)}. Le plancher (0%) est battu par la "
              f"mémoire : G1 monte avec le store, sans rien réoublier.")
        return 0
    print(f"ÉCHEC — {sum(resultats)}/{len(resultats)}.")
    return 1


if __name__ == "__main__":
    raise SystemExit(main())
