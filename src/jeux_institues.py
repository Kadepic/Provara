"""
JEUX INSTITUÉS — règles + coup optimal dans une position finie (PARTIE XII, B-CONV).

Généralise `strategie_jeux` (qui résout le SEUL morpion, plateau 3×3 codé en dur — RÉSERVÉ, importé et
délégué ici, jamais modifié) en un CADRE minimax paramétré par les RÈGLES d'un jeu, plus les théorèmes
exacts qui rendent certaines familles décidables sans dérouler l'arbre.

MÉCANISMES EXACTS (théorèmes, pas des heuristiques) :
  • MINIMAX (von Neumann, théorème minimax) : pour un jeu FINI à information PARFAITE et somme nulle, la valeur
    d'une position EST le résultat du jeu parfait, calculé par énumération exhaustive de l'arbre. On MÉMOÏSE et
    on BORNE la profondeur : si l'arbre n'est pas prouvé fini dans le budget -> ValueError (jamais un résultat
    non prouvé). Le module ne peut PAS vérifier « information parfaite » en général — c'est une PRÉCONDITION du
    caller ; il vérifie en revanche la FINITUDE (borne de profondeur atteinte -> abstention).
  • NIM (théorème de Bouton, 1901) : en jeu normal, une position (tas d'allumettes) est PERDANTE pour le joueur
    au trait SSI la somme de Nim (XOR des tailles) est nulle. Un coup gagnant, quand il existe, ramène la somme
    de Nim à zéro ; s'il n'en existe pas (position perdante) le module ABSTIENT (ValueError) — abstention VRAIE,
    pas un échec.
  • PUISSANCE 4 : jeu RÉSOLU en théorie (victoire du premier joueur), mais l'arbre complet est HORS budget.
    `puissance4_coup_optimal` fait un minimax à profondeur BORNÉE avec évaluation ; il rend un drapeau `exacte`
    qui vaut True UNIQUEMENT si la valeur rendue est le résultat prouvé du jeu (feuilles toutes terminales sur
    l'issue retenue), et False quand une feuille a été COUPÉE par la profondeur (valeur alors APPROCHÉE, dite).
  • ÉCHECS / GO : le module ne prétend PAS jouer -> `coup_optimal('echecs', ...)` / `('go', ...)` -> ValueError.
    Il expose seulement leurs RÈGLES essentielles (pour les échecs : les quatre conditions de nulle nommées).

GARANTIES (vérifiées en adverse par `valide_jeux_institues.py`) :
  - jeu hors catalogue -> ValueError ; échecs/go -> ValueError explicite (on ne joue pas) ;
  - tas de Nim invalide (bool, non-entier, négatif, non-séquence, vide) -> ValueError ;
  - position de Nim perdante -> `nim_coup_gagnant` ABSTIENT (ValueError) ;
  - plateau Puissance 4 invalide / terminal / profondeur ∉ [1,12] / bool -> ValueError ;
  - CADRE : règle non callable, profondeur_max hors bornes, état non hashable, valeur non finie -> ValueError ;
  - déterministe ; conservateur (faux négatif toléré, faux POSITIF interdit).

Stdlib UNIQUEMENT (math, copy). Fonctions PURES et déterministes ; aucun état global mutable.
"""
from __future__ import annotations

import copy
import math

import strategie_jeux as _sj

SOURCE = (
    "théorème minimax (von Neumann, 1928) ; théorème de Bouton du Nim (1901) ; "
    "morpion résolu = nul ; Puissance 4 résolu = victoire du 1er joueur (Allis/Allen, 1988) ; "
    "règles FIDE (conditions de nulle) — jeux à information parfaite, somme nulle"
)

X = "X"
O = "O"

_PROF_MAX_ABS = 64            # borne dure de profondeur du CADRE générique (au-delà : budget dépassé)
_P4_COLS = 7
_P4_ROWS = 6
_P4_PROF_MAX = 12             # budget de recherche Puissance 4 (spec : profondeur > 12 -> ValueError)


# ── helpers internes ────────────────────────────────────────────────────────────────────────────────────────────
def _est_entier(x) -> bool:
    """True ssi x est un int qui n'est PAS un bool (True n'est pas 1)."""
    return isinstance(x, int) and not isinstance(x, bool)


def _est_nombre(x) -> bool:
    """True ssi x est un réel fini (bool REFUSÉ)."""
    return isinstance(x, (int, float)) and not isinstance(x, bool) and math.isfinite(x)


