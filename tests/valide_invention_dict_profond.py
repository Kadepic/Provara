"""
VALIDATION — FAMILLE DICT PROFOND (_DICT_PROFOND, atome 15 du palier structurel) : dict-de-dicts en mono.

Frontière MESURÉE : agrégats des valeurs PROFONDES, aplatissement, dépivot, agrégat par groupe =
brique_manquante — les familles dict ne connaissaient que le dict PLAT (values/keys/argmax) et le
dict-de-LISTES. Comblé par _DICT_PROFOND, dont le DÉPIVOT = l'inverse du pivot 2 niveaux (atome 7) —
referme l'aller-retour pivot/dépivot comme groupby/dégroupage (atome 8) et rle encode/decode.
Validation contextuelle : sur un dict PLAT, _sd.values() crashe -> filtré, jamais une coïncidence.

Prouve : (1) FRONTIÈRES FERMÉES — somme/max des valeurs profondes, aplatissement, dépivot, somme par groupe
deviennent INVENTION ; (2) ALLER-RETOUR — dépivot ∘ pivot-2-niveaux = triplets triés d'origine ;
(3) CORRECT hors moteur ; (4) DÉTERMINISME ; (5) NON-RÉGRESSION — dict plat (argmax) et dict-de-listes
(dégroupage) restent résolus.
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


# dicts de dicts ADVERSARIAUX : tailles de groupes inégales, clés profondes variées.
ND = [{"a": {"x": 1, "y": 2}, "b": {"z": 3}}, {"c": {"w": 5}}, {"d": {"u": 4, "v": 0}, "e": {"t": 7}}]
NDH = [{"f": {"s": 9}, "g": {"r": 1, "q": 2}}]
NDF = [{"h": {"p": 6, "o": 3}}]

CIBLES = [
    ("somme_valeurs_profondes", lambda d: sum(v for sd in d.values() for v in sd.values())),
    ("max_valeurs_profondes", lambda d: max(v for sd in d.values() for v in sd.values())),
    ("aplatit_dict_dicts", lambda d: {k2: v for sd in d.values() for k2, v in sd.items()}),
    ("depivote", lambda d: [[k, k2, v] for k in sorted(d) for k2, v in sorted(d[k].items())]),
    ("somme_par_groupe", lambda d: {k: sum(sd.values()) for k, sd in sorted(d.items())}),
]

realisations = {}
for nom, ref in CIBLES:
    v = MI.examine_cible(nom, "f(x)", [(d, ref(d)) for d in ND], [(d, ref(d)) for d in NDH])
    check(f"{nom} : frontière FERMÉE (INVENTION)", v.statut == MI.INVENTION)
    f = _fn(v.par)
    check(f"{nom} : reproduit paires + sondes fraîches HORS moteur",
          all(f(dict(d)) == ref(d) for d in ND + NDH + NDF))
    realisations[nom] = v.par

# ALLER-RETOUR : dépivot ∘ pivot-2-niveaux (atome 7) = les triplets triés d'origine.
_pivot = lambda x: {a: {p[1]: p[2] for p in x if p[0] == a} for a in sorted({t[0] for t in x})}
triplets = [["a", "x", 1], ["b", "y", 2], ["a", "z", 3]]
check("aller-retour pivot -> dépivot cohérent (triplets triés retrouvés)",
      _fn(realisations["depivote"])(_pivot(triplets)) == [["a", "x", 1], ["a", "z", 3], ["b", "y", 2]])

# DÉTERMINISME.
_ref_0 = CIBLES[0][1]
v2 = MI.examine_cible("somme_valeurs_profondes", "f(x)",
                      [(d, _ref_0(d)) for d in ND], [(d, _ref_0(d)) for d in NDH])
check("déterminisme (somme profonde : même réalisation aux deux passes)",
      v2.statut == MI.INVENTION and v2.par == realisations["somme_valeurs_profondes"])

# NON-RÉGRESSION : dict plat (argmax) et dict-de-listes (dégroupage) restent résolus.
PLATS = [{"a": 3, "b": 9}, {"x": 5, "y": 2}, {"m": 7, "n": 4}]
v = MI.examine_cible("cle_du_max", "f(x)",
                     [(d, max(d, key=d.get)) for d in PLATS], [({"u": 6, "v": 8}, "v")])
check("dict plat : argmax reste résolu", v.statut in (MI.INVENTION, MI.EXISTE_DEJA))
GROUPES = [{0: [4, 2], 1: [3]}, {0: [8], 1: [1, 5, 7]}, {2: [1], 5: [3, 3]}]
_dg = lambda d: [[k, v] for k in sorted(d) for v in d[k]]
v = MI.examine_cible("degroupe", "f(x)", [(d, _dg(d)) for d in GROUPES], [({7: [2, 8]}, [[7, 2], [7, 8]])])
check("dict-de-listes : dégroupage reste INVENTION", v.statut == MI.INVENTION)

print(f"\nvalide_invention_dict_profond : {ok}/{total}")
assert ok == total
