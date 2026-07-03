"""BATTERIES / STOCKAGE ÉLECTRIQUE — primitives EXACTES, directement appelables, FAUX=0 (mission formule/concept).

Posture (identique à `physique`/`chimie`/`maths_discretes`) : le MÉCANISME est exact (relations de définition de
l'électrochimie de stockage), et l'abstention est STRUCTURELLE — toute entrée invalide lève `ValueError`
(jamais un résultat faux). Conservateur : faux négatif (abstention) toléré, faux POSITIF interdit.

Couvre le sujet borné « Stockage (batteries) » :
  • energie_wh(V, Ah)            = V·Ah                  -> énergie stockée (Wh)        [ex. 12 V · 100 Ah = 1200 Wh]
  • capacite_Ah_depuis_energie  = Wh / V                -> capacité (Ah)                [inverse de energie_wh]
  • courant_c_rate(Ah, C)       = Ah·C                  -> courant de (dé)charge (A)    [ex. 100 Ah à 2C = 200 A]
  • temps_charge(Ah, I)         = Ah / I                -> durée idéale (h)             [ex. 100 Ah à 50 A = 2 h]
  • rendement_energetique(o,i)  = e_out / e_in          -> rendement (sans unité, ≤ 1)  [ex. 90/100 = 0.9]

DOMAINE : toutes les grandeurs physiques (tension, capacité, courant, C-rate, énergie) sont STRICTEMENT POSITIVES ;
une valeur ≤ 0 lève ValueError. Le rendement est borné par la conservation de l'énergie : e_out ≤ e_in, donc un
rendement > 1 (sur-unité) est physiquement impossible et lève ValueError.

Les sorties flottantes sont arrondies à 10 chiffres significatifs (précision honnête — ces relations sont des
définitions, l'arrondi ne masque aucune incertitude mais évite un bruit binaire trompeur).
Vérifié en adverse par `valide_batteries.py` (ancres externes connues + soundness : entrée invalide -> ValueError).
"""
from __future__ import annotations

_SIG = 10


def _sig(x: float, n: int = _SIG) -> float:
    """Arrondit à n chiffres significatifs (précision honnête, indépendante de la magnitude)."""
    if x == 0:
        return 0.0
    return float(f"{x:.{n}g}")


def _pos(*xs) -> None:
    """Garde de domaine : chaque grandeur doit être un réel STRICTEMENT positif (bool/str/≤0 -> ValueError)."""
    for x in xs:
        if isinstance(x, bool) or not isinstance(x, (int, float)):
            raise ValueError(f"nombre réel attendu, reçu {x!r}")
        if not (x > 0):
            raise ValueError(f"grandeur strictement positive attendue, reçu {x!r}")


def energie_wh(tension_V: float, capacite_Ah: float) -> float:
    """Énergie stockée (Wh) = tension (V) × capacité (Ah). Ex. : 12 V · 100 Ah = 1200 Wh."""
    _pos(tension_V, capacite_Ah)
    return _sig(tension_V * capacite_Ah)


def capacite_Ah_depuis_energie(energie_Wh: float, tension_V: float) -> float:
    """Capacité (Ah) = énergie (Wh) / tension (V). Inverse de energie_wh."""
    _pos(energie_Wh, tension_V)
    return _sig(energie_Wh / tension_V)


def courant_c_rate(capacite_Ah: float, c_rate: float) -> float:
    """Courant de (dé)charge (A) = capacité (Ah) × C-rate. Ex. : 100 Ah à 2C = 200 A."""
    _pos(capacite_Ah, c_rate)
    return _sig(capacite_Ah * c_rate)


def temps_charge(capacite_Ah: float, courant_A: float) -> float:
    """Durée idéale de charge (h) = capacité (Ah) / courant (A). Ex. : 100 Ah à 50 A = 2 h."""
    _pos(capacite_Ah, courant_A)
    return _sig(capacite_Ah / courant_A)


def rendement_energetique(e_out: float, e_in: float) -> float:
    """Rendement énergétique (aller-retour) = énergie restituée / énergie fournie. Borné par 1 (e_out ≤ e_in).

    Un rendement > 1 violerait la conservation de l'énergie -> ValueError (jamais un résultat « sur-unité »).
    """
    _pos(e_out, e_in)
    if e_out > e_in:
        raise ValueError(f"rendement > 1 impossible (e_out={e_out!r} > e_in={e_in!r})")
    return _sig(e_out / e_in)
