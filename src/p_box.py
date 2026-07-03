"""
PALIER 2 — P-BOXES (boîtes de probabilité) : encadrer une loi de probabilité INCONNUE par une paire de fonctions de
répartition (brique 57, 2026-06-26).

Une p-box est un couple de CDF [F̲, F̄] avec F̲(x) ≤ F̄(x) ∀x : elle affirme que la vraie CDF F vérifie
F̲(x) ≤ F(x) ≤ F̄(x) partout. Elle marie incertitude SUR LA VALEUR (intervalle) et SUR LA DISTRIBUTION (probabilité)
— l'objet central de l'analyse d'incertitude imprécise (Ferson). Elle borne automatiquement :
  • la probabilité d'un seuil :  P(X ≤ x) ∈ [F̲(x), F̄(x)]
  • l'espérance :                E[X] ∈ [moyenne des bornes basses, moyenne des bornes hautes]
  • un quantile :                q_p ∈ [F̄⁻¹(p), F̲⁻¹(p)]   (les inverses s'échangent)

CONSTRUCTION DEPUIS DES DONNÉES INTERVALLES (capteur à tolérance, mesure censurée) : chaque donnée vᵢ n'est connue
qu'à vᵢ ∈ [aᵢ, bᵢ]. Alors  F̲(x)=#{bᵢ≤x}/n,  F̄(x)=#{aᵢ≤x}/n  ENCADRENT la vraie CDF empirique F_n (preuve :
bᵢ≤x ⟹ vᵢ≤x donne F̲≤F_n ; vᵢ≤x ⟹ aᵢ≤x donne F_n≤F̄). Garantie, sans hypothèse de forme.

LE MODE D'ÉCHEC DÉMASQUÉ : réduire la p-box à UNE CDF précise (prendre le milieu des intervalles comme exact) et
annoncer une probabilité/quantile ponctuel est SUR-CONFIANT — la vraie valeur peut être n'importe où dans le bracket.
Vertu : quand les intervalles se resserrent (données précises), la p-box COLLAPSE sur la CDF empirique (imprécision→0).
ABSTENTION si une donnée a aᵢ>bᵢ ou liste vide. Pur Python.
"""
from __future__ import annotations

import bisect
import math

ABSTENTION = "abstention"
PBOX = "pbox"


class PBox:
    """p-box discrète construite depuis des données intervalles. F̲ = CDF des bornes hautes, F̄ = CDF des basses."""

    __slots__ = ("a", "b", "n")

    def __init__(self, a_tries, b_tries, n):
        self.a = a_tries   # bornes basses triées
        self.b = b_tries   # bornes hautes triées
        self.n = n

    def F_bas(self, x):
        """F̲(x) = #{bᵢ ≤ x}/n (CDF INFÉRIEURE : la plus à droite)."""
        return bisect.bisect_right(self.b, x) / self.n

    def F_haut(self, x):
        """F̄(x) = #{aᵢ ≤ x}/n (CDF SUPÉRIEURE : la plus à gauche)."""
        return bisect.bisect_right(self.a, x) / self.n

    def proba_seuil(self, x):
        """P(X ≤ x) ∈ [F̲(x), F̄(x)]."""
        return (self.F_bas(x), self.F_haut(x))

    def esperance(self):
        """E[X] ∈ [moyenne(aᵢ), moyenne(bᵢ)]."""
        return (sum(self.a) / self.n, sum(self.b) / self.n)

    def quantile(self, p):
        """q_p ∈ [q_bas, q_haut] : q_bas = (⌈p·n⌉)ᵉ plus petite borne BASSE (via F̄) ; q_haut via F̲ (bornes hautes)."""
        if not (0.0 < p <= 1.0):
            raise ValueError("p doit être dans (0,1]")
        k = min(self.n, max(1, math.ceil(p * self.n)))
        return (self.a[k - 1], self.b[k - 1])

    def largeur_max(self):
        """Imprécision maximale = sup_x (F̄(x) − F̲(x))."""
        pts = sorted(set(self.a + self.b))
        return max(self.F_haut(x) - self.F_bas(x) for x in pts) if pts else 0.0


def depuis_intervalles(intervalles):
    """Construit une p-box depuis [(a₁,b₁),…] (données connues par intervalle). (PBOX, pbox) ou (ABSTENTION, raison)."""
    if not intervalles:
        return (ABSTENTION, "aucune donnée")
    a, b = [], []
    for ai, bi in intervalles:
        if ai > bi:
            return (ABSTENTION, f"intervalle invalide a>b : ({ai},{bi})")
        a.append(float(ai)); b.append(float(bi))
    return (PBOX, PBox(sorted(a), sorted(b), len(intervalles)))


def cdf_precise(intervalles):
    """CDF ponctuelle SUR-CONFIANTE : prend le milieu de chaque intervalle comme valeur exacte. Renvoie une fonction."""
    mids = sorted((ai + bi) / 2 for ai, bi in intervalles)
    n = len(mids)
    return lambda x: bisect.bisect_right(mids, x) / n


def formule(res, x=None) -> str:
    if res[0] == ABSTENTION:
        return f"Je ne peux pas construire la p-box : {res[1]}."
    pb = res[1]
    elo, ehi = pb.esperance()
    base = f"p-box sur {pb.n} données ; E[X] ∈ [{elo:.3f}, {ehi:.3f}] (imprécision max {pb.largeur_max():.3f})"
    if x is not None:
        lo, hi = pb.proba_seuil(x)
        return base + f" ; P(X ≤ {x}) ∈ [{lo:.3f}, {hi:.3f}] (annoncer un point précis serait sur-confiant)."
    return base + "."


if __name__ == "__main__":
    print("=== P-BOX — encadrer une loi inconnue depuis des données intervalles ===\n")
    data = [(1, 2), (2, 4), (3, 3), (0, 5), (4, 6)]   # 5 mesures à tolérance
    st, pb = depuis_intervalles(data)
    print(f"  données = {data}")
    for x in (2, 3, 4):
        lo, hi = pb.proba_seuil(x)
        print(f"   P(X ≤ {x}) ∈ [{lo:.2f}, {hi:.2f}]")
    print(f"   E[X] ∈ {tuple(round(v,2) for v in pb.esperance())}  ; médiane ∈ {pb.quantile(0.5)}")
    print(f"   imprécision max = {pb.largeur_max():.2f}")
    print(" ", formule((st, pb), x=3))
    # données précises -> collapse
    st2, pb2 = depuis_intervalles([(v, v) for v in (1, 2, 3, 3, 5)])
    print(f"\n  Données PRÉCISES → imprécision max = {pb2.largeur_max():.2f} (la p-box collapse sur la CDF empirique).")
