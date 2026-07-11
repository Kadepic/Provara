"""
MOTEUR D'INVENTION MULTI-ARGUMENT (chantier FORGE — cap multi-arg, 2026-07-12) : franchit le palier mono→binaire.

`moteur_invention.examine_cible` tranche des cibles MONO-argument f(x). Toute une classe d'inventions vit à
PLUSIEURS arguments : f(a, b) = combinaison de deux entrées (arithmétique, distance, moyenne, sommes de carrés,
théorie des nombres…). Ce module ajoute `examine_cible_multi` — chemin SÉPARÉ (zéro impact sur le mono-arg, la
non-régression du moteur mono reste intacte) avec les MÊMES gardes de soundness que le mono-arg (cohérence,
EXISTE_DEJA, unicité comportementale sur sondes, juge held-out en subprocess, nouveauté) → FAUX=0 préservé.

SYMÉTRIE (commutativité, le piège du multi-arg — cf. littérature synthèse) : a+b ≡ b+a sont IDENTIQUES sur
toute sonde → jamais une fausse ambiguïté ; mais a−b ≠ b−a divergent sur une sonde ASYMÉTRIQUE (a≠b). Les
sondes incluent donc le SWAP (b, a) et des paires asymétriques → l'ordre des arguments est discriminé, sound.

RUNGS couverts : arité 2 (binaire) et arité 3 (ternaire), chacun avec son registre (EXISTANT_BINAIRE /
EXISTANT_TERNAIRE), son vocabulaire de recombinaison et ses sondes — PATRON REPRODUCTIBLE (ajouter une arité =
ajouter un registre + un générateur + des sondes, sans toucher aux autres). Une arité non couverte tombe
honnêtement en BRIQUE_MANQUANTE.
"""
from __future__ import annotations

from auto_invention_ouverte import LIM
from juge import juge
from moteur_invention import (AMBIGU, BRIQUE_MANQUANTE, EXISTE_DEJA, INCOHERENT, INVENTION, Verdict)

# Registre BINAIRE : capacités connues à deux arguments entiers (la nouveauté se mesure CONTRE lui).
EXISTANT_BINAIRE: dict[str, str] = {
    "somme": "a + b",
    "difference": "a - b",
    "produit": "a * b",
    "maximum": "max(a, b)",
    "minimum": "min(a, b)",
    "distance": "abs(a - b)",
    "quotient": "a // b",
    "reste": "a % b",
    "puissance": "a ** b",
    "pgcd": "__import__('math').gcd(a, b)",
    "ppcm": "__import__('math').lcm(a, b)",
    "moyenne_basse": "(a + b) // 2",
}

# Vocabulaire de recombinaison binaire : combineurs sur transformations unaires de chaque argument. Curé et
# BORNÉ (unaires × unaires × combineurs) — assez pour les fonctions binaires canoniques, sans les aimants à
# coïncidences (pas d'affine a+k·b généralisé). La soundness vient des gardes, pas de la petitesse du vocab.
_UNAIRE = ["{v}", "abs({v})", "-{v}"]
_COMBINE = ["{pa} + {pb}", "{pa} - {pb}", "{pa} * {pb}", "max({pa}, {pb})", "min({pa}, {pb})",
            "abs({pa} - {pb})", "{pa} // {pb}", "{pa} % {pb}", "{pa} ** {pb}",
            # bit-à-bit (frontière mesurée : xor/and/or ; sémantique exacte, pas d'aimant à coïncidences).
            "{pa} ^ {pb}", "{pa} & {pb}", "{pa} | {pb}"]
_BASE_SUPPL = ["b - a", "b // a", "b % a", "b ** a", "a * a + b * b", "a * a - b * b",
               "a * b + a + b", "__import__('math').gcd(a, b)"]

# FORME DE TYPE LISTE×SCALAIRE (palier structurel 2026-07-12) : l'arité 2 HÉTÉROGÈNE — un argument-STRUCTURE
# (liste) + un paramètre scalaire (entier). Frontière MESURÉE : n_premiers, kieme_plus_grand, compte_superieurs,
# rotation restaient brique_manquante (le vocabulaire binaire est scalaire pur). MÊME PATRON que les arités
# (un registre + un générateur + des sondes), routé par FORME DE TYPE détectée sur TOUS les exemples — le
# chemin entier×entier ne bouge pas. C'est la classe DeepCoder des opérateurs de premier ordre (take/drop/
# access/count paramétrés). Templates {L}/{K} : instanciés selon l'ordre observé (liste, k) ou (k, liste) —
# l'ordre des arguments est une donnée du spec, pas une convention.
_LS_REGISTRE: dict[str, str] = {
    "compte_occurrences": "{L}.count({K})",
    "appartient": "{K} in {L}",
    "element_a_l_indice": "{L}[{K}]",
    "premier_indice": "{L}.index({K})",
}
# Générateur borné, sémantique EXACTE (pas d'aimant à coïncidences arithmétiques) : tranches des deux bords,
# k-ième trié, rotations, comptages/filtres vs seuil, map paramétré, paquets de taille k.
_LS_OPS = [
    "{L}[:{K}]", "{L}[{K}:]", "{L}[-{K}:]", "{L}[:-{K}]",
    "sorted({L})[-{K}]", "sorted({L})[{K} - 1]",
    "sorted({L})[:{K}]", "sorted({L})[-{K}:]",
    "{L}[{K}:] + {L}[:{K}]", "{L}[-{K}:] + {L}[:-{K}]",
    "sum(1 for _e in {L} if _e > {K})", "sum(1 for _e in {L} if _e < {K})",
    "sum(1 for _e in {L} if _e >= {K})",
    "[_e for _e in {L} if _e > {K}]", "[_e for _e in {L} if _e < {K}]",
    "[_e for _e in {L} if _e != {K}]",
    "[_e + {K} for _e in {L}]", "[_e * {K} for _e in {L}]",
    "[{L}[_i:_i + {K}] for _i in range(0, len({L}), {K})]",
    # AGG∘TRANCHE (frontière MESURÉE après le 1er lot : somme_k_plus_grands & co = brique_manquante) — la
    # classe canonique top-k (sum/max/min d'une tranche brute ou triée). EXCLUES les identités déguisées
    # max(sorted[-k:]) ≡ max et min(sorted[:k]) ≡ min (k-invariantes, jamais une capacité neuve — même esprit
    # que le filtre identité de composition_filtree).
    "sum({L}[:{K}])", "sum({L}[{K}:])", "sum(sorted({L})[:{K}])", "sum(sorted({L})[-{K}:])",
    "max({L}[:{K}])", "max({L}[{K}:])", "max(sorted({L})[:{K}])",
    "min({L}[:{K}])", "min({L}[{K}:])", "min(sorted({L})[-{K}:])",
    # MATRICE×ENTIER (atome 16, frontière mesurée : colonne_k / agrégats ligne-colonne = brique_manquante ;
    # la ligne m[k] était déjà au registre). Sur liste PLATE d'entiers ces ops crashent (int non itérable)
    # -> validation contextuelle, jamais une coïncidence.
    "[_r[{K}] for _r in {L}]",                                            # colonne k
    "sum({L}[{K}])", "max({L}[{K}])", "min({L}[{K}])",                    # agrégats de la ligne k
    "sum(_r[{K}] for _r in {L})", "max(_r[{K}] for _r in {L})",           # agrégats de la colonne k
    "min(_r[{K}] for _r in {L})",
    # LISTE×SÉPARATEUR (atome 16, frontière mesurée : join paramétré = brique_manquante). Scalaire str.
    "{K}.join({L})",
]


