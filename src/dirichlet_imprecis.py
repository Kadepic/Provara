"""
PALIER 2 — MODÈLE DE DIRICHLET IMPRÉCIS (IDM, Walley 1996) : estimer des probabilités catégorielles sans inventer de
certitude quand les données sont rares (brique 54, 2026-06-26).

« k₁,…,k_K observations dans K catégories — quelle est P(catégorie) ? » Le maximum de vraisemblance (n_k/N) est
SUR-CONFIANT : une catégorie JAMAIS observée reçoit P=0 (certitude absurde qu'elle est impossible — cf. le [0,0] de
Wald). Le lissage de Laplace ((n_k+1)/(N+K)) donne un point mais DÉPEND de K (découper l'espace autrement change la
réponse) et masque encore l'imprécision.

L'IDM est un BAYÉSIEN ROBUSTE : au lieu d'UN prior de Dirichlet, il considère TOUTE la famille de priors de force
totale s fixée (s≈1–2) et de moyennes variables. Il en sort un INTERVALLE de probabilité par événement :
    P(A) ∈ [ n_A / (N+s) ,  (n_A + s) / (N+s) ]
Borne basse = on attribue toute la masse a priori HORS de A ; borne haute = toute DANS A. Largeur = s/(N+s) →
rétrécit avec N (apprentissage), indépendante des comptes.

PROPRIÉTÉS CLÉS :
  • HONNÊTETÉ sur le zéro : n_A=0 → [0, s/(N+s)], jamais P=0 (≠ MLE sur-confiant).
  • INVARIANCE DE REPRÉSENTATION (signature de l'IDM) : l'intervalle d'un événement A ne dépend que de n_A et N, PAS
    de K ni de la façon de partitionner le reste — contrairement à Laplace. Cohérence : Σ bornes basses ≤ 1 ≤ Σ hautes.
LE MODE D'ÉCHEC DÉMASQUÉ : le MLE assigne 0 à l'inobservé → log-loss prédictive INFINIE dès qu'une telle catégorie
réapparaît (sur-confiance catastrophique) ; l'IDM garde des bornes > 0. ABSTENTION si N+s ≤ 0. Pur Python.
"""
from __future__ import annotations

import math

ABSTENTION = "abstention"
BORNES = "bornes"


def _N(counts):
    return sum(counts)


def bornes(counts, s: float = 1.0):
    """Liste d'intervalles [P_bas, P_haut] par catégorie : (n_k/(N+s), (n_k+s)/(N+s)). N = Σ counts."""
    N = _N(counts)
    d = N + s
    return [(n / d, (n + s) / d) for n in counts]


def intervalle_evenement(n_A: float, N: float, s: float = 1.0):
    """Intervalle IDM pour un événement A (union de catégories) : ne dépend QUE de n_A et N (invariance de
    représentation), pas de K. → (n_A/(N+s), (n_A+s)/(N+s))."""
    d = N + s
    return (n_A / d, (n_A + s) / d)


def mle(counts):
    """Maximum de vraisemblance n_k/N (SUR-CONFIANT : 0 pour l'inobservé)."""
    N = _N(counts)
    if N == 0:
        return [0.0 for _ in counts]
    return [n / N for n in counts]


def laplace(counts, alpha: float = 1.0):
    """Lissage de Laplace/additif (n_k+α)/(N+Kα). DÉPEND de K (non invariant par représentation)."""
    N = _N(counts)
    K = len(counts)
    d = N + K * alpha
    return [(n + alpha) / d for n in counts]


def predictif_credal(counts, s: float = 1.0):
    """Un point prédictif MEMBRE du crédal IDM (moyenne a priori uniforme) : (n_k + s/K)/(N+s). Positif partout →
    log-loss prédictive FINIE (≠ MLE). Sert à scorer ; l'IDM reste fondamentalement un intervalle."""
    N = _N(counts)
    K = len(counts)
    d = N + s
    return [(n + s / K) / d for n in counts]


def estime(counts, indice=None, s: float = 1.0):
    """Façade : (BORNES, [intervalles]) ou, si `indice` donné, (BORNES, (bas,haut)) pour cette catégorie ;
    (ABSTENTION, raison) si N+s ≤ 0."""
    if _N(counts) + s <= 0:
        return (ABSTENTION, "N+s ≤ 0 : force a priori invalide")
    b = bornes(counts, s)
    return (BORNES, b if indice is None else b[indice])


def formule(res, nom="cette catégorie") -> str:
    if res[0] == ABSTENTION:
        return f"Je ne peux pas estimer : {res[1]}."
    val = res[1]
    if isinstance(val, tuple):
        bas, haut = val
        return (f"P({nom}) ∈ [{bas:.3f}, {haut:.3f}] (Dirichlet imprécis). "
                f"{'Catégorie jamais observée : borne basse 0 mais PAS impossible. ' if bas == 0 else ''}"
                f"Annoncer le seul {((bas+haut)/2):.3f} serait sur-confiant à ce volume de données.")
    return f"Probabilités encadrées (IDM) : {[(round(b,3),round(h,3)) for b,h in val]}."


if __name__ == "__main__":
    print("=== DIRICHLET IMPRÉCIS (IDM) — honnêteté sur les données rares ===\n")
    counts = [8, 5, 0, 0]   # 13 obs, 2 catégories jamais vues
    print(f"  counts = {counts} (N=13), s=1")
    print(f"   MLE      = {[round(p,3) for p in mle(counts)]}  (catégories 3,4 = 0 : FAUSSE certitude)")
    print(f"   IDM      = {[(round(b,3),round(h,3)) for b,h in bornes(counts)]}  (3,4 = [0, 0.071] : honnête)")
    print(f"\n  Invariance de représentation : événement A avec n_A=5, N=13")
    print(f"   IDM(A) avec K=4 : {tuple(round(x,4) for x in intervalle_evenement(5,13))}")
    print(f"   IDM(A) avec K=9 : {tuple(round(x,4) for x in intervalle_evenement(5,13))}  (INCHANGÉ)")
    print(f"   Laplace(A) K=4 : {round((5+1)/(13+4),4)}   Laplace(A) K=9 : {round((5+1)/(13+9),4)}  (CHANGE !)")
    print(" ", formule(estime(counts, 2)))
