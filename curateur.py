"""
Brique 8 — LE CURATEUR.

La matière première vient de l'EXTÉRIEUR (toi, moi, un dataset), JAMAIS du modèle
lui-même — sinon il choisirait des problèmes faciles ou auto-référentiels et
« progresserait » dans le vide (cf. la discussion : c'est le 2e garde-fou, distinct
du juge). Le curateur sert des exercices, du facile au dur, au fil des progrès.

Deux responsabilités :

  1. AUTO-VALIDER chaque tâche (le garde-fou sur le curateur) : sa solution de
     référence doit passer ses propres tests visibles ET held-out, ET survivre au
     fuzz. Une tâche bancale est REJETÉE. Ainsi le juge garde le modèle honnête
     (pas de faux succès) ET le curateur honnête (pas d'exercice truqué).

  2. GRADUER : servir les tâches du palier courant, et monter de palier quand le
     modèle généralise assez (signal mesuré par B7). Le programme d'études qui
     s'adapte — du facile au dur, sans qu'on le dicte tâche par tâche.
"""

from __future__ import annotations

import dataclasses

from juge import Limites, juge


# --- 1. L'auto-validation des tâches ----------------------------------------

@dataclasses.dataclass(frozen=True)
class RapportTache:
    """Bilan de santé d'une tâche proposée au curriculum."""
    valide: bool
    raisons: list[str]      # ce qui cloche (vide si valide)


def _harnais_robustesse(tache, n: int, seed: int = 0) -> str:
    """Programme qui passe la référence sur les entrées de son PROPRE générateur,
    sans oracle : si la référence lève quoi que ce soit, c'est un crash (ERROR)."""
    fn = tache.point_entree
    return f'''
import random as _r
{tache.gen_entrees}
_rng = _r.Random({seed})
for _i in range({n}):
    _inp = _gen(_rng)
    {fn}(*_inp)
'''


def valide_tache(tache, n_fuzz: int = 120, limites: Limites | None = None) -> RapportTache:
    """
    Vérifie qu'une tâche est saine AVANT de la servir. Le juge tranche, comme
    pour le modèle : la référence doit réellement passer, sinon la tâche est fausse.
    """
    raisons: list[str] = []

    if not tache.solution_ref:
        raisons.append("pas de solution de référence (rien ne prouve la tâche solvable)")
    if not tache.tests:
        raisons.append("pas de tests visibles")

    if not raisons:
        v = juge(tache.solution_ref, tache.tests, limites)
        if not v.passe:
            raisons.append(f"la référence ÉCHOUE ses propres tests visibles (statut={v.statut})")

        if tache.tests_held_out:
            vh = juge(tache.solution_ref, tache.tests_held_out, limites)
            if not vh.passe:
                raisons.append(f"la référence ÉCHOUE le held-out (statut={vh.statut})")

        # Auto-robustesse : la référence ne doit pas crasher sur les entrées que
        # SON PROPRE générateur produit. Sinon générateur et référence sont
        # incohérents (domaine mal défini) -> tâche bancale. (≠ fuzz différentiel
        # de B6, qui éprouve un CANDIDAT contre la référence-oracle.)
        if tache.gen_entrees and tache.point_entree:
            vr = juge(tache.solution_ref, _harnais_robustesse(tache, n_fuzz), limites)
            if not vr.passe:
                raisons.append(f"la référence ne survit pas à son propre générateur "
                               f"(statut={vr.statut}) : générateur/domaine incohérents")

    return RapportTache(valide=not raisons, raisons=raisons)


# --- 2. Le curateur gradué --------------------------------------------------

class CurateurGradue:
    """
    Sert un curriculum gradué. À la construction, AUTO-VALIDE toutes les tâches et
    n'en retient que les saines (les rejetées sont listées dans .rejetees).

    Progression : on démarre au niveau le plus facile. À chaque palier, quand le
    modèle généralise au-delà de `seuil`, on débloque le niveau suivant. Le lot
    servi est CUMULATIF (tâches de difficulté <= niveau) : on garde les faciles
    en rotation -> entretien des acquis, synergie avec le rejeu anti-oubli.
    """

    def __init__(self, taches, seuil: float = 0.7, n_fuzz: int = 120,
                 limites: Limites | None = None):
        self.seuil = seuil
        self.valides = []
        self.rejetees = []   # [(tache, RapportTache)] — la transparence sur ce qui est écarté
        for t in taches:
            rapport = valide_tache(t, n_fuzz=n_fuzz, limites=limites)
            (self.valides if rapport.valide else self.rejetees).append(
                t if rapport.valide else (t, rapport))

        self._niveaux = sorted({t.difficulte for t in self.valides})
        self._i = 0   # index dans _niveaux

    @property
    def niveau(self) -> int:
        return self._niveaux[self._i] if self._niveaux else 0

    def lot(self) -> list:
        """Les tâches du palier courant (cumulatif : difficulté <= niveau courant)."""
        return [t for t in self.valides if t.difficulte <= self.niveau]

    def progresse(self, generalisation: float) -> bool:
        """
        Monte d'un palier si le modèle généralise assez. Renvoie True si on a
        avancé. Au dernier palier, reste là (rien de plus dur à servir).
        """
        if generalisation >= self.seuil and self._i < len(self._niveaux) - 1:
            self._i += 1
            return True
        return False

    def fini(self) -> bool:
        """Vrai si on est au dernier palier (plus rien de plus dur à proposer)."""
        return self._i >= len(self._niveaux) - 1
