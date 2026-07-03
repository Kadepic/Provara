"""
HELPERS COMMUNS DES VALIDATEURS — pensée machine : juger le RÉSULTAT, jamais l'étage/mécanisme.

Loi transverse (Yohan 2026-07-02) : un test doit vérifier que la tâche est RÉSOLUE et GÉNÉRALISE (au chemin le plus
efficace choisi par le routeur), pas quel mécanisme/étage l'a produite — vouloir figer l'étage est un biais humain qui
casse dès que le routeur trouve mieux (et contredit le comportement désiré). La vivacité d'une brique spécialiste se
prouve par appel DIRECT de son générateur (hors routeur), pas en imposant qu'une tâche-sonde y route.

FAUX=0 PRÉSERVÉ : `generalise` (held-out) reste dans l'assertion de résultat — une coïncidence (passe le visible,
rate le held-out) donne generalise=False -> l'assertion échoue. Les contrôles négatifs de soundness (`not inc.ok`)
ne passent PAS par ici : ils testent l'absence de résolution (HORS honnête), on les garde tels quels.
"""
from __future__ import annotations

from juge import Limites, juge
from taches import Tache


def resolu(rep, generalise: bool = True) -> bool:
    """RÈGLE 1 — assertion de RÉSULTAT. Remplace `x.ok and x.etage == "X" and x.generalise`. L'étage est LIBRE
    (la voie la moins chère qui donne la bonne réponse = désiré). `generalise` (held-out) garde FAUX=0."""
    return bool(getattr(rep, "ok", False)) and (bool(getattr(rep, "generalise", False)) if generalise else True)


def brique_vivante(generateur, fn: str, sig: str, tests: str, held: str, n: int = 600,
                   temps_s: float = 3, cpu_s: float = 2) -> bool:
    """RÈGLE 2 — VIVACITÉ (anti-code-mort) d'une brique spécialiste par appel DIRECT de son générateur, HORS
    routeur : le générateur résout SA tâche canonique (tests + held-out DUR obligatoire). Remplace le rôle
    anti-code-mort du pin d'étage. Renvoie True ssi une solution passe tests ET held-out."""
    t = Tache(id=fn, point_entree=fn, prompt=f'def {fn}({sig}):\n    """..."""', tests=tests, tests_held_out=held)
    lim = Limites(temps_s=temps_s, cpu_s=cpu_s)
    for code in generateur.propose(t.prompt, n):
        if juge(code, t.tests, lim).passe and (not t.tests_held_out or juge(code, t.tests_held_out, lim).passe):
            return True
    return False


def cout_borne(rep_chaud, rep_froid, marge: int = 0) -> bool:
    """RÈGLE 3 — cas 'invariance' (le contexte chaud ne dégrade pas) : les deux résolvent+généralisent ET le coût
    chaud ne dépasse pas le froid (+marge). Remplace `chaud.etage == froid.etage` sans figer le mécanisme."""
    return (resolu(rep_chaud) and resolu(rep_froid)
            and getattr(rep_chaud, "appels", 0) <= getattr(rep_froid, "appels", 0) + marge)
