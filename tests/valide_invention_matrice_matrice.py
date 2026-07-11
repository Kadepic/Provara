"""
VALIDATION — FORME MATRICE×MATRICE (invention_multi) : palier structurel, atome 17.

Frontière MESURÉE : somme élément à élément, Hadamard et PRODUIT MATRICIEL = brique_manquante (deux matrices
en deux arguments ne matchaient aucune forme — liste×liste exclut les éléments-listes). Registre = concat
(a + b) ; ops = arithmétique élément à élément + produit matriciel DANS LES DEUX ORDRES (non commutatif :
la sonde SWAP les discrimine).

Méthode SOUND : labels par fonctions de référence, matrices ADVERSARIALES (produit a·b ≠ b·a sur le spec,
non symétriques), held-out séparé, re-vérif HORS moteur.

Prouve : (1) FRONTIÈRES FERMÉES — somme, Hadamard, produit matriciel deviennent INVENTION ; (2) NON-
COMMUTATIVITÉ — le produit servi est bien a·b (vérifié sur une paire où a·b ≠ b·a) ; (3) CORRECT hors
moteur ; (4) CONCAT au registre ; (5) DÉTERMINISME ; (6) NON-RÉGRESSION — liste×liste et int×int intacts.
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


def _prod(a, b):
    return [[sum(a[i][k] * b[k][j] for k in range(len(b))) for j in range(len(b[0]))] for i in range(len(a))]


# matrices ADVERSARIALES : a·b ≠ b·a sur chaque exemple, non symétriques.
MM = [(([[1, 2], [3, 4]], [[5, 6], [7, 8]]),), (([[2, 0], [1, 3]], [[4, 1], [2, 2]]),),
      (([[0, 1], [1, 0]], [[3, 5], [2, 9]]),)]
MMH = [(([[1, 1], [2, 2]], [[3, 3], [4, 4]]),)]
MMF = [(([[2, 1], [0, 3]], [[1, 4], [5, 2]]),)]

CIBLES = [
    ("somme_matrices", lambda a, b: [[x + y for x, y in zip(ra, rb)] for ra, rb in zip(a, b)]),
    ("hadamard", lambda a, b: [[x * y for x, y in zip(ra, rb)] for ra, rb in zip(a, b)]),
    ("produit_matriciel", _prod),
]

realisations = {}
for nom, ref in CIBLES:
    v = IM.examine_cible_multi(nom,
                               [((a, b), ref(a, b)) for (a, b), in MM],
                               [((a, b), ref(a, b)) for (a, b), in MMH])
    check(f"{nom} : frontière FERMÉE (INVENTION)", v.statut == IM.INVENTION)
    f = _fn2(v.par)
    check(f"{nom} : reproduit paires + sondes fraîches HORS moteur",
          all(f([list(r) for r in a], [list(r) for r in b]) == ref(a, b) for (a, b), in MM + MMH + MMF))
    realisations[nom] = v.par

# NON-COMMUTATIVITÉ : le produit servi est bien a·b.
A, B = [[1, 2], [3, 4]], [[5, 6], [7, 8]]
check("produit servi = a·b (≠ b·a sur cette paire)",
      _fn2(realisations["produit_matriciel"])(A, B) == _prod(A, B) and _prod(A, B) != _prod(B, A))

# CONCAT au registre.
_ref_c = lambda a, b: a + b
v = IM.examine_cible_multi("concat_matrices",
                           [((a, b), _ref_c(a, b)) for (a, b), in MM],
                           [((a, b), _ref_c(a, b)) for (a, b), in MMH])
check("concat_matrices : reste EXISTE_DEJA (registre)", v.statut == IM.EXISTE_DEJA)

# DÉTERMINISME.
v2 = IM.examine_cible_multi("produit_matriciel",
                            [((a, b), _prod(a, b)) for (a, b), in MM],
                            [((a, b), _prod(a, b)) for (a, b), in MMH])
check("déterminisme (produit : même réalisation aux deux passes)",
      v2.statut == IM.INVENTION and v2.par == realisations["produit_matriciel"])

# NON-RÉGRESSION : liste×liste et int×int intacts.
v = IM.examine_cible_multi("intersection_triee",
                           [(([3, 1, 4], [1, 9, 3]), [1, 3]), (([5, 5, 2], [2, 8]), [2]),
                            (([9, 0, 7], [7, 9, 4]), [7, 9])],
                           [(([6, 2, 8], [8, 1, 2]), [2, 8])])
check("liste×liste : intersection reste INVENTION", v.statut == IM.INVENTION)
v = IM.examine_cible_multi("difference", [((7, 2), 5), ((9, 4), 5), ((3, 1), 2)], [((10, 6), 4), ((5, 5), 0)])
check("int×int : difference reste EXISTE_DEJA (a - b)", v.statut == IM.EXISTE_DEJA and v.par == "a - b")

print(f"\nvalide_invention_matrice_matrice : {ok}/{total}")
assert ok == total
