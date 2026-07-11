"""
VALIDATION — LISTE-OP MATRICIELLE (etend_matrice + _MAT_LISTE_OP) : Forge sur une frontière matricielle.

Frontière MESURÉE (avant : brique_manquante) : etend_matrice n'agrégeait une primitive matricielle qu'en
SCALAIRE (sum/max/min/prod). Une cible dont la sortie est une LISTE réordonnée de l'aplatie (aplati trié,
unique trié, décroissant) restait hors de portée.

Méthode SOUND : labels générés par la fonction de référence, matrices adversariales de formes variées
(lignes de longueurs inégales), réalisation re-vérifiée hors moteur sur toutes les paires + sondes fraîches.

Prouve : (1) FRONTIÈRES FERMÉES — aplati_trie, aplati_unique, aplati_desc deviennent INVENTION ; (2) CORRECT —
reproduit toutes les paires + sondes fraîches (hors moteur) ; (3) DÉTERMINISME ; (4) NON-RÉGRESSION — une
cible matricielle SCALAIRE (grand_total = somme de l'aplatie) reste l'invention attendue.
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


def _reproduit_tout(expr, paires):
    f = _fn(expr)
    return all(f(a) == o for a, o in paires)


MATS = [[[3, 1], [2]], [[5], [4, 6]], [[9, 7], [8]], [[2, 2], [1, 1]], [[0], [9, 3, 1]], [[6, 5, 4], [3], [2, 1]]]
SONDES = [[[1]], [[8, 8], [8]], [[0, 5], [2, 5, 1]]]

REFS = {
    "aplati_trie": lambda m: sorted(v for r in m for v in r),
    "aplati_unique": lambda m: sorted(set(v for r in m for v in r)),
    "aplati_desc": lambda m: sorted((v for r in m for v in r), reverse=True),
}


def _paires(f, mats):
    return [(m, f(m)) for m in mats]


for nom, f in REFS.items():
    ps = _paires(f, MATS)
    ex, held = ps[:3], ps[3:]
    v = MI.examine_cible(nom, "x", ex, held)
    check(f"{nom} : frontière FERMÉE en INVENTION", v.statut == MI.INVENTION)
    check(f"{nom} : reproduit toutes les paires (hors moteur)", v.par and _reproduit_tout(v.par, ex + held))
    fresh = [(m, f(m)) for m in SONDES]
    check(f"{nom} : correcte sur des matrices FRAÎCHES (pas une coïncidence)", _reproduit_tout(v.par, fresh))
    v2 = MI.examine_cible(nom, "x", ex, held)
    check(f"{nom} : déterministe", v2.par == v.par)

# non-régression : cible matricielle SCALAIRE reste résolue (grand_total = somme de l'aplatie).
gt = _paires(lambda m: sum(v for r in m for v in r), MATS)
vg = MI.examine_cible("grand_total", "x", gt[:3], gt[3:])
check("non-rég : grand_total (scalaire) reste INVENTION/EXISTE (résolu)",
      vg.statut in (MI.INVENTION, MI.EXISTE_DEJA) and vg.par is not None)

print(f"\n== VALIDE_INVENTION_MATRICE_LISTE : {ok}/{total} ==")
assert ok == total
