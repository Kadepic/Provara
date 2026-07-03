"""
STRATÉGIE OPTIMALE — jeux résolus à information parfaite (mandat : « Stratégie optimale (jeux résolus : morpion,
etc.) »). MÉCANISME EXACT = minimax énuméré sur l'arbre complet de jeu. Aucune heuristique, aucune table apprise :
la valeur d'une position EST le résultat du jeu parfait, calculé exhaustivement.

Le morpion (tic-tac-toe) est un jeu RÉSOLU : sous jeu parfait des deux joueurs, l'issue est NULLE. Ce module le
PROUVE par construction (la racine d'un plateau vide a pour valeur minimax 0) plutôt que de l'affirmer.

GARANTIES (vérifiées en adverse par `valide_strategie_jeux.py`) :
  - jeu parfait depuis le début -> valeur 0 (nul) — propriété connue du morpion, ici recalculée par énumération ;
  - un coup gagnant immédiat est trouvé (valeur de retour = la case qui gagne) ;
  - une menace adverse imparable au prochain coup est BLOQUÉE (minimax préfère le coup qui empêche la défaite) ;
  - plateau INVALIDE (longueur ≠ 9, symbole hors {'X','O',' '}, compte X/O incohérent, deux gagnants) -> ValueError :
    jamais une réponse sur une position qui ne peut pas exister ;
  - déterministe (mémoïsation pure ; le coup choisi est le plus petit indice à valeur optimale, donc reproductible).

Convention de valeur : +1 = victoire de 'X', −1 = victoire de 'O', 0 = nul. 'X' MAXIMISE, 'O' MINIMISE.
"""
from __future__ import annotations

from functools import lru_cache

X = "X"
O = "O"
VIDE = " "

# Les 8 alignements gagnants du morpion (lignes, colonnes, diagonales) sur la grille 0..8 :
#   0 1 2
#   3 4 5
#   6 7 8
_LIGNES = (
    (0, 1, 2), (3, 4, 5), (6, 7, 8),   # lignes
    (0, 3, 6), (1, 4, 7), (2, 5, 8),   # colonnes
    (0, 4, 8), (2, 4, 6),              # diagonales
)


def _valide_plateau(plateau) -> tuple:
    """Vérifie la légalité STRUCTURELLE d'une position et renvoie le tuple normalisé. Sinon ValueError."""
    if not isinstance(plateau, (list, tuple)):
        raise ValueError("plateau doit être une liste/tuple de 9 cases")
    t = tuple(plateau)
    if len(t) != 9:
        raise ValueError(f"plateau de longueur {len(t)} (attendu 9)")
    for c in t:
        if c not in (X, O, VIDE):
            raise ValueError(f"case invalide {c!r} (attendu 'X', 'O' ou ' ')")
    nx = t.count(X)
    no = t.count(O)
    # X commence : à tout instant légal, nx == no (à X de jouer) ou nx == no+1 (à O de jouer).
    if not (nx == no or nx == no + 1):
        raise ValueError(f"compte incohérent : {nx} X / {no} O (X commence, alterne)")
    gx = _gagne(t, X)
    go = _gagne(t, O)
    if gx and go:
        raise ValueError("position impossible : 'X' et 'O' gagnants simultanément")
    # Si X a gagné, X a joué le dernier coup -> nx == no+1. Si O a gagné -> nx == no.
    if gx and nx != no + 1:
        raise ValueError("position impossible : 'X' gagnant mais compte incohérent")
    if go and nx != no:
        raise ValueError("position impossible : 'O' gagnant mais compte incohérent")
    return t


def _gagne(t: tuple, joueur: str) -> bool:
    return any(t[a] == t[b] == t[c] == joueur for a, b, c in _LIGNES)


def gagnant(plateau):
    """Renvoie 'X' ou 'O' si l'un a un alignement, sinon None (partie nulle ou en cours)."""
    t = _valide_plateau(plateau)
    if _gagne(t, X):
        return X
    if _gagne(t, O):
        return O
    return None


def _trait(t: tuple) -> str:
    """À qui de jouer (X commence). Pré-condition : position validée et non terminale par victoire."""
    return X if t.count(X) == t.count(O) else O


def _terminal(t: tuple):
    """Renvoie la valeur (+1/−1/0) si la position est terminale, sinon None."""
    if _gagne(t, X):
        return 1
    if _gagne(t, O):
        return -1
    if VIDE not in t:
        return 0
    return None


@lru_cache(maxsize=None)
def _minimax(t: tuple) -> int:
    """Valeur minimax EXACTE de la position t (énumération exhaustive de l'arbre, mémoïsée)."""
    term = _terminal(t)
    if term is not None:
        return term
    joueur = _trait(t)
    coups = [i for i in range(9) if t[i] == VIDE]
    valeurs = []
    for i in coups:
        suiv = t[:i] + (joueur,) + t[i + 1:]
        valeurs.append(_minimax(suiv))
    return max(valeurs) if joueur == X else min(valeurs)


def valeur_minimax(plateau, joueur=None) -> int:
    """Valeur du jeu parfait depuis `plateau` : +1 (X gagne), −1 (O gagne), 0 (nul).

    `joueur` est optionnel : le trait est déduit du plateau (X commence, alterne). S'il est fourni, il DOIT
    coïncider avec le trait réel, sinon ValueError (on ne calcule pas une position dont c'est l'autre de jouer).
    """
    t = _valide_plateau(plateau)
    if joueur is not None:
        if joueur not in (X, O):
            raise ValueError(f"joueur invalide {joueur!r}")
        if _terminal(t) is None and joueur != _trait(t):
            raise ValueError(f"ce n'est pas à {joueur} de jouer dans cette position")
    return _minimax(t)


def morpion_coup_optimal(plateau) -> int:
    """Indice (0..8) du meilleur coup par minimax pour le joueur au trait. ValueError si pas de coup possible
    (plateau plein ou déjà gagné). Choix déterministe : à valeur optimale égale, le PLUS PETIT indice."""
    t = _valide_plateau(plateau)
    if _terminal(t) is not None:
        raise ValueError("position terminale : aucun coup à jouer")
    joueur = _trait(t)
    coups = [i for i in range(9) if t[i] == VIDE]
    meilleur_i = None
    meilleure_v = None
    for i in coups:
        suiv = t[:i] + (joueur,) + t[i + 1:]
        v = _minimax(suiv)
        if meilleure_v is None or (joueur == X and v > meilleure_v) or (joueur == O and v < meilleure_v):
            meilleure_v = v
            meilleur_i = i
    return meilleur_i
