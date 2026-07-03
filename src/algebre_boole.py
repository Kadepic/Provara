"""ALGÈBRE DE BOOLE — évaluation EXACTE d'expressions booléennes & tables de vérité, FAUX=0 (formule/concept 2026-06-29).

Parseur (descente récursive) sur les connecteurs : NOT (~ ! ¬), AND (& * ∧), XOR (^ ⊕), OR (| + ∨), IMPL (-> →),
EQUIV (<-> ↔ =). Variables = mots [a-z]+ ; constantes 0/1. Sur les 2ⁿ affectations on calcule la table de vérité,
d'où tautologie / satisfiabilité / contradiction / équivalence — EXACT, déterministe. Abstention STRUCTURELLE :
expression mal formée -> ValueError (jamais un verdict faux).

Couvre le sujet borné « Algèbre de Boole ».
Vérifié en adverse par `valide_algebre_boole.py` (lois connues : De Morgan, tiers exclu, distributivité, modus ponens).
"""
from __future__ import annotations

import re

_TOKENS = [
    (r"\s+", None),
    (r"<->|↔|<=>", "EQUIV"),
    (r"->|→|=>", "IMPL"),
    (r"[&*∧]", "AND"),
    (r"[|+∨]", "OR"),
    (r"[\^⊕]", "XOR"),
    (r"[~!¬]", "NOT"),
    (r"=", "EQUIV"),
    (r"\(", "LP"),
    (r"\)", "RP"),
    (r"[01]", "CONST"),
    (r"[a-zA-Z][a-zA-Z0-9_]*", "VAR"),
]


def _lex(s: str):
    i, n, out = 0, len(s), []
    while i < n:
        for motif, typ in _TOKENS:
            m = re.match(motif, s[i:])
            if m:
                if typ:
                    out.append((typ, m.group(0)))
                i += m.end()
                break
        else:
            raise ValueError(f"caractère invalide en position {i}: {s[i]!r}")
    out.append(("EOF", ""))
    return out


class _Parseur:
    """Précédence (faible -> fort) : EQUIV < IMPL < OR < XOR < AND < NOT < atome."""

    def __init__(self, toks):
        self.toks = toks
        self.k = 0

    def _peek(self):
        return self.toks[self.k][0]

    def _eat(self, typ):
        if self._peek() != typ:
            raise ValueError(f"attendu {typ}, vu {self.toks[self.k]}")
        t = self.toks[self.k]
        self.k += 1
        return t

    def parse(self):
        n = self._equiv()
        if self._peek() != "EOF":
            raise ValueError(f"jeton inattendu : {self.toks[self.k]}")
        return n

    def _equiv(self):
        g = self._impl()
        while self._peek() == "EQUIV":
            self._eat("EQUIV")
            d = self._impl()
            g = ("EQUIV", g, d)
        return g

    def _impl(self):
        g = self._or()
        if self._peek() == "IMPL":          # implication = associative à droite
            self._eat("IMPL")
            d = self._impl()
            return ("IMPL", g, d)
        return g

    def _or(self):
        g = self._xor()
        while self._peek() == "OR":
            self._eat("OR")
            g = ("OR", g, self._xor())
        return g

    def _xor(self):
        g = self._and()
        while self._peek() == "XOR":
            self._eat("XOR")
            g = ("XOR", g, self._and())
        return g

    def _and(self):
        g = self._not()
        while self._peek() == "AND":
            self._eat("AND")
            g = ("AND", g, self._not())
        return g

    def _not(self):
        if self._peek() == "NOT":
            self._eat("NOT")
            return ("NOT", self._not())
        return self._atome()

    def _atome(self):
        t = self._peek()
        if t == "LP":
            self._eat("LP")
            n = self._equiv()
            self._eat("RP")
            return n
        if t == "CONST":
            return ("CONST", self._eat("CONST")[1] == "1")
        if t == "VAR":
            return ("VAR", self._eat("VAR")[1])
        raise ValueError(f"atome attendu, vu {self.toks[self.k]}")


