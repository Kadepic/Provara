"""
Brique 9 — LA SESSION D'ENTRAÎNEMENT (l'orchestrateur complet).

Toutes les briques en UNE boucle d'auto-amélioration, de bout en bout :

  CURATEUR sert le palier courant (du facile au dur)
     -> BOUCLE générer -> juger -> [OBSERVATOIRE anti-triche] -> garder (STORE)
        -> MESURE de la réussite et de la généralisation
           -> APPRENDRE (ici simulé ; en réel = fine-tune sur le store, sur GPU)
              -> le CURATEUR monte de palier quand le modèle généralise assez
                 -> on recommence, plus dur.

C'est le squelette vivant du projet (cf. PROJET-AUTO-AMELIORATION-CODE.md §3, §9).
Une seule pièce reste factice : le générateur (et donc l'étape APPRENDRE). Tout le
reste est réel. Quand on branchera un vrai LLM local, on ne changera QUE ça.
"""

from __future__ import annotations

import dataclasses

from boucle import tour
from juge import Limites
from mesure import evalue


@dataclasses.dataclass
class Etape:
    """Le compte-rendu d'un tour de session."""
    tour: int
    niveau: int               # palier de difficulté servi ce tour
    taches: int               # nb de tâches du lot servi
    store: int                # taille du store (succès vérifiés cumulés)
    reussite: float           # réussite moyenne sur le lot (tests visibles)
    generalisation: float     # généralisation moyenne sur le lot (held-out)
    monte: bool               # le curateur a-t-il débloqué le palier suivant ?

    def resume(self) -> str:
        fleche = "  ↑palier" if self.monte else ""
        return (f"  tour {self.tour:>2} | niveau {self.niveau} | {self.taches} tâche(s) | "
                f"store={self.store:>2} | réussite={self.reussite:>4.0%} | "
                f"généralisation={self.generalisation:>4.0%}{fleche}")


def _moyenne(valeurs: list[float]) -> float:
    return sum(valeurs) / len(valeurs) if valeurs else 0.0


def session(generateur, curateur, store, n: int = 8, max_tours: int = 15,
            n_eval: int = 10, limites: Limites | None = None,
            inspecteur=None, selection=None) -> list[Etape]:
    """
    Lance une session d'entraînement complète et renvoie le journal (un Etape/tour).

    Un tour = collecter des succès sur le palier courant, apprendre dessus, se
    mesurer, et faire avancer le curriculum si la généralisation est au rendez-vous.
    S'arrête quand on est au dernier palier ET que la généralisation y est haute.

    Si une `selection` (utilité évolutive, B10) est fournie, la phase GARDER ne se
    contente plus d'empiler : elle conserve, par tâche, la solution LA PLUS UTILE,
    supplante le moins bon, et reste révisable. La logique gardée évolue.
    """
    journal: list[Etape] = []

    for t in range(max_tours):
        niveau = curateur.niveau
        lot = curateur.lot()

        # 1. COLLECTER : une passe de boucle sur chaque tâche du palier -> store + selection.
        for tache in lot:
            tour(generateur, store, tache, n, limites, inspecteur, selection)

        # 2. APPRENDRE : le modèle se renforce sur ses succès vérifiés.
        #    (factice : on monte la compétence ; réel : fine-tuning sur le store.)
        generateur.apprendre()

        # 3. MESURER : réussite + généralisation sur le lot (du non-vu pour le held-out).
        mesures = [evalue(generateur, tache, n_eval, limites) for tache in lot]
        reussite = _moyenne([r for r, _ in mesures])
        generalisation = _moyenne([g for _, g in mesures])

        # 4. GRADUER : le curateur débloque le palier suivant si on généralise assez.
        monte = curateur.progresse(generalisation)

        journal.append(Etape(tour=t, niveau=niveau, taches=len(lot), store=len(store),
                             reussite=reussite, generalisation=generalisation, monte=monte))

        # Arrêt : au sommet du curriculum et généralisation haute -> rien de plus à faire.
        if curateur.fini() and generalisation >= 0.95:
            break

    return journal
