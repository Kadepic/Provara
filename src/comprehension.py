"""
LA COMPRÉHENSION (1/2) — abstraire par compression (le « sommeil »).

Tout le reste du harnais est de la sélection AVEUGLE : on garde ce qui passe sans
comprendre pourquoi. Ici, le premier pas de la compréhension : regarder le store,
voir que plusieurs succès PARTAGENT une structure et ne diffèrent que par un SENS
(le prédicat, la condition), et en extraire une ABSTRACTION — un concept réutilisable.

« Comprendre, c'est compresser » : passer de « je garde N solutions » à « j'ai saisi
le principe qui les engendre ». Et — garde-fou n°1 — une abstraction n'est dite
COMPRISE que si, régénérée puis re-jugée, elle couvre RÉELLEMENT tous ses cas.
La compréhension reste jugée par le réel, jamais déclarée.
"""

from __future__ import annotations

import dataclasses

from generateur import TYPES_CONDITIONS, fragments_riches
from juge import Limites, juge


@dataclasses.dataclass(frozen=True)
class Abstraction:
    """Un concept : une structure (squelette à trou) + les SENS vus qui l'instancient."""
    squelette: str                 # ex. "sum((1 for x in args[0] if {C}))"
    instances: tuple               # ((slot, tache_id), ...) — les cas compris

    @property
    def couverture(self) -> int:
        return len(self.instances)

    @property
    def sens(self) -> tuple:
        return tuple(slot for slot, _ in self.instances)

    def genere(self, point_entree: str, slot: str) -> str:
        """Régénère une solution en instanciant le concept avec un sens donné."""
        return f"def {point_entree}(*args, **kwargs):\n    return {self.squelette.replace('{C}', slot)}\n"


def _paires(solution: str, types=TYPES_CONDITIONS):
    """(squelette, sens) extractibles d'une solution : la structure, et le fragment
    qu'on peut en retirer (le morceau interchangeable = le sens). `types` règle la
    RICHESSE du vocabulaire (cf. `fragments_riches`) — défaut : les conditions (historique) ;
    `TYPES_RICHES` ajoute opérations binaires et agrégations."""
    try:
        expr, fragments = fragments_riches(solution, types)
    except SyntaxError:
        return []
    if expr is None:
        return []
    return [(expr.replace(c, "{C}", 1), c) for c in fragments if c in expr]


def abstrais(store, types=TYPES_CONDITIONS):
    """
    Compresse le store en abstractions. Renvoie (abstractions, squelettes_singletons).
    Une abstraction = un squelette vu avec AU MOINS DEUX sens distincts (généralisation).
    Un squelette vu une seule fois reste un singleton : pas encore un concept.
    `types` règle la richesse du vocabulaire miné (cf. `_paires`).
    """
    groupes: dict[str, dict[str, str]] = {}   # squelette -> {sens: tache_id}
    for s in store:
        for squelette, sens in _paires(s.solution, types):
            groupes.setdefault(squelette, {}).setdefault(sens, s.tache_id)

    abstractions, singletons = [], []
    for squelette, sens_vus in groupes.items():
        if len(sens_vus) >= 2:
            abstractions.append(Abstraction(squelette, tuple(sorted(sens_vus.items()))))
        else:
            singletons.append(squelette)
    return abstractions, singletons


class Predicteur:
    """
    LA COMPRÉHENSION (2/2) — anticiper le réel.

    Prédit si un candidat passera le juge SANS l'exécuter, à partir des concepts
    appris : un candidat est un squelette CONNU rempli d'un sens CONNU. Le point
    clé : il prédit juste même des COMBINAISONS NEUVES (squelette d'une tâche + sens
    d'une autre, jamais vus ensemble) -> il comprend, il ne mémorise pas.

    Conservateur : ce qu'il ne reconnaît pas, il le prédit « non » (pas de fausse
    confiance). Et — garde-fou — une prédiction ne vaut que VÉRIFIÉE ensuite par le
    juge : ici on MESURE sa justesse, on ne lui fait jamais aveuglément confiance.
    Sa valeur : DIRIGER (essayer d'abord le prédit-utile), de plus en plus juste.

    DEUX MÉMOIRES (le principe « seul le juge promeut ») :
      - mémoire LONGUE = `squelettes` + `sens`, apprise du store -> les positifs
        CONFIRMÉS par le juge. Durable, mais jamais une liste noire.
      - mémoire COURTE = `_echecs_courts`, les croisements RÉFUTÉS récemment par le
        juge. Transitoire, vit en RAM, n'est JAMAIS écrite dans le store : un faux
        pari rétrograde le candidat (`rang`), mais ne devient pas un savoir durable.
    Un croisement réfuté est EXPULSÉ vers le bas, pas BANNI (`oublie()` l'efface) :
    ce qui est faux aujourd'hui peut redevenir candidat demain (contexte changé).
    """

    def __init__(self, store=None, types=TYPES_CONDITIONS):
        self.squelettes: set[str] = set()   # \
        self.sens: set[str] = set()         # /  mémoire LONGUE (confirmée par le juge)
        self._echecs_courts: set[str] = set()  # mémoire COURTE (réfutés récents, RAM, jamais gravée)
        self._types = types   # le vocabulaire que ce prédicteur sait reconnaître
        if store is not None:
            self.apprends(store)

    def apprends(self, store) -> None:
        for s in store:
            for squelette, sens in _paires(s.solution, self._types):
                self.squelettes.add(squelette)
                self.sens.add(sens)

    def predit_passe(self, solution: str) -> bool:
        """Anticipe (sans juger) : squelette connu rempli d'un sens connu -> oui."""
        for squelette, sens in _paires(solution, self._types):
            if squelette in self.squelettes and sens in self.sens:
                return True
        return False

    def note_echec(self, solution: str) -> None:
        """Le juge a RÉFUTÉ ce candidat -> mémoire COURTE (le rétrograder ensuite).
        N'écrit rien de durable : c'est un brouillon, pas un savoir gravé."""
        self._echecs_courts.add(solution)

    def oublie(self) -> None:
        """Efface la mémoire courte : on n'a rien banni, la porte se rouvre."""
        self._echecs_courts.clear()

    def rang(self, solution: str) -> int:
        """Promesse d'un candidat pour DIRIGER (petit = à juger tôt) :
          0 = prédit-utile et pas encore réfuté  -> en premier ;
          1 = inconnu (ni reconnu, ni réfuté)     -> au milieu (peut surprendre) ;
          2 = déjà réfuté récemment (court terme) -> en dernier (mais jamais jeté)."""
        if solution in self._echecs_courts:
            return 2
        return 0 if self.predit_passe(solution) else 1


def confirme(abstraction: Abstraction, taches: dict, limites: Limites | None = None) -> bool:
    """
    L'abstraction est-elle COMPRISE (pas juste plausible) ? On régénère chaque
    instance et on la re-juge contre sa tâche d'origine. Tout doit passer : la
    compression doit être LOSSLESS — le concept couvre vraiment ses cas.
    """
    for slot, tache_id in abstraction.instances:
        t = taches[tache_id]
        code = abstraction.genere(t.point_entree, slot)
        if not juge(code, t.tests, limites).passe:
            return False
    return True
