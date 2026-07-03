"""
PALIER 2 — BIAIS DE LONGUEUR / PARADOXE D'INSPECTION & D'AMITIÉ : « la moyenne que j'échantillonne = la moyenne de la
population » est sur-confiant (brique 102, 2026-06-27).

Quand on échantillonne un élément avec une probabilité PROPORTIONNELLE à sa taille, les GRANDS éléments sont
sur-représentés. La moyenne observée n'est PAS la moyenne de la population μ, mais
    μ_biaisée = E[X²]/E[X] = μ + σ²/μ ≥ μ,
strictement supérieure dès que la variance est non nulle. Trois visages du même biais :
  • INSPECTION / TEMPS D'ATTENTE : un instant tiré au hasard tombe plus souvent dans un LONG intervalle → l'intervalle où
    l'on se trouve est plus long que l'intervalle moyen (« le bus met plus longtemps que la moyenne annoncée »).
  • AMITIÉ : un voisin tiré au hasard a un degré moyen E[D²]/E[D] ≥ E[D] → « vos amis ont en moyenne plus d'amis que
    vous ».
  • TAILLE DE CLASSE / d'entreprise : l'étudiant moyen voit une classe plus grande que la taille moyenne des classes.

LA CORRECTION : pondérer par 1/taille. La moyenne HARMONIQUE de l'échantillon biaisé en taille récupère μ :
    1 / E_biaisé[1/X] = μ  (densité biaisée g(x)=x·f(x)/μ ⇒ E_g[1/X]=1/μ).

LE MODE D'ÉCHEC DÉMASQUÉ : prendre la moyenne arithmétique d'un échantillon biaisé en taille est SUR-confiant (sur-estime
μ de σ²/μ) ; la correction harmonique la rétablit. Distinct de echantillon_pondere (28, Horvitz-Thompson général avec π
connus) et de biais_survie (85, observations MANQUANTES). ABSTENTION si données insuffisantes. Pur Python, rng seedé.
"""
from __future__ import annotations

ABSTENTION = "abstention"
ANALYSE = "analyse"


def moyenne(xs):
    return sum(xs) / len(xs)


def variance(xs):
    m = moyenne(xs)
    return sum((x - m) ** 2 for x in xs) / len(xs)


def moyenne_biaisee_taille(tailles):
    """Moyenne d'un échantillon biaisé en taille = E[X²]/E[X] = μ + σ²/μ (valeur exacte sur la population)."""
    s = sum(tailles)
    return sum(x * x for x in tailles) / s if s else 0.0


def echantillonne_biais_taille(tailles, n, rng):
    """Tire n éléments avec probabilité ∝ taille (échantillonnage biaisé en longueur)."""
    total = sum(tailles)
    seuils = []
    cum = 0.0
    for x in tailles:
        cum += x
        seuils.append(cum)
    out = []
    for _ in range(n):
        r = rng.random() * total
        for i, s in enumerate(seuils):
            if r <= s:
                out.append(tailles[i])
                break
    return out


def correction_harmonique(echantillon):
    """Récupère μ depuis un échantillon biaisé en taille : μ = 1 / moyenne(1/x)."""
    return 1.0 / moyenne([1.0 / x for x in echantillon])


# ─────────────────────────── paradoxe d'amitié ───────────────────────────
def degre_moyen(graphe):
    """E[D] sur un graphe (dict sommet → liste de voisins)."""
    return moyenne([len(v) for v in graphe.values()])


def degre_voisin_moyen(graphe):
    """Degré moyen d'un VOISIN tiré au hasard = degré d'une extrémité d'arête tirée au hasard = E[D²]/E[D]
    = (Σ dᵢ²)/(Σ dᵢ) ≥ E[D] (paradoxe d'amitié ; égalité ssi graphe régulier)."""
    degres = [len(v) for v in graphe.values()]
    den = sum(degres)
    return sum(d * d for d in degres) / den if den else 0.0


def analyse(tailles):
    """Façade : moyenne vraie vs moyenne biaisée en taille, écart σ²/μ, correction harmonique.
    (ANALYSE, {mu, mu_biaisee, ecart, ...}) ou (ABSTENTION, raison)."""
    if len(tailles) < 3 or any(x <= 0 for x in tailles):
        return (ABSTENTION, "données insuffisantes / tailles ≤ 0")
    mu = moyenne(tailles)
    mb = moyenne_biaisee_taille(tailles)
    return (ANALYSE, {"mu": mu, "mu_biaisee": mb, "ecart": mb - mu, "ecart_theorique": variance(tailles) / mu})


def formule(res) -> str:
    if res[0] == ABSTENTION:
        return f"Pas d'analyse : {res[1]}."
    i = res[1]
    return (f"Moyenne réelle μ={i['mu']:.2f} ; moyenne d'un échantillon biaisé en taille = {i['mu_biaisee']:.2f} "
            f"(= μ + σ²/μ, écart +{i['ecart']:.2f}). Croire que l'échantillon biaisé reflète la population serait "
            f"sur-confiant — les grands éléments sont sur-représentés ; corriger par la moyenne harmonique.")


if __name__ == "__main__":
    import random
    rng = random.Random(0)
    tailles = [1, 1, 2, 3, 5, 8, 13, 21, 50, 100]
    print("=== BIAIS DE LONGUEUR / PARADOXE D'INSPECTION ===\n")
    st, info = analyse(tailles)
    ech = echantillonne_biais_taille(tailles, 200000, rng)
    print(f"  μ réel={info['mu']:.2f} ; biaisé théorie={info['mu_biaisee']:.2f} ; biaisé simulé={moyenne(ech):.2f}")
    print(f"  correction harmonique de l'échantillon biaisé = {correction_harmonique(ech):.2f} (≈ μ)")
    print(" ", formule((st, info)))
    # paradoxe d'amitié : chemin 1-2-3-4 (degrés 1,2,2,1)
    g = {1: [2], 2: [1, 3], 3: [2, 4], 4: [3]}
    print(f"\n  amitié : degré moyen={degre_moyen(g):.2f} ; degré moyen d'un voisin={degre_voisin_moyen(g):.2f} (≥)")
