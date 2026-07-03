"""
PALIER 2 — CONFIDENTIALITÉ DIFFÉRENTIELLE (mécanisme de Laplace, ε-DP) : garantir la vie privée avec un bruit
CALIBRÉ, pas une promesse en l'air (brique 75, 2026-06-27).

Publier une statistique f(D) d'un jeu de données peut révéler des individus. La ε-DP exige que retirer/changer UNE
personne change peu la loi de la sortie : pour tous voisins D, D' et toute sortie o,
    P(M(D)=o) ≤ e^ε · P(M(D')=o).
Le MÉCANISME DE LAPLACE l'obtient en ajoutant un bruit calibré à la SENSIBILITÉ Δf (variation max de f entre voisins) :
    M(D) = f(D) + Laplace(0, b),  avec  b = Δf/ε.
La perte de confidentialité RÉELLE d'un bruit d'échelle b est Δf/b (exacte pour Laplace : |ln ratio| = |Δ|/b ≤ Δf/b).

LE MODE D'ÉCHEC DÉMASQUÉ : SOUS-BRUITER (b < Δf/ε, pour « garder de l'utilité ») rend la perte réelle Δf/b > ε →
on ANNONCE ε mais on offre BIEN MOINS de vie privée = SUR-CONFIANCE (un attaquant distingue mieux les voisins que ne
le permet ε). COMPOSITION : K requêtes ε-DP coûtent (basiquement) Kε au TOTAL — croire que « chaque requête est privée
donc tout va bien » sous-compte la fuite cumulée. Compromis : ε petit ⇒ plus de bruit ⇒ moins d'utilité. ABSTENTION
si ε≤0 / Δf<0. Pur Python.
"""
from __future__ import annotations

import math

ABSTENTION = "abstention"
PRIVE = "prive"


def laplace(rng, b):
    """Tire un bruit de Laplace(0, b) par inversion : −b·sgn(u)·ln(1−2|u|), u∈(−0.5,0.5)."""
    u = rng.random() - 0.5
    return -b * (1 if u >= 0 else -1) * math.log(1 - 2 * abs(u)) if u != 0 else 0.0


def mecanisme(rng, valeur, sensibilite, epsilon):
    """Mécanisme de Laplace ε-DP : valeur + Laplace(0, Δf/ε)."""
    return valeur + laplace(rng, sensibilite / epsilon)


def echelle_bruit(sensibilite, epsilon):
    """Échelle de bruit requise b = Δf/ε pour la ε-DP."""
    return sensibilite / epsilon


def perte_confidentialite(sensibilite, b):
    """Perte de confidentialité RÉELLE d'un bruit d'échelle b : ε_réel = Δf/b (exacte pour Laplace)."""
    return sensibilite / b if b > 0 else float("inf")


def ratio_log_max(sensibilite, b):
    """max_o |ln P(M(D)=o)/P(M(D')=o)| = Δf/b (= ε_réel) : la borne ε-DP exacte du Laplace."""
    return sensibilite / b if b > 0 else float("inf")


def composition(epsilons):
    """Composition BASIQUE : K mécanismes ε_i-DP → (Σε_i)-DP (la fuite cumulée s'ADDITIONNE)."""
    return sum(epsilons)


def borne_avantage(epsilon):
    """Borne sur l'avantage d'un attaquant qui distingue deux voisins : (e^ε−1)/(e^ε+1)."""
    return (math.exp(epsilon) - 1) / (math.exp(epsilon) + 1)


def analyse(sensibilite, epsilon, b=None):
    """Façade : compare le bruit choisi b à l'exigence Δf/ε. (PRIVE, {b_requis, b, epsilon_reel, conforme}) ou
    (ABSTENTION, raison). Si b=None, utilise le bruit correct b=Δf/ε."""
    if epsilon <= 0 or sensibilite < 0:
        return (ABSTENTION, "ε≤0 ou Δf<0")
    b_req = echelle_bruit(sensibilite, epsilon)
    if b is None:
        b = b_req
    eps_reel = perte_confidentialite(sensibilite, b)
    return (PRIVE, {"b_requis": b_req, "b": b, "epsilon_annonce": epsilon, "epsilon_reel": eps_reel,
                    "conforme": eps_reel <= epsilon + 1e-12})


def formule(res) -> str:
    if res[0] == ABSTENTION:
        return f"Pas de garantie : {res[1]}."
    i = res[1]
    if i["conforme"]:
        return f"Bruit b={i['b']:.3f} ⇒ {i['epsilon_reel']:.2f}-DP (≤ {i['epsilon_annonce']:.2f} annoncé) : garantie tenue."
    return (f"⚠ Sous-bruité : b={i['b']:.3f} offre seulement {i['epsilon_reel']:.2f}-DP alors qu'on annonce "
            f"{i['epsilon_annonce']:.2f}-DP — SUR-CONFIANCE sur la vie privée (il faudrait b≥{i['b_requis']:.3f}).")


if __name__ == "__main__":
    import random
    rng = random.Random(0)
    print("=== CONFIDENTIALITÉ DIFFÉRENTIELLE (Laplace, ε-DP) ===\n")
    Df, eps = 1.0, 0.5
    print(f"  Δf={Df}, ε annoncé={eps} → bruit requis b=Δf/ε={echelle_bruit(Df,eps):.1f}")
    print("  ", formule(analyse(Df, eps)))                       # bruit correct
    print("  ", formule(analyse(Df, eps, b=0.5)))                # sous-bruité (b<2)
    print(f"  Composition de 5 requêtes 0.5-DP → {composition([0.5]*5)}-DP au total (la fuite s'additionne).")
    # utilité : erreur typique = √2·b
    for eps in (0.1, 1.0, 5.0):
        print(f"   ε={eps}: bruit b={echelle_bruit(1.0,eps):.2f}, erreur-type ≈ {math.sqrt(2)*echelle_bruit(1.0,eps):.2f}")
