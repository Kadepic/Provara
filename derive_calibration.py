"""
PALIER 2 — DÉTECTEUR DE DÉRIVE DE CALIBRATION (brique 13, 2026-06-25). Surveiller que la calibration TIENT.

L'ACI (conformal_adaptatif.py) RÉPARE la dérive ; ce module la DÉTECTE et ALERTE — le complément diagnostique.
On surveille un flux de couples (confiance annoncée, justesse 0/1). L'écart instantané gₜ = confianceₜ − justesseₜ
a une espérance NULLE si le système est calibré ; il devient POSITIF si le système se met à SUR-promettre
(sur-confiance = la ligne rouge). On le traque avec une CARTE CUSUM UNILATÉRALE (vers le haut seulement — on ne
s'alarme pas de la prudence) :

    Sₜ = max(0, Sₜ₋₁ + (gₜ − k))         alarme quand Sₜ ≥ h

k = marge morte (on ignore une sur-confiance < k) ; h = seuil (règle le compromis fausses alarmes / délai). Sous H0
(calibré), la dérive de S est négative -> alarmes RARES (faux positifs contrôlés). Sous sur-confiance, S grimpe vite
-> détection rapide. On NE s'alarme PAS de la sous-confiance (sûre). C'est l'invariant de calibration, surveillé dans le temps.
"""
from __future__ import annotations

ALERTE = "alerte"
STABLE = "stable"


class DetecteurDerive:
    """Carte CUSUM unilatérale détectant l'apparition de SUR-CONFIANCE dans un flux (confiance, justesse).
    `k` = marge morte, `h` = seuil d'alarme. `observe()` renvoie le statut courant ; l'alarme est LATCHÉE
    (reste ALERTE jusqu'à `reinitialise()`)."""

    __slots__ = ("k", "h", "S", "alarme", "n", "S_max")

    def __init__(self, k: float = 0.10, h: float = 8.0):
        self.k = k
        self.h = h
        self.S = 0.0
        self.alarme = False
        self.n = 0
        self.S_max = 0.0

    def observe(self, confiance, juste):
        """Intègre un nouveau couple (confiance ∈ [0,1], juste ∈ {0,1}). Renvoie (ALERTE/STABLE, S)."""
        g = float(confiance) - (1.0 if juste else 0.0)
        self.S = max(0.0, self.S + g - self.k)
        self.S_max = max(self.S_max, self.S)
        self.n += 1
        if self.S >= self.h:
            self.alarme = True
        return (ALERTE if self.alarme else STABLE, self.S)

    def statut(self):
        return ALERTE if self.alarme else STABLE

    def reinitialise(self):
        self.S = 0.0
        self.alarme = False


def formule(detecteur) -> str:
    if detecteur.alarme:
        return ("⚠ DÉRIVE DE CALIBRATION détectée : mes confiances sont devenues trop sûres d'elles (sur-confiance "
                "soutenue). Il faut me recalibrer — je ne suis plus fiable tel quel.")
    return "Ma calibration tient : pas de sur-confiance soutenue détectée dans le flux récent."


if __name__ == "__main__":
    print("=== DÉTECTEUR DE DÉRIVE DE CALIBRATION ===\n")
    import random
    rng = random.Random(0)
    det = DetecteurDerive(k=0.10, h=8.0)
    # 1000 pas calibrés puis bascule en sur-confiance
    bascule = None
    for t in range(2000):
        c = 0.5 + 0.5 * rng.random()
        p_juste = c if t < 1000 else max(0.0, c - 0.25)     # après 1000 : sur-confiant
        juste = 1 if rng.random() < p_juste else 0
        st, _ = det.observe(c, juste)
        if st == ALERTE and bascule is None:
            bascule = t
    print(f"  alarme levée au pas {bascule} (dérive injectée au pas 1000)")
    print(" ", formule(det))
