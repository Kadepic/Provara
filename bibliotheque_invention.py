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

import chercheur_invention as C
import moteur_invention as MI


def promeut_abstraction(inv) -> tuple[str, str] | None:
    """De l'inventaire, prend l'abstraction la PLUS réutilisée et en fait une capacité NOMMÉE : le MAP
    élément-par-élément `[F for _e in x]`. Renvoie (nom, expr) ou None si aucune abstraction réutilisée."""
    if not inv.abstractions:
        return None
    F = inv.abstractions[0][0]                 # transform la plus réutilisée (ex. '_e * _e')
    return (f"map[{F}]", f"[{F} for _e in x]")


def etend_bibliotheque(existant: dict, inv) -> dict:
    """Renvoie une COPIE de la bibliothèque enrichie de l'abstraction promue (si elle existe)."""
    etendue = dict(existant)
    promo = promeut_abstraction(inv)
    if promo and promo[0] not in etendue:
        etendue[promo[0]] = promo[1]
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
