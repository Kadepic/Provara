"""
PALIER 2 — P-HACKING / JARDIN DES CHEMINS BIFURQUANTS : le p-value du « gagnant » est sur-confiant (brique 98, 2026-06-27).

On essaie m analyses (m sous-groupes, m covariables, m spécifications — le « jardin des chemins bifurquants » de Gelman),
on garde la PLUS significative et on rapporte SON p-value brut comme s'il s'agissait d'un test unique. C'est SUR-CONFIANT :
sous l'hypothèse nulle GLOBALE (aucun effet réel), le MINIMUM de m p-values n'est PAS uniforme — il suit Beta(1, m). La
probabilité qu'AU MOINS une analyse soit « significative » à α est  1 − (1−α)^m ≈ m·α,  très supérieure à α. Le p brut du
gagnant n'est donc plus calibré : à m=20, α=0.05, le taux de faux positif réel est ~0.64, pas 0.05.

LA CORRECTION — INFÉRENCE SÉLECTIVE : ajuster le p du gagnant au nombre de chemins explorés.
    Šidák (exact si indépendants) :  p_aj = 1 − (1 − p_min)^m.
    Bonferroni (borne conservatrice) :  p_aj = min(1, m · p_min).
Le test ajusté contrôle l'erreur de 1ʳᵉ espèce du résultat RETENU (FWER) ⇒ taux de faux positif ramené ≤ α (calibré).

DISTINCT de FDR (brique 13 Benjamini-Hochberg : contrôle la PROPORTION attendue de fausses découvertes parmi BEAUCOUP de
rejets — moins conservateur, pas pour un gagnant unique) et du winner's curse (brique 71 : biais d'AMPLITUDE de l'effet
retenu, pas de p-value). Ici : calibration du p-value SÉLECTIONNÉ / FWER.

LE MODE D'ÉCHEC DÉMASQUÉ : rapporter le p brut du gagnant est sur-confiant (FPR ≫ α) ; l'ajustement sélectif le calibre.
ABSTENTION si données insuffisantes. Pur Python (erf).
"""
from __future__ import annotations

import math

ABSTENTION = "abstention"
ANALYSE = "analyse"
_SQRT2 = math.sqrt(2.0)


def _Phi(z):
    return 0.5 * (1.0 + math.erf(z / _SQRT2))


def p_bilateral(z):
    """p-value bilatérale d'une statistique z ~ N(0,1) sous H0."""
    return 2.0 * (1.0 - _Phi(abs(z)))


# ─────────────────────────── distribution du gagnant ───────────────────────────
def cdf_p_min(t, m):
    """P(min de m p-values ≤ t) sous H0 globale = 1 − (1−t)^m (le min suit Beta(1,m))."""
    return 1.0 - (1.0 - t) ** m


def prob_au_moins_un_significatif(m, alpha):
    """FPR réel d'une sélection naïve sur m analyses indépendantes = 1 − (1−α)^m ≈ m·α (≫ α)."""
    return 1.0 - (1.0 - alpha) ** m


# ─────────────────────────── ajustement sélectif ───────────────────────────
def p_ajuste_sidak(p_min, m):
    return 1.0 - (1.0 - p_min) ** m


def p_ajuste_bonferroni(p_min, m):
    return min(1.0, m * p_min)


def analyse(pvalues, alpha=0.05, methode="sidak"):
    """Façade : un ensemble de p-values issus de m chemins d'analyse. Compare le verdict NAÏF (p brut du gagnant) au
    verdict AJUSTÉ (inférence sélective). (ANALYSE, {...}) ou (ABSTENTION, raison)."""
    if not pvalues or len(pvalues) < 2 or any(not (0.0 <= p <= 1.0) for p in pvalues):
        return (ABSTENTION, "p-values insuffisantes / hors [0,1]")
    m = len(pvalues)
    p_min = min(pvalues)
    p_aj = p_ajuste_sidak(p_min, m) if methode == "sidak" else p_ajuste_bonferroni(p_min, m)
    return (ANALYSE, {"m": m, "p_min": p_min, "p_ajuste": p_aj, "alpha": alpha,
                      "significatif_naif": p_min <= alpha, "significatif_ajuste": p_aj <= alpha,
                      "fpr_naif": prob_au_moins_un_significatif(m, alpha)})


def formule(res) -> str:
    if res[0] == ABSTENTION:
        return f"Pas d'analyse : {res[1]}."
    i = res[1]
    return (f"Sur {i['m']} chemins d'analyse, le gagnant a p={i['p_min']:.4f} (naïvement "
            f"{'significatif' if i['significatif_naif'] else 'non significatif'}). Mais le p brut du gagnant est "
            f"sur-confiant : sous H0 la sélection donne un FPR de {i['fpr_naif']:.2f} (≫ α={i['alpha']}). p ajusté "
            f"(sélectif) = {i['p_ajuste']:.4f} → {'significatif' if i['significatif_ajuste'] else 'NON significatif'}.")


if __name__ == "__main__":
    import random
    rng = random.Random(0)
    m, alpha = 20, 0.05
    # sous H0 : m analyses, chacune une stat z ~ N(0,1) → p-values uniformes
    ps = [p_bilateral(rng.gauss(0, 1)) for _ in range(m)]
    print("=== P-HACKING / JARDIN DES CHEMINS BIFURQUANTS ===\n")
    print(f"  FPR naïf d'une sélection sur m={m} analyses = {prob_au_moins_un_significatif(m, alpha):.2f} (vs α={alpha})")
    print(" ", formule(analyse(ps, alpha)))
