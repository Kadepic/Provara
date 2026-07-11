"""
FORCE DU SPEC — mutation testing pour MESURER si un besoin (spec) est assez fort (chantier FORGE, atome 4 :
« descends au niveau des protons pour adapter les besoins », Yohan 2026-07-12).

Le moteur d'invention détecte déjà l'AMBIGU quand DEUX réalisations connues divergent sous le spec. Ce
module descend un cran : il MUTE la réalisation retenue elle-même (constantes ±1, opérateurs voisins,
comparaisons inversées…) et regarde combien de mutants le spec ÉCHOUE à tuer. Un mutant survivant qui n'est
PAS équivalent à l'original = une variation que le spec ne distingue pas = le besoin est SOUS-DÉTERMINÉ
sur cet axe. C'est le TEST DU DIABLE (chaque brique = unique réalisation) rendu MÉCANIQUE et mesurable.

FONDATIONS (recherche — toutes pré-2000 sauf mention) :
  • Mutation testing (DeMillo, Lipton, Sayward 1978) : la force d'un jeu de tests = sa capacité à tuer les
    mutants du programme.
  • Le PROBLÈME DU MUTANT ÉQUIVALENT (Budd & Angluin 1982) : un mutant sémantiquement IDENTIQUE à l'original
    survit toujours — ce n'est PAS une faiblesse du spec. On le neutralise par SONDAGE COMPORTEMENTAL : un
    mutant qui coïncide avec l'original sur un large jeu de sondes (au-delà du spec) est jugé équivalent et
    EXCLU du dénominateur. Au doute (aucune divergence observée), on ne compte JAMAIS une fausse faiblesse.

SOUNDNESS : ce module ne PRODUIT rien, il MESURE. Il ne peut pas créer de faux fait. Sa seule sortie
actionnable — un « exemple discriminant » — est une ENTRÉE sur laquelle un survivant NON équivalent diffère
de l'original : par construction, l'ajouter au spec tue ce survivant (vérifié avant d'être proposé).
"""
from __future__ import annotations

import ast

import moteur_invention as MI


# ── GÉNÉRATION DE MUTANTS (AST, sur l'expression retenue) ────────────────────────────────────────────────
_CMP_VOISINS = {
    ast.Lt: [ast.LtE, ast.Gt, ast.NotEq], ast.LtE: [ast.Lt, ast.GtE, ast.Eq],
    ast.Gt: [ast.GtE, ast.Lt, ast.NotEq], ast.GtE: [ast.Gt, ast.LtE, ast.Eq],
    ast.Eq: [ast.NotEq, ast.LtE, ast.GtE], ast.NotEq: [ast.Eq, ast.Lt, ast.Gt],
}
_BIN_VOISINS = {
    ast.Add: [ast.Sub, ast.Mult], ast.Sub: [ast.Add, ast.Mult], ast.Mult: [ast.Add, ast.Sub],
    ast.Div: [ast.Mult, ast.FloorDiv], ast.FloorDiv: [ast.Div, ast.Mult], ast.Mod: [ast.Mult, ast.FloorDiv],
    ast.Pow: [ast.Mult],
}
_BOOL_VOISIN = {ast.And: ast.Or, ast.Or: ast.And}


class _Mutateur(ast.NodeTransformer):
    """Applique UNE mutation ciblée (indexée) à l'arbre — un mutant = une seule graine changée."""
    def __init__(self, cible: int):
        self.cible = cible
        self.i = -1

    def _tour(self):
        self.i += 1
        return self.i == self.cible

    def visit_Constant(self, node):
        if isinstance(node.value, bool):                       # bool avant int (True est un int en Python)
            if self._tour():
                return ast.copy_location(ast.Constant(not node.value), node)
        elif isinstance(node.value, (int, float)):
            for delta in (1, -1, 0):
                if self._tour():
                    val = 0 if delta == 0 and node.value != 0 else node.value + delta
                    return ast.copy_location(ast.Constant(val), node)
        return node

    def visit_Compare(self, node):
        self.generic_visit(node)
        neufs = []
        for op in node.ops:
            remplace = op
            for cand in _CMP_VOISINS.get(type(op), []):
                if self._tour():
                    remplace = cand()
                    break
            neufs.append(remplace)
        node.ops = neufs
        return node

    def visit_BinOp(self, node):
        self.generic_visit(node)
        for cand in _BIN_VOISINS.get(type(node.op), []):
            if self._tour():
                node.op = cand()
                break
        return node

    def visit_BoolOp(self, node):
        self.generic_visit(node)
        if type(node.op) in _BOOL_VOISIN and self._tour():
            node.op = _BOOL_VOISIN[type(node.op)]()
        return node


def _nb_graines(expr: str) -> int:
    """Compte les points de mutation d'une expression (pour énumérer tous les mutants sans en rater)."""
    n = 0
    for node in ast.walk(ast.parse(expr, mode="eval")):
        if isinstance(node, ast.Constant):
            if isinstance(node.value, bool):
                n += 1
            elif isinstance(node.value, (int, float)):
                n += 3
        elif isinstance(node, ast.Compare):
            n += sum(len(_CMP_VOISINS.get(type(op), [])) for op in node.ops)
        elif isinstance(node, ast.BinOp):
            n += len(_BIN_VOISINS.get(type(node.op), []))
        elif isinstance(node, ast.BoolOp):
            n += 1 if type(node.op) in _BOOL_VOISIN else 0
    return n


