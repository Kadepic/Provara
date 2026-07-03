"""
L'INVENTION DANS LA BOUCLE VIVANTE — le système grimpe ET se crée ses briques, en autonomie.

Jusqu'ici l'invention était validée HORS LIGNE (en pièces). Ici on la branche dans la boucle `montee` :
l'orchestrateur a un DERNIER étage `invention` (opt-in `inventer=True`) qui minte un atome quand toute la
composition a échoué ; la rétroaction de `montee` verse l'atome confirmé au registre. Dans UNE SEULE
session, sur un curriculum gradué, le moteur doit donc :

  P1  cube(x) = x**3          -> aucune composition ne le fait -> il l'INVENTE (mutation de `carre`)
                                 -> l'atome `cube` confirmé (held-out) est versé au registre.
  P2  cube_plus_un(x) = x**3+1 -> devient atteignable par COMPOSITION `incremente ∘ cube`,
                                 *parce que* P1 a inventé et déposé `cube`.

C'est la vision en petit : maîtriser -> se heurter au mur -> INVENTER l'atome manquant -> COMPOSER dessus,
sans qu'on orchestre la séquence à la main. Seul le juge promeut (visible + held-out).

A/B (seul diffère : le dernier étage `invention` est-il actif ?) :
  1. CONTRÔLE         : inventer=False -> cube ET cube_plus_un restent HORS DE PORTÉE (rien à composer).
  2. INVENTION VIVANTE : inventer=True -> cube est résolu à l'étage `invention` et déposé.
  3. COMPOUNDING SUR L'INVENTÉ : dans la MÊME session, cube_plus_un est résolu à l'étage `composition`.
  4. GÉNÉRALISATION   : les deux passent le held-out (aucun atome bidon promu).
"""

from __future__ import annotations

import tempfile
from pathlib import Path

from comprehension import Predicteur
from compounding import montee
from curateur import CurateurGradue
from generateur import TYPES_RICHES, GenerateurOrchestre
from juge import Limites
from store import Store
from taches import Tache

LIM = Limites(temps_s=3, cpu_s=2)

# Matière confirmée du registre : `carre` (à muter en cube) + `incremente` (pour composer) + op mul.
PRIMITIVES = [
    ("carre", "def carre(*args, **kwargs):\n    return args[0] * args[0]\n"),
    ("incremente", "def incremente(*args, **kwargs):\n    return args[0] + 1\n"),
]
OPS = [("mul", "def mul(*args, **kwargs):\n    return args[0] * args[1]\n")]


def _t(fn, tests, held, ref_corps, diff):
    prompt = f'def {fn}(x):\n    """..."""'
    ref = f"def {fn}(*args, **kwargs):\n{ref_corps}\n"
    return Tache(id=f"iv/{fn}", point_entree=fn, prompt=prompt, tests=tests,
                 tests_held_out=held, solution_ref=ref, difficulte=diff)


TACHES = [
    _t("cube",
       "def check(c):\n    assert c(2) == 8\n    assert c(3) == 27\n    assert c(0) == 0\n    assert c(1) == 1\ncheck(cube)",
       "def check(c):\n    assert c(4) == 64\n    assert c(5) == 125\n    assert c(-2) == -8\ncheck(cube)",
       "    return args[0] ** 3", 1),
    _t("cube_plus_un",
       "def check(c):\n    assert c(2) == 9\n    assert c(3) == 28\n    assert c(0) == 1\n    assert c(1) == 2\ncheck(cube_plus_un)",
       "def check(c):\n    assert c(4) == 65\n    assert c(5) == 126\n    assert c(-2) == -7\ncheck(cube_plus_un)",
       "    return args[0] ** 3 + 1", 2),
]


def _check(nom, condition):
    print(f"  [{'OK ' if condition else 'RATÉ'}] {nom}")
    return condition


def _session(d, suffixe, inventer):
    store = Store(Path(d) / f"s_{suffixe}.jsonl")
    orch = GenerateurOrchestre(store, primitives=list(PRIMITIVES), ops=list(OPS),
                               predicteur=Predicteur(store, types=TYPES_RICHES), inventer=inventer)
    curateur = CurateurGradue(TACHES, seuil=0.0, limites=LIM)
    assert not curateur.rejetees, f"curriculum rejeté : {curateur.rejetees}"
    return montee(orch, curateur, store, limites=LIM, retroaction=True)


def main() -> int:
    resultats = []

    with tempfile.TemporaryDirectory() as d:
        print("CONTRÔLE — boucle SANS l'étage invention :")
        sans = _session(d, "sans", inventer=False)
        for p in sans:
            print(p.resume())
        franchies_sans = {p.point_entree for p in sans if p.confirme}

        print("\nINVENTION VIVANTE — boucle AVEC l'étage invention (dernier recours) :")
        avec = _session(d, "avec", inventer=True)
        for p in avec:
            print(p.resume())
        # étage de PREMIÈRE résolution par tâche (la suite est de la réutilisation).
        etage_premier: dict[str, str] = {}
        for p in avec:
            if p.confirme and p.point_entree not in etage_premier:
                etage_premier[p.point_entree] = p.etage
        franchies_avec = set(etage_premier)

    print()
    resultats.append(_check("CONTRÔLE : sans invention, `cube` ET `cube_plus_un` restent HORS DE PORTÉE",
                            not franchies_sans))
    resultats.append(_check(f"INVENTION VIVANTE : `cube` minté SEUL dans la boucle, à l'étage `{etage_premier.get('cube')}`",
                            etage_premier.get("cube") == "invention"))
    resultats.append(_check(f"COMPOUNDING SUR L'INVENTÉ : `cube_plus_un` résolu à l'étage `{etage_premier.get('cube_plus_un')}` "
                            f"(incremente ∘ cube inventé), dans la MÊME session",
                            etage_premier.get("cube_plus_un") == "composition"))
    resultats.append(_check("GÉNÉRALISATION : les 2 tâches franchies sur le held-out (montee confirme avant de verser)",
                            franchies_avec == {"cube", "cube_plus_un"}))

    print()
    if all(resultats):
        print(f"INVENTION VIVANTE VALIDÉE — {len(resultats)}/{len(resultats)}. Dans UNE seule session autonome, le "
              f"système se heurte au mur, INVENTE l'atome manquant (cube), le dépose, et COMPOSE dessus (cube_plus_un) "
              f"— maîtriser→inventer→composer, sans orchestration manuelle, jugé par le réel. La vision tourne en boucle.")
        return 0
    print(f"ÉCHEC — {sum(resultats)}/{len(resultats)}. La boucle vivante ne se ferme pas (encore) : c'est un RÉSULTAT.")
    return 1


if __name__ == "__main__":
    raise SystemExit(main())
