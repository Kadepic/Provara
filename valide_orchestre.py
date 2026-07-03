"""
L'ORCHESTRATEUR — une seule façade sur toute la trousse, en ESCALADE DIRIGÉE.

Première intégration : prouver que les briques forment un SYSTÈME. UN seul générateur
(`GenerateurOrchestre`), un seul store + registre de primitives/ops, résout une tâche par
ÉTAGE — sans qu'on lui dise lequel employer. Il escalade du moins cher au plus cher et
s'arrête au 1er succès ; la direction ordonne dans chaque étage.

Connaissance commune (déposée une fois, réutilisée partout) :
  store      : tous_pairs, compte_positifs, somme_carres   (succès confirmés -> fragments)
  primitives : trie, avant_dernier                          (briques appelables)
  ops        : mul, max2                                    (opérations binaires)

Cinq tâches, une par étage (lower tiers échouent, le bon étage résout) :
  tous_pairs            -> RÉUTILISATION (déjà au store)
  compte_pairs          -> RECOMBINAISON (squelette de compte_positifs + condition de tous_pairs)
  somme_carres_positifs -> FUSION        (élément de somme_carres + filtre de compte_positifs)
  deuxieme_plus_grand   -> COMPOSITION   (avant_dernier ∘ trie)
  factorielle           -> PLI           (reduce(mul, range(1,n+1), 1))

On exige :
  1. SYSTÈME : la même façade résout les 5 (zéro câblage par tâche), via `propose`.
  2. ESCALADE : chaque tâche est résolue au bon étage (le moins cher qui marche).
  3. COÛT CROISSANT : le nombre d'appels au juge croît du plus simple (réutilisation) au plus
     complexe (pli) — « escalade », chiffrée.
"""

from __future__ import annotations

import tempfile
from pathlib import Path

from comprehension import Predicteur
from generateur import GenerateurOrchestre, TYPES_RICHES
from juge import Limites, juge
from store import Store
from taches import Tache

LIM = Limites(temps_s=3, cpu_s=2)


def _t(fn, tests):
    return Tache(id=f"orch/{fn}", point_entree=fn, prompt=f'def {fn}(xs):\n    """..."""', tests=tests)


# --- Connaissance commune ----------------------------------------------------
STORE_SEEDS = {
    "tous_pairs":      ("def tous_pairs(*args, **kwargs):\n    return all(x % 2 == 0 for x in args[0])\n",
                        "def check(c):\n    assert c([2,4]) is True\n    assert c([1,2]) is False\n    assert c([]) is True\ncheck(tous_pairs)"),
    "compte_positifs": ("def compte_positifs(*args, **kwargs):\n    return sum(1 for x in args[0] if x > 0)\n",
                        "def check(c):\n    assert c([1,-2,3]) == 2\n    assert c([]) == 0\ncheck(compte_positifs)"),
    "somme_carres":    ("def somme_carres(*args, **kwargs):\n    return sum(x * x for x in args[0])\n",
                        "def check(c):\n    assert c([1,2,3]) == 14\n    assert c([]) == 0\ncheck(somme_carres)"),
}
PRIMITIVES = [
    ("trie", "def trie(*args, **kwargs):\n    return sorted(args[0])\n"),
    ("avant_dernier", "def avant_dernier(*args, **kwargs):\n    return args[0][-2]\n"),
]
OPS = [
    ("mul", "def mul(*args, **kwargs):\n    return args[0] * args[1]\n"),
    ("max2", "def max2(*args, **kwargs):\n    return args[0] if args[0] > args[1] else args[1]\n"),
]

# --- Les 5 cibles, une par étage ---------------------------------------------
TOUS_PAIRS = _t("tous_pairs",
                "def check(c):\n    assert c([2,4]) is True\n    assert c([1,2]) is False\n    assert c([]) is True\ncheck(tous_pairs)")
COMPTE_PAIRS = _t("compte_pairs",
                  "def check(c):\n    assert c([1,2,3,4]) == 2\n    assert c([]) == 0\n    assert c([2,4,6]) == 3\ncheck(compte_pairs)")
