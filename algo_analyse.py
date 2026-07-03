"""ALGO_ANALYSE — analyse de complexité & correction d'algorithmes, MÉCANISME EXACT, FAUX=0
(mission formule/concept 2026-06-29).

Posture (identique à `maths_discretes`/`physique`) : ce ne sont PAS des opinions mais des FAITS
ÉTABLIS (manuels de référence type CLRS) — ordre de croissance asymptotique, classes de complexité
des tris classiques, nombre EXACT de comparaisons des tris quadratiques, correction d'une boucle de
sommation par invariant. L'abstention est STRUCTURELLE : toute entrée invalide / hors-catalogue
(classe asymptotique inconnue, algorithme inconnu, cas inconnu, dénombrement non établi) lève
`ValueError` — JAMAIS une réponse inventée.

Vérifié en adverse par `valide_algo_analyse.py` (ancres = théorèmes/ordres connus + soundness).
"""
from __future__ import annotations

# ── Ordre de croissance asymptotique ÉTABLI (du plus lent au plus rapide) ─────────────────────────
# 1 < log n < n < n log n < n² < n³ < 2^n < n!   (fait de référence, démontrable par limites)
ORDRE_ASYMPTOTIQUE = ("1", "log n", "n", "n log n", "n^2", "n^3", "2^n", "n!")
_RANG = {c: i for i, c in enumerate(ORDRE_ASYMPTOTIQUE)}


def _entier_pos(x, *, mini=0):
    if not isinstance(x, int) or isinstance(x, bool) or x < mini:
        raise ValueError(f"entier >= {mini} attendu, reçu {x!r}")


# ── Complexité d'une imbrication de boucles ───────────────────────────────────────────────────────
def complexite_boucle(profondeur_imbrication: int) -> str:
    """k boucles imbriquées itérant chacune ~n fois -> n^k itérations (fait exact).

    Renvoie la classe polynomiale sous forme de chaîne : 0 -> '1', 1 -> 'n', 2 -> 'n^2', k -> 'n^k'.
    """
    _entier_pos(profondeur_imbrication)
    k = profondeur_imbrication
    if k == 0:
        return "1"
    if k == 1:
        return "n"
    return f"n^{k}"


# ── Comparaison asymptotique : laquelle domine ────────────────────────────────────────────────────
def compare_asymptotique(c1: str, c2: str) -> str:
    """Renvoie la classe qui DOMINE (croît le plus vite) parmi `ORDRE_ASYMPTOTIQUE`.
    Si c1 et c2 sont équivalentes, renvoie cette classe. Classe inconnue -> ValueError (abstention).
    """
    if c1 not in _RANG:
        raise ValueError(f"classe asymptotique inconnue : {c1!r}")
    if c2 not in _RANG:
        raise ValueError(f"classe asymptotique inconnue : {c2!r}")
    return c1 if _RANG[c1] >= _RANG[c2] else c2


# ── Catalogue ÉTABLI des classes de complexité des tris par comparaison (CLRS) ────────────────────
# Seules les entrées CERTAINES sont cataloguées ; (algo, cas) absent -> abstention (ValueError).
_CLASSE_TRI = {
    ("bulle", "pire"): "n^2",
    ("bulle", "moyen"): "n^2",
    ("insertion", "pire"): "n^2",
    ("insertion", "moyen"): "n^2",
    ("insertion", "meilleur"): "n",       # déjà trié : n-1 comparaisons -> linéaire
    ("selection", "pire"): "n^2",
    ("selection", "moyen"): "n^2",
    ("selection", "meilleur"): "n^2",     # selection sort : toujours n(n-1)/2 comparaisons
    ("fusion", "pire"): "n log n",
    ("fusion", "moyen"): "n log n",
    ("fusion", "meilleur"): "n log n",    # tri fusion : Θ(n log n) dans tous les cas
    ("tas", "pire"): "n log n",
    ("tas", "moyen"): "n log n",
    ("rapide", "pire"): "n^2",            # pivot dégénéré
    ("rapide", "moyen"): "n log n",
    ("rapide", "meilleur"): "n log n",    # partition équilibrée
}
_ALGOS_TRI = {"bulle", "insertion", "selection", "fusion", "tas", "rapide"}
_CAS = {"pire", "moyen", "meilleur"}


def nombre_operations_tri(n: int, algo: str, cas: str = "pire") -> str:
    """Classe de complexité ÉTABLIE d'un tri par comparaison, pour un cas donné.

    n est validé (>= 1) en garde de soundness ; la classe est un fait asymptotique indépendant de n.
    'bulle'/'insertion' = n^2 (pire cas), 'fusion'/'tas' = n log n, 'rapide' = n^2 (pire) / n log n (moyen).
    (algo, cas) hors catalogue établi -> ValueError (abstention, jamais d'invention).
    """
    _entier_pos(n, mini=1)
    if not isinstance(algo, str) or algo not in _ALGOS_TRI:
        raise ValueError(f"algorithme de tri inconnu : {algo!r}")
    if not isinstance(cas, str) or cas not in _CAS:
        raise ValueError(f"cas inconnu : {cas!r} (attendu pire/moyen/meilleur)")
    cle = (algo, cas)
    if cle not in _CLASSE_TRI:
        raise ValueError(f"classe non établie pour {cle!r} -> abstention")
    return _CLASSE_TRI[cle]


def comparaisons_pire_cas(n: int, algo: str) -> int:
    """Nombre EXACT de comparaisons dans le pire cas, pour les tris quadratiques par comparaison
    dont ce compte est un fait établi et non ambigu : bulle/insertion/selection = n(n-1)/2.
    Tout autre algorithme (fusion/tas/rapide : compte exact dépendant de l'implémentation) -> ValueError.
    """
    _entier_pos(n, mini=1)
    if not isinstance(algo, str) or algo not in _ALGOS_TRI:
        raise ValueError(f"algorithme de tri inconnu : {algo!r}")
    if algo not in {"bulle", "insertion", "selection"}:
        raise ValueError(f"compte exact non établi pour {algo!r} -> abstention")
    return n * (n - 1) // 2


# ── Correction par invariant de boucle : somme 0..n = n(n+1)/2 ────────────────────────────────────
def invariant_boucle_somme(n: int) -> bool:
    """Vérifie la CORRECTION d'une boucle de sommation 0..n par son invariant.

    Invariant maintenu : après avoir ajouté k, l'accumulateur vaut exactement k(k+1)/2.
    Exécute réellement la boucle, contrôle l'invariant à chaque pas, et confirme la valeur finale
    = n(n+1)/2 (formule fermée de Gauss). Renvoie True ssi la correction est intégralement vérifiée.
    """
    _entier_pos(n)
    s = 0
    for k in range(0, n + 1):
        s += k
        if s != k * (k + 1) // 2:          # invariant violé -> serait un bug
            return False
    return s == n * (n + 1) // 2
