"""
SÉLECTEUR SITUATIONNEL GÉNÉRIQUE — la méta-architecture « façon cerveau » (2026-06-19, vision Yohan : « qu'elle
s'adapte à la situation et décide : là je route par clé, là par X, là par Y… sur ABSOLUMENT TOUS les plans de l'IA »).

PRINCIPE. Un plan de décision a plusieurs VARIANTES interchangeables (même résultat, coût différent). Le Selecteur
apprend, par CLÉ DE SITUATION (lisible AVANT d'agir), la variante la moins chère observée, et la choisit. À froid
(situation jamais vue) -> variante DÉFAUT (sûre). Il se réchauffe par l'usage (apprendre) ou un warm-up amorti.

SÛRETÉ. Le Selecteur ne doit router QUE des variantes à COUVERTURE IDENTIQUE -> le choix est NEUTRE EN CORRECTION
(une mauvaise variante coûte des appels, jamais un faux). C'est l'invariant qui rend la généralisation sûre PARTOUT.

GATE (réalité juge, pas l'humain). Un plan ne mérite un Selecteur QUE si une clé pas chère DISCRIMINE quelle variante
gagne (mesuré). Sinon la variante par défaut suffit. Vérifié :
  - Routage de stratégie (clé tâche) : DISCRIMINE -> per-clé LOO −24 % (cf. mesure_routage_strategie). ADOPTÉ.
  - Switch en cours de tâche / occam-global / cost-ascending : NE DISCRIMINE PAS à l'aveugle -> REFUSÉ (défaut gagne).
Chaque nouveau plan passe ce test avant d'être câblé (cf. roadmap dans REPRISE).

RouteurStrategie (strategies.py) est l'instanciation au plan ROUTAGE. Pour tout autre plan : instancier Selecteur avec
sa cle_fn et son défaut.
"""

from __future__ import annotations


class Selecteur:
    """Sélection situationnelle apprise, réutilisable sur tout plan à variantes interchangeables.

    cle_fn(situation) -> clé hashable lisible sans agir. defaut = variante sûre à froid.
    apprendre(situation, variante, cout) accumule ; predit(situation) rend la variante de coût moyen min, sinon defaut.
    """

    def __init__(self, cle_fn, defaut, variantes=None):
        self._cle_fn = cle_fn
        self._defaut = defaut
        self._variantes = set(variantes) if variantes is not None else None   # None = pas de garde
        self._stats: dict = {}                                                # cle -> {variante: [somme, n]}

    def apprendre(self, situation, variante, cout: float) -> None:
        if self._variantes is not None and variante not in self._variantes:
            return
        c = self._cle_fn(situation)
        d = self._stats.setdefault(c, {})
        s = d.setdefault(variante, [0.0, 0])
        s[0] += cout
        s[1] += 1

    def predit(self, situation):
        d = self._stats.get(self._cle_fn(situation))
        if not d:
            return self._defaut
        return min(d, key=lambda v: d[v][0] / d[v][1])

    def vu(self, situation) -> bool:
        """La situation a-t-elle de l'historique ? (utile pour cascader : chaud -> Selecteur, froid -> défaut/autre plan)."""
        return bool(self._stats.get(self._cle_fn(situation)))

    def etat(self) -> dict:
        return {c: {v: round(s[0] / s[1], 1) for v, s in d.items()} for c, d in self._stats.items()}
