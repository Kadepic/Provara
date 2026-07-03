"""DEUXIÈME PRINCIPE (ENTROPIE) — primitives thermodynamiques EXACTES, directement appelables, FAUX=0
(mission formule/concept 2026-06-29).

Posture (identique à `physique`/`chimie`/`maths_discretes`) : le MÉCANISME est exact (définition de Clausius
de la variation d'entropie d'un transfert réversible de chaleur), et l'abstention est STRUCTURELLE — toute
entrée hors-domaine (température ≤ 0 K, type non numérique, valeur non finie) lève `ValueError`, JAMAIS un
résultat faux. Conservateur : un faux négatif (abstention) est toléré, un faux POSITIF est interdit.

MÉCANISME (deuxième principe de la thermodynamique) :
  • variation_entropie(Q, T) = Q / T
        Variation d'entropie d'un réservoir à température T (Kelvin) recevant la chaleur Q (J), de façon
        réversible (transfert isotherme). Q > 0 → l'entropie du réservoir augmente ; Q < 0 → elle diminue.
        Unité : J/K. Domaine : T > 0 (échelle Kelvin absolue ; T ≤ 0 K impossible — 3ᵉ principe).

  • entropie_univers(Q, T_chaud, T_froid) = Q/T_froid − Q/T_chaud
        Variation d'entropie de l'UNIVERS (les deux réservoirs) lorsqu'une chaleur Q (> 0) est transférée
        du réservoir chaud (T_chaud) vers le réservoir froid (T_froid). Le froid GAGNE Q (+Q/T_froid), le
        chaud PERD Q (−Q/T_chaud). Pour Q > 0, le résultat est ≥ 0 ssi T_chaud ≥ T_froid : c'est l'énoncé
        de Clausius (la chaleur ne passe spontanément que du chaud vers le froid). Un transfert vers un
        réservoir PLUS chaud (T_froid > T_chaud, ou Q < 0) donne ΔS_univers < 0 : impossible spontanément.

  • spontane(delta_S_univers) = (delta_S_univers > 0)
        Critère d'évolution : un processus est spontané (irréversible) ssi l'entropie de l'univers AUGMENTE
        strictement. ΔS = 0 → transformation réversible (équilibre), NON spontanée au sens strict.
        ΔS < 0 → impossible (violerait le deuxième principe).

La sortie numérique est arrondie à 10 chiffres significatifs (précision honnête : pas de faux exact au-delà).
Vérifié en adverse par `valide_entropie_thermo.py` (ancres externes + soundness : domaine invalide -> ValueError).
"""
from __future__ import annotations

import math

_CHIFFRES_SIGNIFICATIFS = 10


def _arrondi(x: float) -> float:
    """Arrondi à 10 chiffres significatifs (précision honnête)."""
    if x == 0.0:
        return 0.0
    return round(x, _CHIFFRES_SIGNIFICATIFS - 1 - int(math.floor(math.log10(abs(x)))))


def _reel(x, nom: str) -> float:
    """Coerce un réel fini ; refuse bool, non-numérique, NaN/inf."""
    if isinstance(x, bool) or not isinstance(x, (int, float)):
        raise ValueError(f"{nom} : réel attendu, reçu {x!r}")
    xf = float(x)
    if not math.isfinite(xf):
        raise ValueError(f"{nom} : valeur non finie {x!r}")
    return xf


def _temperature(T, nom: str = "T") -> float:
    """Température absolue : réel fini > 0 (Kelvin). T ≤ 0 K -> ValueError."""
    Tf = _reel(T, nom)
    if Tf <= 0.0:
        raise ValueError(f"{nom} : température absolue > 0 K requise, reçu {Tf}")
    return Tf


def variation_entropie(Q, T) -> float:
    """ΔS = Q/T (J/K) d'un réservoir à T (K) recevant Q (J) de façon réversible. T > 0 requis."""
    Qf = _reel(Q, "Q")
    Tf = _temperature(T, "T")
    return _arrondi(Qf / Tf)


def entropie_univers(Q, T_chaud, T_froid) -> float:
    """ΔS_univers = Q/T_froid − Q/T_chaud pour un transfert de chaleur Q du chaud vers le froid.
    T_chaud > 0 et T_froid > 0 requis. ≥ 0 ssi (pour Q>0) T_chaud ≥ T_froid (énoncé de Clausius)."""
    Qf = _reel(Q, "Q")
    Tc = _temperature(T_chaud, "T_chaud")
    Tf = _temperature(T_froid, "T_froid")
    return _arrondi(Qf / Tf - Qf / Tc)


def spontane(delta_S_univers) -> bool:
    """Critère du deuxième principe : spontané ssi ΔS_univers > 0 (strict). ΔS = 0 → réversible (non spontané)."""
    dS = _reel(delta_S_univers, "delta_S_univers")
    return dS > 0.0
