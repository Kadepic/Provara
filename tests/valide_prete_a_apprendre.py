"""
VALIDE — L'IA EST PRÊTE À APPRENDRE (2026-06-17). Vérifie TOUS les planes du maillon APPRENDRE, sans GPU : il ne
manque QUE l'entraînement sur GPU. Et prouve que la boucle se REFERME (apprentissage CONTINU).

Critères de MORT (4) :
  1. DONNÉES     : l'usine accumule un corpus de paires (prompt->solution) VÉRIFIÉES (tout correct par construction).
  2. EXPORT      : le store s'exporte en JEU D'ENTRAÎNEMENT bien formé (JSONL standard, 0 mal-formé, solutions réelles).
  3. RÉ-INGESTION : une sortie de MODÈLE (stub, via l'INTERFACE générateur) passe le juge+held-out et REJOINT le store
                    -> la boucle GÉNÉRER(modèle)→JUGER→GARDER se referme (un modèle entraîné se rebranche).
  4. CONTINU     : le store GRANDIT après ré-ingestion -> l'IA apprend EN CONTINU (le passé nourrit le futur).
"""

from __future__ import annotations

import tempfile
from pathlib import Path

from exporte_dataset import exporte, resume
from juge import Limites, juge
from store import Store
from taches import Tache
from usine_donnees import accumule

LIM = Limites(temps_s=3, cpu_s=2)


class ModeleStub:
    """Stub d'un MODÈLE appris : implémente l'INTERFACE générateur (`propose`). Prouve qu'un modèle entraîné
    remplace le générateur sans toucher au reste (la boucle se referme)."""

    def __init__(self, solution: str):
        self._sol = solution

    def propose(self, prompt: str, n: int) -> list[str]:
        return [self._sol]


def _check(nom, ok):
    print(f"  [{'OK ' if ok else 'RATÉ'}] {nom}", flush=True)
    return ok


def main() -> int:
    r = []
    with tempfile.TemporaryDirectory() as d:
        store_path = Path(d) / "corpus.jsonl"

        # 1. DONNÉES (corpus borné pour rester rapide ; le corpus complet = usine_donnees.py sur les 49)
        store = accumule(store_path, limite=12)
        r.append(_check(f"DONNÉES : {len(store)} paires (prompt->solution) VÉRIFIÉES accumulées", len(store) >= 10))

        # 2. EXPORT
        out = Path(d) / "train.jsonl"
        rexp = exporte(store_path, out, "chat")
        rres = resume(out)
        r.append(_check(f"EXPORT : {rexp['exemples']} exemples, {rres['valides']} bien formés, {rres['mal_formees']} mal-formés, "
                        f"{rres['solutions_distinctes']} solutions distinctes",
                        rexp["exemples"] >= 10 and rres["mal_formees"] == 0 and rres["valides"] == rexp["exemples"]))

        # 3. RÉ-INGESTION (boucle fermée) : un MODÈLE (stub) propose -> jugé -> stocké.
        tache = Tache(id="apprend/carre", point_entree="carre", prompt='def carre(x):\n    """..."""',
                      tests="def check(c):\n    assert c(3)==9\n    assert c(5)==25\ncheck(carre)",
                      tests_held_out="def check(c):\n    assert c(0)==0\n    assert c(-2)==4\ncheck(carre)")
        modele = ModeleStub("def carre(*args, **kwargs):\n    return args[0]*args[0]\n")
        n_avant = len(store)
        cand = modele.propose(tache.prompt, 1)[0]
        ok_juge = juge(cand, tache.tests, LIM).passe and juge(cand, tache.tests_held_out, LIM).passe
        reingere = ok_juge and store.ajoute(tache, cand, juge(cand, tache.tests, LIM))
        r.append(_check("RÉ-INGESTION : une sortie de MODÈLE (stub) passe juge+held-out et REJOINT le store (boucle fermée)",
                        reingere))

        # 4. CONTINU : le store a grandi (relu du disque).
        store2 = Store(store_path)
        r.append(_check(f"CONTINU : le store a grandi ({n_avant} -> {len(store2)}) -> apprentissage EN CONTINU (compounding)",
                        len(store2) == n_avant + 1))

    print()
    print("IA PRÊTE À APPRENDRE — 4/4 (il ne manque que le GPU)." if all(r) else f"ÉCHEC — {sum(r)}/4.")
    return 0 if all(r) else 1


if __name__ == "__main__":
    raise SystemExit(main())
