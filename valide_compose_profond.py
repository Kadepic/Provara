"""
INDUSTRIALISER LA PROFONDEUR — la composition nidifie au-delà de la profondeur 2 (tours de skills plus hautes).

`valide_compounding_stress` a mesuré un mur : la composition nidifie à profondeur 2 (`p2(p1(x))`) ; une cible à
profondeur 3 D'UN COUP (sans tremplin intermédiaire versé) est HORS-PORTÉE. On industrialise : `GenerateurCompose`
prend une `profondeur` (défaut 2 = historique) et nidifie des chaînes de primitives DISTINCTES de longueur 2..N.

A/B au niveau générateur (mécanisme contre mécanisme) :
    PROFONDEUR 2 (contrôle) : `incremente(double(carre(x)))` = 2x²+1 HORS-PORTÉE (3 profond, pas de tremplin).
    PROFONDEUR 3            : RÉSOLU + GÉNÉRALISE (held-out).

Critères de MORT :
  1. MUR (prof 2)      : la cible 3-profonde n'est PAS atteinte en profondeur 2.
  2. PROFOND (prof 3)  : elle l'est ET généralise (held-out) — vraie composition, pas un fluke.
  3. PORTÉE PRÉSERVÉE  : en profondeur 3, une cible 2-profonde reste résolue (pas de régression de portée).
  4. HONNÊTE          : sans une primitive nécessaire (carre retiré), même en profondeur 3 -> rien (compose
                        des primitives confirmées, ne conjure pas).
  5. VIVANT (modèle)   : l'orchestrateur avec `profondeur_compo=3` résout la cible à l'étage `composition`.
"""

from __future__ import annotations

import tempfile
from pathlib import Path

from comprehension import Predicteur
from generateur import TYPES_RICHES, GenerateurCompose, GenerateurOrchestre
from juge import Limites, juge
from store import Store
from taches import Tache

LIM = Limites(temps_s=3, cpu_s=2)

PRIMS = [("carre", "def carre(*args, **kwargs):\n    return args[0] * args[0]\n"),
         ("double", "def double(*args, **kwargs):\n    return args[0] + args[0]\n"),
         ("incremente", "def incremente(*args, **kwargs):\n    return args[0] + 1\n")]


def _t(fn, tests, held=""):
    return Tache(id=f"cp/{fn}", point_entree=fn, prompt=f'def {fn}(x):\n    """..."""',
                 tests=tests, tests_held_out=held)


# Cible 3-PROFONDE : incremente(double(carre(x))) = 2x² + 1 (3 primitives distinctes en cascade).
CIBLE3 = _t("deux_carres_plus_un",
    "def check(c):\n    assert c(2) == 9\n    assert c(3) == 19\n    assert c(0) == 1\ncheck(deux_carres_plus_un)",
    "def check(c):\n    assert c(4) == 33\n    assert c(5) == 51\n    assert c(-1) == 3\ncheck(deux_carres_plus_un)")
# Cible 2-PROFONDE : double(carre(x)) = 2x² (témoin de non-régression de portée).
CIBLE2 = _t("double_carre",
    "def check(c):\n    assert c(2) == 8\n    assert c(3) == 18\n    assert c(0) == 0\ncheck(double_carre)",
    "def check(c):\n    assert c(4) == 32\n    assert c(-2) == 8\ncheck(double_carre)")


def _check(nom, condition):
    print(f"  [{'OK ' if condition else 'RATÉ'}] {nom}")
    return condition


def _resout(generateur, tache, n=400):
    for code in generateur.propose(tache.prompt, n):
        if juge(code, tache.tests, LIM).passe:
            return code
    return None


def _gen(code, tache):
    return code is not None and juge(code, tache.tests_held_out, LIM).passe


def _etage_resolvant(orch, tache, k=300):
    for nom, cands in orch.etages(tache.prompt, k):
        for code in cands:
            if juge(code, tache.tests, LIM).passe:
                return nom
    return None


def main() -> int:
    resultats = []
    prof2 = GenerateurCompose(PRIMS, profondeur=2)
    prof3 = GenerateurCompose(PRIMS, profondeur=3)

    # 1. MUR : profondeur 2 ne résout pas la cible 3-profonde.
    resultats.append(_check(
        "MUR (prof 2) : `incremente(double(carre(x)))` = 2x²+1 HORS-PORTÉE en profondeur 2",
        _resout(prof2, CIBLE3) is None))

    # 2. PROFOND : profondeur 3 résout + généralise.
    g3 = _resout(prof3, CIBLE3)
    if g3:
        print(f"    profondeur 3 -> {g3.strip().splitlines()[-1].strip()}")
    resultats.append(_check(
        "PROFOND (prof 3) : la cible 3-profonde est RÉSOLUE et passe le HELD-OUT", _gen(g3, CIBLE3)))

    # 3. PORTÉE PRÉSERVÉE : profondeur 3 résout encore une cible 2-profonde.
    resultats.append(_check(
        "PORTÉE PRÉSERVÉE : en profondeur 3, la cible 2-profonde `double(carre(x))` reste résolue",
        _gen(_resout(prof3, CIBLE2), CIBLE2)))

    # 4. HONNÊTE : sans `carre`, même en profondeur 3, rien.
    sans_carre = GenerateurCompose([p for p in PRIMS if p[0] != "carre"], profondeur=3)
    resultats.append(_check(
        "HONNÊTE : sans la primitive `carre`, même en profondeur 3 la cible reste HORS-PORTÉE (ne conjure rien)",
        _resout(sans_carre, CIBLE3) is None))

    # 5. VIVANT : l'orchestrateur avec profondeur_compo=3 résout à l'étage composition.
    with tempfile.TemporaryDirectory() as d:
        store = Store(Path(d) / "s.jsonl")
        orch = GenerateurOrchestre(store, primitives=PRIMS, predicteur=Predicteur(store, types=TYPES_RICHES),
                                   profondeur_compo=3)
        etage = _etage_resolvant(orch, CIBLE3)
    resultats.append(_check(
        f"VIVANT (modèle) : l'orchestrateur (profondeur_compo=3) résout la cible à l'étage `{etage}`",
        etage == "composition"))

    print()
    if all(resultats):
        print(f"PROFONDEUR INDUSTRIALISÉE — {len(resultats)}/{len(resultats)}. La composition nidifie maintenant "
              f"au-delà de 2 (chaînes de primitives distinctes de longueur 2..N) : le moteur franchit en UN coup une "
              f"cible 3-profonde que la profondeur 2 ratait sans tremplin, sans perdre la portée 2, sans conjurer "
              f"(compose des primitives confirmées), et le modèle l'utilise (étage composition). Tours de skills plus "
              f"hautes — capacité du modèle étendue, défaut inchangé (rétrocompatible).")
        return 0
    print(f"ÉCHEC — {sum(resultats)}/{len(resultats)}. La profondeur ne s'industrialise pas (encore) : RÉSULTAT.")
    return 1


if __name__ == "__main__":
    raise SystemExit(main())