def _arbre(expr: str):
    if not isinstance(expr, str) or not expr.strip():
        raise ValueError("expression vide")
    return _Parseur(_lex(expr)).parse()


def _eval(noeud, env) -> bool:
    t = noeud[0]
    if t == "CONST":
        return noeud[1]
    if t == "VAR":
        if noeud[1] not in env:
            raise ValueError(f"variable non affectée : {noeud[1]}")
        return bool(env[noeud[1]])
    if t == "NOT":
        return not _eval(noeud[1], env)
    a = _eval(noeud[1], env)
    b = _eval(noeud[2], env)
    if t == "AND":
        return a and b
    if t == "OR":
        return a or b
    if t == "XOR":
        return a != b
    if t == "IMPL":
        return (not a) or b
    if t == "EQUIV":
        return a == b
    raise ValueError(f"nœud inconnu {t}")


def _vars(noeud, acc):
    if noeud[0] == "VAR":
        acc.add(noeud[1])
    elif noeud[0] in ("NOT",):
        _vars(noeud[1], acc)
    elif noeud[0] in ("AND", "OR", "XOR", "IMPL", "EQUIV"):
        _vars(noeud[1], acc)
        _vars(noeud[2], acc)


def variables(expr: str) -> list[str]:
    acc = set()
    _vars(_arbre(expr), acc)
    return sorted(acc)


def evalue(expr: str, env: dict) -> bool:
    """Évalue l'expression sous l'affectation env {variable: bool}. ValueError si variable manquante / mal formé."""
    return _eval(_arbre(expr), env)


def table_verite(expr: str):
    """Liste de (affectation, résultat) sur les 2ⁿ affectations des variables (ordre lexicographique des variables)."""
    arbre = _arbre(expr)
    vs = sorted({v for v in _collecte_vars(arbre)})
    lignes = []
    for masque in range(2 ** len(vs)):
        env = {v: bool((masque >> i) & 1) for i, v in enumerate(reversed(vs))}
        lignes.append((env, _eval(arbre, env)))
    return lignes


def _collecte_vars(arbre):
    acc = set()
    _vars(arbre, acc)
    return acc


def est_tautologie(expr: str) -> bool:
    """Vrai ssi l'expression est vraie pour TOUTE affectation (loi logique)."""
    return all(r for _, r in table_verite(expr))


def est_contradiction(expr: str) -> bool:
    """Vrai ssi l'expression est fausse pour toute affectation."""
    return all(not r for _, r in table_verite(expr))


def est_satisfiable(expr: str) -> bool:
    """Vrai ssi au moins une affectation rend l'expression vraie."""
    return any(r for _, r in table_verite(expr))


def equivalent(expr1: str, expr2: str) -> bool:
    """Vrai ssi les deux expressions ont la même valeur sur toutes les affectations de l'UNION de leurs variables."""
    a1, a2 = _arbre(expr1), _arbre(expr2)
    vs = sorted(_collecte_vars(a1) | _collecte_vars(a2))
    for masque in range(2 ** len(vs)):
        env = {v: bool((masque >> i) & 1) for i, v in enumerate(reversed(vs))}
        if _eval(a1, env) != _eval(a2, env):
            return False
    return True


if __name__ == "__main__":
    print("tiers exclu  a | ~a :", est_tautologie("a | ~a"))
    print("non-contradiction ~(a & ~a) :", est_tautologie("~(a & ~a)"))
    print("De Morgan ~(a&b) <-> (~a|~b) :", est_tautologie("~(a & b) <-> (~a | ~b)"))
    print("distributivité :", est_tautologie("a & (b | c) <-> (a & b) | (a & c)"))
    print("modus ponens ((a -> b) & a) -> b :", est_tautologie("((a -> b) & a) -> b"))
    print("a & ~a contradiction :", est_contradiction("a & ~a"))
    print("a -> b satisfiable :", est_satisfiable("a -> b"))
    print("a|b équiv b|a :", equivalent("a | b", "b | a"))
    print("a->b équiv ~a|b :", equivalent("a -> b", "~a | b"))
