"""
TRIANGULATION — brique Vague 6 (accord de deux dérivations INDÉPENDANTES = corroboration non-circulaire).

POURQUOI : une valeur obtenue par deux chemins indépendants qui CONCORDENT est bien plus crédible qu'une seule
dérivation. À l'inverse, un désaccord signale une erreur quelque part. La clé : les deux dérivations doivent être
INDÉPENDANTES (méthodes/intrants distincts) — sinon l'accord est trivial et ne corrobore rien (circularité).

MODÈLE : deux valeurs, chacune avec l'étiquette de sa méthode ; on vérifie (a) que les méthodes DIFFÈRENT, (b) que
les valeurs concordent dans la tolérance.

FAUX=0 :
  • Si les deux méthodes sont IDENTIQUES -> `non_independant` (pas de corroboration : on ne se confirme pas soi-même).
  • Accord dans la tolérance -> `corrobore` ; désaccord -> `discorde` (une erreur à débusquer, jamais ignorée).
  • Valeurs non finies -> `indetermine` (jamais un accord fabriqué).
Stdlib pur, déterministe, souverain.
"""
from __future__ import annotations

import math

CORROBORE = "corrobore"
DISCORDE = "discorde"
NON_INDEPENDANT = "non_independant"
INDETERMINE = "indetermine"


def triangule(valeur_a, methode_a: str, valeur_b, methode_b: str, tol_rel: float = 1e-6):
    """Confronte deux dérivations indépendantes d'une même grandeur. Renvoie un des verdicts CORROBORE / DISCORDE /
    NON_INDEPENDANT / INDETERMINE, jamais un accord supposé."""
    if methode_a == methode_b:
        return NON_INDEPENDANT               # même méthode -> accord trivial, ne corrobore rien
    try:
        a, b = float(valeur_a), float(valeur_b)
    except (TypeError, ValueError):
        return INDETERMINE
    if not (math.isfinite(a) and math.isfinite(b)):
        return INDETERMINE
    echelle = max(abs(a), abs(b), 1e-12)
    return CORROBORE if abs(a - b) <= tol_rel * echelle else DISCORDE


def confirme(valeur_a, methode_a, valeur_b, methode_b, tol_rel: float = 1e-6) -> bool:
    """True SEULEMENT si deux méthodes INDÉPENDANTES concordent. Tout le reste (désaccord, même méthode, indéfini)
    -> False (pas de corroboration abusive)."""
    return triangule(valeur_a, methode_a, valeur_b, methode_b, tol_rel) == CORROBORE
