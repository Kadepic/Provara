"""
PALIER 2 — PARADOXE DE BOREL-KOLMOGOROV : conditionner sur un événement de mesure NULLE est ambigu (brique 120, 2026-06-28).

Écrire P(X | Y = y) quand Y est CONTINUE traite « Y = y » comme un événement bien défini. Or {Y = y} est de probabilité
NULLE : la loi conditionnelle n'est définie que comme LIMITE d'événements de mesure positive qui rétrécissent vers lui —
et le RÉSULTAT DÉPEND de la manière de rétrécir.

Exemple canonique (sphère uniforme). On veut la loi de la latitude θ « sachant qu'on est sur un GRAND CERCLE » (un
méridien). Deux procédures limites légitimes :
  • BANDE DE LONGITUDE (|φ − φ₀| < ε → 0) : la latitude suit une loi ∝ cos θ (points concentrés près de l'équateur),
    E|θ| → π/2 − 1 ≈ 0.571.
  • BANDE PERPENDICULAIRE au plan du grand cercle (|n·p| < ε → 0) : la latitude est UNIFORME le long du cercle,
    E|θ| → π/4 ≈ 0.785.
MÊME grand cercle, MÊME quantité θ, DEUX lois conditionnelles différentes. « La loi de θ sur le cercle » n'est pas
définie sans préciser la procédure de conditionnement.

LE MODE D'ÉCHEC DÉMASQUÉ : manipuler P(X | Y=y) pour Y continue comme un objet unique est SUR-CONFIANT — il faut spécifier
le mécanisme limite. Conditionner sur un événement de mesure POSITIVE (la bande, ε>0) est, lui, bien défini. Analogue
continu de la dépendance au protocole, distinct de Bertrand (112, indifférence géométrique) et revelation_bayesienne (99,
discret). ABSTENTION si procédure non spécifiée. Pur Python, rng seedé.
"""
from __future__ import annotations

import math

ABSTENTION = "abstention"
ANALYSE = "analyse"

PROCEDURES = ("longitude", "perpendiculaire")
# E|θ| limite selon la procédure
E_ABS_THEORIQUE = {"longitude": math.pi / 2 - 1, "perpendiculaire": math.pi / 4}


def simule(procedure, n, rng, eps=0.04):
    """Échantillonne une sphère uniforme et garde les latitudes des points dans la bande de la procédure (demi x>0,
    pour comparer le même arc). Renvoie la liste des latitudes θ."""
    lat = []
    for _ in range(n):
        z = rng.uniform(-1, 1)
        phi = rng.uniform(0, 2 * math.pi)
        r = math.sqrt(1 - z * z)
        x = r * math.cos(phi)
        y = r * math.sin(phi)
        theta = math.asin(z)
        if procedure == "longitude":
            if abs(math.atan2(y, x)) < eps:            # bande de longitude autour de φ₀=0
                lat.append(theta)
        elif procedure == "perpendiculaire":
            if abs(y) < eps and x > 0:                 # bande autour du plan du grand cercle (y=0)
                lat.append(theta)
        else:
            raise ValueError("procédure inconnue")
    return lat


def e_abs_latitude(procedure, n, rng, eps=0.04):
    lat = simule(procedure, n, rng, eps)
    return sum(abs(t) for t in lat) / len(lat) if lat else 0.0


def analyse(procedure=None, n=2000000, rng=None, eps=0.04):
    """Façade. procedure=None ⇒ ABSTENTION (conditionnement non spécifié). Sinon (ANALYSE, {procedure, e_abs, theorique})."""
    if procedure is None:
        return (ABSTENTION, "conditionnement sur événement de mesure nulle non spécifié — la loi n'est pas définie")
    if procedure not in PROCEDURES or rng is None:
        return (ABSTENTION, "procédure inconnue / rng requis")
    return (ANALYSE, {"procedure": procedure, "e_abs": e_abs_latitude(procedure, n, rng, eps),
                      "theorique": E_ABS_THEORIQUE[procedure]})


def formule(res) -> str:
    if res[0] == ABSTENTION:
        return f"Pas d'analyse : {res[1]}."
    i = res[1]
    loi = "∝ cos θ (concentrée à l'équateur)" if i["procedure"] == "longitude" else "UNIFORME le long du cercle"
    return (f"Procédure « {i['procedure']} » : E|θ| = {i['e_abs']:.3f} (théorie {i['theorique']:.3f}) — loi {loi}. Une "
            f"autre procédure limite vers le MÊME grand cercle donne une autre loi. Écrire « la » loi conditionnelle sur "
            f"un événement de mesure nulle est sur-confiant.")


if __name__ == "__main__":
    import random
    print("=== PARADOXE DE BOREL-KOLMOGOROV (sphère) ===\n")
    for proc in PROCEDURES:
        st, info = analyse(proc, 2000000, random.Random(0))
        print(f"  {proc:15s}: E|θ|={info['e_abs']:.3f} (théorie {info['theorique']:.3f})")
    print("\n ", formule(analyse(None)))