# FORME DE TYPE DICT×SCALAIRE (2e forme hétérogène, même patron) : un dict + une clé OU un seuil scalaire.
# Frontière MESURÉE : valeur_de_cle, retrait de clé, get-avec-défaut, clés/comptes par seuil sur les VALEURS =
# brique_manquante. Un scalaire ENTIER peut être clé OU seuil : les DEUX vocabulaires sont émis, les sondes
# discriminent (spec faible -> AMBIGU honnête). Sorties ordonnées par sorted() : déterminisme.
_DS_REGISTRE: dict[str, str] = {
    "valeur_de_cle": "{L}[{K}]",
    "appartient_cles": "{K} in {L}",
}
_DS_OPS = [
    "{L}.get({K}, 0)",                                                    # lookup avec défaut (clé absente -> 0)
    "{{_k2: _v for _k2, _v in {L}.items() if _k2 != {K}}}",               # retrait de la clé
    "sorted(_k2 for _k2, _v in {L}.items() if _v > {K})",                 # clés dont la valeur dépasse le seuil
    "sorted(_k2 for _k2, _v in {L}.items() if _v < {K})",
    "sum(1 for _v in {L}.values() if _v > {K})",                          # comptes par seuil sur les valeurs
    "sum(1 for _v in {L}.values() if _v < {K})",
    "sum(1 for _v in {L}.values() if _v >= {K})",
]


def _forme_dict_scalaire(toutes):
    """(dict, clé/seuil str|int) ou l'ordre inverse sur TOUS les exemples -> (var_dict, var_scalaire), sinon None."""
    def _scal(v):
        return isinstance(v, str) or (isinstance(v, int) and not isinstance(v, bool))
    if all(len(a) == 2 and isinstance(a[0], dict) and _scal(a[1]) for a, _ in toutes):
        return ("a", "b")
    if all(len(a) == 2 and isinstance(a[1], dict) and _scal(a[0]) for a, _ in toutes):
        return ("b", "a")
    return None


def _registre_dict_scalaire(forme) -> dict[str, str]:
    L, K = forme
    return {n: t.format(L=L, K=K) for n, t in _DS_REGISTRE.items()}


def _candidats_dict_scalaire(exemples, forme) -> list[str]:
    L, K = forme
    cands: set[str] = set(_registre_dict_scalaire(forme).values())
    cands.update(t.format(L=L, K=K) for t in _DS_OPS)
    return [e for e in cands if _reproduit_multi(_callable_multi(e, "f", ["a", "b"]), exemples)]


def _sondes_dict_scalaire(exemples, forme) -> list[tuple]:
    """Sondes de FORME : dict SANS la clé (discrimine d[k] vs get vs appartenance), valeur À la clé perturbée
    (discrimine lecture de valeur vs structure), AUTRE clé du dict, seuil±1 pour les entiers (> vs >=)."""
    scal_premier = forme == ("b", "a")
    out = []
    for args, _ in exemples:
        d, k = (args[1], args[0]) if scal_premier else (args[0], args[1])

        def mk(dd, kk):
            return (kk, dd) if scal_premier else (dd, kk)
        out.append(mk(dict(d), k))
        out.append(mk({k2: v for k2, v in d.items() if k2 != k}, k))       # clé retirée
        if k in d:
            out.append(mk({**d, k: (d[k] + 1 if isinstance(d[k], int) else d[k])}, k))
        autres = sorted((k2 for k2 in d if k2 != k), key=repr)
        if autres:
            out.append(mk(dict(d), autres[0]))                             # autre clé observée
        if isinstance(k, int) and not isinstance(k, bool):
            out.append(mk(dict(d), k + 1))
            out.append(mk(dict(d), k - 1))
    seen, res = set(), []
    for s in out:
        c = repr(s)
        if c not in seen:
            seen.add(c)
            res.append(s)
    return res


# FORME DE TYPE LISTE×LISTE (atome 10 du palier structurel) : deux séquences HOMOGÈNES en deux ARGUMENTS
# (vs etend_paire_listes mono qui reçoit [A, B] en UN argument). Frontière MESURÉE : intersection triée,
# différence, zip/produit scalaire = brique_manquante — et la mesure a montré le PIÈGE de la forme : sans
# routage, les capacités SCALAIRES tournent sur les listes (max(a, b) lexicographique a reproduit une
# différence sans chevauchement). Registre honnête = les capacités scalaires VALIDES sur listes (concat,
# max/min lexicographiques) ; sondes de forme = SWAP + injection de CHEVAUCHEMENT (tue les coïncidences
# sans-recouvrement) + renversements. Classe canonique : set-ops + ZipWith (DSL DeepCoder).
_LL_REGISTRE: dict[str, str] = {
    "concatenation": "a + b",
}
_LL_OPS = [
    # max/min lexicographiques en CANDIDATS (pas au registre) : au registre ils court-circuiteraient en
    # EXISTE_DEJA un spec faible (différence sans recouvrement reproduite par max) ; en candidats, l'unicité
    # sur sondes tranche -> AMBIGU honnête avec sonde discriminante (le spec faible est renvoyé à l'usager).
    "max(a, b)", "min(a, b)",
    "sorted(set(a) & set(b))", "sorted(set(a) | set(b))", "sorted(set(a) - set(b))",
    "[_e for _e in a if _e in b]", "[_e for _e in a if _e not in b]",     # variantes PRÉSERVANT l'ordre
    "[_x + _y for _x, _y in zip(a, b)]", "[_x - _y for _x, _y in zip(a, b)]",
    "[_x * _y for _x, _y in zip(a, b)]", "[max(_x, _y) for _x, _y in zip(a, b)]",
    "[min(_x, _y) for _x, _y in zip(a, b)]",
    "sum(_x * _y for _x, _y in zip(a, b))",                               # produit scalaire
    "sum(1 for _x, _y in zip(a, b) if _x == _y)",                         # positions d'accord
]


def _forme_liste_liste(toutes):
    """(liste de scalaires, liste de scalaires) sur TOUS les exemples -> True, sinon None. Symétrique :
    pas d'ordre L/K — l'asymétrie éventuelle de la cible est discriminée par la sonde SWAP."""
    def _plate(v):
        return (isinstance(v, list)
                and all(not isinstance(e, (list, dict, set, tuple)) for e in v))
    if all(len(x) == 2 and _plate(x[0]) and _plate(x[1]) for x, _ in toutes):
        return True
    return None


def _candidats_liste_liste(exemples) -> list[str]:
    cands: set[str] = set(_LL_REGISTRE.values()) | set(_LL_OPS)
    return [e for e in cands if _reproduit_multi(_callable_multi(e, "f", ["a", "b"]), exemples)]


