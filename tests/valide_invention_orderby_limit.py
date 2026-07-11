"""
VALIDATION — ORDER BY / DISTINCT / LIMIT (invention_multi) : palier structurel, atome 23 — le cœur SQL se referme.

Trois frontières MESURÉES (les dernières clauses) : tri par champ, valeurs distinctes d'un champ, limite/
offset/n-ième. Avec colonne (A9), WHERE (A21), GROUP BY (A22), jointure (A11), pivot/dépivot (A7/A15) :
SELECT, WHERE, GROUP BY+agrégats, ORDER BY, DISTINCT, LIMIT, JOIN — le cœur SQL est couvert, paramétré.

Le tri est DÉCORE-TRIE-PROJETTE sans lambda : (clé, indice, enregistrement) — l'indice casse les égalités
AVANT de comparer les dicts (stable ET pas de nœud Lambda : reste dans la liste blanche d'innocuité).

Prouve : (1) FRONTIÈRES FERMÉES — tri_par_champ, valeurs_distinctes, limite deviennent INVENTION ;
(2) STABILITÉ — deux enregistrements à clé ÉGALE gardent leur ordre (spec avec égalités) ; (3) CORRECT hors
moteur ; (4) DISTINCT ≠ colonne triée (doublons retirés) ; (5) DÉTERMINISME ; (6) NON-RÉGRESSION — colonne,
GROUP BY et int×int intacts.
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


# tables NON TRIÉES ; un exemple avec CLÉS ÉGALES (stabilité) ; champs multiples.
T = [(([{"g": 1, "n": "a"}, {"g": 1, "n": "b"}, {"g": 0, "n": "c"}], "g"),),
     (([{"g": 9, "n": "x"}, {"g": 5, "n": "y"}], "g"),),
     (([{"t": 4, "n": "m"}, {"t": 0, "n": "p"}, {"t": 2, "n": "q"}], "t"),)]
TH = [(([{"u": 7, "n": "r"}, {"u": 3, "n": "s"}], "u"),)]
TF = [(([{"z": 2, "n": "w"}, {"z": 2, "n": "v"}, {"z": 1, "n": "u"}], "z"),)]
D = [(([{"g": 3}, {"g": 1}, {"g": 3}], "g"),), (([{"g": 2}, {"g": 2}], "g"),), (([{"t": 4}, {"t": 0}, {"t": 4}], "t"),)]
DH = [(([{"u": 7}, {"u": 7}, {"u": 1}], "u"),)]
DF = [(([{"z": 5}, {"z": 5}, {"z": 5}], "z"),)]
L = [(([{"n": 3}, {"n": 7}, {"n": 4}], 2),), (([{"n": 5}, {"n": 1}], 1),), (([{"n": 9}, {"n": 0}, {"n": 2}, {"n": 8}], 3),)]
LH = [(([{"n": 6}, {"n": 2}], 1),)]
LF = [(([{"n": 4}, {"n": 5}, {"n": 6}], 1),)]

CIBLES = [
    ("tri_par_champ", lambda t, k: sorted(t, key=lambda d: d[k]), T, TH, TF),
    ("valeurs_distinctes", lambda t, k: sorted({d[k] for d in t}), D, DH, DF),
    ("limite", lambda t, n: t[:n], L, LH, LF),
]

realisations = {}
for nom, ref, spec_in, held_in, frais in CIBLES:
    v = IM.examine_cible_multi(nom,
                               [((t, k), ref(t, k)) for (t, k), in spec_in],
                               [((t, k), ref(t, k)) for (t, k), in held_in])
    check(f"{nom} : frontière FERMÉE (INVENTION)", v.statut == IM.INVENTION)
    f = _fn2(v.par)
    check(f"{nom} : reproduit paires + sondes fraîches HORS moteur",
          all(f(t, k) == ref(t, k) for (t, k), in spec_in + held_in + frais))
    realisations[nom] = v.par

# STABILITÉ : clés égales -> ordre d'origine conservé.
check("tri stable (clés égales gardent l'ordre : a avant b)",
      _fn2(realisations["tri_par_champ"])([{"g": 1, "n": "a"}, {"g": 1, "n": "b"}, {"g": 0, "n": "c"}], "g")
      == [{"g": 0, "n": "c"}, {"g": 1, "n": "a"}, {"g": 1, "n": "b"}])

# DISTINCT ≠ colonne triée (doublons retirés).
check("valeurs_distinctes retire les doublons ([3,1,3] -> [1,3])",
      _fn2(realisations["valeurs_distinctes"])([{"g": 3}, {"g": 1}, {"g": 3}], "g") == [1, 3])

# ORDER BY DESC + HAVING (atome 25 — la frontière se déplace, complétée dans la même famille).
_ref_d = lambda t, k: sorted(t, key=lambda d: d[k], reverse=True)
TD = [(([{"g": 1, "n": "a"}, {"g": 3, "n": "b"}, {"g": 1, "n": "c"}], "g"),),
      (([{"g": 9, "n": "x"}, {"g": 5, "n": "y"}], "g"),),
      (([{"t": 4, "n": "m"}, {"t": 0, "n": "p"}, {"t": 7, "n": "q"}], "t"),)]
v = IM.examine_cible_multi("tri_desc",
                           [((t, k), _ref_d(t, k)) for (t, k), in TD],
                           [(([{"u": 7, "n": "r"}, {"u": 3, "n": "s"}], "u"),
                             _ref_d([{"u": 7, "n": "r"}, {"u": 3, "n": "s"}], "u"))])
check("tri DESC : frontière FERMÉE (INVENTION)", v.statut == IM.INVENTION)
check("tri DESC : STABLE (clés égales gardent l'ordre d'origine : a avant c)",
      _fn2(v.par)([{"g": 1, "n": "a"}, {"g": 3, "n": "b"}, {"g": 1, "n": "c"}], "g")
      == [{"g": 3, "n": "b"}, {"g": 1, "n": "a"}, {"g": 1, "n": "c"}])
_ref_h = lambda t, k: sorted(v for v in {d[k] for d in t} if sum(1 for d in t if d[k] == v) > 1)
HV = [(([{"g": 0}, {"g": 1}, {"g": 0}], "g"),), (([{"g": 2}, {"g": 2}, {"g": 3}], "g"),), (([{"t": 4}, {"t": 5}], "t"),)]
v = IM.examine_cible_multi("groupes_multiples",
                           [((t, k), _ref_h(t, k)) for (t, k), in HV],
                           [(([{"u": 7}, {"u": 7}, {"u": 1}], "u"), [7])])
check("HAVING count>1 : frontière FERMÉE (INVENTION)", v.statut == IM.INVENTION)

# DÉTERMINISME.
_ref_0 = CIBLES[0][1]
v2 = IM.examine_cible_multi("tri_par_champ",
                            [((t, k), _ref_0(t, k)) for (t, k), in T],
                            [((t, k), _ref_0(t, k)) for (t, k), in TH])
check("déterminisme (tri : même réalisation aux deux passes)",
      v2.statut == IM.INVENTION and v2.par == realisations["tri_par_champ"])

# NON-RÉGRESSION.
v = IM.examine_cible_multi("somme_colonne",
                           [(([{"n": 3, "p": 1}, {"n": 7, "p": 2}], "n"), 10),
                            (([{"a": 5, "n": 0}, {"n": 4, "a": 1}], "n"), 4)],
                           [(([{"n": 6}, {"n": 2}], "n"), 8)])
check("liste-de-dicts×clé : somme_colonne reste INVENTION", v.statut == IM.INVENTION)
_gb = lambda t, k: {v: [d for d in t if d[k] == v] for v in sorted({d[k] for d in t})}
GB = [(([{"g": 0, "n": 3}, {"g": 1, "n": 7}, {"g": 0, "n": 4}], "g"),),
      (([{"g": 2, "n": 5}, {"g": 2, "n": 1}, {"g": 3, "n": 9}], "g"),),
      (([{"t": 1, "n": 9}, {"t": 3, "n": 0}], "t"),)]
v = IM.examine_cible_multi("groupby_par_champ",
                           [((t, k), _gb(t, k)) for (t, k), in GB],
                           [(([{"u": 5, "n": 2}, {"u": 6, "n": 8}, {"u": 5, "n": 1}], "u"),
                             _gb([{"u": 5, "n": 2}, {"u": 6, "n": 8}, {"u": 5, "n": 1}], "u"))])
check("GROUP BY reste INVENTION", v.statut == IM.INVENTION)
v = IM.examine_cible_multi("difference", [((7, 2), 5), ((9, 4), 5), ((3, 1), 2)], [((10, 6), 4), ((5, 5), 0)])
check("int×int : difference reste EXISTE_DEJA (a - b)", v.statut == IM.EXISTE_DEJA and v.par == "a - b")

print(f"\nvalide_invention_orderby_limit : {ok}/{total}")
assert ok == total
