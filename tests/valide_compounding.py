"""
LA MONTÉE AUTONOME (compounding) — le test le plus informatif du projet.

Question de vision (cf. REPRISE) : le système résout-il, SEUL, des tâches qu'il ne
pouvait PAS au départ, *parce que le passé nourrit le présent* ? On le prouve par une
EXPÉRIENCE A/B contrôlée — la réalité juge, au niveau SYSTÈME, et le test PEUT échouer :

    CONTRÔLE   : montée AVEC rétroaction figée au seed (le registre ne grandit pas).
    TRAITEMENT : montée AVEC rétroaction vive (chaque succès confirmé devient une brique).

Tout le reste est identique : MÊME orchestrateur, MÊME curriculum gradué (servi de
l'extérieur, auto-validé par le curateur), MÊMES seeds. Seul diffère le levier `retroaction`.

Le curriculum (gradué trivial -> stateful), une tâche par étage de la trousse :
  tous_pairs            (1) -> RÉUTILISATION   (déjà au store)
  compte_pairs          (1) -> RECOMBINAISON
  somme_carres_positifs (2) -> FUSION
  deuxieme_plus_grand   (3) -> COMPOSITION     -> VERSÉ comme primitive
  deuxieme_plus_un      (4) -> COMPOSITION PROFONDE = incremente ∘ deuxieme_plus_grand
                               *** HORS DE PORTÉE AU SEED *** (profondeur 3 ; le composeur
                               est de profondeur 2). Atteignable UNIQUEMENT si le palier 3
                               a déposé `deuxieme_plus_grand` -> c'est ICI que vit le compounding.
  factorielle           (5) -> PLI             (reduce(mul, …) ; op du vocabulaire de base)

Seeds (vocabulaire irréductible, déclaré honnêtement) :
  store      : tous_pairs, compte_positifs, somme_carres
  primitives : trie, avant_dernier, incremente
  ops        : mul, max2

Critères de MORT (si l'un tombe, le compounding est réfuté) :
  1. CONTRÔLE        — sans rétroaction, deuxieme_plus_un reste HORS DE PORTÉE.
  2. COMPOUNDING     — avec rétroaction, deuxieme_plus_un est RÉSOLU (par le dépôt du palier 3).
  3. COUVERTURE ↑    — la rétroaction débloque STRICTEMENT plus de tâches que le contrôle.
  4. GÉNÉRALISATION  — chaque succès gardé passe le HELD-OUT (aucun hard-coder versé).
  5. SYSTÈME/ÉTAGES  — l'escalade libre traverse plusieurs étages (composition ET pli atteints).
"""

from __future__ import annotations

import tempfile
from pathlib import Path

from comprehension import Predicteur
from compounding import etages_atteints, franchies, montee
from curateur import CurateurGradue, valide_tache
from generateur import TYPES_RICHES, GenerateurOrchestre
from juge import Limites, juge
from store import Store
from taches import Tache

LIM = Limites(temps_s=3, cpu_s=2)


def _t(fn, arg, tests, held_out, ref_corps, diff):
    """Une tâche de curriculum, avec held-out (généralisation) et réf (auto-validation)."""
    prompt = f'def {fn}({arg}):\n    """..."""'
    ref = f"def {fn}(*args, **kwargs):\n{ref_corps}\n"
    return Tache(id=f"comp/{fn}", point_entree=fn, prompt=prompt, tests=tests,
                 tests_held_out=held_out, solution_ref=ref, difficulte=diff)


# --- Le curriculum gradué ----------------------------------------------------
TACHES = [
    _t("tous_pairs", "xs",
       "def check(c):\n    assert c([2,4]) is True\n    assert c([1,2]) is False\n    assert c([]) is True\ncheck(tous_pairs)",
       "def check(c):\n    assert c([6,8,10]) is True\n    assert c([2,3]) is False\n    assert c([0]) is True\ncheck(tous_pairs)",
       "    return all(x % 2 == 0 for x in args[0])", 1),
    _t("compte_pairs", "xs",
       "def check(c):\n    assert c([1,2,3,4]) == 2\n    assert c([]) == 0\n    assert c([2,4,6]) == 3\ncheck(compte_pairs)",
       "def check(c):\n    assert c([2,4,5,7]) == 2\n    assert c([1,3]) == 0\n    assert c([8]) == 1\ncheck(compte_pairs)",
       "    return sum(1 for x in args[0] if x % 2 == 0)", 1),
    _t("somme_carres_positifs", "xs",
       "def check(c):\n    assert c([1,-2,3]) == 10\n    assert c([-1,-2]) == 0\n    assert c([2]) == 4\ncheck(somme_carres_positifs)",
       "def check(c):\n    assert c([4,-5]) == 16\n    assert c([]) == 0\n    assert c([1,2,-3]) == 5\ncheck(somme_carres_positifs)",
       "    return sum(x * x for x in args[0] if x > 0)", 2),
    _t("deuxieme_plus_grand", "xs",
       "def check(c):\n    assert c([3,1,2]) == 2\n    assert c([5,1,4,2]) == 4\n    assert c([1,2]) == 1\ncheck(deuxieme_plus_grand)",
       "def check(c):\n    assert c([10,20,30]) == 20\n    assert c([9,4,4]) == 4\n    assert c([0,5]) == 0\ncheck(deuxieme_plus_grand)",
       "    return sorted(args[0])[-2]", 3),
    _t("deuxieme_plus_un", "xs",
       "def check(c):\n    assert c([3,1,2]) == 3\n    assert c([5,1,4,2]) == 5\n    assert c([1,2]) == 2\ncheck(deuxieme_plus_un)",
       "def check(c):\n    assert c([10,20,30]) == 21\n    assert c([9,4,4]) == 5\n    assert c([0,5]) == 1\ncheck(deuxieme_plus_un)",
       "    return sorted(args[0])[-2] + 1", 4),
    _t("factorielle", "n",
       "def check(c):\n    assert c(5) == 120\n    assert c(0) == 1\n    assert c(3) == 6\ncheck(factorielle)",
       "def check(c):\n    assert c(4) == 24\n    assert c(1) == 1\n    assert c(6) == 720\ncheck(factorielle)",
       "    r = 1\n    for i in range(1, args[0] + 1):\n        r *= i\n    return r", 5),
]
CIBLE_HORS_PORTEE = "deuxieme_plus_un"

