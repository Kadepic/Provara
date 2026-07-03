"""
MÉTA-ROUTEUR INTÉGRÉ (2026-06-19, vision Yohan « s'adapter à la situation, router par clé/x/y comme le cerveau ») —
on vérifie l'ASSEMBLÉ (pas l'isolé) : AssistantIA = means-end (si applicable) -> routage d'ÉTAGES -> routage de
STRATÉGIE par clé -> fallback. Le warm-up amorti (prechauffe) réchauffe les deux routeurs ; à chaud, une tâche de clé
connue est résolue MOINS cher, SANS changer le résultat (neutre en correction).

Critères de MORT (4) :
  1. COLD RÉSOUT : AssistantIA fraîche résout max_minus_min (means-end ne l'attrape pas -> passe par le routage) + généralise.
  2. WARM RÉSOUT : après prechauffe sur la batterie, ré-résout max_minus_min + généralise (couverture préservée).
  3. WARM MOINS CHER : appels chaud < appels froid (le méta-routage réduit le coût DANS l'assemblage vivant).
  4. NEUTRE EN CORRECTION : même étage résolveur à froid et à chaud (on n'a pas changé la réponse, juste l'ordre).

SÉQUENTIEL + garde. La prechauffe sur 59 familles est lourde (sous ulimit + timeout).
"""

from __future__ import annotations

import tempfile
from pathlib import Path

from demande import AssistantIA
from diable import BATTERIE
from garde_ressources import borne
from routeur import cle_tache

# mêmes exemples que la tâche max_minus_min de la batterie -> clé identique -> le routage chaud s'applique.
MMM = ("max_minus_min", "xs",
       [(([3, 1, 2],), 2), (([5, 5],), 0)],
       [(([10, 1, 7],), 9), (([4],), 0), (([1, 2, 3, 4, 5],), 4), (([1, 3, 5, 7, 9],), 8)])


def _check(nom, ok):
    print(f"  [{'OK ' if ok else 'RATÉ'}] {nom}", flush=True)
    return ok


def main() -> int:
    borne()
    r = []
    # prechauffe sur la FAMILLE (1,list,int) seulement (légère ; contient la clé de max_minus_min) — amorti représentatif.
    taches = [t for _, t in BATTERIE if cle_tache(t)[:3] == (1, "list", "int")]

    with tempfile.TemporaryDirectory() as d:
        # COLD
        ia_froid = AssistantIA(Path(d) / "froid.jsonl")
        froid = ia_froid.demande(*MMM[:2], MMM[2], MMM[3])
        r.append(_check(f"COLD RÉSOUT : max_minus_min -> `{froid.etage}` en {froid.appels} appels, généralise={froid.generalise}",
                        froid.ok and froid.generalise))

        # WARM : prechauffe amortie sur la batterie, puis re-demande
        ia_chaud = AssistantIA(Path(d) / "chaud.jsonl")
        ia_chaud.prechauffe(taches, k=200)
        chaud = ia_chaud.demande(*MMM[:2], MMM[2], MMM[3])
        r.append(_check(f"WARM RÉSOUT : max_minus_min -> `{chaud.etage}` en {chaud.appels} appels, généralise={chaud.generalise}",
                        chaud.ok and chaud.generalise))

        r.append(_check(f"WARM MOINS CHER : chaud {chaud.appels} < froid {froid.appels} appels "
                        f"({100*(froid.appels-chaud.appels)/froid.appels:+.0f}%)",
                        chaud.ok and froid.ok and chaud.appels < froid.appels))

        r.append(_check(f"NEUTRE EN CORRECTION : même étage résolveur (froid `{froid.etage}` == chaud `{chaud.etage}`)",
                        froid.etage == chaud.etage and chaud.generalise))

    print()
    print("MÉTA-ROUTEUR INTÉGRÉ VALIDÉ — 4/4." if all(r) else f"ÉCHEC — {sum(r)}/4.")
    return 0 if all(r) else 1


if __name__ == "__main__":
    raise SystemExit(main())
