"""
BOUCLE BORNÉE — l'arrêt anticipé, en un schéma figé (la part de contrôle qui restait différée).

Le branchement (`valide_branche`) a levé le contrôle SANS boucle ; restait l'arrêt anticipé (`somme_jusqua_neg`),
que ni le pli (replie sur TOUTE la séquence) ni le ternaire ne font. `GenerateurBoucle` le lève en UN schéma
figé (accumuler-jusqu'à-arrêt) sur op + prédicat CONFIRMÉS — pas de boucle libre, pas d'imbrication.

On exige (A/B falsifiable) :
  1. MUR        : ni pli, ni branchement (ni compose/jointure/multi-entrée) ne résolvent somme_jusqua_neg.
  2. BOUCLE     : le schéma accumuler-jusqu'à-arrêt (add, est_negatif, init 0) le résout.
  3. HONNÊTETÉ  : sans le prédicat d'arrêt `est_negatif`, plus de solution (emploie le confirmé).
  4. ESCALADE   : via l'orchestrateur (ops + predicats), résolu à l'étage `boucle`.
  5. BORNE      : un seul schéma — chaque candidat a exactement UNE boucle `for`, un `break`, aucun `while`.
"""

from __future__ import annotations

import tempfile
from pathlib import Path

from comprehension import Predicteur
from generateur import (TYPES_RICHES, GenerateurBoucle, GenerateurBranche, GenerateurMultiEntree,
                        GenerateurOrchestre, GenerateurPli)
from juge import Limites, juge
from store import Store
from taches import Tache

LIM = Limites(temps_s=3, cpu_s=2)

ADD = ("add", "def add(*args, **kwargs):\n    return args[0] + args[1]\n")
EST_NEGATIF = ("est_negatif", "def est_negatif(*args, **kwargs):\n    return args[0] < 0\n")
EST_POSITIF = ("est_positif", "def est_positif(*args, **kwargs):\n    return args[0] > 0\n")
OPS = [ADD]
PREDICATS = [EST_NEGATIF, EST_POSITIF]

# Held-out adverse : somme jusqu'au PREMIER négatif (exclu). Accumuler-jusqu'à-arrêt.
#   [5,-2,100]->5 (négatif au MILIEU, stop avant 100) ; [7]->7 (singleton sans négatif) ;
#   [1,2,3,4]->10 (ne CASSE jamais, somme totale) ; []->0 ; [-5,9]->0 (négatif en tête) ;
#   [0,1,-1]->1 (0 n'est pas négatif). Tue : sum(xs) brut, sum des positifs (donnerait 105 sur [5,-2,100]),
#   sum après le négatif, oubli du break, etc.
SOMME_JN = Tache(id="bb/somme_jusqua_neg", point_entree="somme_jusqua_neg",
                 prompt='def somme_jusqua_neg(xs):\n    """..."""',
                 tests="def check(c):\n    assert c([1,2,-1,5]) == 3\n    assert c([3,4]) == 7\n    assert c([-1,9]) == 0\n    assert c([]) == 0\ncheck(somme_jusqua_neg)",
                 tests_held_out="def check(c):\n    assert c([5,-2,100]) == 5\n    assert c([7]) == 7\n    assert c([1,2,3,4]) == 10\n    assert c([]) == 0\n    assert c([-5,9]) == 0\n    assert c([0,1,-1]) == 1\ncheck(somme_jusqua_neg)")


def _check(nom, condition):
    print(f"  [{'OK ' if condition else 'RATÉ'}] {nom}")
    return condition


def _resout(generateur, tache, n=600):
    for code in generateur.propose(tache.prompt, n):
        if juge(code, tache.tests, LIM).passe and (not tache.tests_held_out or juge(code, tache.tests_held_out, LIM).passe):
            return code
    return None


def _resout_escalade(orch, tache, k=600):
    for nom_etage, cands in orch.etages(tache.prompt, k):
        for code in cands:
            if juge(code, tache.tests, LIM).passe and (not tache.tests_held_out or juge(code, tache.tests_held_out, LIM).passe):
                return nom_etage
    return None


def main() -> int:
    resultats = []

    # 1. MUR : pli, branchement, multi-entrée ne font pas l'arrêt anticipé.
    mur = (_resout(GenerateurPli(OPS), SOMME_JN) is None
           and _resout(GenerateurBranche(PREDICATS), SOMME_JN) is None
           and _resout(GenerateurMultiEntree(OPS), SOMME_JN) is None)
    resultats.append(_check("MUR : ni pli, ni branchement, ni multi-entrée ne résolvent somme_jusqua_neg", mur))

    # 2. BOUCLE : le schéma accumuler-jusqu'à-arrêt résout.
    g = _resout(GenerateurBoucle(OPS, PREDICATS), SOMME_JN)
    if g:
        print("    boucle ->\n      " + "\n      ".join(g.strip().splitlines()[-5:]))
    resultats.append(_check("BOUCLE : accumuler-jusqu'à-arrêt (add, est_negatif) résout somme_jusqua_neg", g is not None))

    # 3. HONNÊTETÉ : sans le prédicat d'arrêt, plus de solution.
    resultats.append(_check("HONNÊTETÉ : sans `est_negatif`, la boucle ne résout PLUS (emploie le confirmé)",
                            _resout(GenerateurBoucle(OPS, [EST_POSITIF]), SOMME_JN) is None))

    # 4. ESCALADE.
    with tempfile.TemporaryDirectory() as d:
        store = Store(Path(d) / "s.jsonl")
        orch = GenerateurOrchestre(store, ops=OPS, predicats=PREDICATS,
                                   predicteur=Predicteur(store, types=TYPES_RICHES))
        etage = _resout_escalade(orch, SOMME_JN)
    resultats.append(_check(f"ESCALADE : l'orchestrateur résout somme_jusqua_neg à l'étage `{etage}`", etage == "boucle"))

    # 5. BORNE : un seul schéma — une boucle `for`, un `break`, aucun `while`, aucune imbrication.
    cands = GenerateurBoucle(OPS, PREDICATS).propose(SOMME_JN.prompt, 100)
    borne = cands and all(c.count("for ") == 1 and "break" in c and "while" not in c for c in cands)
    resultats.append(_check("BORNE : chaque candidat = UNE boucle for + break, aucun while, aucune imbrication", borne))

    print()
    if all(resultats):
        print(f"BOUCLE BORNÉE VALIDÉE — {len(resultats)}/{len(resultats)}. L'arrêt anticipé est franchi par UN schéma "
              f"figé à slots confirmés — la part de contrôle différée est levée, en périmètre étroit, sans modèle "
              f"externe, jugé par le réel. Le plafond mesuré est entièrement adressé côté mécanisme.")
        return 0
    print(f"ÉCHEC — {sum(resultats)}/{len(resultats)}.")
    return 1


if __name__ == "__main__":
    raise SystemExit(main())
