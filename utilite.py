"""
Brique « UTILITÉ ÉVOLUTIVE » — garder le plus utile, supplanter, re-juger.

La vision de Yohan : « Utile ? on garde. Inutile ? on jette. Et la logique évolue,
rien n'est figé. » Le store (B2) garde tout, à jamais. Ici on ajoute la couche qui
manquait : l'utilité n'est plus BINAIRE (passe/passe pas) et le choix n'est plus
DÉFINITIF.

  - Utilité RICHE, jugée par le RÉEL (jamais par l'IA elle-même — sinon dérive) :
        correct  (passe les tests visibles — prérequis)
        + généralise (passe le held-out)
        + robuste    (survit au fuzz)
        + simple     (code plus court)
        + rapide     (s'exécute plus vite)
    Ordre lexicographique : généralise d'abord, puis robuste, puis simple, puis rapide.

  - On garde LE PLUS UTILE par tâche ; une meilleure solution SUPPLANTE l'ancienne.

  - RIEN N'EST FIGÉ : reevalue() re-juge les solutions gardées quand l'expérience
    grandit (fuzz plus strict, tests élargis...). Ce qui semblait utile peut être
    dépassé -> le meilleur change. La logique évolue.
"""

from __future__ import annotations

import dataclasses

from fuzz import crible
from juge import Limites, juge


@dataclasses.dataclass(frozen=True)
class Utilite:
    """Combien une solution est utile — mesuré par le réel, pas déclaré."""
    correct: bool        # passe les tests visibles (prérequis pour être gardée)
    generalise: bool     # passe le held-out (du non-vu)
    robuste: bool        # survit au fuzz (entrées aberrantes)
    taille: int          # longueur du code (plus petit = plus utile)
    duree: float         # temps d'exécution (plus court = plus utile)

    @property
    def cle(self):
        """Clé de comparaison : plus grande = plus utile (ordre lexicographique)."""
        return (self.generalise, self.robuste, -self.taille, -self.duree)


def evalue_utilite(tache, solution: str, verdict, limites: Limites | None = None,
                   n_fuzz: int = 60) -> Utilite:
    """Mesure l'utilité d'une solution. Tout est tranché par le juge/crible, pas par avis."""
    correct = verdict.passe
    generalise = correct and (
        not tache.tests_held_out or juge(solution, tache.tests_held_out, limites).passe)
    robuste = correct and (
        not (tache.gen_entrees and tache.point_entree)
        or crible(tache, solution, n_essais=n_fuzz, limites=limites).robuste)
    return Utilite(correct=correct, generalise=bool(generalise), robuste=bool(robuste),
                   taille=len(solution.strip()), duree=verdict.duree_s)


class Selection:
    """
    Garde, par tâche, la solution LA PLUS UTILE ; les autres sont conservées comme
    prétendantes mais ne sont pas « le meilleur ». reevalue() re-juge tout : rien
    n'est figé. Compte les supplantations (le pouls de l'évolution de la logique).
    """

    def __init__(self, limites: Limites | None = None, n_fuzz: int = 60):
        self.limites = limites
        self.n_fuzz = n_fuzz
        self._cands: dict[str, list] = {}   # tache_id -> [(solution, Utilite, tache)]
        self.supplantations = 0

    @staticmethod
    def _meilleur(lst):
        return max(lst, key=lambda e: e[1].cle) if lst else None

    def offre(self, tache, solution: str, verdict) -> bool:
        """
        Propose une solution vérifiée. Renvoie True si elle DEVIENT le meilleur de
        sa tâche. Garde-fou : une solution non correcte n'entre pas.
        """
        u = evalue_utilite(tache, solution, verdict, self.limites, self.n_fuzz)
        if not u.correct:
            return False
        lst = self._cands.setdefault(tache.id, [])
        avant = self._meilleur(lst)
        lst.append((solution, u, tache))
        apres = self._meilleur(lst)
        if avant is not None and apres[0] != avant[0]:
            self.supplantations += 1
        return apres[0] == solution

    def meilleur(self, tache_id: str):
        b = self._meilleur(self._cands.get(tache_id, []))
        return b[0] if b else None

    def utilite(self, tache_id: str):
        b = self._meilleur(self._cands.get(tache_id, []))
        return b[1] if b else None

    def reevalue(self, taches_maj: dict | None = None, n_fuzz: int | None = None) -> int:
        """
        Re-juge toutes les solutions gardées — par ex. parce que l'EXPÉRIENCE a
        grandi : fuzz plus strict (n_fuzz), ou tâche enrichie de nouveaux tests
        (taches_maj : tache_id -> Tache mise à jour). Renvoie le nombre de tâches
        dont le MEILLEUR a changé. C'est le « rien n'est figé » : ce qui passait
        pour le plus utile peut être dépassé quand on en sait plus.
        """
        taches_maj = taches_maj or {}
        nf = n_fuzz or self.n_fuzz
        change = 0
        for tid, lst in list(self._cands.items()):
            avant = self._meilleur(lst)
            rescored = []
            for (s, _, t) in lst:
                t2 = taches_maj.get(tid, t)
                v = juge(s, t2.tests, self.limites)
                rescored.append((s, evalue_utilite(t2, s, v, self.limites, nf), t2))
            self._cands[tid] = rescored
            apres = self._meilleur(rescored)
            if avant and apres and avant[0] != apres[0]:
                change += 1
                self.supplantations += 1
        return change
