"""
PALIER 2 — RÉGRESSION VERS LA MOYENNE (Galton) : un rebond statistique n'est pas un effet causal (brique 86,
2026-06-27).

Quand une mesure comporte du BRUIT, les observations EXTRÊMES sont en moyenne suivies de valeurs MOINS extrêmes —
purement par hasard. Si on SÉLECTIONNE un groupe sur une 1ʳᵉ mesure extrême (les « pires » élèves, les patients les
plus malades, les actions les plus chutées) puis on le re-mesure, il « s'améliore » SANS aucune intervention.

Modèle : valeur vraie θ + bruit → X₁=θ+ε₁, X₂=θ+ε₂. La fiabilité ρ = Var(θ)/Var(X) = corr(X₁,X₂). Pour un groupe
sélectionné d'écart (X̄₁−μ), l'espérance de la 2ᵉ mesure est  X̄₂ ≈ μ + ρ·(X̄₁−μ)  : elle régresse vers la moyenne
d'un facteur (1−ρ). ρ=1 (pas de bruit) → aucune régression ; ρ=0 (tout bruit) → retour total à μ.

LE MODE D'ÉCHEC DÉMASQUÉ : attribuer ce rebond à une cause (« le tutorat a marché », « la punition est efficace »,
« le management a redressé l'action ») est SUR-CONFIANT — sans groupe de CONTRÔLE, l'amélioration attendue par
régression à la moyenne est confondue avec un effet. Inversion célèbre : sélectionner les MEILLEURS → ils régressent
vers le BAS (« la louange nuit »). ABSTENTION si données insuffisantes. Pur Python.
"""
from __future__ import annotations

import math

ABSTENTION = "abstention"
RTM = "rtm"


def moyenne(xs):
    return sum(xs) / len(xs)


def correlation(x1, x2):
    """Fiabilité ρ = corrélation entre les deux mesures."""
    n = len(x1)
    m1, m2 = moyenne(x1), moyenne(x2)
    cov = sum((x1[i] - m1) * (x2[i] - m2) for i in range(n)) / n
    s1 = math.sqrt(sum((x - m1) ** 2 for x in x1) / n)
    s2 = math.sqrt(sum((x - m2) ** 2 for x in x2) / n)
    return cov / (s1 * s2) if s1 > 0 and s2 > 0 else 0.0


def selectionne(x1, x2, fraction=0.1, cote="bas"):
    """Indices du groupe extrême sur X₁ (fraction du bas ou du haut)."""
    n = len(x1)
    k = max(1, int(round(fraction * n)))
    ordre = sorted(range(n), key=lambda i: x1[i], reverse=(cote == "haut"))
    return ordre[:k]


def regression_vers_moyenne(x1, x2, fraction=0.1, cote="bas"):
    """Mesure la régression vers la moyenne d'un groupe sélectionné sur X₁. Renvoie un dict d'indicateurs."""
    mu = moyenne(x1)
    rho = correlation(x1, x2)
    idx = selectionne(x1, x2, fraction, cote)
    s1 = moyenne([x1[i] for i in idx]); s2 = moyenne([x2[i] for i in idx])
    return {"mu": mu, "rho": rho, "moy_x1_sel": s1, "moy_x2_sel": s2,
            "changement": s2 - s1, "attendu_rtm": mu + rho * (s1 - mu),
            "ecart_x1": abs(s1 - mu), "ecart_x2": abs(s2 - mu)}


def analyse(x1, x2, fraction=0.1, cote="bas"):
    """Façade : (RTM, indicateurs) ou (ABSTENTION, raison)."""
    if len(x1) < 10 or len(x1) != len(x2):
        return (ABSTENTION, "données insuffisantes (n<10) ou tailles différentes")
    return (RTM, regression_vers_moyenne(x1, x2, fraction, cote))


def formule(res) -> str:
    if res[0] == ABSTENTION:
        return f"Pas d'analyse : {res[1]}."
    i = res[1]
    sens = "amélioré" if i["changement"] > 0 else "dégradé"
    return (f"Groupe extrême : X̄₁={i['moy_x1_sel']:.2f} → X̄₂={i['moy_x2_sel']:.2f} (semble s'être {sens} de "
            f"{abs(i['changement']):.2f}). Mais la régression vers la moyenne (ρ={i['rho']:.2f}) PRÉDIT X̄₂≈"
            f"{i['attendu_rtm']:.2f} SANS aucune cause. Attribuer ce rebond à une intervention serait sur-confiant.")


if __name__ == "__main__":
    import random
    rng = random.Random(0)
    def echantillon(rng, n, s_theta, s_eps):
        x1, x2 = [], []
        for _ in range(n):
            th = rng.gauss(0, s_theta)
            x1.append(th + rng.gauss(0, s_eps)); x2.append(th + rng.gauss(0, s_eps))
        return x1, x2
    print("=== RÉGRESSION VERS LA MOYENNE ===\n")
    for s_th, s_ep, lab in [(1, 1, "bruit modéré (ρ≈0.5)"), (1, 0.01, "pas de bruit (ρ≈1)"), (0.01, 1, "tout bruit (ρ≈0)")]:
        x1, x2 = echantillon(rng, 4000, s_th, s_ep)
        i = regression_vers_moyenne(x1, x2, 0.1, "bas")
        print(f"  {lab:24s}: pires 10% X̄₁={i['moy_x1_sel']:+.2f} → X̄₂={i['moy_x2_sel']:+.2f} "
              f"(RTM attendu {i['attendu_rtm']:+.2f}, ρ={i['rho']:.2f})")
    x1, x2 = echantillon(rng, 4000, 1, 1)
    print("\n  Sélection des MEILLEURS (louange) :", "régression vers le BAS →",
          f"X̄₁={regression_vers_moyenne(x1,x2,0.1,'haut')['moy_x1_sel']:+.2f} → X̄₂={regression_vers_moyenne(x1,x2,0.1,'haut')['moy_x2_sel']:+.2f}")
    print(" ", formule(analyse(x1, x2, 0.1, "bas")))
