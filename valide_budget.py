"""
BUDGET DE PUISSANCE — le 2e cran (2026-06-17, vision Yohan « dépenser la puissance à hauteur du besoin », par-dessus
`niveau_richesse`). `resoudre(..., budget=N)` borne DURE les appels juge : succès si trouvé sous N, sinon HORS propre.
Motivé par la carte richesse (atteindre une capacité tardive coûte 3000-3500 appels) et le test insoluble (~1888
candidats brûlés sur du sans-solution) : le budget cape le gaspillage SANS jamais rendre de faux.

Critères de MORT (4) :
  1. BORNE RESPECTÉE : budget=50 sur une tâche chère (coin_change ~3481) -> HORS, et appels <= 50 (la borne tient).
  2. HORS PROPRE     : ce HORS rend (None, code=None) -> jamais un faux, jamais un crash (juste « pas dans le budget »).
  3. COUVERTURE      : budget LARGE -> coin_change résolu au MÊME étage et MÊME coût que l'escalade illimitée.
  4. SEUIL           : une tâche cheap (somme_carres, coût 1) reste résolue même budget=2 ; la chère reste HORS à 50
                       mais résolue illimitée -> le budget borne le gaspillage sans casser le faisable bon marché.
"""

from __future__ import annotations

import tempfile
from pathlib import Path

from compounding import resoudre
from diable import _moteur_complet, _seede
from juge import Limites
from store import Store
from taches import Tache

LIM = Limites(temps_s=3, cpu_s=2)
K = 1000

COIN = Tache(id="bud/coin", point_entree="coin_change", prompt='def coin_change(coins, m):\n    """..."""',
             tests="def check(c):\n    assert c([1,2,5],11) == 3\n    assert c([2],3) == -1\ncheck(coin_change)",
             tests_held_out="def check(c):\n    assert c([1,3,4],6) == 2\n    assert c([5],3) == -1\ncheck(coin_change)")
CHEAP = Tache(id="bud/sc", point_entree="somme_carres", prompt='def somme_carres(xs):\n    """..."""',
              tests="def check(c):\n    assert c([1,2,3]) == 14\ncheck(somme_carres)",
              tests_held_out="def check(c):\n    assert c([2,3]) == 13\n    assert c([0]) == 0\ncheck(somme_carres)")


def _check(nom, ok):
    print(f"  [{'OK ' if ok else 'RATÉ'}] {nom}", flush=True)
    return ok


def main() -> int:
    r = []
    with tempfile.TemporaryDirectory() as d:
        store = Store(Path(d) / "s.jsonl")
        _seede(store)
        orch = _moteur_complet(store)

        # Référence : coin_change en escalade ILLIMITÉE.
        e_inf, a_inf, c_inf, _ = resoudre(orch, COIN, LIM, K)

        # 1. BORNE RESPECTÉE : budget=50 -> HORS, appels <= 50.
        e_b, a_b, c_b, _ = resoudre(orch, COIN, LIM, K, budget=50)
        r.append(_check(f"BORNE RESPECTÉE : budget=50 sur coin_change (~{a_inf} illimité) -> {a_b} appels (<=50)",
                        a_b <= 50))

        # 2. HORS PROPRE : rend None, pas de faux code, pas de crash.
        r.append(_check("HORS PROPRE : budget épuisé -> (code=None), jamais un faux candidat", c_b is None))

        # 3. COUVERTURE : budget large -> même étage ET même coût qu'illimité.
        e_l, a_l, c_l, _ = resoudre(orch, COIN, LIM, K, budget=10_000)
        r.append(_check(f"COUVERTURE : budget large -> coin_change résolu à `{e_l}` en {a_l} appels "
                        f"(== illimité `{e_inf}`/{a_inf})", c_l is not None and e_l == e_inf and a_l == a_inf))

        # 4. SEUIL : cheap résolu même budget=2 ; chère HORS à 50 mais résolue illimitée.
        e_c, a_c, c_c, _ = resoudre(orch, CHEAP, LIM, K, budget=2)
        seuil = (c_c is not None) and (c_b is None) and (c_inf is not None)
        r.append(_check(f"SEUIL : somme_carres résolu budget=2 ({a_c} appel) ; coin_change HORS budget=50 mais "
                        f"résolu illimité -> borne le gaspillage sans casser le cheap", seuil))

    print()
    print("BUDGET DE PUISSANCE VALIDÉ — 4/4." if all(r) else f"ÉCHEC — {sum(r)}/4.")
    return 0 if all(r) else 1


if __name__ == "__main__":
    raise SystemExit(main())
