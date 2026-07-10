"""
CONVERGENCE D'UNE SÉRIE — critères GÉNÉRAUX appliqués à un terme général u : n -> u(n) (PARTIE I, B-NEC).

Complément de `series_calcul` (qui ne traite QUE les familles fermées géométrique et Riemann, avec sommes
EXACTES sur ℚ). Ici on couvre les CRITÈRES classiques d'analyse, appliqués à un terme général fourni comme
FONCTION de l'indice n. Mécanismes (théorèmes exacts) :
  • Critère de d'ALEMBERT (règle du rapport) : soit L = lim |u(n+1)/u(n)|. Si L < 1 la série Σu converge
    absolument, si L > 1 elle diverge, si L = 1 le critère est INDÉTERMINÉ (aucune conclusion).
  • Critère de CAUCHY (règle de la racine) : soit L = lim |u(n)|^(1/n). Même trichotomie (L<1 conv., L>1 div.,
    L=1 indéterminé).
  • Critère des séries ALTERNÉES (LEIBNIZ) : si a_n = |u(n)| DÉCROÎT et a_n -> 0, alors Σ(-1)^n a_n converge.
  • Critère de COMPARAISON : si 0 ≤ u(n) ≤ v(n) pour tout n et si Σv converge (FAIT établi passé en argument),
    alors Σu converge.
  • Condition NÉCESSAIRE : si u(n) NE tend PAS vers 0, alors Σu DIVERGE. La réciproque est FAUSSE : u(n) -> 0
    n'implique RIEN (piège de la série harmonique Σ1/n). ATTENTION : depuis des données FINIES on ne peut
    conclure 'diverge' que si le terme s'est numériquement STABILISÉ à une valeur non nulle ; une fenêtre
    encore CROISSANTE ne prouve rien (Σ n·rⁿ avec |r|<1 : le terme croît d'abord puis décroît vers 0).
  • converge_riemann(alpha) et converge_geometrique(r) sont DÉLÉGUÉS à `series_calcul` (aucune duplication).

POSTURE FAUX=0 (capitale — HONNÊTETÉ NUMÉRIQUE) : d'Alembert et Cauchy sont estimés NUMÉRIQUEMENT sur un
horizon FINI. On ne peut JAMAIS prouver L ≠ 1 depuis des données finies. Le module rend donc 'indetermine'
DÈS QUE l'estimation approche le cas limite 1 — soit parce que la valeur estimée tombe dans une bande autour de
1, soit parce que la suite des estimations est encore en TRAIN de monter/descendre VERS 1 (tendance détectée).
Un verdict 'converge' issu d'une limite estimée < 1 est un verdict SOUS HYPOTHÈSE de régularité de u, PAS une
preuve. En revanche, pour les familles CONNUES (géométrique |r|<1, Riemann α>1, alternée harmonique), le
verdict EST une preuve. Le verdict 'diverge' via la condition nécessaire n'est rendu que si le terme s'est
numériquement STABILISÉ à une valeur non nulle sur l'horizon (queue dans une bande relative étroite, bornée
loin de 0) — pour un terme qui converge vraiment vers L≠0 (ex. n/(n+1)→1) c'est une preuve de divergence, sous
l'hypothèse que la stabilisation observée persiste. Une fenêtre encore CROISSANTE ou évolutive ne prouve NI la
convergence NI la divergence (ex. n/1.01ⁿ, série CONVERGENTE dont le terme croît puis décroît vers 0) : le
module s'abstient ('indetermine'). C'est le refus explicite du faux positif de divergence.

GARANTIES (vérifiées en adverse par `valide_convergence_series.py`) :
  - u non appelable -> ValueError ; u(n) non fini (NaN/inf) ou non réel -> ValueError ;
  - iterations < 10 -> ValueError (horizon trop court pour estimer une limite) ;
  - n0 non entier ≥ 1 -> ValueError ; bool/str/NaN/inf en argument -> ValueError ;
  - le cas limite L ≈ 1 est rendu 'indetermine', JAMAIS tranché (anti faux positif) ;
  - u(n) -> 0 ne produit JAMAIS 'converge' (piège harmonique) ; 'diverge' UNIQUEMENT sur terme stabilisé ≠ 0 ;
  - une fenêtre finie CROISSANTE (terme d'une série pourtant convergente) ne rend JAMAIS 'diverge' (anti FP) ;
  - conservateur : faux négatif (abstention 'indetermine') toléré, faux POSITIF interdit ; déterministe.

Toutes les fonctions sont PURES et déterministes ; stdlib uniquement (math), + délégation à `series_calcul`.
"""
from __future__ import annotations

