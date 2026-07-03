"""
PALIER 2 — DÉCISION SOUS AMBIGUÏTÉ : choisir quand on a un CRÉDAL de probabilités, pas une seule (brique 60,
2026-06-26).

Quand l'incertitude est imprécise (crédal M = ensemble de probabilités, cf. [[prevision_walley]]/[[croyance_dempster_shafer]]),
l'utilité espérée classique sous UNE proba ne suffit plus. Plusieurs critères rationnels :
  • MAXMIN EU (Gilboa-Schmeidler / Wald) : maximiser le PIRE-CAS sur M.  a* = argmax_a min_{P∈M} E_P[u_a].
    (= maximiser la prévision INFÉRIEURE P̲(u_a) — pont direct vers Walley/Choquet.) Aversion à l'ambiguïté.
  • MAXMAX EU : optimiste (max sur M).
  • α-MAXMIN (Hurwicz) : α·min + (1−α)·max, α = degré d'aversion à l'ambiguïté (α=1 maxmin, α=0 maxmax).
  • REGRET MINIMAX (Savage) : minimiser le pire regret max_{P∈M}( max_b E_P[u_b] − E_P[u_a] ).

LE MODE D'ÉCHEC DÉMASQUÉ : optimiser l'utilité espérée sous UNE proba précise (le « centre » du crédal) IGNORE
l'ambiguïté → l'acte choisi peut être FRAGILE : son pire-cas est strictement pire que celui de l'acte maxmin. Croire
que sa performance prédite est garantie = SUR-CONFIANT. Le maxmin offre un PLANCHER garanti (jamais violé). Le
paradoxe d'ELLSBERG (préférer le connu à l'ambigu) est rationalisé par maxmin mais INCOMPATIBLE avec toute proba
unique. ABSTENTION si crédal ou actes vides. Pur Python.
"""
from __future__ import annotations

ROBUSTE = "robuste"
ABSTENTION = "abstention"


def eu(P, u):
    """Utilité espérée E_P[u] (u dict état→utilité)."""
    return sum(P[s] * u[s] for s in u)


def valeur_maxmin(credal, u):
    """min_{P∈M} E_P[u] = prévision inférieure de l'acte (pire-cas, atteint à un sommet)."""
    return min(eu(P, u) for P in credal)


def valeur_maxmax(credal, u):
    return max(eu(P, u) for P in credal)


def valeur_hurwicz(credal, u, alpha):
    """α·pire + (1−α)·meilleur (α = aversion à l'ambiguïté ∈ [0,1])."""
    return alpha * valeur_maxmin(credal, u) + (1 - alpha) * valeur_maxmax(credal, u)


def regret_pire(credal, acts, a):
    """Pire regret de l'acte a : max_{P∈M} (max_b E_P[u_b] − E_P[u_a]) (atteint à un sommet)."""
    return max(max(eu(P, u) for u in acts.values()) - eu(P, acts[a]) for P in credal)


def choisir(credal, acts, critere="maxmin", alpha=1.0):
    """Choisit un acte selon le critère. Renvoie (ROBUSTE, action*, table) ou (ABSTENTION, None, raison).
    `critere` ∈ {maxmin, maxmax, hurwicz, regret_minimax}. table = {action: score}."""
    if not credal or not acts:
        return (ABSTENTION, None, "crédal ou actes vides")
    if critere == "maxmin":
        table = {a: valeur_maxmin(credal, u) for a, u in acts.items()}
        best = max(table, key=table.get)
    elif critere == "maxmax":
        table = {a: valeur_maxmax(credal, u) for a, u in acts.items()}
        best = max(table, key=table.get)
    elif critere == "hurwicz":
        table = {a: valeur_hurwicz(credal, u, alpha) for a, u in acts.items()}
        best = max(table, key=table.get)
    elif critere == "regret_minimax":
        table = {a: regret_pire(credal, acts, a) for a in acts}
        best = min(table, key=table.get)
    else:
        return (ABSTENTION, None, f"critère inconnu : {critere}")
    return (ROBUSTE, best, table)


def e_admissibles(credal, acts):
    """Actes E-ADMISSIBLES (Walley) : optimaux (max EU) pour AU MOINS une proba (sommet) du crédal."""
    adm = set()
    for P in credal:
        vals = {a: eu(P, u) for a, u in acts.items()}
        mx = max(vals.values())
        adm |= {a for a, v in vals.items() if v >= mx - 1e-12}
    return adm


def domine(credal, acts, a, b):
    """a est DOMINÉ par b si E_P[u_b] > E_P[u_a] pour tout P∈M (strictement)."""
    return all(eu(P, acts[b]) > eu(P, acts[a]) + 1e-12 for P in credal)


def maximaux(credal, acts):
    """Actes MAXIMAUX : non dominés par aucun autre acte."""
    return {a for a in acts if not any(domine(credal, acts, a, b) for b in acts if b != a)}


def formule(res, critere="maxmin") -> str:
    if res[0] == ABSTENTION:
        return f"Je ne peux pas décider : {res[2]}."
    best, table = res[1], res[2]
    return (f"Décision ({critere}) : « {best} » (score {table[best]:.3f}). Optimiser l'utilité espérée sous une seule "
            f"proba ignorerait l'ambiguïté — un acte au meilleur prédit peut avoir un pire-cas inférieur.")


if __name__ == "__main__":
    print("=== DÉCISION SOUS AMBIGUÏTÉ — paradoxe d'Ellsberg ===\n")
    # Urne : 30 R sur 90 ; 60 B-ou-Y en proportion INCONNUE. Crédal = bornes sur P(B).
    credal = [{"R": 1/3, "B": 0.0, "Y": 2/3}, {"R": 1/3, "B": 2/3, "Y": 0.0}]
    acts = {"A_parie_R": {"R": 1, "B": 0, "Y": 0}, "B_parie_B": {"R": 0, "B": 1, "Y": 0},
            "C_R_ou_Y": {"R": 1, "B": 0, "Y": 1}, "D_B_ou_Y": {"R": 0, "B": 1, "Y": 1}}
    for a, u in acts.items():
        print(f"   {a}: maxmin={valeur_maxmin(credal,u):.3f}")
    print(f"\n   maxmin préfère A(R) à B(B) : {valeur_maxmin(credal,acts['A_parie_R']) > valeur_maxmin(credal,acts['B_parie_B'])}")
    print(f"   maxmin préfère D(B∨Y) à C(R∨Y) : {valeur_maxmin(credal,acts['D_B_ou_Y']) > valeur_maxmin(credal,acts['C_R_ou_Y'])}")
    print("   → A≻B et D≻C = pattern d'Ellsberg, INCOMPATIBLE avec toute proba unique.")
    print(" ", formule(choisir(credal, acts, "maxmin"), "maxmin"))
