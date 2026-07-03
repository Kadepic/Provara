"""
Validation de la BRIQUE 2 (le store).

Critère de la brique : le coffre des succès vérifiés doit garantir
  1. il n'archive QU'UN succès réellement jugé (via le vrai juge sur HumanEval/0) ;
  2. il DÉ-DUPLIQUE : la même solution ré-ajoutée ne compte pas deux fois ;
  3. il PERSISTE : un nouveau Store sur le même fichier retrouve tout (reprise) ;
  4. il REFUSE un verdict non passant (garde-fou anti-dérive).

Si ces 4 points tiennent, le futur jeu de ré-entraînement ne peut contenir que
du vrai-vérifié, sans doublons, et survit aux redémarrages.
"""

from __future__ import annotations

import tempfile
from pathlib import Path

from juge import juge
from store import Store
from taches import HUMANEVAL_0 as t


def _check(nom: str, condition: bool) -> bool:
    print(f"  [{'OK ' if condition else 'RATÉ'}] {nom}")
    return condition


def main() -> int:
    resultats = []
    with tempfile.TemporaryDirectory() as d:
        chemin = Path(d) / "succes.jsonl"

        # On obtient un VRAI succès en passant par le vrai juge (pas de triche).
        bon = juge(t.solution_ref, t.tests)
        assert bon.passe, "pré-condition : la solution de référence doit passer"

        store = Store(chemin)

        # 1. Archive un succès vérifié.
        ajoute1 = store.ajoute(t, t.solution_ref, bon)
        resultats.append(_check("archive un succès vérifié (renvoie True)", ajoute1 and len(store) == 1))

        # 2. Dé-duplication : même solution -> refusée, taille inchangée.
        ajoute2 = store.ajoute(t, t.solution_ref, bon)
        resultats.append(_check("dé-duplique le même succès (renvoie False)", (not ajoute2) and len(store) == 1))

        # 2b. Une solution DIFFÉRENTE mais valide compte comme un nouveau succès.
        autre = t.prompt + "\n    return any(abs(a-b) < threshold for i,a in enumerate(numbers) for j,b in enumerate(numbers) if i!=j)\n"
        v_autre = juge(autre, t.tests)
        assert v_autre.passe, "pré-condition : la solution alternative doit aussi passer"
        ajoute3 = store.ajoute(t, autre, v_autre)
        resultats.append(_check("archive une autre solution valide (distincte)", ajoute3 and len(store) == 2))

        # 3. Persistance : un nouveau Store sur le même fichier retrouve les 2.
        store2 = Store(chemin)
        resultats.append(_check("persiste et recharge (reprise à chaud)", len(store2) == 2))
        # Et la dé-dup survit au rechargement.
        ajoute4 = store2.ajoute(t, t.solution_ref, bon)
        resultats.append(_check("dé-dup survit au rechargement", (not ajoute4) and len(store2) == 2))

        # 4. Garde-fou : refuse d'archiver un verdict non passant.
        faux = juge(t.prompt + "\n    return False\n", t.tests)
        assert not faux.passe
        try:
            store.ajoute(t, "peu importe", faux)
            resultats.append(_check("refuse un verdict non passant", False))
        except ValueError:
            resultats.append(_check("refuse un verdict non passant (ValueError)", True))

        # Bonus : la vue par tâche est cohérente.
        resultats.append(_check("par_tache() cohérent", store2.par_tache() == {t.id: 2}))

    print()
    if all(resultats):
        print(f"BRIQUE 2 VALIDÉE — {len(resultats)}/{len(resultats)}. Le coffre ne garde que le vrai-vérifié.")
        return 0
    print(f"ÉCHEC — {sum(resultats)}/{len(resultats)}.")
    return 1


if __name__ == "__main__":
    raise SystemExit(main())
