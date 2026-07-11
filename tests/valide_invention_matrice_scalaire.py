"""
VALIDATION — SÉQUENCE×SCALAIRE étendue (invention_multi) : palier structurel, atome 16 — matrice×k + join.

Deux frontières MESURÉES, une extension de la même forme :
- MATRICE×ENTIER : colonne_k, agrégats de la ligne/colonne k = brique_manquante (la ligne m[k] était déjà au
  registre — c'est a[b]). Ops matrice dans _LS_OPS ; sur liste plate d'entiers elles crashent (validation
  contextuelle), jamais une coïncidence.
- LISTE×SÉPARATEUR (scalaire STR accepté) : le join paramétré sep.join(mots) = brique_manquante. (str, str)
  reste la forme CHAÎNE×CHAÎNE (exclue ici) ; une chaîne n'accepte qu'un scalaire entier. Les primitives
  count/in/index valent pour (liste de mots, mot) -> registre. Sondes : k±1 gardé aux entiers, séparateur
  varié pour un scalaire str.

Prouve : (1) FRONTIÈRES FERMÉES — colonne_k, somme_ligne_k, somme_colonne_k, joint_par deviennent
INVENTION ; (2) REGISTRE — ligne_k (a[b]) et compte_mot (a.count(b)) restent EXISTE_DEJA ; (3) CORRECT hors
moteur ; (4) ANTI-COÏNCIDENCE — ligne ≠ colonne (matrice non symétrique) ; (5) DÉTERMINISME ;
(6) NON-RÉGRESSION — str×str -> chaîne×chaîne, str×int -> séquences, liste×int et int×int intacts.
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


# matrices NON SYMÉTRIQUES (ligne k ≠ colonne k partout), k varié.
M = [(([[3, 1], [4, 1], [5, 9]], 1),), (([[2, 7], [9, 5]], 0),), (([[8, 2], [6, 4], [1, 3]], 1),)]
MH = [(([[7, 3], [2, 8]], 1),)]
MF = [(([[1, 4], [6, 2]], 0),)]
ML = [(([[3, 1], [4, 1], [5, 9]], 1),), (([[2, 7, 6], [9, 5, 0]], 0),), (([[8, 2], [6, 4], [1, 3]], 2),)]
J = [((["a", "b", "c"], "-"),), ((["chat", "chien"], ", "),), ((["x", "y", "z", "w"], ""),)]
JH = [((["un", "deux"], " "),)]
JF = [((["p", "q"], "+"),)]

CIBLES = [
    ("colonne_k", lambda m, k: [r[k] for r in m], M, MH, MF),
    ("somme_ligne_k", lambda m, k: sum(m[k]), ML, MH, MF),
    ("somme_colonne_k", lambda m, k: sum(r[k] for r in m), M, MH, MF),
    ("joint_par", lambda l, s: s.join(l), J, JH, JF),
]

realisations = {}
for nom, ref, spec_in, held_in, frais in CIBLES:
    v = IM.examine_cible_multi(nom,
                               [((x, k), ref(x, k)) for (x, k), in spec_in],
                               [((x, k), ref(x, k)) for (x, k), in held_in])
    check(f"{nom} : frontière FERMÉE (INVENTION)", v.statut == IM.INVENTION)
    f = _fn2(v.par)
    check(f"{nom} : reproduit paires + sondes fraîches HORS moteur",
          all(f(x, k) == ref(x, k) for (x, k), in spec_in + held_in + frais))
    realisations[nom] = v.par

# REGISTRE : ligne_k = a[b], compte de mot = a.count(b) restent EXISTE_DEJA.
v = IM.examine_cible_multi("ligne_k", [((m, k), m[k]) for (m, k), in ML], [((m, k), m[k]) for (m, k), in MH])
check("ligne_k : reste EXISTE_DEJA (a[b] au registre)", v.statut == IM.EXISTE_DEJA and v.par == "a[b]")
v = IM.examine_cible_multi("compte_mot",
                           [((["a", "b", "a"], "a"), 2), ((["x", "y"], "z"), 0), ((["m", "m", "m"], "m"), 3)],
                           [((["u", "u"], "u"), 2)])
check("compte_mot (liste, mot) : reste EXISTE_DEJA (a.count(b))", v.statut == IM.EXISTE_DEJA)

# ANTI-COÏNCIDENCE : ligne ≠ colonne sur matrice non symétrique.
check("ligne k ≠ colonne k ([[3,1],[4,1],[5,9]], k=1 : ligne [4,1], colonne [1,1,9])",
      _fn2(realisations["colonne_k"])([[3, 1], [4, 1], [5, 9]], 1) == [1, 1, 9])

# DÉTERMINISME.
_ref_0 = CIBLES[0][1]
v2 = IM.examine_cible_multi("colonne_k",
                            [((m, k), _ref_0(m, k)) for (m, k), in M],
                            [((m, k), _ref_0(m, k)) for (m, k), in MH])
check("déterminisme (colonne_k : même réalisation aux deux passes)",
      v2.statut == IM.INVENTION and v2.par == realisations["colonne_k"])

# NON-RÉGRESSION : les routages voisins ne bougent pas.
v = IM.examine_cible_multi("contient",
                           [(("le chat", "chat"), True), (("aa", "b"), False), (("xyz", "y"), True)],
                           [(("bord", "or"), True)])
check("str×str : contient reste EXISTE_DEJA (chaîne×chaîne)", v.statut == IM.EXISTE_DEJA)
v = IM.examine_cible_multi("n_premiers_car",
                           [(("banane", 3), "ban"), (("chat", 1), "c"), (("portail", 4), "port")],
                           [(("mercredi", 2), "me")])
check("str×int : n_premiers_car reste INVENTION (séquence×entier)", v.statut == IM.INVENTION)
v = IM.examine_cible_multi("n_premiers",
                           [(([3, 1, 4, 1, 5], 2), [3, 1]), (([2, 7, 6], 1), [2]), (([9, 8, 5, 3], 3), [9, 8, 5])],
                           [(([1, 2, 3, 4, 5, 6], 4), [1, 2, 3, 4])])
check("liste×int : n_premiers reste INVENTION", v.statut == IM.INVENTION)
v = IM.examine_cible_multi("difference", [((7, 2), 5), ((9, 4), 5), ((3, 1), 2)], [((10, 6), 4), ((5, 5), 0)])
check("int×int : difference reste EXISTE_DEJA (a - b)", v.statut == IM.EXISTE_DEJA and v.par == "a - b")

print(f"\nvalide_invention_matrice_scalaire : {ok}/{total}")
assert ok == total
