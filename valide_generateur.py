"""
Validation de la BRIQUE 3 (le générateur).

Critère de la brique :
  1. le factice respecte le contrat Generateur (typage Protocol) ;
  2. il ne renvoie QUE des candidats du prompt demandé (pas de fuite de tests) ;
  3. il est DÉTERMINISTE (même seed -> même sortie ; seed ≠ -> ordre ≠) ;
  4. la banque de démo couvre bien tous les statuts du juge quand on la passe au
     vrai juge (pass / fail / timeout / error) -> elle exercera la boucle B4.

Si ça tient, on a une source de candidats branchable, et le vrai LLM n'aura qu'à
implémenter la même méthode propose() pour le remplacer.
"""

from __future__ import annotations

from generateur import Generateur, GenerateurFactice, banque_demo
from juge import juge
from taches import HUMANEVAL_0 as t


def _check(nom: str, condition: bool) -> bool:
    print(f"  [{'OK ' if condition else 'RATÉ'}] {nom}")
    return condition


def main() -> int:
    resultats = []
    banque = banque_demo(t)
    gen = GenerateurFactice(banque, seed=42)

    # 1. Respecte le contrat (Protocol runtime-checkable).
    resultats.append(_check("respecte l'interface Generateur", isinstance(gen, Generateur)))

    # 2. propose(n) renvoie n candidats, tous issus du prompt demandé.
    cands = gen.propose(t.prompt, 5)
    resultats.append(_check("propose(n=5) renvoie 5 candidats", len(cands) == 5))
    resultats.append(_check("aucun candidat ne contient les tests cachés",
                            all("check(has_close_elements)" not in c for c in cands)))
    resultats.append(_check("prompt inconnu -> liste vide",
                            gen.propose("prompt jamais vu", 3) == []))

    # 3. Déterminisme.
    a = GenerateurFactice(banque, seed=42).propose(t.prompt, 7)
    b = GenerateurFactice(banque, seed=42).propose(t.prompt, 7)
    c = GenerateurFactice(banque, seed=99).propose(t.prompt, 7)
    resultats.append(_check("même seed -> sortie identique", a == b))
    resultats.append(_check("seed différente -> ordre différent", a != c))

    # 4. La banque couvre tous les statuts du juge (on tire LARGE pour tout voir).
    tous = GenerateurFactice(banque, seed=0).propose(t.prompt, 50)
    statuts = {juge(code, t.tests, limites=_limites_rapides()).statut for code in set(tous)}
    attendus = {"pass", "fail", "timeout", "error"}
    resultats.append(_check(f"la banque couvre {attendus} (vu: {statuts})",
                            attendus <= statuts))

    print()
    if all(resultats):
        print(f"BRIQUE 3 VALIDÉE — {len(resultats)}/{len(resultats)}. Source de candidats branchable et déterministe.")
        return 0
    print(f"ÉCHEC — {sum(resultats)}/{len(resultats)}.")
    return 1


def _limites_rapides():
    # Timeout court pour que la validation (qui inclut une boucle infinie) reste rapide.
    from juge import Limites
    return Limites(temps_s=2, cpu_s=1)


if __name__ == "__main__":
    raise SystemExit(main())
