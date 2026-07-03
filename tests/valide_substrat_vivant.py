"""
LE SUBSTRAT DANS LA BOUCLE VIVANTE — l'invention par énumération devient un ÉTAGE de l'orchestrateur.

`valide_invention_substrat` a prouvé le mécanisme EN ISOLATION (le générateur minte `s.upper()`). Mais en
conditions réelles — une montée autonome — l'orchestrateur ne l'appelait pas : `majuscule` restait hors-portée.
Ici on CÂBLE `GenerateurSubstrat` comme TOUT DERNIER étage (opt-in `substrat=True`, derrière la mutation), et on
prouve qu'en UNE seule session le moteur invente `majuscule` PUIS compose dessus — comme `invention_vivante` l'a
fait pour la mutation. L'A/B isole exactement le câblage du substrat (`substrat` on/off) ; tout le reste est commun.

    CONTRÔLE   (substrat=False) : `majuscule` (token `.upper` absent) HORS-PORTÉE -> `inverse_majuscule` aussi.
    TRAITEMENT (substrat=True)  : `majuscule` RÉSOLU à l'étage `substrat`, routé primitive, puis
                                  `inverse_majuscule = majuscule(inverse_chaine(s))` RÉSOLU à `composition`.

Critères de MORT :
  1. CONTRÔLE        : sans substrat -> `majuscule` ET `inverse_majuscule` HORS-PORTÉE.
  2. SESSION (mint)  : avec substrat -> `majuscule` RÉSOLU à l'étage `substrat` en montée (pas en isolation).
  3. SESSION (compose): et `inverse_majuscule` RÉSOLU à `composition` (compose sur l'atome inventé) — UNE session.
"""

from __future__ import annotations

import tempfile
from pathlib import Path

from comprehension import Predicteur
from compounding import franchies, montee
from curateur import CurateurGradue
from generateur import TYPES_RICHES, GenerateurOrchestre
from juge import Limites, juge
from store import Store
from taches import Tache

LIM = Limites(temps_s=3, cpu_s=2)


def _t(fn, sig, tests, held, ref_corps, diff):
    return Tache(id=f"sv/{fn}", point_entree=fn, prompt=f'def {fn}({sig}):\n    """..."""',
                 tests=tests, tests_held_out=held,
                 solution_ref=f"def {fn}(*args, **kwargs):\n{ref_corps}\n", difficulte=diff)


# Curriculum : inventer `majuscule` (substrat), PUIS composer dessus avec une primitive seedée.
TACHES = [
    _t("majuscule", "s",
       "def check(c):\n    assert c('abc') == 'ABC'\n    assert c('') == ''\n    assert c('Ab') == 'AB'\ncheck(majuscule)",
       "def check(c):\n    assert c('xyz') == 'XYZ'\n    assert c('hi!') == 'HI!'\ncheck(majuscule)",
       "    return args[0].upper()", 1),
    _t("inverse_majuscule", "s",
       "def check(c):\n    assert c('abc') == 'CBA'\n    assert c('Hi') == 'IH'\n    assert c('') == ''\ncheck(inverse_majuscule)",
       "def check(c):\n    assert c('xy') == 'YX'\n    assert c('aB') == 'BA'\ncheck(inverse_majuscule)",
       "    return args[0][::-1].upper()", 2),
]
CIBLE = "inverse_majuscule"

# Seed : une primitive de renversement (pour composer sur l'inventé `majuscule`).
INVERSE = ("inverse_chaine", "def inverse_chaine(*args, **kwargs):\n    return args[0][::-1]\n")


def _etage_de(journal, point_entree):
    for p in journal:
        if p.point_entree == point_entree and p.confirme:
            return p.etage
    return None


def _montee(d, suffixe, substrat):
    store = Store(Path(d) / f"s_{suffixe}.jsonl")
    pred = Predicteur(store, types=TYPES_RICHES)
    orch = GenerateurOrchestre(store, primitives=[INVERSE], predicteur=pred,
                               inventer=True, substrat=substrat)
    curateur = CurateurGradue(TACHES, seuil=0.7, limites=LIM)
    assert not curateur.rejetees, f"curriculum rejeté : {curateur.rejetees}"
    return montee(orch, curateur, store, limites=LIM, retroaction=True, routage=True)


def _check(nom, condition):
    print(f"  [{'OK ' if condition else 'RATÉ'}] {nom}")
    return condition


def main() -> int:
    resultats = []
    with tempfile.TemporaryDirectory() as d:
        print("  CONTRÔLE — montée SANS substrat câblé :")
        j_sans = _montee(d, "sans", substrat=False)
        for p in j_sans:
            print(p.resume())
        f_sans = franchies(j_sans)

        print("\n  TRAITEMENT — montée AVEC substrat câblé (dernier étage) :")
        j_avec = _montee(d, "avec", substrat=True)
        for p in j_avec:
            print(p.resume())
        f_avec = franchies(j_avec)
        etage_maj = _etage_de(j_avec, "majuscule")
        etage_cible = _etage_de(j_avec, CIBLE)

    print()
    resultats.append(_check(
        "CONTRÔLE : sans substrat câblé -> `majuscule` ET `inverse_majuscule` HORS-PORTÉE (token absent)",
        "majuscule" not in f_sans and CIBLE not in f_sans))
    resultats.append(_check(
        f"SESSION (mint) : avec substrat -> `majuscule` RÉSOLU à l'étage `{etage_maj}` en MONTÉE (pas en isolation)",
        "majuscule" in f_avec and etage_maj == "substrat"))
    resultats.append(_check(
        f"SESSION (compose) : `{CIBLE}` RÉSOLU à l'étage `{etage_cible}` — compose sur l'atome inventé, UNE session",
        CIBLE in f_avec and etage_cible == "composition"))

    print()
    if all(resultats):
        print(f"SUBSTRAT VIVANT VALIDÉ — {len(resultats)}/{len(resultats)}. L'invention par énumération n'est plus sur "
              f"l'établi : c'est un ÉTAGE de l'orchestrateur (dernier recours, derrière la mutation). En conditions "
              f"réelles — une montée autonome — le moteur INVENTE `majuscule` (token `.upper` qu'aucune mutation ne "
              f"crée), le ROUTE en primitive, et COMPOSE dessus (`inverse_majuscule`) — sans main. Le trou « validé mais "
              f"pas branché » est fermé pour le substrat.")
        return 0
    print(f"ÉCHEC — {sum(resultats)}/{len(resultats)}. Le substrat ne s'active pas (encore) dans la boucle : RÉSULTAT.")
    return 1


if __name__ == "__main__":
    raise SystemExit(main())
