"""
VALIDATION — FORME DICT×DICT (invention_multi) : palier structurel, atome 13 — deux mappings en deux arguments.

Frontière MESURÉE : clés communes, soustraction, restriction = brique_manquante — et la fusion était servie
par le vocab SCALAIRE (a | b) : la forme routée fait passer la fusion au REGISTRE (primitive du langage,
les 2 ordres — la priorité de fusion est une donnée du spec, épinglée par un CONFLIT de clé commune).

Méthode SOUND : labels par fonctions de référence, dicts ADVERSARIAUX (clés communes AVEC CONFLIT de valeur,
clés propres des deux côtés), held-out séparé, re-vérif HORS moteur ; sondes de forme = SWAP, clé commune
retirée, valeur commune perturbée, conflit injecté.

Prouve : (1) FRONTIÈRES FERMÉES — cles_communes_dicts, soustraction_dict, restriction_dict deviennent
INVENTION ; (2) FUSION AU REGISTRE — {**a,**b} reste EXISTE_DEJA (l'ordre épinglé par le conflit du spec) ;
(3) ASYMÉTRIE — la soustraction est a\\b (SWAP la discrimine) ; (4) CORRECT hors moteur ; (5) DÉTERMINISME ;
(6) NON-RÉGRESSION — dict×scalaire et int×int intacts.
"""
from __future__ import annotations

from garde_ressources import borne
borne(max_cpu_s=400)
import invention_multi as IM

ok = total = 0


def check(nom, cond):
    global ok, total
    total += 1
    print(f"  [{'OK ' if cond else 'XXX'}] {nom}")
    if cond:
        ok += 1
    else:
        raise AssertionError(nom)


def _fn2(expr):
    ns: dict = {}
    exec(f"def _f(a, b):\n    return {expr}\n", ns)
    return ns["_f"]


# dicts ADVERSARIAUX : clés communes AVEC conflit de valeur (épingle l'ordre de fusion), clés propres des 2 côtés.
DD = [(({"a": 1, "b": 2}, {"b": 9, "c": 3}),), (({"x": 5}, {"x": 1, "y": 2}),), (({"m": 4, "n": 6}, {"n": 6}),)]
DDH = [(({"u": 2, "v": 3}, {"v": 8, "w": 1}),)]
DDF = [(({"p": 7, "q": 1}, {"q": 4}),)]

CIBLES = [
    ("cles_communes_dicts", lambda a, b: sorted(set(a) & set(b))),
    ("soustraction_dict", lambda a, b: {k: v for k, v in a.items() if k not in b}),
    ("restriction_dict", lambda a, b: {k: v for k, v in a.items() if k in b}),
]

realisations = {}
for nom, ref in CIBLES:
    v = IM.examine_cible_multi(nom,
                               [((a, b), ref(a, b)) for (a, b), in DD],
                               [((a, b), ref(a, b)) for (a, b), in DDH])
    check(f"{nom} : frontière FERMÉE (INVENTION)", v.statut == IM.INVENTION)
    f = _fn2(v.par)
    check(f"{nom} : reproduit paires + sondes fraîches HORS moteur",
          all(f(dict(a), dict(b)) == ref(a, b) for (a, b), in DD + DDH + DDF))
    realisations[nom] = v.par

# FUSION AU REGISTRE : {**a, **b} EXISTE_DEJA — l'ordre est épinglé par le conflit (b: 2 vs 9 -> 9 gagne).
_ref_f = lambda a, b: {**a, **b}
v = IM.examine_cible_multi("fusion_dicts",
                           [((a, b), _ref_f(a, b)) for (a, b), in DD],
                           [((a, b), _ref_f(a, b)) for (a, b), in DDH])
check("fusion : reste EXISTE_DEJA ({**a, **b}, ordre épinglé par le conflit)",
      v.statut == IM.EXISTE_DEJA and v.par == "{**a, **b}")
_ref_g = lambda a, b: {**b, **a}
v = IM.examine_cible_multi("fusion_inverse",
                           [((a, b), _ref_g(a, b)) for (a, b), in DD],
                           [((a, b), _ref_g(a, b)) for (a, b), in DDH])
check("fusion inverse : reste EXISTE_DEJA ({**b, **a})", v.statut == IM.EXISTE_DEJA and v.par == "{**b, **a}")

# ASYMÉTRIE : la soustraction est a\b.
check("soustraction asymétrique (a\\b ≠ b\\a)",
      _fn2(realisations["soustraction_dict"])({"a": 1, "b": 2}, {"b": 9}) == {"a": 1}
      and _fn2(realisations["soustraction_dict"])({"b": 9}, {"a": 1, "b": 2}) == {})

# DÉTERMINISME.
_ref_0 = CIBLES[0][1]
v2 = IM.examine_cible_multi("cles_communes_dicts",
                            [((a, b), _ref_0(a, b)) for (a, b), in DD],
                            [((a, b), _ref_0(a, b)) for (a, b), in DDH])
check("déterminisme (clés communes : même réalisation aux deux passes)",
      v2.statut == IM.INVENTION and v2.par == realisations["cles_communes_dicts"])

# NON-RÉGRESSION : dict×scalaire et int×int intacts.
v = IM.examine_cible_multi("retire_cle",
                           [(({"a": 3, "b": 1}, "a"), {"b": 1}), (({"x": 5, "z": 9}, "z"), {"x": 5}),
                            (({"m": 7, "n": 4}, "n"), {"m": 7})],
                           [(({"u": 6, "v": 1}, "v"), {"u": 6})])
check("dict×scalaire : retire_cle reste INVENTION", v.statut == IM.INVENTION)
v = IM.examine_cible_multi("difference", [((7, 2), 5), ((9, 4), 5), ((3, 1), 2)], [((10, 6), 4), ((5, 5), 0)])
check("int×int : difference reste EXISTE_DEJA (a - b)", v.statut == IM.EXISTE_DEJA and v.par == "a - b")

print(f"\nvalide_invention_dict_dict : {ok}/{total}")
assert ok == total