def _sondes_liste_liste(exemples) -> list[tuple]:
    """Sondes de FORME : SWAP (différence/zip asymétriques), renversements (ordre interne), injection de
    CHEVAUCHEMENT (a[0] ajouté à b : sépare set-ops des coïncidences sans-recouvrement), troncature."""
    out = []
    for (x, y), _ in exemples:
        out.append((list(x), list(y)))
        out.append((list(y), list(x)))                          # SWAP
        out.append((list(reversed(x)), list(y)))
        out.append((list(x), list(reversed(y))))
        if x:
            out.append((list(x), list(y) + [x[0]]))             # chevauchement injecté
        if y:
            out.append((list(x) + [y[0]], list(y)))
        if len(y) > 1:
            out.append((list(x), list(y[:-1])))                 # longueurs inégales (zip tronque)
    seen, res = set(), []
    for s in out:
        c = repr(s)
        if c not in seen:
            seen.add(c)
            res.append(s)
    return res


# FORME DE TYPE DICT×LISTE (atome 20 du palier structurel) : un mapping + une liste de clés — la classe
# TABLE DE TRADUCTION (map-par-table [d[e] for e in l], restriction par liste, retrait par liste).
# Frontière MESURÉE : les trois = brique_manquante. Registre VIDE honnête. Templates {D}/{L} instanciés
# selon l'ordre observé ((dict, liste) ou (liste, dict) : même classe, l'ordre = donnée du spec).
_DL_OPS = [
    "[{D}[_k] for _k in {L}]",                                   # valeurs dans l'ordre / traduction par table
    "[{D}.get(_k, 0) for _k in {L}]",                            # traduction avec défaut
    "{{_k: {D}[_k] for _k in {L}}}",                             # restriction par liste (ordre de la liste)
    "{{_k: _v for _k, _v in {D}.items() if _k not in {L}}}",     # retrait des clés listées
    "[_k for _k in {L} if _k in {D}]",                           # clés de la liste présentes dans la table
]


def _forme_dict_liste(toutes):
    """(dict, liste de scalaires) ou l'ordre inverse sur TOUS les exemples -> (var_dict, var_liste), sinon None."""
    def _cles(v):
        return (isinstance(v, list)
                and all(isinstance(e, str) or (isinstance(e, int) and not isinstance(e, bool)) for e in v))
    if all(len(x) == 2 and isinstance(x[0], dict) and _cles(x[1]) for x, _ in toutes):
        return ("a", "b")
    if all(len(x) == 2 and isinstance(x[1], dict) and _cles(x[0]) for x, _ in toutes):
        return ("b", "a")
    return None


def _candidats_dict_liste(exemples, forme) -> list[str]:
    D, L = forme
    cands = {t.format(D=D, L=L) for t in _DL_OPS}
    return [e for e in cands if _reproduit_multi(_callable_multi(e, "f", ["a", "b"]), exemples)]


def _sondes_dict_liste(exemples, forme) -> list[tuple]:
    """Sondes de FORME : liste RENVERSÉE (l'ordre de sortie suit la liste), clé de la liste RETIRÉE du dict
    (d[k] vs get vs filtre), valeur perturbée, clé du dict hors liste ajoutée à la liste."""
    dict_premier = forme == ("a", "b")
    out = []
    for args, _ in exemples:
        d, l = (args[0], args[1]) if dict_premier else (args[1], args[0])

        def mk(dd, ll):
            return (dd, ll) if dict_premier else (ll, dd)
        out.append(mk(dict(d), list(l)))
        out.append(mk(dict(d), list(l)[::-1]))                  # ordre de la liste
        if l:
            k = l[0]
            out.append(mk({k2: v for k2, v in d.items() if k2 != k}, list(l)))   # clé listée retirée du dict
            if k in d and isinstance(d[k], int):
                out.append(mk({**d, k: d[k] + 1}, list(l)))
        hors = sorted((k2 for k2 in d if k2 not in l), key=repr)
        if hors:
            out.append(mk(dict(d), list(l) + [hors[0]]))        # clé du dict ajoutée à la liste
    seen, res = set(), []
    for s in out:
        c = repr(s)
        if c not in seen:
            seen.add(c)
            res.append(s)
    return res


# FORME DE TYPE MATRICE×MATRICE (atome 17 du palier structurel) : deux matrices en deux arguments.
# Frontière MESURÉE : somme élément à élément et PRODUIT MATRICIEL = brique_manquante. Registre = concat
# (a + b, listes) ; ops = arithmétique élément à élément (somme/différence/Hadamard) + produit matriciel.
# Le produit est NON COMMUTATIF -> la sonde SWAP le discrimine de la version b·a.
_MM_REGISTRE: dict[str, str] = {
    "concatenation": "a + b",
}
_MM_OPS = [
    "[[_x + _y for _x, _y in zip(_ra, _rb)] for _ra, _rb in zip(a, b)]",
    "[[_x - _y for _x, _y in zip(_ra, _rb)] for _ra, _rb in zip(a, b)]",
    "[[_x * _y for _x, _y in zip(_ra, _rb)] for _ra, _rb in zip(a, b)]",     # Hadamard
    "[[sum(a[_i][_k] * b[_k][_j] for _k in range(len(b))) for _j in range(len(b[0]))] for _i in range(len(a))]",
    "[[sum(b[_i][_k] * a[_k][_j] for _k in range(len(a))) for _j in range(len(a[0]))] for _i in range(len(b))]",
]


def _forme_matrice_matrice(toutes):
    """(matrice, matrice) — deux listes non vides de listes de scalaires — sur TOUS les exemples, sinon None."""
    def _mat(v):
        return (isinstance(v, list) and v
                and all(isinstance(r, list) and all(not isinstance(e, (list, dict, set, tuple)) for e in r)
                        for r in v))
    if all(len(x) == 2 and _mat(x[0]) and _mat(x[1]) for x, _ in toutes):
        return True
    return None


def _candidats_matrice_matrice(exemples) -> list[str]:
    cands: set[str] = set(_MM_REGISTRE.values()) | set(_MM_OPS)
    return [e for e in cands if _reproduit_multi(_callable_multi(e, "f", ["a", "b"]), exemples)]


def _sondes_matrice_matrice(exemples) -> list[tuple]:
    """Sondes de FORME : SWAP (le produit matriciel est non commutatif), lignes renversées, élément perturbé."""
    out = []
    for (x, y), _ in exemples:
        cx = [list(r) for r in x]
        cy = [list(r) for r in y]
        out.append((cx, cy))
        out.append((cy, cx))                                    # SWAP
        out.append(([list(r) for r in reversed(x)], cy))
        if y and y[0] and isinstance(y[0][0], int):
            out.append((cx, [[y[0][0] + 1] + list(y[0][1:])] + [list(r) for r in y[1:]]))
    seen, res = set(), []
    for s in out:
        c = repr(s)
        if c not in seen:
            seen.add(c)
            res.append(s)
    return res


# FORME DE TYPE DICT×DICT (atome 13 du palier structurel) : deux mappings en deux arguments. Frontière
# MESURÉE : clés communes, soustraction/restriction = brique_manquante — et la fusion était servie par le
# vocab SCALAIRE (a | b, union dict exacte) : une fois la forme routée, ce chemin disparaît -> la fusion
# passe au REGISTRE (primitive du langage, les 2 ordres : la priorité de fusion est une donnée du spec).
_DD_REGISTRE: dict[str, str] = {
    "fusion": "{**a, **b}",
    "fusion_inverse": "{**b, **a}",
}
_DD_OPS = [
    "sorted(set(a) & set(b))", "sorted(set(a) | set(b))", "sorted(set(a) - set(b))",   # clés
    "{_k: _v for _k, _v in a.items() if _k not in b}",                                 # soustraction
    "{_k: _v for _k, _v in a.items() if _k in b}",                                     # restriction
    "{_k: a[_k] + b[_k] for _k in sorted(set(a) & set(b))}",                           # somme sur clés communes
]


