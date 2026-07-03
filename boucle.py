"""
Brique 4 — LA BOUCLE d'orchestration.

C'est ici que les trois briques se rejoignent en UNE mécanique :

    GÉNÉRER   (le générateur propose N candidats pour une tâche)
       -> JUGER     (le juge tranche chaque candidat sur les tests cachés)
          -> GARDER    (le store archive UNIQUEMENT ce qui a réellement passé)

(cf. PROJET-AUTO-AMELIORATION-CODE.md §3 — la boucle d'auto-amélioration.)

La 5e étape du pattern (APPRENDRE = ré-entraîner le modèle sur ses succès) se
fait hors d'ici, sur GPU : la boucle PRODUIT le jeu de ré-entraînement (le store),
elle ne fait pas le fine-tuning. Ici, tout est testable sans modèle (factice).

Principe d'observabilité (Décision C du plan) : la boucle ne fait rien en
silence. Chaque tour renvoie un Rapport chiffré — proposés, verdicts par statut,
archivés, doublons — pour qu'on VOIE le tri "garder seulement ce qui passe".
"""

from __future__ import annotations

import dataclasses

from generateur import Generateur
from juge import Limites, juge
from store import Store


@dataclasses.dataclass
class Rapport:
    """Le compte-rendu chiffré d'un tour de boucle sur une tâche."""
    tache_id: str
    proposes: int                       # combien de candidats demandés/produits
    par_statut: dict[str, int]          # {pass, fail, timeout, killed, error: n}
    archives: int                       # succès NOUVEAUX ajoutés au store
    doublons: int                       # succès qui passaient mais déjà connus
    suspects: int = 0                   # passants ÉCARTÉS par l'inspecteur (exploit/hard-coding)

    @property
    def passes(self) -> int:
        """Combien ont réellement passé le juge (archivés + doublons + suspects)."""
        return self.par_statut.get("pass", 0)

    def resume(self) -> str:
        details = " ".join(f"{k}={v}" for k, v in sorted(self.par_statut.items()))
        suspects = f" suspects={self.suspects}" if self.suspects else ""
        return (f"{self.tache_id}: {self.proposes} proposés | {details} "
                f"| archivés={self.archives} doublons={self.doublons}{suspects}")


def tour(generateur: Generateur, store: Store, tache, n: int,
         limites: Limites | None = None, inspecteur=None, selection=None) -> Rapport:
    """
    Un tour : N candidats pour UNE tâche -> jugés -> les vrais succès archivés.

    Ne fait QUE passer les briques dans le bon ordre. Aucune intelligence ici :
    c'est la réalité (le juge) qui décide ce qui passe.

    Si un `inspecteur` (B5) est fourni, il s'intercale entre JUGER et GARDER :
    un candidat qui passe n'est archivé que s'il est LÉGITIME (généralise, sans
    sabotage). Les autres (exploit du juge, hard-coding) sont écartés du store et
    consignés dans le journal de l'inspecteur — comptés ici comme 'suspects'.

    Si une `selection` (utilité évolutive, B10) est fournie, chaque succès légitime
    lui est aussi OFFERT : elle garde, par tâche, le PLUS UTILE (pas juste le
    correct) et supplante le moins bon. Le store reste le journal brut ; la
    selection est la « meilleure logique » courante, révisable.
    """
    candidats = generateur.propose(tache.prompt, n)

    par_statut: dict[str, int] = {}
    archives = 0
    doublons = 0
    suspects = 0

    for code in candidats:
        verdict = juge(code, tache.tests, limites)
        par_statut[verdict.statut] = par_statut.get(verdict.statut, 0) + 1
        if not verdict.passe:
            continue
        # L'inspecteur écarte exploits et hard-coding AVANT de garder.
        if inspecteur is not None and not inspecteur.garde(tache, code, verdict):
            suspects += 1
            continue
        # GARDER : le store journalise (dé-dup) ; la selection garde le plus utile.
        if selection is not None:
            selection.offre(tache, code, verdict)
        if store.ajoute(tache, code, verdict):
            archives += 1
        else:
            doublons += 1

    return Rapport(tache_id=tache.id, proposes=len(candidats),
                   par_statut=par_statut, archives=archives, doublons=doublons,
                   suspects=suspects)


def campagne(generateur: Generateur, store: Store, taches: list, n: int,
             tours: int, limites: Limites | None = None, inspecteur=None,
             selection=None) -> list[Rapport]:
    """
    Plusieurs tours sur plusieurs tâches. Rend la liste des rapports (un par
    tour par tâche), dans l'ordre. Montre le store grossir puis SATURER (les
    doublons montent quand le générateur n'a plus d'idée neuve qui passe).
    """
    rapports = []
    for _ in range(tours):
        for tache in taches:
            rapports.append(tour(generateur, store, tache, n, limites, inspecteur, selection))
    return rapports


# --- Démo : la boucle entière qui tourne, sans GPU --------------------------

def _demo() -> None:
    import tempfile
    from pathlib import Path

    from generateur import GenerateurFactice, banque_demo
    from taches import HUMANEVAL_0 as t

    gen = GenerateurFactice(banque_demo(t), seed=7)
    limites = Limites(temps_s=2, cpu_s=1)  # court : la banque contient une boucle infinie

    with tempfile.TemporaryDirectory() as d:
        store = Store(Path(d) / "succes.jsonl")
        print("Boucle GÉNÉRER -> JUGER -> GARDER sur HumanEval/0 "
              "(générateur factice, 8 candidats/tour) :\n")
        rapports = campagne(gen, store, [t], n=8, tours=4, limites=limites)
        for i, r in enumerate(rapports, 1):
            print(f"  tour {i}  {r.resume()}  | store={len(store)}")
        print(f"\nStore final : {len(store)} succès vérifiés distincts "
              f"-> {store.par_tache()}")
        print("On garde le vrai-vérifié, on dé-duplique, on sature proprement. "
              "Ce store EST le jeu de ré-entraînement.")


if __name__ == "__main__":
    _demo()
