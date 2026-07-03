"""
PALIER 2 — BANDIT CONTEXTUEL (LinUCB) : le choix glouton (estimation ponctuelle, exploration nulle) est sur-confiant
(brique 97, 2026-06-27).

À chaque tour un CONTEXTE x arrive, on choisit un bras, on observe une récompense r ≈ θ*_a·x + bruit. Le bras OPTIMAL
DÉPEND du contexte. Un agent GLOUTON qui joue argmax de son estimation PONCTUELLE θ̂_a·x (exploration nulle) est
SUR-CONFIANT : il traite une estimation bruitée et sous-explorée comme une vérité, se VERROUILLE sur un bras qui « semble »
bon, et ne corrige jamais — regret LINÉAIRE (une fraction constante d'erreurs pour toujours).

LA CORRECTION — LinUCB : on garde une LARGEUR DE CONFIANCE honnête sur chaque estimation. Pour le bras a, avec
A_a = λI + Σ xxᵀ et θ̂_a = A_a⁻¹ Σ r x, le score OPTIMISTE est  θ̂_a·x + α·√(xᵀ A_a⁻¹ x). Le bonus = écart-type de
l'estimation projetée sur x ; il est GRAND quand a est peu testé dans cette direction (→ on explore), PETIT quand a est
bien estimé (→ on exploite). Optimisme calibré ⇒ regret SUBLINÉAIRE (regret/T → 0), sans verrouillage.

LE MODE D'ÉCHEC DÉMASQUÉ : exploiter une estimation ponctuelle (glouton, ε=0) est sur-confiant et donne un regret
linéaire ; la largeur de confiance UCB le rend sublinéaire. Ignorer le contexte est aussi sur-confiant si le meilleur
bras en dépend. ABSTENTION si données insuffisantes. Pur Python (algèbre linéaire maison, rng seedé requis).
"""
from __future__ import annotations

import math

ABSTENTION = "abstention"
ANALYSE = "analyse"


# ─────────────────────────── algèbre linéaire (petites dimensions) ───────────────────────────
def _inverse(A):
    """Inverse d'une matrice d×d par Gauss-Jordan (d petit)."""
    d = len(A)
    M = [list(A[i]) + [1.0 if j == i else 0.0 for j in range(d)] for i in range(d)]
    for col in range(d):
        piv = max(range(col, d), key=lambda r: abs(M[r][col]))
        if abs(M[piv][col]) < 1e-15:
            raise ValueError("matrice singulière")
        M[col], M[piv] = M[piv], M[col]
        p = M[col][col]
        M[col] = [v / p for v in M[col]]
        for r in range(d):
            if r != col:
                f = M[r][col]
                M[r] = [M[r][k] - f * M[col][k] for k in range(2 * d)]
    return [row[d:] for row in M]


def _matvec(A, v):
    return [sum(A[i][j] * v[j] for j in range(len(v))) for i in range(len(A))]


def _dot(a, b):
    return sum(x * y for x, y in zip(a, b))


# ─────────────────────────── agent LinUCB / glouton ───────────────────────────
class Agent:
    """Bandit contextuel linéaire à K bras (disjoint). alpha=0 ⇒ GLOUTON (sur-confiant) ; alpha>0 ⇒ LinUCB."""

    def __init__(self, k, d, alpha, lam=1.0):
        self.k, self.d, self.alpha = k, d, alpha
        self.A = [[[lam if i == j else 0.0 for j in range(d)] for i in range(d)] for _ in range(k)]
        self.b = [[0.0] * d for _ in range(k)]
        self._Ainv = [_inverse(self.A[a]) for a in range(k)]

    def theta(self, a):
        return _matvec(self._Ainv[a], self.b[a])

    def largeur(self, a, x):
        """Largeur de confiance √(xᵀ A_a⁻¹ x) (écart-type de l'estimation projetée sur x)."""
        return math.sqrt(max(0.0, _dot(x, _matvec(self._Ainv[a], x))))

    def score(self, a, x):
        return _dot(self.theta(a), x) + self.alpha * self.largeur(a, x)

    def choisir(self, x):
        return max(range(self.k), key=lambda a: self.score(a, x))

    def maj(self, a, x, r):
        for i in range(self.d):
            for j in range(self.d):
                self.A[a][i][j] += x[i] * x[j]
            self.b[a][i] += r * x[i]
        self._Ainv[a] = _inverse(self.A[a])


# ─────────────────────────── simulation ───────────────────────────
def simule(thetas, contextes, rng, alpha, bruit=0.1, sans_contexte=False):
    """Joue une séquence de contextes. Renvoie le regret cumulé vs l'oracle (meilleur bras par contexte).
    sans_contexte=True ⇒ l'agent ignore x (politique moyenne par bras)."""
    k = len(thetas)
    d = len(thetas[0])
    ag = Agent(k, 1 if sans_contexte else d, alpha)
    regret = 0.0
    courbe = []
    for x in contextes:
        xx = [1.0] if sans_contexte else x
        a = ag.choisir(xx)
        moy = [_dot(thetas[j], x) for j in range(k)]          # récompenses moyennes vraies
        r = moy[a] + rng.gauss(0, bruit)
        regret += max(moy) - moy[a]
        ag.maj(a, xx, r)
        courbe.append(regret)
    return regret, courbe, ag


def analyse(thetas, contextes, rng, alpha=1.0, bruit=0.1):
    """Façade : compare LinUCB (alpha) vs glouton (alpha=0). (ANALYSE, {...}) ou (ABSTENTION, raison)."""
    if rng is None or len(contextes) < 20 or len(thetas) < 2:
        return (ABSTENTION, "données insuffisantes / rng requis")
    import random as _r
    g = _r.Random(rng.random())
    u = _r.Random(rng.random())
    reg_g, courbe_g, _ = simule(thetas, contextes, g, alpha=0.0, bruit=bruit)
    reg_u, courbe_u, ag_u = simule(thetas, contextes, u, alpha=alpha, bruit=bruit)
    n = len(contextes)
    return (ANALYSE, {"regret_glouton": reg_g, "regret_linucb": reg_u,
                      "regret_par_tour_glouton": reg_g / n, "regret_par_tour_linucb": reg_u / n,
                      "courbe_glouton": courbe_g, "courbe_linucb": courbe_u, "n": n})


def formule(res) -> str:
    if res[0] == ABSTENTION:
        return f"Pas d'analyse : {res[1]}."
    i = res[1]
    return (f"Bandit contextuel : regret GLOUTON {i['regret_glouton']:.1f} (≈{i['regret_par_tour_glouton']:.3f}/tour, "
            f"linéaire) vs LinUCB {i['regret_linucb']:.1f} (≈{i['regret_par_tour_linucb']:.3f}/tour → 0). Exploiter "
            f"l'estimation ponctuelle (glouton) serait sur-confiant — il se verrouille sur un mauvais bras ; la largeur "
            f"de confiance UCB garde un optimisme calibré.")


if __name__ == "__main__":
    import random
    rng = random.Random(0)
    # 3 bras, contexte 2D ; le meilleur bras DÉPEND du contexte
    thetas = [[1.0, 0.0], [0.0, 1.0], [0.6, 0.6]]
    contextes = [[1.0, 0.0] if rng.random() < 0.5 else [0.0, 1.0] for _ in range(400)]
    print("=== BANDIT CONTEXTUEL (LinUCB vs glouton) ===\n")
    print(" ", formule(analyse(thetas, contextes, random.Random(1))))