# ════════════════════════════════════════════════════════════════════════════════════════════════════════════════
# (a) CADRE GÉNÉRIQUE — minimax paramétré par les RÈGLES du jeu
# ════════════════════════════════════════════════════════════════════════════════════════════════════════════════
def _valide_regles(coups, applique, terminal, valeur, joueur_max, profondeur_max) -> int:
    for f, nom in ((coups, "coups"), (applique, "applique"), (terminal, "terminal"),
                   (valeur, "valeur"), (joueur_max, "joueur_max")):
        if not callable(f):
            raise ValueError(f"règle {nom!r} non callable")
    if not _est_entier(profondeur_max) or not (1 <= profondeur_max <= _PROF_MAX_ABS):
        raise ValueError(f"profondeur_max invalide : entier dans [1, {_PROF_MAX_ABS}] requis")
    return profondeur_max


def minimax(etat, coups, applique, terminal, valeur, joueur_max, profondeur_max):
    """Valeur minimax EXACTE de `etat` pour un jeu fini à information parfaite (somme nulle).

    Règles (callables) : coups(e)->itérable de coups ; applique(e,c)->nouvel état ; terminal(e)->bool ;
    valeur(e)->nombre fini (payoff du joueur MAX aux feuilles) ; joueur_max(e)->bool (True si au trait = MAX).
    `profondeur_max` BORNE la finitude : si une branche non terminale dépasse ce budget -> ValueError (le jeu
    n'est pas prouvé fini). État MÉMOÏSÉ (doit être hashable, sinon ValueError). Résultat déterministe.
    """
    _valide_regles(coups, applique, terminal, valeur, joueur_max, profondeur_max)
    memo: dict = {}

    def rec(e, prof):
        try:
            cle = e
            hash(cle)
        except TypeError:
            raise ValueError("état non hashable : le CADRE exige des états hashables pour la mémoïsation")
        if cle in memo:
            return memo[cle]
        if terminal(e):
            v = valeur(e)
            if not _est_nombre(v):
                raise ValueError("valeur(feuille) non finie : le CADRE refuse une valeur non numérique")
            memo[cle] = v
            return v
        if prof <= 0:
            raise ValueError("jeu non prouvé fini dans le budget : profondeur_max dépassée (abstention)")
        cs = list(coups(e))
        if not cs:
            # aucun coup mais non 'terminal' : on traite comme feuille (valeur définie par les règles)
            v = valeur(e)
            if not _est_nombre(v):
                raise ValueError("valeur(feuille sans coup) non finie")
            memo[cle] = v
            return v
        vals = [rec(applique(e, c), prof - 1) for c in cs]
        r = max(vals) if joueur_max(e) else min(vals)
        memo[cle] = r
        return r

    return rec(etat, profondeur_max)


def coup_optimal_generique(etat, coups, applique, terminal, valeur, joueur_max, profondeur_max):
    """Meilleur coup ET valeur du jeu pour `etat` (CADRE générique, minimax exhaustif borné).

    Renvoie (coup, valeur). Le coup est celui qui optimise la valeur pour le joueur au trait ; à valeur égale,
    le PREMIER dans l'ordre (déterministe) rendu par coups(). État terminal / sans coup -> ValueError.
    """
    _valide_regles(coups, applique, terminal, valeur, joueur_max, profondeur_max)
    if terminal(etat):
        raise ValueError("état terminal : aucun coup à jouer")
    cs = list(coups(etat))
    if not cs:
        raise ValueError("aucun coup disponible dans cet état")
    maxi = bool(joueur_max(etat))
    meilleur_c = None
    meilleure_v = None
    for c in cs:
        v = minimax(applique(etat, c), coups, applique, terminal, valeur, joueur_max, profondeur_max)
        if meilleure_v is None or (maxi and v > meilleure_v) or ((not maxi) and v < meilleure_v):
            meilleure_v = v
            meilleur_c = c
    return (meilleur_c, meilleure_v)


# ════════════════════════════════════════════════════════════════════════════════════════════════════════════════
# (b) NIM — théorème de Bouton (décidable sans dérouler l'arbre)
# ════════════════════════════════════════════════════════════════════════════════════════════════════════════════
def _valide_tas(tas) -> tuple:
    if not isinstance(tas, (list, tuple)):
        raise ValueError("tas invalide : une liste/tuple de tailles entières ≥ 0 est requise")
    t = tuple(tas)
    if len(t) == 0:
        raise ValueError("tas invalide : au moins un tas est requis")
    for v in t:
        if not _est_entier(v) or v < 0:
            raise ValueError(f"taille de tas invalide {v!r} : entier ≥ 0 requis (bool refusé)")
    return t


