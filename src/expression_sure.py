"""
EXPRESSION SÛRE — le juge d'INNOCUITÉ de la forge (chantier FORGE atome 7).

La re-jugeance (atome 1) prouve la CORRECTION d'une brique (elle reproduit son spec) ; elle ne prouve PAS
son INNOCUITÉ. Une expression spec-correcte peut porter un effet de bord — `(open(p,'w').write(...), sum(x))[1]`
reproduit `somme` ET écrit un fichier — et l'admission l'EXÉCUTE (donc déclenche l'effet) avant de la servir.
Mesuré : elle passait `retient()` et `existant()`.

Ce module tranche STATIQUEMENT (sans exécuter — condition sine qua non : on ne peut pas « tester » l'innocuité
en lançant du code hostile) si une expression/`def` mono-fonction est SÛRE : réductions pures sur des données,
sans I/O, sans accès système, sans évasion de bac à sable. Modèle « promotion prouvée » (STOKE) : nœud AST
inconnu, nom dangereux ou attribut dunder -> REFUS (conservateur), jamais un doute servi.

Ce qui reste PERMIS (couvre tout l'inventaire EXISTANT et les familles etend_*) : arithmétique/logique/
comparaisons, compréhensions et lambdas, indexation/tranchage, littéraux list/tuple/set/dict, appels aux
builtins purs listés, méthodes de données (.upper/.split/.count/.values/.items…), et le SEUL `__import__`
autorisé avec un module littéral dans {math, itertools, functools}. Croise `audit_code` (CWE) pour la forme `def`.
"""
from __future__ import annotations

import ast

# Builtins PURS autorisés en appel (aucun I/O, aucun accès système, aucune réflexion).
_BUILTINS_SURS = frozenset({
    "abs", "all", "any", "bool", "dict", "divmod", "enumerate", "filter", "float", "frozenset",
    "int", "len", "list", "map", "max", "min", "range", "reversed", "round", "set", "sorted",
    "str", "sum", "tuple", "zip", "bin", "hex", "oct", "ord", "chr", "pow", "complex",
})
# Modules littéraux autorisés pour l'UNIQUE `__import__` toléré (ceux qu'utilise EXISTANT : math.prod, etc.).
_MODULES_SURS = frozenset({"math", "itertools", "functools"})

# Nœuds AST autorisés. Tout le reste (Import, With, Global, Yield, Await, NamedExpr, comprehension async…)
# = REFUS. `ast.Index`/`ast.ExtSlice` inclus pour compat < 3.9 (dépréciés mais inoffensifs).
_NOEUDS_SURS = tuple(getattr(ast, n) for n in (
    "Expression", "Module", "FunctionDef", "Return", "arguments", "arg", "Lambda",
    "Load", "Store", "Del",
    "BoolOp", "And", "Or", "BinOp", "UnaryOp",
    "Add", "Sub", "Mult", "Div", "FloorDiv", "Mod", "Pow", "LShift", "RShift",
    "BitOr", "BitAnd", "BitXor", "MatMult", "USub", "UAdd", "Not", "Invert",
    "Compare", "Eq", "NotEq", "Lt", "LtE", "Gt", "GtE", "Is", "IsNot", "In", "NotIn",
    "Call", "keyword", "IfExp",
    "Constant", "Name", "Attribute", "Subscript", "Slice", "Starred",
    "List", "Tuple", "Set", "Dict",
    "ListComp", "SetComp", "DictComp", "GeneratorExp", "comprehension",
) if hasattr(ast, n))


def _arbre(code: str):
    """Parse une expression OU un `def f(x): return …`. Renvoie l'AST, ou lève SyntaxError (= non sûr)."""
    src = code if code.lstrip().startswith("def ") else f"(lambda x: {code})"
    return ast.parse(src, mode="exec" if src.lstrip().startswith("def ") else "eval")


def raison_danger(code: str) -> str | None:
    """None si l'expression est SÛRE ; sinon la raison PRÉCISE (servable/traçable). Ne l'EXÉCUTE jamais."""
    if not isinstance(code, str) or not code.strip():
        return "expression vide"
    try:
        arbre = _arbre(code)
    except (SyntaxError, ValueError) as e:
        return f"non analysable ({e.__class__.__name__})"
    for n in ast.walk(arbre):
        if not isinstance(n, _NOEUDS_SURS):
            return f"nœud non autorisé : {type(n).__name__}"
        # Attribut dunder = évasion classique (().__class__.__bases__…__subclasses__()) -> refus.
        if isinstance(n, ast.Attribute) and n.attr.startswith("__") and n.attr.endswith("__"):
            return f"accès à un attribut spécial interdit : .{n.attr}"
        if isinstance(n, ast.Name):
            nom = n.id
            # __import__ n'est toléré que dans la forme d'appel vérifiée ci-dessous ; nu, il est refusé.
            if nom.startswith("__") and nom.endswith("__") and nom != "__import__":
                return f"nom spécial interdit : {nom}"
        if isinstance(n, ast.Call):
            f = n.func
            if isinstance(f, ast.Name):
                if f.id == "__import__":
                    a = n.args
                    if not (len(a) == 1 and isinstance(a[0], ast.Constant)
                            and a[0].value in _MODULES_SURS):
                        return "__import__ n'est autorisé qu'avec un module littéral sûr (math/itertools/functools)"
                elif f.id not in _BUILTINS_SURS:
                    return f"appel d'un nom non autorisé : {f.id}(…)"
            # f est un Attribute (méthode de données, ex. x.upper()) ou un Call/Lambda/Subscript composé :
            # les gardes dunder + node-whitelist ci-dessus suffisent (aucun module dangereux n'est atteignable
            # sans __import__, déjà restreint).
    return None


def est_sure(code: str) -> bool:
    """Vrai ssi `code` est une expression/def PURE et inoffensive (jugé statiquement, sans exécution)."""
    return raison_danger(code) is None
