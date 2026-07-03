"""
PALIER 2 — PARADOXE DE BERTRAND (probabilités géométriques) : énoncer « LA » probabilité sans spécifier le mécanisme de
tirage est sur-confiant (brique 112, 2026-06-28).

« Quelle est la probabilité qu'une CORDE ALÉATOIRE d'un cercle soit plus longue que le côté du triangle équilatéral
inscrit (= √3·R) ? » La question semble avoir UNE réponse. Mais « corde aléatoire » est AMBIGU — trois constructions
« uniformes » toutes légitimes donnent trois réponses DIFFÉRENTES :
  • EXTRÉMITÉS uniformes (deux points uniformes sur le cercle) → P = 1/3.
  • RAYON uniforme (direction au hasard, milieu uniforme le long du rayon) → P = 1/2.
  • MILIEU uniforme (point uniforme dans le DISQUE comme milieu de la corde) → P = 1/4.
Chaque méthode est INTERNE­MENT cohérente ; aucune n'est « la bonne ». Le PRINCIPE D'INDIFFÉRENCE (« tout est
équiprobable ») est ambigu en continu : il dépend de la PARAMÉTRISATION choisie.

LE MODE D'ÉCHEC DÉMASQUÉ : affirmer « la » probabilité d'un événement géométrique sans fixer le mécanisme de tirage est
SUR-CONFIANT. L'attitude honnête : exiger la spécification du protocole — une fois fixé, la probabilité est DÉTERMINÉE
(pas de nihilisme). C'est l'analogue CONTINU/géométrique de la dépendance au protocole (≠ revelation_bayesienne 99,
discret/Monty Hall). ABSTENTION si la méthode n'est pas spécifiée. Pur Python, rng seedé.
"""
from __future__ import annotations

import math

ABSTENTION = "abstention"
ANALYSE = "analyse"

SEUIL = math.sqrt(3.0)        # côté du triangle équilatéral inscrit (R=1) ; corde plus longue ⟺ distance au centre < 1/2
METHODES = ("extremites", "rayon", "milieu")
P_THEORIQUE = {"extremites": 1 / 3, "rayon": 1 / 2, "milieu": 1 / 4}


def _longue(d):
    """Une corde à distance d du centre (R=1) a pour longueur 2√(1−d²) ; plus longue que √3 ⟺ d < 1/2."""
    return 2 * math.sqrt(max(0.0, 1 - d * d)) > SEUIL


def tire_corde_longue(methode, rng):
    """Tire une corde selon la méthode et renvoie True si elle dépasse le côté du triangle inscrit."""
    if methode == "extremites":
        a = rng.uniform(0, 2 * math.pi)
        b = rng.uniform(0, 2 * math.pi)
        return 2 * abs(math.sin((a - b) / 2)) > SEUIL
    if methode == "rayon":
        d = rng.uniform(0, 1)                      # milieu uniforme le long d'un rayon
        return _longue(d)
    if methode == "milieu":
        d = math.sqrt(rng.uniform(0, 1))           # point uniforme dans le disque (densité ∝ r)
        return _longue(d)
    raise ValueError("méthode inconnue")


def probabilite(methode, n, rng):
    """Estimation Monte-Carlo de P(corde longue) pour une méthode."""
    return sum(tire_corde_longue(methode, rng) for _ in range(n)) / n


def analyse(methode=None, n=200000, rng=None):
    """Façade. Si methode=None ⇒ ABSTENTION (question mal posée). Sinon (ANALYSE, {methode, p_sim, p_theorique})."""
    if methode is None:
        return (ABSTENTION, "« corde aléatoire » non spécifiée — la probabilité n'est pas définie sans le mécanisme")
    if methode not in METHODES or rng is None:
        return (ABSTENTION, "méthode inconnue / rng requis")
    return (ANALYSE, {"methode": methode, "p_sim": probabilite(methode, n, rng),
                      "p_theorique": P_THEORIQUE[methode]})


def formule(res) -> str:
    if res[0] == ABSTENTION:
        return f"Pas d'analyse : {res[1]}."
    i = res[1]
    return (f"Méthode « {i['methode']} » : P(corde longue) = {i['p_sim']:.3f} (théorie {i['p_theorique']:.3f}). "
            f"D'autres constructions « uniformes » donnent d'autres valeurs (1/3, 1/2, 1/4) — affirmer « la » probabilité "
            f"sans fixer le mécanisme serait sur-confiant.")


if __name__ == "__main__":
    import random
    print("=== PARADOXE DE BERTRAND (corde aléatoire) ===\n")
    for meth in METHODES:
        st, info = analyse(meth, 300000, random.Random(0))
        print(f"  {meth:10s}: P={info['p_sim']:.3f} (théorie {info['p_theorique']:.3f})")
    print("\n ", formule(analyse(None)))
