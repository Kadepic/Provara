"""
Validation de G0 — LE PLANCHER (générateur aléatoire).

Ce n'est pas une "brique de capacité", c'est une RÉFÉRENCE : on mesure ce que
donne le pur hasard, sur de vraies tâches. Deux choses à établir :

  1. le PLANCHER est bas — du code aléatoire ne passe presque rien (la mesure
     empirique du mur du démarrage à froid) ;
  2. G0 est STATIQUE — il n'apprend pas, il ne touche pas au store : son taux ne
     bouge pas. C'est la ligne plate que les vrais générateurs devront dépasser.

Le chiffre obtenu ici devient le seuil à battre pour G1 (recombinaison du store).
"""

from __future__ import annotations

from exercices import CATALOGUE
from generateur import GenerateurAleatoire, GenerateurApprenantMulti
from juge import Limites
from mesure import evalue
from taches import HUMANEVAL_0

LIM = Limites(temps_s=3, cpu_s=2)


def _check(nom, condition):
    print(f"  [{'OK ' if condition else 'RATÉ'}] {nom}")
    return condition


def main() -> int:
    resultats = []
    taches = CATALOGUE + [HUMANEVAL_0]
    g0 = GenerateurAleatoire(seed=0)

    print("G0 — le plancher (générateur aléatoire) sur les vraies tâches :\n")
    planchers = []
    for t in taches:
        rv, rg = evalue(g0, t, n_essais=20, limites=LIM)
        planchers.append(rg)
        print(f"  {t.id:<24} réussite={rv:>4.0%}  généralisation={rg:>4.0%}")
    plancher = sum(planchers) / len(planchers)
    print(f"\n  >>> PLANCHER moyen (généralisation) = {plancher:.0%}  "
          f"— le seuil que G1 devra battre.\n")

    # 1. Le plancher est bas (le hasard ne passe ~rien -> mur du démarrage à froid).
    resultats.append(_check("plancher bas : généralisation moyenne < 15%", plancher < 0.15))

    # 2. Candidats bien formés (bon nom de fonction lu dans l'énoncé).
    cands = g0.propose(CATALOGUE[0].prompt, 5)
    resultats.append(_check("produit n candidats au bon nom de fonction",
                            len(cands) == 5 and all("def compte_pairs(" in c for c in cands)))

    # 3. Statique : pas d'apprentissage (contraste avec GenerateurApprenantMulti).
    resultats.append(_check("G0 n'a PAS de méthode apprendre (plancher figé)",
                            not hasattr(g0, "apprendre")))
    resultats.append(_check("(contraste) un générateur apprenant, lui, a apprendre()",
                            hasattr(GenerateurApprenantMulti(CATALOGUE), "apprendre")))

    print()
    if all(resultats):
        print(f"G0 ÉTABLI — {len(resultats)}/{len(resultats)}. Plancher = {plancher:.0%}. "
              f"La barre est posée : à G1 de la franchir, mesuré par la courbe.")
        return 0
    print(f"ÉCHEC — {sum(resultats)}/{len(resultats)}.")
    return 1


if __name__ == "__main__":
    raise SystemExit(main())