SOMME_CARRES_POS = _t("somme_carres_positifs",
                      "def check(c):\n    assert c([1,-2,3]) == 10\n    assert c([-1,-2]) == 0\n    assert c([2]) == 4\ncheck(somme_carres_positifs)")
DEUXIEME = _t("deuxieme_plus_grand",
              "def check(c):\n    assert c([3,1,2]) == 2\n    assert c([5,1,4,2]) == 4\n    assert c([1,2]) == 1\ncheck(deuxieme_plus_grand)")
FACTORIELLE = _t("factorielle",
                 "def check(c):\n    assert c(5) == 120\n    assert c(0) == 1\n    assert c(3) == 6\ncheck(factorielle)")

CIBLES = [
    (TOUS_PAIRS, "réutilisation"),
    (COMPTE_PAIRS, "recombinaison"),
    (SOMME_CARRES_POS, "fusion"),
    (DEUXIEME, "composition"),
    (FACTORIELLE, "pli"),
]


def _check(nom, condition):
    print(f"  [{'OK ' if condition else 'RATÉ'}] {nom}")
    return condition


def _resout_escalade(orch, tache, k=300):
    """Juge étage par étage (escalade), s'arrête au 1er succès. Renvoie (étage, appels_juge)."""
    appels = 0
    for nom_etage, cands in orch.etages(tache.prompt, k):
        for code in cands:
            appels += 1
            if juge(code, tache.tests, LIM).passe:
                return nom_etage, appels
    return None, appels


def main() -> int:
    resultats = []

    with tempfile.TemporaryDirectory() as d:
        store = Store(Path(d) / "s.jsonl")
        for fn, (src, tests) in STORE_SEEDS.items():
            t = _t(fn, tests)
            v = juge(src, tests, LIM)
            assert v.passe, f"pré-condition store : {fn}"
            store.ajoute(t, src, v)

        predicteur = Predicteur(store, types=TYPES_RICHES)   # direction intra-étage
        orch = GenerateurOrchestre(store, primitives=PRIMITIVES, ops=OPS, predicteur=predicteur)

        print("Une seule façade (GenerateurOrchestre) sur store + primitives + ops :\n")
        print(f"    {'tâche':<22}{'étage attendu':<16}{'étage atteint':<16}{'appels juge'}")
        print("-" * 70)

        etage_ok, systeme_ok, couts = True, True, []
        for tache, attendu in CIBLES:
            etage, appels = _resout_escalade(orch, tache)
            couts.append((tache.point_entree, attendu, etage, appels))
            # fidélité d'interface : la voie propose() (plate) résout aussi.
            par_propose = any(juge(c, tache.tests, LIM).passe for c in orch.propose(tache.prompt, 300))
            systeme_ok = systeme_ok and (etage is not None) and par_propose
            etage_ok = etage_ok and (etage == attendu)
            print(f"    {tache.point_entree:<22}{attendu:<16}{str(etage):<16}{appels}")
        print()

        appels_par_etage = {att: ap for _, att, _, ap in couts}
        # 1. Système : la même façade résout les 5.
        resultats.append(_check("SYSTÈME : une seule façade résout les 5 tâches (zéro câblage par tâche)",
                                systeme_ok))
        # 2. Escalade : chaque tâche au bon (= moins cher) étage.
        resultats.append(_check("ESCALADE : chaque tâche résolue à l'étage attendu (le moins cher qui marche)",
                                etage_ok))
        # 3. Coût croissant : réutilisation << pli.
        croissant = appels_par_etage["réutilisation"] < appels_par_etage["pli"]
        resultats.append(_check(f"COÛT CROISSANT : appels au juge montent du simple au complexe "
                                f"({appels_par_etage['réutilisation']} -> {appels_par_etage['pli']})",
                                croissant))

    print()
    if all(resultats):
        print(f"ORCHESTRATEUR VALIDÉ — {len(resultats)}/{len(resultats)}. Les briques forment un SYSTÈME : une "
              f"seule façade, dirigée et en escalade, résout du trivial au stateful en choisissant elle-même le "
              f"bon mécanisme. Prêt à brancher sur la session pour la MONTÉE autonome (compounding).")
        return 0
    print(f"ÉCHEC — {sum(resultats)}/{len(resultats)}.")
    return 1


if __name__ == "__main__":
    raise SystemExit(main())
