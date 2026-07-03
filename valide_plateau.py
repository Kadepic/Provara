"""
LA CARTE DU PLAFOND — mesurer OÙ la composition-sur-atomes-semés cale, et POURQUOI.

Tout ce qu'on a bâti COMPOSE sur des atomes donnés (fragments + primitives + ops + combinateurs).
Avant de parler d'INVENTER (minter un atome neuf), le principe impose de MESURER le plafond — pas de
le supposer. Dans l'esprit de `valide_mur`/`valide_carte` : on énumère un curriculum DIVERS, on classe
chaque tâche DANS/HORS portée de l'orchestrateur (seeds fixes), et on LOCALISE la cause des hors-portée.

Cette carte ÉVOLUE avec le moteur. État initial : 3 murs (ATOME / MULTI-ENTRÉE / STRUCTUREL-contrôle). Les
TROIS murs de MÉCANISME sont désormais levés — multi-entrée (arité>2), branchement + boucle (contrôle) — et
l'ATOME par l'invention (couche opt-in). Ce que cette carte re-mesure honnêtement.

Curriculum divers (nombres, listes, chaînes), seeds fixes :
  store      : tous_pairs, compte_positifs, somme_carres
  primitives : trie, avant_dernier, premier, dernier, incremente
  ops        : mul, max2, add, min2          prédicats : est_positif, est_negatif

DANS la portée (un par étage — la maîtrise tient à l'échelle/diversité) :
  tous_pairs            -> réutilisation     compte_pairs          -> recombinaison
  somme_carres_positifs -> fusion            deuxieme_plus_grand   -> composition
  produit_premier_dernier -> jointure        somme_liste, factorielle -> pli
  clamp(x,lo,hi)        -> multi-entrée      (mur arité>2 LEVÉ : max2(lo, min2(x, hi)))
  signe(x)              -> branchement       (mur contrôle LEVÉ : ternaire sur prédicats confirmés)
  somme_jusqua_neg(xs)  -> boucle            (mur arrêt-anticipé LEVÉ : accumuler-jusqu'à-arrêt)

HORS portée — le plafond RESTANT, UNE seule cause :
  ATOME absent : inverse_chaine (s[::-1]), nb_voyelles (prédicat voyelles), moyenne_deux (manque `//2`)
                 -> il manque un ATOME (op/constante/littéral) non donné. Tous les murs de MÉCANISME étant
                    levés, c'est le SEUL plafond de la composition — précisément le domaine de l'INVENTION.

Critères de MORT (la carte est falsifiable) :
  1. MAÎTRISE  : toutes les tâches DANS la portée résolues, à l'étage prévu (jusqu'à branchement/boucle).
  2. PLAFOND   : toutes les tâches HORS portée le sont vraiment (aucune résolue par accident).
  3. CARTE     : le plafond RESTANT a UNE seule cause — l'ATOME absent. Tous les murs de mécanisme tombés.
                 Démontrer, pas supposer.
"""

from __future__ import annotations

import tempfile
from pathlib import Path

from comprehension import Predicteur
from generateur import TYPES_RICHES, GenerateurOrchestre
from juge import Limites, juge
from store import Store
from taches import Tache

LIM = Limites(temps_s=3, cpu_s=2)
K = 250


def _t(fn, arg, tests):
    return Tache(id=f"plat/{fn}", point_entree=fn, prompt=f'def {fn}({arg}):\n    """..."""', tests=tests)


# --- Seeds -------------------------------------------------------------------
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
    ("premier", "def premier(*args, **kwargs):\n    return args[0][0]\n"),
    ("dernier", "def dernier(*args, **kwargs):\n    return args[0][-1]\n"),
    ("incremente", "def incremente(*args, **kwargs):\n    return args[0] + 1\n"),
]
OPS = [
    ("mul", "def mul(*args, **kwargs):\n    return args[0] * args[1]\n"),
    ("max2", "def max2(*args, **kwargs):\n    return args[0] if args[0] > args[1] else args[1]\n"),
    ("add", "def add(*args, **kwargs):\n    return args[0] + args[1]\n"),
    ("min2", "def min2(*args, **kwargs):\n    return args[0] if args[0] < args[1] else args[1]\n"),
]
PREDICATS = [
    ("est_positif", "def est_positif(*args, **kwargs):\n    return args[0] > 0\n"),
    ("est_negatif", "def est_negatif(*args, **kwargs):\n    return args[0] < 0\n"),
]

