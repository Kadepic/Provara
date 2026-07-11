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
]


def _forme_liste_scalaire(toutes):
    """(liste, entier) ou (entier, liste) sur TOUS les exemples -> (var_liste, var_scalaire), sinon None."""
    def _est(v, t):
        return isinstance(v, t) and not isinstance(v, bool)
    if all(len(a) == 2 and _est(a[0], list) and _est(a[1], int) for a, _ in toutes):
        return ("a", "b")
    if all(len(a) == 2 and _est(a[0], int) and _est(a[1], list) for a, _ in toutes):
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
        out.append(mk(list(x), k))
        out.append(mk(list(reversed(x)), k))
        out.append(mk(sorted(x), k))
        if 1 <= k + 1 <= len(x):
            out.append(mk(list(x), k + 1))
        if k - 1 >= 1:
            out.append(mk(list(x), k - 1))
        if x:
            out.append(mk(list(x) + [x[0]], k))
    seen, res = set(), []
    for s in out:
        c = repr(s)
        if c not in seen:
            seen.add(c)
            res.append(s)
    return res


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
    # FORME DE TYPE (palier structurel) : arité 2 hétérogène liste×scalaire -> registre/candidats/sondes de la
    # forme ; sinon chemins scalaires INCHANGÉS. Un `existant` passé par l'appelant garde la priorité.
    forme_ls = _forme_liste_scalaire(toutes) if arite == 2 else None
    if existant is None:
        existant = _registre_liste_scalaire(forme_ls) if forme_ls else _REGISTRES.get(arite, {})

    # 0) COHÉRENCE : même entrée -> deux sorties = contradiction.
    vus: dict = {}
    for a, o in toutes:
        k = repr(a)
        if k in vus and vus[k] != o:
            return Verdict(INCOHERENT, nom, justification="deux sorties différentes pour la même entrée")
        vus[k] = o

    sondes = (_sondes_liste_scalaire(toutes, forme_ls) if forme_ls else _sondes_binaires(toutes)) if arite == 2 \
        else _sondes_ternaires(toutes) if arite == 3 \
        else [tuple(a) for a, _ in toutes]

    # 1) EXISTE DÉJÀ : une capacité connue reproduit la cible ?
    for capa, expr in existant.items():
        if _reproduit_multi(_callable_multi(expr, nom, params), toutes):
            return Verdict(EXISTE_DEJA, nom, par=expr, proche_de=capa,
                           justification="déjà couvert par l'inventaire binaire existant")

    # 2) RÉALISABLE par recombinaison ? (arité 2 = binaire, arité 3 = ternaire ; patron reproductible)
    candidats = (_candidats_liste_scalaire(toutes, forme_ls) if forme_ls else _candidats_binaires(toutes)) \
        if arite == 2 else _candidats_ternaires(toutes) if arite == 3 else []
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
