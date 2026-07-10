"""SIMPLIFICATION BOOLÉENNE — minimisation EXACTE somme-de-produits par QUINE-McCLUSKEY, FAUX=0 (B-NEC).

`algebre_boole` ÉVALUE et teste tautologie/équivalence, mais ne MINIMISE rien. Ce module fournit la
MINIMISATION exacte et déterministe. Contrairement aux tableaux de Karnaugh (procédé graphique, faillible
à la main), l'algorithme de Quine-McCluskey est un THÉORÈME algorithmique : il énumère TOUS les implicants
premiers par fusion itérative des termes différant d'un seul bit, puis en sélectionne une couverture
minimale (implicants premiers ESSENTIELS d'abord, puis recherche exhaustive du reste).

MÉCANISME (exact, déterministe) :
  • (a) `minterms(table)` / `depuis_expression(expr, variables)` : les minterms (indices où la fonction vaut 1).
  • (b) `impliquants_premiers(minterms, n_vars)` : fusion itérative -> ensemble des implicants premiers.
  • (c) `couverture_minimale(impliquants, minterms)` : essentiels + couverture exacte du reste par recherche
        exhaustive (le problème est NP-difficile : n_vars <= 8 BORNÉ, au-delà ValueError — budget honnête et DIT).
  • (d) `minimise(expr, variables)` -> chaîne somme-de-produits minimale.
  • (e) VÉRIFICATION INTERNE (FAUX=0) : la forme minimisée est comparée à l'originale sur les 2ⁿ valuations par
        `algebre_boole.equivalent` (chemin de code INDÉPENDANT) ; toute divergence -> RuntimeError (jamais rendu).
  • (f) `nombre_litteraux(expr)` : compte les littéraux (montre le gain).

POSTURE FAUX=0 : un résultat prouvé équivalent, ou une abstention explicite. Jamais une forme « plausible ».
Le faux négatif (abstenir/RuntimeError) est toléré ; le faux positif (rendre une forme non équivalente) est INTERDIT.

GARANTIES (vérifiées en adverse par `valide_simplification_booleenne.py`) :
  - bool / str / flottant / NaN / inf en indice de minterm ou n_vars  -> ValueError ;
  - table de longueur non-puissance-de-2, entrées hors {0,1}          -> ValueError ;
  - minterm hors [0, 2ⁿ)                                              -> ValueError ;
  - n_vars > 8                                                        -> ValueError (budget exhaustif borné) ;
  - variable de l'expression absente de `variables`                  -> ValueError (variable inconnue) ;
  - expression tautologique -> '1' ; contradiction -> '0' ;
  - forme minimisée NON équivalente à l'originale                    -> RuntimeError (garde FAUX=0) ;
  - déterministe ; PUR ; stdlib uniquement (re, itertools) + `algebre_boole` (évaluation indépendante).
"""
from __future__ import annotations

import re
from itertools import combinations

import algebre_boole

SOURCE = "algorithme de Quine-McCluskey (McCluskey 1956 ; Quine 1952) — minimisation exacte des fonctions booléennes"

MAX_VARS = 8  # budget honnête : la couverture exacte est NP-difficile, on borne strictement n_vars.


def _cle(patron: tuple):
    """Clé de tri déterministe pour un patron mêlant 0/1 (int) et '-' (str)."""
    return tuple(str(c) for c in patron)


# ── helpers de validation ────────────────────────────────────────────────────────────────────────────────────────
def _est_entier(x) -> bool:
    """True ssi x est un int authentique (les bool sont REFUSÉS : True n'est pas 1)."""
    return isinstance(x, int) and not isinstance(x, bool)


def _exige_n_vars(n_vars) -> int:
    if not _est_entier(n_vars) or n_vars < 0:
        raise ValueError("n_vars invalide : un entier >= 0 est requis")
    if n_vars > MAX_VARS:
        raise ValueError(f"n_vars = {n_vars} > {MAX_VARS} : hors budget exhaustif (abstention structurelle)")
    return n_vars


def _exige_minterms(minterms, n_vars: int) -> list[int]:
    if not isinstance(minterms, (list, tuple, set, frozenset)):
        raise ValueError("minterms invalide : liste/tuple/ensemble d'entiers requis")
    borne = 1 << n_vars
    vus = set()
    for m in minterms:
        if not _est_entier(m):
            raise ValueError(f"minterm invalide : entier attendu, reçu {m!r}")
        if not (0 <= m < borne):
            raise ValueError(f"minterm {m} hors du domaine [0, {borne})")
        vus.add(m)
    return sorted(vus)


def _exige_variables(variables) -> list[str]:
    if not isinstance(variables, (list, tuple)):
        raise ValueError("variables invalide : liste/tuple de noms requis")
    noms = list(variables)
    for v in noms:
        if not isinstance(v, str) or not re.fullmatch(r"[a-zA-Z][a-zA-Z0-9_]*", v):
            raise ValueError(f"nom de variable invalide : {v!r}")
    if len(set(noms)) != len(noms):
        raise ValueError("variables invalide : noms dupliqués")
    _exige_n_vars(len(noms))
    return noms