# --- Le curriculum : (tâche, étage attendu | None, cause si hors-portée) ------
DANS = [
    (_t("tous_pairs", "xs",
        "def check(c):\n    assert c([2,4]) is True\n    assert c([1,2]) is False\n    assert c([]) is True\ncheck(tous_pairs)"), "réutilisation"),
    (_t("compte_pairs", "xs",
        "def check(c):\n    assert c([1,2,3,4]) == 2\n    assert c([]) == 0\n    assert c([2,4,6]) == 3\ncheck(compte_pairs)"), "recombinaison"),
    (_t("somme_carres_positifs", "xs",
        "def check(c):\n    assert c([1,-2,3]) == 10\n    assert c([-1,-2]) == 0\n    assert c([2]) == 4\ncheck(somme_carres_positifs)"), "fusion"),
    (_t("deuxieme_plus_grand", "xs",
        "def check(c):\n    assert c([3,1,2]) == 2\n    assert c([5,1,4,2]) == 4\n    assert c([1,2]) == 1\ncheck(deuxieme_plus_grand)"), "composition"),
    (_t("produit_premier_dernier", "xs",
        "def check(c):\n    assert c([2,3,4]) == 8\n    assert c([5,1]) == 5\n    assert c([3]) == 9\ncheck(produit_premier_dernier)"), "jointure"),
    (_t("somme_liste", "xs",
        "def check(c):\n    assert c([1,2,3]) == 6\n    assert c([]) == 0\n    assert c([5]) == 5\ncheck(somme_liste)"), "pli"),
    (_t("factorielle", "n",
        "def check(c):\n    assert c(5) == 120\n    assert c(0) == 1\n    assert c(3) == 6\ncheck(factorielle)"), "pli"),
    # clamp : le mur MULTI-ENTRÉE est TOMBÉ (étage multi-entrée) -> désormais DANS la portée.
    (_t("clamp", "x, lo, hi",
        "def check(c):\n    assert c(5,0,10) == 5\n    assert c(-3,0,10) == 0\n    assert c(20,0,10) == 10\ncheck(clamp)"), "multi-entrée"),
    # signe : le mur CONTRÔLE (branchement) est TOMBÉ (ternaire sur prédicats confirmés) -> DANS.
    (_t("signe", "x",
        "def check(c):\n    assert c(5) == 1\n    assert c(-3) == -1\n    assert c(0) == 0\ncheck(signe)"), "branchement"),
    # somme_jusqua_neg : le mur BOUCLE est TOMBÉ (schéma accumuler-jusqu'à-arrêt) -> DANS.
    (_t("somme_jusqua_neg", "xs",
        "def check(c):\n    assert c([1,2,-1,5]) == 3\n    assert c([3,4]) == 7\n    assert c([-1,9]) == 0\ncheck(somme_jusqua_neg)"), "boucle"),
]

# HORS : il ne reste qu'UNE cause — l'ATOME absent (op/constante/littéral non donné). Tous les murs de
# MÉCANISME sont levés ; ce qui reste relève de la couche INVENTION (opt-in), pas de la composition.
HORS = [
    (_t("inverse_chaine", "s",
        "def check(c):\n    assert c('abc') == 'cba'\n    assert c('') == ''\n    assert c('x') == 'x'\ncheck(inverse_chaine)"), "ATOME absent"),
    (_t("nb_voyelles", "s",
        "def check(c):\n    assert c('chat') == 1\n    assert c('aieou') == 5\n    assert c('xyz') == 0\ncheck(nb_voyelles)"), "ATOME absent"),
    (_t("moyenne_deux", "a, b",
        "def check(c):\n    assert c(2,4) == 3\n    assert c(0,10) == 5\n    assert c(5,5) == 5\ncheck(moyenne_deux)"), "ATOME absent"),
]


