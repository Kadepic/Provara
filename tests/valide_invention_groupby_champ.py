"""
VALIDATION — GROUP BY RELATIONNEL PAR CHAMP (invention_multi) : palier structurel, atome 22.

Deux frontières MESURÉES — le GROUP BY SQL complet, dernière pièce relationnelle paramétrée :
- (table, clé) : groupby_par_champ -> {valeur: [enregistrements]} + compte par groupe (_LD_OPS) ;
- (table, clé groupe, clé valeur) : GROUP BY + AGRÉGAT (somme/max/liste des c par groupe, _TCV_OPS) — le
  3e argument est un CHAMP ici, une VALEUR dans le WHERE : les deux lectures coexistent en candidats, la
  validation contextuelle et les sondes discriminent.

Méthode SOUND : tables ADVERSARIALES (groupes de tailles inégales, valeurs de groupe non contiguës,
champs multiples), held-out séparé, re-vérif HORS moteur.

Prouve : (1) FRONTIÈRES FERMÉES — groupby_par_champ, compte_par_groupe, groupby_somme, groupby_max
deviennent INVENTION ; (2) COHÉRENCE WHERE/GROUP BY — le WHERE (c = valeur) reste résolu à côté du
GROUP BY (c = champ) ; (3) CORRECT hors moteur ; (4) DÉTERMINISME ; (5) NON-RÉGRESSION — colonne, jointure
et int×int intacts.
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


def _fn3(expr):
    ns: dict = {}
    exec(f"def _f(a, b, c):\n    return {expr}\n", ns)
    return ns["_f"]


# tables ADVERSARIALES : groupes de tailles inégales, valeurs non contiguës.
T = [(([{"g": 0, "n": 3}, {"g": 1, "n": 7}, {"g": 0, "n": 4}], "g"),),
     (([{"g": 2, "n": 5}, {"g": 2, "n": 1}, {"g": 3, "n": 9}], "g"),),
     (([{"t": 1, "n": 9}, {"t": 3, "n": 0}], "t"),)]
TH = [(([{"u": 5, "n": 2}, {"u": 6, "n": 8}, {"u": 5, "n": 1}], "u"),)]
TF = [(([{"z": 4, "n": 1}, {"z": 7, "n": 2}, {"z": 4, "n": 3}], "z"),)]
T3 = [(([{"g": 0, "n": 3}, {"g": 1, "n": 7}, {"g": 0, "n": 4}], "g", "n"),),
      (([{"g": 2, "n": 5}, {"g": 2, "n": 1}, {"g": 3, "n": 9}], "g", "n"),),
      (([{"t": 1, "m": 9}, {"t": 3, "m": 0}], "t", "m"),)]
T3H = [(([{"u": 5, "n": 2}, {"u": 6, "n": 8}, {"u": 5, "n": 1}], "u", "n"),)]
T3F = [(([{"z": 4, "w": 1}, {"z": 7, "w": 2}, {"z": 4, "w": 3}], "z", "w"),)]

# (table, clé) — binaires.
CIBLES2 = [
    ("groupby_par_champ", lambda t, k: {v: [d for d in t if d[k] == v] for v in sorted({d[k] for d in t})}),
    ("compte_par_groupe", lambda t, k: {v: sum(1 for d in t if d[k] == v) for v in sorted({d[k] for d in t})}),
]
realisations = {}
for nom, ref in CIBLES2:
    v = IM.examine_cible_multi(nom, [((t, k), ref(t, k)) for (t, k), in T], [((t, k), ref(t, k)) for (t, k), in TH])
    check(f"{nom} : frontière FERMÉE (INVENTION)", v.statut == IM.INVENTION)
    f = _fn2(v.par)
    check(f"{nom} : reproduit paires + sondes fraîches HORS moteur",
          all(f(t, k) == ref(t, k) for (t, k), in T + TH + TF))
    realisations[nom] = v.par

# (table, clé groupe, clé valeur) — ternaires.
CIBLES3 = [
    ("groupby_somme", lambda t, k, k2: {v: sum(d[k2] for d in t if d[k] == v) for v in sorted({d[k] for d in t})}),
    ("groupby_max", lambda t, k, k2: {v: max(d[k2] for d in t if d[k] == v) for v in sorted({d[k] for d in t})}),
]
for nom, ref in CIBLES3:
    v = IM.examine_cible_multi(nom,
                               [((t, k, k2), ref(t, k, k2)) for (t, k, k2), in T3],
                               [((t, k, k2), ref(t, k, k2)) for (t, k, k2), in T3H])
    check(f"{nom} : frontière FERMÉE (INVENTION)", v.statut == IM.INVENTION)
    f = _fn3(v.par)
    check(f"{nom} : reproduit paires + sondes fraîches HORS moteur",
          all(f(t, k, k2) == ref(t, k, k2) for (t, k, k2), in T3 + T3H + T3F))

# COHÉRENCE WHERE/GROUP BY : le WHERE (c = VALEUR) reste résolu.
W = [(([{"g": 0, "n": 3}, {"g": 1, "n": 7}, {"g": 0, "n": 4}], "g", 0),),
     (([{"g": 2, "n": 5}, {"g": 3, "n": 1}], "g", 2),),
     (([{"t": 1, "n": 9}, {"t": 3, "n": 0}], "t", 3),)]
_ref_w = lambda t, k, v: [d for d in t if d[k] == v]
v = IM.examine_cible_multi("selection_where",
                           [((t, k, val), _ref_w(t, k, val)) for (t, k, val), in W],
                           [(([{"u": 5, "n": 2}, {"u": 6, "n": 8}], "u", 6), [{"u": 6, "n": 8}])])
check("WHERE (valeur) reste INVENTION à côté du GROUP BY (champ)", v.statut == IM.INVENTION)

# DÉTERMINISME.
_ref_0 = CIBLES2[0][1]
v2 = IM.examine_cible_multi("groupby_par_champ",
                            [((t, k), _ref_0(t, k)) for (t, k), in T],
                            [((t, k), _ref_0(t, k)) for (t, k), in TH])
check("déterminisme (groupby : même réalisation aux deux passes)",
      v2.statut == IM.INVENTION and v2.par == realisations["groupby_par_champ"])

# NON-RÉGRESSION.
v = IM.examine_cible_multi("somme_colonne",
                           [(([{"n": 3, "p": 1}, {"n": 7, "p": 2}], "n"), 10),
                            (([{"a": 5, "n": 0}, {"n": 4, "a": 1}], "n"), 4)],
                           [(([{"n": 6}, {"n": 2}], "n"), 8)])
check("liste-de-dicts×clé : somme_colonne reste INVENTION", v.statut == IM.INVENTION)
_T1 = [{"id": 1, "n": "a"}, {"id": 2, "n": "b"}, {"id": 3, "n": "c"}]
_U1 = [{"id": 2, "v": 20}, {"id": 1, "v": 10}, {"id": 8, "v": 80}]
_ref_j = lambda a, b: [{**da, **db} for da in a for db in b if da["id"] == db["id"]]
v = IM.examine_cible_multi("jointure_interne",
                           [((_T1, _U1), _ref_j(_T1, _U1)),
                            (([{"id": 6, "n": "y"}, {"id": 5, "n": "x"}], [{"id": 6, "v": 3}, {"id": 4, "v": 8}]),
                             [{"id": 6, "n": "y", "v": 3}])],
                           [(([{"id": 9, "n": "m"}], [{"id": 9, "v": 1}, {"id": 4, "v": 2}]),
                             [{"id": 9, "n": "m", "v": 1}])])
check("table×table : jointure reste INVENTION", v.statut == IM.INVENTION)
v = IM.examine_cible_multi("difference", [((7, 2), 5), ((9, 4), 5), ((3, 1), 2)], [((10, 6), 4), ((5, 5), 0)])
check("int×int : difference reste EXISTE_DEJA (a - b)", v.statut == IM.EXISTE_DEJA and v.par == "a - b")

print(f"\nvalide_invention_groupby_champ : {ok}/{total}")
assert ok == total
