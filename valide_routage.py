"""
AUTO-ROUTAGE DU VERSEMENT — la dernière soudure pour que la clôture tourne EN AUTONOMIE.

`valide_cloture` a prouvé invention->op->multi-entrée, mais en versant l'op `sub` À LA MAIN
(`orch.verse_op`). Ici on enlève la main : dans UNE SEULE session `montee` (inventer=True), le
moteur INVENTE l'op, la ROUTE LUI-MÊME au bon registre (par signature : arité ≥ 2 -> op), et
l'étage MULTI-ENTRÉE compose dessus — `ecart3(a,b,c) = a-b-c = sub(sub(a,b), c)` — sans aucun
versement manuel.

La règle de routage a été TRANCHÉE PAR LA DONNÉE (`recense.py`, 20/20 atomes ; règle enrichie :
arité ≥ 2 -> op ; unaire booléen SUR SCALAIRE -> prédicat ; sinon primitive). L'A/B isole
EXACTEMENT le routage : les deux bras INVENTENT `sub` (même invention) ; seul diffère où il
atterrit.

    CONTRÔLE   (routage=False) : tout succès versé en PRIMITIVE (l'ancien comportement). L'op
                                 inventée n'atteint jamais multi-entrée (qui ne lit que les ops)
                                 -> `ecart3` reste HORS-PORTÉE.
    TRAITEMENT (routage=True)  : `sub` inventé est routé en OP -> multi-entrée compose -> `ecart3`
                                 RÉSOLU, sans une seule ligne de versement manuel.

Critères de MORT (si l'un tombe, l'auto-routage est réfuté) :
  1. ROUTAGE (unité) : la règle range `sub` en 'op', `est_positif` en 'predicat',
     `tous_pairs`/`cube` en 'primitive' — la signature suffit.
  2. CONTRÔLE        : routage naïf (tout->primitive) -> `ecart3` HORS-PORTÉE en session.
  3. CLÔTURE AUTONOME: avec routage -> `ecart3` RÉSOLU à l'étage `multi-entrée`, en UNE session.
  4. INVENTION       : `sub` (sous le nom `soustrais`) est bien minté et franchi par les DEUX bras
                       (l'invention est constante ; seul le routage du versement change).
"""

from __future__ import annotations

import tempfile
from pathlib import Path

from comprehension import Predicteur
from compounding import franchies, montee, route
from curateur import CurateurGradue
from generateur import TYPES_RICHES, GenerateurOrchestre
from juge import Limites, juge
from store import Store
from taches import Tache

LIM = Limites(temps_s=3, cpu_s=2)


def _t(fn, sig, tests, held, ref_corps, diff):
    prompt = f'def {fn}({sig}):\n    """..."""'
    ref = f"def {fn}(*args, **kwargs):\n{ref_corps}\n"
    return Tache(id=f"rt/{fn}", point_entree=fn, prompt=prompt, tests=tests,
                 tests_held_out=held, solution_ref=ref, difficulte=diff)


# --- Le curriculum gradué : inventer une OP, puis composer dessus ------------
TACHES = [
    _t("soustrais", "a, b",
       "def check(c):\n    assert c(5,3) == 2\n    assert c(0,0) == 0\n    assert c(10,4) == 6\ncheck(soustrais)",
       "def check(c):\n    assert c(7,1) == 6\n    assert c(-2,3) == -5\n    assert c(9,9) == 0\ncheck(soustrais)",
       "    return args[0] - args[1]", 1),
    _t("ecart3", "a, b, c",
       "def check(c):\n    assert c(10,3,2) == 5\n    assert c(0,0,0) == 0\n    assert c(5,1,1) == 3\ncheck(ecart3)",
       "def check(c):\n    assert c(20,5,5) == 10\n    assert c(7,2,0) == 5\n    assert c(-1,-1,-1) == 1\ncheck(ecart3)",
       "    return args[0] - args[1] - args[2]", 2),
]
CIBLE = "ecart3"

# Seed : la seule op de base est `add`. `sub` n'est PAS donné — il sera INVENTÉ (mutation de add).
ADD = ("add", "def add(*args, **kwargs):\n    return args[0] + args[1]\n")


def _etage_de(journal, point_entree):
    for p in journal:
        if p.point_entree == point_entree and p.confirme:
            return p.etage
    return None


