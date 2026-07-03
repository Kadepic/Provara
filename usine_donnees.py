"""
USINE À DONNÉES (2026-06-17, « rendre l'IA prête à apprendre ») — accumuler un CORPUS de succès VÉRIFIÉS dans un
store persistant : la matière brute du fine-tuning (le maillon APPRENDRE). Sans GPU.

On résout une batterie LARGE (les 49 capacités du diable = couverture complète des compétences) avec le moteur
complet, et on verse chaque succès confirmé (passe le juge ET le held-out) dans le store. Tout y est correct par
construction (le store refuse le non-vérifié) et dédupliqué.
"""

from __future__ import annotations

from compounding import resoudre
from diable import BATTERIE, _moteur_complet, _seede
from juge import Limites
from store import Store

LIM = Limites(temps_s=3, cpu_s=2)
K = 1000


def accumule(chemin_store, limite: int | None = None) -> Store:
    """Remplit (ou enrichit) le store persistant `chemin_store` avec les solutions vérifiées des capacités.
    `limite` = ne résoudre que les `limite` premières (corpus rapide pour la validation ; None = les 49)."""
    store = Store(chemin_store)
    _seede(store)                       # graines de base (skills de départ)
    orch = _moteur_complet(store)
    for att, t in (BATTERIE[:limite] if limite else BATTERIE):
        _, _, code, verdict = resoudre(orch, t, LIM, K)
        if code is not None:
            try:
                store.ajoute(t, code, verdict)
            except ValueError:
                pass                    # held-out non passé / déjà connu : on n'ajoute pas (garde-fou)
    return store


if __name__ == "__main__":
    import sys
    chemin = sys.argv[1] if len(sys.argv) > 1 else "corpus.jsonl"
    store = accumule(chemin)
    print(f"Corpus accumulé : {len(store)} succès vérifiés -> {chemin}")
    compte = store.par_tache()
    print(f"Tâches distinctes : {len(compte)}")