def _forme_dict_dict(toutes):
    """(dict, dict) sur TOUS les exemples -> True, sinon None. Le SWAP discrimine l'asymétrie."""
    if all(len(x) == 2 and isinstance(x[0], dict) and isinstance(x[1], dict) for x, _ in toutes):
        return True
    return None


def _candidats_dict_dict(exemples) -> list[str]:
    cands: set[str] = set(_DD_REGISTRE.values()) | set(_DD_OPS)
    return [e for e in cands if _reproduit_multi(_callable_multi(e, "f", ["a", "b"]), exemples)]


def _sondes_dict_dict(exemples) -> list[tuple]:
    """Sondes de FORME : SWAP (fusion/soustraction asymétriques), clé commune RETIRÉE de b, clé de a copiée
    dans b avec une AUTRE valeur (discrimine l'ordre de fusion), valeur commune perturbée."""
    out = []
    for (x, y), _ in exemples:
        out.append((dict(x), dict(y)))
        out.append((dict(y), dict(x)))                          # SWAP
        communes = sorted(set(x) & set(y), key=repr)
        if communes:
            k = communes[0]
            out.append((dict(x), {k2: v for k2, v in y.items() if k2 != k}))
            if isinstance(y.get(k), int):
                out.append((dict(x), {**y, k: y[k] + 1}))       # valeur commune perturbée
        propres = sorted(set(x) - set(y), key=repr)
        if propres:
            k = propres[0]
            out.append((dict(x), {**y, k: (x[k] + 1 if isinstance(x[k], int) else x[k])}))   # conflit de fusion
    seen, res = set(), []
    for s in out:
        c = repr(s)
        if c not in seen:
            seen.add(c)
            res.append(s)
    return res


# FORME DE TYPE CHAÎNE×CHAÎNE (atome 12 du palier structurel) : deux chaînes en deux arguments — la classe
# FlashFill/BlinkFill des transformations de paires de chaînes. Frontière MESURÉE : préfixe commun (canonique,
# l'edit distance le saute en linéaire), concat avec séparateur, Hamming, mots communs = brique_manquante.
# Registre = primitives du langage (concat, appartenance, comptage, position) ; sondes = SWAP + renversement
# + préfixe forcé + cas égalité.
_CC_REGISTRE: dict[str, str] = {
    "concatenation": "a + b",
    "contient": "b in a",
    "compte_sous_chaine": "a.count(b)",
    "position_sous_chaine": "a.find(b)",
}
_CC_OPS = [
    "a[:max(_i for _i in range(min(len(a), len(b)) + 1) if a[:_i] == b[:_i])]",   # préfixe commun
    "a[len(a) - max(_i for _i in range(min(len(a), len(b)) + 1) if a[len(a) - _i:] == b[len(b) - _i:]):]",  # suffixe commun
    "a + ' ' + b",                                                                 # concat avec séparateur canonique
    "b + ' ' + a",
    "a.replace(b, '')",                                                            # retrait des occurrences
    "sum(1 for _x, _y in zip(a, b) if _x != _y)",                                  # distance de Hamming (préfixe zip)
    "a.startswith(b)", "a.endswith(b)",
    "' '.join(sorted(set(a.split()) & set(b.split())))",                           # mots communs (triés)
]


def _forme_chaine_chaine(toutes):
    """(chaîne, chaîne) sur TOUS les exemples -> True, sinon None. Le SWAP discrimine l'asymétrie."""
    if all(len(x) == 2 and isinstance(x[0], str) and isinstance(x[1], str) for x, _ in toutes):
        return True
    return None


def _candidats_chaine_chaine(exemples) -> list[str]:
    cands: set[str] = set(_CC_REGISTRE.values()) | set(_CC_OPS)
    return [e for e in cands if _reproduit_multi(_callable_multi(e, "f", ["a", "b"]), exemples)]


def _sondes_chaine_chaine(exemples) -> list[tuple]:
    """Sondes de FORME : SWAP (asymétrie), renversements, b devenu PRÉFIXE de a (sépare préfixe-commun de
    contient/startswith), cas d'ÉGALITÉ a==a."""
    out = []
    for (x, y), _ in exemples:
        out.append((x, y))
        out.append((y, x))                                      # SWAP
        out.append((x[::-1], y))
        out.append((x, y[::-1]))
        out.append((y + x, y))                                  # b préfixe de a
        out.append((x, x))                                      # égalité
    seen, res = set(), []
    for s in out:
        c = repr(s)
        if c not in seen:
            seen.add(c)
            res.append(s)
    return res


# FORME DE TYPE TABLE×TABLE (atome 11 du palier structurel) : la JOINTURE — deux tables (listes
# d'enregistrements) en deux arguments. Referme l'algèbre relationnelle de base (colonne ✓, sélection ✓,
# groupby/pivot/dégroupage ✓, jointure ✗->✓). La CLÉ de jointure est DÉCOUVERTE dans les données (champs
# présents dans TOUS les enregistrements des DEUX tables, patron etend_synthese : constantes dirigées par
# les exemples) puis cuite en littéral dans le candidat — les sondes (retrait d'une correspondance, valeur
# de clé perturbée, doublon de clé = multiplicité) discriminent la bonne clé et la bonne variante.
_TT_REGISTRE: dict[str, str] = {
    "concatenation": "a + b",
}
_TT_OPS_PAR_CLE = [
    "[{{**_da, **_db}} for _da in a for _db in b if _da[{K}] == _db[{K}]]",      # jointure interne
    "sorted({{_d[{K}] for _d in a}} & {{_d[{K}] for _d in b}})",                 # clés communes
    "[_da for _da in a if _da[{K}] in {{_d[{K}] for _d in b}}]",                 # semi-jointure
    "[_da for _da in a if _da[{K}] not in {{_d[{K}] for _d in b}}]",             # anti-jointure
]


def _forme_table_table(toutes):
    """(liste non vide de dicts, liste non vide de dicts) sur TOUS les exemples -> True, sinon None."""
    def _table(v):
        return isinstance(v, list) and v and all(isinstance(d, dict) for d in v)
    if all(len(x) == 2 and _table(x[0]) and _table(x[1]) for x, _ in toutes):
        return True
    return None


def _cles_communes_tables(exemples) -> list[str]:
    """Champs présents dans TOUS les enregistrements des DEUX tables de TOUS les exemples (clés candidates)."""
    communes = None
    for (x, y), _ in exemples:
        cles = set(x[0]) if x else set()
        for d in x:
            cles &= set(d)
        for d in y:
            cles &= set(d)
        communes = cles if communes is None else communes & cles
    return sorted(communes or (), key=repr)


