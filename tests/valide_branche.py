"""
BRANCHEMENT — lever le dernier mur du plafond (le CONTRÔLE), en périmètre étroit.

La carte du plafond a isolé un dernier mur de mécanisme : le CONTRÔLE (`signe` exige un branchement, ni
expression unique, ni pli). Décision Yohan : « branchement seul d'abord » — un TERNAIRE `a if pred(x) else b`
(imbriqué une fois) sur des PRÉDICATS CONFIRMÉS, pas de boucle (différée). `GenerateurBranche` le fait.

On exige (A/B falsifiable) :
  1. MUR        : ni composition, ni jointure, ni multi-entrée, ni pli ne résolvent `signe` (pas de contrôle).
  2. BRANCHEMENT: avec les prédicats confirmés (est_positif, est_negatif), le ternaire imbriqué résout signe.
  3. HONNÊTETÉ  : sans le prédicat `est_negatif`, plus de signe (emploie le confirmé, n'invente pas la condition).
  4. ESCALADE   : via l'orchestrateur (predicats fournis), signe est résolu à l'étage `branchement`.
  5. BORNE      : aucune boucle — `GenerateurBranche` ne produit que des ternaires (périmètre étroit tenu).
"""

from __future__ import annotations

import tempfile
from pathlib import Path

from comprehension import Predicteur
from generateur import (TYPES_RICHES, GenerateurBranche, GenerateurCompose, GenerateurJointure,
                        GenerateurMultiEntree, GenerateurOrchestre, GenerateurPli)
from juge import Limites, juge
from store import Store
from taches import Tache

LIM = Limites(temps_s=3, cpu_s=2)

EST_POSITIF = ("est_positif", "def est_positif(*args, **kwargs):\n    return args[0] > 0\n")
EST_NEGATIF = ("est_negatif", "def est_negatif(*args, **kwargs):\n    return args[0] < 0\n")
PREDICATS = [EST_POSITIF, EST_NEGATIF]
OPS = [("add", "def add(*args, **kwargs):\n    return args[0] + args[1]\n"),
       ("max2", "def max2(*args, **kwargs):\n    return args[0] if args[0] > args[1] else args[1]\n")]
PRIMS = [("incremente", "def incremente(*args, **kwargs):\n    return args[0] + 1\n")]


def _t(fn, tests, held=""):
    return Tache(id=f"br/{fn}", point_entree=fn, prompt=f'def {fn}(x):\n    """..."""',
                 tests=tests, tests_held_out=held)


# Held-out adverse : signe(x) = 1 si x>0, -1 si x<0, 0 si x==0.
#   grands positifs/négatifs (100, -100, 999999, -7) + zéro + ±1.
# Tue : identité (renverrait 100), x//abs(x) (crash sur 0), magnitude, ternaire à un seul seuil, etc.
SIGNE = _t("signe",
           "def check(c):\n    assert c(5) == 1\n    assert c(-3) == -1\n    assert c(0) == 0\n    assert c(2) == 1\ncheck(signe)",
           "def check(c):\n    assert c(100) == 1\n    assert c(-100) == -1\n    assert c(0) == 0\n    assert c(1) == 1\n    assert c(-1) == -1\n    assert c(999999) == 1\n    assert c(-7) == -1\ncheck(signe)")


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

    # 1. MUR : aucune voie de composition/pli ne résout signe.
    mur = (_resout(GenerateurCompose(PRIMS), SIGNE) is None
           and _resout(GenerateurJointure(PRIMS, OPS), SIGNE) is None
           and _resout(GenerateurMultiEntree(OPS), SIGNE) is None
           and _resout(GenerateurPli(OPS), SIGNE) is None)
    resultats.append(_check("MUR : ni composition, ni jointure, ni multi-entrée, ni pli ne résolvent signe", mur))

    # 2. BRANCHEMENT : ternaire imbriqué sur prédicats confirmés.
    g = _resout(GenerateurBranche(PREDICATS), SIGNE)
    if g:
        print(f"    branche -> {g.strip().splitlines()[-1].strip()}")
    resultats.append(_check("BRANCHEMENT : le ternaire sur (est_positif, est_negatif) résout signe", g is not None))

    # 3. HONNÊTETÉ : sans est_negatif, plus de signe.
    resultats.append(_check("HONNÊTETÉ : sans le prédicat `est_negatif`, le branchement ne résout PLUS signe",
                            _resout(GenerateurBranche([EST_POSITIF]), SIGNE) is None))

    # 4. ESCALADE : via l'orchestrateur (predicats fournis).
    with tempfile.TemporaryDirectory() as d:
        store = Store(Path(d) / "s.jsonl")
        orch = GenerateurOrchestre(store, primitives=PRIMS, ops=OPS, predicats=PREDICATS,
                                   predicteur=Predicteur(store, types=TYPES_RICHES))
        etage = _resout_escalade(orch, SIGNE)
    resultats.append(_check(f"ESCALADE : l'orchestrateur résout signe à l'étage `{etage}`", etage == "branchement"))

    # 5. BORNE : aucune boucle produite (périmètre étroit) — pas de `for`/`while` dans les candidats.
    sans_boucle = all(("for " not in c and "while " not in c)
                      for c in GenerateurBranche(PREDICATS).propose(SIGNE.prompt, 100))
    resultats.append(_check("BORNE : le branchement ne produit que des ternaires (aucune boucle)", sans_boucle))

    print()
    if all(resultats):
        print(f"BRANCHEMENT VALIDÉ — {len(resultats)}/{len(resultats)}. Le dernier mur du plafond (le CONTRÔLE) "
              f"est levé en périmètre ÉTROIT : un ternaire sur prédicats confirmés résout signe, sans boucle, sans "
              f"modèle externe, jugé par le réel. (La boucle bornée reste différée — brique séparée.)")
        return 0
    print(f"ÉCHEC — {sum(resultats)}/{len(resultats)}.")
    return 1


if __name__ == "__main__":
    raise SystemExit(main())
