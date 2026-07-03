"""
PALIER 2 — CALIBRATION D'UNE DISTRIBUTION PRÉDICTIVE (PIT + pinball, brique 26, 2026-06-25).

Quand on prédit non pas une valeur mais une DISTRIBUTION complète (CDF F prédictive), la bonne question d'honnêteté
est : la réalité tombe-t-elle aux bons quantiles ? Outil canonique = la PIT (Probability Integral Transform) :

    uᵢ = Fᵢ(yᵢ)     (valeur de la CDF prédictive au point réalisé)

Si la distribution prédictive est CALIBRÉE, les uᵢ sont ~UNIFORMES sur [0,1] (l'histogramme PIT est PLAT). Les écarts
RÉVÈLENT le défaut, et son SENS :
  • PIT en forme de U (masse aux extrêmes) -> distribution TROP ÉTROITE = SUR-CONFIANT (var(PIT) > 1/12).
  • PIT en bosse centrale -> distribution TROP LARGE = SOUS-CONFIANT (var(PIT) < 1/12).
  • PIT plat -> CALIBRÉ (var(PIT) ≈ 1/12 ≈ 0.083, la variance d'une loi uniforme).

Plus la PERTE PINBALL (quantile loss) pour estimer/évaluer un quantile τ : ρ_τ(y−q) = (τ − 1{y<q})(y−q), minimisée
par le vrai τ-quantile (règle propre orientée quantile).

INVARIANT (jugé ici-même par la PIT, prouvé Monte-Carlo dans valide_predictif) : on NOMME la sur-confiance d'une
distribution prédictive. ABSTENTION si trop peu de réalisations.
"""
from __future__ import annotations

ABSTENTION = "abstention"
CALIBRE = "calibre"
SURCONFIANT = "surconfiant"
SOUSCONFIANT = "sousconfiant"
N_MIN = 30
_VAR_UNIF = 1.0 / 12.0


def pit_echantillon(echantillons, verites):
    """Calcule les valeurs PIT u = F(y) où F est la CDF EMPIRIQUE d'un échantillon prédictif (un échantillon par cas).
    `echantillons` = liste (un par cas) de listes de valeurs simulées ; `verites` = valeur réalisée. u = fraction de
    l'échantillon ≤ y (avec demi-correction de continuité)."""
    pits = []
    for ech, y in zip(echantillons, verites):
        xs = sorted(float(v) for v in ech)
        n = len(xs)
        if n == 0:
            raise ValueError("échantillon vide")
        inf = sum(1 for x in xs if x < y)
        egal = sum(1 for x in xs if x == y)
        pits.append((inf + 0.5 * egal) / n)
    return pits


def pit_cdf(cdf_au_point):
    """Si on a déjà les valeurs F_i(y_i) (CDF prédictive évaluée au réalisé), la PIT EST cette liste. Passe-plat
    explicite (clampe dans [0,1])."""
    return [max(0.0, min(1.0, float(u))) for u in cdf_au_point]


def histogramme_pit(pits, n_bins=10):
    """Histogramme PIT (comptes par casier) : plat = calibré."""
    h = [0] * n_bins
    for u in pits:
        b = min(n_bins - 1, int(max(0.0, min(1.0, u)) * n_bins))
        h[b] += 1
    return h


def variance_pit(pits):
    n = len(pits)
    m = sum(pits) / n
    return sum((u - m) ** 2 for u in pits) / n


def est_calibre_pit(pits, tol=0.015):
    """Verdict sur une distribution prédictive via la variance de la PIT. Renvoie (verdict, infos).
    var > 1/12 + tol -> SURCONFIANT (trop étroite) ; var < 1/12 − tol -> SOUSCONFIANT (trop large) ; sinon CALIBRE."""
    n = len(pits)
    if n < N_MIN:
        return (ABSTENTION, {"n": n, "raison": f"trop peu de réalisations (n={n} < {N_MIN})"})
    var = variance_pit(pits)
    moy = sum(pits) / n
    infos = {"n": n, "variance_pit": var, "var_uniforme": _VAR_UNIF, "moyenne_pit": moy}
    if var > _VAR_UNIF + tol:
        verdict = SURCONFIANT
    elif var < _VAR_UNIF - tol:
        verdict = SOUSCONFIANT
    else:
        verdict = CALIBRE
    return (verdict, infos)


def perte_pinball(q, y, tau):
    """Perte pinball (quantile loss) du quantile q pour la réalisation y au niveau tau. Minimisée par le vrai τ-quantile."""
    d = float(y) - float(q)
    return (tau - (1.0 if d < 0 else 0.0)) * d


def quantile_pinball(echantillon, tau):
    """τ-quantile empirique (minimise la perte pinball moyenne) par interpolation."""
    xs = sorted(float(v) for v in echantillon)
    n = len(xs)
    if n == 0:
        raise ValueError("échantillon vide")
    i = tau * (n - 1)
    lo = int(i)
    if lo + 1 >= n:
        return xs[-1]
    return xs[lo] * (1 - (i - lo)) + xs[lo + 1] * (i - lo)


def formule(verdict_infos) -> str:
    verdict, infos = verdict_infos
    if verdict == ABSTENTION:
        return f"Je ne peux pas juger ma distribution prédictive : {infos.get('raison')}."
    if verdict == SURCONFIANT:
        return ("⚠ Ma distribution prédictive est TROP ÉTROITE (la réalité tombe trop souvent dans les queues) : "
                "je suis sur-confiant sur l'étendue des possibles.")
    if verdict == SOUSCONFIANT:
        return "Ma distribution prédictive est trop LARGE (prudente) : la réalité tombe trop souvent au centre."
    return "Ma distribution prédictive est calibrée : la réalité se répartit uniformément sur les quantiles annoncés."


if __name__ == "__main__":
    print("=== CALIBRATION D'UNE DISTRIBUTION PRÉDICTIVE (PIT) ===\n")
    import random
    rng = random.Random(0)
    def ech(mu, sd):
        return [[rng.gauss(mu, sd) for _ in range(200)] for _ in range(2000)]
    vt = [rng.gauss(0, 1) for _ in range(2000)]
    for nom, sd in [("calibré", 1.0), ("trop étroit", 0.5), ("trop large", 2.0)]:
        pits = pit_echantillon(ech(0, sd), vt)
        print(f"  {nom:12} : var(PIT)={variance_pit(pits):.3f} ->", formule(est_calibre_pit(pits)))