def _candidats_table_table(exemples) -> list[str]:
    cands: set[str] = set(_TT_REGISTRE.values())
    for k in _cles_communes_tables(exemples):
        for t in _TT_OPS_PAR_CLE:
            cands.add(t.format(K=repr(k)))
    return [e for e in cands if _reproduit_multi(_callable_multi(e, "f", ["a", "b"]), exemples)]


def _sondes_table_table(exemples) -> list[tuple]:
    """Sondes de FORME : SWAP (ordre de fusion/colonnes), tables renversées, RETRAIT d'un enregistrement de b
    (change la jointure), valeur de clé PERTURBÉE (casse une correspondance), DOUBLON de clé (multiplicité)."""
    cles = _cles_communes_tables(exemples)
    out = []
    for (x, y), _ in exemples:
        cx = [dict(d) for d in x]
        cy = [dict(d) for d in y]
        out.append((cx, cy))
        out.append((cy, cx))                                    # SWAP
        out.append((list(reversed(cx)), cy))
        if len(cy) > 1:
            out.append((cx, cy[:-1]))                           # retrait d'un enregistrement
        if cy:
            out.append((cx, cy + [dict(cy[0])]))                # doublon (multiplicité de jointure)
        for k in cles[:1]:
            if cy and isinstance(cy[0].get(k), int):
                out.append((cx, [{**cy[0], k: cy[0][k] + 1}] + cy[1:]))   # correspondance cassée
    seen, res = set(), []
    for s in out:
        c = repr(s)
        if c not in seen:
            seen.add(c)
            res.append(s)
    return res


# FORME DE TYPE LISTE-DE-DICTS×CLÉ (3e forme hétérogène, atome 9 du palier structurel) : la COLONNE
# relationnelle — une table (liste d'enregistrements) + un champ PARAMÈTRE. Frontière MESURÉE : colonne =
# brique_manquante (etend_liste_dicts mono découvre le champ dans les DONNÉES ; ici le champ est un ARGUMENT —
# croisement multi-arg × structures). Détectée AVANT liste×scalaire (forme plus spécifique : une clé entière
# matcherait (liste, int) à tort). Registre VIDE honnête : rien ne servait cette classe avant.
_LD_OPS = [
    "[_d[{K}] for _d in {L}]",                       # colonne (projection du champ)
    "[_d.get({K}, 0) for _d in {L}]",                # colonne avec défaut (champ absent -> 0)
    "sum(_d[{K}] for _d in {L})",                    # agrégats de colonne
    "max(_d[{K}] for _d in {L})",
    "min(_d[{K}] for _d in {L})",
    "sorted(_d[{K}] for _d in {L})",                 # colonne triée
    "[_d for _d in {L} if {K} in _d]",               # sélection des enregistrements possédant le champ
]


def _forme_liste_dicts(toutes):
    """(liste NON VIDE de dicts, clé str|int) ou l'ordre inverse sur TOUS les exemples, sinon None."""
    def _cle(v):
        return isinstance(v, str) or (isinstance(v, int) and not isinstance(v, bool))
    def _table(v):
        return isinstance(v, list) and v and all(isinstance(d, dict) for d in v)
    if all(len(a) == 2 and _table(a[0]) and _cle(a[1]) for a, _ in toutes):
        return ("a", "b")
    if all(len(a) == 2 and _table(a[1]) and _cle(a[0]) for a, _ in toutes):
        return ("b", "a")
    return None


def _candidats_liste_dicts(exemples, forme) -> list[str]:
    L, K = forme
    cands = {t.format(L=L, K=K) for t in _LD_OPS}
    return [e for e in cands if _reproduit_multi(_callable_multi(e, "f", ["a", "b"]), exemples)]


def _sondes_liste_dicts(exemples, forme) -> list[tuple]:
    """Sondes de FORME : table RENVERSÉE (l'ordre des enregistrements), champ RETIRÉ du 1er enregistrement
    (discrimine d[k] vs get vs sélection), valeur du champ perturbée, autre champ commun observé."""
    scal_premier = forme == ("b", "a")
    out = []
    for args, _ in exemples:
        x, k = (args[1], args[0]) if scal_premier else (args[0], args[1])

        def mk(xx, kk):
            return (kk, xx) if scal_premier else (xx, kk)
        out.append(mk([dict(d) for d in x], k))
        out.append(mk([dict(d) for d in reversed(x)], k))
        if x and k in x[0]:
            prive = [{k2: v for k2, v in x[0].items() if k2 != k}] + [dict(d) for d in x[1:]]
            out.append(mk(prive, k))
            if isinstance(x[0][k], int) and not isinstance(x[0][k], bool):
                out.append(mk([{**x[0], k: x[0][k] + 1}] + [dict(d) for d in x[1:]], k))
        communs = sorted((k2 for k2 in x[0] if k2 != k and all(k2 in d for d in x)), key=repr) if x else []
        if communs:
            out.append(mk([dict(d) for d in x], communs[0]))
    seen, res = set(), []
    for s in out:
        c = repr(s)
        if c not in seen:
            seen.add(c)
            res.append(s)
    return res


def _forme_liste_scalaire(toutes):
    """(SÉQUENCE, entier) ou (entier, SÉQUENCE) sur TOUS les exemples -> (var_seq, var_scalaire), sinon None.
    Séquence = liste OU chaîne (atome 12 : les tranches/rotations/paquets valent verbatim pour str — mesuré
    n_premiers_car/rotation_chaine = brique_manquante) ; les ops inapplicables à l'un des types (comparaisons
    _e > k sur str, sum) crashent à la validation contextuelle -> filtrées, jamais un faux."""
    def _est_int(v):
        return isinstance(v, int) and not isinstance(v, bool)
    def _scal(v):
        return _est_int(v) or isinstance(v, str)
    def _seq(v):
        return isinstance(v, (list, str))
    # (str, str) est la forme CHAÎNE×CHAÎNE, pas séquence×scalaire : une LISTE accepte un scalaire str
    # (join, count, in) mais une chaîne n'accepte qu'un entier (tranches/rotations).
    if all(len(a) == 2 and _seq(a[0]) and _scal(a[1])
           and not (isinstance(a[0], str) and isinstance(a[1], str)) for a, _ in toutes):
        return ("a", "b")
    if all(len(a) == 2 and _scal(a[0]) and _seq(a[1])
           and not (isinstance(a[1], str) and isinstance(a[0], str)) for a, _ in toutes):
        return ("b", "a")
    return None


def _registre_liste_scalaire(forme) -> dict[str, str]:
    L, K = forme
    return {n: t.format(L=L, K=K) for n, t in _LS_REGISTRE.items()}


def _candidats_liste_scalaire(exemples, forme) -> list[str]:
    """Expressions liste×scalaire qui REPRODUISENT les exemples. Bornée, dédupliquée ; soundness par les gardes."""
    L, K = forme
    cands: set[str] = set(_registre_liste_scalaire(forme).values())
    cands.update(t.format(L=L, K=K) for t in _LS_OPS)
    return [e for e in cands if _reproduit_multi(_callable_multi(e, "f", ["a", "b"]), exemples)]


