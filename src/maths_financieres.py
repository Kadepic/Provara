"""
MATHÉMATIQUES FINANCIÈRES (intérêts) — borné FORMULE, la réalité (la définition) juge, jamais un faux.

Même posture que `physique` / `hydrologie` : le MÉCANISME (la formule de la valeur-temps de l'argent) est EXACT et
établi par convention financière ; aucune valeur-pays/marché n'est inventée, on ne fournit QUE le calcul exact.

Fonctions pures déterministes, sortie ARRONDIE au centime (2 décimales = précision honnête pour des montants
monétaires). Toute entrée invalide -> ValueError (ABSTENTION : on lève plutôt que de renvoyer un faux).

CATALOGUE (C = capital/principal, t = taux par période en décimal, n = nombre de périodes) :
  • interet_simple(C, t, n)        = C · t · n                  -> le MONTANT d'intérêt simple
  • valeur_acquise_simple(C, t, n) = C · (1 + t·n)             -> capital + intérêt simple
  • interet_compose(C, t, n)       = C · (1 + t)^n             -> VALEUR ACQUISE en capitalisation composée
  • valeur_acquise / valeur_future = alias de interet_compose  (la valeur future composée)
  • valeur_actuelle(VF, t, n)      = VF / (1 + t)^n            -> actualisation (present value)
  • annuite_constante(C, t, n)     = C · t / (1 − (1+t)^−n)    -> mensualité/annuité d'un prêt
                                     (cas limite t=0 : C/n, remboursement à intérêt nul)
  • van / npv(taux, flux)          = Σ_i flux_i / (1 + taux)^i -> valeur actuelle nette (flux_0 en t=0)

SOUNDNESS (vérifié en adverse par `valide_maths_financieres.py`) :
  C < 0 (ou VF < 0), taux ≤ −1 (≤ −100 %), n < 0 (n ≤ 0 pour l'annuité), entrée non numérique / booléenne /
  NaN / inf, flux vide ou non numérique  ->  ValueError. Déterministe.
"""
from __future__ import annotations

import math

_DECIMALES = 2  # arrondi au centime : précision honnête d'un montant monétaire


# ── VALIDATION (abstention par ValueError, jamais un faux) ─────────────────────────────────────────────────────
def _exige_nombre(x, nom: str) -> None:
    if isinstance(x, bool) or not isinstance(x, (int, float)) or not math.isfinite(x):
        raise ValueError(f"{nom} doit être un nombre réel fini, reçu {x!r}")


def _exige_positif_ou_nul(x, nom: str) -> None:
    _exige_nombre(x, nom)
    if x < 0:
        raise ValueError(f"{nom} doit être >= 0, reçu {x!r}")


def _exige_taux(t) -> None:
    _exige_nombre(t, "taux t")
    if t <= -1:
        raise ValueError(f"taux t doit être > -1 (> -100 %), reçu {t!r}")


def _exige_periodes(n, strict: bool = False) -> None:
    _exige_nombre(n, "n")
    if strict:
        if n <= 0:
            raise ValueError(f"nombre de périodes n doit être > 0, reçu {n!r}")
    elif n < 0:
        raise ValueError(f"nombre de périodes n doit être >= 0, reçu {n!r}")


def _r(x: float) -> float:
    """Arrondi au centime, résultat fini garanti (-0.0 normalisé en 0.0)."""
    if not math.isfinite(x):
        raise ValueError("résultat non fini")
    return round(x, _DECIMALES) + 0.0


# ── INTÉRÊT SIMPLE ─────────────────────────────────────────────────────────────────────────────────────────────
def interet_simple(C, t, n) -> float:
    """Montant d'intérêt simple : C · t · n."""
    _exige_positif_ou_nul(C, "capital C")
    _exige_taux(t)
    _exige_periodes(n)
    return _r(C * t * n)


def valeur_acquise_simple(C, t, n) -> float:
    """Valeur acquise en intérêt simple : C · (1 + t·n) = C + intérêt simple."""
    _exige_positif_ou_nul(C, "capital C")
    _exige_taux(t)
    _exige_periodes(n)
    return _r(C * (1 + t * n))


# ── INTÉRÊT COMPOSÉ / VALEUR ACQUISE-FUTURE ────────────────────────────────────────────────────────────────────
def interet_compose(C, t, n) -> float:
    """Valeur acquise en capitalisation composée : C · (1 + t)^n."""
    _exige_positif_ou_nul(C, "capital C")
    _exige_taux(t)
    _exige_periodes(n)
    return _r(C * (1 + t) ** n)


def valeur_acquise(C, t, n) -> float:
    """Alias : valeur acquise composée C · (1 + t)^n."""
    return interet_compose(C, t, n)


def valeur_future(C, t, n) -> float:
    """Alias : valeur future composée C · (1 + t)^n."""
    return interet_compose(C, t, n)


# ── ACTUALISATION (VALEUR ACTUELLE / PRESENT VALUE) ────────────────────────────────────────────────────────────
def valeur_actuelle(VF, t, n) -> float:
    """Valeur actuelle d'un montant futur : VF / (1 + t)^n."""
    _exige_positif_ou_nul(VF, "valeur future VF")
    _exige_taux(t)
    _exige_periodes(n)
    return _r(VF / (1 + t) ** n)


# ── ANNUITÉ / MENSUALITÉ CONSTANTE D'UN PRÊT ───────────────────────────────────────────────────────────────────
def annuite_constante(C, t, n) -> float:
    """Annuité (mensualité) constante d'un prêt : C · t / (1 − (1+t)^−n).

    Cas limite t = 0 (prêt sans intérêt) : la formule est 0/0 ; la valeur exacte est C/n
    (amortissement linéaire du capital).
    """
    _exige_positif_ou_nul(C, "capital C")
    _exige_taux(t)
    _exige_periodes(n, strict=True)
    if t == 0:
        return _r(C / n)
    return _r(C * t / (1 - (1 + t) ** (-n)))


# ── VALEUR ACTUELLE NETTE (VAN / NPV) ──────────────────────────────────────────────────────────────────────────
def van(taux, flux) -> float:
    """Valeur actuelle nette : Σ_i flux_i / (1 + taux)^i, le flux d'indice 0 étant pris en t = 0."""
    _exige_taux(taux)
    if not isinstance(flux, (list, tuple)) or len(flux) == 0:
        raise ValueError(f"flux doit être une liste/tuple non vide, reçu {flux!r}")
    for i, f in enumerate(flux):
        _exige_nombre(f, f"flux[{i}]")
    return _r(sum(f / (1 + taux) ** i for i, f in enumerate(flux)))


def npv(taux, flux) -> float:
    """Alias anglophone de `van`."""
    return van(taux, flux)
