"""
STRESS / PERF ENFER+ du noyau de compréhension — la RÉALITÉ (le juge + son timeout) exige la forme EFFICACE.

Défaut trouvé (audit perf) : les compréhensions filtrées recalculaient l'agrégat À CHAQUE élément
(`if x CMP AGG(args[0])`) -> O(n²). Corrigé en HOISTANT l'agrégat (`_m = AGG ; ... if x CMP _m`) -> O(n).

Ici on PROUVE par le réel, pas par l'affirmation : un held-out GÉANT (n=30000) sous timeout SERRÉ (1 s).
  - une forme O(n²) DÉPASSE le timeout -> rejetée par le juge (le test a des dents) ;
  - le noyau (hoisté) produit une forme O(n) qui PASSE.
Plus : la génération reste BORNÉE même avec beaucoup de primitives (pas d'explosion mémoire/CPU).

Critères de MORT :
  1. DENTS      : la forme O(n²) naïve ÉCHOUE le held-out géant (timeout) — le test discrimine vraiment.
  2. PERF RÉEL  : le noyau résout le composite AVEC le held-out géant (donc il émet la forme O(n)).
  3. BORNÉ      : avec 10 primitives, la génération reste sous un plafond raisonnable (pas d'explosion).
"""

from __future__ import annotations

from generateur import GenerateurComprehensionGenerale
from juge import Limites, juge
from taches import Tache

LIM = Limites(temps_s=1, cpu_s=1)   # timeout SERRÉ : O(n²) sur n=30000 dépasse, O(n) passe largement

CARRE = ("carre", "def carre(*args, **kwargs):\n    return args[0] * args[0]\n")

# held-out GÉANT : la référence est calculée en O(n) DANS le check (agrégat hoisté), donc le check est rapide ;
# seul le CANDIDAT est mis à l'épreuve. Un candidat O(n²) sur n=30000 dépasse le timeout.
HELD_GEANT = ("def check(c):\n"
              "    xs = list(range(30000))\n"
              "    m = sum(xs) / len(xs)\n"
              "    exp = sum(x * x for x in xs if x > m)\n"
              "    assert c(xs) == exp\n"
              "check(somme_carres_au_dessus_moyenne)")
VISIBLE = ("def check(c):\n    assert c([1,2,3,4]) == 25\n    assert c([2,2,2]) == 0\n"
           "    assert c([1,5]) == 25\ncheck(somme_carres_au_dessus_moyenne)")

TACHE = Tache(id="stress/scm", point_entree="somme_carres_au_dessus_moyenne",
              prompt='def somme_carres_au_dessus_moyenne(xs):\n    """..."""',
              tests=VISIBLE, tests_held_out=HELD_GEANT)

NAIVE_ON2 = ("def somme_carres_au_dessus_moyenne(*args, **kwargs):\n"
             "    return sum(x * x for x in args[0] if x > sum(args[0]) / len(args[0]))\n")


def _check(nom, condition):
    print(f"  [{'OK ' if condition else 'RATÉ'}] {nom}")
    return condition


def main() -> int:
    resultats = []

    # 1. DENTS : la forme O(n²) passe le visible mais ÉCHOUE le held-out géant (timeout) -> le test discrimine.
    naive_visible = juge(NAIVE_ON2, VISIBLE, LIM).passe
    naive_geant = juge(NAIVE_ON2, HELD_GEANT, LIM).passe
    resultats.append(_check(f"DENTS : la forme O(n²) passe le visible ({naive_visible}) mais ÉCHOUE le held-out "
                            f"géant ({not naive_geant}) — le test a des dents", naive_visible and not naive_geant))

    # 2. PERF RÉEL : le noyau résout le composite AVEC le held-out géant -> il émet la forme O(n) hoistée.
    sol = None
    for code in GenerateurComprehensionGenerale([CARRE]).propose(TACHE.prompt, 100000):
        if juge(code, TACHE.tests, LIM).passe and juge(code, TACHE.tests_held_out, LIM).passe:
            sol = code
            break
    if sol:
        print(f"    solution -> {sol.strip().splitlines()[-1].strip()}  (agrégat hoisté : {'_m =' in sol})")
    resultats.append(_check("PERF RÉEL : le noyau résout le composite SOUS timeout serré sur n=30000 "
                            "(donc forme O(n) hoistée)", sol is not None and "_m =" in sol))

    # 3. BORNÉ : 10 primitives -> génération sans explosion (plafond raisonnable).
    prims10 = [(f"p{i}", f"def p{i}(*args, **kwargs):\n    return args[0] + {i}\n") for i in range(10)]
    nb = len(GenerateurComprehensionGenerale(prims10).propose(TACHE.prompt, 1000000))
    resultats.append(_check(f"BORNÉ : 10 primitives -> {nb} candidats (plafond raisonnable, pas d'explosion)",
                            nb < 1200))

    print()
    if all(resultats):
        print(f"STRESS NOYAU VALIDÉ — {len(resultats)}/{len(resultats)}. La réalité (timeout du juge) EXIGE la forme "
              f"O(n) : l'agrégat hoisté tient sur n=30000 sous 1 s là où l'O(n²) meurt ; génération bornée même à "
              f"10 primitives. Perf prouvée par le réel, pas affirmée.")
        return 0
    print(f"ÉCHEC — {sum(resultats)}/{len(resultats)}. RÉSULTAT.")
    return 1


if __name__ == "__main__":
    raise SystemExit(main())
