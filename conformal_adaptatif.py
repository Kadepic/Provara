"""
PALIER 2 — CONFORME ADAPTATIF EN LIGNE (brique 6, 2026-06-25). La calibration qui TIENT quand le monde CHANGE.

Le conforme statique (conformal.py) garantit la couverture SOUS ÉCHANGEABILITÉ. Mais la réalité DÉRIVE : le vrai
d'hier devient faux, le bruit s'amplifie, la distribution glisse (cf. « vérité datée / base froide »). Sous dérive,
un intervalle calibré sur le passé SOUS-COUVRE le présent — il devient sur-confiant sans le savoir.

ACI (Adaptive Conformal Inference, Gibbs & Candès 2021) répare ça SANS hypothèse de stationnarité : on ajuste en
ligne le niveau effectif αₜ selon qu'on a couvert ou raté le dernier point :

    αₜ₊₁ = αₜ + γ · (α_cible − erreurₜ)        (erreurₜ = 1 si le dernier point est sorti de l'intervalle, sinon 0)

Si on rate trop (erreur > cible) → αₜ baisse → intervalles plus LARGES ; si on couvre trop → αₜ monte → plus étroits.
GARANTIE (déterministe, sans loi) : la fréquence empirique de couverture sur le flux converge vers 1 − α_cible, QUELLE
QUE SOIT la dérive. C'est l'invariant de calibration rendu robuste au temps.

ABSTENTION : tant que la fenêtre de scores récents est trop courte, on ne fabrique pas d'intervalle.
"""
from __future__ import annotations

import conformal as _CF

ABSTENTION = "abstention"
ESTIMATION = "estimation"
N_MIN_FENETRE = 20


class ConformeAdaptatif:
    """Estimateur d'intervalle conforme EN LIGNE, robuste à la dérive. Usage : à chaque pas, `intervalle(prediction)`
    pour l'intervalle courant, puis `observe(prediction, verite)` quand la vérité arrive (met à jour αₜ et la fenêtre).
    `taille_fenetre` = mémoire des scores récents (suit la dérive) ; `gamma` = vitesse d'adaptation."""

    __slots__ = ("alpha_cible", "gamma", "taille", "alpha_t", "fenetre", "n_vu", "n_couvert")

    def __init__(self, alpha_cible: float = 0.10, gamma: float = 0.05, taille_fenetre: int = 200):
        self.alpha_cible = alpha_cible
        self.gamma = gamma
        self.taille = taille_fenetre
        self.alpha_t = alpha_cible
        self.fenetre: list[float] = []
        self.n_vu = 0
        self.n_couvert = 0

    def _q(self):
        """Quantile conforme courant sur la fenêtre, au niveau effectif αₜ (clampé). None SEULEMENT si fenêtre trop
        courte. Si αₜ exige un niveau que la fenêtre ne peut garantir (ex. ~100 %), on renvoie le score MAX (intervalle
        le plus large vu) — ce que veut ACI quand il cherche à tout couvrir — plutôt qu'une abstention trompeuse."""
        if len(self.fenetre) < N_MIN_FENETRE:
            return None
        a = min(0.999, max(1e-4, self.alpha_t))     # αₜ peut sortir de [0,1] ; on clampe pour le quantile
        q = _CF.quantile_conforme(self.fenetre, a)
        return q if q is not None else max(self.fenetre)

    def intervalle(self, prediction):
        """Intervalle conforme courant autour de `prediction`. (ESTIMATION, (bas, haut), 1−α_cible) ou ABSTENTION."""
        q = self._q()
        if q is None:
            return (ABSTENTION, None, f"fenêtre trop courte (n={len(self.fenetre)} < {N_MIN_FENETRE})")
        p = float(prediction)
        return (ESTIMATION, (p - q, p + q), 1.0 - self.alpha_cible)

    def observe(self, prediction, verite):
        """Enregistre la vérité : décide si l'intervalle courant l'a couverte, met à jour αₜ (loi ACI) et la fenêtre."""
        r = abs(float(verite) - float(prediction))
        q = self._q()
        if q is not None:                            # on ne comptabilise que quand un intervalle était offert
            couvert = r <= q
            self.n_vu += 1
            self.n_couvert += 1 if couvert else 0
            err = 0.0 if couvert else 1.0
            self.alpha_t += self.gamma * (self.alpha_cible - err)
        self.fenetre.append(r)
        if len(self.fenetre) > self.taille:
            self.fenetre.pop(0)

    def couverture_empirique(self):
        """Fréquence de couverture observée sur le flux (la quantité que l'invariant veut ≈ 1−α_cible)."""
        return self.n_couvert / self.n_vu if self.n_vu else None


def formule(res) -> str:
    if res[0] == ABSTENTION:
        return f"Je préfère ne pas me prononcer : {res[2]}."
    _, (bas, haut), conf = res
    return (f"La vraie valeur est entre {bas:.2f} et {haut:.2f} (visée {round(conf*100)}%), un intervalle qui "
            "s'adapte en continu si la situation change.")


if __name__ == "__main__":
    print("=== CONFORME ADAPTATIF (couverture maintenue sous dérive) ===\n")
    import random
    rng = random.Random(0)
    aci = ConformeAdaptatif(alpha_cible=0.10, gamma=0.05, taille_fenetre=150)
    # dérive : l'amplitude du bruit GRANDIT au fil du temps (le monde devient plus incertain)
    for t in range(3000):
        echelle = 1.0 + 4.0 * t / 3000.0
        verite = rng.gauss(0, echelle)
        aci.intervalle(0.0)
        aci.observe(0.0, verite)
    print(f"  couverture empirique sous dérive = {aci.couverture_empirique():.3f} (visée 0.90)")
    print("  ", formule(aci.intervalle(0.0)))
