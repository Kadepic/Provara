"""
PALIER 2 — CONFORME HÉTÉROSCÉDASTIQUE (brique 9, 2026-06-25). La couverture CONDITIONNELLE, pas seulement marginale.

Le conforme de base (conformal.py) garantit la couverture MARGINALE (~1−α en moyenne), mais avec une largeur CONSTANTE.
Si le bruit varie selon la situation (hétéroscédasticité), un intervalle de largeur unique SUR-COUVRE les cas faciles
et SOUS-COUVRE les cas difficiles : marginalement honnête, mais CONDITIONNELLEMENT trompeur (sur-confiant là où c'est
dur). Deux remèdes model-free :

  • MONDRIAN (group-conditional) : un quantile conforme SÉPARÉ par groupe (catégorie, ou bin de difficulté). Chaque
    groupe est couvert ~1−α -> couverture conditionnelle par groupe. Garantie distribution-free intra-groupe.
  • NORMALISÉ : score = |y−ŷ| / σ̂(x) (σ̂ = difficulté locale estimée). Intervalle = ŷ ± q·σ̂(x) -> largeur qui s'adapte
    continûment. Couvre marginalement ; resserre où c'est facile, élargit où c'est dur.

INVARIANT : la couverture PAR GROUPE / PAR RÉGIME reste ≥ ~1−α (jamais sur-confiant localement), prouvé MC, jugé par
calibration.py. ABSTENTION par groupe si trop peu de points de calibration dans ce groupe.
"""
from __future__ import annotations

import conformal as _CF

ABSTENTION = "abstention"
ESTIMATION = "estimation"


class ConformeMondrian:
    """Conforme group-conditional : un quantile par groupe. `ajuste(groupes, residus)` puis `intervalle(groupe, pred)`."""

    __slots__ = ("alpha", "quantiles")

    def __init__(self, alpha: float = 0.10):
        self.alpha = alpha
        self.quantiles: dict = {}

    def ajuste(self, groupes, residus):
        """Apprend un quantile conforme |résidu| par groupe. Groupe avec trop peu de points -> quantile None (abstention)."""
        par_groupe: dict = {}
        for g, r in zip(groupes, residus):
            par_groupe.setdefault(g, []).append(abs(float(r)))
        self.quantiles = {g: _CF.quantile_conforme(rs, self.alpha) for g, rs in par_groupe.items()}
        return self

    def intervalle(self, groupe, prediction):
        """Intervalle conforme propre au groupe. (ESTIMATION, (bas, haut), 1−α) ou ABSTENTION (groupe inconnu/trop peu)."""
        q = self.quantiles.get(groupe)
        if q is None:
            return (ABSTENTION, None, f"groupe {groupe!r} sans quantile fiable (inconnu ou trop peu de calibration)")
        p = float(prediction)
        return (ESTIMATION, (p - q, p + q), 1.0 - self.alpha)


def intervalle_normalise(residus_cal, sigmas_cal, prediction, sigma_pred, alpha: float = 0.10):
    """Conforme NORMALISÉ : score_i = |résidu_i| / σ̂_i ; q = quantile conforme des scores ; intervalle =
    prediction ± q·σ_pred. `σ̂` = estimation de difficulté locale (>0). Renvoie (ESTIMATION, (bas, haut), 1−α) ou
    ABSTENTION. Largeur ADAPTATIVE : grande où σ_pred est grand (cas dur), petite où il est petit (cas facile)."""
    scores = []
    for r, s in zip(residus_cal, sigmas_cal):
        if s <= 0:
            return (ABSTENTION, None, f"σ̂ invalide ({s}) : doit être > 0")
        scores.append(abs(float(r)) / float(s))
    q = _CF.quantile_conforme(scores, alpha)
    if q is None:
        return (ABSTENTION, None, f"trop peu de points de calibration (n={len(scores)}) pour {round((1-alpha)*100)}%")
    if sigma_pred <= 0:
        return (ABSTENTION, None, f"σ_pred invalide ({sigma_pred})")
    p = float(prediction)
    demi = q * float(sigma_pred)
    return (ESTIMATION, (p - demi, p + demi), 1.0 - alpha)


def formule(res) -> str:
    if res[0] == ABSTENTION:
        return f"Je préfère ne pas me prononcer : {res[2]}."
    _, (bas, haut), conf = res
    return (f"La vraie valeur est entre {bas:.2f} et {haut:.2f} (garantie {round(conf*100)}%), avec une largeur "
            "adaptée à la difficulté locale.")


if __name__ == "__main__":
    print("=== CONFORME HÉTÉROSCÉDASTIQUE ===\n")
    import random
    rng = random.Random(0)
    # deux régimes : facile (σ=1) et dur (σ=5)
    groupes, residus = [], []
    for _ in range(400):
        groupes.append("facile"); residus.append(rng.gauss(0, 1))
        groupes.append("dur");    residus.append(rng.gauss(0, 5))
    m = ConformeMondrian(0.10).ajuste(groupes, residus)
    print("  Mondrian facile :", formule(m.intervalle("facile", 0.0)))
    print("  Mondrian dur    :", formule(m.intervalle("dur", 0.0)))
    # normalisé : σ̂ = le régime
    sig = [1.0 if g == "facile" else 5.0 for g in groupes]
    print("  normalisé (σ=1) :", formule(intervalle_normalise(residus, sig, 0.0, 1.0)))
    print("  normalisé (σ=5) :", formule(intervalle_normalise(residus, sig, 0.0, 5.0)))
