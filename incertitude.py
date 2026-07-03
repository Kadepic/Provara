"""
PHASE 2 — NON-BORNÉ : LE JUGE D'INCERTITUDE CALIBRÉE (1re brique, 2026-06-23).

Le borné garantit « jamais un faux » (exact, vérifié, ou abstention). Le non-borné ne peut PAS garantir
l'exactitude d'une estimation unique. La discipline change donc, SANS perdre l'honnêteté :

    « estimation + CONFIANCE CALIBRÉE + abstention quand on ne sait pas »  (l'équivalent gradué de l'abstention).

LE PONT (pourquoi ça reste jugé par la réalité) : on ne vérifie pas qu'UNE estimation est juste — on vérifie
que l'INCERTITUDE est CALIBRÉE : un intervalle annoncé « à 90 % » doit contenir la vraie valeur ~90 % du temps,
ce qui se VÉRIFIE par simulation Monte-Carlo (cf. valide_incertitude.py). La réalité juge l'honnêteté de
l'incertitude, pas la réponse. Méthodes sans dépendance (bootstrap / Wilson) : robustes et auto-suffisantes.

JAMAIS de fausse précision : échantillon trop petit -> ABSTENTION (on ne fabrique pas un intervalle bidon).
"""
from __future__ import annotations

import math
import random

ABSTENTION = "abstention"
ESTIMATION = "estimation"
N_MIN = 5                      # en-dessous : incertitude non quantifiable honnêtement -> abstention

_Z = {0.80: 1.2816, 0.90: 1.6449, 0.95: 1.9600, 0.99: 2.5758}   # quantiles normaux usuels


def estime_moyenne(echantillon, confiance: float = 0.90, n_boot: int = 2000, seed: int = 0):
    """Estime la MOYENNE d'une population à partir d'un échantillon, avec intervalle de confiance par BOOTSTRAP
    (rééchantillonnage, sans hypothèse de loi). Renvoie (ESTIMATION, (point, (bas, haut)), confiance) ou
    (ABSTENTION, None, raison) si l'échantillon est trop petit. Déterministe (seed)."""
    ech = [float(v) for v in echantillon]
    n = len(ech)
    if n < N_MIN:
        return (ABSTENTION, None, f"échantillon trop petit (n={n} < {N_MIN}) : incertitude non quantifiable")
    point = sum(ech) / n
    rng = random.Random(seed)
    moyennes = []
    for _ in range(n_boot):
        s = 0.0
        for _ in range(n):
            s += ech[rng.randrange(n)]
        moyennes.append(s / n)
    moyennes.sort()
    alpha = (1.0 - confiance) / 2.0
    bas = moyennes[int(alpha * n_boot)]
    haut = moyennes[min(n_boot - 1, int((1.0 - alpha) * n_boot))]
    return (ESTIMATION, (point, (bas, haut)), confiance)


def estime_proportion(echantillon, confiance: float = 0.90):
    """Estime une PROPORTION (échantillon de 0/1 ou booléens) avec l'intervalle de WILSON (calibré même pour p
    extrême / petit n, contrairement à l'intervalle normal naïf). Renvoie (ESTIMATION, (p, (bas, haut)),
    confiance) ou ABSTENTION si trop petit."""
    ech = [1 if v else 0 for v in echantillon]
    n = len(ech)
    if n < N_MIN:
        return (ABSTENTION, None, f"échantillon trop petit (n={n} < {N_MIN}) : incertitude non quantifiable")
    z = _Z.get(round(confiance, 2), 1.6449)
    k = sum(ech)
    p = k / n
    denom = 1.0 + z * z / n
    centre = (p + z * z / (2.0 * n)) / denom
    marge = (z * math.sqrt(p * (1.0 - p) / n + z * z / (4.0 * n * n))) / denom
    return (ESTIMATION, (p, (max(0.0, centre - marge), min(1.0, centre + marge))), confiance)


DIFFERENT = "different"
INDETERMINE = "indetermine"


