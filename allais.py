"""
PALIER 2 — PARADOXE D'ALLAIS (violation de l'axiome d'indépendance) : supposer que les préférences obéissent à
l'utilité espérée est sur-confiant (brique 118, 2026-06-28).

Deux choix de loteries (gains en millions ; 0, 1, 5) :
  • Paire 1 : 1A = 1 M CERTAIN  vs  1B = (89 % : 1 M, 10 % : 5 M, 1 % : 0). La plupart préfèrent 1A (effet de CERTITUDE).
  • Paire 2 : 2A = (11 % : 1 M, 89 % : 0)  vs  2B = (10 % : 5 M, 90 % : 0). La plupart préfèrent 2B.
Or les deux paires partagent une CONSÉQUENCE COMMUNE (89 %) : 1A/1B = sous-choix + « 89 % de 1 M » ; 2A/2B = MÊME
sous-choix + « 89 % de 0 ». Par l'AXIOME D'INDÉPENDANCE, cette conséquence commune est sans effet ⇒ un agent à utilité
espérée choisit dans le MÊME sens aux deux paires. Le schéma d'Allais (1A≻1B ET 2B≻2A) est donc INCOHÉRENT avec TOUTE
fonction d'utilité : il impose à la fois 0.11·u(1M) > 0.10·u(5M)+0.01·u(0) et l'inverse — contradictoire.

L'effet de certitude (sur-pondération de la quasi-certitude) reproduit Allais sous une utilité à PONDÉRATION DE
PROBABILITÉ (rang-dépendante), modèle NON-EU.

LE MODE D'ÉCHEC DÉMASQUÉ : tenir pour acquis qu'un agent satisfait l'indépendance (donc l'EU) est sur-confiant — les
préférences réelles la violent systématiquement. Distinct de cadrage (108, invariance de description) et decision (8,
utilité espérée). ABSTENTION si données incohérentes. Pur Python, rng seedé.
"""
from __future__ import annotations

ABSTENTION = "abstention"
ANALYSE = "analyse"

G1A = [(1.0, 1)]
G1B = [(0.89, 1), (0.10, 5), (0.01, 0)]
G2A = [(0.11, 1), (0.89, 0)]
G2B = [(0.10, 5), (0.90, 0)]


def eu(gamble, u):
    """Utilité espérée standard."""
    return sum(p * u(x) for p, x in gamble)


def _w(p, gamma):
    """Pondération de probabilité de Tversky-Kahneman (inverse-S pour γ<1, effet de certitude)."""
    if p <= 0 or p >= 1:
        return float(p)
    return p ** gamma / (p ** gamma + (1 - p) ** gamma) ** (1 / gamma)


def rdu(gamble, u, gamma):
    """Utilité rang-dépendante (modèle NON-EU). gamma<1 ⇒ effet de certitude."""
    s = sorted(gamble, key=lambda pe: u(pe[1]))
    val = 0.0
    cum = 0.0
    for p, x in reversed(s):                 # du meilleur au pire résultat
        val += (_w(cum + p, gamma) - _w(cum, gamma)) * u(x)
        cum += p
    return val


def schema_allais(val1A, val1B, val2A, val2B):
    """True si le schéma d'Allais (1A≻1B ET 2B≻2A) est présent."""
    return val1A > val1B and val2B > val2A


def contradiction_eu(u):
    """Les deux inégalités qu'impose le schéma d'Allais pour une utilité u. A>B (pour 1A≻1B) et B>A (pour 2B≻2A) :
    contradictoires. Renvoie (A, B)."""
    A = 0.11 * u(1)
    B = 0.10 * u(5) + 0.01 * u(0)
    return A, B


def analyse(gamma=0.5, u=None):
    """Façade : un agent EU (any u) ne peut pas exhiber Allais ; un agent à effet de certitude (rdu, gamma) le peut.
    (ANALYSE, {eu_allais, rdu_allais, A, B}) ou (ABSTENTION)."""
    if not (0 < gamma <= 1):
        return (ABSTENTION, "gamma hors ]0,1]")
    if u is None:
        u = lambda x: {0: 0.0, 1: 1.0, 5: 1.8}[x]
    eu_allais = schema_allais(eu(G1A, u), eu(G1B, u), eu(G2A, u), eu(G2B, u))
    rdu_allais = schema_allais(rdu(G1A, u, gamma), rdu(G1B, u, gamma), rdu(G2A, u, gamma), rdu(G2B, u, gamma))
    A, B = contradiction_eu(u)
    return (ANALYSE, {"eu_allais": eu_allais, "rdu_allais": rdu_allais, "A": A, "B": B, "gamma": gamma})


def formule(res) -> str:
    if res[0] == ABSTENTION:
        return f"Pas d'analyse : {res[1]}."
    i = res[1]
    return (f"Un agent à utilité espérée n'exhibe JAMAIS le schéma d'Allais (eu_allais={i['eu_allais']}) — il impose "
            f"0.11·u(1M)={i['A']:.2f} à la fois > et < à 0.10·u(5M)+0.01·u(0)={i['B']:.2f}. Un agent à effet de certitude "
            f"(rang-dépendant, γ={i['gamma']}) le reproduit (rdu_allais={i['rdu_allais']}). Supposer l'axiome "
            f"d'indépendance (l'EU) est sur-confiant — les préférences réelles le violent.")


if __name__ == "__main__":
    print("=== PARADOXE D'ALLAIS (axiome d'indépendance) ===\n")
    st, info = analyse()
    print(" ", formule((st, info)))
