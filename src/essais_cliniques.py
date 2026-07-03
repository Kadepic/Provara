"""
ESSAIS CLINIQUES — épidémiologie clinique (mesures d'effet EXACTES).

Même posture que `physique` / `chimie` / `aerodynamique` (la réalité juge, jamais un faux) :
  • Le MÉCANISME (définitions standard des mesures d'effet) est EXACT — épidémiologie établie.
  • La sortie ratio/différence est ARRONDIE à 6 chiffres significatifs — précision HONNÊTE.
  • Le NNT est un ENTIER (arrondi SUPÉRIEUR de 1/RRA, convention clinique).
  • Toute entrée hors domaine (incidence ∉ [0,1], dénominateur nul, RRA ≤ 0…) lève ValueError
    (ABSTENTION) — jamais un nombre absurde, jamais un faux.

DÉFINITIONS (établies — épidémiologie clinique, tables 2×2) :
  - Risque relatif       RR  = Ie / Ine                  (—)   Ie, Ine = incidences (proportions)
  - Réduction du risque  RRA = Rc − Rt                   (—)   Rc, Rt = risques contrôle / traité
    absolue (ARR)              (RRA < 0 = augmentation, calcul exact, valeur légitime)
  - Nombre de sujets     NNT = ⌈ 1 / RRA ⌉               (entier)  RRA ∈ (0,1]
    à traiter (NNT)
  - Odds ratio (table    OR  = (a·d) / (b·c)             (—)
    2×2 a,b,c,d)              a = exposés-cas, b = exposés-témoins, c = non-exposés-cas, d = non-exposés-témoins

PROPRIÉTÉS structurelles (vérifiées en adverse, non circulaires) :
  • NNT round-trip : si 1/RRA est entier, NNT·RRA == 1 ;
  • OR invariant par transposition de la table : OR(a,b,c,d) == OR(d,c,b,a) ;
  • OR réciproque : OR(a,b,c,d)·OR(b,a,d,c) == 1.

SOUNDNESS (vérifiée en adverse par `valide_essais_cliniques.py`) :
  - incidence / risque ∉ [0,1]            -> ValueError ;
  - dénominateur nul (Ine = 0, b·c = 0)   -> ValueError ;
  - RRA ≤ 0 ou RRA > 1 (NNT)              -> ValueError ;
  - effectif de cellule (OR) non entier / négatif / non fini -> ValueError ;
  - tout argument non numérique / booléen / non fini -> ValueError ;
  - déterministe ; conservateur (abstention tolérée, faux POSITIF interdit).
"""
from __future__ import annotations

import math

SOURCE = "épidémiologie clinique (RR, RRA, NNT, OR — tables 2×2, mesures d'effet standard)"

_CHIFFRES_SIGNIFICATIFS = 6


def _sig(x: float, n: int = _CHIFFRES_SIGNIFICATIFS) -> float:
    """Arrondit à n chiffres significatifs (précision honnête, indépendante de la magnitude)."""
    if x == 0:
        return 0.0
    return float(f"{x:.{n}g}")


def _num(x, nom: str) -> float:
    """Convertit x en float fini en REFUSANT booléens / non numériques / non finis -> ValueError."""
    if isinstance(x, bool) or not isinstance(x, (int, float)):
        raise ValueError(f"{nom} non numérique : {x!r}")
    f = float(x)
    if not math.isfinite(f):
        raise ValueError(f"{nom} non fini : {x!r}")
    return f


def _proportion(x, nom: str) -> float:
    """Valide une proportion (incidence / risque) ∈ [0,1] ; sinon ValueError."""
    f = _num(x, nom)
    if f < 0.0 or f > 1.0:
        raise ValueError(f"{nom} doit être une proportion ∈ [0,1] : {f!r}")
    return f


def _compte(x, nom: str) -> int:
    """Valide un effectif de cellule : entier (ou flottant entier) >= 0 ; sinon ValueError."""
    if isinstance(x, bool):
        raise ValueError(f"{nom} (effectif) ne peut être un booléen : {x!r}")
    if isinstance(x, int):
        n = x
    elif isinstance(x, float):
        if not math.isfinite(x) or not x.is_integer():
            raise ValueError(f"{nom} (effectif) doit être un entier : {x!r}")
        n = int(x)
    else:
        raise ValueError(f"{nom} (effectif) non numérique : {x!r}")
    if n < 0:
        raise ValueError(f"{nom} (effectif) doit être >= 0 : {n!r}")
    return n


