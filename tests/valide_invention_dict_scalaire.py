"""
VALIDATION — FORME DICT×SCALAIRE (invention_multi) : palier structurel, atome 5 — 2e forme hétérogène.

Frontière MESURÉE (sonde 2026-07-12, après la forme liste×scalaire) : la classe (dict, clé/seuil) restait
brique_manquante ENTIÈRE — lookup avec défaut, retrait de clé, clés/comptes par seuil sur les valeurs.
Comblé par la forme DICT×SCALAIRE, MÊME PATRON (registre _DS_REGISTRE : d[k], k in d ; générateur _DS_OPS ;
sondes de forme : dict sans la clé, valeur perturbée à la clé, autre clé, seuil±1), routé par forme détectée —
chemins liste×scalaire et int×int INCHANGÉS. Un entier peut être clé OU seuil : les deux vocabulaires sont
émis, les sondes discriminent.

Méthode SOUND (leçon PBE : les filtres exigent des exemples sur les DEUX branches) : specs avec clé ABSENTE
dans un exemple (sépare get(k,0) de d[k]), valeur ÉGALE au seuil (sépare > de >=), valeurs des deux côtés du
seuil ; held-out séparé ; re-vérif HORS moteur sur sondes fraîches.

Prouve : (1) FRONTIÈRES FERMÉES — valeur_ou_zero, retire_cle, cles_valeur_superieure, nb_valeurs_superieures
(et >=) deviennent INVENTION ; (2) NOUVEAUTÉ CONTRE REGISTRE — valeur_de_cle et contient_cle restent
EXISTE_DEJA ; (3) CORRECT — re-vérif hors moteur ; (4) ANTI-COÏNCIDENCE — > vs >= séparés, retire_cle retire
LA clé ; (5) HONNÊTETÉ — cible hors vocabulaire -> BRIQUE_MANQUANTE ; (6) DÉTERMINISME ; (7) NON-RÉGRESSION
des deux autres chemins d'arité 2.
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


D = [({"a": 3, "b": 1}, "a"), ({"x": 5, "y": 2, "z": 9}, "z"), ({"m": 7, "n": 4}, "n"), ({"p": 0, "q": 8}, "p")]
D_HELD = [({"u": 6, "v": 1, "w": 3}, "v"), ({"k": 2}, "k")]
D_FRAIS = [({"r": 4, "s": 2}, "s"), ({"t": 9}, "t")]
# clé ABSENTE dans un exemple : d[k] crashe, seul le lookup avec défaut reproduit.
G = D + [({"seul": 4}, "absente")]
G_HELD = [({"u": 6}, "manque"), ({"k": 2}, "k")]
G_FRAIS = [({"r": 4}, "ailleurs"), ({"t": 9}, "t")]
# seuils : valeur ÉGALE au seuil dans le spec (sépare > de >=), valeurs des deux côtés.
S = [({"a": 3, "b": 1}, 3), ({"x": 5, "y": 2, "z": 9}, 5), ({"m": 7, "n": 4}, 4), ({"p": 0, "q": 8}, 8)]
S_HELD = [({"u": 6, "v": 1}, 3), ({"k": 2}, 2)]
S_FRAIS = [({"r": 4, "s": 2}, 4), ({"t": 9, "w": 0}, 5)]

CIBLES = [
    ("valeur_ou_zero", lambda d, k: d.get(k, 0), G, G_HELD, G_FRAIS),
    ("retire_cle", lambda d, k: {kk: v for kk, v in d.items() if kk != k}, D, D_HELD, D_FRAIS),
    ("cles_valeur_superieure", lambda d, s: sorted(k for k, v in d.items() if v > s), S, S_HELD, S_FRAIS),
    ("nb_valeurs_superieures", lambda d, s: sum(1 for v in d.values() if v > s), S, S_HELD, S_FRAIS),
    ("nb_valeurs_sup_egal", lambda d, s: sum(1 for v in d.values() if v >= s), S, S_HELD, S_FRAIS),
]

realisations = {}
for nom, ref, spec_in, held_in, frais in CIBLES:
    v = IM.examine_cible_multi(nom,
                               [((d, k), ref(d, k)) for d, k in spec_in],
                               [((d, k), ref(d, k)) for d, k in held_in])
    check(f"{nom} : frontière FERMÉE (INVENTION)", v.statut == IM.INVENTION)
    f = _fn2(v.par)
    check(f"{nom} : reproduit paires + sondes fraîches HORS moteur",
          all(f(d, k) == ref(d, k) for d, k in spec_in + held_in + frais))
    realisations[nom] = v.par

# NOUVEAUTÉ CONTRE REGISTRE : les primitives de la forme restent EXISTE_DEJA.
v = IM.examine_cible_multi("valeur_de_cle", [((d, k), d[k]) for d, k in D], [((d, k), d[k]) for d, k in D_HELD])
check("valeur_de_cle : reste EXISTE_DEJA (registre de la forme)", v.statut == IM.EXISTE_DEJA)
v = IM.examine_cible_multi("contient_cle", [((d, k), k in d) for d, k in G], [((d, k), k in d) for d, k in G_HELD])
check("contient_cle : reste EXISTE_DEJA (registre de la forme)", v.statut == IM.EXISTE_DEJA)

# ANTI-COÏNCIDENCE : > vs >= réellement séparés ; retire_cle retire LA clé.
check("> et >= séparés (seuil 4 sur {m:7, n:4} : 1 vs 2)",
      _fn2(realisations["nb_valeurs_superieures"])({"m": 7, "n": 4}, 4) == 1
      and _fn2(realisations["nb_valeurs_sup_egal"])({"m": 7, "n": 4}, 4) == 2)
check("retire_cle retire la clé demandée et garde le reste",
      _fn2(realisations["retire_cle"])({"a": 1, "b": 2, "c": 3}, "b") == {"a": 1, "c": 3})

# HONNÊTETÉ : cible HORS vocabulaire (somme des valeurs des clés ≠ k) -> BRIQUE_MANQUANTE.
_ref_hors = lambda d, k: sum(v for kk, v in d.items() if kk != k)
v = IM.examine_cible_multi("somme_valeurs_sauf_cle",
                           [((d, k), _ref_hors(d, k)) for d, k in D],
                           [((d, k), _ref_hors(d, k)) for d, k in D_HELD])
check("cible hors vocabulaire : BRIQUE_MANQUANTE honnête", v.statut == IM.BRIQUE_MANQUANTE)

# DÉTERMINISME.
_ref_rc = CIBLES[1][1]
v2 = IM.examine_cible_multi("retire_cle",
                            [((d, k), _ref_rc(d, k)) for d, k in D],
                            [((d, k), _ref_rc(d, k)) for d, k in D_HELD])
check("déterminisme (retire_cle : même réalisation aux deux passes)",
      v2.statut == IM.INVENTION and v2.par == realisations["retire_cle"])

# NON-RÉGRESSION : les deux autres chemins d'arité 2 ne bougent pas.
v = IM.examine_cible_multi("n_premiers",
                           [(([3, 1, 4, 1, 5], 2), [3, 1]), (([2, 7, 6], 1), [2]), (([9, 8, 5, 3], 3), [9, 8, 5])],
                           [(([1, 2, 3, 4, 5, 6], 4), [1, 2, 3, 4])])
check("liste×scalaire : n_premiers reste INVENTION", v.statut == IM.INVENTION)
v = IM.examine_cible_multi("difference", [((7, 2), 5), ((9, 4), 5), ((3, 1), 2)], [((10, 6), 4), ((5, 5), 0)])
check("int×int : difference reste EXISTE_DEJA (a - b)", v.statut == IM.EXISTE_DEJA and v.par == "a - b")

print(f"\nvalide_invention_dict_scalaire : {ok}/{total}")
assert ok == total