def mutants(expr: str):
    """Tous les mutants distincts de `expr` (chacun = une graine changée). Chaîne d'expression -> chaînes."""
    try:
        base = ast.parse(expr, mode="eval")
    except SyntaxError:
        return []
    vus, out = {expr}, []
    for k in range(_nb_graines(expr)):
        arbre = _Mutateur(k).visit(ast.parse(expr, mode="eval"))
        ast.fix_missing_locations(arbre)
        try:
            code = ast.unparse(arbre)
        except Exception:
            continue
        if code not in vus:
            vus.add(code)
            out.append(code)
    return out


# ── MESURE DE LA FORCE ───────────────────────────────────────────────────────────────────────────────────
def _diverge(f, g, sondes):
    """Première sonde où f et g diffèrent (résultat OU erreur), sinon None. Sert à la fois à écarter les
    mutants équivalents ET à fournir l'exemple discriminant."""
    for s in sondes:
        try:
            rf, ef = f(s), None
        except Exception as e:
            rf, ef = None, type(e).__name__
        try:
            rg, eg = g(s), None
        except Exception as e:
            rg, eg = None, type(e).__name__
        if ef != eg or (ef is None and (rf != rg or isinstance(rf, bool) != isinstance(rg, bool))):
            return s
    return None


def _sondes_asymetriques(spec):
    """Sondes à VALEURS DISTINCTES dérivées de la forme des entrées du spec. Les sondes structurelles
    automatiques ([2,2]->[3,3]) gardent les éléments ÉGAUX : un mutant qui échange des index (x[1] au lieu
    de x[0]) ou double le mauvais élément y coïncide par accident et passe pour « équivalent ». Une entrée
    à valeurs distinctes [1,2,…,n] — et sa renversée — brise cette symétrie et démasque le mutant. N'ajoute
    de sondes que pour des séquences NUMÉRIQUES (type-safe : sur une matrice/liste de chaînes, x[i] arithmétique
    lèverait — on ne force pas hors du domaine observé). SOUND : plus de sondes ne peut que RECLASSER un faux
    « équivalent » en vrai survivant (plus de faiblesses vues), jamais créer un faux fait."""
    out = []
    for a, _ in spec:
        if isinstance(a, (list, tuple)) and len(a) >= 2 and all(
                isinstance(e, (int, float)) and not isinstance(e, bool) for e in a):
            n = len(a)
            croissant = list(range(1, n + 1))
            out.append(croissant)
            out.append(croissant[::-1])
    return out


def force_du_spec(expr: str, exemples, held, sondes=None) -> dict:
    """MESURE la force du spec (exemples+held) à déterminer `expr`, par mutation testing.

    Renvoie un rapport : nb de mutants, tués, équivalents (écartés), SURVIVANTS non équivalents, score de
    mutation ∈ [0,1] (tués / non-équivalents), et — s'il existe un survivant — un `discriminant` : une entrée
    (input, sortie attendue = expr(input)) qui, ajoutée au spec, TUE ce survivant. score == 1.0 => le spec
    fixe la brique de façon unique parmi ses mutations (aucune faiblesse détectée)."""
    spec = list(exemples) + list(held)
    f = MI._callable(expr, "f")
    if f is None or not MI._reproduit(f, spec):
        raise ValueError("force_du_spec : l'expression de référence doit reproduire son propre spec")
    # sondes : celles fournies, + les entrées du spec, + des variantes structurelles automatiques.
    base_sondes = list(sondes or [])
    base_sondes += [a for a, _ in spec]
    auto = MI.MoteurAutonome.sondes_auto(spec) or []
    base_sondes += [s[0] if isinstance(s, tuple) and len(s) == 1 else s for s in auto]
    base_sondes += _sondes_asymetriques(spec)      # brise les symétries que les sondes auto conservent

    muts = mutants(expr)
    tues = equivalents = 0
    survivants = []
    for m in muts:
        g = MI._callable(m, "f")
        if g is None or not MI._reproduit(g, spec):
            tues += 1                                          # le spec le distingue de l'original : tué
            continue
        # survit au spec : équivalent (coïncide partout) ou vraie faiblesse (diverge hors spec) ?
        d = _diverge(f, g, base_sondes)
        if d is None:
            equivalents += 1                                   # indistinguable même hors spec -> équivalent (écarté)
        else:
            survivants.append((m, d))
    non_equivalents = tues + len(survivants)
    rap = {
        "mutants": len(muts), "tues": tues, "equivalents": equivalents,
        "survivants": len(survivants),
        "score": 1.0 if non_equivalents == 0 else tues / non_equivalents,
        "discriminant": None,
    }
    if survivants:
        # l'exemple discriminant : sur l'entrée où le 1er survivant diverge, la BONNE sortie est celle de
        # l'original (vérité = expr, déjà prouvée sur le spec). L'ajouter tue ce survivant (par construction).
        m0, d0 = survivants[0]
        rap["discriminant"] = (d0, f(d0))
        rap["survivant_exemple"] = m0
    return rap


if __name__ == "__main__":
    from garde_ressources import borne
    borne()
    print("=== FORCE DU SPEC — mutation testing (le besoin est-il assez fort ?) ===\n")
    # spec FORT : amplitude = max - min, spec discriminant -> tous les mutants non équivalents meurent.
    fort = force_du_spec("max(x) - min(x)", [([3, 1, 5], 4), ([2, 2], 0)], [([0, 9, 4], 9), ([7], 0)])
    print("  amplitude (spec fort)  :", fort)
    # spec FAIBLE : une seule paire -> un mutant (+1 sur une constante) peut survivre.
    faible = force_du_spec("x[0] + 1", [([5], 6)], [])
    print("  x[0]+1 (spec faible)   :", faible)
