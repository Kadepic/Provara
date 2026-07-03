"""
PALIER 2 — PARADOXE DES DEUX ENVELOPPES : l'argument « échanger rapporte 25 % à coup sûr » est sur-confiant
(brique 104, 2026-06-27).

Une enveloppe contient X, l'autre 2X ; vous en choisissez une. Argument NAÏF : « soit A mon montant ; l'autre vaut A/2
ou 2A avec proba ½ chacune, donc E[autre] = ½·(A/2) + ½·(2A) = 1.25·A > A ⇒ il faut TOUJOURS échanger ». Absurde : par
symétrie le même argument vaut pour l'autre enveloppe (échange sans fin), et on n'a rien observé.

LE DÉFAUT — un a priori IMPROPRE : poser P(autre=2A) = P(autre=A/2) = ½ pour TOUTE valeur A suppose une loi UNIFORME sur
un montant non borné, qui ne se normalise pas. Sous un a priori PROPRE (forcément décroissant / borné), la probabilité de
tenir la PETITE enveloppe sachant A dépend de A : elle vaut ½ à l'INTÉRIEUR du support, mais 1 au plancher et 0 au
plafond. Ces BORNES — que l'a priori impropre escamote — font que l'espérance INCONDITIONNELLE du gain d'échange est
EXACTEMENT 0 (les enveloppes sont échangeables : E[échanger] = E[rester]).

LE MODE D'ÉCHEC DÉMASQUÉ : « +25 % gratuits en échangeant » est sur-confiant — il extrapole un a priori impropre sans
bornes. Le gain conditionnel (+25 %) est réel à l'intérieur mais ANNULÉ par les bornes ; gain inconditionnel = 0. La
résolution LÉGITIME (Cover) utilise un a priori propre et un seuil. ABSTENTION si support trop petit. Pur Python, rng seedé.
"""
from __future__ import annotations

ABSTENTION = "abstention"
ANALYSE = "analyse"


def p_petite_sachant(j, K):
    """P(tenir la PETITE enveloppe | montant observé = 2^j), a priori : i uniforme sur {0..K}, paires (2^i, 2^{i+1})."""
    peut_petite = (0 <= j <= K)          # j est le petit d'une paire (i=j)
    peut_grande = (1 <= j <= K + 1)      # j est le grand d'une paire (i=j-1)
    if peut_petite and peut_grande:
        return 0.5                        # intérieur : ½
    if peut_petite:
        return 1.0                        # plancher j=0 : forcément la petite
    return 0.0                            # plafond j=K+1 : forcément la grande


def gain_conditionnel(j, K):
    """E[échanger | a=2^j] − a : gain espéré d'échanger en ayant observé 2^j."""
    a = 2 ** j
    ps = p_petite_sachant(j, K)
    e_autre = ps * (2 * a) + (1 - ps) * (a / 2)
    return e_autre - a


def esperance_gain_inconditionnel(K):
    """E[montant après échange] − E[montant en restant], moyenné sur l'a priori propre. Vaut EXACTEMENT 0."""
    total = 0.0
    poids = 0.0
    for i in range(K + 1):                # paire (2^i, 2^{i+1}), i uniforme
        for petite in (True, False):      # quelle enveloppe on tient (½ chacune)
            a = 2 ** i if petite else 2 ** (i + 1)
            autre = 2 ** (i + 1) if petite else 2 ** i
            total += (autre - a)          # gain d'échanger ce tirage précis
            poids += 1
    return total / poids


def simule(K, n, rng, strategie="echanger", seuil=None):
    """Argent moyen obtenu. strategie : 'rester', 'echanger', ou 'seuil' (échanger ssi a ≤ seuil). a priori i~U{0..K}."""
    total = 0.0
    larges = 0
    for _ in range(n):
        i = rng.randint(0, K)
        paire = (2 ** i, 2 ** (i + 1))
        tient = paire[rng.randint(0, 1)]
        autre = paire[1] if tient == paire[0] else paire[0]
        if strategie == "rester":
            final = tient
        elif strategie == "echanger":
            final = autre
        else:                              # seuil
            final = autre if tient <= seuil else tient
        total += final
        larges += (final == max(paire))
    return total / n, larges / n


def analyse(K=10):
    """Façade. (ANALYSE, {gain_interieur, p_petite_interieur, gain_inconditionnel, ...}) ou (ABSTENTION, raison)."""
    if K < 2:
        return (ABSTENTION, "support trop petit (K < 2)")
    j_int = K // 2                         # une valeur intérieure
    return (ANALYSE, {"K": K, "p_petite_interieur": p_petite_sachant(j_int, K),
                      "gain_interieur": gain_conditionnel(j_int, K),
                      "p_petite_plancher": p_petite_sachant(0, K),
                      "p_petite_plafond": p_petite_sachant(K + 1, K),
                      "gain_inconditionnel": esperance_gain_inconditionnel(K)})


def formule(res) -> str:
    if res[0] == ABSTENTION:
        return f"Pas d'analyse : {res[1]}."
    i = res[1]
    return (f"À l'intérieur, P(petite|a)={i['p_petite_interieur']:.2f} et le gain d'échange semble +{i['gain_interieur']:.0f} "
            f"(l'argument naïf). Mais aux bornes P(petite)={i['p_petite_plancher']:.0f}/{i['p_petite_plafond']:.0f}, et le "
            f"gain INCONDITIONNEL = {i['gain_inconditionnel']:.0f}. « +25 % en échangeant » est sur-confiant : il "
            f"extrapole un a priori impropre sans bornes.")


if __name__ == "__main__":
    import random
    K = 10
    print("=== PARADOXE DES DEUX ENVELOPPES ===\n")
    st, info = analyse(K)
    print(" ", formule((st, info)))
    rng = random.Random(0)
    m_rester, _ = simule(K, 400000, rng, "rester")
    m_echanger, _ = simule(K, 400000, rng, "echanger")
    print(f"\n  argent moyen : rester={m_rester:.1f} ; échanger={m_echanger:.1f} (≈ égaux)")
    _, p_large = simule(K, 400000, rng, "seuil", seuil=2 ** (K // 2))
    print(f"  règle à seuil (Cover) : P(finir avec la grande) = {p_large:.3f} (> 0.5, résolution légitime via l'a priori)")
