"""
Validation de la COMPRÉHENSION (2/2) — la prédiction.

Le prédicteur anticipe le verdict du juge SANS exécuter. On exige :

  1. PRÉCISION QUI MONTE : à mesure que la boîte à concepts grandit (le store), la
     précision de prédiction grimpe — le marqueur d'émergence d'AUTOS.
  2. COMBINAISONS NEUVES : il prédit JUSTE des solutions jamais vues, en combinant
     un squelette connu et un sens connu venus de tâches DIFFÉRENTES -> il comprend.
  3. HONNÊTE : conservateur (l'inconnu -> « non », pas de fausse confiance), et la
     prédiction est toujours MESURÉE contre le juge (jamais crue aveuglément).
"""

from __future__ import annotations

from comprehension import Predicteur
from juge import Limites, juge
from store import Store
from taches import Tache

import tempfile
from pathlib import Path

LIM = Limites(temps_s=3, cpu_s=2)


def _t(id, fn, tests):
    return Tache(id=id, point_entree=fn, prompt=f'def {fn}(xs):\n    """..."""', tests=tests)


# 5 tâches en 2 familles (squelettes 'sum' et 'all'), 3 sens (x%2==0, x>0, x%2==1).
T = {
    "pairs":    _t("c/pairs", "f", "def check(c):\n    assert c([1,2,3,4])==2\n    assert c([])==0\ncheck(f)"),
    "positifs": _t("c/positifs", "f", "def check(c):\n    assert c([1,-2,3])==2\n    assert c([])==0\ncheck(f)"),
    "impairs":  _t("c/impairs", "f", "def check(c):\n    assert c([1,2,3,4])==2\n    assert c([])==0\ncheck(f)"),
    "tpairs":   _t("t/pairs", "f", "def check(c):\n    assert c([2,4]) is True\n    assert c([1,2]) is False\n    assert c([]) is True\ncheck(f)"),
    "tpositifs":_t("t/positifs", "f", "def check(c):\n    assert c([1,2]) is True\n    assert c([-1,2]) is False\n    assert c([]) is True\ncheck(f)"),
}
SOL = {
    "pairs":    "def f(*args, **kwargs):\n    return sum(1 for x in args[0] if x % 2 == 0)\n",
    "positifs": "def f(*args, **kwargs):\n    return sum(1 for x in args[0] if x > 0)\n",
    "impairs":  "def f(*args, **kwargs):\n    return sum(1 for x in args[0] if x % 2 == 1)\n",
    "tpairs":   "def f(*args, **kwargs):\n    return all(x % 2 == 0 for x in args[0])\n",
    "tpositifs":"def f(*args, **kwargs):\n    return all(x > 0 for x in args[0])\n",
}
GARBAGE = "def f(*args, **kwargs):\n    return None\n"


def _check(nom, condition):
    print(f"  [{'OK ' if condition else 'RATÉ'}] {nom}")
    return condition


def _seme(store, cle):
    v = juge(SOL[cle], T[cle].tests, LIM)
    store.ajoute(T[cle], SOL[cle], v)


def main() -> int:
    resultats = []

    # Jeu d'évaluation : les 5 bonnes solutions (vérité=passe) + 5 garbage (vérité=échoue).
    eval_set = [(SOL[k], T[k], True) for k in T] + [(GARBAGE, T[k], False) for k in T]
    # Vérité-terrain, calculée UNE fois par le juge.
    verite = [(cand, t, juge(cand, t.tests, LIM).passe) for cand, t, _ in eval_set]

    def precision(pred):
        bons = sum(1 for cand, t, gt in verite if pred.predit_passe(cand) == gt)
        return bons / len(verite)

    with tempfile.TemporaryDirectory() as d:
        store = Store(Path(d) / "s.jsonl")
        etapes = []   # (description, precision, store_keys)

        # Étape 0 : aucun concept.
        etapes.append(("aucun concept", precision(Predicteur(store))))
        # Étape 1 : un concept de comptage (sum + x%2==0).
        _seme(store, "pairs")
        p1 = Predicteur(store)
        etapes.append(("+ compte_pairs", precision(p1)))
        # Étape 2 : on ajoute 'all + x>0' -> on connaît {sum, all} et {x%2==0, x>0}.
        _seme(store, "tpositifs")
        p2 = Predicteur(store)
        etapes.append(("+ tous_positifs", precision(p2)))
        # Étape 3 : on ajoute le sens 'x%2==1'.
        _seme(store, "impairs")
        p3 = Predicteur(store)
        etapes.append(("+ compte_impairs", precision(p3)))

        print("Précision de prédiction à mesure que la compréhension grandit :\n")
        for desc, prec in etapes:
            print(f"    {desc:<22} -> {prec:>4.0%}")
        print()

        precisions = [p for _, p in etapes]
        # 1. La précision monte (monotone), de 50% (rien) vers 100% (tout compris).
        resultats.append(_check("précision monotone croissante", all(precisions[i] <= precisions[i+1] for i in range(len(precisions)-1))))
        resultats.append(_check("part de 50% (aucun concept)", precisions[0] == 0.5))
        resultats.append(_check("atteint 100% (tout compris)", precisions[-1] == 1.0))

        # 2. Combinaisons NEUVES : à l'étape 2, compte_positifs (sum+x>0) et tous_pairs
        #    (all+x%2==0) sont prédits PASSE sans avoir jamais été au store.
        novel_pos = p2.predit_passe(SOL["positifs"])   # jamais vu compte_positifs
        novel_tp = p2.predit_passe(SOL["tpairs"])       # jamais vu tous_pairs
        resultats.append(_check("prédit JUSTE des combinaisons neuves (compte_positifs, tous_pairs)",
                                novel_pos and novel_tp))

        # 3. Honnête : conservateur sur l'inconnu (le garbage -> toujours 'non').
        conservateur = all(not p3.predit_passe(GARBAGE) for _ in range(1))
        resultats.append(_check("conservateur : le garbage est toujours prédit 'non'", conservateur))
        # Et au début, le sens inconnu 'x%2==1' (compte_impairs) est prédit 'non' (pas de fausse confiance).
        resultats.append(_check("sens encore inconnu -> prédit 'non' (pas de fausse confiance)",
                                not p2.predit_passe(SOL["impairs"])))

    print()
    if all(resultats):
        print(f"COMPRÉHENSION (2/2) VALIDÉE — {len(resultats)}/{len(resultats)}. Le système ANTICIPE le réel "
              f"sans l'exécuter, juste de mieux en mieux, y compris sur du jamais-vu. Il comprend.")
        return 0
    print(f"ÉCHEC — {sum(resultats)}/{len(resultats)}.")
    return 1


if __name__ == "__main__":
    raise SystemExit(main())
