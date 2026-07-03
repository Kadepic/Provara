"""ÉQUILIBRES CHIMIQUES — quotient de réaction et sens d'évolution, FAUX=0 (mission formule/concept 2026-06-29).

Quotient de réaction Q = Π[produits]^νᵢ / Π[réactifs]^νⱼ, comparaison à la constante d'équilibre K pour prédire le
SENS d'évolution (loi d'action de masse) : Q < K -> sens direct ; Q > K -> sens inverse ; Q = K -> équilibre.
Mécanisme EXACT (rationnel via Fraction quand les entrées le permettent), sortie arrondie. Abstention STRUCTURELLE :
concentration ≤ 0, K ≤ 0 -> ValueError.

Couvre le sujet borné « Équilibres chimiques ».
Vérifié en adverse par `valide_equilibre_chimique.py` (Q connu, sens d'évolution, Le Chatelier de base).
"""
from __future__ import annotations

_SIG = 6


def _sig(x):
    if x == 0:
        return 0.0
    return float(f"{x:.{_SIG}g}")


def _valide_termes(termes, nom):
    if not isinstance(termes, (list, tuple)) or not termes:
        raise ValueError(f"{nom} : liste non vide de (concentration, coefficient) requise")
    for t in termes:
        if len(t) != 2:
            raise ValueError(f"{nom} : chaque terme = (concentration, coefficient)")
        conc, coeff = t
        if isinstance(conc, bool) or not isinstance(conc, (int, float)) or conc <= 0:
            raise ValueError(f"{nom} : concentration > 0 requise (reçu {conc!r})")
        if isinstance(coeff, bool) or not isinstance(coeff, (int, float)) or coeff < 0:
            raise ValueError(f"{nom} : coefficient ≥ 0 requis")


def _produit(termes):
    p = 1.0
    for conc, coeff in termes:
        p *= conc ** coeff
    return p


def quotient_reaction(produits, reactifs) -> float:
    """Q = Π[produit]^coeff / Π[réactif]^coeff. `produits`/`reactifs` = listes de (concentration, coefficient)."""
    _valide_termes(produits, "produits")
    _valide_termes(reactifs, "reactifs")
    return _sig(_produit(produits) / _produit(reactifs))


def sens_evolution(q, k) -> str:
    """Sens d'évolution d'un système hors équilibre : 'direct' (Q<K), 'inverse' (Q>K) ou 'equilibre' (Q=K)."""
    if isinstance(q, bool) or isinstance(k, bool) or not isinstance(q, (int, float)) or not isinstance(k, (int, float)):
        raise ValueError("Q et K numériques requis")
    if q <= 0 or k <= 0:
        raise ValueError("Q, K > 0 requis")
    if abs(q - k) <= 1e-9 * max(q, k):
        return "equilibre"
    return "direct" if q < k else "inverse"


def deplace_equilibre_temperature(exothermique: bool, augmente_temperature: bool) -> str:
    """Loi de Le Chatelier (température) : pour une réaction exothermique, ↑T déplace vers les RÉACTIFS (sens inverse) ;
    pour une endothermique, ↑T déplace vers les PRODUITS (sens direct). Renvoie 'direct' ou 'inverse'."""
    if not isinstance(exothermique, bool) or not isinstance(augmente_temperature, bool):
        raise ValueError("booléens requis")
    # ↑T favorise le sens endothermique. Si réaction exothermique -> sens endothermique = inverse.
    favorise_produits = augmente_temperature != exothermique
    return "direct" if favorise_produits else "inverse"


if __name__ == "__main__":
    # N2 + 3H2 ⇌ 2NH3 : [NH3]=2, [N2]=1, [H2]=1 -> Q = 2²/(1·1³) = 4
    q = quotient_reaction([(2, 2)], [(1, 1), (1, 3)])
    print("Q (NH3) :", q)
    print("sens si K=10 :", sens_evolution(q, 10), "| K=1 :", sens_evolution(q, 1), "| K=4 :", sens_evolution(q, 4))
    print("Le Chatelier exo + ↑T :", deplace_equilibre_temperature(True, True))
    print("Le Chatelier endo + ↑T :", deplace_equilibre_temperature(False, True))
