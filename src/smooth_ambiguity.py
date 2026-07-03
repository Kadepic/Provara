"""
PALIER 2 — AMBIGUÏTÉ LISSE (smooth ambiguity, Klibanoff-Marinacci-Mukerji 2005) : séparer le RISQUE de
l'AMBIGUÏTÉ (brique 61, 2026-06-26).

Le maxmin [[decision_ambiguite]] est une aversion à l'ambiguïté EXTRÊME (on ne regarde que le pire prior). Le modèle
LISSE de KMM la rend graduelle via un prior de SECOND ORDRE μ (croyance sur quel prior P est le bon) et une fonction
φ d'attitude face à l'ambiguïté :
    V(f) = Σ_j μ_j · φ( E_{P_j}[u(f)] )
  • u = utilité des conséquences → attitude au RISQUE (premier ordre).
  • φ = utilité de second ordre → attitude à l'AMBIGUÏTÉ. φ CONCAVE = aversion ; φ LINÉAIRE = neutralité ; convexe = goût.

DEUX FAITS CLÉS :
  • φ LINÉAIRE ⇒ V(f) = E_μ[E_P[u(f)]] = espérance sous le prior RÉDUIT P̄=Σμ_j P_j = utilité espérée classique
    (l'ambiguïté est INVISIBLE).
  • φ CONCAVE ⇒ par Jensen, un acte dont l'utilité espérée VARIE selon le prior est PÉNALISÉ (prime d'ambiguïté).
    Limite φ infiniment concave (CARA λ→∞) → maxmin (pont vers brique 60).

LE MODE D'ÉCHEC DÉMASQUÉ : traiter l'ambiguïté COMME du risque (réduire μ à un seul prior P̄ et appliquer l'EU) est
SUR-CONFIANT — aveugle à l'étalement de E_P sur les priors plausibles (incertitude de modèle). Deux actes de MÊME
espérance réduite mais d'ambiguïté différente sont jugés ÉGAUX par l'EU ; un φ concave préfère STRICTEMENT le moins
ambigu. Reproduit Ellsberg. ABSTENTION si μ ne somme pas à 1 / actes vides. Pur Python.
"""
from __future__ import annotations

import math

ROBUSTE = "robuste"
ABSTENTION = "abstention"


def eu(P, act):
    return sum(P[s] * act[s] for s in act)


def phi_lineaire(x):
    return x


def phi_cara(lam):
    """Utilité de 2ᵉ ordre CARA φ(x) = −e^{−λx} (λ>0 ⇒ CONCAVE ⇒ aversion à l'ambiguïté ; λ=aversion)."""
    return lambda x: -math.exp(-lam * x)


def prior_reduit(priors, mu):
    """Prior de 1ᵉ ordre réduit P̄ = Σ_j μ_j P_j (ce que l'EU « ambiguïté-neutre » utilise)."""
    etats = priors[0].keys()
    return {s: sum(mu[j] * priors[j][s] for j in range(len(priors))) for s in etats}


def valeur(priors, mu, act, phi):
    """Critère lisse V(f) = Σ_j μ_j φ(E_{P_j}[act])."""
    return sum(mu[j] * phi(eu(priors[j], act)) for j in range(len(priors)))


def eu_reduit(priors, mu, act):
    """Valeur ambiguïté-NEUTRE = E_{P̄}[act] = Σ_j μ_j E_{P_j}[act] (= V avec φ linéaire)."""
    return sum(mu[j] * eu(priors[j], act) for j in range(len(priors)))


def equiv_certain_cara(priors, mu, act, lam):
    """Équivalent certain sous CARA λ : CE = −(1/λ)·ln Σ_j μ_j e^{−λ E_{P_j}[act]} (stable, log-sum-exp).
    → E_réduit quand λ→0 ; → min_j E_{P_j} (maxmin) quand λ→∞."""
    es = [eu(priors[j], act) for j in range(len(priors))]
    mn = min(es)
    s = sum(mu[j] * math.exp(-lam * (es[j] - mn)) for j in range(len(priors)))
    return mn - math.log(s) / lam


def choisir(priors, mu, acts, phi=None, lam=None):
    """Choisit l'acte de valeur lisse maximale. φ explicite OU lam (CARA via équivalent certain, stable).
    Renvoie (ROBUSTE, action*, table) ou (ABSTENTION, None, raison)."""
    if not priors or not acts:
        return (ABSTENTION, None, "priors ou actes vides")
    if abs(sum(mu) - 1.0) > 1e-9:
        return (ABSTENTION, None, "μ (2ᵉ ordre) ne somme pas à 1")
    if lam is not None:
        table = {a: equiv_certain_cara(priors, mu, u, lam) for a, u in acts.items()}
    else:
        phi = phi or phi_lineaire
        table = {a: valeur(priors, mu, u, phi) for a, u in acts.items()}
    best = max(table, key=table.get)
    return (ROBUSTE, best, table)


def formule(res, neutre=False) -> str:
    if res[0] == ABSTENTION:
        return f"Je ne peux pas décider : {res[2]}."
    best, table = res[1], res[2]
    mode = "ambiguïté-neutre (EU)" if neutre else "ambiguïté-averse (φ concave)"
    return (f"Décision {mode} : « {best} ». Réduire l'ambiguïté à un seul prior (EU) ignorerait l'étalement des "
            f"espérances entre priors plausibles — sur-confiant si les actes diffèrent en ambiguïté.")


if __name__ == "__main__":
    print("=== AMBIGUÏTÉ LISSE (KMM) — séparer risque et ambiguïté ===\n")
    priors = [{"s1": 0.8, "s2": 0.2}, {"s1": 0.2, "s2": 0.8}]   # 2 priors plausibles
    mu = [0.5, 0.5]
    sur = {"s1": 1.0, "s2": 1.0}    # acte SÛR (E_P=1 quel que soit P) : pas d'ambiguïté
    amb = {"s1": 2.0, "s2": 0.0}    # acte AMBIGU : E_P ∈ {1.6, 0.4}, même moyenne réduite 1.0
    print(f"  E_réduit(sûr)={eu_reduit(priors,mu,sur):.2f} = E_réduit(ambigu)={eu_reduit(priors,mu,amb):.2f} → EU INDIFFÉRENT")
    for lam in (0.01, 1.0, 5.0):
        vs = equiv_certain_cara(priors, mu, sur, lam); va = equiv_certain_cara(priors, mu, amb, lam)
        print(f"   λ={lam:>4}: CE(sûr)={vs:.3f}  CE(ambigu)={va:.3f}  → préfère {'sûr' if vs>va else 'ambigu'}")
    print(" ", formule(choisir(priors, mu, {"sûr": sur, "ambigu": amb}, lam=2.0)))
