"""
VALIDATION — FAMILLE D'INVENTION INDEXÉE (etend_indexe) : employer la Forge pour repousser une frontière.

Frontière MESURÉE (avant la famille : verdict brique_manquante, 0 candidat) : aucune famille ne construisait
d'agrégat où le PRÉDICAT ou la TRANSFORMATION référence l'INDICE `_i`, pas seulement la valeur `_e`. Donc le
compte des points fixes (x[i]==i), le compte des éléments dépassant leur position (e>i)… étaient hors de portée.

Méthode SOUND (anti-coïncidence, cf. [[feedback-resolution-coincidence-froid]]) : les labels sont GÉNÉRÉS par
la fonction de référence (jamais à la main — les erreurs de comptage d'index créent de fausses frontières), sur
des entrées ADVERSARIALES de longueurs variées (2..7) où une réalisation positionnelle simple (x[0], stride)
diverge. La réalisation rendue est RE-VÉRIFIÉE ici, indépendamment du moteur, sur toutes les paires ET sur des
sondes fraîches d'autres longueurs.

Prouve : (1) FRONTIÈRE FERMÉE — compte_fixe et compte_e_sup_index deviennent INVENTION, réalisation
index-référençante (contient `enumerate`) issue de la famille ; (2) CORRECT — la réalisation reproduit toutes
les paires + des sondes fraîches (hors moteur) ; (3) ANTI-COÏNCIDENCE — la cible dépend de l'ORDRE : exiger
l'invariance par permutation la REFUSE (le moteur ne prétend jamais une invariance fausse) ; (4) SOLIDITÉ —
force_spec donne un score élevé (spec fort) ; (5) DÉTERMINISME ; (6) NON-RÉGRESSION — une cible non indexée
(amplitude) reste l'invention attendue.
"""
from __future__ import annotations

from garde_ressources import borne
borne(max_cpu_s=400)
import ia
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
    for a, o in paires:
        r = f(list(a))
        if r != o or isinstance(r, bool) != isinstance(o, bool):
            return False
    return True


# Entrées adversariales : longueurs 2..7, valeurs qui ne coïncident pas avec une agrégation positionnelle simple.
LISTES = [[0, 9, 2, 1], [5, 1, 7], [0, 1, 2, 3, 9], [9, 9, 9], [0, 2, 2, 4, 4, 5], [3, 1, 2, 0],
          [0, 1], [7, 1, 2, 3, 4, 9, 6]]
SONDES_FRAICHES = [[0], [1, 1, 2, 2], [0, 0, 2, 0, 4, 5], [2, 2, 2, 2, 2]]   # d'AUTRES longueurs, hors ex/held

REFS = {
    "compte_fixe": lambda x: sum(1 for i, e in enumerate(x) if e == i),
    "compte_e_sup_index": lambda x: sum(1 for i, e in enumerate(x) if e > i),
}


def _paires(f, listes):
    return [(xs, f(xs)) for xs in listes]


for nom, f in REFS.items():
    ps = _paires(f, LISTES)
    ex, held = ps[:3], ps[3:]
    v = MI.examine_cible(nom, "x", ex, held)
    # (1) frontière fermée en INVENTION, réalisation index-référençante
    check(f"{nom} : frontière FERMÉE en INVENTION", v.statut == MI.INVENTION)
    check(f"{nom} : réalisation index-référençante (contient enumerate)",
          v.par is not None and "enumerate" in v.par)
    # (2) correct sur les paires ET sur des sondes fraîches d'autres longueurs (re-vérifié hors moteur)
    check(f"{nom} : reproduit toutes les paires (hors moteur)", _reproduit_tout(v.par, ex + held))
    fresh = [(s, f(s)) for s in SONDES_FRAICHES]
    check(f"{nom} : correcte sur des sondes FRAÎCHES d'autres longueurs (pas une coïncidence)",
          _reproduit_tout(v.par, fresh))
    # (3) anti-coïncidence métamorphique : dépend de l'ordre -> exiger la permutation la REFUSE
    vp = MI.examine_cible(nom, "x", ex, held, proprietes=("invariance_permutation",))
    check(f"{nom} : exiger l'invariance par permutation la refuse (dépend de l'index)",
          vp.statut != MI.INVENTION)
    # (4) solidité : force_spec score élevé
    fs = ia.force_du_spec(v.par, ex, held)
    check(f"{nom} : spec fort (score de mutation >= 0.6)", fs["score"] >= 0.6)
    # (5) déterminisme
    v2 = MI.examine_cible(nom, "x", ex, held)
    check(f"{nom} : déterministe (même réalisation)", v2.par == v.par)

# (6) non-régression : une cible NON indexée reste l'invention attendue
va = MI.examine_cible("amplitude", "x", [([3, 1, 5], 4), ([2, 2], 0), ([10, 0, 3], 10)],
                      [([0, 9, 4], 9), ([7], 0), ([5, 5, 1], 4)])
check("non-rég : amplitude reste INVENTION (max-min), la nouvelle famille ne la perturbe pas",
      va.statut == MI.INVENTION and va.par is not None and "enumerate" not in va.par)

print(f"\n== VALIDE_INVENTION_INDEXE : {ok}/{total} ==")
assert ok == total