def risque_relatif(incidence_exposes, incidence_non_exposes) -> float:
    """Risque relatif RR = Ie / Ine.

    Ie, Ine = incidences (proportions ∈ [0,1]). Ine = 0 (dénominateur nul) -> ValueError.
    RR > 1 : surrisque ; RR < 1 : protection ; RR = 1 : pas d'effet.
    """
    ie = _proportion(incidence_exposes, "incidence_exposes")
    ine = _proportion(incidence_non_exposes, "incidence_non_exposes")
    if ine == 0.0:
        raise ValueError("incidence_non_exposes nulle : risque relatif indéfini (division par zéro)")
    return _sig(ie / ine)


def reduction_risque_absolue(risque_controle, risque_traite) -> float:
    """Réduction du risque absolue RRA = Rc − Rt.

    Rc, Rt = risques (proportions ∈ [0,1]). RRA < 0 = augmentation du risque (valeur exacte, légitime).
    """
    rc = _proportion(risque_controle, "risque_controle")
    rt = _proportion(risque_traite, "risque_traite")
    return _sig(rc - rt)


def nombre_sujets_a_traiter(rra) -> int:
    """Nombre de sujets à traiter NNT = ⌈ 1 / RRA ⌉ (entier, arrondi supérieur).

    RRA ∈ (0,1]. RRA ≤ 0 (pas de bénéfice) ou RRA > 1 (impossible pour des proportions) -> ValueError.
    """
    r = _num(rra, "rra")
    if r <= 0.0:
        raise ValueError("RRA doit être > 0 pour un NNT (RRA ≤ 0 = pas de bénéfice à traiter)")
    if r > 1.0:
        raise ValueError("RRA doit être ≤ 1 (différence de proportions)")
    # round(…, 9) absorbe les artefacts flottants (1/0.05 = 19.9999999996) avant le plafond entier.
    return math.ceil(round(1.0 / r, 9))


def odds_ratio(a, b, c, d) -> float:
    """Odds ratio OR = (a·d) / (b·c) à partir d'une table 2×2.

    a = exposés-cas, b = exposés-témoins, c = non-exposés-cas, d = non-exposés-témoins.
    Effectifs entiers >= 0. b = 0 ou c = 0 (dénominateur nul) -> ValueError.
    """
    a = _compte(a, "a")
    b = _compte(b, "b")
    c = _compte(c, "c")
    d = _compte(d, "d")
    if b == 0 or c == 0:
        raise ValueError("b·c = 0 : odds ratio indéfini (division par zéro)")
    return _sig((a * d) / (b * c))


def _p_essais_cliniques() -> bool:
    """Preuve auto-portée : vrai sur cas connus + abstention sur entrée invalide."""
    import essais_cliniques as M

    def _leve_v(fn, *a, **k) -> bool:
        try:
            fn(*a, **k)
            return False
        except ValueError:
            return True
        except Exception:
            return False

    return (
        abs(M.risque_relatif(0.15, 0.10) - 1.5) < 1e-9
        and abs(M.risque_relatif(0.20, 0.40) - 0.5) < 1e-9
        and abs(M.risque_relatif(0.10, 0.10) - 1.0) < 1e-9
        and abs(M.reduction_risque_absolue(0.20, 0.15) - 0.05) < 1e-9
        and abs(M.reduction_risque_absolue(0.10, 0.15) - (-0.05)) < 1e-9
        and M.nombre_sujets_a_traiter(0.05) == 20
        and M.nombre_sujets_a_traiter(0.03) == 34
        and abs(M.odds_ratio(20, 80, 10, 90) - 2.25) < 1e-9
        and abs(M.odds_ratio(10, 10, 10, 10) - 1.0) < 1e-9
        and _leve_v(M.risque_relatif, 0.15, 0.0)        # dénominateur nul
        and _leve_v(M.risque_relatif, 1.5, 0.10)        # incidence > 1
        and _leve_v(M.nombre_sujets_a_traiter, 0.0)     # RRA <= 0
        and _leve_v(M.odds_ratio, 20, 0, 10, 90)        # b = 0 -> indéfini
    )
