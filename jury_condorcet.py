"""
PALIER 2 — THÉORÈME DU JURY DE CONDORCET / SAGESSE DES FOULES : « plus de votants ⇒ meilleure décision » est
sur-confiant (brique 117, 2026-06-28).

Le théorème du jury de Condorcet (1785) : si des votants INDÉPENDANTS tranchent une question binaire et que chacun a une
COMPÉTENCE p > 1/2 (probabilité de voter juste), la précision de la MAJORITÉ → 1 quand le nombre N de votants grandit.
C'est la base de la « sagesse des foules ». Mais ses DEUX hypothèses sont cruciales :
  • COMPÉTENCE > 1/2 : si p < 1/2 (votants systématiquement biaisés), la majorité converge vers la RÉPONSE FAUSSE — une
    foule de plus en plus CONFIANTE et de plus en plus FAUSSE.
  • INDÉPENDANCE : si les votants partagent une source d'erreur (corrélation), la précision majoritaire PLAFONNE bien en
    dessous de 1 ; ajouter des votants n'aide presque plus.

LE MODE D'ÉCHEC DÉMASQUÉ : « la majorité / la foule a forcément raison, et plus elle est nombreuse mieux c'est » est
SUR-CONFIANT sans indépendance ET compétence. Distinct de choix_social (83 : agrégation de PRÉFÉRENCES, Condorcet
paradoxe/Arrow) — ici agrégation ÉPISTÉMIQUE (poursuite de la VÉRITÉ). ABSTENTION si données incohérentes. rng seedé.
"""
from __future__ import annotations

ABSTENTION = "abstention"
ANALYSE = "analyse"


def _beta(a, b, rng):
    x = rng.gammavariate(a, 1)
    y = rng.gammavariate(b, 1)
    return x / (x + y) if (x + y) > 0 else 0.5


def precision_majorite(p, N, rng, kappa=None, T=4000):
    """Précision de la décision MAJORITAIRE. kappa=None ⇒ votants INDÉPENDANTS (compétence p fixe). kappa fini ⇒ votants
    CORRÉLÉS : compétence commune θ ~ Beta(p·κ, (1−p)·κ) tirée par élection (κ petit = forte corrélation)."""
    ok = 0
    for _ in range(T):
        theta = p if kappa is None else _beta(p * kappa, (1 - p) * kappa, rng)
        votes = sum(1 for _ in range(N) if rng.random() < theta)
        ok += votes > N / 2
    return ok / T


def analyse(p=0.6, kappa=None, tailles=(11, 51, 201), T=4000, rng=None):
    """Façade : précision majoritaire vs N. (ANALYSE, {courbe, monte, converge_vrai, plafonne}) ou (ABSTENTION)."""
    if rng is None or not (0 < p < 1):
        return (ABSTENTION, "rng requis / p hors ]0,1[")
    courbe = [(N, precision_majorite(p, N, rng, kappa, T)) for N in tailles]
    accs = [a for _, a in courbe]
    return (ANALYSE, {"p": p, "kappa": kappa, "courbe": courbe, "individu": p,
                      "monte": accs[-1] > accs[0], "acc_grand_N": accs[-1]})


def formule(res) -> str:
    if res[0] == ABSTENTION:
        return f"Pas d'analyse : {res[1]}."
    i = res[1]
    a = i["acc_grand_N"]
    if i["kappa"] is None and i["p"] > 0.5:
        diag = f"compétents+indépendants : la majorité → {a:.2f} (sagesse des foules réelle)"
    elif i["p"] < 0.5:
        diag = f"INCOMPÉTENTS (p<½) : la majorité → {a:.2f} (de plus en plus FAUSSE)"
    else:
        diag = f"CORRÉLÉS : la précision PLAFONNE à {a:.2f} (ajouter des votants n'aide plus)"
    return (f"Compétence individuelle p={i['p']}, {('indépendants' if i['kappa'] is None else 'corrélés')} : à grand N, "
            f"{diag}. Croire que « plus de votants = mieux » est sur-confiant sans indépendance ET compétence > ½.")


if __name__ == "__main__":
    import random
    print("=== THÉORÈME DU JURY DE CONDORCET (sagesse des foules) ===\n")
    for nom, p, kap in (("indépendants compétents", 0.6, None), ("incompétents", 0.45, None), ("corrélés", 0.6, 5)):
        st, info = analyse(p, kap, rng=random.Random(0))
        print(f"  {nom:24s}: " + " ".join(f"N={N}:{a:.2f}" for N, a in info["courbe"]))
        print("       ", formule((st, info)))