def _montee(d, suffixe, routage):
    """Une montée FRAÎCHE (orchestrateur + store isolés), inventer=True. Seul `routage` change."""
    store = Store(Path(d) / f"s_{suffixe}.jsonl")
    pred = Predicteur(store, types=TYPES_RICHES)
    orch = GenerateurOrchestre(store, ops=[ADD], predicteur=pred, inventer=True)
    curateur = CurateurGradue(TACHES, seuil=0.7, limites=LIM)
    assert not curateur.rejetees, f"curriculum rejeté : {curateur.rejetees}"
    return montee(orch, curateur, store, limites=LIM, retroaction=True, routage=routage)


def _check(nom, condition):
    print(f"  [{'OK ' if condition else 'RATÉ'}] {nom}")
    return condition


# Atomes-témoins pour la sonde unité (les trois natures + le piège conteneur).
TEMOINS = {
    "op":        "def sub(*args, **kwargs):\n    return args[0] - args[1]\n",
    "predicat":  "def est_positif(*args, **kwargs):\n    return args[0] > 0\n",
    "primitive": "def cube(*args, **kwargs):\n    return args[0] ** 3\n",
    "piège":     "def tous_pairs(*args, **kwargs):\n    return all(x % 2 == 0 for x in args[0])\n",
}


def main() -> int:
    resultats = []

    # 1. ROUTAGE (unité) : la signature range chaque nature au bon registre.
    r_op   = route(TEMOINS["op"], "sub", LIM)
    r_pred = route(TEMOINS["predicat"], "est_positif", LIM)
    r_prim = route(TEMOINS["primitive"], "cube", LIM)
    r_piege = route(TEMOINS["piège"], "tous_pairs", LIM)
    print(f"    routage témoins : sub->{r_op}, est_positif->{r_pred}, cube->{r_prim}, tous_pairs->{r_piege}")
    resultats.append(_check(
        "ROUTAGE : sub->op, est_positif->predicat, cube->primitive, tous_pairs->primitive (bool sur conteneur)",
        r_op == "op" and r_pred == "predicat" and r_prim == "primitive" and r_piege == "primitive"))

    with tempfile.TemporaryDirectory() as d:
        print("\n  CONTRÔLE — montée, routage NAÏF (tout en primitive) :")
        j_sans = _montee(d, "sans", routage=False)
        for p in j_sans:
            print(p.resume())
        franchies_sans = franchies(j_sans)

        print("\n  TRAITEMENT — montée, AUTO-ROUTAGE (sub inventé -> op) :")
        j_avec = _montee(d, "avec", routage=True)
        for p in j_avec:
            print(p.resume())
        franchies_avec = franchies(j_avec)
        etage_cible = _etage_de(j_avec, CIBLE)

    print()

    # 4. INVENTION : `soustrais` minté et franchi par les DEUX bras (invention constante).
    resultats.append(_check(
        "INVENTION : `soustrais` est minté et franchi dans les DEUX bras (seul le routage diffère)",
        "soustrais" in franchies_sans and "soustrais" in franchies_avec))

    # 2. CONTRÔLE : routage naïf -> la cible reste hors de portée (sub parti en primitive).
    resultats.append(_check(
        f"CONTRÔLE : routage naïf (tout->primitive) -> `{CIBLE}` HORS-PORTÉE (l'op n'atteint pas multi-entrée)",
        CIBLE not in franchies_sans))

    # 3. CLÔTURE AUTONOME : avec routage -> cible résolue à multi-entrée, zéro versement manuel.
    resultats.append(_check(
        f"CLÔTURE AUTONOME : auto-routage -> `{CIBLE}` RÉSOLU à l'étage `{etage_cible}` en UNE session",
        CIBLE in franchies_avec and etage_cible == "multi-entrée"))

    print()
    if all(resultats):
        print(f"AUTO-ROUTAGE VALIDÉ — {len(resultats)}/{len(resultats)}. Le moteur INVENTE l'op qui lui manque, "
              f"la ROUTE lui-même au bon registre (par signature, règle tranchée par la donnée), et un étage de "
              f"MÉCANISME compose dessus — dans UNE seule session, SANS aucun versement manuel. La boucle "
              f"invention->registre->mécanisme tourne désormais en pleine autonomie. La dernière soudure est faite.")
        return 0
    print(f"ÉCHEC — {sum(resultats)}/{len(resultats)}. L'auto-routage ne tient pas (encore) : c'est un RÉSULTAT.")
    return 1


if __name__ == "__main__":
    raise SystemExit(main())
