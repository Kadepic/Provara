"""
MOTEUR D'AUTO-INVENTION — exploration AUTONOME jugée par la réalité (2026-06-18, cap « réseau de réflexion qui ne
dépend pas de la vision humaine », cf. mémoire project-vision-auto-evolution-verite).

L'invention par mutation (GenerateurInvention) et le compounding sur l'inventé existent déjà — MAIS dirigés : un
humain désigne chaque tâche-cible. Ici on enlève l'humain de la boucle de DÉCOUVERTE : le moteur mute son propre
répertoire et GARDE tout atome que la RÉALITÉ valide — sans qu'on lui dise quoi chercher. « Jugé par la vérité » sans
tâche = exécution : l'atome doit être DÉTERMINISTE, TOTAL sur le domaine sondé, et BEHAVIORALEMENT NOUVEAU (empreinte
d'E/S jamais vue), et rester total sur des entrées HELD-OUT (il généralise, pas un hasard sur les sondes).

Mesure de la valeur (sans cible humaine) : après exploration autonome, le moteur résout des tâches INATTEIGNABLES
depuis la graine — parce que le répertoire s'est étendu SEUL. C'est la vision en miniature : elle teste le possible,
garde le vérifié, et ça débloque ce qu'on n'avait pas mis en place.

Borné (esprit brique par brique) : mutation simple (un site), atomes unaires sur args[0], budget de rounds.
"""
from __future__ import annotations

import ast

from generateur import GenerateurInvention
from juge import Limites, juge

LIM = Limites(temps_s=3, cpu_s=2)
SONDES = (0, 1, 2, 3, 5, -1, -2)          # domaine d'empreinte (la réalité teste le comportement E/S)
HELD_OUT = (4, 7, 10, -3, 8, -5)          # entrées disjointes : un atome gardé doit y rester total (généralise)


def _fn(expr: str):
    ns: dict = {}
    try:
        exec(f"def _f(*args, **kwargs):\n    return {expr}\n", ns)
    except Exception:
        return None
    return ns.get("_f")


def _empreinte(expr: str, entrees):
    """Empreinte comportementale = (sorties sur `entrees`), ou None si crash / non-déterministe / non-entier."""
    fn = _fn(expr)
    if fn is None:
        return None
    out = []
    for x in entrees:
        try:
            r = fn(x)
        except Exception:
            return None
        if not isinstance(r, int) or isinstance(r, bool):
            return None
        if fn(x) != r:                    # déterminisme (deux appels -> même valeur)
            return None
        out.append(r)
    return tuple(out)


def _expr_retour(src: str):
    node = GenerateurInvention._expr_retour(src)
    if node is None:
        return None
    try:
        return ast.unparse(node)
    except Exception:
        return None


class MoteurAutoInvention:
    """Répertoire d'atomes (expressions unaires) qui s'ÉTEND SEUL par mutation, jugé par l'exécution."""

    def __init__(self, primitives=None, seed: int = 0):
        self.exprs = list(primitives or ["args[0]", "args[0] * args[0]", "args[0] + 1"])
        self._seed = seed
        self.empreintes = {}                # empreinte -> expr (garantit la nouveauté comportementale)
        for e in list(self.exprs):
            fp = _empreinte(e, SONDES)
            if fp is not None:
                self.empreintes.setdefault(fp, e)
        self.inventes = []                  # exprs mintées AUTONOMEMENT (hors graine)

    def explore(self, rounds: int = 5, par_round: int = 3000):
        """Mute le répertoire courant ; garde tout atome déterministe, total, NOUVEAU et qui généralise (held-out).
        Itère (les atomes mintés deviennent matière à mutation -> compounding de l'invention). S'arrête à sec."""
        a_sec = 0
        for r in range(rounds):
            atomes = [(f"a{i}", f"def a{i}(*args, **kwargs):\n    return {e}\n") for i, e in enumerate(self.exprs)]
            inv = GenerateurInvention(atomes, seed=self._seed + r)
            neuf = 0
            for src in inv.propose('def cand(x):\n    """x"""\n', par_round):
                expr = _expr_retour(src)
                if expr is None:
                    continue
                fp = _empreinte(expr, SONDES)
                if fp is None or fp in self.empreintes:           # invalide ou déjà connu comportementalement
                    continue
                if _empreinte(expr, HELD_OUT) is None:            # ne généralise pas (crash hors sondes) -> rejet
                    continue
                self.empreintes[fp] = expr
                self.exprs.append(expr)
                self.inventes.append(expr)
                neuf += 1
            a_sec = a_sec + 1 if neuf == 0 else 0
            if a_sec >= 2:
                break
        return self.inventes

    def resoudre(self, tache):
        """Le répertoire (graine + inventé) résout-il une tâche réelle ? (juge sur visible + held-out)."""
        for expr in self.exprs:
            code = f"def {tache.point_entree}(*args, **kwargs):\n    return {expr}\n"
            if juge(code, tache.tests, LIM).passe and (
                    not tache.tests_held_out or juge(code, tache.tests_held_out, LIM).passe):
                return code
        return None


if __name__ == "__main__":
    m = MoteurAutoInvention()
    mintes = m.explore()
    print(f"Exploration AUTONOME (sans tâche humaine) : {len(mintes)} atomes mintés et vérifiés par la réalité.")
    print(f"Répertoire : {len(m.exprs)} atomes (graine {len(m.exprs) - len(mintes)} + inventés {len(mintes)}).")
    print("Échantillon d'atomes auto-inventés (expr unaire sur args[0]) :")
    for e in mintes[:14]:
        print(f"    {e}")
