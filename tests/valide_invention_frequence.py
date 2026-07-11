"""
VALIDATION — COMPLÉTION DE LA FAMILLE FRÉQUENCE (_NOMBRES_LISTE) : Forge sur deux frontières multiset.

Frontière MESURÉE (avec exemples NON groupés, sinon fréquence coïncide avec plus-longue-série — piège de
coïncidence) : la famille fréquence avait le mode et le compte des doublons (count>1), mais PAS le compte des
hapax (count==1) ni la fréquence du mode (max des comptes) -> compte_uniques et nb_max_freq restaient
brique_manquante.

Méthode SOUND : labels générés par Counter, listes ADVERSARIALES dispersées (valeurs répétées à positions
non consécutives, pour tuer la coïncidence avec groupby/plus-longue-série), réalisation re-vérifiée hors
moteur sur sondes fraîches.

Prouve : (1) FRONTIÈRES FERMÉES — compte_uniques (hapax) et nb_max_freq (fréquence du mode) deviennent
INVENTION ; (2) CORRECT — reproduit toutes les paires + sondes fraîches (hors moteur) ; (3) ANTI-COÏNCIDENCE —
sur une liste DISPERSÉE, la réalisation diffère de la plus-longue-série (elle compte bien les fréquences, pas
les runs) ; (4) DÉTERMINISME ; (5) NON-RÉGRESSION — compte des doublons (count>1, déjà présent) reste résolu.
"""
from __future__ import annotations

from collections import Counter

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
    return all(f(list(a)) == o for a, o in paires)


# listes DISPERSÉES (répétitions non consécutives) : fréquence != plus-longue-série
LISTES = [[1, 2, 1, 3], [5, 5, 6, 7, 5], [4, 3, 4, 3, 9], [8, 1, 8, 1, 2, 3], [2, 7, 2, 7, 7], [1, 2, 3], [9, 9, 1, 1, 5]]
SONDES = [[3, 1, 3, 1, 3], [1, 2, 3, 4], [6, 6, 6], [0, 5, 0, 5, 9, 9]]

REFS = {
    "compte_uniques": lambda x: sum(1 for v in Counter(x).values() if v == 1),
    "nb_max_freq": lambda x: max(Counter(x).values()),
}

for nom, f in REFS.items():
    ps = [(x, f(x)) for x in LISTES]
    ex, held = ps[:4], ps[4:]
    v = MI.examine_cible(nom, "x", ex, held)
    check(f"{nom} : frontière FERMÉE en INVENTION", v.statut == MI.INVENTION)
    check(f"{nom} : reproduit toutes les paires (hors moteur)", v.par and _reproduit_tout(v.par, ex + held))
    fresh = [(s, f(s)) for s in SONDES]
    check(f"{nom} : correcte sur des sondes FRAÎCHES (pas une coïncidence)", _reproduit_tout(v.par, fresh))
    v2 = MI.examine_cible(nom, "x", ex, held)
    check(f"{nom} : déterministe", v2.par == v.par)

# (3) anti-coïncidence : sur [3,1,3,1,3] (dispersée), nb_max_freq = 3 (le 3 apparaît 3×), mais la
# plus-longue-série consécutive = 1 (aucun doublon adjacent) -> la fréquence n'est PAS le run.
disp = [3, 1, 3, 1, 3]
plus_longue_serie = max(sum(1 for _ in g) for _, g in __import__("itertools").groupby(disp))
check("anti-coïncidence : fréquence du mode (3) != plus-longue-série (1) sur liste dispersée",
      REFS["nb_max_freq"](disp) == 3 and plus_longue_serie == 1)

# (5) non-régression : compte des doublons (count>1, fixture préexistante) reste résolu
vd = MI.examine_cible("compte_doublons", "x",
                      [(x, sum(1 for v in Counter(x).values() if v >= 2)) for x in LISTES][:4],
                      [(x, sum(1 for v in Counter(x).values() if v >= 2)) for x in LISTES][4:])
check("non-rég : compte des doublons (count>1) reste résolu", vd.statut in (MI.INVENTION, MI.EXISTE_DEJA))

print(f"\n== VALIDE_INVENTION_FREQUENCE : {ok}/{total} ==")
assert ok == total
