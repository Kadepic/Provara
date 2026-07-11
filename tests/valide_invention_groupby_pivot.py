"""
VALIDATION — GROUPBY GÉNÉRALISÉ + PIVOT 2 NIVEAUX (_SORTIE_STRUCTUREE, atome 7 du palier structurel).

Frontière MESURÉE (après l'atome 2) : le groupby par clé CALCULÉE ne connaissait que parité/mod3/longueur —
groupe par PREMIER ÉLÉMENT (mots/listes), groupe par SIGNE et pivot 2 NIVEAUX (liste de triplets [a,b,c] ->
{a: {b: c}}, le canon pandas pivot_table) restaient brique_manquante. Comblé par 3 schémas à sémantique
exacte, sorties DISTINCTIVES (dict-de-listes, dict-de-dicts) — jamais une cible plate par coïncidence.

Méthode SOUND : labels par fonctions de référence, entrées ADVERSARIALES (groupes de tailles inégales,
clés dispersées non consécutives, triplets à 1er niveau répété), held-out séparé, re-vérif HORS moteur.

Prouve : (1) FRONTIÈRES FERMÉES — les 3 cibles deviennent INVENTION ; (2) CORRECT — re-vérif hors moteur
sur sondes fraîches ; (3) ANTI-COÏNCIDENCE — le pivot 2 niveaux GROUPE bien par 1er champ (clé répétée ->
sous-dicts fusionnés), le groupe par signe sépare -1/0/+1 ; (4) DÉTERMINISME ; (5) NON-RÉGRESSION —
groupe_par_parite (atome 2) reste INVENTION, cible plate reste EXISTE_DEJA.
"""
from __future__ import annotations

from garde_ressources import borne
borne(max_cpu_s=500)
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


MOTS = [["avion", "bateau", "auto", "bus"], ["chat", "chien", "aigle"], ["mer", "monts", "aube"]]
MOTS_HELD = [["arbre", "bois", "buse"], ["nid", "aile"]]
MOTS_FRAIS = [["zinc", "azur", "zeste"], ["col", "arc"]]
INTS = [[3, -1, 4, -5], [-2, 7, 6], [1, -2, 3, -4, 5], [0, 2, -3]]
INTS_HELD = [[-9, 4, -3, 8], [5, -5, 0]]
INTS_FRAIS = [[7, -1, 0, 2], [-4, -6, 3]]
TRIPLES = [[["a", "x", 1], ["a", "y", 2], ["b", "x", 3]], [["c", "z", 5], ["c", "w", 6]]]
TRIPLES_HELD = [[["d", "u", 7], ["e", "v", 8], ["d", "w", 9]]]
TRIPLES_FRAIS = [[["f", "p", 1], ["g", "q", 2], ["f", "r", 3]]]

CIBLES = [
    ("groupe_par_premiere_lettre",
     lambda x: {k: [w for w in x if w[0] == k] for k in sorted({w[0] for w in x})},
     MOTS, MOTS_HELD, MOTS_FRAIS),
    ("groupe_par_signe",
     lambda x: {k: [e for e in x if (e > 0) - (e < 0) == k] for k in sorted({(e > 0) - (e < 0) for e in x})},
     INTS, INTS_HELD, INTS_FRAIS),
    ("pivot_2_niveaux",
     lambda x: {a: {b: c for aa, b, c in x if aa == a} for a in sorted({t[0] for t in x})},
     TRIPLES, TRIPLES_HELD, TRIPLES_FRAIS),
]

realisations = {}
for nom, ref, spec_in, held_in, frais in CIBLES:
    v = MI.examine_cible(nom, "f(x)", [(x, ref(x)) for x in spec_in], [(x, ref(x)) for x in held_in])
    check(f"{nom} : frontière FERMÉE (INVENTION)", v.statut == MI.INVENTION)
    f = _fn(v.par)
    check(f"{nom} : reproduit paires + sondes fraîches HORS moteur",
          all(f(x) == ref(x) for x in spec_in + held_in + frais))
    realisations[nom] = v.par

# ANTI-COÏNCIDENCE : le pivot GROUPE par 1er champ ; le signe sépare -1/0/+1.
check("pivot 2 niveaux : clé répétée -> sous-dicts FUSIONNÉS",
      _fn(realisations["pivot_2_niveaux"])([["a", "x", 1], ["b", "y", 2], ["a", "z", 3]])
      == {"a": {"x": 1, "z": 3}, "b": {"y": 2}})
check("groupe par signe : -1/0/+1 séparés",
      _fn(realisations["groupe_par_signe"])([2, -3, 0, 5]) == {-1: [-3], 0: [0], 1: [2, 5]})

# DÉTERMINISME.
_ref_p = CIBLES[2][1]
v2 = MI.examine_cible("pivot_2_niveaux", "f(x)",
                      [(x, _ref_p(x)) for x in TRIPLES], [(x, _ref_p(x)) for x in TRIPLES_HELD])
check("déterminisme (pivot : même réalisation aux deux passes)",
      v2.statut == MI.INVENTION and v2.par == realisations["pivot_2_niveaux"])

# NON-RÉGRESSION : l'atome 2 reste résolu ; une cible plate reste EXISTE_DEJA.
LISTES = [[3, 1, 4, 1, 5], [2, 7, 6, 9], [1, 2, 3, 4, 5, 6], [8, 5, 8, 2]]
_ref_g = lambda x: {k: [e for e in x if e % 2 == k] for k in sorted({v % 2 for v in x})}
v3 = MI.examine_cible("groupe_par_parite", "f(x)",
                      [(x, _ref_g(x)) for x in LISTES], [([9, 4, 3, 8, 1, 6], _ref_g([9, 4, 3, 8, 1, 6]))])
check("groupe_par_parite (atome 2) reste INVENTION", v3.statut == MI.INVENTION)
v4 = MI.examine_cible("somme_plate", "f(x)",
                      [([3, 1, 4], 8), ([2, 7, 6, 9], 24), ([5, 5, 2], 12)],
                      [([8, 1, 6], 15), ([2, 2], 4)])
check("cible plate somme : reste EXISTE_DEJA", v4.statut == MI.EXISTE_DEJA)

print(f"\nvalide_invention_groupby_pivot : {ok}/{total}")
assert ok == total