def compare_moyennes(a, b, confiance: float = 0.90, n_boot: int = 2000, seed: int = 0):
    """Compare deux groupes : « la moyenne de A diffère-t-elle de celle de B ? ». Renvoie (verdict, diff_estimée,
    (bas, haut), confiance) où verdict ∈ {DIFFERENT (l'intervalle de la différence EXCLUT 0), INDETERMINE (inclut
    0)} ou (ABSTENTION, ...) si trop petit. Intervalle de la différence par BOOTSTRAP. SOUNDNESS = sous H0 (A et B
    de même moyenne), DIFFERENT n'est émis qu'à ~(1-confiance) près = TAUX DE FAUX POSITIFS CONTRÔLÉ (calibré,
    prouvé Monte-Carlo). JAMAIS « identiques » affirmé : INDETERMINE = « pas de différence détectée » (pas une preuve)."""
    a = [float(v) for v in a]
    b = [float(v) for v in b]
    if len(a) < N_MIN or len(b) < N_MIN:
        return (ABSTENTION, None, None, f"échantillon(s) trop petit(s) (n<{N_MIN})")
    na, nb = len(a), len(b)
    diff = sum(a) / na - sum(b) / nb
    rng = random.Random(seed)
    diffs = []
    for _ in range(n_boot):
        sa = sum(a[rng.randrange(na)] for _ in range(na)) / na
        sb = sum(b[rng.randrange(nb)] for _ in range(nb)) / nb
        diffs.append(sa - sb)
    diffs.sort()
    alpha = (1.0 - confiance) / 2.0
    bas = diffs[int(alpha * n_boot)]
    haut = diffs[min(n_boot - 1, int((1.0 - alpha) * n_boot))]
    verdict = DIFFERENT if (bas > 0 or haut < 0) else INDETERMINE
    return (verdict, diff, (bas, haut), confiance)


def predit_intervalle(echantillon, confiance: float = 0.90):
    """Intervalle de PRÉDICTION : où tombera la PROCHAINE observation, ~confiance du temps (quantiles empiriques).
    DIFFÉRENT de l'IC de la moyenne (plus large : porte sur UN tirage futur, pas sur l'estimation d'un paramètre).
    Renvoie (ESTIMATION, (None, (bas, haut)), confiance) ou ABSTENTION. Calibré pour des données i.i.d. (prouvé MC)."""
    ech = sorted(float(v) for v in echantillon)
    n = len(ech)
    if n < N_MIN:
        return (ABSTENTION, None, f"échantillon trop petit (n={n} < {N_MIN})")
    alpha = (1.0 - confiance) / 2.0

    def q(p):
        i = p * (n - 1)
        lo = int(i)
        if lo + 1 >= n:
            return ech[-1]
        return ech[lo] * (1.0 - (i - lo)) + ech[lo + 1] * (i - lo)

    return (ESTIMATION, (None, (q(alpha), q(1.0 - alpha))), confiance)


ANORMAL = "anormal"
NORMAL = "normal"
HAUSSE = "hausse"
BAISSE = "baisse"
STABLE = "stable"


def est_anormal(valeur, echantillon, confiance: float = 0.95):
    """Une valeur est-elle ANORMALE par rapport à l'échantillon ? = hors de l'intervalle de PRÉDICTION à
    `confiance`. SOUNDNESS = sous H0 (valeur tirée de la MÊME loi), ANORMAL n'est émis qu'à ~(1-confiance) =
    TAUX DE FAUSSES ALERTES CONTRÔLÉ (calibré). Renvoie (ANORMAL/NORMAL, (bas, haut), confiance) ou ABSTENTION.
    NORMAL = « rien d'inhabituel détecté » (pas une preuve de normalité)."""
    res = predit_intervalle(echantillon, confiance)
    if res[0] == ABSTENTION:
        return (ABSTENTION, None, res[-1])
    _, (_, (bas, haut)), conf = res
    v = float(valeur)
    return (ANORMAL if (v < bas or v > haut) else NORMAL, (bas, haut), conf)


def tendance(serie, confiance: float = 0.90, n_boot: int = 2000, seed: int = 0):
    """La série a-t-elle une TENDANCE (hausse/baisse) dans le temps ? Pente d'une régression simple, IC par
    bootstrap de paires. Verdict HAUSSE/BAISSE (l'IC de la pente exclut 0) ou STABLE (inclut 0), ou ABSTENTION.
    SOUNDNESS = sous H0 (pas de tendance, valeurs i.i.d.), HAUSSE/BAISSE n'est émis qu'à ~(1-confiance) =
    FAUX POSITIFS CONTRÔLÉS. STABLE = « pas de tendance détectée » (jamais « constant » affirmé)."""
    ys = [float(v) for v in serie]
    n = len(ys)
    if n < N_MIN:
        return (ABSTENTION, None, None, f"série trop courte (n={n} < {N_MIN})")
    xs = list(range(n))

    def pente(ix, iy):
        mx = sum(ix) / len(ix)
        my = sum(iy) / len(iy)
        den = sum((v - mx) ** 2 for v in ix)
        if den == 0:
            return 0.0
        return sum((ix[i] - mx) * (iy[i] - my) for i in range(len(ix))) / den

    p = pente(xs, ys)
    rng = random.Random(seed)
    pentes = []
    for _ in range(n_boot):
        idx = [rng.randrange(n) for _ in range(n)]
        bx = [xs[i] for i in idx]
        by = [ys[i] for i in idx]
        pentes.append(pente(bx, by))
    pentes.sort()
    alpha = (1.0 - confiance) / 2.0
    bas = pentes[int(alpha * n_boot)]
    haut = pentes[min(n_boot - 1, int((1.0 - alpha) * n_boot))]
    if bas > 0:
        verdict = HAUSSE
    elif haut < 0:
        verdict = BAISSE
    else:
        verdict = STABLE
    return (verdict, p, (bas, haut), confiance)


