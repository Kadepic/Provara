"""
VALIDATION — FORMES TERNAIRES HÉTÉROGÈNES PRIMITIVES (invention_multi) : palier structurel, atome 18.

Frontières MESURÉES : remplace (str, motif, substitut) et get-avec-défaut (dict, clé, défaut) =
brique_manquante à l'arité 3 — ce sont des PRIMITIVES du langage -> REGISTRES de forme ; les variantes
d'ORDRE (a.replace(c, b), a.get(c, b), c.join(a.split(b))) en CANDIDATS : les sondes-permutations de
l'arité 3 (swaps adjacents, rotation, renversement) discriminent l'ordre des arguments.

Méthode SOUND : specs ADVERSARIAUX — le motif est PRÉSENT dans la chaîne et motif ≠ substitut (l'ordre
compte) ; la clé est ABSENTE dans certains exemples (le défaut sert), PRÉSENTE dans d'autres.

Prouve : (1) PRIMITIVES AU REGISTRE — remplace et get_defaut restent EXISTE_DEJA ; (2) ORDRE = DONNÉE DU
SPEC — la variante à arguments échangés est résolue (INVENTION a.replace(c, b)) sur un spec qui l'impose ;
(3) CORRECT hors moteur ; (4) DÉTERMINISME ; (5) NON-RÉGRESSION — int³, (seq, i, j) et le binaire intacts.
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


# motif PRÉSENT, motif ≠ substitut, substitution VISIBLE dans la sortie.
R = [(("le chat dort", "chat", "chien"),), (("aaa", "a", "b"),), (("xyz", "y", ""),)]
RH = [(("bord de mer", "mer", "lac"),)]
RF = [(("un deux un", "un", "trois"),)]
# clé ABSENTE dans certains exemples (le défaut sert), présente dans d'autres.
G = [(({"a": 3}, "a", 0),), (({"x": 5, "y": 2}, "z", 9),), (({"m": 7}, "n", 1),)]
GH = [(({"u": 6}, "u", 4),)]
GF = [(({"p": 2}, "q", 8),)]

# (1) PRIMITIVES AU REGISTRE.
_ref_r = lambda a, b, c: a.replace(b, c)
v = IM.examine_cible_multi("remplace",
                           [((a, b, c), _ref_r(a, b, c)) for (a, b, c), in R],
                           [((a, b, c), _ref_r(a, b, c)) for (a, b, c), in RH])
check("remplace : reste EXISTE_DEJA (a.replace(b, c) au registre)",
      v.statut == IM.EXISTE_DEJA and v.par == "a.replace(b, c)")
f = _fn3(v.par)
check("remplace : reproduit paires + sondes fraîches HORS moteur",
      all(f(a, b, c) == _ref_r(a, b, c) for (a, b, c), in R + RH + RF))

_ref_g = lambda a, b, c: a.get(b, c)
v = IM.examine_cible_multi("get_defaut",
                           [((a, b, c), _ref_g(a, b, c)) for (a, b, c), in G],
                           [((a, b, c), _ref_g(a, b, c)) for (a, b, c), in GH])
check("get_defaut : reste EXISTE_DEJA (a.get(b, c) au registre)",
      v.statut == IM.EXISTE_DEJA and v.par == "a.get(b, c)")
f = _fn3(v.par)
check("get_defaut : reproduit paires + sondes fraîches HORS moteur",
      all(f(dict(a), b, c) == _ref_g(a, b, c) for (a, b, c), in G + GH + GF))

# (2) ORDRE = DONNÉE DU SPEC : (chaîne, substitut, motif) -> a.replace(c, b) INVENTION.
_ref_i = lambda a, b, c: a.replace(c, b)
RI = [(("le chat dort", "chien", "chat"),), (("aaa", "b", "a"),), (("xyz", "", "y"),)]
RIH = [(("bord de mer", "lac", "mer"),)]
v = IM.examine_cible_multi("remplace_ordre_inverse",
                           [((a, b, c), _ref_i(a, b, c)) for (a, b, c), in RI],
                           [((a, b, c), _ref_i(a, b, c)) for (a, b, c), in RIH])
check("ordre inversé (chaîne, substitut, motif) : INVENTION a.replace(c, b)",
      v.statut == IM.INVENTION and v.par == "a.replace(c, b)")

# (4) DÉTERMINISME.
v2 = IM.examine_cible_multi("remplace_ordre_inverse",
                            [((a, b, c), _ref_i(a, b, c)) for (a, b, c), in RI],
                            [((a, b, c), _ref_i(a, b, c)) for (a, b, c), in RIH])
check("déterminisme (même réalisation aux deux passes)", v2.statut == IM.INVENTION and v2.par == v.par)

# (5) NON-RÉGRESSION : int³, (seq, i, j), binaire.
v = IM.examine_cible_multi("mediane3", [((3, 1, 2), 2), ((7, 9, 8), 8), ((5, 0, 4), 4)], [((6, 2, 4), 4)])
check("int³ : mediane3 reste EXISTE_DEJA", v.statut == IM.EXISTE_DEJA)
v = IM.examine_cible_multi("somme_tranche",
                           [(([3, 1, 4, 1, 5], 1, 3), 5), (([2, 7, 6, 9], 0, 2), 9), (([9, 8, 5, 3, 2], 2, 5), 10)],
                           [(([1, 6, 2, 4, 5, 3], 1, 4), 12)])
check("(seq, i, j) : somme_tranche reste INVENTION", v.statut == IM.INVENTION)
v = IM.examine_cible_multi("difference", [((7, 2), 5), ((9, 4), 5), ((3, 1), 2)], [((10, 6), 4), ((5, 5), 0)])
check("int×int : difference reste EXISTE_DEJA (a - b)", v.statut == IM.EXISTE_DEJA and v.par == "a - b")

print(f"\nvalide_invention_ternaires_het : {ok}/{total}")
assert ok == total
