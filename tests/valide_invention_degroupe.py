"""
VALIDATION — DÉGROUPAGE (_SORTIE_STRUCTUREE, atome 8 du palier structurel) : l'INVERSE du groupby.

Frontière MESURÉE (après l'atome 7) : dict-de-listes -> liste de paires [clé, valeur] restait
brique_manquante — le groupby avait son aller (liste -> dict groupé) mais pas son retour. Même patron que
rle encode/decode (« le plafond monte, la frontière se déplace vers l'inverse »). Clés TRIÉES = déterminisme.

Méthode SOUND : labels par fonction de référence, dicts ADVERSARIAUX (groupes de tailles inégales, clés non
contiguës), held-out séparé, re-vérif HORS moteur ; entrée distinctive (dict de listes) — sur un dict plat,
l'itération des valeurs crashe -> jamais une cible dict-plate par coïncidence.

Prouve : (1) FRONTIÈRE FERMÉE — degroupe devient INVENTION ; (2) CORRECT — re-vérif hors moteur ;
(3) ALLER-RETOUR — degroupe ∘ groupby = paires triées d'origine (cohérence de la boucle) ; (4) DÉTERMINISME ;
(5) NON-RÉGRESSION — groupe_par_parite reste INVENTION, argmax dict (existant) reste résolu.
"""
from __future__ import annotations

from garde_ressources import borne
borne(max_cpu_s=400)
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


GROUPES = [{0: [4, 2], 1: [3]}, {0: [8], 1: [1, 5, 7]}, {0: [2, 6], 1: [9]}, {2: [1], 5: [3, 3]}]
GROUPES_HELD = [{0: [4], 1: [3, 1]}, {7: [2, 8, 5]}]
GROUPES_FRAIS = [{1: [9, 0], 4: [6]}, {3: [5]}]

_ref = lambda d: [[k, v] for k in sorted(d) for v in d[k]]

v = MI.examine_cible("degroupe", "f(x)",
                     [(d, _ref(d)) for d in GROUPES], [(d, _ref(d)) for d in GROUPES_HELD])
check("degroupe : frontière FERMÉE (INVENTION)", v.statut == MI.INVENTION)
f = _fn(v.par)
check("degroupe : reproduit paires + sondes fraîches HORS moteur",
      all(f(dict(d)) == _ref(d) for d in GROUPES + GROUPES_HELD + GROUPES_FRAIS))

# ALLER-RETOUR : degroupe ∘ groupby(parité) = les paires [parité, valeur] dans l'ordre du groupe.
_grp = lambda x: {k: [e for e in x if e % 2 == k] for k in sorted({v % 2 for v in x})}
check("aller-retour groupby -> degroupe cohérent ([4,3,2,1] -> [[0,4],[0,2],[1,3],[1,1]])",
      f(_grp([4, 3, 2, 1])) == [[0, 4], [0, 2], [1, 3], [1, 1]])

# DÉTERMINISME.
v2 = MI.examine_cible("degroupe", "f(x)",
                      [(d, _ref(d)) for d in GROUPES], [(d, _ref(d)) for d in GROUPES_HELD])
check("déterminisme (même réalisation aux deux passes)", v2.statut == MI.INVENTION and v2.par == v.par)

# NON-RÉGRESSION : le groupby (aller) reste résolu ; une cible dict PLATE (argmax, existant) reste résolue.
LISTES = [[3, 1, 4, 1, 5], [2, 7, 6, 9], [1, 2, 3, 4, 5, 6], [8, 5, 8, 2]]
_g = lambda x: {k: [e for e in x if e % 2 == k] for k in sorted({v % 2 for v in x})}
v3 = MI.examine_cible("groupe_par_parite", "f(x)",
                      [(x, _g(x)) for x in LISTES], [([9, 4, 3, 8, 1, 6], _g([9, 4, 3, 8, 1, 6]))])
check("groupe_par_parite reste INVENTION (aller intact)", v3.statut == MI.INVENTION)
PLATS = [{"a": 3, "b": 9}, {"x": 5, "y": 2}, {"m": 7, "n": 4}]
v4 = MI.examine_cible("cle_du_max", "f(x)",
                      [(d, max(d, key=d.get)) for d in PLATS], [({"u": 6, "v": 8}, "v")])
check("dict plat (argmax) reste résolu — pas de collision avec le dégroupage",
      v4.statut in (MI.INVENTION, MI.EXISTE_DEJA))

print(f"\nvalide_invention_degroupe : {ok}/{total}")
assert ok == total