def _sondes_liste_scalaire(exemples, forme) -> list[tuple]:
    """Sondes de FORME : liste RENVERSÉE (discrimine take vs sorted-take), liste TRIÉE, k±1 DANS le domaine,
    doublon ajouté (discrimine comptage vs appartenance). Pas de SWAP : types invalides -> ERR uniforme sur
    tous les candidats de la forme, aucune discrimination à y gagner."""
    scal_premier = forme == ("b", "a")
    out = []
    for args, _ in exemples:
        x, k = (args[1], args[0]) if scal_premier else (args[0], args[1])

        def mk(xx, kk):
            return (kk, xx) if scal_premier else (xx, kk)
        est_str = isinstance(x, str)                            # sondes fidèles au TYPE (séquence = liste ou str)
        copie = (lambda s: s) if est_str else list
        out.append(mk(copie(x), k))
        out.append(mk(x[::-1], k))
        out.append(mk("".join(sorted(x)) if est_str else sorted(x), k))
        if isinstance(k, int) and not isinstance(k, bool):
            if 1 <= k + 1 <= len(x):
                out.append(mk(copie(x), k + 1))
            if k - 1 >= 1:
                out.append(mk(copie(x), k - 1))
        else:                                                   # scalaire str (séparateur/élément) : le varier
            out.append(mk(copie(x), k + "·"))
        if x:
            out.append(mk(x + x[0] if est_str else list(x) + [x[0]], k))
    seen, res = set(), []
    for s in out:
        c = repr(s)
        if c not in seen:
            seen.add(c)
            res.append(s)
    return res


# FORME DE TYPE SÉQUENCE×INT×INT (atome 14 du palier structurel) : première forme STRUCTURÉE à l'arité 3 —
# la TRANCHE À DEUX BORNES a[b:c] (liste ou chaîne) et ses agrégats. Frontière MESURÉE : tranche et
# somme_tranche = brique_manquante à l'arité 3 (le vocabulaire ternaire est scalaire pur). Registre =
# la tranche elle-même (primitive du langage, comme a[b] ou d[k]) ; ops = agrégats ∘ tranche. Séquence en
# POSITION 0 (le cas canonique mesuré) — autre position -> chemin scalaire, brique_manquante honnête.
_T3_REGISTRE: dict[str, str] = {
    "tranche": "a[b:c]",
    # élément (ligne, colonne) d'une matrice — chaîne de primitives (atome 21) ; sur liste PLATE, a[b] est
    # un scalaire -> [c] crashe -> jamais servie par coïncidence (validation contextuelle).
    "element_ligne_colonne": "a[b][c]",
}
_T3_OPS = [
    "sum(a[b:c])", "max(a[b:c])", "min(a[b:c])",
    "a[c:b]",                                    # bornes inversées (l'ordre des bornes = donnée du spec)
    "a[c][b]",                                   # élément (colonne, ligne) — l'ordre = donnée du spec
]

# FORMES TERNAIRES HÉTÉROGÈNES SUPPLÉMENTAIRES (atome 21) — mesurées brique_manquante :
# (table, clé, valeur) = la SÉLECTION WHERE relationnelle ; (str, séparateur, indice) = segment de découpe.
_TCV_OPS = [
    "[_d for _d in a if _d[b] == c]",            # WHERE k = v
    "[_d for _d in a if _d[b] != c]",            # WHERE k ≠ v
    "sum(1 for _d in a if _d[b] == c)",          # COUNT WHERE
]
_SSI_OPS = [
    "a.split(b)[c]",                             # c-ième segment après découpe
    "b.join(a.split(b)[:c])",                    # c premiers segments rejoints
]


def _forme_table_cle_valeur(toutes):
    def _scal(v):
        return isinstance(v, str) or (isinstance(v, int) and not isinstance(v, bool))
    def _table(v):
        return isinstance(v, list) and v and all(isinstance(d, dict) for d in v)
    if all(len(x) == 3 and _table(x[0]) and _scal(x[1]) and _scal(x[2]) for x, _ in toutes):
        return True
    return None


def _forme_str_str_int(toutes):
    if all(len(x) == 3 and isinstance(x[0], str) and isinstance(x[1], str)
           and isinstance(x[2], int) and not isinstance(x[2], bool) for x, _ in toutes):
        return True
    return None


def _forme_seq_int_int(toutes):
    """(séquence, entier, entier) sur TOUS les exemples -> True, sinon None."""
    def _est_int(v):
        return isinstance(v, int) and not isinstance(v, bool)
    if all(len(x) == 3 and isinstance(x[0], (list, str)) and _est_int(x[1]) and _est_int(x[2])
           for x, _ in toutes):
        return True
    return None


def _candidats_seq_int_int(exemples) -> list[str]:
    cands: set[str] = set(_T3_REGISTRE.values()) | set(_T3_OPS)
    return [e for e in cands if _reproduit_multi(_callable_multi(e, "f", ["a", "b", "c"]), exemples)]


def _sondes_seq_int_int(exemples) -> list[tuple]:
    """Sondes de FORME : séquence renversée/triée (tranche brute vs triée), bornes ±1 DANS le domaine,
    bornes ÉCHANGÉES (tranche vide -> discrimine a[b:c] de a[c:b])."""
    out = []
    for (x, i, j), _ in exemples:
        est_str = isinstance(x, str)
        copie = (lambda s: s) if est_str else list
        out.append((copie(x), i, j))
        out.append((x[::-1], i, j))
        out.append(("".join(sorted(x)) if est_str else sorted(x), i, j))
        out.append((copie(x), j, i))                            # bornes échangées
        if i + 1 <= j:
            out.append((copie(x), i + 1, j))
        if j - 1 >= i:
            out.append((copie(x), i, j - 1))
    seen, res = set(), []
    for s in out:
        c = repr(s)
        if c not in seen:
            seen.add(c)
            res.append(s)
    return res


# FORMES TERNAIRES HÉTÉROGÈNES PRIMITIVES (atome 18 du palier structurel) : remplace (str, motif, substitut)
# et get-avec-défaut (dict, clé, défaut) — mesurées brique_manquante, ce sont des PRIMITIVES du langage ->
# registres ; les variantes d'ORDRE en candidats (les sondes-permutations de l'arité 3 discriminent).
_SSS_REGISTRE: dict[str, str] = {
    "remplace": "a.replace(b, c)",
}
_SSS_OPS = ["a.replace(c, b)", "b.replace(a, c)", "c.join(a.split(b))"]
_DCD_REGISTRE: dict[str, str] = {
    "valeur_ou_defaut": "a.get(b, c)",
}
_DCD_OPS = ["a.get(c, b)"]


def _forme_str_str_str(toutes):
    if all(len(x) == 3 and all(isinstance(v, str) for v in x) for x, _ in toutes):
        return True
    return None


def _forme_dict_cle_defaut(toutes):
    def _scal(v):
        return isinstance(v, str) or (isinstance(v, int) and not isinstance(v, bool))
    if all(len(x) == 3 and isinstance(x[0], dict) and _scal(x[1]) and _scal(x[2]) for x, _ in toutes):
        return True
    return None


def _candidats_ternaires_het(exemples, registre, ops) -> list[str]:
    cands: set[str] = set(registre.values()) | set(ops)
    return [e for e in cands if _reproduit_multi(_callable_multi(e, "f", ["a", "b", "c"]), exemples)]


