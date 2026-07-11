"""
VALIDATION — FORME LISTE×LISTE (invention_multi) : palier structurel, atome 10 — deux séquences en deux ARGUMENTS.

Frontière MESURÉE : intersection/union/différence, ZipWith (somme/produit par position), produit scalaire =
brique_manquante — et la MESURE A ATTRAPÉ LE PIÈGE de la forme : sans routage, les capacités SCALAIRES
tournaient sur les listes (max(a, b) LEXICOGRAPHIQUE reproduisait une différence sans recouvrement -> faux
sentiment d'EXISTE_DEJA sur spec faible). Design retenu : registre = concat seul ; max/min lexicographiques
en CANDIDATS (l'unicité sur sondes tranche) ; sondes de forme = SWAP + injection de CHEVAUCHEMENT +
renversements + longueurs inégales.

Méthode SOUND : labels par fonctions de référence, specs À RECOUVREMENT (éléments communs ET propres des
deux côtés — la leçon), held-out séparé, re-vérif HORS moteur.

Prouve : (1) FRONTIÈRES FERMÉES — intersection_triee, difference_ordonnee, union_triee, zip_somme,
produit_scalaire deviennent INVENTION ; (2) LE PIÈGE EST FERMÉ — un spec SANS recouvrement rend AMBIGU
honnête avec sonde discriminante (pas un EXISTE_DEJA par coïncidence lexicographique) ; (3) max
lexicographique LÉGITIME reste accessible (INVENTION sur spec adéquat) ; (4) CORRECT — re-vérif hors
moteur ; (5) ASYMÉTRIE — la différence est bien a\\b (le SWAP la discrimine) ; (6) DÉTERMINISME ;
(7) NON-RÉGRESSION des autres chemins d'arité 2.
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


# specs À RECOUVREMENT : éléments communs ET propres des deux côtés (tue les coïncidences sans-recouvrement).
R = [(([3, 1, 4], [1, 9, 3]),), (([5, 5, 2], [2, 8]),), (([9, 0, 7], [7, 9, 4]),)]
RH = [(([6, 2, 8], [8, 1, 2]),)]
RF = [(([4, 7, 1], [1, 4]),)]
Z = [(([3, 1, 4], [2, 7, 6]),), (([5, 5], [1, 2]),), (([9, 0, 1], [4, 4, 2]),)]
ZH = [(([6, 2], [3, 9]),)]
ZF = [(([1, 8], [5, 5]),)]

CIBLES = [
    ("intersection_triee", lambda a, b: sorted(set(a) & set(b)), R, RH, RF),
    ("difference_ordonnee", lambda a, b: [e for e in a if e not in b], R, RH, RF),
    ("union_triee", lambda a, b: sorted(set(a) | set(b)), R, RH, RF),
    ("zip_somme", lambda a, b: [x + y for x, y in zip(a, b)], Z, ZH, ZF),
    ("produit_scalaire", lambda a, b: sum(x * y for x, y in zip(a, b)), Z, ZH, ZF),
]

realisations = {}
for nom, ref, spec_in, held_in, frais in CIBLES:
    v = IM.examine_cible_multi(nom,
                               [((a, b), ref(a, b)) for (a, b), in spec_in],
                               [((a, b), ref(a, b)) for (a, b), in held_in])
    check(f"{nom} : frontière FERMÉE (INVENTION)", v.statut == IM.INVENTION)
    f = _fn2(v.par)
    check(f"{nom} : reproduit paires + sondes fraîches HORS moteur",
          all(f(a, b) == ref(a, b) for (a, b), in spec_in + held_in + frais))
    realisations[nom] = v.par

# LE PIÈGE EST FERMÉ : spec SANS recouvrement (différence = a partout) -> AMBIGU honnête, sonde discriminante.
NO = [(([3, 1, 4], [2, 7, 6]),), (([5, 5], [1, 2]),), (([9, 0, 1, 3], [4, 4, 2, 8]),)]
_ref_d = lambda a, b: [e for e in a if e not in b]
v = IM.examine_cible_multi("difference_sans_recouvrement",
                           [((a, b), _ref_d(a, b)) for (a, b), in NO],
                           [(([6, 2], [3, 9]), [6, 2])])
check("spec sans recouvrement : AMBIGU honnête avec sonde (pas d'EXISTE_DEJA lexicographique)",
      v.statut == IM.AMBIGU and v.sonde is not None)

# max lexicographique LÉGITIME accessible (candidat, pas registre).
_ref_m = lambda a, b: max(a, b)
L = [(([3, 1], [3, 9]),), (([5, 5, 2], [5, 5, 8]),), (([9, 0], [2, 7]),)]
v = IM.examine_cible_multi("max_lexicographique",
                           [((a, b), _ref_m(a, b)) for (a, b), in L],
                           [(([6, 2], [6, 8]), [6, 8])])
check("max lexicographique légitime : INVENTION (candidat sous sondes)",
      v.statut == IM.INVENTION and v.par == "max(a, b)")

# ASYMÉTRIE : la différence servie est bien a\b.
check("différence asymétrique (a\\b : [3,1,4]\\[1,9,3] = [4])",
      _fn2(realisations["difference_ordonnee"])([3, 1, 4], [1, 9, 3]) == [4]
      and _fn2(realisations["difference_ordonnee"])([1, 9, 3], [3, 1, 4]) == [9])

# DÉTERMINISME.
_ref_i = CIBLES[0][1]
v2 = IM.examine_cible_multi("intersection_triee",
                            [((a, b), _ref_i(a, b)) for (a, b), in R],
                            [((a, b), _ref_i(a, b)) for (a, b), in RH])
check("déterminisme (intersection : même réalisation aux deux passes)",
      v2.statut == IM.INVENTION and v2.par == realisations["intersection_triee"])

# NON-RÉGRESSION : concat reste EXISTE_DEJA (registre) ; les autres chemins d'arité 2 ne bougent pas.
_ref_c = lambda a, b: a + b
v = IM.examine_cible_multi("concat",
                           [((a, b), _ref_c(a, b)) for (a, b), in Z],
                           [(([6, 2], [3, 9]), [6, 2, 3, 9])])
check("concat : reste EXISTE_DEJA (registre de la forme)", v.statut == IM.EXISTE_DEJA)
v = IM.examine_cible_multi("n_premiers",
                           [(([3, 1, 4, 1, 5], 2), [3, 1]), (([2, 7, 6], 1), [2]), (([9, 8, 5, 3], 3), [9, 8, 5])],
                           [(([1, 2, 3, 4, 5, 6], 4), [1, 2, 3, 4])])
check("liste×scalaire : n_premiers reste INVENTION", v.statut == IM.INVENTION)
v = IM.examine_cible_multi("difference", [((7, 2), 5), ((9, 4), 5), ((3, 1), 2)], [((10, 6), 4), ((5, 5), 0)])
check("int×int : difference reste EXISTE_DEJA (a - b)", v.statut == IM.EXISTE_DEJA and v.par == "a - b")

print(f"\nvalide_invention_liste_liste : {ok}/{total}")
assert ok == total
