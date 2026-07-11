"""
VALIDATION — FORME DICT×LISTE (invention_multi) : palier structurel, atome 20 — la TABLE DE TRADUCTION.

Frontière MESURÉE : restriction par liste de clés, valeurs dans l'ordre de la liste (= map-par-table
[d[e] for e in l]), retrait par liste = brique_manquante. Registre VIDE honnête ; templates {D}/{L}
instanciés selon l'ordre observé ((dict, liste) ou (liste, dict) — même classe).

Méthode SOUND : labels par fonctions de référence, listes de clés dans un ORDRE ≠ ordre du dict (l'ordre de
sortie suit la LISTE), clés répétées dans la liste (traduction ≠ restriction), held-out séparé, re-vérif
HORS moteur ; sondes = liste renversée, clé listée retirée du dict, valeur perturbée, clé hors liste ajoutée.

Prouve : (1) FRONTIÈRES FERMÉES — restriction_par_liste, retrait_par_liste, traduction AVEC DÉFAUT (spec à
clé absente, leçon PBE) deviennent INVENTION ; (2) AMBIGU HONNÊTE STRUCTUREL — la traduction STRICTE (toutes
clés présentes au spec) est indécidable face à la variante get -> AMBIGU avec sonde discriminante (même
situation prouvée qu'à l'atome 9 pour la colonne) ; (3) ORDRE — la sortie suit l'ordre de la LISTE ;
(4) CORRECT hors moteur ; (5) DÉTERMINISME ; (6) NON-RÉGRESSION — dict×scalaire, liste-de-dicts×clé,
int×int intacts.
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


# listes de clés dans un ordre ≠ ordre du dict ; une liste avec RÉPÉTITION (traduction ≠ restriction).
DL = [(({"a": 3, "b": 1, "c": 5}, ["c", "a"]),), (({"x": 5, "y": 2}, ["y"]),), (({"m": 7, "n": 4, "o": 0}, ["o", "m"]),)]
DLH = [(({"u": 6, "v": 1}, ["v", "u"]),)]
DLF = [(({"p": 2, "q": 8}, ["q", "p"]),)]
# traduction avec RÉPÉTITION + clé ABSENTE (épingle la variante get, les 2 branches du filtre).
TR = [((["a", "b", "a"], {"a": 1, "b": 2}),), ((["x", "w"], {"x": 9, "z": 0}),), ((["m", "n", "m"], {"m": 4, "n": 6}),)]
TRH = [((["u", "q", "u"], {"u": 7, "v": 8}),)]
TRF = [((["r", "r", "s"], {"r": 3}),)]

CIBLES = [
    ("restriction_par_liste", lambda d, l: {k: d[k] for k in l}, DL, DLH, DLF, True),
    ("retrait_par_liste", lambda d, l: {k: v for k, v in d.items() if k not in l}, DL, DLH, DLF, True),
    ("traduit_avec_defaut", lambda l, d: [d.get(e, 0) for e in l], TR, TRH, TRF, False),
]

realisations = {}
for nom, ref, spec_in, held_in, frais, dict_premier in CIBLES:
    v = IM.examine_cible_multi(nom,
                               [((x, y), ref(x, y)) for (x, y), in spec_in],
                               [((x, y), ref(x, y)) for (x, y), in held_in])
    check(f"{nom} : frontière FERMÉE (INVENTION)", v.statut == IM.INVENTION)
    f = _fn2(v.par)
    check(f"{nom} : reproduit paires + sondes fraîches HORS moteur",
          all(f(x if dict_premier else list(x), list(y) if dict_premier else dict(y)) == ref(x, y)
              for (x, y), in spec_in + held_in + frais))
    realisations[nom] = v.par

# AMBIGU HONNÊTE : traduction STRICTE (toutes clés présentes) vs get — indécidable par I/O pur.
_ref_s = lambda l, d: [d[e] for e in l]
TS = [((["a", "b", "a"], {"a": 1, "b": 2}),), ((["x"], {"x": 9, "z": 0}),), ((["m", "n"], {"m": 4, "n": 6}),)]
v = IM.examine_cible_multi("traduit_strict",
                           [((l, d), _ref_s(l, d)) for (l, d), in TS],
                           [((["u", "v", "u"], {"u": 7, "v": 8}), [7, 8, 7])])
check("traduction stricte : AMBIGU honnête (indécidable par I/O pur) avec sonde",
      v.statut == IM.AMBIGU and v.sonde is not None)

# ORDRE : la sortie suit l'ordre de la LISTE, pas celui du dict.
check("restriction suit l'ordre de la liste ({a,b,c}, ['c','a'] -> {'c':5,'a':3})",
      list(_fn2(realisations["restriction_par_liste"])({"a": 3, "b": 1, "c": 5}, ["c", "a"]).items())
      == [("c", 5), ("a", 3)])

# DÉTERMINISME.
_ref_0 = CIBLES[0][1]
v2 = IM.examine_cible_multi("restriction_par_liste",
                            [((d, l), _ref_0(d, l)) for (d, l), in DL],
                            [((d, l), _ref_0(d, l)) for (d, l), in DLH])
check("déterminisme (restriction : même réalisation aux deux passes)",
      v2.statut == IM.INVENTION and v2.par == realisations["restriction_par_liste"])

# NON-RÉGRESSION.
v = IM.examine_cible_multi("retire_cle",
                           [(({"a": 3, "b": 1}, "a"), {"b": 1}), (({"x": 5, "z": 9}, "z"), {"x": 5}),
                            (({"m": 7, "n": 4}, "n"), {"m": 7})],
                           [(({"u": 6, "v": 1}, "v"), {"u": 6})])
check("dict×scalaire : retire_cle reste INVENTION", v.statut == IM.INVENTION)
v = IM.examine_cible_multi("somme_colonne",
                           [(([{"n": 3, "p": 1}, {"n": 7, "p": 2}], "n"), 10),
                            (([{"a": 5, "n": 0}, {"n": 4, "a": 1}], "n"), 4)],
                           [(([{"n": 6}, {"n": 2}], "n"), 8)])
check("liste-de-dicts×clé : somme_colonne reste INVENTION", v.statut == IM.INVENTION)
v = IM.examine_cible_multi("difference", [((7, 2), 5), ((9, 4), 5), ((3, 1), 2)], [((10, 6), 4), ((5, 5), 0)])
check("int×int : difference reste EXISTE_DEJA (a - b)", v.statut == IM.EXISTE_DEJA and v.par == "a - b")

print(f"\nvalide_invention_dict_liste : {ok}/{total}")
assert ok == total
