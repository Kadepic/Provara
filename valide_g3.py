"""
Validation de G3 — ablation de l'échafaudage.

On exige :
  1. l'ablation TROUVE les briques porteuses : exactement le squelette de comptage
     et le remplisseur « x % 2 == 0 » (les seuls qui résolvent compte_pairs) ;
  2. tout le RESTE est superflu (le retirer ne change pas la couverture) ;
  3. l'échafaudage MINIMAL préserve la couverture, avec BEAUCOUP moins de briques ;
  4. retirer une brique porteuse FAIT chuter la couverture (preuve qu'elle portait).

Le chiffre final = la dose minimale d'échafaudage pour bootstraper : mesurée, pas supposée.
"""

from __future__ import annotations

from echafaudage import ablation, briques, couverture, minimal
from exercices import CATALOGUE
from generateur import GenerateurBriques
from juge import Limites
from taches import HUMANEVAL_0

LIM = Limites(temps_s=3, cpu_s=2)
TACHES = CATALOGUE + [HUMANEVAL_0]

PORTEUSES_ATTENDUES = {
    ("sq", None, "return sum(1 for x in args[0] if {P})"),
    ("rmp", "P", "x % 2 == 0"),
}


def _check(nom, condition):
    print(f"  [{'OK ' if condition else 'RATÉ'}] {nom}")
    return condition


def main() -> int:
    resultats = []
    g_plein = GenerateurBriques()
    base = couverture(g_plein.squelettes, g_plein.remplisseurs, TACHES, LIM)
    n_briques = len(briques(g_plein.squelettes, g_plein.remplisseurs))
    print(f"Bibliothèque pleine : {n_briques} briques, couverture = {sorted(base)}\n")

    # 1-2. Ablation : qui est porteur, qui est superflu ?
    rapport = ablation(TACHES, LIM)
    porteuses = {b for (b, porteuse, _) in rapport if porteuse}
    print("Briques PORTEUSES trouvées :")
    for b in sorted(porteuses):
        print(f"    {b}")
    n_superflues = sum(1 for (_, porteuse, _) in rapport if not porteuse)

    resultats.append(_check("les porteuses sont exactement les 2 attendues",
                            porteuses == PORTEUSES_ATTENDUES))
    resultats.append(_check(f"tout le reste est superflu ({n_superflues}/{n_briques})",
                            n_superflues == n_briques - 2))

    # 4. Retirer une porteuse fait chuter la couverture.
    from echafaudage import retire
    b_porteuse = ("rmp", "P", "x % 2 == 0")
    sq, rmp = retire(g_plein.squelettes, g_plein.remplisseurs, b_porteuse)
    cov_sans = couverture(sq, rmp, TACHES, LIM)
    resultats.append(_check(f"sans « x%2==0 » -> couverture chute ({sorted(base)} -> {sorted(cov_sans)})",
                            cov_sans != base and len(cov_sans) < len(base)))

    # 3. Échafaudage minimal : même couverture, beaucoup moins de briques.
    sq_min, rmp_min = minimal(TACHES, LIM)
    cov_min = couverture(sq_min, rmp_min, TACHES, LIM)
    n_min = len(briques(sq_min, rmp_min))
    print(f"\nÉchafaudage MINIMAL : {n_min} brique(s), couverture = {sorted(cov_min)}")
    resultats.append(_check("minimal préserve la couverture", cov_min == base))
    resultats.append(_check(f"minimal bien plus petit ({n_min} vs {n_briques} briques)",
                            n_min <= 2))

    print()
    if all(resultats):
        print(f"G3 VALIDÉ — {len(resultats)}/{len(resultats)}. Dose minimale d'échafaudage = "
              f"{n_min} brique(s) sur {n_briques} pour bootstraper. Mesuré, pas supposé.")
        return 0
    print(f"ÉCHEC — {sum(resultats)}/{len(resultats)}.")
    return 1


if __name__ == "__main__":
    raise SystemExit(main())
