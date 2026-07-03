"""
PALIER 2 — INTÉGRALE DE CHOQUET & MESURES NON-ADDITIVES (capacités) : agréger/espérer sans supposer l'additivité
(brique 55, 2026-06-26).

Une CAPACITÉ (mesure floue) μ sur un ensemble Ω vérifie μ(∅)=0, μ(Ω)=1, et la MONOTONIE (A⊆B ⇒ μ(A)≤μ(B)) — mais
PAS l'additivité. La non-additivité encode l'INTERACTION : μ super-additive (μ(A∪B) > μ(A)+μ(B)) = synergie /
complémentarité ; sous-additive = redondance. L'INTÉGRALE DE CHOQUET agrège un vecteur de scores x w.r.t. μ :
    C_μ(x) = Σ_i x_{(i)} · [ μ(A_{(i)}) − μ(A_{(i+1)}) ]    (x_{(1)} ≤ … ≤ x_{(n)}, A_{(i)} = {(i),…,(n)})
Si μ est additive, C_μ = moyenne arithmétique pondérée.

LE LIEN AVEC LA CALIBRATION (T2) : une fonction de CROYANCE ν (Dempster-Shafer, [[croyance_dempster_shafer]]) est une
capacité 2-monotone. Son crédal M(ν) = {P : P(A) ≥ ν(A) ∀A} est une FAMILLE de probabilités. Théorème (Schmeidler) :
    C_ν(x) = min_{P∈M(ν)} E_P[x]     (espérance INFÉRIEURE / lower prevision de Walley)
    C_ν̄(x) = max_{P∈M(ν)} E_P[x]     (ν̄ = capacité conjuguée = plausibilité)
Donc [C_ν(x), C_ν̄(x)] ENCADRE l'espérance vraie pour TOUT P compatible.

LE MODE D'ÉCHEC DÉMASQUÉ : s'engager sur UN prior additif (le « centre ») et annoncer son espérance ponctuelle est
SUR-CONFIANT — la vraie espérance peut être n'importe où dans [C_ν, C_ν̄]. La réponse honnête est l'encadrement de
Choquet. ABSTENTION si la capacité n'est pas valide (non monotone / μ(Ω)≠1). Pur Python.
"""
from __future__ import annotations

import itertools

import croyance_dempster_shafer as _DS

ABSTENTION = "abstention"
VALEUR = "valeur"


def capacite_additive(poids):
    """Capacité ADDITIVE μ(A)=Σ_{i∈A} poids[i] (poids ≥ 0 sommant à 1). Choquet → moyenne pondérée."""
    return lambda A: sum(poids[i] for i in A)


def capacite_croyance(masse):
    """Capacité = fonction de CROYANCE ν(A)=Bel(A) issue d'une masse de Dempster-Shafer (2-monotone)."""
    return lambda A: _DS.belief(masse, A)


def conjuguee(mu, omega):
    """Capacité conjuguée μ̄(A) = 1 − μ(Ω∖A). (croyance → plausibilité). Donne l'espérance SUPÉRIEURE."""
    omega = frozenset(omega)
    return lambda A: 1.0 - mu(omega - frozenset(A))


def choquet(mu, x):
    """Intégrale de Choquet de x (dict label→score) w.r.t. la capacité μ (callable frozenset→[0,1])."""
    labels = sorted(x, key=lambda k: x[k])      # ascendant
    n = len(labels)
    total = 0.0
    for i in range(n):
        A_i = frozenset(labels[i:])              # {(i),…,(n)}
        A_next = frozenset(labels[i + 1:])
        total += x[labels[i]] * (mu(A_i) - mu(A_next))
    return total


def est_capacite(mu, omega, tol=1e-9):
    """Valide : μ(∅)=0, μ(Ω)=1, monotonie sur tous les sous-ensembles (Ω petit)."""
    omega = list(omega)
    if abs(mu(frozenset())) > tol or abs(mu(frozenset(omega)) - 1.0) > tol:
        return False
    subsets = []
    for r in range(len(omega) + 1):
        subsets += [frozenset(c) for c in itertools.combinations(omega, r)]
    for A in subsets:
        for B in subsets:
            if A <= B and mu(A) > mu(B) + tol:
                return False
    return True


def encadre_esperance(masse, x):
    """Façade : encadre E[x] par Choquet inférieur/supérieur d'une fonction de croyance. Renvoie
    (VALEUR, (inf, sup)) ou (ABSTENTION, raison). [inf,sup] contient E_P[x] pour tout P du crédal."""
    omega = frozenset(x)
    nu = capacite_croyance(masse)
    try:
        if not est_capacite(nu, omega):
            return (ABSTENTION, "la masse ne définit pas une capacité valide sur ces labels")
        inf = choquet(nu, x)
        sup = choquet(conjuguee(nu, omega), x)
    except ValueError as e:
        return (ABSTENTION, f"masse invalide : {e}")
    return (VALEUR, (inf, sup))


def formule(res) -> str:
    if res[0] == ABSTENTION:
        return f"Je ne peux pas encadrer l'espérance : {res[1]}."
    inf, sup = res[1]
    return (f"Espérance encadrée dans [{inf:.3f}, {sup:.3f}] (Choquet inférieur/supérieur d'une croyance). "
            f"S'engager sur un seul prior donnerait un point précis mais SUR-confiant.")


if __name__ == "__main__":
    print("=== INTÉGRALE DE CHOQUET — interaction & espérance imprécise ===\n")
    # Synergie : il faut LES DEUX critères (super-additif)
    syn = lambda A: {frozenset(): 0.0, frozenset({"a"}): 0.1, frozenset({"b"}): 0.1, frozenset({"a", "b"}): 1.0}[frozenset(A)]
    print("  Capacité SYNERGIE μ(a)=μ(b)=0.1, μ(ab)=1 (super-additive) :")
    print(f"   Choquet(a=1,b=0)={choquet(syn, {'a':1,'b':0}):.2f}  Choquet(a=1,b=1)={choquet(syn, {'a':1,'b':1}):.2f}  (il faut les deux)")
    add = capacite_additive({"a": 0.5, "b": 0.5})
    print(f"  Capacité ADDITIVE 0.5/0.5 → Choquet(2,4)={choquet(add, {'a':2,'b':4}):.2f} (= moyenne pondérée 3.0)\n")
    masse = {("a",): 0.3, ("b",): 0.2, ("a", "b"): 0.5}   # 0.5 d'ignorance sur {a,b}
    print(" ", formule(encadre_esperance(masse, {"a": 0.0, "b": 1.0})))
