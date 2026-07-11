"""
VALIDATION — TERNAIRES RELATIONNELS & DÉCOUPE (invention_multi) : palier structurel, atome 21.

Trois frontières MESURÉES à l'arité 3 :
- (table, clé, valeur) : la SÉLECTION WHERE relationnelle ([d for d in t if d[k] == v], ≠, COUNT) —
  complète l'algèbre relationnelle paramétrée (colonne, jointure, groupby… et maintenant WHERE à valeur).
- (str, séparateur, indice) : le SEGMENT de découpe (a.split(b)[c]) + les c premiers segments rejoints.
- élément m[i][j] d'une matrice : chaîne de primitives -> REGISTRE du ternaire séquentiel (a[b][c]),
  l'ordre (colonne, ligne) en candidat (a[c][b], les sondes-permutations discriminent).

Méthode SOUND : specs ADVERSARIAUX — WHERE avec correspondances PARTIELLES (des enregistrements matchent,
d'autres non), matrices NON SYMÉTRIQUES (m[i][j] ≠ m[j][i]), segments tous DISTINCTS dans la chaîne.

Prouve : (1) FRONTIÈRES FERMÉES — selection_where, compte_where, segment deviennent INVENTION ;
(2) element_matrice au REGISTRE (EXISTE_DEJA) et l'ordre (colonne, ligne) résolu en INVENTION a[c][b] ;
(3) CORRECT hors moteur ; (4) DÉTERMINISME ; (5) NON-RÉGRESSION — (seq,i,j), str³, int³ intacts.
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


def _fn3(expr):
    ns: dict = {}
    exec(f"def _f(a, b, c):\n    return {expr}\n", ns)
    return ns["_f"]


# WHERE : correspondances PARTIELLES (matchent et ne matchent pas dans chaque table).
W = [(([{"g": 0, "n": 3}, {"g": 1, "n": 7}, {"g": 0, "n": 4}], "g", 0),),
     (([{"g": 2, "n": 5}, {"g": 3, "n": 1}], "g", 2),),
     (([{"t": 1, "n": 9}, {"t": 3, "n": 0}], "t", 3),)]
WH = [(([{"u": 5, "n": 2}, {"u": 6, "n": 8}], "u", 6),)]
WF = [(([{"z": 4, "n": 1}, {"z": 4, "n": 2}, {"z": 5, "n": 3}], "z", 4),)]
# segments tous DISTINCTS ; indices variés.
S = [(("a-b-c", "-", 1),), (("x,y", ",", 0),), (("u v w z", " ", 2),)]
SH = [(("p:q:r", ":", 2),)]
SF = [(("m.n.o", ".", 0),)]
# matrices NON SYMÉTRIQUES : m[i][j] ≠ m[j][i] sur le spec.
M = [(([[3, 1], [4, 5]], 0, 1),), (([[2, 7, 6], [9, 5, 0]], 1, 2),), (([[8, 2], [6, 4], [1, 3]], 2, 0),)]
MH = [(([[7, 3], [2, 8]], 0, 1),)]
MF = [(([[1, 9], [6, 2]], 1, 0),)]

CIBLES = [
    ("selection_where", lambda t, k, v: [d for d in t if d[k] == v], W, WH, WF),
    ("compte_where", lambda t, k, v: sum(1 for d in t if d[k] == v), W, WH, WF),
    ("segment", lambda a, b, c: a.split(b)[c], S, SH, SF),
]

realisations = {}
for nom, ref, spec_in, held_in, frais in CIBLES:
    v = IM.examine_cible_multi(nom,
                               [((x, y, z), ref(x, y, z)) for (x, y, z), in spec_in],
                               [((x, y, z), ref(x, y, z)) for (x, y, z), in held_in])
    check(f"{nom} : frontière FERMÉE (INVENTION)", v.statut == IM.INVENTION)
    f = _fn3(v.par)
    check(f"{nom} : reproduit paires + sondes fraîches HORS moteur",
          all(f(x, y, z) == ref(x, y, z) for (x, y, z), in spec_in + held_in + frais))
    realisations[nom] = v.par

# element_matrice au REGISTRE ; l'ordre (colonne, ligne) en INVENTION a[c][b].
_ref_e = lambda m, i, j: m[i][j]
v = IM.examine_cible_multi("element_matrice",
                           [((m, i, j), _ref_e(m, i, j)) for (m, i, j), in M],
                           [((m, i, j), _ref_e(m, i, j)) for (m, i, j), in MH])
check("element_matrice : reste EXISTE_DEJA (a[b][c] au registre)",
      v.statut == IM.EXISTE_DEJA and v.par == "a[b][c]")
_ref_ji = lambda m, j, i: m[i][j]
v = IM.examine_cible_multi("element_colonne_ligne",
                           [((m, j, i), _ref_ji(m, j, i)) for (m, i, j), in M],
                           [((m, j, i), _ref_ji(m, j, i)) for (m, i, j), in MH])
check("ordre (colonne, ligne) : INVENTION a[c][b]", v.statut == IM.INVENTION and v.par == "a[c][b]")

# DÉTERMINISME.
_ref_0 = CIBLES[0][1]
v2 = IM.examine_cible_multi("selection_where",
                            [((x, y, z), _ref_0(x, y, z)) for (x, y, z), in W],
                            [((x, y, z), _ref_0(x, y, z)) for (x, y, z), in WH])
check("déterminisme (WHERE : même réalisation aux deux passes)",
      v2.statut == IM.INVENTION and v2.par == realisations["selection_where"])

# NON-RÉGRESSION : (seq, i, j), str³, int³.
v = IM.examine_cible_multi("somme_tranche",
                           [(([3, 1, 4, 1, 5], 1, 3), 5), (([2, 7, 6, 9], 0, 2), 9), (([9, 8, 5, 3, 2], 2, 5), 10)],
                           [(([1, 6, 2, 4, 5, 3], 1, 4), 12)])
check("(seq, i, j) : somme_tranche reste INVENTION", v.statut == IM.INVENTION)
v = IM.examine_cible_multi("remplace",
                           [(("le chat dort", "chat", "chien"), "le chien dort"), (("aaa", "a", "b"), "bbb"),
                            (("xyz", "y", ""), "xz")],
                           [(("bord de mer", "mer", "lac"), "bord de lac")])
check("str³ : remplace reste EXISTE_DEJA", v.statut == IM.EXISTE_DEJA)
v = IM.examine_cible_multi("mediane3", [((3, 1, 2), 2), ((7, 9, 8), 8), ((5, 0, 4), 4)], [((6, 2, 4), 4)])
check("int³ : mediane3 reste EXISTE_DEJA", v.statut == IM.EXISTE_DEJA)

print(f"\nvalide_invention_ternaires_relationnels : {ok}/{total}")
assert ok == total
