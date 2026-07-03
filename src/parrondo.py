"""
PALIER 2 — PARADOXE DE PARRONDO : « perdant + perdant = perdant » est sur-confiant (brique 105, 2026-06-27).

Intuition de dominance : si le jeu A fait perdre et le jeu B fait perdre, alors n'importe quelle combinaison fait perdre.
C'est SUR-CONFIANT — l'intuition de linéarité/dominance suppose que les gains s'additionnent indépendamment de la
DYNAMIQUE. Or si un jeu dépend de l'ÉTAT (ici le capital modulo 3), alterner les deux jeux CHANGE la distribution
stationnaire de l'état, et la combinaison peut GAGNER.

Construction (Harmer & Abbott) :
  • Jeu A : pièce simplement biaisée, P(gagner) = ½ − ε  (perd seul).
  • Jeu B : DÉPENDANT DE L'ÉTAT — si capital ≡ 0 (mod 3) : mauvaise pièce P = 1/10 − ε ; sinon : bonne pièce P = 3/4 − ε.
    Joué SEUL, B passe trop de temps dans l'état défavorable (≡0) → perd.
  • Alterner A et B (ou les mélanger au hasard) : A « brasse » le capital et l'éloigne de l'état ≡0 où B est mauvais →
    l'ENSEMBLE GAGNE (dérive positive).

LE MODE D'ÉCHEC DÉMASQUÉ : conclure qu'une combinaison de jeux perdants perd est sur-confiant — il faut suivre la chaîne
de MARKOV de l'état caché, pas additionner les espérances marginales. Distinct d'ergodicité (93 : moyenne temporelle ≠
d'ensemble). ABSTENTION si horizon insuffisant. Pur Python, rng seedé.
"""
from __future__ import annotations

ABSTENTION = "abstention"
ANALYSE = "analyse"


def _pas_A(capital, rng, eps):
    return capital + (1 if rng.random() < 0.5 - eps else -1)


def _pas_B(capital, rng, eps):
    p = (0.1 - eps) if capital % 3 == 0 else (0.75 - eps)
    return capital + (1 if rng.random() < p else -1)


def joue(strategie, n, rng, eps=0.005, capital0=0):
    """Joue n pas. strategie : 'A', 'B', 'mix' (A/B au hasard), 'alterne' (ABAB...). Renvoie (derive, hist_etat)
    où derive = (capital_final − capital0)/n et hist_etat = fréquences du capital mod 3."""
    cap = capital0
    hist = [0, 0, 0]
    for k in range(n):
        hist[cap % 3] += 1
        if strategie == "A":
            cap = _pas_A(cap, rng, eps)
        elif strategie == "B":
            cap = _pas_B(cap, rng, eps)
        elif strategie == "alterne":
            cap = _pas_A(cap, rng, eps) if k % 2 == 0 else _pas_B(cap, rng, eps)
        else:  # mix aléatoire 50/50
            cap = _pas_A(cap, rng, eps) if rng.random() < 0.5 else _pas_B(cap, rng, eps)
    return (cap - capital0) / n, [h / n for h in hist]


def joue_motif(motif, n, rng, eps=0.005, capital0=0):
    """Joue un MOTIF périodique déterministe (ex. 'ABB'). Renvoie la dérive (capital_final − capital0)/n."""
    cap = capital0
    for k in range(n):
        g = motif[k % len(motif)]
        cap = _pas_A(cap, rng, eps) if g == "A" else _pas_B(cap, rng, eps)
    return (cap - capital0) / n


def derive_motif(motif, n, graines, eps=0.005):
    import random as _r
    return sum(joue_motif(motif, n, _r.Random(g), eps) for g in graines) / len(graines)


def derive_moyenne(strategie, n, graines, eps=0.005):
    """Dérive moyenne sur plusieurs graines (réduit la variance)."""
    import random as _r
    ds = [joue(strategie, n, _r.Random(g), eps)[0] for g in graines]
    return sum(ds) / len(ds)


def analyse(n=40000, eps=0.005, graines=(1, 2, 3, 4, 5)):
    """Façade : dérives de A, B, et du mélange. (ANALYSE, {derive_A, derive_B, derive_mix, ...}) ou (ABSTENTION)."""
    if n < 5000:
        return (ABSTENTION, "horizon trop court pour estimer la dérive")
    dA = derive_moyenne("A", n, graines, eps)
    dB = derive_moyenne("B", n, graines, eps)
    dMix = derive_moyenne("mix", n, graines, eps)
    return (ANALYSE, {"derive_A": dA, "derive_B": dB, "derive_mix": dMix,
                      "A_perd": dA < 0, "B_perd": dB < 0, "mix_gagne": dMix > 0})


def formule(res) -> str:
    if res[0] == ABSTENTION:
        return f"Pas d'analyse : {res[1]}."
    i = res[1]
    return (f"Dérives : A={i['derive_A']:+.4f} ({'perd' if i['A_perd'] else 'gagne'}), B={i['derive_B']:+.4f} "
            f"({'perd' if i['B_perd'] else 'gagne'}), mélange A/B={i['derive_mix']:+.4f} "
            f"({'GAGNE' if i['mix_gagne'] else 'perd'}). Conclure « perdant + perdant = perdant » serait sur-confiant — "
            f"le mélange change la distribution stationnaire de l'état caché.")


if __name__ == "__main__":
    print("=== PARADOXE DE PARRONDO ===\n")
    st, info = analyse()
    print(" ", formule((st, info)))
    import random
    _, hist_B = joue("B", 200000, random.Random(0))
    _, hist_mix = joue("mix", 200000, random.Random(0))
    print(f"\n  temps en état défavorable (cap≡0 mod 3) : B seul={hist_B[0]:.3f} ; mélange={hist_mix[0]:.3f} (1/3≈0.333)")
