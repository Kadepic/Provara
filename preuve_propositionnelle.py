"""THÉORIE DE LA DÉMONSTRATION — vérification EXACTE de la validité d'inférences propositionnelles, FAUX=0.

Une inférence `premisses ⊢ conclusion` est VALIDE (sémantiquement) ssi (∧premisses) → conclusion est une
tautologie : toute affectation des variables qui rend TOUTES les prémisses vraies rend la conclusion vraie.
On le décide EXACTEMENT par table de vérité (2ⁿ affectations) en réutilisant le parseur booléen sound de
`algebre_boole` (descente récursive, connecteurs ~ & | ^ -> <->). C'est mécanique, déterministe, certain.

On expose aussi les RÈGLES de la déduction naturelle comme applications SYNTAXIQUES exactes :
  - modus ponens   : de (A -> B) et A, on dérive B ;
  - modus tollens  : de (A -> B) et ~B, on dérive ~A.
L'appariement se fait sur l'ARBRE de syntaxe (robuste aux parenthèses/espaces), JAMAIS sur la chaîne brute, et
chaque règle ne s'applique que si la forme est exacte — sinon abstention (ValueError). Les inférences ainsi
dérivées sont sémantiquement valides (vérifié en adverse par `valide_preuve_propositionnelle.py`).

Abstention STRUCTURELLE : expression mal formée, prémisses non itérables, forme de règle non respectée ->
ValueError. Jamais de verdict inventé.

Couvre le sujet borné « Théorie de la démonstration ».
"""
from __future__ import annotations

import algebre_boole as B

# Au-delà de cette borne le nombre d'affectations (2ⁿ) explose : on s'abstient plutôt que de partir en vrille.
_MAX_VARS = 20

_OP = {"AND": "&", "OR": "|", "XOR": "^", "IMPL": "->", "EQUIV": "<->"}
_BINAIRES = ("AND", "OR", "XOR", "IMPL", "EQUIV")


def _vers_str(noeud) -> str:
    """Sérialise un arbre de syntaxe en chaîne canonique, entièrement parenthésée donc re-parseable."""
    t = noeud[0]
    if t == "CONST":
        return "1" if noeud[1] else "0"
    if t == "VAR":
        return noeud[1]
    if t == "NOT":
        enfant = noeud[1]
        s = _vers_str(enfant)
        if enfant[0] in _BINAIRES:
            s = "(" + s + ")"
        return "~" + s
    if t in _BINAIRES:
        return "(" + _vers_str(noeud[1]) + " " + _OP[t] + " " + _vers_str(noeud[2]) + ")"
    raise ValueError(f"nœud inconnu : {t}")


def _arbres_premisses(premisses):
    """Parse chaque prémisse (-> arbre) ; ValueError si premisses n'est pas une liste/tuple ou si une prémisse
    est mal formée."""
    if not isinstance(premisses, (list, tuple)):
        raise ValueError("premisses doit être une liste de chaînes")
    return [B._arbre(p) for p in premisses]


def inference_valide(premisses, conclusion: str) -> bool:
    """True ssi (∧premisses) → conclusion est une tautologie (toute affectation satisfaisant les prémisses
    satisfait la conclusion). EXACT par table de vérité. ValueError si une expression est mal formée.

    Prémisses vide -> la validité équivaut à « conclusion est une tautologie »."""
    arbres_p = _arbres_premisses(premisses)
    arbre_c = B._arbre(conclusion)

    variables = set()
    for a in arbres_p:
        variables |= B._collecte_vars(a)
    variables |= B._collecte_vars(arbre_c)
    variables = sorted(variables)
    if len(variables) > _MAX_VARS:
        raise ValueError(f"trop de variables ({len(variables)} > {_MAX_VARS}) : abstention")

    for masque in range(2 ** len(variables)):
        env = {v: bool((masque >> i) & 1) for i, v in enumerate(reversed(variables))}
        if all(B._eval(a, env) for a in arbres_p):
            if not B._eval(arbre_c, env):
                return False
    return True


def regle_modus_ponens(conditionnel: str, antecedent: str) -> str:
    """Application SYNTAXIQUE du modus ponens : de (A -> B) et A, dérive B (chaîne canonique).
    ValueError si `conditionnel` n'est pas une implication de tête ou si l'antécédent ne correspond pas (arbres)."""
    c = B._arbre(conditionnel)
    a = B._arbre(antecedent)
    if c[0] != "IMPL":
        raise ValueError("modus ponens : la première prémisse doit être une implication A -> B")
    if c[1] != a:
        raise ValueError("modus ponens : l'antécédent fourni ne correspond pas à A")
    return _vers_str(c[2])


def regle_modus_tollens(conditionnel: str, negation_consequent: str) -> str:
    """Application SYNTAXIQUE du modus tollens : de (A -> B) et ~B, dérive ~A (chaîne canonique).
    ValueError si la forme n'est pas respectée."""
    c = B._arbre(conditionnel)
    nb = B._arbre(negation_consequent)
    if c[0] != "IMPL":
        raise ValueError("modus tollens : la première prémisse doit être une implication A -> B")
    if nb[0] != "NOT" or nb[1] != c[2]:
        raise ValueError("modus tollens : la seconde prémisse doit être la négation du conséquent (~B)")
    return _vers_str(("NOT", c[1]))


if __name__ == "__main__":
    print("modus ponens   ['p','p -> q'] |- q :", inference_valide(["p", "p -> q"], "q"))
    print("modus tollens  ['p -> q','~q'] |- ~p :", inference_valide(["p -> q", "~q"], "~p"))
    print("affirm. conséq ['p -> q','q'] |- p :", inference_valide(["p -> q", "q"], "p"))
    print("non-séquence   ['p'] |- q :", inference_valide(["p"], "q"))
    print("règle MP  (p -> q, p) ->", regle_modus_ponens("p -> q", "p"))
    print("règle MT  (p -> q, ~q) ->", regle_modus_tollens("p -> q", "~q"))
