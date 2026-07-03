"""
Brique 7 — LE MESUREUR D'APPRENTISSAGE (la boîte de verre).

« Observabilité avant capacité » (Décision C du PLAN-DE-CONSTRUCTION). On ne
SUPPOSE pas que le modèle s'améliore : on le MESURE. Et surtout, on traque le
piège n°2 du doc (§2) : une IA qui *se croit* meilleure sans l'être.

L'instrument trace, au fil des tours de ré-entraînement, DEUX courbes :
  - RÉUSSITE       : fraction des propositions qui passent les tests VISIBLES ;
  - GÉNÉRALISATION : fraction qui passe aussi le HELD-OUT (du jamais-vu).

La métrique reine = la GÉNÉRALISATION. Si elle monte -> il apprend VRAIMENT.
Si seule la réussite monte et que la généralisation reste plate -> il MÉMORISE :
il se trompe lui-même. L'instrument doit crier la différence, pas la cacher.

C'est l'équivalent, pour ce projet, du « morts/1000 pas qui baisse » d'AUTOS :
le chiffre qui prouve l'apprentissage, ou le réfute honnêtement.
"""

from __future__ import annotations

import dataclasses

from juge import Limites, juge


@dataclasses.dataclass(frozen=True)
class Point:
    """Un relevé de compétence à un tour donné."""
    tour: int
    essais: int
    reussite: float          # fraction passant les tests visibles
    generalisation: float    # fraction passant le held-out (compétence honnête)


def evalue(generateur, tache, n_essais: int = 10,
           limites: Limites | None = None) -> tuple[float, float]:
    """
    Mesure la compétence ACTUELLE du générateur sur une tâche : on lui demande
    n_essais propositions, et on compte combien passent le visible, et combien
    passent aussi le held-out. Renvoie (taux_reussite, taux_generalisation).

    Pure mesure : n'archive rien, ne modifie rien. C'est un thermomètre.
    """
    candidats = generateur.propose(tache.prompt, n_essais)
    n = len(candidats)
    if n == 0:
        return (0.0, 0.0)

    passe_visible = 0
    passe_heldout = 0
    for code in candidats:
        if juge(code, tache.tests, limites).passe:
            passe_visible += 1
            if tache.tests_held_out and juge(code, tache.tests_held_out, limites).passe:
                passe_heldout += 1
    return (passe_visible / n, passe_heldout / n)


@dataclasses.dataclass(frozen=True)
class Diagnostic:
    """Le verdict sur une courbe d'apprentissage."""
    apprend: bool             # la généralisation monte nettement
    generalise: bool          # elle atteint un vrai niveau (pas juste "monte un peu")
    memorise: bool            # PIÈGE : réussite monte mais généralisation reste à terre
    gain_reussite: float      # variation réussite (fin - début)
    gain_generalisation: float
    verdict: str              # phrase lisible


def analyse(courbe: list[Point], marge: float = 0.15) -> Diagnostic:
    """
    Compare le DÉBUT et la FIN de la courbe (par tiers, pour lisser le bruit) et
    rend un diagnostic honnête : apprend / mémorise / plateau.
    """
    if len(courbe) < 2:
        return Diagnostic(False, False, False, 0.0, 0.0, "courbe trop courte pour conclure")

    k = max(1, len(courbe) // 3)
    debut, fin = courbe[:k], courbe[-k:]
    moy = lambda pts, sel: sum(sel(p) for p in pts) / len(pts)

    dv = moy(debut, lambda p: p.reussite)
    fv = moy(fin, lambda p: p.reussite)
    dg = moy(debut, lambda p: p.generalisation)
    fg = moy(fin, lambda p: p.generalisation)
    gain_v, gain_g = fv - dv, fg - dg

    apprend = gain_g >= marge
    generalise = fg >= 0.5
    memorise = (gain_v >= marge) and (fg < 0.2)

    if memorise:
        verdict = ("MÉMORISE (piège) : meilleur sur le visible, ~nul sur le held-out. "
                   "Il se croit bon sans l'être — exactement ce qu'on refuse.")
    elif apprend and generalise:
        verdict = ("APPREND VRAIMENT : la réussite sur du NON-VU monte. "
                   "C'est de la compétence réelle, pas de l'illusion.")
    elif apprend:
        verdict = "progresse, mais la généralisation reste basse — laisser tourner / tâches intermédiaires."
    else:
        verdict = ("PLATEAU : pas d'amélioration nette. Besoin de tâches plus dures, "
                   "de plus de matière, ou d'un autre réglage.")
    return Diagnostic(apprend, generalise, memorise, gain_v, gain_g, verdict)


_BARRES = "▁▂▃▄▅▆▇█"


def _spark(valeurs: list[float]) -> str:
    return "".join(_BARRES[min(7, int(v * 8))] for v in valeurs)


def trace(courbe: list[Point]) -> str:
    """Rend la courbe lisible dans le terminal : tableau + sparklines."""
    lignes = ["  tour | réussite(visible) | généralisation(held-out)",
              "  -----+-------------------+------------------------"]
    for p in courbe:
        lignes.append(f"  {p.tour:>4} |      {p.reussite:>4.0%}        |        {p.generalisation:>4.0%}")
    lignes.append(f"  réussite       {_spark([p.reussite for p in courbe])}")
    lignes.append(f"  généralisation {_spark([p.generalisation for p in courbe])}")
    return "\n".join(lignes)