# Registre TERNAIRE : capacités connues à trois arguments entiers (rung suivant, patron identique au binaire).
EXISTANT_TERNAIRE: dict[str, str] = {
    "somme3": "a + b + c",
    "produit3": "a * b * c",
    "maximum3": "max(a, b, c)",
    "minimum3": "min(a, b, c)",
    "moyenne3_basse": "(a + b + c) // 3",
    "mediane3": "a + b + c - max(a, b, c) - min(a, b, c)",
    "amplitude3": "max(a, b, c) - min(a, b, c)",
}
# Combineurs binaires pour l'ASSEMBLAGE ternaire en arbre g2(g1(x, y), z).
_COMBINE3 = ["{x} + {y}", "{x} - {y}", "{x} * {y}", "max({x}, {y})", "min({x}, {y})"]

_REGISTRES = {2: EXISTANT_BINAIRE, 3: EXISTANT_TERNAIRE}


def _params(arite: int) -> list[str]:
    return ["a", "b", "c", "d", "e"][:arite]


def _callable_multi(expr: str, nom: str, params: list[str]):
    src = (expr if expr.lstrip().startswith("def ")
           else f"def {nom}({', '.join(params)}):\n    return {expr}\n")
    ns: dict = {}
    try:
        exec(src, ns)
        return ns.get(nom)
    except Exception:
        return None


def _reproduit_multi(f, paires) -> bool:
    if f is None:
        return False
    for args, o in paires:
        try:
            r = f(*args)
            # égalité TYPE-EXACTE sur bool (même règle que le mono-arg : 1 n'est pas True).
            if r != o or isinstance(r, bool) != isinstance(o, bool):
                return False
        except Exception:
            return False
    return True


def _sig_multi(f, sondes) -> list[str]:
    out = []
    for s in sondes:
        try:
            out.append(repr(f(*s)))
        except Exception:
            out.append("ERR")
    return out


def _candidats_binaires(exemples) -> list[str]:
    """Expressions binaires qui REPRODUISENT les exemples (validation contextuelle). Bornée, dédupliquée."""
    cands: set[str] = set(EXISTANT_BINAIRE.values()) | set(_BASE_SUPPL)
    for ta in _UNAIRE:
        pa = ta.format(v="a")
        for tb in _UNAIRE:
            pb = tb.format(v="b")
            for c in _COMBINE:
                cands.add(c.format(pa=pa, pb=pb))
    ok = []
    for e in cands:
        if _reproduit_multi(_callable_multi(e, "f", ["a", "b"]), exemples):
            ok.append(e)
    return ok


def _candidats_ternaires(exemples) -> list[str]:
    """Expressions ternaires qui REPRODUISENT les exemples. Base curée + ASSEMBLAGE en arbre : deux vars
    combinées puis avec la troisième, g2(g1(x, y), z), sur toutes les affectations (a,b,c). Bornée (6 perms
    × 5 × 5 ≈ 150), dédupliquée. Soundness par les gardes d'examine_cible_multi."""
    import itertools
    cands: set[str] = set(EXISTANT_TERNAIRE.values())
    cands.update(["a * a + b * b + c * c", "abs(a - b) + abs(b - c) + abs(a - c)"])
    vs = ["a", "b", "c"]
    for i, j, k in itertools.permutations(range(3)):
        x, y, z = vs[i], vs[j], vs[k]
        for g1 in _COMBINE3:
            inner = "(" + g1.format(x=x, y=y) + ")"
            for g2 in _COMBINE3:
                cands.add(g2.format(x=inner, y=z))
    ok = []
    for e in cands:
        if _reproduit_multi(_callable_multi(e, "f", ["a", "b", "c"]), exemples):
            ok.append(e)
    return ok


def _sondes_ternaires(exemples) -> list[tuple]:
    """Sondes de stress pour l'arité 3 : permutations (swaps adjacents, rotation, renversement — discriminent
    l'ORDRE des trois arguments) + perturbations +1 par position DANS le domaine (signe gardé). Générique."""
    ints = [v for args, _ in exemples for v in args if isinstance(v, int) and not isinstance(v, bool)]
    signe = any(v < 0 for v in ints)
    out = []
    for args, _ in exemples:
        if len(args) != 3:
            continue
        args = tuple(args)
        out.append(args)
        for i in range(len(args) - 1):                          # swaps adjacents
            sw = list(args)
            sw[i], sw[i + 1] = sw[i + 1], sw[i]
            out.append(tuple(sw))
        out.append(args[1:] + args[:1])                         # rotation
        out.append(args[::-1])                                  # renversement
        if all(isinstance(v, int) and not isinstance(v, bool) for v in args):
            for i in range(len(args)):
                p = list(args)
                p[i] += 1
                out.append(tuple(p))
            if signe:
                out.append(tuple(-v for v in args))
    seen, res = set(), []
    for s in out:
        k = repr(s)
        if k not in seen:
            seen.add(k)
            res.append(s)
    return res


def _sondes_binaires(exemples) -> list[tuple]:
    """Sondes de stress dérivées des exemples : SWAP (discrimine le non-commutatif) + perturbations DANS le
    domaine observé (signe gardé comme en mono-arg). Pas de sortie inventée : seulement des entrées."""
    ints = [v for args, _ in exemples for v in args if isinstance(v, int) and not isinstance(v, bool)]
    signe = any(v < 0 for v in ints)
    out = []
    for args, _ in exemples:
        if len(args) != 2:
            continue
        a, b = args
        out.append((a, b))
        out.append((b, a))                          # SWAP : a−b vs b−a divergent ici
        if isinstance(a, int) and isinstance(b, int) and not isinstance(a, bool) and not isinstance(b, bool):
            out.append((a + 1, b))
            out.append((a, b + 1))
            out.append((a + 1, b + 2))              # paire asymétrique
            if signe:
                out.append((-a, b))
    seen, res = set(), []
    for s in out:
        k = repr(s)
        if k not in seen:
            seen.add(k)
            res.append(s)
    return res


def _asserts_multi(nom: str, paires) -> str:
    from demande import _asserts
    return _asserts(nom, [(tuple(args), o) for args, o in paires])


