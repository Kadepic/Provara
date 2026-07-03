"""
PALIER 2 — LOI DE GOODHART : optimiser un PROXY corrélé à l'objectif est sur-confiant (brique 113, 2026-06-28).

« Quand une mesure devient une cible, elle cesse d'être une bonne mesure » (Goodhart / Campbell). Un proxy P observé est
fortement corrélé à l'objectif vrai U — il SEMBLE donc un excellent indicateur. Mais quand on SÉLECTIONNE ou RÉCOMPENSE
sur P, on crée une pression d'optimisation : les agents poussent la composante GAMEABLE de P (effort détourné de la vraie
qualité). Sous cette pression :
    P_mesuré = U + g       (le gaming g INFLE la mesure),
    U_livré  = U − λ·g     (le gaming DÉGRADE la qualité réelle, λ>0).
La corrélation observationnelle entre P et U_livré s'EFFONDRE (voire s'inverse) ; le métrique MONTE pendant que la qualité
livrée des sélectionnés BAISSE. Sélectionner les meilleurs au sens de P livre alors MOINS que de sélectionner au sens de
U (oracle), et l'écart se creuse avec la pression.

DISTINCT de winner_curse (71 : l'ESTIMATION du gagnant est biaisée haut par bruit indépendant) — ici la RELATION
structurelle proxy↔objectif se BRISE sous optimisation (λ>0, arbitrage actif). Sans gameabilité (λ=0), maximiser P aide
encore : le défaut requiert la pression d'optimisation.

LE MODE D'ÉCHEC DÉMASQUÉ : « P corrèle avec U, donc maximisons P » est sur-confiant dès qu'il y a pression
d'optimisation. Remède : mesurer U directement, pénaliser le gameable, ou garder la métrique secrète. ABSTENTION si
données insuffisantes. Pur Python, rng seedé.
"""
from __future__ import annotations

ABSTENTION = "abstention"
ANALYSE = "analyse"


def _moyenne(xs):
    return sum(xs) / len(xs)


def correlation(xs, ys):
    mx, my = _moyenne(xs), _moyenne(ys)
    num = sum((x - mx) * (y - my) for x, y in zip(xs, ys))
    dx = sum((x - mx) ** 2 for x in xs) ** 0.5
    dy = sum((y - my) ** 2 for y in ys) ** 0.5
    return num / (dx * dy) if dx * dy else 0.0


def simule(pression, lam, n, rng, frac=0.1):
    """Génère n items (U vraie qualité, g gaming ∝ pression). Renvoie les indicateurs Goodhart.
    Sélection : top frac par PROXY vs top frac par qualité vraie (oracle)."""
    U = [rng.gauss(0, 1) for _ in range(n)]
    g = [pression * rng.random() for _ in range(n)]
    P = [u + gi for u, gi in zip(U, g)]                 # métrique mesurée
    Ueff = [u - lam * gi for u, gi in zip(U, g)]        # qualité réellement livrée
    k = max(1, int(frac * n))
    top_proxy = sorted(range(n), key=lambda i: P[i], reverse=True)[:k]
    top_oracle = sorted(range(n), key=lambda i: Ueff[i], reverse=True)[:k]
    return {
        "corr_P_U": correlation(P, Ueff),
        "proxy_des_selectionnes": _moyenne([P[i] for i in top_proxy]),
        "qualite_des_selectionnes": _moyenne([Ueff[i] for i in top_proxy]),
        "qualite_oracle": _moyenne([Ueff[i] for i in top_oracle]),
        "qualite_pop": _moyenne(Ueff),
    }


def analyse(pressions=(0.0, 1.0, 3.0), lam=1.0, n=4000, rng=None):
    """Façade : balaye la pression d'optimisation. (ANALYSE, {courbe, ...}) ou (ABSTENTION)."""
    if rng is None or n < 200:
        return (ABSTENTION, "rng requis / n trop petit")
    courbe = [(pr, simule(pr, lam, n, rng)) for pr in pressions]
    bas, haut = courbe[0][1], courbe[-1][1]
    return (ANALYSE, {"courbe": courbe,
                      "corr_chute": bas["corr_P_U"] - haut["corr_P_U"],
                      "qualite_chute": bas["qualite_des_selectionnes"] - haut["qualite_des_selectionnes"],
                      "proxy_monte": haut["proxy_des_selectionnes"] - bas["proxy_des_selectionnes"]})


def formule(res) -> str:
    if res[0] == ABSTENTION:
        return f"Pas d'analyse : {res[1]}."
    i = res[1]
    bas = i["courbe"][0][1]
    haut = i["courbe"][-1][1]
    return (f"Sans pression : corr(proxy, qualité)={bas['corr_P_U']:.2f}, qualité des sélectionnés "
            f"{bas['qualite_des_selectionnes']:+.2f}. Sous forte pression : corr={haut['corr_P_U']:.2f}, proxy des "
            f"sélectionnés MONTE à {haut['proxy_des_selectionnes']:+.2f} mais qualité livrée TOMBE à "
            f"{haut['qualite_des_selectionnes']:+.2f}. Optimiser le proxy est sur-confiant — la mesure cesse de suivre "
            f"l'objectif sous pression.")


if __name__ == "__main__":
    import random
    print("=== LOI DE GOODHART (optimiser un proxy) ===\n")
    st, info = analyse(rng=random.Random(0))
    for pr, d in info["courbe"]:
        print(f"  pression={pr}: corr={d['corr_P_U']:+.2f}  proxy_sel={d['proxy_des_selectionnes']:+.2f}  "
              f"qualité_sel={d['qualite_des_selectionnes']:+.2f}  (oracle {d['qualite_oracle']:+.2f})")
    print("\n ", formule((st, info)))
