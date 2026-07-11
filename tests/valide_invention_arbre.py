"""
VALIDATION — FAMILLE ARBRE (_ARBRE) : palier structurel, agrégats sur imbrication PROFONDE (profondeur arbitraire).

Frontière MESURÉE (sonde palier structurel 2026-07-12) : l'atome flatten RÉCURSIF (_EXPANSION, combinateur
auto-appliqué) existait mais RIEN ne composait par-dessus — somme_arbre, max_arbre, nb_feuilles et
profondeur_arbre restaient brique_manquante. Comblé par la famille _ARBRE, SCOPÉE à l'aplatie récursive
(même design prouvé que _MAT_APLATIE) : AGG∘flatten_rec + le catamorphisme profondeur — sémantique exacte,
pas d'aimant à coïncidences.

Méthode SOUND : labels générés par fonctions de référence RÉCURSIVES, arbres ADVERSARIAUX (profondeurs 2..4
variées, somme du niveau 1 ≠ somme totale, nb feuilles ≠ len du niveau 1, vecteurs de labels tous distincts
entre cibles), réalisation re-vérifiée HORS moteur sur sondes fraîches.

Prouve : (1) FRONTIÈRES FERMÉES — somme_arbre/max_arbre/nb_feuilles/profondeur_arbre deviennent INVENTION ;
(2) CORRECT — chaque réalisation reproduit toutes les paires + sondes fraîches (hors moteur) ; (3) ANTI-
COÏNCIDENCE — la réalisation traite bien l'arbre PROFOND (nb_feuilles([[1,2],[3]])=3 pas 2 ; profondeur ≠ max) ;
(4) DÉTERMINISME ; (5) NON-RÉGRESSION — aplatit_recursif reste INVENTION, une cible PLATE reste EXISTE_DEJA
(sur liste plate, AGG∘flatten_rec ≡ AGG(x) : même signature -> jamais de fausse AMBIGU).
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


def _flat(l):
    out = []
    for e in l:
        out.extend(_flat(e) if isinstance(e, list) else [e])
    return out


def _depth(l):
    return 1 + max((_depth(e) for e in l if isinstance(e, list)), default=0)


# arbres ADVERSARIAUX : profondeurs 2..4, somme niveau-1 ≠ somme totale, feuilles ≠ len niveau-1 ;
# les vecteurs de labels (somme/max/min/feuilles/profondeur) sont tous DISTINCTS entre cibles.
ARBRES = [
    [1, [2, 3], 4],
    [[5, [6]], 7],
    [[1], [2, [3, [4]]], 5],
    [10, [20, [30]]],
    [[2, 4], [6]],
]
ARBRES_HELD = [
    [[[[9]]], 8, [7]],
    [1, [1, [1, [1]]]],
    [[3, [1]], [2], 0],
]
SONDES_FRAICHES = [
    [[7, [2]], [5], 1],
    [4, [4, [4]]],
    [[1, 2], [3]],
]

REFS = {
    "somme_arbre":      lambda x: sum(_flat(x)),
    "max_arbre":        lambda x: max(_flat(x)),
    "nb_feuilles":      lambda x: len(_flat(x)),
    "profondeur_arbre": lambda x: _depth(x),
}

realisations = {}
for nom, ref in REFS.items():
    spec = [(x, ref(x)) for x in ARBRES]
    held = [(x, ref(x)) for x in ARBRES_HELD]
    v = MI.examine_cible(nom, "f(x)", spec, held)
    check(f"{nom} : frontière FERMÉE (INVENTION)", v.statut == MI.INVENTION)
    f = _fn(v.par)
    check(f"{nom} : reproduit paires + sondes fraîches HORS moteur",
          all(f(x) == ref(x) for x in ARBRES + ARBRES_HELD + SONDES_FRAICHES))
    realisations[nom] = v.par

# ANTI-COÏNCIDENCE : la réalisation traite l'arbre PROFOND, pas le seul niveau 1.
check("nb_feuilles compte les FEUILLES ([[1,2],[3]] -> 3, pas len niveau-1 = 2)",
      _fn(realisations["nb_feuilles"])([[1, 2], [3]]) == 3)
check("profondeur ≠ max (sur [1,[2,3],4] : profondeur 2, max 4)",
      _fn(realisations["profondeur_arbre"])([1, [2, 3], 4]) == 2
      and _fn(realisations["max_arbre"])([1, [2, 3], 4]) == 4)
check("somme_arbre = somme TOTALE ([[5,[6]],7] -> 18, pas 7 seul au niveau 1)",
      _fn(realisations["somme_arbre"])([[5, [6]], 7]) == 18)

# DÉTERMINISME : même spec -> même réalisation.
v2 = MI.examine_cible("somme_arbre", "f(x)",
                      [(x, sum(_flat(x))) for x in ARBRES],
                      [(x, sum(_flat(x))) for x in ARBRES_HELD])
check("déterminisme (somme_arbre : même réalisation aux deux passes)",
      v2.statut == MI.INVENTION and v2.par == realisations["somme_arbre"])

# NON-RÉGRESSION : le flatten récursif lui-même reste couvert.
v3 = MI.examine_cible("aplatit_recursif", "f(x)",
                      [(x, _flat(x)) for x in ARBRES],
                      [(x, _flat(x)) for x in ARBRES_HELD])
check("aplatit_recursif reste résolu (non-régression)", v3.statut == MI.INVENTION)

# NON-RÉGRESSION : une cible PLATE (somme) reste EXISTE_DEJA — pas de fausse AMBIGU introduite par _ARBRE.
PLATES = [[3, 1, 4], [2, 7, 6, 9], [5, 5, 2]]
v4 = MI.examine_cible("somme_plate", "f(x)",
                      [(x, sum(x)) for x in PLATES],
                      [([8, 1, 6], 15), ([2, 2], 4)])
check("cible plate somme : reste EXISTE_DEJA (aucune fausse ambiguïté)", v4.statut == MI.EXISTE_DEJA)

print(f"\nvalide_invention_arbre : {ok}/{total}")
assert ok == total
