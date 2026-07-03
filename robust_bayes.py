"""
PALIER 2 — BAYES ROBUSTE par ε-CONTAMINATION (Berger) : ne pas faire semblant de connaître le prior exactement
(brique 56, 2026-06-26).

Le bayésien standard s'engage sur UN prior π₀. Mais π₀ est rarement connu avec certitude. Le modèle d'ε-CONTAMINATION
remplace π₀ par une CLASSE de priors :
    Γ = { (1−ε)·π₀ + ε·q  :  q prior ARBITRAIRE }        (ε = part d'ignorance sur le prior, ex. 0.1–0.2)
La quantité a posteriori (moyenne de g(θ), ou probabilité d'un événement) n'est alors plus un point mais un
INTERVALLE [inf, sup] sur Γ.

FORME CLOSE EXACTE : la moyenne a posteriori est une fonction LINÉAIRE-FRACTIONNAIRE de q (numérateur et dénominateur
affines en q) ; sur le simplexe des priors, ses extrêmes sont atteints aux SOMMETS = masses de Dirac δ_θ. Donc
    r(θ) = [ (1−ε)·a + ε·g(θ)L(θ) ] / [ (1−ε)·b + ε·L(θ) ],   a=Σg(θ)L(θ)π₀(θ),  b=ΣL(θ)π₀(θ)
    inf = min_θ r(θ),  sup = max_θ r(θ).
[inf, sup] contient la moyenne a posteriori pour TOUT prior de Γ.

LE MODE D'ÉCHEC DÉMASQUÉ : rapporter le seul posterior de π₀ (a/b) est SUR-CONFIANT — il suppose le prior connu
exactement. La réponse honnête est l'intervalle. Vertu : quand les DONNÉES sont informatives (vraisemblance piquée),
l'intervalle RÉTRÉCIT même à ε fixé — l'évidence achète la robustesse. ABSTENTION si ε∉[0,1] ou vraisemblance nulle
partout. Pur Python.
"""
from __future__ import annotations

ABSTENTION = "abstention"
INTERVALLE = "intervalle"


def indicatrice(evenement, thetas):
    """g = fonction indicatrice d'un événement A ⊆ Θ (pour la PROBABILITÉ a posteriori de A)."""
    A = set(evenement)
    return {t: (1.0 if t in A else 0.0) for t in thetas}


def posterieur_contamine(prior0, vrais, g, eps):
    """Intervalle [inf, sup] de la moyenne a posteriori de g sous la classe d'ε-contamination de π₀.
    prior0, vrais (vraisemblance L), g : dicts θ→valeur. Renvoie (inf, sup) ou None si vraisemblance nulle."""
    thetas = list(prior0)
    a = sum(g[t] * vrais[t] * prior0[t] for t in thetas)
    b = sum(vrais[t] * prior0[t] for t in thetas)
    if b <= 0.0:
        return None
    if eps <= 0.0:
        v = a / b
        return (v, v)
    rs = [((1 - eps) * a + eps * g[t] * vrais[t]) / ((1 - eps) * b + eps * vrais[t]) for t in thetas]
    return (min(rs), max(rs))


def posterieur_nominal(prior0, vrais, g):
    """Moyenne a posteriori sous π₀ SEUL (le point sur-confiant). a/b."""
    thetas = list(prior0)
    b = sum(vrais[t] * prior0[t] for t in thetas)
    if b <= 0.0:
        return None
    return sum(g[t] * vrais[t] * prior0[t] for t in thetas) / b


def estime(prior0, vrais, g, eps=0.1):
    """Façade : (INTERVALLE, (inf, sup), nominal) ou (ABSTENTION, None, raison)."""
    if not (0.0 <= eps <= 1.0):
        return (ABSTENTION, None, f"ε={eps} hors [0,1]")
    r = posterieur_contamine(prior0, vrais, g, eps)
    if r is None:
        return (ABSTENTION, None, "vraisemblance nulle sous π₀ (données impossibles)")
    return (INTERVALLE, r, posterieur_nominal(prior0, vrais, g))


def formule(res, quoi="la quantité") -> str:
    if res[0] == ABSTENTION:
        return f"Je ne peux pas estimer {quoi} : {res[2]}."
    (inf, sup), nom = res[1], res[2]
    return (f"A posteriori, {quoi} ∈ [{inf:.3f}, {sup:.3f}] (Bayes robuste, ε-contamination). Le posterior nominal "
            f"{nom:.3f} (prior unique) serait SUR-confiant — la largeur {sup-inf:.3f} reflète l'incertitude sur le prior.")


if __name__ == "__main__":
    print("=== BAYES ROBUSTE (ε-contamination) — l'incertitude sur le prior compte ===\n")
    thetas = ["H0", "H1", "H2"]
    prior0 = {"H0": 0.5, "H1": 0.3, "H2": 0.2}
    g = indicatrice(["H0"], thetas)   # proba a posteriori de H0
    print("  Probabilité a posteriori de H0 :")
    for L, lab in [({"H0": 0.6, "H1": 0.5, "H2": 0.4}, "données faibles"),
                   ({"H0": 0.9, "H1": 0.05, "H2": 0.01}, "données fortes (piquées)")]:
        for eps in (0.0, 0.2):
            inf, sup = posterieur_contamine(prior0, L, g, eps)
            print(f"   {lab:24s} ε={eps}: [{inf:.3f}, {sup:.3f}] (largeur {sup-inf:.3f})")
    print()
    print(" ", formule(estime(prior0, {"H0": 0.6, "H1": 0.5, "H2": 0.4}, g, 0.2), "P(H0)"))
