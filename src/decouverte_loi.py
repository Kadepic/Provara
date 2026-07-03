"""
DÉCOUVERTE SYMBOLIQUE DE LOI — brique Vague 4. Le pivot RAPPEL -> RAISONNEMENT (data -> loi manipulable).

POURQUOI : la machine possède des données (mesures, faits numériques) ; en extraire une LOI (y = f(x)) la fait passer
du rappel au raisonnement — elle peut alors extrapoler, inverser, calculer une limite. C'est ainsi qu'elle apprend
des lois du monde à partir de l'observation, pas seulement les retrouver.

MODÈLE : régression symbolique BORNÉE — un petit espace de gabarits (constante, proportionnel, linéaire, inverse,
carré, cube, racine). Pour chaque gabarit : ajustement EXACT depuis le minimum de points nécessaires, puis
VÉRIFICATION sur TOUS les points (dont au moins un non utilisé pour l'ajustement = garde anti-surapprentissage).

FAUX=0 :
  • Une loi n'est retournée QUE si elle colle à TOUS les points dans la tolérance (y compris des points HELD-OUT
    non utilisés pour l'ajuster). Sinon -> None : « pas de loi simple trouvée » (abstention honnête, jamais une loi
    plaquée qui ne colle pas partout).
  • Il faut STRICTEMENT plus de points que de paramètres (au moins 1 point de vérification) — sinon -> None (on ne
    conclut pas d'un ajustement trivial).
  • Déterministe (gabarits essayés du plus simple au plus complexe).
Stdlib pur, souverain. Extension multi-variables (produits de puissances, à la Buckingham) = ultérieure.
"""
from __future__ import annotations

import math


def _colle(predit, data, tol):
    for x, y in data:
        p = predit(x)
        if p is None or not math.isfinite(p):
            return False
        echelle = max(abs(y), 1e-12)
        if abs(p - y) / echelle > tol:
            return False
    return True


def _gabarits(data):
    """Génère (forme, n_params, ajuste->predit|None) du plus simple au plus complexe. Ajuste depuis les 1ers points."""
    x0, y0 = data[0]
    x1, y1 = data[1] if len(data) > 1 else (None, None)

    # constante : y = c
    yield ("constante", 1, {"c": y0}, (lambda x, c=y0: c))

    # proportionnel : y = a·x
    if x0 != 0:
        a = y0 / x0
        yield ("proportionnel", 1, {"a": a}, (lambda x, a=a: a * x))

    # inverse : y = a/x
    if x0 != 0:
        a = y0 * x0
        yield ("inverse", 1, {"a": a}, (lambda x, a=a: a / x if x != 0 else None))

    # carré : y = a·x²
    if x0 != 0:
        a = y0 / (x0 * x0)
        yield ("carré", 1, {"a": a}, (lambda x, a=a: a * x * x))

    # cube : y = a·x³
    if x0 != 0:
        a = y0 / (x0 ** 3)
        yield ("cube", 1, {"a": a}, (lambda x, a=a: a * x ** 3))

    # racine : y = a·√x
    if x0 > 0:
        a = y0 / math.sqrt(x0)
        yield ("racine", 1, {"a": a}, (lambda x, a=a: a * math.sqrt(x) if x >= 0 else None))

    # linéaire : y = a·x + b (2 params -> 2 points à x distincts)
    if x1 is not None and x1 != x0:
        a = (y1 - y0) / (x1 - x0)
        b = y0 - a * x0
        yield ("linéaire", 2, {"a": a, "b": b}, (lambda x, a=a, b=b: a * x + b))


def decouvre(data, tol: float = 1e-6):
    """Cherche la loi la plus simple y=f(x) qui colle à TOUS les points de `data` (liste de (x, y)). Renvoie
    {forme, params, predit} ou None (aucune loi simple ne colle partout / trop peu de points). FAUX=0."""
    data = [(float(x), float(y)) for x, y in data]
    n = len(data)
    if n < 2:
        return None                              # 1 point ne détermine aucune loi vérifiable -> abstention
    for forme, nparams, params, predit in _gabarits(data):
        if n <= nparams:
            continue                             # pas de point de vérification held-out -> on ne conclut pas
        if _colle(predit, data, tol):
            return {"forme": forme, "params": params, "predit": predit}
    return None                                  # aucune loi simple ne colle partout -> HORS honnête
