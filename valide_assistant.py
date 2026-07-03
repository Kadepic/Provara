"""
ASSISTANT IA À MÉMOIRE PERSISTANTE (2026-06-17) — l'IA s'améliore À L'USAGE : store + routeur qui se réchauffent ->
la puissance BAISSE avec l'usage, SÛREMENT (zone-routing gate-protégée). C'est la voie SÛRE pour capter le plafond
du routage (vs le ré-ordonnancement brut qui masque, cf. cherche_ordre.py -> reverté).

Critères de MORT (4) :
  1. RÉSOLU À FROID : 1ʳᵉ demande (two_sum) résolue + généralise (cold == escalade, sûr).
  2. MOINS CHER À CHAUD : 2ᵉ demande de MÊME CLÉ (two_product, jamais vue) résolue en BIEN moins d'appels (routée).
  3. GÉNÉRALISE (pas mémorise) : two_product (clé identique, tâche différente) routée au BON étage -> la famille, pas le cas.
  4. PERSISTANCE : le store a ACCUMULÉ la compétence (len > 0) -> mémoire entre usages.
"""

from __future__ import annotations

import tempfile
from pathlib import Path

from demande import AssistantIA

# two_sum et two_product partagent la clé (2, list, bool) -> le routeur réchauffé transfère.
TWO_SUM = ("two_sum", "xs, t",
           [(([1, 2, 3], 5), True), (([1, 2, 3], 10), False)],
           [(([5], 5), False), (([1, 2], 4), False)])
TWO_PROD = ("two_product", "xs, t",
            [(([2, 3, 4], 6), True), (([2, 3, 4], 5), False)],
            [(([1, 5, 2], 10), True), (([3], 9), False)])


def _check(nom, ok):
    print(f"  [{'OK ' if ok else 'RATÉ'}] {nom}", flush=True)
    return ok


def main() -> int:
    r = []
    with tempfile.TemporaryDirectory() as d:
        ia = AssistantIA(Path(d) / "memoire.jsonl")

        # 1. À FROID : two_sum.
        froid = ia.demande(*TWO_SUM[:2], TWO_SUM[2], TWO_SUM[3])
        r.append(_check(f"RÉSOLU À FROID : two_sum -> `{froid.etage}` en {froid.appels} appels, généralise={froid.generalise}",
                        froid.ok and froid.generalise))

        # 2. À CHAUD : two_product (MÊME clé, jamais vue) -> routé, bien moins cher.
        chaud = ia.demande(*TWO_PROD[:2], TWO_PROD[2], TWO_PROD[3])
        r.append(_check(f"MOINS CHER À CHAUD : two_product -> `{chaud.etage}` en {chaud.appels} appels "
                        f"(vs {froid.appels} à froid ; >=5× moins)",
                        chaud.ok and chaud.appels * 5 <= froid.appels))

        # 3. GÉNÉRALISE : routé au bon étage (la famille), pas mémorisé.
        r.append(_check(f"GÉNÉRALISE : two_product routé à `{chaud.etage}` (== froid `{froid.etage}`), pas une mémorisation",
                        chaud.ok and chaud.etage == froid.etage and chaud.generalise))

        # 4. PERSISTANCE : la compétence est accumulée dans le store.
        r.append(_check(f"PERSISTANCE : le store a accumulé {len(ia._store)} succès (mémoire entre usages)",
                        len(ia._store) >= 1))

    print()
    print("ASSISTANT IA PERSISTANT VALIDÉ — 4/4." if all(r) else f"ÉCHEC — {sum(r)}/4.")
    return 0 if all(r) else 1


if __name__ == "__main__":
    raise SystemExit(main())
