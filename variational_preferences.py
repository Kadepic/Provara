"""
PALIER 2 — PRÉFÉRENCES VARIATIONNELLES / MULTIPLIER (Hansen-Sargent ; Maccheroni-Marinacci-Rustichini) : robustesse
à la MAUVAISE SPÉCIFICATION d'un modèle de référence (brique 62, 2026-06-27).

On a un modèle de référence P₀ mais on ne le croit pas EXACT. Les préférences variationnelles évaluent un acte f par
    V(f) = min_P { E_P[u(f)] + c(P) }
où une « nature » adverse peut distordre P₀ en P, mais paie un coût c(P) (l'index d'ambiguïté). Cas MULTIPLIER
(Hansen-Sargent) : c(P) = θ·KL(P‖P₀), pénalité = entropie relative, θ>0 = paramètre de robustesse. (Cas maxmin
[[decision_ambiguite]] : c=0 sur un crédal, +∞ dehors → préférences variationnelles = généralisation commune.)

FORME CLOSE (dualité de Donsker-Varadhan / contrôle robuste) :
    min_P { E_P[X] + θ·KL(P‖P₀) } = −θ · ln E_{P₀}[ e^{−X/θ} ]
C'est le certain-équivalent ENTROPIQUE (exponentiel) ; la distribution adverse optimale est l'INCLINAISON
exponentielle P*(s) ∝ P₀(s)·e^{−u(s)/θ} (penche vers les MAUVAIS états). Limites : θ→∞ ⇒ E_{P₀}[u] (on fait
confiance au modèle) ; θ→0 ⇒ min_s u(s) (pire état, robustesse totale). (Même forme que la CARA de [[smooth_ambiguity]].)

LE MODE D'ÉCHEC DÉMASQUÉ : faire CONFIANCE au modèle de référence (utilité espérée sous P₀, θ→∞) est SUR-CONFIANT —
ça suppose P₀ exact. Si la réalité dévie (dans une boule d'entropie), l'acte EU peut être battu : sa valeur ROBUSTE
V_θ ≤ E_{P₀}[u] (prime de robustesse), et un adversaire dans le budget d'entropie le punit là où l'acte robuste tient.
ABSTENTION si θ ≤ 0 ou P₀ non normalisé. Pur Python.
"""
from __future__ import annotations

import math

ROBUSTE = "robuste"
ABSTENTION = "abstention"


def eu(P, u):
    return sum(P[s] * u[s] for s in u)


def kl(P, P0):
    """Entropie relative KL(P‖P₀) = Σ P(s) ln(P(s)/P₀(s)) (0·ln0=0 ; exige P₀(s)>0 là où P(s)>0)."""
    tot = 0.0
    for s in P:
        if P[s] > 0:
            tot += P[s] * math.log(P[s] / P0[s])
    return tot


def pire_distribution(P0, u, theta):
    """Distribution adverse optimale P*(s) ∝ P₀(s)·e^{−u(s)/θ} (incline vers les états de faible utilité)."""
    etats = list(u)
    log_w = [(-u[s] / theta) for s in etats]
    m = max(log_w)
    w = [P0[s] * math.exp(lw - m) for s, lw in zip(etats, log_w)]
    z = sum(w)
    return {s: wi / z for s, wi in zip(etats, w)}


def valeur_robuste(P0, u, theta):
    """V_θ(u) = −θ·ln E_{P₀}[e^{−u/θ}] (Hansen-Sargent, forme close stable)."""
    etats = list(u)
    log_t = [(-u[s] / theta) for s in etats]
    m = max(log_t)
    s = sum(P0[st] * math.exp(lt - m) for st, lt in zip(etats, log_t))
    return -theta * (m + math.log(s))


def valeur_directe(P0, u, theta):
    """Évalue min_P{E_P[u]+θKL} en utilisant la distribution adverse optimale (doit égaler valeur_robuste)."""
    Ps = pire_distribution(P0, u, theta)
    return eu(Ps, u) + theta * kl(Ps, P0)


def choisir(P0, acts, theta):
    """Choisit l'acte de valeur robuste maximale. (ROBUSTE, action*, table) ou (ABSTENTION, None, raison)."""
    if theta <= 0:
        return (ABSTENTION, None, "θ doit être > 0")
    if not P0 or not acts or abs(sum(P0.values()) - 1.0) > 1e-9:
        return (ABSTENTION, None, "P₀ vide/non normalisé ou actes vides")
    table = {a: valeur_robuste(P0, u, theta) for a, u in acts.items()}
    best = max(table, key=table.get)
    return (ROBUSTE, best, table)


def formule(res, theta) -> str:
    if res[0] == ABSTENTION:
        return f"Je ne peux pas décider : {res[2]}."
    best, table = res[1], res[2]
    return (f"Décision ROBUSTE (θ={theta}) : « {best} » (valeur {table[best]:.3f}). Faire pleinement confiance au "
            f"modèle de référence (utilité espérée) serait sur-confiant — la valeur robuste anticipe sa mauvaise spécification.")


if __name__ == "__main__":
    print("=== PRÉFÉRENCES VARIATIONNELLES / MULTIPLIER (Hansen-Sargent) ===\n")
    P0 = {"calme": 0.9, "crise": 0.1}     # modèle de référence : crise rare
    risque = {"calme": 2.0, "crise": -8.0}   # rentable en calme (EU=1.0), catastrophique en crise
    prudent = {"calme": 0.3, "crise": 0.3}   # acte plat (EU=0.3)
    print(f"  E_P0 : risqué={eu(P0,risque):.2f}, prudent={eu(P0,prudent):.2f} → EU choisit risqué")
    for theta in (100.0, 1.0, 0.3):
        vr = valeur_robuste(P0, risque, theta); vp = valeur_robuste(P0, prudent, theta)
        print(f"   θ={theta:>5}: V(risqué)={vr:.3f}  V(prudent)={vp:.3f}  → {'risqué' if vr>vp else 'prudent'}"
              f"  [pire-distrib crise={pire_distribution(P0,risque,theta)['crise']:.2f}]")
    print(" ", formule(choisir(P0, {"risqué": risque, "prudent": prudent}, 0.5), 0.5))
