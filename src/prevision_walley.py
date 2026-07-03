"""
PALIER 2 — PRÉVISIONS INFÉRIEURES / SUPÉRIEURES (Walley) : le cadre le plus général de la probabilité imprécise
(brique 58, 2026-06-26).

Une prévision INFÉRIEURE P̲(X) sur des « gambles » (fonctions bornées X:Ω→ℝ, des gains incertains) = le prix
d'ACHAT maximal qu'on accepte pour recevoir X. La prévision SUPÉRIEURE P̄(X) = prix de VENTE minimal. Conjugaison :
P̄(X) = −P̲(−X). Walley : une prévision inférieure est COHÉRENTE ⟺ c'est l'ENVELOPPE INFÉRIEURE d'un ensemble
convexe fermé de probabilités (le crédal M) : P̲(X) = min_{P∈M} E_P[X]. (Englobe Dempster-Shafer
[[croyance_dempster_shafer]], possibilités [[possibilite]], Choquet [[choquet]] comme cas particuliers.)

On représente M par ses SOMMETS (points extrêmes = vecteurs de probabilité). Alors P̲/P̄ = min/max d'une fonctionnelle
LINÉAIRE sur un polytope = min/max sur les sommets (exact, pur Python).

DEUX RATIONALITÉS, DEUX MODES D'ÉCHEC DÉMASQUÉS :
  • ÉVITER LA PERTE SÛRE (no Dutch book) : une cohérente vérifie min(X) ≤ P̲(X) ≤ max(X). Acheter X au prix p > max(X)
    garantit une perte (X−p < 0 dans TOUT état) = SUR-CONFIANCE punie par un pari hollandais. Démontré explicitement.
  • SUR-CONFIANCE PROBABILISTE : s'engager sur UNE proba précise (prévision linéaire P̲=P̄) annonce une espérance
    ponctuelle ; si le crédal est non-dégénéré, c'est sur-confiant — la réponse honnête est [P̲(X), P̄(X)].
ABSTENTION si le crédal est vide (aucune proba compatible). Pur Python.
"""
from __future__ import annotations

import itertools

import croyance_dempster_shafer as _DS

ABSTENTION = "abstention"
PREVISION = "prevision"


def _esp(P, X):
    return sum(P[w] * X[w] for w in X)


def lower(credal, X):
    """Prévision INFÉRIEURE P̲(X) = min_{P∈M} E_P[X] (envelope inférieure ; = extension naturelle de X)."""
    return min(_esp(P, X) for P in credal)


def upper(credal, X):
    """Prévision SUPÉRIEURE P̄(X) = max_{P∈M} E_P[X] = −P̲(−X) (conjuguée)."""
    return max(_esp(P, X) for P in credal)


def intervalle(credal, X):
    """[P̲(X), P̄(X)] : encadre E_P[X] pour toute proba du crédal."""
    return (lower(credal, X), upper(credal, X))


def perte_sure(X, prix):
    """Le pire gain net en achetant X au prix `prix` = max_ω (X(ω) − prix). < 0 ⇒ PERTE SÛRE (pari hollandais)."""
    return max(X[w] - prix for w in X)


def credal_depuis_croyance(masse, omega):
    """Sommets du crédal d'une fonction de CROYANCE : pour chaque permutation σ de Ω,
    P_σ(ω_{(i)}) = Bel({ω_{(1)},…,ω_{(i)}}) − Bel({ω_{(1)},…,ω_{(i-1)}}). (Englobe DS ; lower = intégrale de Choquet.)"""
    omega = list(omega)
    vues = set()
    credal = []
    for perm in itertools.permutations(omega):
        P, prec = {}, frozenset()
        bel_prec = 0.0
        for w in perm:
            cur = prec | {w}
            bel_cur = _DS.belief(masse, cur)
            P[w] = bel_cur - bel_prec
            prec, bel_prec = cur, bel_cur
        cle = tuple(round(P[w], 12) for w in omega)
        if cle not in vues:
            vues.add(cle)
            credal.append(P)
    return credal


def encadre_gamble(credal, X):
    """Façade : (PREVISION, (P̲, P̄)) ou (ABSTENTION, raison) si crédal vide."""
    if not credal:
        return (ABSTENTION, "crédal vide : aucune probabilité compatible (perte sûre)")
    return (PREVISION, intervalle(credal, X))


def formule(res, nom="ce gamble") -> str:
    if res[0] == ABSTENTION:
        return f"Je ne peux pas évaluer {nom} : {res[1]}."
    lo, hi = res[1]
    return (f"Prix d'achat/vente pour {nom} : P̲={lo:.3f}, P̄={hi:.3f}. L'espérance vraie est dans [{lo:.3f}, {hi:.3f}] ; "
            f"s'engager sur un seul prix précis serait sur-confiant.")


if __name__ == "__main__":
    print("=== PRÉVISIONS INFÉRIEURES/SUPÉRIEURES (Walley) ===\n")
    masse = {("p",): 0.3, ("f",): 0.2, ("p", "f"): 0.5}   # pile/face, 0.5 d'ignorance
    omega = ["p", "f"]
    credal = credal_depuis_croyance(masse, omega)
    print(f"  crédal (sommets) = {[{k: round(v,2) for k,v in P.items()} for P in credal]}")
    X = {"p": 1.0, "f": 0.0}   # gamble = 1€ si pile
    lo, hi = intervalle(credal, X)
    print(f"   gamble 'pile' : P̲={lo:.2f} (=Bel(pile)), P̄={hi:.2f} (=Pl(pile))")
    print(f"\n  Pari hollandais : acheter X=[1 si pile, 0 sinon] au prix 1.2 (> max X=1) :")
    print(f"   pire net = {perte_sure(X, 1.2):.2f} < 0 → PERTE SÛRE (sur-confiance punie).")
    print(" ", formule(encadre_gamble(credal, X), "miser sur pile"))
