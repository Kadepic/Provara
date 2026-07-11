"""
CAPSTONE RÉCURSIF — phase « SOMMEIL » (DreamCoder) : l'IA s'améliore ELLE-MÊME au niveau BIBLIOTHÈQUE.

Le chercheur (chercheur_invention) découvre, par RÉUTILISATION mesurée, une abstraction de valeur
(ex. la transformation « _e * _e »). La phase sommeil la PROMEUT en capacité NOMMÉE de la bibliothèque
de « ce qui existe ». Effet RÉCURSIF + mesurable + sound :
  • GAIN ÉPISTÉMIQUE : une cible identique à l'abstraction passe de INVENTION (re-dérivée à chaque fois)
    à EXISTE_DEJA (reconnue comme une brique connue) — l'IA a APPRIS un bloc de construction réutilisable.
  • GARDE DE NON-RÉGRESSION (« sûr avant rapide ») : étendre la bibliothèque ne doit JAMAIS rendre un
    verdict faux ni perdre une solution. On le VÉRIFIE : aucune cible solvable ne devient non-réalisable,
    et toute capacité (existante ou promue) invoquée reproduit réellement les exemples qu'elle prétend couvrir.

C'est la boucle de Yohan fermée d'un cran de plus : découvrir -> intégrer -> re-mesurer, sans régresser.
"""
from __future__ import annotations

import ast

import chercheur_invention as C
import moteur_invention as MI


def _taille(expr: str) -> int:
    """Longueur de description (proxy MDL) d'une expression = nombre de nœuds AST. Robuste aux espaces
    (contrairement au nb de caractères) et monotone avec la complexité réelle. Fallback : nb de tokens
    non triviaux si l'expr ne parse pas seule (rare — les transforms extraites parsent)."""
    try:
        return sum(1 for _ in ast.walk(ast.parse(expr, mode="eval")))
    except SyntaxError:
        return max(1, len([t for t in expr.replace("(", " ").replace(")", " ").split() if t]))


def gain_mdl(transform: str, k: int) -> int:
    """Gain de compression (en nœuds AST) à promouvoir une abstraction `map[transform]` réutilisée par
    `k` cibles, selon MDL = L(bibliothèque) + Σ L(programmes | bibliothèque) (DreamCoder).

    L'abstraction promue est `[transform for _e in x]` : son coût de description est celui du MAP entier
    (transform + l'ossature de compréhension), pas du seul cœur. AVANT : chaque cible réécrit le map en
    entier -> k · s. APRÈS : la bibliothèque le stocke UNE fois (s) + chaque cible le référence par un nom
    (coût 1) -> s + k. Gain = k·s − (s + k) = s·(k−1) − k. Promouvoir ssi > 0 : une abstraction qui ne
    compresse pas ne rentre pas (parcimonie, pas d'enflure de bibliothèque)."""
    s = _taille(f"[{transform} for _e in x]")
    return s * (k - 1) - k


def promeut_abstractions(inv) -> list[tuple[str, str, int]]:
    """TOUTES les abstractions de l'inventaire dont la promotion COMPRESSE (gain MDL > 0), en capacités
    nommées `map[F] := [F for _e in x]`. Triées par gain décroissant. Sound : chaque F est extraite d'une
    solution VÉRIFIÉE et réutilisée par ≥2 cibles (cf. chercheur_invention) ; le seuil MDL est objectif."""
    promues = []
    for F, users in inv.abstractions:
        g = gain_mdl(F, len(users))
        if g > 0:
            promues.append((f"map[{F}]", f"[{F} for _e in x]", g))
    return sorted(promues, key=lambda p: (-p[2], p[0]))


def promeut_abstraction(inv) -> tuple[str, str] | None:
    """L'abstraction la PLUS payante (compat. historique) : capacité nommée `map[F] := [F for _e in x]`.
    None si aucune abstraction réutilisée ne compresse."""
    p = promeut_abstractions(inv)
    return (p[0][0], p[0][1]) if p else None


