"""
DELTA-DEBUGGING (ddmin) — minimisation de reproducteur d'échec (brique code avancé, 2026-07-02).

POURQUOI : quand une entrée (une liste d'éléments, une séquence de lignes de code, une chaîne) déclenche un
ÉCHEC, la RÉDUIRE au plus petit sous-ensemble qui échoue ENCORE rend le bug lisible et actionnable — c'est LA
primitive de débogage générique (Zeller & Hildebrand, ddmin). Elle alimente la réparation automatique (localiser
la cause) et rend les contre-exemples du fuzzing exploitables.

FAUX=0 :
  • Le résultat rendu DÉCLENCHE TOUJOURS l'échec (`echoue(resultat)` re-vérifiable), et il est 1-MINIMAL :
    retirer n'importe quel élément fait DISPARAÎTRE l'échec. On ne renvoie jamais un « minimal » qui n'échoue pas.
  • Déterministe (découpes et tests dans un ordre fixe). Si l'entrée initiale n'échoue pas -> renvoyée inchangée
    (rien à minimiser ; l'appelant vérifie `echoue` lui-même s'il en doute).
Stdlib pur, souverain. `echoue` est un prédicat fourni par l'appelant (le test/juge) — la réalité tranche.
"""
from __future__ import annotations


def _sans(sequence, indices: set):
    return [x for i, x in enumerate(sequence) if i not in indices]


def _decoupe(n_elems: int, k: int):
    """Bornes des `k` tranches ~égales de [0, n_elems). Renvoie une liste de (debut, fin)."""
    tranches = []
    base = n_elems // k
    reste = n_elems % k
    debut = 0
    for i in range(k):
        taille = base + (1 if i < reste else 0)
        if taille == 0:
            continue
        tranches.append((debut, debut + taille))
        debut += taille
    return tranches


def ddmin(entree, echoue) -> list:
    """Minimise `entree` (séquence) au plus petit sous-ensemble qui satisfait ENCORE `echoue`. `echoue(sous)` -> bool.
    Renvoie une liste 1-minimale telle que echoue(liste) est vrai et retirer tout élément la rend fausse."""
    seq = list(entree)
    if not echoue(seq):
        return seq                                   # ne reproduit pas -> rien à minimiser (honnête)
    n = 2
    while len(seq) >= 2:
        tranches = _decoupe(len(seq), min(n, len(seq)))
        # 1) réduire à un COMPLÉMENT (retirer une tranche) — préféré : converge vite
        reduit = False
        for (a, b) in tranches:
            comp = _sans(seq, set(range(a, b)))
            if comp and echoue(comp):
                seq = comp
                n = max(n - 1, 2)
                reduit = True
                break
        if reduit:
            continue
        # 2) réduire à une TRANCHE seule
        for (a, b) in tranches:
            sous = seq[a:b]
            if sous and echoue(sous):
                seq = sous
                n = 2
                reduit = True
                break
        if reduit:
            continue
        # 3) augmenter la granularité, ou terminer
        if n >= len(seq):
            break
        n = min(len(seq), n * 2)
    return seq


def est_1_minimal(seq, echoue) -> bool:
    """Vérifie qu'aucun élément ne peut être retiré sans faire disparaître l'échec (garde FAUX=0 du résultat)."""
    if not echoue(list(seq)):
        return False
    for i in range(len(seq)):
        if echoue(_sans(seq, {i})):
            return False                             # on pouvait retirer i -> pas minimal
    return True


def minimise_texte(texte: str, echoue_texte, par_ligne: bool = False) -> str:
    """Variante confort : minimise une CHAÎNE (par caractères, ou par lignes si `par_ligne`). `echoue_texte(str)->bool`."""
    unites = texte.splitlines(keepends=True) if par_ligne else list(texte)
    reduit = ddmin(unites, lambda sous: echoue_texte("".join(sous)))
    return "".join(reduit)
