"""
MÉMOIRE DE BRIQUES PERSISTANTE — « l'IA apprend ET RETIENT » (mandat Yohan 2026-06-24).

Chaînon manquant entre `store.py` (coffre append-only des succès vérifiés) et `examine_cible` (qui accepte
déjà un registre `existant` étendu, cf. bibliotheque_invention.py « sommeil » DreamCoder) : une mémoire de
briques VÉRIFIÉES, persistée sur disque, qu'on RÉINJECTE dans le registre `existant`. Effet :

  • RETENTION : chaque INVENTION vérifiée (par-expr qui passe held-out + unicité) est GARDÉE (JSON), et survit
    aux redémarrages de process / runs.
  • RÉUTILISATION : une cible déjà apprise redevient EXISTE_DEJA (reconnue d'emblée) au lieu d'être re-dérivée
    par la recherche générative coûteuse -> beaucoup plus rapide (cf. AssistantIA two_sum→two_product).
  • SOUNDNESS INCHANGÉE : EXISTE_DEJA exige toujours que la brique REPRODUISE les données de la nouvelle cible
    (`_reproduit` dans examine_cible) -> jamais un faux. On ne mémorise QUE du vrai-vérifié (comme le store).

C'est la boucle DreamCoder fermée d'un cran : DÉRIVER (éveil) -> RETENIR (sommeil) -> RECONNAÎTRE/RÉUTILISER.
"""
from __future__ import annotations

import json
import os


def _normalise(expr: str) -> str:
    """Normalise une expr pour la dé-duplication (la même idée à espaces près = une seule brique)."""
    return "\n".join(l.rstrip() for l in expr.strip().splitlines())


class MemoireBriques:
    """Bibliothèque PERSISTANTE de briques vérifiées (nom -> expr). Réinjectable dans `examine_cible(existant=)`."""

    def __init__(self, chemin: str | None = None, base: dict | None = None):
        self.chemin = chemin
        self.base = dict(base) if base else {}     # registre de départ (EXISTANT), jamais réécrit sur disque
        self.appris: dict[str, str] = {}           # briques APPRISES (persistées)
        self._exprs: set[str] = set()              # exprs normalisées connues (base + apprises) pour dé-dup
        for e in self.base.values():
            self._exprs.add(_normalise(e))
        self.charge()

    # — persistance —
    def charge(self) -> int:
        if self.chemin and os.path.exists(self.chemin):
            with open(self.chemin) as f:
                self.appris = json.load(f)
            for e in self.appris.values():
                self._exprs.add(_normalise(e))
        return len(self.appris)

    def sauve(self) -> None:
        if not self.chemin:
            return
        tmp = self.chemin + ".tmp"
        with open(tmp, "w") as f:
            json.dump(self.appris, f, ensure_ascii=False, indent=1)
        os.replace(tmp, self.chemin)

    # — apprentissage —
    def connait(self, expr: str) -> bool:
        return _normalise(expr) in self._exprs

    def retient(self, par: str) -> bool:
        """Garde une brique VÉRIFIÉE si nouvelle (dé-dup). Renvoie True si elle vient d'être apprise."""
        if par is None:
            return False
        n = _normalise(par)
        if n in self._exprs:
            return False
        self.appris[f"appris_{len(self.appris)}"] = par
        self._exprs.add(n)
        return True

    # — usage —
    def existant(self) -> dict:
        """Le registre COMPLET à passer à examine_cible(existant=...) : base + tout ce qui a été appris."""
        return {**self.base, **self.appris}

    def __len__(self) -> int:
        return len(self.appris)


if __name__ == "__main__":
    from garde_ressources import borne
    borne(max_cpu_s=300)
    import moteur_invention as MI

    print("=== DÉMO MÉMOIRE : apprendre -> retenir -> réutiliser (sound) ===")
    mem = MemoireBriques(base=MI.EXISTANT)
    # amplitude = max - min : INVENTION la 1re fois (re-dérivée), puis RETENUE.
    ex = [([3, 1, 5], 4), ([2, 2], 0), ([10, 0, 3], 10)]
    held = [([0, 9, 4], 9), ([7], 0), ([5, 5, 1], 4)]
    v1 = MI.examine_cible("amplitude", "x", ex, held, existant=mem.existant())
    print(f"  1er passage : {v1.statut}  (par={v1.par})")
    if v1.statut == MI.INVENTION:
        mem.retient(v1.par)
    v2 = MI.examine_cible("amplitude_bis", "x", ex, held, existant=mem.existant())
    print(f"  2e passage (après rétention) : {v2.statut}  (par={v2.par})")
    print(f"  briques apprises : {len(mem)}")
    ok = v1.statut == MI.INVENTION and v2.statut == MI.EXISTE_DEJA
    print("  RETENTION+RÉUTILISATION :", "✅ INVENTION -> EXISTE_DEJA" if ok else "❌")