def nim_somme(tas) -> int:
    """Somme de Nim = XOR des tailles de tas (invariant de Bouton). tas invalide -> ValueError."""
    t = _valide_tas(tas)
    s = 0
    for v in t:
        s ^= v
    return s


def nim_position_perdante(tas) -> bool:
    """True ssi la position est PERDANTE pour le joueur au trait (somme de Nim nulle — théorème de Bouton)."""
    return nim_somme(tas) == 0


def nim_coup_gagnant(tas):
    """Coup gagnant (index_tas, nb_allumettes_retirées) ramenant la somme de Nim à 0.

    Si la position est PERDANTE (somme de Nim nulle), aucun coup gagnant n'existe -> ValueError : c'est une
    ABSTENTION VRAIE (le réel dit qu'il n'y a pas de coup gagnant), pas un échec. Déterministe : plus petit
    index de tas admissible.
    """
    t = _valide_tas(tas)
    s = 0
    for v in t:
        s ^= v
    if s == 0:
        raise ValueError("position perdante (somme de Nim nulle) : aucun coup gagnant — abstention")
    for i, a in enumerate(t):
        cible = a ^ s          # taille visée du tas i pour annuler la somme de Nim
        if cible < a:
            return (i, a - cible)
    # inatteignable si s != 0 (Bouton garantit un tel tas via le bit de poids fort de s) — garde défensive
    raise ValueError("incohérence interne Nim : aucun tas réducteur trouvé malgré une somme non nulle")


# ════════════════════════════════════════════════════════════════════════════════════════════════════════════════
# (c) PUISSANCE 4 — minimax à profondeur BORNÉE + évaluation (valeur non exacte au-delà de la profondeur)
# ════════════════════════════════════════════════════════════════════════════════════════════════════════════════
def _p4_valide(plateau) -> tuple:
    """Valide un plateau Puissance 4 = 7 colonnes empilées bas->haut (jetons 'X'/'O'), gravité implicite."""
    if not isinstance(plateau, (list, tuple)) or len(plateau) != _P4_COLS:
        raise ValueError(f"plateau Puissance 4 invalide : {_P4_COLS} colonnes requises")
    cols = []
    for c in plateau:
        if not isinstance(c, (list, tuple)):
            raise ValueError("colonne invalide : liste/tuple de jetons requise")
        cc = tuple(c)
        if len(cc) > _P4_ROWS:
            raise ValueError(f"colonne trop haute : au plus {_P4_ROWS} jetons")
        for tok in cc:
            if tok not in (X, O):
                raise ValueError(f"jeton invalide {tok!r} (attendu 'X' ou 'O')")
        cols.append(cc)
    cols = tuple(cols)
    nx = sum(col.count(X) for col in cols)
    no = sum(col.count(O) for col in cols)
    if not (nx == no or nx == no + 1):     # X commence, alterne
        raise ValueError(f"compte incohérent : {nx} X / {no} O")
    gx = _p4_gagne(cols, X)
    go = _p4_gagne(cols, O)
    if gx and go:
        raise ValueError("position impossible : deux joueurs alignés simultanément")
    if gx and nx != no + 1:
        raise ValueError("position impossible : 'X' aligné mais compte incohérent")
    if go and nx != no:
        raise ValueError("position impossible : 'O' aligné mais compte incohérent")
    return cols


def _p4_cell(cols, c, r):
    if 0 <= c < _P4_COLS and 0 <= r < _P4_ROWS and r < len(cols[c]):
        return cols[c][r]
    return None


def _p4_gagne(cols, joueur) -> bool:
    """True ssi `joueur` a un alignement de 4 (horizontal, vertical, deux diagonales)."""
    for c in range(_P4_COLS):
        for r in range(_P4_ROWS):
            if _p4_cell(cols, c, r) != joueur:
                continue
            for dc, dr in ((1, 0), (0, 1), (1, 1), (1, -1)):
                if all(_p4_cell(cols, c + dc * k, r + dr * k) == joueur for k in range(1, 4)):
                    return True
    return False


def _p4_trait(cols) -> str:
    nx = sum(col.count(X) for col in cols)
    no = sum(col.count(O) for col in cols)
    return X if nx == no else O


def _p4_terminal_value(cols):
    """Renvoie +1 (X gagne), −1 (O gagne), 0 (plein/nul), ou None (partie en cours)."""
    if _p4_gagne(cols, X):
        return 1.0
    if _p4_gagne(cols, O):
        return -1.0
    if all(len(col) == _P4_ROWS for col in cols):
        return 0.0
    return None


