"""
G4 — QUANTIFIER LE MUR : l'échafaudage transfère-t-il d'une tâche à l'autre ?

On prend une bibliothèque ciblée couvrant 3 tâches hétérogènes, et on mesure, par
tâche, ses briques PORTEUSES (celles dont l'absence casse SA résolution). Puis on
regarde le PARTAGE entre tâches :

  - les SQUELETTES (la structure : « return {STR} ») peuvent être partagés ;
  - les REMPLISSEURS (la LOGIQUE propre à la tâche) le sont-ils ?

Thèse falsifiable : la logique NE transfère PAS — chaque tâche réclame son propre
remplisseur porteur (coût linéaire, 1 brique de logique par tâche). Seule la
structure générique s'amortit un peu. C'est *pourquoi*, au-delà, un modèle appris
(qui capture la logique, pas que la structure) devient nécessaire.
"""

from __future__ import annotations

from echafaudage import ablation, couverture
from exercices import COMPTE_PAIRS, ECHAPPE_HTML, INVERSER_MOTS
from juge import Limites

LIM = Limites(temps_s=3, cpu_s=2)
TACHES = [COMPTE_PAIRS, INVERSER_MOTS, ECHAPPE_HTML]

# Bibliothèque ciblée : 2 squelettes (structure), 6 remplisseurs (dont la logique).
SQUELETTES = [
    ("return sum(1 for x in args[0] if {P})", "P"),
    ("return {STR}", "STR"),
]
REMPLISSEURS = {
    "P": ["x % 2 == 0", "x % 2 == 1", "x > 0"],                      # seul x%2==0 résout compte_pairs
    "STR": [
        "' '.join(args[0].split(' ')[::-1])",                        # logique inverser_mots
        "args[0].replace('&', '&amp;').replace('<', '&lt;').replace('>', '&gt;')",  # logique echappe_html
        "args[0]",                                                   # distracteur (ne résout rien)
    ],
}


def _check(nom, condition):
    print(f"  [{'OK ' if condition else 'RATÉ'}] {nom}")
    return condition


def main() -> int:
    resultats = []

    base = couverture(SQUELETTES, REMPLISSEURS, TACHES, LIM)
    resultats_couv = base == {t.id for t in TACHES}
    print(f"Couverture de la bibliothèque ciblée : {sorted(base)}\n")
    resultats.append(_check("la bibliothèque couvre bien les 3 tâches", resultats_couv))

    # Briques porteuses PAR tâche.
    porteuses = {}
    for t in TACHES:
        rap = ablation([t], LIM, SQUELETTES, REMPLISSEURS)
        porteuses[t.id] = {b for (b, p, _) in rap if p}

    print("Briques porteuses par tâche (sq = structure, rmp = logique) :")
    for tid, bs in porteuses.items():
        for b in sorted(bs):
            print(f"    {tid:<20} {b[0]:<4} {b[2]}")
        print()

    # Sépare structure (sq) et logique (rmp).
    logique = {tid: {b for b in bs if b[0] == "rmp"} for tid, bs in porteuses.items()}
    structure = {tid: {b for b in bs if b[0] == "sq"} for tid, bs in porteuses.items()}

    # 1. Chaque tâche a exactement 1 brique de logique porteuse.
    resultats.append(_check("1 brique de LOGIQUE porteuse par tâche (coût unitaire)",
                            all(len(s) == 1 for s in logique.values())))

    # 2. Les logiques sont DEUX À DEUX DISJOINTES (zéro transfert de logique).
    union_logique = set().union(*logique.values())
    somme_logique = sum(len(s) for s in logique.values())
    resultats.append(_check(f"logique NE transfère PAS : union={len(union_logique)} == somme={somme_logique}",
                            len(union_logique) == somme_logique))

    # 3. La STRUCTURE, elle, s'amortit : le squelette « return {STR} » porte 2 tâches.
    str_sk = ("sq", None, "return {STR}")
    partage_structure = sum(1 for bs in structure.values() if str_sk in bs)
    resultats.append(_check(f"la STRUCTURE s'amortit un peu (« return {{STR}} » porte {partage_structure} tâches)",
                            partage_structure == 2))

    # 4. Bilan : coût total des briques porteuses ≈ linéaire en tâches.
    union_tout = set().union(*porteuses.values())
    print(f"Bilan : {len(union_tout)} briques porteuses pour {len(TACHES)} tâches "
          f"(dont {len(union_logique)} de logique, 1/tâche, non partagées).")
    resultats.append(_check("coût ≈ linéaire : ~1 brique de logique NEUVE par tâche",
                            len(union_logique) == len(TACHES)))

    print()
    if all(resultats):
        print(f"G4 VALIDÉ — {len(resultats)}/{len(resultats)}. Le mur est quantifié : la STRUCTURE "
              f"s'amortit, la LOGIQUE non (1 brique/tâche). D'où le besoin d'un modèle appris au-delà.")
        return 0
    print(f"ÉCHEC — {sum(resultats)}/{len(resultats)}.")
    return 1


if __name__ == "__main__":
    raise SystemExit(main())