def _n(v):
    """Formate un nombre lisiblement (entier si rond)."""
    return str(int(round(v))) if abs(v - round(v)) < 1e-9 else f"{v:.2f}"


def formule(res, quoi: str = "moyenne") -> str:
    """LA PAROLE DU NON-BORNÉ — traduit un résultat (estime/compare/predit) en phrase HONNÊTE et nuancée :
    « je pense que…, mais ce n'est pas sûr — à X% c'est entre … ». Jamais de fausse certitude ; l'abstention
    se dit aussi. `quoi` ∈ {moyenne, proportion, prediction, comparaison}."""
    statut = res[0]
    if statut == ABSTENTION:
        return f"Je préfère ne pas me prononcer : {res[-1]}."
    if quoi == "anomalie":
        verdict, (bas, haut), conf = res
        pct = round(conf * 100)
        if verdict == ANORMAL:
            return (f"Cette valeur me semble anormale : l'habituel (~{pct}%) est entre {_n(bas)} et {_n(haut)}, "
                    f"elle en sort — mais ça peut arriver par hasard dans moins de {100 - pct}% des cas.")
        return (f"Rien d'inhabituel : cette valeur est dans la plage attendue ({_n(bas)} à {_n(haut)}). "
                "Ça ne prouve pas qu'elle est « normale », juste que je ne vois pas d'anomalie.")
    if quoi == "tendance":
        verdict, pente, (bas, haut), conf = res
        pct = round(conf * 100)
        if verdict == HAUSSE:
            return f"Je pense que ça monte (pente ≈ {_n(pente)}), mais je peux me tromper dans moins de {100 - pct}% des cas."
        if verdict == BAISSE:
            return f"Je pense que ça baisse (pente ≈ {_n(pente)}), mais je peux me tromper dans moins de {100 - pct}% des cas."
        return "Je ne détecte pas de tendance nette — ça ne prouve pas que c'est stable, seulement que je ne la vois pas."
    if quoi == "comparaison":
        verdict, diff, (bas, haut), conf = res
        pct = round(conf * 100)
        if verdict == DIFFERENT:
            return (f"Je pense qu'il y a une vraie différence (écart ≈ {_n(diff)}, entre {_n(bas)} et {_n(haut)}), "
                    f"mais je peux me tromper dans moins de {100 - pct}% des cas.")
        return ("Je ne détecte pas de différence nette entre les deux — attention, ça ne prouve PAS qu'ils sont "
                "identiques, seulement que je ne la vois pas.")
    point, (bas, haut), conf = res[1][0], res[1][1], res[2]
    pct = round(conf * 100)
    if quoi == "proportion":
        return (f"J'estime à peu près {round(point * 100)}%, mais sans certitude : à {pct}% de confiance, "
                f"c'est entre {round(bas * 100)}% et {round(haut * 100)}%.")
    if quoi == "prediction":
        return (f"La prochaine valeur devrait tomber entre {_n(bas)} et {_n(haut)} environ {pct}% du temps, "
                f"mais je ne peux pas la garantir.")
    return (f"Je pense que c'est autour de {_n(point)}, mais ce n'est pas sûr : à {pct}% de confiance, "
            f"la vraie valeur est entre {_n(bas)} et {_n(haut)}.")


if __name__ == "__main__":
    from garde_ressources import borne
    borne()
    print("=== JUGE D'INCERTITUDE CALIBRÉE (non-borné, honnête) ===\n")
    print(" ", formule(estime_moyenne([2, 4, 6, 8, 10, 3, 5, 7]), "moyenne"))
    print(" ", formule(estime_proportion([1, 0, 1, 1, 0, 1, 1, 0, 1, 1]), "proportion"))
    print(" ", formule(predit_intervalle([2, 4, 6, 8, 10, 3, 5, 7, 9, 1]), "prediction"))
    print(" ", formule(compare_moyennes([1, 2, 3, 4, 5], [8, 9, 10, 11, 12]), "comparaison"))
    print(" ", formule(estime_moyenne([1, 2, 3]), "moyenne"))
    print("  compare [1,2,3,4,5] vs [6,7,8,9,10] @90% :", compare_moyennes([1, 2, 3, 4, 5], [6, 7, 8, 9, 10]))
    print("  moyenne [2,4,6,8,10,3,5,7] @90% :", estime_moyenne([2, 4, 6, 8, 10, 3, 5, 7]))
    print("  proportion [1,0,1,1,0,1,1,0,1,1] @90% :", estime_proportion([1, 0, 1, 1, 0, 1, 1, 0, 1, 1]))
    print("  abstention (n=3) :", estime_moyenne([1, 2, 3]))
