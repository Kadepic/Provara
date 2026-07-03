"""
PALIER 2 — PROBLÈME DE PASCAL (Pascal's mugging) / UTILITÉ NON BORNÉE : maximiser naïvement l'espérance d'utilité avec des
gains non bornés est sur-confiant (brique 123, 2026-06-28).

Un maître-chanteur réclame une petite somme D en promettant un gain ASTRONOMIQUE M (« donne-moi 5 € ou je torture 3^^^3
personnes / je te donne 10^100 d'utilité »). L'agent qui MAXIMISE NAÏVEMENT l'espérance d'utilité assigne une probabilité
infime ε à la promesse, mais ε·M peut dépasser D dès que M est assez grand. Comme le chanteur peut ANNONCER M aussi grand
qu'il veut, l'agent finit TOUJOURS par payer — il est exploitable SANS BORNE par n'importe quelle promesse extravagante.
C'est SUR-CONFIANT : traiter une espérance dominée par un produit (probabilité infime) × (gain colossal) comme un guide
fiable de décision.

LES CORRECTIONS :
  • UTILITÉ BORNÉE : au-delà d'un plafond U_max, des promesses plus grandes n'augmentent plus l'espérance ⇒ l'agent
    refuse les demandes qui exigent plus que ε·U_max.
  • PÉNALITÉ DE LEVIER (prior sceptique) : la probabilité de POUVOIR délivrer M décroît au moins comme c/M ⇒ ε(M)·M ≤ c
    reste BORNÉ ⇒ l'agent refuse les promesses géantes.

LE MODE D'ÉCHEC DÉMASQUÉ : la maximisation d'EU à utilité/promesses non bornées est exploitable ; borner l'utilité ou
pénaliser le levier la rend robuste. Pour une promesse VÉRIFIABLE et modérée, l'EU reste raisonnable (honnêteté). Distinct
de saint_petersbourg (91, espérance infinie d'un seul tirage) et decision (8, utilité espérée). Pur Python.
"""
from __future__ import annotations

ABSTENTION = "abstention"
ANALYSE = "analyse"


def paye_naif(M, eps, D):
    """Agent EU naïf : paie ssi ε·M > D (probabilité ε fixe quel que soit M)."""
    return eps * M > D


def paye_borne(M, eps, U_max, D):
    """Agent à utilité BORNÉE : l'utilité de la promesse est plafonnée à U_max."""
    return eps * min(M, U_max) > D


def proba_levier(M, eps, c):
    """Prior à pénalité de levier : P(délivrer M) = min(ε, c/M) — décroît avec l'ampleur de la promesse."""
    return min(eps, c / M) if M > 0 else eps


def paye_levier(M, eps, c, D):
    """Agent à pénalité de levier : paie ssi P(M)·M > D, avec P(M)·M ≤ c borné."""
    return proba_levier(M, eps, c) * M > D


def analyse(eps=1e-9, D=5.0, U_max=1e6, c=1.0, promesses=(1e3, 1e9, 1e15, 1e30, 1e100)):
    """Façade : pour des promesses M croissantes, qui paie ? (ANALYSE, {...}) ou (ABSTENTION)."""
    if not (0 < eps < 1) or D <= 0:
        return (ABSTENTION, "ε hors ]0,1[ ou D ≤ 0")
    lignes = []
    for M in promesses:
        lignes.append((M, {"naif": paye_naif(M, eps, D), "borne": paye_borne(M, eps, U_max, D),
                           "levier": paye_levier(M, eps, c, D), "ev_levier": proba_levier(M, eps, c) * M}))
    naif_paie_geant = lignes[-1][1]["naif"]
    levier_borne = max(l[1]["ev_levier"] for l in lignes)
    return (ANALYSE, {"lignes": lignes, "naif_paie_la_plus_grande": naif_paie_geant,
                      "borne_paie_la_plus_grande": lignes[-1][1]["borne"],
                      "levier_paie_la_plus_grande": lignes[-1][1]["levier"], "ev_levier_max": levier_borne, "D": D})


def formule(res) -> str:
    if res[0] == ABSTENTION:
        return f"Pas d'analyse : {res[1]}."
    i = res[1]
    return (f"Face à une promesse colossale : l'agent NAÏF paie ({i['naif_paie_la_plus_grande']}) — exploitable sans "
            f"borne. L'agent à utilité BORNÉE refuse ({not i['borne_paie_la_plus_grande']}=refus) ; l'agent à pénalité de "
            f"LEVIER refuse aussi (espérance plafonnée à {i['ev_levier_max']:.2f} < D={i['D']}). Maximiser l'EU à gains "
            f"non bornés est sur-confiant.")


if __name__ == "__main__":
    print("=== PROBLÈME DE PASCAL (Pascal's mugging) ===\n")
    st, info = analyse()
    for M, d in info["lignes"]:
        print(f"  M={M:.0e}: naïf paie={d['naif']}  borné paie={d['borne']}  levier paie={d['levier']} "
              f"(EV levier={d['ev_levier']:.2f})")
    print("\n ", formule((st, info)))