import math
from fractions import Fraction

import series_calcul

SOURCE = ("critères classiques de convergence des séries : règle de d'Alembert (rapport), règle de Cauchy "
          "(racine), critère de Leibniz (séries alternées), comparaison, condition nécessaire uₙ→0 — "
          "analyse réelle standard")

_CHIFFRES_SIGNIFICATIFS = 10

# Demi-largeur de la bande d'INDÉTERMINATION autour du cas limite L = 1 (règles rapport/racine).
# Une estimation dans [1-_MARGE, 1+_MARGE] est rendue 'indetermine' : on ne tranche jamais près de 1.
_MARGE = 0.1
# Seuil de TENDANCE : si les estimations montent (resp. descendent) vers 1 de plus de ce pas sur la moitié
# finale de l'horizon, on refuse de conclure (la limite pourrait valoir 1). Attrape Σ1/n même à petit n.
_TREND_TOL = 1e-3
# Seuils de la condition nécessaire (uₙ→0) : en-dessous de _ZERO on considère le terme numériquement nul ;
# _NONZERO est le PLANCHER : toute la queue doit rester au-dessus pour parler de terme borné loin de 0.
_ZERO = 1e-9
_NONZERO = 1e-6
# Largeur relative MAX de la bande de STABILISATION : on ne conclut 'diverge' (terme ↛ 0) que si toute la
# queue tient dans (max-min) ≤ _CONV_REL·max — i.e. le terme a numériquement CONVERGÉ à une valeur non nulle.
# Une queue encore croissante/évolutive (spread relatif large) NE stabilise PAS -> abstention (anti faux positif).
_CONV_REL = 0.1


# ── HELPERS ─────────────────────────────────────────────────────────────────────────────────────────────────────
def _sig(x: float, n: int = _CHIFFRES_SIGNIFICATIFS) -> float:
    """Arrondit à n chiffres significatifs (précision honnête d'une estimation flottante)."""
    if x == 0:
        return 0.0
    return float(f"{x:.{n}g}")


def _exige_appelable(u) -> None:
    if not callable(u) or isinstance(u, bool):
        raise ValueError("terme général u invalide : une fonction appelable u(n) est requise")


def _exige_entier(x, mini: int, nom: str) -> int:
    if not isinstance(x, int) or isinstance(x, bool) or x < mini:
        raise ValueError(f"{nom} invalide : un entier ≥ {mini} est requis")
    return x


def _exige_iterations(iterations) -> int:
    if not isinstance(iterations, int) or isinstance(iterations, bool) or iterations < 10:
        raise ValueError("iterations invalide : un entier ≥ 10 est requis (horizon trop court sinon)")
    return iterations


def _valeur(u, n) -> float:
    """u(n) évalué et validé : réel FINI (bool/str/complexe/NaN/inf -> ValueError). Renvoie un float."""
    try:
        y = u(n)
    except ValueError:
        raise
    except Exception as e:  # noqa: BLE001 — toute autre erreur d'évaluation = abstention structurelle
        raise ValueError(f"u({n}) inévaluable : {e!r}")
    if isinstance(y, bool):
        raise ValueError(f"u({n}) booléen refusé (True n'est pas 1)")
    if isinstance(y, Fraction):
        y = float(y)
    elif isinstance(y, int):
        y = float(y)
    elif isinstance(y, float):
        pass
    else:
        raise ValueError(f"u({n}) non réel : reçu {type(y).__name__}")
    if not math.isfinite(y):
        raise ValueError(f"u({n}) non fini (NaN/inf) : abstention")
    return y


