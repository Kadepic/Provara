"""
VALIDATION — FORME LISTE×SCALAIRE (invention_multi) : palier structurel, atome 3 — l'arité 2 HÉTÉROGÈNE.

Frontière MESURÉE (sonde palier structurel 2026-07-12) : la classe ENTIÈRE des cibles (structure, paramètre)
restait brique_manquante — le vocabulaire binaire était scalaire pur (n_premiers, kieme_plus_grand,
compte_superieurs, rotation). Comblé par la forme de type LISTE×SCALAIRE : registre (_LS_REGISTRE, primitives
comptage/appartenance/accès) + générateur borné (_LS_OPS, classe DeepCoder : take/drop/access/count paramétrés)
+ sondes de forme, routés par FORME détectée sur TOUS les exemples — chemin entier×entier INCHANGÉ.

Méthode SOUND : labels par fonctions de référence, listes NON TRIÉES (take ≠ sorted-take sur chaque exemple),
seuils avec élément ÉGAL (discrimine > vs >=), k varié, held-out séparé, re-vérif HORS moteur sur sondes
fraîches ; sondes de forme = liste renversée/triée, k±1, doublon.

Prouve : (1) FRONTIÈRES FERMÉES — n_premiers, kieme_plus_grand, compte_superieurs, rotation_gauche,
paquets_de_k deviennent INVENTION ; (2) ORDRE = DONNÉE DU SPEC — (k, liste) résolu avec les variables
échangées ; (3) CORRECT — re-vérif hors moteur ; (4) NOUVEAUTÉ CONTRE REGISTRE — compte_occurrences reste
EXISTE_DEJA ; (5) HONNÊTETÉS — spec FAIBLE (listes triées) -> AMBIGU avec sonde discriminante, cible HORS
vocabulaire (somme des k plus grands) -> BRIQUE_MANQUANTE ; (6) DÉTERMINISME ; (7) NON-RÉGRESSION int×int.
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


# listes NON TRIÉES (x[:k] ≠ sorted(x)[:k] partout), k varié, doublons présents.
HB = [([3, 1, 4, 1, 5], 2), ([2, 7, 6], 1), ([9, 8, 5, 3], 3), ([4, 2, 6, 0, 1], 2)]
HB_HELD = [([1, 2, 3, 4, 5, 6], 4), ([7, 3], 1)]
HB_FRAIS = [([6, 2, 9, 1], 2), ([5, 8, 0], 1)]
# seuils : un élément ÉGAL au seuil dans le spec (discrimine > vs >=).
SEUIL = [([3, 1, 4, 4, 5], 4), ([2, 7, 6], 2), ([9, 8, 5, 3], 5), ([4, 2, 6, 0, 1], 2)]
SEUIL_HELD = [([1, 2, 3, 4, 5, 6], 3), ([7, 3], 7)]
SEUIL_FRAIS = [([5, 5, 1, 9], 5), ([2, 8], 3)]

CIBLES = [
    ("n_premiers", lambda x, k: x[:k], HB, HB_HELD, HB_FRAIS),
    ("kieme_plus_grand", lambda x, k: sorted(x)[-k], HB, HB_HELD, HB_FRAIS),
    ("compte_superieurs", lambda x, s: sum(1 for v in x if v > s), SEUIL, SEUIL_HELD, SEUIL_FRAIS),
    ("rotation_gauche", lambda x, k: x[k:] + x[:k], HB, HB_HELD, HB_FRAIS),
    ("paquets_de_k", lambda x, k: [x[i:i + k] for i in range(0, len(x), k)], HB, HB_HELD, HB_FRAIS),
]

realisations = {}
for nom, ref, spec_in, held_in, frais in CIBLES:
    spec = [((x, k), ref(x, k)) for x, k in spec_in]
    held = [((x, k), ref(x, k)) for x, k in held_in]
    v = IM.examine_cible_multi(nom, spec, held)
    check(f"{nom} : frontière FERMÉE (INVENTION)", v.statut == IM.INVENTION)
    f = _fn2(v.par)
    check(f"{nom} : reproduit paires + sondes fraîches HORS moteur",
          all(f(x, k) == ref(x, k) for x, k in spec_in + held_in + frais))
    realisations[nom] = v.par

# ORDRE = DONNÉE DU SPEC : (k, liste) résolu avec les variables échangées.
_ref_cs = lambda k, x: sum(1 for v in x if v > k)
v = IM.examine_cible_multi("compte_superieurs_inverse",
                           [((k, x), _ref_cs(k, x)) for x, k in SEUIL],
                           [((k, x), _ref_cs(k, x)) for x, k in SEUIL_HELD])
check("ordre (k, liste) : résolu (INVENTION, variables échangées)",
      v.statut == IM.INVENTION and _fn2(v.par)(3, [1, 2, 3, 4, 5, 6]) == 3)

# NOUVEAUTÉ CONTRE REGISTRE : une primitive du registre reste EXISTE_DEJA.
_ref_cnt = lambda x, k: x.count(k)
v = IM.examine_cible_multi("compte_occurrences",
                           [(([3, 1, 3, 3], 3), 3), (([2, 7, 6], 7), 1), (([4, 4], 5), 0)],
                           [(([1, 1, 2], 1), 2), (([9], 9), 1)])
check("compte_occurrences : reste EXISTE_DEJA (registre de la forme)", v.statut == IM.EXISTE_DEJA)

# HONNÊTETÉ AMBIGU : spec FAIBLE (listes TRIÉES -> take ≡ sorted-take) -> AMBIGU avec sonde discriminante.
_TRIEES = [([1, 2, 3, 4], 2), ([5, 6, 7], 1), ([0, 3, 8, 9], 3)]
v = IM.examine_cible_multi("n_premiers_spec_faible",
                           [((x, k), x[:k]) for x, k in _TRIEES],
                           [(([2, 4, 6, 8], 2), [2, 4])])
check("spec faible (listes triées) : AMBIGU honnête avec sonde discriminante",
      v.statut == IM.AMBIGU and v.sonde is not None)

# HONNÊTETÉ BRIQUE_MANQUANTE : cible HORS vocabulaire — nb d'INVERSIONS parmi les k premiers (principe
# toutes-paires O(n²), hors de la forme). NB : somme_k_plus_grands, l'ancien témoin, a été COMBLÉ par
# l'atome AGG∘tranche (la frontière se déplace) — cf. valide_invention_agg_tranche.
_ref_inv = lambda x, k: sum(1 for i in range(min(k, len(x))) for j in range(i + 1, min(k, len(x))) if x[i] > x[j])
v = IM.examine_cible_multi("nb_inversions_k_premiers",
                           [((x, k), _ref_inv(x, k)) for x, k in HB],
                           [((x, k), _ref_inv(x, k)) for x, k in HB_HELD])
check("cible hors vocabulaire : BRIQUE_MANQUANTE honnête", v.statut == IM.BRIQUE_MANQUANTE)

# DÉTERMINISME.
_ref_np = CIBLES[0][1]
v2 = IM.examine_cible_multi("n_premiers",
                            [((x, k), _ref_np(x, k)) for x, k in HB],
                            [((x, k), _ref_np(x, k)) for x, k in HB_HELD])
check("déterminisme (n_premiers : même réalisation aux deux passes)",
      v2.statut == IM.INVENTION and v2.par == realisations["n_premiers"])

# NON-RÉGRESSION : le chemin entier×entier ne bouge pas.
v = IM.examine_cible_multi("difference", [((7, 2), 5), ((9, 4), 5), ((3, 1), 2)], [((10, 6), 4), ((5, 5), 0)])
check("int×int : difference reste EXISTE_DEJA (a - b)", v.statut == IM.EXISTE_DEJA and v.par == "a - b")
v = IM.examine_cible_multi("somme_carres", [((2, 3), 13), ((1, 4), 17), ((0, 5), 25)], [((3, 3), 18), ((2, 5), 29)])
check("int×int : somme des carrés reste INVENTION", v.statut == IM.INVENTION)

print(f"\nvalide_invention_liste_scalaire : {ok}/{total}")
assert ok == total