def etend_bibliotheque(existant: dict, inv) -> dict:
    """Renvoie une COPIE de la bibliothèque enrichie de TOUTES les abstractions qui compressent (gain MDL
    > 0), additive et idempotente (une capacité déjà présente n'est pas réécrite)."""
    etendue = dict(existant)
    for nom, expr, _g in promeut_abstractions(inv):
        if nom not in etendue:
            etendue[nom] = expr
    return etendue


def _verdict(nom, ex, held, existant, budget):
    return MI.examine_cible(nom, "x", ex, held, budget=budget, existant=existant)


def gain_reconnaissance(cibles, base: dict, etendue: dict, budget: int = 2000):
    """Cibles qui passent de INVENTION (base) à EXISTE_DEJA (bibliothèque étendue) = re-dérivation évitée."""
    gagnees = []
    for nom, ex, held in cibles:
        vb = _verdict(nom, ex, held, base, budget)
        ve = _verdict(nom, ex, held, etendue, budget)
        if vb.statut == MI.INVENTION and ve.statut == MI.EXISTE_DEJA:
            gagnees.append(nom)
    return gagnees


def verifie_non_regression(cibles, base: dict, etendue: dict, budget: int = 2000) -> bool:
    """True si étendre la bibliothèque n'a RIEN cassé : (a) aucune cible solvable (EXISTE_DEJA/INVENTION)
    ne devient non-réalisable ; (b) toute capacité invoquée reproduit réellement exemples+held (jamais un faux)."""
    SOLVABLE = {MI.EXISTE_DEJA, MI.INVENTION}
    for nom, ex, held in cibles:
        vb = _verdict(nom, ex, held, base, budget)
        ve = _verdict(nom, ex, held, etendue, budget)
        if vb.statut in SOLVABLE and ve.statut not in SOLVABLE:
            return False                                  # perte de solution = régression
        if ve.statut in SOLVABLE and ve.par is not None:  # le code invoqué doit reproduire la cible
            if not MI._reproduit(MI._callable(ve.par, nom), list(ex) + list(held)):
                return False
    return True


if __name__ == "__main__":
    from garde_ressources import borne
    borne()
    print("=== PHASE SOMMEIL : promotion d'abstraction + non-régression (récursif, sound) ===\n")

    # 1) ÉVEIL : inventaire d'un corpus -> découverte de l'abstraction réutilisée.
    CORPUS = [
        ("somme_totale", "xs", [([1, 2, 3], 6), ([5], 5)], [([0, 4], 4), ([2, 2], 4)]),
        ("somme_carres", "xs", [([1, 2, 3], 14), ([2, 3], 13)], [([5], 25), ([0, 4], 16), ([1, 1], 2)]),
        ("max_carres", "xs", [([-3, 2], 9), ([1, 4], 16), ([-1, -5], 25)], [([0, 3], 9), ([2, -2], 4), ([-6, 1], 36)]),
    ]
    inv = C.inventorie(CORPUS)
    promo = promeut_abstraction(inv)
    print(f"  abstraction découverte et promue : {promo[0]}  :=  {promo[1]}")

    base = MI.EXISTANT
    etendue = etend_bibliotheque(base, inv)
    print(f"  bibliothèque : {len(base)} capacités -> {len(etendue)} (après sommeil)\n")

    # 2) GAIN : une cible = la liste des carrés. Avant : INVENTION (re-dérivée). Après : EXISTE_DEJA (reconnue).
    cibles = [("liste_carres", [([1, 2, 3], [1, 4, 9]), ([2, 3], [4, 9])], [([5], [25]), ([0, 4], [0, 16])])]
    g = gain_reconnaissance(cibles, base, etendue)
    print(f"  GAIN de reconnaissance (INVENTION -> EXISTE_DEJA) : {g}")

    # 3) GARDE : la bibliothèque étendue n'a rien cassé sur le corpus d'origine + la nouvelle cible.
    corpus_test = [(n, e, h) for n, _s, e, h in CORPUS] + cibles
    print(f"  non-régression vérifiée : {verifie_non_regression(corpus_test, base, etendue)}")
