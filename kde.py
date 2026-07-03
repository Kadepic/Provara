"""
PALIER 2 — ESTIMATION DE DENSITÉ PAR NOYAU (KDE) & choix de la fenêtre : une fenêtre trop étroite voit des modes qui
sont du bruit (brique 81, 2026-06-27).

Pour estimer la densité d'où proviennent des données, le KDE pose une petite « bosse » (noyau gaussien) sur chaque
point : f̂(x) = (1/nh) Σ K((x−xᵢ)/h). Le choix de la FENÊTRE h fait tout :
  • h trop PETIT → f̂ est une forêt de pics, un mode par point : on « voit » une structure fine qui est du pur bruit
    d'échantillonnage = SUR-CONFIANCE. Pire, f̂ assigne une densité ≈ 0 entre les pics → un point nouveau y tombe et
    récolte une log-vraisemblance catastrophique.
  • h trop GRAND → tout est lissé, on rate la vraie structure.

LE DIAGNOSTIC HONNÊTE — la vraisemblance LEAVE-ONE-OUT : ℓ(h) = Σᵢ ln f̂₋ᵢ(xᵢ) (densité en xᵢ sans utiliser xᵢ). Elle
s'effondre pour h petit (sur-ajustement démasqué), est maximale pour un h INTERMÉDIAIRE, et redescend pour h grand.
La règle de Silverman h≈1.06·σ·n^{−1/5} en donne une bonne valeur de départ pour des données ~gaussiennes.

LE MODE D'ÉCHEC DÉMASQUÉ : prendre h trop petit (sur-confiance dans des modes-fantômes) est puni par la
vraisemblance held-out ; le h choisi par LOO généralise. ABSTENTION si n<3 ou h≤0. Pur Python.
"""
from __future__ import annotations

import math

ABSTENTION = "abstention"
DENSITE = "densite"
_C = 1.0 / math.sqrt(2 * math.pi)


def noyau(u):
    return _C * math.exp(-0.5 * u * u)


def densite(xs, x, h):
    """f̂(x) = (1/nh) Σ K((x−xᵢ)/h)."""
    n = len(xs)
    return sum(noyau((x - xi) / h) for xi in xs) / (n * h)


def log_vraisemblance_loo(xs, h):
    """Log-vraisemblance leave-one-out ℓ(h) = Σᵢ ln f̂₋ᵢ(xᵢ) (s'effondre si h trop petit)."""
    n = len(xs)
    tot = 0.0
    for i, xi in enumerate(xs):
        d = sum(noyau((xi - xj) / h) for j, xj in enumerate(xs) if j != i) / ((n - 1) * h)
        tot += math.log(d) if d > 0 else -1e300
    return tot


def silverman(xs):
    """Règle de Silverman h ≈ 1.06·σ·n^{−1/5}."""
    n = len(xs)
    m = sum(xs) / n
    sd = math.sqrt(sum((x - m) ** 2 for x in xs) / (n - 1))
    return 1.06 * sd * n ** (-1 / 5)


def h_optimal(xs, grille=None):
    """Fenêtre maximisant la vraisemblance leave-one-out (sur une grille autour de Silverman)."""
    h0 = silverman(xs)
    if grille is None:
        grille = [h0 * 2 ** (k / 4) for k in range(-8, 9)]
    return max(grille, key=lambda h: log_vraisemblance_loo(xs, h))


def n_modes(xs, h, grille=None):
    """Nombre de maxima locaux de f̂ (modes) sur une grille : explose quand h est trop petit (modes fantômes)."""
    if grille is None:
        lo, hi = min(xs), max(xs)
        marge = (hi - lo) * 0.1 + 1e-9
        grille = [lo - marge + (hi - lo + 2 * marge) * k / 400 for k in range(401)]
    ds = [densite(xs, x, h) for x in grille]
    return sum(1 for i in range(1, len(ds) - 1) if ds[i] > ds[i - 1] and ds[i] > ds[i + 1])


def analyse(xs, h=None):
    """Façade : (DENSITE, {h, h_silverman, loo, n_modes}) ou (ABSTENTION, raison). h=None → h optimal (LOO)."""
    if len(xs) < 3:
        return (ABSTENTION, "n < 3")
    if h is not None and h <= 0:
        return (ABSTENTION, "h ≤ 0")
    hh = h if h is not None else h_optimal(xs)
    return (DENSITE, {"h": hh, "h_silverman": silverman(xs), "loo": log_vraisemblance_loo(xs, hh),
                      "n_modes": n_modes(xs, hh)})


def formule(res) -> str:
    if res[0] == ABSTENTION:
        return f"Pas d'estimation : {res[1]}."
    i = res[1]
    return (f"Fenêtre h={i['h']:.3f} (Silverman {i['h_silverman']:.3f}) : {i['n_modes']} mode(s), vraisemblance LOO "
            f"{i['loo']:.1f}. Une fenêtre plus étroite verrait des modes-fantômes (sur-confiance, mal généralisée).")


if __name__ == "__main__":
    import random
    rng = random.Random(0)
    xs = [rng.gauss(0, 1) for _ in range(120)]      # vraie densité = unimodale
    print("=== ESTIMATION DE DENSITÉ PAR NOYAU (KDE) ===\n")
    h_s = silverman(xs)
    for h in (h_s / 6, h_s, h_s * 3):
        print(f"  h={h:.3f} : {n_modes(xs, h):>3} modes, vraisemblance LOO={log_vraisemblance_loo(xs, h):.1f}")
    print(f"\n  Silverman h={h_s:.3f} ; h optimal (LOO) = {h_optimal(xs):.3f}")
    print(" ", formule(analyse(xs)))