# --- Les seeds (vocabulaire irréductible) ------------------------------------
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
    ("incremente", "def incremente(*args, **kwargs):\n    return args[0] + 1\n"),
]
OPS = [
    ("mul", "def mul(*args, **kwargs):\n    return args[0] * args[1]\n"),
    ("max2", "def max2(*args, **kwargs):\n    return args[0] if args[0] > args[1] else args[1]\n"),
]


def _check(nom, condition):
    print(f"  [{'OK ' if condition else 'RATÉ'}] {nom}")
    return condition


def _store_amorce(d, suffixe):
    """Un store neuf, amorcé des fragments de base (les seeds)."""
    store = Store(Path(d) / f"s_{suffixe}.jsonl")
    for fn, (src, tests) in STORE_SEEDS.items():
        v = juge(src, tests, LIM)
        assert v.passe, f"pré-condition seed store : {fn}"
        store.ajoute(Tache(id=f"seed/{fn}", point_entree=fn,
                           prompt=f'def {fn}(xs):\n    """..."""', tests=tests), src, v)
    return store


def _montee(d, suffixe, retroaction):
    """Une montée complète sur un orchestrateur + store FRAIS (isolation A/B)."""
    store = _store_amorce(d, suffixe)
    predicteur = Predicteur(store, types=TYPES_RICHES)
    orch = GenerateurOrchestre(store, primitives=list(PRIMITIVES), ops=list(OPS),
                               predicteur=predicteur)
    curateur = CurateurGradue(TACHES, seuil=0.7, limites=LIM)
    assert not curateur.rejetees, f"curriculum rejeté : {curateur.rejetees}"
    return montee(orch, curateur, store, limites=LIM, retroaction=retroaction)


def main() -> int:
    resultats = []

    # Garde-fou : le curriculum doit être sain (chaque réf passe ses tests + held-out).
    for tache in TACHES:
        r = valide_tache(tache, n_fuzz=0, limites=LIM)
        assert r.valide, f"tâche bancale {tache.id} : {r.raisons}"

    with tempfile.TemporaryDirectory() as d:
        print("CONTRÔLE — montée SANS rétroaction (le registre reste figé au seed) :")
        j_sans = _montee(d, "sans", retroaction=False)
        for p in j_sans:
            print(p.resume())
        franchies_sans = franchies(j_sans)

        print("\nTRAITEMENT — montée AVEC rétroaction (chaque succès confirmé devient une brique) :")
        j_avec = _montee(d, "avec", retroaction=True)
        for p in j_avec:
            print(p.resume())
        franchies_avec = franchies(j_avec)
        etages = etages_atteints(j_avec)

    print()
    cible = CIBLE_HORS_PORTEE
    toutes = {t.point_entree for t in TACHES}

    # 1. CONTRÔLE : sans rétroaction, la cible reste hors de portée.
    resultats.append(_check(
        f"CONTRÔLE : sans rétroaction, `{cible}` reste HORS DE PORTÉE (le registre n'aide pas)",
        cible not in franchies_sans))

    # 2. COMPOUNDING : avec rétroaction, la cible est résolue grâce au dépôt du palier 3.
    resultats.append(_check(
        f"COMPOUNDING : avec rétroaction, `{cible}` est RÉSOLU (le passé a nourri le présent)",
        cible in franchies_avec))

    # 3. COUVERTURE : la rétroaction débloque STRICTEMENT plus de tâches.
    resultats.append(_check(
        f"COUVERTURE ↑ : rétroaction résout plus ({len(franchies_avec)}) que le contrôle ({len(franchies_sans)})",
        len(franchies_avec) > len(franchies_sans)))

    # 4. GÉNÉRALISATION : toutes les cibles franchies (et chacune a passé le held-out).
    resultats.append(_check(
        f"GÉNÉRALISATION : les {len(toutes)} tâches franchies sur le held-out (aucun hard-coder versé)",
        franchies_avec == toutes))

    # 5. SYSTÈME : l'escalade libre traverse plusieurs étages (composition ET pli inclus).
    resultats.append(_check(
        f"SYSTÈME : escalade libre sur {len(etages)} étages {dict(sorted(etages.items()))}",
        len(etages) >= 3 and "composition" in etages and "pli" in etages))

    print()
    if all(resultats):
        print(f"MONTÉE AUTONOME VALIDÉE — {len(resultats)}/{len(resultats)}. Le système résout SEUL des "
              f"tâches hors de portée au départ PARCE QUE le passé nourrit le présent : un succès confirmé "
              f"devient une brique, les étages hauts grandissent, le compounding est RÉEL — et mesuré par "
              f"une A/B où le contrôle échoue. La vision est visible.")
        return 0
    print(f"ÉCHEC — {sum(resultats)}/{len(resultats)}. Le compounding est réfuté sur ce point : c'est un RÉSULTAT.")
    return 1


if __name__ == "__main__":
    raise SystemExit(main())
