"""
VALIDATION — FAMILLE SORTIES STRUCTURÉES (_SORTIE_STRUCTUREE) : palier structurel, atome 2.

Frontière MESURÉE (sonde palier structurel 2026-07-12) : partition par prédicat, groupby par clé CALCULÉE et
pivot liste-de-paires -> dict restaient brique_manquante (paquets_de_2 déjà couvert par découpe). Comblé par
la famille _SORTIE_STRUCTUREE — les opérateurs de première classe de la littérature table-manipulation
(GroupBy/Pivot/Partition), dirigée BORNÉE, sorties DISTINCTIVES (liste-de-2-listes, dict-de-listes, dict).

Méthode SOUND : labels générés par fonctions de référence, entrées ADVERSARIALES (parités dispersées, paires
ASYMÉTRIQUES pour discriminer pivot direct vs inversé, groupes de tailles inégales), held-out séparé,
réalisation re-vérifiée HORS moteur sur sondes fraîches.

Prouve : (1) FRONTIÈRES FERMÉES — partition_pair_impair, groupe_par_parite, groupe_par_longueur,
pivote_en_dict, pivote_inverse deviennent INVENTION ; (2) CORRECT — chaque réalisation reproduit paires +
sondes fraîches (hors moteur) ; (3) ANTI-COÏNCIDENCE — pivot direct ≠ inversé sur paire asymétrique ;
le groupby rend un DICT groupé, pas une liste filtrée ; (4) DÉTERMINISME ; (5) NON-RÉGRESSION —
paquets_de_2 reste INVENTION (découpe), une cible plate (somme) reste EXISTE_DEJA.
"""
from __future__ import annotations

from garde_ressources import borne
borne(max_cpu_s=600)
import moteur_invention as MI

ok = total = 0


def check(nom, cond):
    global ok, total
    total += 1
    print(f"  [{'OK ' if cond else 'XXX'}] {nom}")
    if cond:
        ok += 1
    else:
        raise AssertionError(nom)


def _fn(expr):
    ns: dict = {}
    exec(f"def _f(x):\n    return {expr}\n", ns)
    return ns["_f"]


# entrées ADVERSARIALES : parités DISPERSÉES (jamais groupées), tailles de groupes inégales.
LISTES = [[3, 1, 4, 1, 5], [2, 7, 6, 9], [1, 2, 3, 4, 5, 6], [8, 5, 8, 2]]
LISTES_HELD = [[9, 4, 3, 8, 1, 6], [5, 5, 2, 7]]
LISTES_FRAICHES = [[7, 2, 9, 4, 4], [1, 3, 6]]
# paires ASYMÉTRIQUES (a ≠ b partout) : pivot direct et inversé divergent sur CHAQUE exemple.
PAIRES = [[[1, 10], [2, 20], [3, 30]], [[5, 7], [8, 9]], [[4, 1], [6, 2], [9, 3]]]
PAIRES_HELD = [[[2, 5], [7, 1], [9, 8]], [[0, 3], [1, 4]]]
PAIRES_FRAICHES = [[[6, 2], [3, 8]], [[10, 40], [50, 20]]]
MOTS = [["a", "bb", "cc", "d"], ["xyz", "ab", "p"], ["mm", "nnn", "oo"]]
MOTS_HELD = [["q", "rr", "sss", "t"], ["uu", "v"]]
MOTS_FRAIS = [["e", "ff", "ggg"], ["hh", "i", "jj"]]

CIBLES = [
    ("partition_pair_impair",
     lambda x: [[e for e in x if e % 2 == 0], [e for e in x if e % 2 == 1]],
     LISTES, LISTES_HELD, LISTES_FRAICHES),
    ("groupe_par_parite",
     lambda x: {k: [e for e in x if e % 2 == k] for k in sorted({v % 2 for v in x})},
     LISTES, LISTES_HELD, LISTES_FRAICHES),
    ("groupe_par_longueur",
     lambda x: {k: [e for e in x if len(e) == k] for k in sorted({len(v) for v in x})},
     MOTS, MOTS_HELD, MOTS_FRAIS),
    ("pivote_en_dict", lambda x: {a: b for a, b in x}, PAIRES, PAIRES_HELD, PAIRES_FRAICHES),
    ("pivote_inverse", lambda x: {b: a for a, b in x}, PAIRES, PAIRES_HELD, PAIRES_FRAICHES),
]

realisations = {}
for nom, ref, spec_in, held_in, frais in CIBLES:
    v = MI.examine_cible(nom, "f(x)", [(x, ref(x)) for x in spec_in], [(x, ref(x)) for x in held_in])
    check(f"{nom} : frontière FERMÉE (INVENTION)", v.statut == MI.INVENTION)
    f = _fn(v.par)
    check(f"{nom} : reproduit paires + sondes fraîches HORS moteur",
          all(f(x) == ref(x) for x in spec_in + held_in + frais))
    realisations[nom] = v.par

# ANTI-COÏNCIDENCE : pivot direct ≠ inversé sur une paire asymétrique ; groupby rend un DICT groupé.
check("pivot direct ≠ pivot inversé (paire asymétrique [[3, 8]])",
      _fn(realisations["pivote_en_dict"])([[3, 8]]) == {3: 8}
      and _fn(realisations["pivote_inverse"])([[3, 8]]) == {8: 3})
check("groupe_par_parite rend un DICT de listes ({0: pairs, 1: impairs})",
      _fn(realisations["groupe_par_parite"])([4, 3, 2, 1]) == {0: [4, 2], 1: [3, 1]})

# DÉTERMINISME : même spec -> même réalisation.
_ref_part = CIBLES[0][1]
v2 = MI.examine_cible("partition_pair_impair", "f(x)",
                      [(x, _ref_part(x)) for x in LISTES], [(x, _ref_part(x)) for x in LISTES_HELD])
check("déterminisme (partition : même réalisation aux deux passes)",
      v2.statut == MI.INVENTION and v2.par == realisations["partition_pair_impair"])

# NON-RÉGRESSION : paquets_de_2 (déjà couvert AVANT l'atome) reste résolu.
v3 = MI.examine_cible("paquets_de_2", "f(x)",
                      [(x, [x[i:i + 2] for i in range(0, len(x), 2)]) for x in LISTES],
                      [(x, [x[i:i + 2] for i in range(0, len(x), 2)]) for x in LISTES_HELD])
check("paquets_de_2 reste résolu (non-régression)", v3.statut == MI.INVENTION)

# NON-RÉGRESSION : une cible PLATE (somme) reste EXISTE_DEJA — aucune fausse ambiguïté introduite.
v4 = MI.examine_cible("somme_plate", "f(x)",
                      [([3, 1, 4], 8), ([2, 7, 6, 9], 24), ([5, 5, 2], 12)],
                      [([8, 1, 6], 15), ([2, 2], 4)])
check("cible plate somme : reste EXISTE_DEJA (aucune fausse ambiguïté)", v4.statut == MI.EXISTE_DEJA)

print(f"\nvalide_invention_sorties_structurees : {ok}/{total}")
assert ok == total
