"""
PALIER 2 — INÉGALITÉ DE JENSEN / « FLAW OF AVERAGES » : brancher la moyenne des entrées dans une fonction non linéaire est
sur-confiant (brique 129, 2026-06-28).

« Prends la valeur MOYENNE de l'entrée pour obtenir la sortie moyenne » est un réflexe SUR-CONFIANT dès que la fonction est
NON LINÉAIRE. Par l'inégalité de Jensen :
    f CONVEXE  ⇒  E[f(X)] ≥ f(E[X])    (brancher la moyenne SOUS-estime la vraie moyenne),
    f CONCAVE  ⇒  E[f(X)] ≤ f(E[X])    (brancher la moyenne SUR-estime).
L'écart (« gap de Jensen ») croît avec la VARIANCE de l'entrée — il vaut exactement σ² pour f(x)=x². D'où le « flaw of
averages » (Savage) : un projet dont chaque tâche dure « en moyenne » t finit en moyenne PLUS TARD que t ; l'utilité de la
richesse moyenne ≠ l'utilité moyenne ; la moyenne des ratios ≠ le ratio des moyennes. Ignorer la variance en branchant la
moyenne donne une réponse systématiquement biaisée, du côté dicté par la CONVEXITÉ.

LE MODE D'ÉCHEC DÉMASQUÉ : remplacer une entrée incertaine par sa moyenne dans un modèle non linéaire est sur-confiant ;
il faut propager la distribution. Pour une fonction LINÉAIRE (ou sans incertitude), brancher la moyenne est exact
(honnêteté). Distinct de propagation (5, Monte-Carlo CODATA) et fermi (29, ordres de grandeur). rng seedé.
"""
from __future__ import annotations

ABSTENTION = "abstention"
ANALYSE = "analyse"


def gap_jensen(f, mu, sigma, rng, n=200000):
    """Renvoie (E[f(X)], f(E[X]), écart) pour X ~ N(mu, sigma) par Monte-Carlo."""
    s = 0.0
    for _ in range(n):
        s += f(rng.gauss(mu, sigma))
    e_f = s / n
    f_e = f(mu)
    return e_f, f_e, e_f - f_e


def analyse(f, mu, sigma, convexite, rng=None, n=200000):
    """Façade : compare E[f(X)] et f(E[X]). convexite ∈ {'convexe','concave','lineaire'}.
    (ANALYSE, {e_f, f_e, ecart, signe_attendu_ok}) ou (ABSTENTION)."""
    if rng is None or sigma < 0:
        return (ABSTENTION, "rng requis / sigma < 0")
    e_f, f_e, ecart = gap_jensen(f, mu, sigma, rng, n)
    if convexite == "convexe":
        ok = ecart >= -1e-6
    elif convexite == "concave":
        ok = ecart <= 1e-6
    else:                                    # linéaire
        ok = abs(ecart) < 0.05
    return (ANALYSE, {"e_f": e_f, "f_e": f_e, "ecart": ecart, "convexite": convexite, "signe_attendu_ok": ok})


def formule(res) -> str:
    if res[0] == ABSTENTION:
        return f"Pas d'analyse : {res[1]}."
    i = res[1]
    if i["convexite"] == "lineaire":
        return (f"Fonction linéaire : E[f(X)]={i['e_f']:.3f} = f(E[X])={i['f_e']:.3f} (écart {i['ecart']:+.3f}). Brancher "
                f"la moyenne est exact ici.")
    sens = "SOUS-estime" if i["convexite"] == "convexe" else "SUR-estime"
    return (f"Fonction {i['convexite']} : E[f(X)]={i['e_f']:.3f} vs f(E[X])={i['f_e']:.3f} (écart {i['ecart']:+.3f}). "
            f"Brancher la moyenne {sens} la vraie moyenne — c'est sur-confiant ; l'écart de Jensen vient de la variance.")


if __name__ == "__main__":
    import random
    import math
    rng = random.Random(0)
    print("=== INÉGALITÉ DE JENSEN / FLAW OF AVERAGES ===\n")
    for nom, f, conv in (("x²", lambda x: x * x, "convexe"), ("√x", lambda x: math.sqrt(max(x, 0)), "concave"),
                         ("3x", lambda x: 3 * x, "lineaire")):
        st, info = analyse(f, 10.0, 3.0, conv, rng=random.Random(0))
        print(f"  {nom:4s}: " + formule((st, info)))