def _p4_coups(cols):
    return [c for c in range(_P4_COLS) if len(cols[c]) < _P4_ROWS]


def _p4_applique(cols, c):
    tok = _p4_trait(cols)
    lst = list(cols)
    lst[c] = cols[c] + (tok,)
    return tuple(lst)


def _p4_heuristique(cols) -> float:
    """Évaluation APPROCHÉE (contrôle du centre), STRICTEMENT dans ]-1, 1[ (jamais ±1 : réservé au terminal)."""
    poids = (1, 2, 3, 4, 3, 2, 1)     # colonnes centrales plus valorisées
    raw = 0
    for c in range(_P4_COLS):
        raw += poids[c] * (cols[c].count(X) - cols[c].count(O))
    return 0.9 * raw / (abs(raw) + 10.0)


def _p4_rec(cols, prof, memo):
    """Minimax borné -> (valeur, exacte). exacte=True SSI la valeur est prouvée (aucune coupe de profondeur
    ne la remet en cause) : soit toutes les feuilles de la valeur retenue sont terminales, soit une victoire/
    défaite prouvée (±1) est atteinte (indépassable pour le camp concerné)."""
    cle = (cols, prof)
    if cle in memo:
        return memo[cle]
    tv = _p4_terminal_value(cols)
    if tv is not None:
        memo[cle] = (tv, True)
        return memo[cle]
    if prof <= 0:
        memo[cle] = (_p4_heuristique(cols), False)   # feuille COUPÉE par la profondeur : valeur APPROCHÉE
        return memo[cle]
    maxi = (_p4_trait(cols) == X)
    enfants = [_p4_rec(_p4_applique(cols, c), prof - 1, memo) for c in _p4_coups(cols)]
    vals = [v for v, _ in enfants]
    tous_exacts = all(e for _, e in enfants)
    if maxi:
        best = max(vals)
        exacte = (best == 1.0) or tous_exacts        # une victoire prouvée est indépassable pour MAX
    else:
        best = min(vals)
        exacte = (best == -1.0) or tous_exacts       # une défaite prouvée est indépassable pour MIN
    memo[cle] = (best, exacte)
    return memo[cle]


def puissance4_coup_optimal(plateau, profondeur):
    """Coup optimal Puissance 4 à profondeur BORNÉE. Renvoie {'coup', 'valeur', 'exacte'}.

    'valeur' est du point de vue de 'X' (+1 = X gagne, −1 = O gagne, 0 = nul) ; le joueur au trait maximise
    (X) ou minimise (O). 'exacte'=False signale que la valeur est APPROCHÉE (arbre coupé par la profondeur) —
    Puissance 4 est résolu en théorie mais son arbre complet est hors budget. profondeur ∉ [1,12] -> ValueError.
    """
    cols = _p4_valide(plateau)
    if not _est_entier(profondeur) or profondeur < 1:
        raise ValueError("profondeur invalide : entier ≥ 1 requis (bool refusé)")
    if profondeur > _P4_PROF_MAX:
        raise ValueError(f"profondeur > {_P4_PROF_MAX} : hors budget (l'arbre complet de Puissance 4 est trop grand)")
    if _p4_terminal_value(cols) is not None:
        raise ValueError("position terminale (gagnée ou pleine) : aucun coup à jouer")
    coups = _p4_coups(cols)
    if not coups:
        raise ValueError("plateau plein : aucun coup à jouer")
    maxi = (_p4_trait(cols) == X)
    memo: dict = {}
    enfants = [(c,) + _p4_rec(_p4_applique(cols, c), profondeur - 1, memo) for c in coups]  # (c, v, e)
    vals = [v for _, v, _ in enfants]
    best = max(vals) if maxi else min(vals)
    coup = min(c for c, v, _ in enfants if v == best)         # déterministe : plus petite colonne optimale
    tous_exacts = all(e for _, _, e in enfants)
    if maxi:
        exacte = (best == 1.0) or tous_exacts
    else:
        exacte = (best == -1.0) or tous_exacts
    return {"coup": coup, "valeur": best, "exacte": bool(exacte)}


# ════════════════════════════════════════════════════════════════════════════════════════════════════════════════
# (d) CATALOGUE DES RÈGLES + dispatcher de coup optimal
# ════════════════════════════════════════════════════════════════════════════════════════════════════════════════
_CATALOGUE = ("morpion", "nim", "puissance4", "echecs", "go")