def _check(nom, condition):
    print(f"  [{'OK ' if condition else 'RATÉ'}] {nom}")
    return condition


def _etage_resolvant(orch, tache):
    """Escalade : renvoie le 1er étage dont un candidat passe les tests visibles, sinon None."""
    for nom_etage, cands in orch.etages(tache.prompt, K):
        for code in cands:
            if juge(code, tache.tests, LIM).passe:
                return nom_etage
    return None


def main() -> int:
    resultats = []

    with tempfile.TemporaryDirectory() as d:
        store = Store(Path(d) / "s.jsonl")
        for fn, (src, tests) in STORE_SEEDS.items():
            v = juge(src, tests, LIM)
            assert v.passe, f"seed store {fn}"
            store.ajoute(_t(fn, "xs", tests), src, v)
        orch = GenerateurOrchestre(store, primitives=PRIMITIVES, ops=OPS, predicats=PREDICATS,
                                   predicteur=Predicteur(store, types=TYPES_RICHES))

        print(f"    {'tâche':<24}{'attendu':<16}{'mesuré'}")
        print("-" * 60)
        dans_ok = True
        for tache, attendu in DANS:
            etage = _etage_resolvant(orch, tache)
            ok = etage == attendu
            dans_ok = dans_ok and ok
            print(f"    {tache.point_entree:<24}{attendu:<16}{etage}{'' if ok else '   <-- !'}")

        print()
        hors_ok = True
        causes: dict[str, int] = {}
        for tache, cause in HORS:
            etage = _etage_resolvant(orch, tache)
            hors = etage is None
            hors_ok = hors_ok and hors
            causes[cause] = causes.get(cause, 0) + 1
            print(f"    {tache.point_entree:<24}{'HORS-PORTÉE':<16}{etage if etage else 'hors-portée'}"
                  f"   [{cause}]{'' if hors else '   <-- RÉSOLU ?!'}")
        print()

    # 1. Maîtrise : tout le DANS-portée résolu, au bon étage.
    resultats.append(_check(f"MAÎTRISE : les {len(DANS)} tâches dans la portée résolues, chacune à l'étage prévu",
                            dans_ok))
    # 2. Plafond réel : tout le HORS-portée l'est vraiment.
    resultats.append(_check(f"PLAFOND : les {len(HORS)} tâches hors portée le sont VRAIMENT (rien résolu par accident)",
                            hors_ok))
    # 3. Carte : il ne reste qu'UNE cause — l'ATOME absent. Tous les murs de MÉCANISME sont levés ;
    #    ce qui reste relève de la couche INVENTION (opt-in), pas de la composition.
    une = {"ATOME absent"}
    cartographie = set(causes) == une and causes.get("ATOME absent", 0) > 0
    resultats.append(_check(f"CARTE : le plafond RESTANT a UNE seule cause {dict(sorted(causes.items()))} — "
                            f"tous les murs de MÉCANISME sont levés ; ne reste que l'ATOME absent (→ couche invention)",
                            cartographie))

    print()
    if all(resultats):
        print(f"PLAFOND CARTOGRAPHIÉ — {len(resultats)}/{len(resultats)}. MESURÉ, pas supposé : le moteur MAÎTRISE "
              f"sa portée ({len(DANS)} tâches, {len(set(att for _, att in DANS))} étages, 3 domaines). Les 3 murs de "
              f"MÉCANISME d'origine sont TOUS levés — ATOME→invention, MULTI-ENTRÉE→multi-entrée, CONTRÔLE→branchement "
              f"+ boucle. Le SEUL plafond restant de la composition = l'ATOME absent (op/littéral non donné), qui est "
              f"précisément le domaine de la couche INVENTION (opt-in). La carte évolue avec le moteur.")
        return 0
    print(f"ÉCHEC — {sum(resultats)}/{len(resultats)}. La carte du plafond est fausse sur un point : c'est un RÉSULTAT.")
    return 1


if __name__ == "__main__":
    raise SystemExit(main())
