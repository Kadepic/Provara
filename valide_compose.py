"""
FUSION VERTICALE — 2e étage : SÉQUENÇAGE de primitives appelables (le saut de nature).

L'étage 1 reste dans l'EXPRESSION unique. Ici, un succès confirmé devient une PRIMITIVE
appelable, et on compose par NIDIFICATION : `g(x) = p2(p1(x))`. Ça franchit des pipelines
non réductibles à une compréhension, et — surtout — un composé peut DEVENIR une primitive
(tours de skills), ce qui résout le crédit long horizon (chaînes courtes de briques profondes).

Primitives confirmées (succès sur d'AUTRES tâches) :
  trie           -> sorted(args[0])
  avant_dernier  -> args[0][-2]
  incremente     -> args[0] + 1

On exige :
  1. MUR DU PIPELINE : ni la recombinaison (arité un) ni la fusion d'expressions (étage 1) ne
     résolvent `deuxieme_plus_grand` (= sorted(xs)[-2]) — ce n'est pas une compréhension.
  2. SÉQUENÇAGE RÉSOUT : la composition nidifie avant_dernier∘trie -> sorted(xs)[-2]. Confirmé par le juge.
  3. HONNÊTETÉ : sans la primitive `trie`, la composition ne peut PLUS (elle nidifie du confirmé,
     elle n'invente pas).
  4. TOURS DE SKILLS : `deuxieme_plus_un` (= sorted(xs)[-2] + 1) exige une profondeur 3. Le
     composeur (profondeur 2) ÉCHOUE depuis les primitives brutes — mais RÉUSSIT dès que le
     composé `deuxieme` (lui-même confirmé) est versé dans les primitives : `incremente(deuxieme(x))`.
     Le composé CONTIENT ses parties -> chaîne courte sur une brique profonde.
"""

from __future__ import annotations

import tempfile
from pathlib import Path

from generateur import GenerateurCompose, GenerateurFusion, GenerateurRecombinant, TYPES_RICHES
from juge import Limites, juge
from store import Store
from taches import Tache

LIM = Limites(temps_s=3, cpu_s=2)


def _t(fn, tests):
    return Tache(id=f"comp/{fn}", point_entree=fn, prompt=f'def {fn}(xs):\n    """..."""', tests=tests)


# Primitives confirmées : (nom, source autonome, tests pour pré-valider).
PRIMS = {
    "trie":          ("def trie(*args, **kwargs):\n    return sorted(args[0])\n",
                      "def check(c):\n    assert c([3,1,2]) == [1,2,3]\n    assert c([]) == []\ncheck(trie)"),
    "avant_dernier": ("def avant_dernier(*args, **kwargs):\n    return args[0][-2]\n",
                      "def check(c):\n    assert c([1,2,3]) == 2\n    assert c([5,9]) == 5\ncheck(avant_dernier)"),
    "incremente":    ("def incremente(*args, **kwargs):\n    return args[0] + 1\n",
                      "def check(c):\n    assert c(4) == 5\n    assert c(0) == 1\ncheck(incremente)"),
}

DEUXIEME = _t("deuxieme_plus_grand",
              "def check(c):\n    assert c([3,1,2]) == 2\n    assert c([5,1,4,2]) == 4\n    assert c([1,2]) == 1\ncheck(deuxieme_plus_grand)")
DEUXIEME_PLUS_UN = _t("deuxieme_plus_un",
                      "def check(c):\n    assert c([3,1,2]) == 3\n    assert c([5,1,4,2]) == 5\n    assert c([1,2]) == 2\ncheck(deuxieme_plus_un)")


def _check(nom, condition):
    print(f"  [{'OK ' if condition else 'RATÉ'}] {nom}")
    return condition


def _prevalide():
    for nom, (src, tests) in PRIMS.items():
        assert juge(src, tests, LIM).passe, f"primitive {nom} doit passer"


def _resout(generateur, tache, n=400):
    for code in generateur.propose(tache.prompt, n):
        if juge(code, tache.tests, LIM).passe:
            return code
    return None


def main() -> int:
    _prevalide()
    resultats = []
    raw = [(nom, src) for nom, (src, _) in PRIMS.items()]

    # 1. Le mur du pipeline : recombinaison ET fusion d'expressions échouent.
    with tempfile.TemporaryDirectory() as d:
        store = Store(Path(d) / "s.jsonl")
        for nom, (src, tests) in PRIMS.items():
            store.ajoute(_t(nom, tests), src, juge(src, tests, LIM))
        ni_recomb = _resout(GenerateurRecombinant(store, types=TYPES_RICHES), DEUXIEME) is None
        ni_fusion = _resout(GenerateurFusion(store), DEUXIEME) is None
    resultats.append(_check("MUR : ni recombinaison ni fusion d'expressions ne résolvent sorted(xs)[-2]",
                            ni_recomb and ni_fusion))

    # 2. Séquençage résout par nidification avant_dernier∘trie.
    comp = GenerateurCompose(raw)
    gagnant = _resout(comp, DEUXIEME)
    if gagnant:
        print(f"    composé -> {gagnant.strip().splitlines()[-1].strip()}\n")
    resultats.append(_check("SÉQUENÇAGE : la composition résout deuxieme_plus_grand (avant_dernier ∘ trie)",
                            gagnant is not None))

    # 3. Honnêteté : sans `trie`, la composition ne peut plus.
    sans_trie = [(nom, src) for nom, src in raw if nom != "trie"]
    resultats.append(_check("HONNÊTETÉ : sans la primitive `trie`, la composition ne résout PLUS (nidifie, n'invente pas)",
                            _resout(GenerateurCompose(sans_trie), DEUXIEME) is None))

    # 4. Tours de skills : profondeur 3 inatteignable en profondeur 2... sauf si le composé devient primitive.
    sans_composite = _resout(GenerateurCompose(raw), DEUXIEME_PLUS_UN)   # profondeur 2 sur primitives brutes
    # On VERSE le composé confirmé dans les primitives, sous le nom RÉELLEMENT défini par sa source.
    primitives_plus = raw + [(DEUXIEME.point_entree, gagnant)]
    avec_composite = _resout(GenerateurCompose(primitives_plus), DEUXIEME_PLUS_UN)
    if avec_composite:
        print(f"    tours de skills -> {avec_composite.strip().splitlines()[-1].strip()}  "
              f"(incremente ∘ {DEUXIEME.point_entree}, qui est lui-même un composé)\n")
    resultats.append(_check("TOURS DE SKILLS : deuxieme_plus_un échoue en profondeur 2 brute, RÉUSSIT quand `deuxieme` devient primitive",
                            sans_composite is None and avec_composite is not None))

    print()
    if all(resultats):
        print(f"FUSION VERTICALE (séquençage) VALIDÉE — {len(resultats)}/{len(resultats)}. Un succès confirmé devient "
              f"une PRIMITIVE appelable ; la nidification franchit les pipelines hors-compréhension ; et un composé "
              f"devient lui-même une primitive (tours de skills) — chaînes courtes sur briques profondes, le crédit "
              f"long horizon résolu. Le saut de nature est fait, brique par brique.")
        return 0
    print(f"ÉCHEC — {sum(resultats)}/{len(resultats)}.")
    return 1


if __name__ == "__main__":
    raise SystemExit(main())
