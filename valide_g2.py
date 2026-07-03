"""
Validation de G2 — SYNTHÈSE PAR BRIQUES (l'échafaudage qui bootstrap).

Ce que G2 doit prouver — et son honnêteté :

  1. BOOTSTRAP À FROID : sur un store VIDE, G2 RÉSOUT au moins une vraie tâche
     (≥1 candidat passe visible + held-out) — ce que G1 seul ne peut PAS (G1 froid
     = 0%). C'est G2 qui produit les premiers succès.
  2. LE MUR EST VISIBLE : avec une petite bibliothèque générale, G2 ne couvre pas
     tout. On RAPPORTE ce qu'il résout et ce qu'il ne résout pas (le mur mesuré).
  3. COMPOSITION G2 -> G1 : les succès de G2, archivés, sont ensuite RÉUTILISÉS
     par G1. Bootstrap (G2) + mémoire (G1) = le générateur maison qui démarre.
"""

from __future__ import annotations

import tempfile
from pathlib import Path

from exercices import CATALOGUE
from generateur import GenerateurBriques, GenerateurReutilisateur
from juge import Limites, juge
from store import Store
from taches import HUMANEVAL_0

LIM = Limites(temps_s=3, cpu_s=2)


def _check(nom, condition):
    print(f"  [{'OK ' if condition else 'RATÉ'}] {nom}")
    return condition


def resout(generateur, tache, n=30) -> bool:
    """Vrai si AU MOINS un candidat proposé passe visible ET held-out (succès réel)."""
    for code in generateur.propose(tache.prompt, n):
        if juge(code, tache.tests, LIM).passe and \
           (not tache.tests_held_out or juge(code, tache.tests_held_out, LIM).passe):
            return True
    return False


def main() -> int:
    resultats = []
    taches = CATALOGUE + [HUMANEVAL_0]
    g2 = GenerateurBriques(seed=0)

    # 1-2. Qui G2 résout-il, à froid ? (rapport honnête du mur)
    print("Ce que G2 résout à froid (store vide, aucune mémoire) :\n")
    resolus = []
    for t in taches:
        ok = resout(g2, t)
        print(f"  [{'résolu ' if ok else 'MUR    '}] {t.id}")
        if ok:
            resolus.append(t)

    resultats.append(_check(f"bootstrap : G2 résout au moins 1 tâche à froid ({len(resolus)})",
                            len(resolus) >= 1))
    resultats.append(_check("honnête : G2 ne résout PAS tout (le mur est visible)",
                            len(resolus) < len(taches)))

    # Contraste : G1 sur store vide ne résout RIEN (il a besoin que G2 amorce).
    with tempfile.TemporaryDirectory() as d:
        store_vide = Store(Path(d) / "vide.jsonl")
        g1_froid = GenerateurReutilisateur(store_vide)
        resultats.append(_check("contraste : G1 seul à froid ne résout rien",
                                not any(resout(g1_froid, t) for t in resolus)))

    # 3. Composition G2 -> G1 : on archive un succès de G2, G1 le réutilise ensuite.
    cible = resolus[0]
    with tempfile.TemporaryDirectory() as d:
        store = Store(Path(d) / "s.jsonl")
        # G2 bootstrap : on récupère son 1er candidat gagnant et on l'archive.
        gagnant = next(c for c in g2.propose(cible.prompt, 30)
                       if juge(c, cible.tests, LIM).passe)
        store.ajoute(cible, gagnant, juge(gagnant, cible.tests, LIM))
        resultats.append(_check(f"G2 a amorcé le store pour {cible.id}", len(store) == 1))

        g1 = GenerateurReutilisateur(store)
        resultats.append(_check("G1 réutilise ensuite le succès amorcé par G2",
                                resout(g1, cible)))

    print()
    if all(resultats):
        print(f"G2 VALIDÉ — {len(resultats)}/{len(resultats)}. L'échafaudage bootstrap le store froid "
              f"({len(resolus)}/{len(taches)} tâches), G1 prend le relais. Le mur restant est mesuré.")
        return 0
    print(f"ÉCHEC — {sum(resultats)}/{len(resultats)}.")
    return 1


if __name__ == "__main__":
    raise SystemExit(main())
