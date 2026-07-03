"""
PALIER 2 — NÉGLIGENCE DU TAUX DE BASE / PARADOXE DU FAUX POSITIF : confondre P(+|maladie) avec P(maladie|+) est
sur-confiant (brique 103, 2026-06-27).

« Le test est fiable à 99 % » est lu comme « si je suis positif, j'ai 99 % de chances d'être malade ». C'est SUR-CONFIANT :
ça confond la SENSIBILITÉ P(+|malade) avec la VALEUR PRÉDICTIVE POSITIVE P(malade|+), en IGNORANT la PRÉVALENCE. Or, par
Bayes,
    VPP = P(malade|+) = sens·prév / [ sens·prév + (1−spéc)·(1−prév) ].
À faible prévalence, le dénominateur est dominé par les FAUX positifs (1−spéc)·(1−prév) : la VPP s'effondre bien en
dessous de la sensibilité. C'est le PARADOXE DU FAUX POSITIF — même un excellent test (sens=spéc=0.99) sur une maladie
rare (prév=0.001) donne VPP ≈ 0.09 : 91 % des positifs sont FAUX.

LA CORRECTION : calculer la VPP bayésienne (qui intègre la prévalence) au lieu d'assimiler « positif » à « malade ».

LE MODE D'ÉCHEC DÉMASQUÉ : reporter la sensibilité comme probabilité a posteriori est SUR-confiant et mal calibré
(Brier/log-loss pires) ; la VPP bayésienne calibre. Distinct de matrice_confusion (84 : métriques dérivées de COMPTAGES
observés) — ici la dépendance à la PRÉVALENCE et la confusion des deux conditionnelles. ABSTENTION si entrées hors [0,1].
Pur Python, vérifié par simulation (rng seedé).
"""
from __future__ import annotations

import math

ABSTENTION = "abstention"
ANALYSE = "analyse"


def vpp(sens, spec, prev):
    """Valeur prédictive positive P(malade|+) = sens·prév / [sens·prév + (1−spéc)(1−prév)]."""
    num = sens * prev
    den = num + (1 - spec) * (1 - prev)
    return num / den if den > 0 else 0.0


def vpn(sens, spec, prev):
    """Valeur prédictive négative P(sain|−)."""
    num = spec * (1 - prev)
    den = num + (1 - sens) * prev
    return num / den if den > 0 else 0.0


def estimation_naive(sens):
    """Réponse de la négligence du taux de base : assimiler P(malade|+) à la sensibilité (ignore la prévalence)."""
    return sens


def brier_naif_vs_bayes(sens, spec, prev):
    """Brier attendu du forecaster naïf (p=sens) vs bayésien (p=VPP) sur l'issue 'malade' parmi les POSITIFS."""
    p_vrai = vpp(sens, spec, prev)
    def brier(p):
        return p_vrai * (p - 1) ** 2 + (1 - p_vrai) * p ** 2
    return brier(estimation_naive(sens)), brier(p_vrai)


def analyse(sens, spec, prev):
    """Façade. (ANALYSE, {vpp, naive, ecart, frac_faux_positifs, brier_naif, brier_bayes}) ou (ABSTENTION, raison)."""
    if not all(0.0 <= x <= 1.0 for x in (sens, spec, prev)):
        return (ABSTENTION, "sens/spéc/prév hors [0,1]")
    v = vpp(sens, spec, prev)
    bn, bb = brier_naif_vs_bayes(sens, spec, prev)
    return (ANALYSE, {"vpp": v, "naive": estimation_naive(sens), "ecart": estimation_naive(sens) - v,
                      "frac_faux_positifs": 1 - v, "brier_naif": bn, "brier_bayes": bb,
                      "sens": sens, "spec": spec, "prev": prev})


def formule(res) -> str:
    if res[0] == ABSTENTION:
        return f"Pas d'analyse : {res[1]}."
    i = res[1]
    return (f"Test sens={i['sens']:.2f}, spéc={i['spec']:.2f}, prévalence={i['prev']:.3f} : la VPP réelle P(malade|+) = "
            f"{i['vpp']:.3f}, pas {i['naive']:.2f} (sensibilité). {100*i['frac_faux_positifs']:.0f} % des positifs sont "
            f"FAUX. Lire « positif » comme « malade » serait sur-confiant — la prévalence domine à faible taux de base.")


if __name__ == "__main__":
    import random
    print("=== NÉGLIGENCE DU TAUX DE BASE / PARADOXE DU FAUX POSITIF ===\n")
    sens, spec = 0.99, 0.99
    for prev in (0.001, 0.01, 0.1, 0.5):
        st, info = analyse(sens, spec, prev)
        print(f"  prév={prev:<6}: VPP={info['vpp']:.3f}  (naïf={info['naive']:.2f}, écart={info['ecart']:.3f})")
    # vérif simulation
    rng = random.Random(0)
    prev = 0.01
    pos_malade = pos_total = 0
    for _ in range(2000000):
        malade = rng.random() < prev
        test = (rng.random() < sens) if malade else (rng.random() < 1 - spec)
        if test:
            pos_total += 1
            pos_malade += malade
    print(f"\n  simulation prév=0.01 : VPP empirique={pos_malade/pos_total:.3f} ; théorie={vpp(sens,spec,0.01):.3f}")