def examine_cible_multi(nom: str, exemples, exemples_held, existant: dict | None = None) -> Verdict:
    """Tranche une cible MULTI-ARGUMENT en EXISTE_DEJA / INVENTION / AMBIGU / BRIQUE_MANQUANTE / INCOHERENT.
    `exemples`/`exemples_held` = listes de (args, sortie) où args est un tuple/liste d'arguments. Mêmes garanties
    de soundness que le mono-arg. `existant` = registre à utiliser (défaut : le registre de l'arité observée —
    binaire (2) ou ternaire (3))."""
    exemples = [(tuple(a), o) for a, o in exemples]
    held = [(tuple(a), o) for a, o in (exemples_held or [])]
    toutes = exemples + held
    if not toutes:
        return Verdict(INCOHERENT, nom, justification="aucun exemple")

    arites = {len(a) for a, _ in toutes}
    if len(arites) != 1:
        return Verdict(INCOHERENT, nom, justification="arité incohérente entre les exemples")
    arite = arites.pop()
    params = _params(arite)
    # FORMES DE TYPE (palier structurel) : arité 2 hétérogène liste-de-dicts×clé (la plus spécifique,
    # détectée en premier), liste×scalaire ou dict×scalaire -> registre/candidats/sondes de la forme ;
    # sinon chemins scalaires INCHANGÉS. `existant` de l'appelant prioritaire.
    forme_tt = _forme_table_table(toutes) if arite == 2 else None
    forme_ld = _forme_liste_dicts(toutes) if arite == 2 and not forme_tt else None
    forme_ls = _forme_liste_scalaire(toutes) if arite == 2 and not (forme_tt or forme_ld) else None
    forme_ds = _forme_dict_scalaire(toutes) if arite == 2 and not (forme_tt or forme_ld or forme_ls) else None
    forme_ll = _forme_liste_liste(toutes) if arite == 2 and not (forme_tt or forme_ld or forme_ls or forme_ds) else None
    forme_cc = _forme_chaine_chaine(toutes) if arite == 2 and not (forme_tt or forme_ld or forme_ls or forme_ds or forme_ll) else None
    forme_dd = _forme_dict_dict(toutes) if arite == 2 and not (forme_tt or forme_ld or forme_ls or forme_ds or forme_ll or forme_cc) else None
    forme_mm = _forme_matrice_matrice(toutes) if arite == 2 and not (forme_tt or forme_ld or forme_ls or forme_ds or forme_ll or forme_cc or forme_dd) else None
    forme_dl = _forme_dict_liste(toutes) if arite == 2 and not (forme_tt or forme_ld or forme_ls or forme_ds or forme_ll or forme_cc or forme_dd or forme_mm) else None
    forme_t3 = _forme_seq_int_int(toutes) if arite == 3 else None
    forme_sss = _forme_str_str_str(toutes) if arite == 3 and not forme_t3 else None
    forme_dcd = _forme_dict_cle_defaut(toutes) if arite == 3 and not (forme_t3 or forme_sss) else None
    forme_tcv = _forme_table_cle_valeur(toutes) if arite == 3 and not (forme_t3 or forme_sss or forme_dcd) else None
    forme_ssi = _forme_str_str_int(toutes) if arite == 3 and not (forme_t3 or forme_sss or forme_dcd or forme_tcv) else None
    if existant is None:
        existant = (dict(_TT_REGISTRE) if forme_tt
                    else {} if forme_ld                  # registre VIDE honnête (rien ne servait la classe)
                    else _registre_liste_scalaire(forme_ls) if forme_ls
                    else _registre_dict_scalaire(forme_ds) if forme_ds
                    else dict(_LL_REGISTRE) if forme_ll
                    else dict(_CC_REGISTRE) if forme_cc
                    else dict(_DD_REGISTRE) if forme_dd
                    else dict(_MM_REGISTRE) if forme_mm
                    else {} if forme_dl
                    else dict(_T3_REGISTRE) if forme_t3
                    else dict(_SSS_REGISTRE) if forme_sss
                    else dict(_DCD_REGISTRE) if forme_dcd
                    else {} if forme_tcv or forme_ssi
                    else _REGISTRES.get(arite, {}))

    # 0) COHÉRENCE : même entrée -> deux sorties = contradiction.
    vus: dict = {}
    for a, o in toutes:
        k = repr(a)
        if k in vus and vus[k] != o:
            return Verdict(INCOHERENT, nom, justification="deux sorties différentes pour la même entrée")
        vus[k] = o

    sondes = (_sondes_table_table(toutes) if forme_tt
              else _sondes_liste_dicts(toutes, forme_ld) if forme_ld
              else _sondes_liste_scalaire(toutes, forme_ls) if forme_ls
              else _sondes_dict_scalaire(toutes, forme_ds) if forme_ds
              else _sondes_liste_liste(toutes) if forme_ll
              else _sondes_chaine_chaine(toutes) if forme_cc
              else _sondes_dict_dict(toutes) if forme_dd
              else _sondes_matrice_matrice(toutes) if forme_mm
              else _sondes_dict_liste(toutes, forme_dl) if forme_dl
              else _sondes_binaires(toutes)) if arite == 2 \
        else (_sondes_seq_int_int(toutes) if forme_t3 else _sondes_ternaires(toutes)) if arite == 3 \
        else [tuple(a) for a, _ in toutes]

    # 1) EXISTE DÉJÀ : une capacité connue reproduit la cible ?
    for capa, expr in existant.items():
        if _reproduit_multi(_callable_multi(expr, nom, params), toutes):
            return Verdict(EXISTE_DEJA, nom, par=expr, proche_de=capa,
                           justification="déjà couvert par l'inventaire binaire existant")

    # 2) RÉALISABLE par recombinaison ? (arité 2 = binaire, arité 3 = ternaire ; patron reproductible)
    candidats = (_candidats_table_table(toutes) if forme_tt
                 else _candidats_liste_dicts(toutes, forme_ld) if forme_ld
                 else _candidats_liste_scalaire(toutes, forme_ls) if forme_ls
                 else _candidats_dict_scalaire(toutes, forme_ds) if forme_ds
                 else _candidats_liste_liste(toutes) if forme_ll
                 else _candidats_chaine_chaine(toutes) if forme_cc
                 else _candidats_dict_dict(toutes) if forme_dd
                 else _candidats_matrice_matrice(toutes) if forme_mm
                 else _candidats_dict_liste(toutes, forme_dl) if forme_dl
                 else _candidats_binaires(toutes)) \
        if arite == 2 else (_candidats_seq_int_int(toutes) if forme_t3
                            else _candidats_ternaires_het(toutes, _SSS_REGISTRE, _SSS_OPS) if forme_sss
                            else _candidats_ternaires_het(toutes, _DCD_REGISTRE, _DCD_OPS) if forme_dcd
                            else _candidats_ternaires_het(toutes, {}, _TCV_OPS) if forme_tcv
                            else _candidats_ternaires_het(toutes, {}, _SSI_OPS) if forme_ssi
                            else _candidats_ternaires(toutes)) if arite == 3 else []
    if candidats:
        sigs = {e: _sig_multi(_callable_multi(e, nom, params), sondes) for e in candidats}
        for j, s in enumerate(sondes):
            if len({sigs[e][j] for e in candidats}) > 1:
                return Verdict(AMBIGU, nom, sonde=s,
                               justification="plusieurs réalisations binaires distinctes satisfont le spec")
        S = min(candidats, key=len)                 # Occam
        code = f"def {nom}({', '.join(params)}):\n    return {S}\n"
        if held and not juge(code, _asserts_multi(nom, held), LIM).passe:
            return Verdict(BRIQUE_MANQUANTE, nom, justification="réalisation non confirmée par le juge sur le held-out")
        sig_S = _sig_multi(_callable_multi(S, nom, params), sondes)
        for capa, expr in existant.items():
            g = _callable_multi(expr, nom, params)
            if g is not None and _sig_multi(g, sondes) == sig_S and _reproduit_multi(g, toutes):
                return Verdict(EXISTE_DEJA, nom, par=expr, proche_de=capa,
                               justification="réalisable mais équivalent à une capacité binaire existante (non nouveau)")
        return Verdict(INVENTION, nom, par=S,
                       justification="recombinaison binaire unique sous le spec, vérifiée (held-out), comportement nouveau")

    # 3) Aucune recombinaison binaire connue -> FRONTIÈRE.
    return Verdict(BRIQUE_MANQUANTE, nom,
                   justification="cohérente mais non réalisable par recombinaison binaire connue : un principe neuf est requis")
