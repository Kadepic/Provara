"""
PALIER 2 — OPTIMISATION BAYÉSIENNE (surrogate par processus gaussien + acquisition) (brique, 2026-06-26).

« Trouver le maximum d'une fonction COÛTEUSE (chaque évaluation prend du temps/de l'argent) en peu d'essais. » La
stratégie GLOUTONNE — n'évaluer que là où le modèle prédit la plus haute MOYENNE — exploite sans jamais explorer :
piégée par le premier optimum LOCAL rencontré, elle ne découvre jamais le pic global plus loin. C'est de la sur-confiance
DÉCISIONNELLE : agir comme si l'estimation actuelle était la vérité.

L'optimisation BAYÉSIENNE ajuste un processus gaussien (`processus_gaussien.py`) qui fournit une moyenne ET une
INCERTITUDE calibrée, puis choisit le prochain point par une fonction d'ACQUISITION qui pèse les deux : UCB
(mean + κ·σ) ou EI (amélioration espérée). L'incertitude attire l'exploration vers les régions mal connues — d'où la
découverte du global. INVARIANT (jugé par calibration.py) : (1) l'incertitude du surrogate est calibrée (couverture des
intervalles ≈ nominal) — c'est ce qui rend l'exploration honnête ; (2) à budget d'évaluations égal, l'acquisition UCB/EI
atteint un meilleur optimum que la stratégie gloutonne sur une fonction à optimum local trompeur. ABSTENTION si pas assez
de points initiaux. Pur Python (au-dessus de processus_gaussien.py).
"""
from __future__ import annotations

import math

import processus_gaussien as GP

ABSTENTION = "abstention"
ESTIMATION = "estimation"
N_INIT_MIN = 3


def _phi(z):
    return math.exp(-0.5 * z * z) / math.sqrt(2 * math.pi)


def _Phi(z):
    return 0.5 * (1 + math.erf(z / math.sqrt(2)))


def acquisition_ucb(model, x, kappa: float = 2.0):
    """Upper Confidence Bound : mean + κ·σ. κ grand => explore davantage."""
    mean, var = GP.gp_predict(model, x)
    return mean + kappa * math.sqrt(max(var, 0.0))


def acquisition_ei(model, x, meilleur: float, xi: float = 0.01):
    """Expected Improvement (maximisation) sur le meilleur y observé."""
    mean, var = GP.gp_predict(model, x)
    s = math.sqrt(max(var, 0.0))
    if s <= 1e-12:
        return 0.0
    z = (mean - meilleur - xi) / s
    return (mean - meilleur - xi) * _Phi(z) + s * _phi(z)


def _grille(borne_inf, borne_sup, n=200):
    pas = (borne_sup - borne_inf) / (n - 1)
    return [borne_inf + i * pas for i in range(n)]


def propose_prochain(xs, ys, borne_inf, borne_sup, *, methode="ucb", kappa=2.0,
                     ell=1.0, sigma_f=1.0, sigma_n=0.1, n_grille=200):
    """Ajuste le GP sur (xs, ys) et renvoie le x de la grille qui MAXIMISE l'acquisition, ou None."""
    model = GP.gp_fit(xs, ys, ell, sigma_f, sigma_n)
    if model is None:
        return None
    meilleur = max(ys)
    best_x, best_a = None, -float("inf")
    for x in _grille(borne_inf, borne_sup, n_grille):
        a = acquisition_ucb(model, x, kappa) if methode == "ucb" else acquisition_ei(model, x, meilleur)
        if a > best_a:
            best_a, best_x = a, x
    return best_x


def optimise(f, borne_inf, borne_sup, *, n_init=4, n_iter=12, methode="ucb", kappa=2.0,
             ell=1.0, sigma_f=1.0, sigma_n=0.1, xs_init=None):
    """Boucle d'optimisation bayésienne (MAXIMISATION). Renvoie (ESTIMATION, (x*, y*), historique) ou ABSTENTION.
    `xs_init` permet d'imposer les points de départ (sinon grille uniforme). `methode` ∈ {'ucb','ei','glouton'}."""
    if n_init < N_INIT_MIN:
        return (ABSTENTION, None, f"trop peu de points initiaux (n_init={n_init} < {N_INIT_MIN})")
    if xs_init is None:
        pas = (borne_sup - borne_inf) / (n_init + 1)
        xs = [borne_inf + (i + 1) * pas for i in range(n_init)]
    else:
        xs = list(xs_init)
    ys = [f(x) for x in xs]
    for _ in range(n_iter):
        if methode == "glouton":
            # GLOUTON : prochain = argmax de la MOYENNE postérieure (κ=0, aucune exploration).
            nx = propose_prochain(xs, ys, borne_inf, borne_sup, methode="ucb", kappa=0.0,
                                  ell=ell, sigma_f=sigma_f, sigma_n=sigma_n)
        else:
            nx = propose_prochain(xs, ys, borne_inf, borne_sup, methode=methode, kappa=kappa,
                                  ell=ell, sigma_f=sigma_f, sigma_n=sigma_n)
        if nx is None:
            break
        xs.append(nx); ys.append(f(nx))
    i_best = max(range(len(ys)), key=lambda i: ys[i])
    return (ESTIMATION, (xs[i_best], ys[i_best]), list(zip(xs, ys)))


def formule(res) -> str:
    if res[0] == ABSTENTION:
        return f"Je ne peux pas optimiser : {res[2]}."
    x, y = res[1]
    return (f"Optimum trouvé : f({x:.2f}) ≈ {y:.3f}, en exploitant l'incertitude calibrée du surrogate pour explorer "
            f"(une recherche gloutonne resterait piégée dans le premier optimum local).")


if __name__ == "__main__":
    # Fonction trompeuse : bosse LOCALE en x=2 (hauteur 0.6), pic GLOBAL en x=8 (hauteur 1.0).
    def f(x):
        return 0.6 * math.exp(-((x - 2) ** 2) / 0.5) + 1.0 * math.exp(-((x - 8) ** 2) / 0.5)

    print("=== OPTIMISATION BAYÉSIENNE vs GLOUTONNE (fonction à optimum local trompeur) ===\n")
    depart = [1.5, 2.0, 2.5]                  # départ groupé près de la bosse LOCALE
    st, (xu, yu), _ = optimise(f, 0, 10, n_iter=12, methode="ucb", kappa=2.5, xs_init=depart)
    _, (xg, yg), _ = optimise(f, 0, 10, n_iter=12, methode="glouton", xs_init=depart)
    print(f"  UCB     : x*={xu:.2f}, f={yu:.3f}  (vrai global ≈ x=8, f=1.0)")
    print(f"  Glouton : x*={xg:.2f}, f={yg:.3f}  (piégé près de la bosse locale x=2)")
    print(" ", formule((st, (xu, yu), None)))
