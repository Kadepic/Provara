"""
PALIER 2 — THÉORIE DES POSSIBILITÉS (Zadeh ; Dubois & Prade) : encadrer une probabilité inconnue sans inventer de
précision (brique 51, 2026-06-26).

Paradigme « hors-calibration » (incertitude NON-ADDITIVE, frère consonant de Dempster-Shafer [[croyance_dempster_shafer]]).
Une distribution de POSSIBILITÉ π : Θ → [0,1] (avec sup π = 1, condition de normalisation) encode une connaissance
imprécise (avis d'expert, ensemble flou, intervalle de confiance emboîté). Elle induit DEUX mesures duales :
  • POSSIBILITÉ   Π(A) = sup_{x∈A} π(x)        — « à quel point A est-il PLAUSIBLE » (preuve qui n'exclut pas A)
  • NÉCESSITÉ     N(A) = 1 − Π(Aᶜ)             — « à quel point A est-il CERTAIN »   (preuve qui force A)
Propriétés : N(A) ≤ Π(A) ; Π est MAX-additive (Π(A∪B)=max(Π(A),Π(B)), PAS une somme) ; N(A)>0 ⇒ Π(A)=1.

LE THÉORÈME QUI FAIT LA CALIBRATION (Dubois-Prade) : π domine une FAMILLE de probabilités ; pour TOUTE proba P
compatible et TOUT événement A,  N(A) ≤ P(A) ≤ Π(A).  Donc [N(A), Π(A)] est un ENCADREMENT GARANTI de la vraie
probabilité — la réponse honnête est cet intervalle, pas un point.

LE MODE D'ÉCHEC DÉMASQUÉ : lire « Π(A) » COMME une probabilité (Π(A)=1 pour plusieurs A disjoints → on assertait la
certitude de plusieurs événements incompatibles). Utiliser Π(A) comme prévision de probabilité SUR-CONFIE
systématiquement (puisque P(A) ≤ Π(A), annoncer Π(A) sur-estime) ; symétriquement N(A) SOUS-confie. Seul l'intervalle
[N, Π] reste calibré. ABSTENTION si π n'est pas normalisée (sup π < 1 : information sous-normalisée/contradictoire).
Pur Python.
"""
from __future__ import annotations

ABSTENTION = "abstention"
MESURE = "mesure"
_TOL = 1e-9


def normalisee(pi) -> bool:
    """π est-elle normalisée (sup π = 1) ? Sinon l'information est sous-normalisée (partiellement contradictoire)."""
    return bool(pi) and abs(max(pi.values()) - 1.0) <= 1e-9


def possibilite(pi, A) -> float:
    """Π(A) = sup_{x∈A} π(x). Mesure MAX-additive (plausibilité de A)."""
    A = set(A)
    return max((pi[x] for x in A if x in pi), default=0.0)


def necessite(pi, A) -> float:
    """N(A) = 1 − Π(Aᶜ) = inf_{x∉A} (1 − π(x)). Certitude de A. N(A) ≤ Π(A)."""
    A = set(A)
    comp = [pi[x] for x in pi if x not in A]
    return 1.0 - (max(comp) if comp else 0.0)


def intervalle_proba(pi, A):
    """Encadrement GARANTI [N(A), Π(A)] de P(A) pour toute probabilité compatible avec π (théorème de Dubois-Prade).
    Sa largeur = l'imprécision assumée ; une proba ponctuelle l'écraserait (fausse précision)."""
    return (necessite(pi, A), possibilite(pi, A))


def domine(pi, P, tol=1e-9) -> bool:
    """P (proba, dict x→p) est-elle DOMINÉE par π, i.e. P(A) ≤ Π(A) pour TOUT A ⊆ support ? (appartenance au crédal).
    Vérifié sur tous les sous-ensembles (usage : petits Θ). Équivaut à : cumul des p triés ≤ π emboîtés."""
    xs = list(pi.keys())
    n = len(xs)
    for masque in range(1, 1 << n):
        A = [xs[i] for i in range(n) if masque & (1 << i)]
        pa = sum(P.get(x, 0.0) for x in A)
        if pa > possibilite(pi, A) + tol:
            return False
    return True


def depuis_emboitees(niveaux):
    """Construit une π CONSONANTE depuis une famille d'ensembles de confiance EMBOÎTÉS : `niveaux` = liste de
    (confiance c, ensemble S) triée par S croissant, S₁⊆S₂⊆… Chaque x reçoit π(x) = 1 − c du PLUS PETIT S qui le
    contient (1 hors de tous). C'est le pont statistique standard π(x)=inf{1−c : x∈S_c} (la π domine la vraie loi)."""
    pi = {}
    for c, S in sorted(niveaux, key=lambda t: len(t[1])):
        for x in S:
            if x not in pi:
                pi[x] = max(0.0, 1.0 - c)
    return pi


def encadre(pi, A):
    """Façade : (MESURE, (N, Π), π_normalisée?) ou (ABSTENTION, None, raison)."""
    if not normalisee(pi):
        s = max(pi.values()) if pi else 0.0
        return (ABSTENTION, None, f"π non normalisée (sup π = {s:.3f} < 1) : information sous-normalisée")
    return (MESURE, intervalle_proba(pi, A), True)


def formule(res, nom_A="l'événement") -> str:
    if res[0] == ABSTENTION:
        return f"Je ne peux pas encadrer la probabilité : {res[2]}."
    N, Pi = res[1]
    return (f"P({nom_A}) est encadrée dans [{N:.3f}, {Pi:.3f}] : nécessité {N:.3f} (certitude), possibilité {Pi:.3f} "
            f"(plausibilité). Je ne peux pas être plus précis — lire la possibilité {Pi:.3f} comme une probabilité "
            f"serait sur-confiant.")


if __name__ == "__main__":
    print("=== THÉORIE DES POSSIBILITÉS — encadrer sans inventer de précision ===\n")
    # Deux causes pleinement possibles, trois marginales
    pi = {"a": 1.0, "b": 1.0, "c": 0.2, "d": 0.2, "e": 0.1}
    print(f"  π = {pi}  (normalisée: {normalisee(pi)})")
    for A in [["a"], ["a", "b"], ["c", "d", "e"]]:
        N, Pi = intervalle_proba(pi, A)
        print(f"   A={A}: N={N:.2f} ≤ P(A) ≤ Π={Pi:.2f}")
    print("\n  Max-additivité : Π({a,b}) =", possibilite(pi, ["a", "b"]),
          "= max(Π(a),Π(b)) (PAS Π(a)+Π(b)=2, ce qui serait incohérent en proba).")
    print(" ", formule(encadre(pi, ["a"]), "cause = a"))
    print("\n  π depuis ensembles emboîtés de confiance (cœur à c=0 → π=1) :",
          depuis_emboitees([(0.0, {"x"}), (0.9, {"x", "y", "z"})]))