_REGLES = {
    "morpion": {
        "nom": "Morpion (tic-tac-toe)",
        "joueurs": 2,
        "information": "parfaite",
        "plateau": "grille 3×3",
        "but": "aligner 3 de ses symboles (ligne, colonne ou diagonale)",
        "nulle": "grille pleine sans alignement",
        "resolu": "oui — jeu parfait = NULLE (valeur 0)",
    },
    "nim": {
        "nom": "Nim (jeu normal)",
        "joueurs": 2,
        "information": "parfaite",
        "plateau": "plusieurs tas d'allumettes",
        "but": "prendre la DERNIÈRE allumette (jeu normal) ; à son tour on retire ≥ 1 allumette d'un seul tas",
        "perte": "le joueur qui ne peut plus jouer perd",
        "resolu": "oui — théorème de Bouton : position perdante ssi somme de Nim (XOR) = 0",
    },
    "puissance4": {
        "nom": "Puissance 4 (Connect Four)",
        "joueurs": 2,
        "information": "parfaite",
        "plateau": "grille 7 colonnes × 6 lignes, gravité",
        "but": "aligner 4 jetons (horizontal, vertical ou diagonal)",
        "nulle": "grille pleine sans alignement",
        "resolu": "oui en théorie — victoire du PREMIER joueur (arbre complet hors budget ici)",
    },
    "echecs": {
        "nom": "Échecs",
        "joueurs": 2,
        "information": "parfaite",
        "plateau": "échiquier 8×8",
        "but": "mater le roi adverse",
        # Les QUATRE conditions de nulle nommées (règles FIDE) :
        "nulles": ("pat", "règle des 50 coups", "triple répétition", "matériel insuffisant"),
        "resolu": "non — le module NE joue PAS aux échecs",
    },
    "go": {
        "nom": "Go",
        "joueurs": 2,
        "information": "parfaite",
        "plateau": "goban 19×19 (aussi 9×9, 13×13)",
        "but": "contrôler le plus de territoire (+ prisonniers), selon comptage territoire ou aire",
        "resolu": "non — le module NE joue PAS au go",
    },
}


def regles(jeu) -> dict:
    """Règles ESSENTIELLES d'un jeu institué (copie profonde, non mutable). Jeu hors catalogue -> ValueError."""
    if not isinstance(jeu, str):
        raise ValueError("jeu invalide : une chaîne est requise")
    j = jeu.strip().lower()
    if j not in _REGLES:
        raise ValueError(f"jeu hors catalogue : {jeu!r} (connus : {', '.join(sorted(_REGLES))})")
    return copy.deepcopy(_REGLES[j])


def coup_optimal(jeu, etat=None):
    """Coup optimal EXACT + valeur du jeu pour un jeu institué RÉSOLU. Renvoie (coup, valeur).

    - 'morpion' : DÉLÉGUÉ à strategie_jeux (minimax exhaustif) ; valeur +1/−1/0 du point de vue de 'X'.
    - 'nim' : coup de Bouton (index, nb) ; valeur +1 (le joueur au trait gagne). Position perdante -> ValueError.
    - 'echecs' / 'go' : ValueError explicite — le module ne prétend PAS jouer.
    - 'puissance4' : ValueError — résolu en théorie mais hors budget ; utiliser puissance4_coup_optimal(plateau, profondeur).
    - jeu hors catalogue -> ValueError.
    """
    if not isinstance(jeu, str):
        raise ValueError("jeu invalide : une chaîne est requise")
    j = jeu.strip().lower()
    if j not in _CATALOGUE:
        raise ValueError(f"jeu hors catalogue : {jeu!r}")
    if j in ("echecs", "go"):
        raise ValueError(f"le module ne prétend PAS jouer aux {j} : coup optimal non fourni (abstention)")
    if j == "puissance4":
        raise ValueError(
            "Puissance 4 : jeu résolu en théorie mais arbre complet hors budget ; "
            "utilisez puissance4_coup_optimal(plateau, profondeur) (valeur bornée, possiblement non exacte)"
        )
    if j == "morpion":
        coup = _sj.morpion_coup_optimal(etat)       # lève ValueError si plateau invalide / terminal
        valeur = _sj.valeur_minimax(etat)
        return (coup, valeur)
    if j == "nim":
        coup = nim_coup_gagnant(etat)               # lève ValueError si position perdante / tas invalide
        return (coup, 1)                            # position gagnante : le joueur au trait gagne (+1)
    raise ValueError(f"jeu non traité : {jeu!r}")   # garde défensive
