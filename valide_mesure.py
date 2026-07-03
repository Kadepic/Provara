"""
Validation de la BRIQUE 7 (le mesureur d'apprentissage).

Deux scénarios, deux exigences :

  A. UN VRAI APPRENANT — sa compétence monte en produisant des solutions qui
     GÉNÉRALISENT. L'instrument doit voir la généralisation grimper -> APPREND.

  B. UN MÉMORISEUR (le piège §2) — sa compétence monte en produisant des
     hard-coders : il passe de mieux en mieux le VISIBLE, mais reste nul sur le
     HELD-OUT. L'instrument doit le DÉMASQUER -> MÉMORISE, pas "apprend".

Si l'instrument réussit ces deux-là, il sait distinguer la compétence réelle de
l'auto-illusion. C'est l'œil dont la vraie boucle (avec GPU) aura besoin.
"""

from __future__ import annotations

from generateur import GenerateurApprenant
from juge import Limites
from mesure import Point, analyse, evalue, trace
from taches import HUMANEVAL_0 as t

P = t.prompt

# Solutions qui GÉNÉRALISENT (passent visible ET held-out).
GENERALISANTES = [
    t.solution_ref,
    P + "\n    return any(abs(a - b) < threshold "
        "for i, a in enumerate(numbers) for j, b in enumerate(numbers) if i != j)\n",
    P + "\n    s = sorted(numbers)\n"
        "    return any(s[k+1] - s[k] < threshold for k in range(len(s) - 1))\n",
]

# Ratés du début (échouent même le visible).
BROUILLONS = [
    P + "\n    return False\n",
    P + "\n    for i in range(len(numbers) - 1):\n"
        "        if abs(numbers[i] - numbers[i+1]) < threshold:\n"
        "            return True\n    return False\n",
]

# Hard-coders : mémorisent les 7 cas VISIBLES -> passent le visible, ratent le held-out.
HARD_CODERS = ['''
from typing import List


def has_close_elements(numbers: List[float], threshold: float) -> bool:
    memo = {
        ((1.0, 2.0, 3.9, 4.0, 5.0, 2.2), 0.3): True,
        ((1.0, 2.0, 3.9, 4.0, 5.0, 2.2), 0.05): False,
        ((1.0, 2.0, 5.9, 4.0, 5.0), 0.95): True,
        ((1.0, 2.0, 5.9, 4.0, 5.0), 0.8): False,
        ((1.0, 2.0, 3.0, 4.0, 5.0, 2.0), 0.1): True,
        ((1.1, 2.2, 3.1, 4.1, 5.1), 1.0): True,
        ((1.1, 2.2, 3.1, 4.1, 5.1), 0.5): False,
    }
    return memo[(tuple(numbers), threshold)]
''']


def _courbe(montantes, tours=6, n_essais=10, delta=0.2, limites=None) -> list[Point]:
    """Fait monter la compétence d'un générateur et relève la courbe à chaque tour."""
    gen = GenerateurApprenant(P, montantes=montantes, brouillons=BROUILLONS,
                              competence=0.0, seed=3)
    courbe = []
    for tour in range(tours):
        rv, rg = evalue(gen, t, n_essais=n_essais, limites=limites)
        courbe.append(Point(tour=tour, essais=n_essais, reussite=rv, generalisation=rg))
        gen.apprendre(delta)   # un tour de "fine-tuning" simulé
    return courbe


def _check(nom, condition):
    print(f"  [{'OK ' if condition else 'RATÉ'}] {nom}")
    return condition


def main() -> int:
    lim = Limites(temps_s=3, cpu_s=2)
    resultats = []

    # --- A. Le vrai apprenant -------------------------------------------------
    print("A. VRAI APPRENANT (produit des solutions qui généralisent) :\n")
    courbe_a = _courbe(GENERALISANTES, limites=lim)
    print(trace(courbe_a))
    diag_a = analyse(courbe_a)
    print(f"\n  -> {diag_a.verdict}")
    print(f"     (gain réussite={diag_a.gain_reussite:+.0%}, gain généralisation={diag_a.gain_generalisation:+.0%})\n")
    resultats.append(_check("apprenant : APPREND détecté", diag_a.apprend))
    resultats.append(_check("apprenant : GÉNÉRALISE détecté", diag_a.generalise))
    resultats.append(_check("apprenant : PAS faux-positif mémorisation", not diag_a.memorise))

    # --- B. Le mémoriseur (le piège) -----------------------------------------
    print("\nB. MÉMORISEUR (produit des hard-coders : passe le visible, pas le held-out) :\n")
    courbe_b = _courbe(HARD_CODERS, limites=lim)
    print(trace(courbe_b))
    diag_b = analyse(courbe_b)
    print(f"\n  -> {diag_b.verdict}")
    print(f"     (gain réussite={diag_b.gain_reussite:+.0%}, gain généralisation={diag_b.gain_generalisation:+.0%})\n")
    resultats.append(_check("mémoriseur : MÉMORISE démasqué", diag_b.memorise))
    resultats.append(_check("mémoriseur : NON crédité de généralisation", not diag_b.generalise))
    resultats.append(_check("mémoriseur : réussite(visible) monte quand même",
                            diag_b.gain_reussite >= 0.15))

    print()
    if all(resultats):
        print(f"BRIQUE 7 VALIDÉE — {len(resultats)}/{len(resultats)}. "
              f"L'instrument voit l'apprentissage RÉEL et démasque l'auto-illusion.")
        return 0
    print(f"ÉCHEC — {sum(resultats)}/{len(resultats)}.")
    return 1


if __name__ == "__main__":
    raise SystemExit(main())