# ── (a) MINTERMS ─────────────────────────────────────────────────────────────────────────────────────────────────
def minterms(table) -> list[int]:
    """Indices (minterms) où la table de vérité vaut 1.

    `table` = séquence de 2ⁿ entrées dans {0,1} (bool REFUSÉ), indexée par le minterm (0..2ⁿ−1).
    Longueur non-puissance-de-2 -> ValueError ; entrée hors {0,1} -> ValueError."""
    if not isinstance(table, (list, tuple)):
        raise ValueError("table invalide : liste/tuple de 0/1 requis")
    n = len(table)
    if n < 1 or (n & (n - 1)) != 0:
        raise ValueError("table invalide : la longueur doit être une puissance de 2 (2ⁿ lignes)")
    out = []
    for i, v in enumerate(table):
        if not _est_entier(v) or v not in (0, 1):
            raise ValueError(f"entrée de table invalide à l'indice {i} : 0 ou 1 attendu, reçu {v!r}")
        if v == 1:
            out.append(i)
    return out


def _valuation(m: int, n_vars: int) -> tuple[int, ...]:
    """Bits du minterm m, variable 0 = bit de poids fort (MSB)."""
    return tuple((m >> (n_vars - 1 - k)) & 1 for k in range(n_vars))


def depuis_expression(expr: str, variables) -> list[int]:
    """Minterms d'une expression booléenne sur l'ordre `variables` (réutilise `algebre_boole.evalue`).

    Variable de l'expression absente de `variables` -> ValueError (variable inconnue)."""
    noms = _exige_variables(variables)
    presentes = set(algebre_boole.variables(expr))  # valide aussi la syntaxe
    inconnues = presentes - set(noms)
    if inconnues:
        raise ValueError(f"variable inconnue (absente de variables) : {sorted(inconnues)}")
    n = len(noms)
    out = []
    for m in range(1 << n):
        bits = _valuation(m, n)
        env = {noms[k]: bool(bits[k]) for k in range(n)}
        if algebre_boole.evalue(expr, env):
            out.append(m)
    return out


# ── (b) IMPLICANTS PREMIERS (fusion itérative) ───────────────────────────────────────────────────────────────────
def _fusion(a: tuple, b: tuple):
    """Fusionne deux implicants s'ils ont les tirets aux mêmes places et diffèrent d'exactement UN bit."""
    diff = -1
    for k in range(len(a)):
        if a[k] != b[k]:
            if a[k] == "-" or b[k] == "-":
                return None  # un tiret face à un bit : non fusionnable
            if diff != -1:
                return None  # plus d'un bit de différence
            diff = k
    if diff == -1:
        return None  # identiques
    m = list(a)
    m[diff] = "-"
    return tuple(m)


def impliquants_premiers(minterms, n_vars: int) -> list[tuple]:
    """Ensemble des implicants premiers (patrons de longueur n_vars sur {0,1,'-'}), par fusion itérative.

    n_vars > 8 -> ValueError. Chaque implicant premier est un terme maximal (aucune fusion supplémentaire)."""
    n_vars = _exige_n_vars(n_vars)
    ms = _exige_minterms(minterms, n_vars)
    if not ms:
        return []
    courant = {_valuation(m, n_vars) for m in ms}
    premiers: set[tuple] = set()
    while courant:
        utilises: set[tuple] = set()
        suivant: set[tuple] = set()
        termes = sorted(courant, key=_cle)
        for i in range(len(termes)):
            for j in range(i + 1, len(termes)):
                f = _fusion(termes[i], termes[j])
                if f is not None:
                    suivant.add(f)
                    utilises.add(termes[i])
                    utilises.add(termes[j])
        for t in courant:
            if t not in utilises:
                premiers.add(t)
        courant = suivant
    return sorted(premiers, key=_cle)


# ── (c) COUVERTURE MINIMALE ──────────────────────────────────────────────────────────────────────────────────────
def _couvre(pi: tuple, m: int, n_vars: int) -> bool:
    bits = _valuation(m, n_vars)
    for k in range(n_vars):
        if pi[k] != "-" and pi[k] != bits[k]:
            return False
    return True


def _litteraux_patron(pi: tuple) -> int:
    return sum(1 for c in pi if c != "-")