def _classifier_limite(estimations):
    """Trichotomie honnête du critère du rapport/racine à partir des estimations successives de |L|.

    Renvoie (limite_estimee_arrondie, verdict). 'converge' SEULEMENT si l'estimation est nettement < 1 ET ne
    monte pas vers 1 ; 'diverge' SEULEMENT si nettement > 1 ET ne descend pas vers 1 ; sinon 'indetermine'.
    Le verdict 'converge'/'diverge' n'est donc JAMAIS rendu quand la limite pourrait valoir 1."""
    L = estimations[-1]
    tail = estimations[len(estimations) // 2:] or estimations
    pente = tail[-1] - tail[0]
    if L < 1.0:
        if pente > _TREND_TOL:            # encore en train de MONTER vers 1 (par en dessous) -> indécidable
            verdict = "indetermine"
        elif L < 1.0 - _MARGE:
            verdict = "converge"
        else:                              # dans la bande [1-marge, 1[
            verdict = "indetermine"
    elif L > 1.0:
        if pente < -_TREND_TOL:            # encore en train de DESCENDRE vers 1 (par au dessus) -> indécidable
            verdict = "indetermine"
        elif L > 1.0 + _MARGE:
            verdict = "diverge"
        else:                              # dans la bande ]1, 1+marge]
            verdict = "indetermine"
    else:                                  # exactement 1
        verdict = "indetermine"
    return _sig(L), verdict


# ── (a) RÈGLE DE D'ALEMBERT (rapport) ─────────────────────────────────────────────────────────────────────────--
def critere_dalembert(u, n0: int = 1, iterations: int = 100) -> dict:
    """Règle du rapport : estime L = lim |u(n+1)/u(n)| et renvoie {'limite_estimee', 'verdict'}.

    verdict ∈ {'converge', 'diverge', 'indetermine'}. Le cas limite L ≈ 1 est rendu 'indetermine' (JAMAIS
    tranché). Terme nul rencontré (rapport indéfini) -> ValueError. u non appelable / u(n) non fini -> ValueError."""
    _exige_appelable(u)
    n0 = _exige_entier(n0, 1, "n0")
    iterations = _exige_iterations(iterations)
    estimations = []
    for k in range(iterations):
        n = n0 + k
        un = _valeur(u, n)
        un1 = _valeur(u, n + 1)
        if un == 0.0:
            raise ValueError(f"terme u({n}) = 0 : règle du rapport inapplicable (division par zéro)")
        estimations.append(abs(un1 / un))
    L, verdict = _classifier_limite(estimations)
    return {"limite_estimee": L, "verdict": verdict}


# ── (b) RÈGLE DE CAUCHY (racine) ──────────────────────────────────────────────────────────────────────────────--
def critere_cauchy(u, n0: int = 1, iterations: int = 100) -> dict:
    """Règle de la racine : estime L = lim |u(n)|^(1/n) et renvoie {'limite_estimee', 'verdict'}.

    Même trichotomie que d'Alembert ; L ≈ 1 -> 'indetermine'. u non appelable / u(n) non fini -> ValueError."""
    _exige_appelable(u)
    n0 = _exige_entier(n0, 1, "n0")
    iterations = _exige_iterations(iterations)
    estimations = []
    for k in range(iterations):
        n = n0 + k
        un = _valeur(u, n)
        estimations.append(abs(un) ** (1.0 / n))
    L, verdict = _classifier_limite(estimations)
    return {"limite_estimee": L, "verdict": verdict}


# ── (f) CONDITION NÉCESSAIRE : terme général -> 0 ? ───────────────────────────────────────────────────────────--
def terme_general_tend_vers_zero(u, n0: int = 1, iterations: int = 100) -> dict:
    """Condition NÉCESSAIRE de convergence. Renvoie {'tend_vers_zero', 'limite_estimee', 'verdict'}.

    On ne rend 'diverge' que si |u(n)| s'est numériquement STABILISÉ à une valeur non nulle sur la queue de
    l'horizon (bande relative ≤ _CONV_REL, plancher ≥ _NONZERO) -> le terme ne tend pas vers 0 -> Σ DIVERGE
    (ex. n/(n+1)→1). Une fenêtre encore CROISSANTE/évolutive ne prouve RIEN -> 'indetermine' (ex. n/1.01ⁿ,
    série CONVERGENTE dont le terme croît puis décroît vers 0 : REFUS explicite du faux positif). Si |u(n)|
    décroît vers de petites valeurs -> 'indetermine' (condition satisfaite mais NON suffisante : piège Σ1/n).
    JAMAIS 'converge' ici. 'tend_vers_zero' vaut False (divergence conclue), True (décroissance présumée ->0),
    ou None (évolution non concluante, on ne sait pas). u/u(n) invalide -> ValueError."""
    _exige_appelable(u)
    n0 = _exige_entier(n0, 1, "n0")
    iterations = _exige_iterations(iterations)
    mags = [abs(_valeur(u, n0 + k)) for k in range(iterations)]
    tail = mags[len(mags) // 2:] or mags
    dernier = mags[-1]
    tmin = min(tail)
    tmax = max(tail)
    # (1) terme numériquement NUL : condition nécessaire satisfaite (mais NON suffisante -> jamais 'converge').
    if dernier <= _ZERO:
        return {"tend_vers_zero": True, "limite_estimee": _sig(dernier), "verdict": "indetermine"}
    # (2) terme STABILISÉ à une valeur non nulle : toute la queue tient dans une bande relative étroite ET est
    #     bornée loin de 0 -> uₙ ↛ 0 -> Σuₙ DIVERGE. SEUL cas où l'on tranche 'diverge'. Une fenêtre encore
    #     croissante (spread relatif large) n'est PAS stabilisée : elle ne prouve rien (ex. n/1.01ⁿ convergente).
    if tmin >= _NONZERO and (tmax - tmin) <= _CONV_REL * tmax:
        return {"tend_vers_zero": False, "limite_estimee": _sig(dernier), "verdict": "diverge"}
    # (3) queue DÉCROISSANTE vers de petites valeurs -> présumé -> 0 (piège harmonique : Σ1/n, uₙ→0, Σ diverge).
    non_croissante = all(tail[i + 1] <= tail[i] + 1e-15 for i in range(len(tail) - 1))
    if non_croissante:
        return {"tend_vers_zero": True, "limite_estimee": _sig(dernier), "verdict": "indetermine"}
    # (4) queue ni stabilisée-non-nulle ni décroissante (encore croissante/évolutive) : une fenêtre finie
    #     croissante ne prouve NI la convergence NI la divergence du terme -> abstention TOTALE (anti faux positif).
    return {"tend_vers_zero": None, "limite_estimee": _sig(dernier), "verdict": "indetermine"}


# ── (c) CRITÈRE DES SÉRIES ALTERNÉES (LEIBNIZ) ────────────────────────────────────────────────────────────────--
def critere_series_alternees(u, n0: int = 1, iterations: int = 100) -> dict:
    """Critère de Leibniz sur Σ(-1)ⁿ aₙ (u = terme général AVEC son signe alterné).

    Vérifie sur l'horizon fini [n0, n0+iterations] : (1) alternance des signes, (2) décroissance de aₙ=|u(n)|,
    (3) aₙ -> 0. Si les trois tiennent -> verdict 'converge' MARQUÉ 'verifie_jusqua' = N (sous hypothèse de
    régularité au-delà ; pour l'alternée harmonique c'est une preuve). Sinon 'indetermine'. Renvoie
    {'verdict', 'verifie_jusqua', 'alternee', 'decroissante', 'tend_vers_zero'}. u/u(n) invalide -> ValueError."""
    _exige_appelable(u)
    n0 = _exige_entier(n0, 1, "n0")
    iterations = _exige_iterations(iterations)
    vals = [_valeur(u, n0 + k) for k in range(iterations)]
    mags = [abs(v) for v in vals]
    N = n0 + iterations - 1
    alternee = all(vals[i] * vals[i + 1] < 0 for i in range(len(vals) - 1))
    decroissante = all(mags[i + 1] <= mags[i] + 1e-15 for i in range(len(mags) - 1))
    # aₙ -> 0 : décroissante et dernier terme petit (honnête : vérifié sur horizon fini).
    tend_zero = decroissante and (mags[-1] <= mags[0] * 0.5 or mags[-1] <= _ZERO)
    verdict = "converge" if (alternee and decroissante and tend_zero) else "indetermine"
    return {
        "verdict": verdict,
        "verifie_jusqua": N,
        "alternee": alternee,
        "decroissante": decroissante,
        "tend_vers_zero": tend_zero,
    }


# ── (d) CRITÈRE DE COMPARAISON ────────────────────────────────────────────────────────────────────────────────--
def critere_comparaison(u, v, v_converge, n0: int = 1, iterations: int = 100) -> dict:
    """Comparaison : si 0 ≤ u(n) ≤ v(n) sur l'horizon ET si Σv converge (FAIT établi passé en `v_converge`),
    alors Σu converge. Renvoie {'verdict', 'domination_verifiee_jusqua'}.

    verdict = 'converge' si la domination 0≤u≤v tient sur [n0, N] et v_converge est True (sous hypothèse que la
    domination persiste ; pour un majorant Riemann/géométrique c'est une preuve). Sinon 'indetermine' (une
    comparaison avec un majorant divergent, ou une domination violée, ne conclut RIEN). v_converge doit être un
    bool (fait logique établi, non une mesure). u/v/u(n)/v(n) invalide -> ValueError."""
    _exige_appelable(u)
    _exige_appelable(v)
    if not isinstance(v_converge, bool):
        raise ValueError("v_converge invalide : un booléen (fait établi 'Σv converge') est requis")
    n0 = _exige_entier(n0, 1, "n0")
    iterations = _exige_iterations(iterations)
    N = n0 + iterations - 1
    domination = True
    for k in range(iterations):
        n = n0 + k
        un = _valeur(u, n)
        vn = _valeur(v, n)
        if not (0.0 <= un <= vn):
            domination = False
            break
    verdict = "converge" if (domination and v_converge) else "indetermine"
    return {"verdict": verdict, "domination_verifiee_jusqua": N}


# ── (e) DÉLÉGATIONS À series_calcul (aucune duplication) ──────────────────────────────────────────────────────--
def converge_riemann(alpha) -> str:
    """Série de Riemann Σ 1/n^alpha : verdict PROUVÉ (converge ssi alpha > 1). Délégué à series_calcul.

    alpha rationnel (int/Fraction/str) ; flottant/bool refusés par la délégation. Renvoie 'converge'|'diverge'."""
    return "converge" if series_calcul.converge_riemann(alpha) else "diverge"


def converge_geometrique(r) -> str:
    """Série géométrique Σ r^n : verdict PROUVÉ (converge ssi |r| < 1). Délégué à series_calcul.

    r rationnel (int/Fraction/str) ; flottant/bool refusés par la délégation. Renvoie 'converge'|'diverge'."""
    return "converge" if series_calcul.converge_geometrique(r) else "diverge"
