"""
PALIER 2 — MALÉDICTION DE LA DIMENSION (concentration des distances) : se fier aux distances en haute dimension est
sur-confiant (brique 122, 2026-06-28).

Les méthodes fondées sur la DISTANCE (plus proche voisin, noyaux, recherche par similarité, clustering euclidien)
supposent que « proche » a un sens. En haute dimension, c'est SUR-CONFIANT : les distances se CONCENTRENT. Pour des
points aléatoires, le rapport entre le voisin le PLUS PROCHE et le PLUS LOINTAIN tend vers 1 :
    (D_max − D_min) / D_min  →  0   quand d → ∞.
Le « plus proche voisin » devient indiscernable du plus lointain — la notion de voisinage perd son sens. De même, la masse
d'une gaussienne standard se concentre dans une COQUILLE fine de rayon √d : presque AUCUN point n'est près du mode (0),
contre toute intuition de basse dimension. Maintenir une densité d'échantillonnage exige un nombre de points qui croît
EXPONENTIELLEMENT avec d.

LE MODE D'ÉCHEC DÉMASQUÉ : appliquer kNN / densité par noyau / similarité euclidienne en haute dimension en supposant que
les distances restent informatives est SUR-CONFIANT. En basse dimension, le contraste est fort (honnêteté). Distinct de
covariance_grande_dim (77, estimation) et concentration (68, bornes de concentration). ABSTENTION si d<1. rng seedé.
"""
from __future__ import annotations

import math

ABSTENTION = "abstention"
ANALYSE = "analyse"


def contraste_distances(d, rng, n=300):
    """Pour n points uniformes dans [0,1]^d et un point requête, renvoie (contraste relatif, D_min/D_max)."""
    q = [rng.random() for _ in range(d)]
    dmin = float("inf")
    dmax = 0.0
    for _ in range(n):
        s = 0.0
        for k in range(d):
            diff = q[k] - rng.random()
            s += diff * diff
        dist = math.sqrt(s)
        dmin = min(dmin, dist)
        dmax = max(dmax, dist)
    contraste = (dmax - dmin) / dmin if dmin > 0 else 0.0
    return contraste, (dmin / dmax if dmax > 0 else 1.0)


def coquille_gaussienne(d, rng, n=1000):
    """Norme d'une gaussienne standard d-dim : (moyenne, écart-type relatif). Concentre à √d, écart relatif → 0."""
    normes = []
    for _ in range(n):
        s = sum(rng.gauss(0, 1) ** 2 for _ in range(d))
        normes.append(math.sqrt(s))
    moy = sum(normes) / n
    var = sum((x - moy) ** 2 for x in normes) / n
    return moy, (math.sqrt(var) / moy if moy > 0 else 0.0)


def analyse(dims=(2, 10, 100, 1000), rng=None):
    """Façade : concentration des distances et coquille gaussienne selon d. (ANALYSE, {courbe, ...}) ou (ABSTENTION)."""
    if rng is None or any(d < 1 for d in dims):
        return (ABSTENTION, "rng requis / d<1")
    courbe = []
    for d in dims:
        contraste, ratio = contraste_distances(d, rng)
        norme, ecart_rel = coquille_gaussienne(d, rng)
        courbe.append((d, {"contraste": contraste, "ratio_min_max": ratio, "norme_moy": norme,
                           "ecart_relatif": ecart_rel, "sqrt_d": math.sqrt(d)}))
    return (ANALYSE, {"courbe": courbe})


def formule(res) -> str:
    if res[0] == ABSTENTION:
        return f"Pas d'analyse : {res[1]}."
    c = res[1]["courbe"]
    bas, haut = c[0], c[-1]
    return (f"Contraste des distances : d={bas[0]} → {bas[1]['contraste']:.1f} ; d={haut[0]} → {haut[1]['contraste']:.2f} "
            f"(→0). À d={haut[0]}, D_min/D_max={haut[1]['ratio_min_max']:.2f} (le plus proche ≈ le plus lointain) et la "
            f"norme gaussienne se concentre à √d={haut[1]['sqrt_d']:.0f} (écart relatif {haut[1]['ecart_relatif']:.3f}). "
            f"Se fier aux distances / au kNN en haute dimension est sur-confiant.")


if __name__ == "__main__":
    import random
    print("=== MALÉDICTION DE LA DIMENSION ===\n")
    st, info = analyse(rng=random.Random(0))
    for d, m in info["courbe"]:
        print(f"  d={d:5d}: contraste={m['contraste']:7.3f}  D_min/D_max={m['ratio_min_max']:.3f}  "
              f"norme={m['norme_moy']:.2f} (√d={m['sqrt_d']:.2f}, écart rel {m['ecart_relatif']:.3f})")
    print("\n ", formule((st, info)))