def couverture_minimale(impliquants, minterms) -> list[tuple]:
    """Couverture minimale des `minterms` par les `impliquants` premiers.

    Sélectionne d'abord les implicants ESSENTIELS (minterm couvert par un seul), puis résout le reste par
    recherche EXHAUSTIVE (minimum de termes ; à nombre de termes égal, minimum de littéraux — déterministe).
    Renvoie la liste (triée) des patrons choisis. minterm non couvrable par les impliquants -> RuntimeError."""
    if not isinstance(impliquants, (list, tuple, set, frozenset)):
        raise ValueError("impliquants invalide : collection de patrons requise")
    pis = sorted(set(tuple(p) for p in impliquants), key=_cle)
    if pis:
        n_vars = len(pis[0])
        for p in pis:
            if len(p) != n_vars or any(c not in (0, 1, "-") for c in p):
                raise ValueError(f"patron d'implicant invalide : {p!r}")
        _exige_n_vars(n_vars)
        ms = _exige_minterms(minterms, n_vars)
    else:
        ms = list(minterms) if isinstance(minterms, (list, tuple, set, frozenset)) else None
        if ms:
            raise RuntimeError("aucun implicant fourni mais des minterms à couvrir")
        return []
    if not ms:
        return []

    cov = {p: frozenset(m for m in ms if _couvre(p, m, n_vars)) for p in pis}
    for m in ms:
        if not any(m in cov[p] for p in pis):
            raise RuntimeError(f"minterm {m} non couvrable par les implicants fournis")

    # implicants premiers essentiels : minterm couvert par un seul patron.
    essentiels: list[tuple] = []
    vus_ess: set[tuple] = set()
    for m in ms:
        couvrants = [p for p in pis if m in cov[p]]
        if len(couvrants) == 1 and couvrants[0] not in vus_ess:
            vus_ess.add(couvrants[0])
            essentiels.append(couvrants[0])
    couverts: set[int] = set()
    for p in essentiels:
        couverts |= cov[p]
    reste = set(ms) - couverts
    if not reste:
        return sorted(essentiels, key=_cle)

    # recherche exhaustive : plus petit nombre de patrons couvrant le reste ; départage par littéraux.
    utiles = [p for p in pis if p not in vus_ess and (cov[p] & reste)]
    meilleur = None
    for taille in range(1, len(utiles) + 1):
        meilleur_lit = None
        for combo in combinations(utiles, taille):
            u: set[int] = set()
            for p in combo:
                u |= cov[p] & reste
            if u >= reste:
                lit = sum(_litteraux_patron(p) for p in combo)
                if meilleur_lit is None or lit < meilleur_lit:
                    meilleur_lit = lit
                    meilleur = combo
        if meilleur is not None:
            break
    if meilleur is None:
        raise RuntimeError("couverture du reste impossible (incohérence interne)")
    return sorted(essentiels + list(meilleur), key=_cle)


# ── (d) MINIMISE + (e) VÉRIFICATION INTERNE ──────────────────────────────────────────────────────────────────────
def _patron_vers_terme(pi: tuple, noms: list[str]) -> str:
    parts = []
    for k, val in enumerate(pi):
        if val == "-":
            continue
        parts.append(noms[k] if val == 1 else "~" + noms[k])
    return " & ".join(parts) if parts else "1"


def minimise(expr: str, variables) -> str:
    """Forme somme-de-produits MINIMALE de `expr` sur l'ordre `variables`, en chaîne.

    Tautologie -> '1' ; contradiction -> '0' ; variable inconnue -> ValueError ; n_vars > 8 -> ValueError.
    GARDE FAUX=0 : le résultat est comparé à l'original sur les 2ⁿ valuations par `algebre_boole.equivalent`
    (chemin indépendant) ; toute divergence lève RuntimeError plutôt que de rendre une forme fausse."""
    noms = _exige_variables(variables)
    ms = depuis_expression(expr, noms)
    n = len(noms)
    total = 1 << n
    if len(ms) == 0:
        resultat = "0"
    elif len(ms) == total:
        resultat = "1"
    else:
        pis = impliquants_premiers(ms, n)
        choisis = couverture_minimale(pis, ms)
        termes = sorted(_patron_vers_terme(p, noms) for p in choisis)
        resultat = " | ".join(termes)
    # (e) VÉRIFICATION INTERNE — chemin de code INDÉPENDANT (algebre_boole).
    if not algebre_boole.equivalent(expr, resultat):
        raise RuntimeError(
            f"garde FAUX=0 violée : la minimisation {resultat!r} n'est PAS équivalente à {expr!r}"
        )
    return resultat


# ── (f) NOMBRE DE LITTÉRAUX ──────────────────────────────────────────────────────────────────────────────────────
def nombre_litteraux(expr: str) -> int:
    """Nombre d'occurrences de littéraux (variables) dans l'expression. Sert à mesurer le gain.

    Les constantes 0/1 ne sont pas des littéraux. Expression mal formée -> ValueError (via algebre_boole)."""
    algebre_boole.variables(expr)  # valide la syntaxe (lève ValueError si mal formé)
    # après validation, tout identifiant [a-zA-Z][a-zA-Z0-9_]* est une variable (les constantes sont 0/1).
    return len(re.findall(r"[a-zA-Z][a-zA-Z0-9_]*", expr))


if __name__ == "__main__":
    print("a & b | a & ~b  ->", minimise("a & b | a & ~b", ["a", "b"]))
    print("a | a & b       ->", minimise("a | a & b", ["a", "b"]))
    print("~(a & b)        ->", minimise("~(a & b)", ["a", "b"]))
    print("a & ~a          ->", minimise("a & ~a", ["a"]))
    print("a | ~a          ->", minimise("a | ~a", ["a"]))
    print("minterms {0,1,2,5,6,7} ->", couverture_minimale(
        impliquants_premiers([0, 1, 2, 5, 6, 7], 3), [0, 1, 2, 5, 6, 7]))
