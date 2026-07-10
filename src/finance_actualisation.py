"""
FINANCE — ACTUALISATION : VAN, TRI (bissection encadrée), annuités, amortissement, taux équivalents.

Même posture FAUX=0 que `physique` / `geometries_non_euclidiennes` (la définition juge, jamais un faux) :
  • Le MÉCANISME est la valeur-temps de l'argent, convention financière EXACTE :
      – VAN(flux, i)         = Σ_{t=0}^{n} F_t / (1+i)^t          (F_0 typiquement négatif : l'investissement) ;
      – TRI                  = la racine i de VAN(i) = 0, i ∈ ]-1, +∞[ ;
      – annuité constante    a = C·i / (1 − (1+i)^−n)             (cas limite i = 0 : a = C/n, exact) ;
      – amortissement        intérêt_k = restant_{k−1}·i ; principal_k = a − intérêt_k ;
      – taux équivalent      i_p = (1+i_annuel)^(1/p) − 1          (même capitalisation sur l'année) ;
      – taux actuariel       i_a = (1 + i_nominal/p)^p − 1         (taux effectif annuel d'un nominal fractionné).
  • TRI et FAUX=0 — le TRI n'existe pas toujours et n'est pas toujours unique (règle des signes de Descartes
    sur le polynôme Σ F_t·x^t, x = 1/(1+i)) :
      – 0 changement de signe dans les flux  -> ValueError (la VAN ne s'annule jamais : TRI INEXISTANT) ;
      – ≥ 2 changements de signe             -> ValueError « TRI non unique : N changements de signe, la valeur
        serait arbitraire » (plusieurs racines positives possibles : rendre l'une d'elles serait un FAUX) ;
      – exactement 1 changement de signe     -> la racine positive du polynôme est UNIQUE (Descartes : le nombre
        de racines > 0 égale le nombre de changements de signe modulo 2, et premier/dernier coefficients opposés
        garantissent l'existence) ; elle est isolée par BISSECTION sur un encadrement où la VAN change de signe.
  • Le TRI rendu est MARQUÉ approché : dict {"valeur", "lo", "hi", "approchee": True} avec hi − lo ≤ tol ;
    la valeur exacte est DANS [lo, hi] (encadrement prouvé par changement de signe de la VAN).
  • Les sorties flottantes sont ARRONDIES à 10 chiffres significatifs — précision honnête, on ne prétend pas
    à l'exactitude au-delà (SAUF le tableau d'amortissement, rendu en flottants bruts pour préserver
    l'invariant de clôture, vérifié en dur : |restant final| ≤ 1e-6 sinon RuntimeError).

GARANTIES (vérifiées en adverse par `valide_finance_actualisation.py`) :
  - taux ≤ −1 (≤ −100 %)                      -> ValueError ;
  - n ≤ 0, n non entier, périodes ≤ 0          -> ValueError ;
  - capital ≤ 0                                -> ValueError ;
  - flux vide, non-séquence, ou contenant bool/str/NaN/±inf -> ValueError ;
  - flux tous de même signe (0 changement)     -> ValueError (TRI inexistant) ;
  - flux à ≥ 2 changements de signe            -> ValueError (TRI non unique, valeur arbitraire) ;
  - tol hors ]0, 0.1]                          -> ValueError ;
  - racine non isolable dans ]-1, 1e9]         -> ValueError (abstention plutôt qu'une extrapolation) ;
  - types invalides (bool, str, NaN, ±inf)     -> ValueError partout ;
  - invariant d'amortissement (restant final ≠ 0 à 1e-6 près) -> RuntimeError ;
  - déterministe ; conservateur (faux négatif/abstention toléré, faux POSITIF interdit).

NOTE : `maths_financieres.py` couvre déjà intérêt simple/composé, valeur actuelle, annuité, VAN — il n'a AUCUN
TRI et n'est PAS modifié ici. Ce module est autonome (stdlib `math` uniquement), fonctions PURES.
"""
from __future__ import annotations

import math

SOURCE = ("valeur-temps de l'argent (actualisation, convention financière exacte) + règle des signes de "
          "Descartes pour l'existence/unicité du TRI + méthode de bissection (encadrement certifié)")

_CHIFFRES_SIGNIFICATIFS = 10
_TOL_INVARIANT = 1e-6   # clôture du tableau d'amortissement : |restant final| doit être ≤ 1e-6
_HI_MAX = 1e9           # borne d'exploration du TRI (taux de 100 000 000 000 % : au-delà, abstention)


# ── helpers internes (validation = abstention par ValueError) ──────────────────────────────────────────────────
def _sig(x: float, n: int = _CHIFFRES_SIGNIFICATIFS) -> float:
    """Arrondit à n chiffres significatifs (précision honnête, indépendante de la magnitude)."""
    if x == 0:
        return 0.0
    return float(f"{x:.{n}g}")


def _est_reel(x) -> bool:
    """True ssi x est un réel fini (les bool sont REFUSÉS : True n'est pas un montant ni un taux)."""
    return isinstance(x, (int, float)) and not isinstance(x, bool) and math.isfinite(x)


def _exige_taux(t) -> float:
    """Taux par période : réel fini strictement supérieur à −1 (−100 % détruirait toute actualisation)."""
    if not _est_reel(t) or t <= -1.0:
        raise ValueError("taux invalide : un réel fini strictement supérieur à -1 (> -100 %) est requis")
    return float(t)


def _exige_entier(n, mini: int = 1) -> int:
    """Nombre de périodes : entier (bool refusé) ≥ mini."""
    if not isinstance(n, int) or isinstance(n, bool) or n < mini:
        raise ValueError(f"nombre de périodes invalide : un entier >= {mini} est requis")
    return n


def _exige_capital(c) -> float:
    if not _est_reel(c) or c <= 0:
        raise ValueError("capital invalide : un réel fini strictement positif est requis")
    return float(c)


def _exige_flux(flux) -> list:
    """Suite de flux F_0..F_n : séquence non vide de réels finis (bool/str/NaN/inf refusés)."""
    if not isinstance(flux, (list, tuple)) or len(flux) == 0:
        raise ValueError("flux invalide : une liste/tuple non vide de réels finis est requise")
    for f in flux:
        if not _est_reel(f):
            raise ValueError(f"flux invalide : chaque flux doit être un réel fini, reçu {f!r}")
    return [float(f) for f in flux]


def _van_brute(flux: list, taux: float) -> float:
    """VAN non arrondie : Σ F_t/(1+taux)^t (usage interne, entrées déjà validées)."""
    return sum(f / (1.0 + taux) ** t for t, f in enumerate(flux))


def _changements_signe(flux: list) -> int:
    """Nombre de changements de signe de la suite des flux, zéros ignorés (règle de Descartes)."""
    signes = [1 if f > 0 else -1 for f in flux if f != 0.0]
    return sum(1 for a, b in zip(signes, signes[1:]) if a != b)


# ── VAN ─────────────────────────────────────────────────────────────────────────────────────────────────────────
def van(flux, taux) -> float:
    """Valeur actuelle nette : VAN = Σ_{t=0}^{n} F_t / (1+taux)^t  (F_0 au temps 0, non actualisé).

    flux = séquence non vide de réels finis ; taux > −1. Sortie arrondie à 10 chiffres significatifs.
    Dépassement flottant -> ValueError (jamais un infini présenté comme un montant)."""
    fl = _exige_flux(flux)
    t = _exige_taux(taux)
    v = _van_brute(fl, t)
    if not math.isfinite(v):
        raise ValueError("VAN non calculable : dépassement flottant (taux trop proche de -100 %)")
    return _sig(v)


# ── TRI (bissection encadrée, existence/unicité par Descartes) ─────────────────────────────────────────────────
def tri(flux, tol: float = 1e-9) -> dict:
    """TRI = racine de VAN(i)=0, rendue en ENCADREMENT certifié + valeur APPROCHÉE.

    Renvoie {"valeur": (lo+hi)/2, "lo": lo, "hi": hi, "approchee": True} avec hi − lo ≤ tol et la racine
    exacte DANS [lo, hi] (la VAN change de signe entre lo et hi — preuve d'encadrement).
    FAUX=0 : 0 changement de signe des flux -> ValueError (TRI inexistant) ; ≥ 2 changements -> ValueError
    (TRI non unique : la valeur serait arbitraire) ; racine non isolable dans ]-1, 1e9] -> ValueError."""
    fl = _exige_flux(flux)
    if not _est_reel(tol) or not (0.0 < tol <= 0.1):
        raise ValueError("tol invalide : un réel fini dans ]0, 0.1] est requis")
    tol = float(tol)
    nch = _changements_signe(fl)
    if nch == 0:
        raise ValueError("TRI inexistant : aucun changement de signe dans les flux, la VAN ne s'annule jamais")
    if nch >= 2:
        raise ValueError(f"TRI non unique : {nch} changements de signe, la valeur serait arbitraire")

    # 1 changement de signe : racine positive UNIQUE du polynôme (Descartes) -> encadrement puis bissection.
    lo = f_lo = None
    for candidat in (-1.0 + 1e-6, -0.999, -0.99, -0.9, -0.5, 0.0):
        v = _van_brute(fl, candidat)
        if math.isfinite(v):
            lo, f_lo = candidat, v
            break
    if lo is None:
        raise ValueError("TRI non isolable : VAN non calculable près de -100 % (dépassement flottant)")
    if f_lo == 0.0:
        return {"valeur": lo, "lo": lo, "hi": lo, "approchee": True}
    hi = 1.0
    f_hi = _van_brute(fl, hi)
    while f_hi != 0.0 and (f_lo > 0.0) == (f_hi > 0.0) and hi < _HI_MAX:
        hi *= 2.0
        f_hi = _van_brute(fl, hi)
    if f_hi == 0.0:
        return {"valeur": hi, "lo": hi, "hi": hi, "approchee": True}
    if (f_lo > 0.0) == (f_hi > 0.0):
        raise ValueError("TRI non isolable : aucun encadrement où la VAN change de signe dans ]-1, 1e9]")

    while hi - lo > tol:
        mid = 0.5 * (lo + hi)
        if mid <= lo or mid >= hi:
            # précision flottante épuisée avant d'atteindre tol : abstention plutôt qu'un faux encadrement
            raise ValueError("tol plus fin que la précision flottante : encadrement non certifiable")
        f_mid = _van_brute(fl, mid)
        if f_mid == 0.0:
            lo = hi = mid
            break
        if (f_mid > 0.0) == (f_lo > 0.0):
            lo, f_lo = mid, f_mid
        else:
            hi, f_hi = mid, f_mid
    return {"valeur": 0.5 * (lo + hi), "lo": lo, "hi": hi, "approchee": True}


# ── ANNUITÉ CONSTANTE ──────────────────────────────────────────────────────────────────────────────────────────
def annuite_constante(capital, taux, n) -> float:
    """Annuité constante d'un emprunt : a = C·i / (1 − (1+i)^−n) ; cas limite i = 0 : a = C/n (exact).

    capital > 0 ; taux > −1 ; n entier ≥ 1. Sortie arrondie à 10 chiffres significatifs (approchée)."""
    c = _exige_capital(capital)
    t = _exige_taux(taux)
    n = _exige_entier(n, 1)
    if t == 0.0:
        return _sig(c / n)
    return _sig(c * t / (1.0 - (1.0 + t) ** (-n)))


# ── TABLEAU D'AMORTISSEMENT ────────────────────────────────────────────────────────────────────────────────────
def tableau_amortissement(capital, taux, n) -> list:
    """Tableau d'amortissement à annuité constante : liste de n lignes (intérêt, principal, restant).

    intérêt_k = restant_{k−1}·i ; principal_k = a − intérêt_k ; restant_k = restant_{k−1} − principal_k.
    INVARIANT DUR : |restant après la dernière échéance| ≤ 1e-6, sinon RuntimeError (jamais un tableau
    qui ne solde pas la dette). Lignes en flottants bruts (non arrondis) pour préserver l'invariant."""
    c = _exige_capital(capital)
    t = _exige_taux(taux)
    n = _exige_entier(n, 1)
    a = (c / n) if t == 0.0 else c * t / (1.0 - (1.0 + t) ** (-n))   # annuité interne NON arrondie
    if not math.isfinite(a):
        raise ValueError("annuité non calculable : dépassement flottant")
    restant = c
    lignes = []
    for _ in range(n):
        interet = restant * t
        principal = a - interet
        restant = restant - principal
        lignes.append((interet, principal, restant))
    if abs(restant) > _TOL_INVARIANT:
        raise RuntimeError(f"invariant d'amortissement violé : restant final {restant!r} (attendu 0 à 1e-6 près)")
    return lignes


# ── TAUX ÉQUIVALENT / TAUX ACTUARIEL ───────────────────────────────────────────────────────────────────────────
def taux_equivalent(taux_annuel, periodes) -> float:
    """Taux par période ÉQUIVALENT à un taux annuel : i_p = (1 + i_annuel)^(1/p) − 1.

    Même valeur acquise après p capitalisations : (1+i_p)^p = 1+i_annuel. taux_annuel > −1 ; p entier ≥ 1.
    Sortie arrondie à 10 chiffres significatifs (approchée)."""
    ta = _exige_taux(taux_annuel)
    p = _exige_entier(periodes, 1)
    return _sig((1.0 + ta) ** (1.0 / p) - 1.0)


def taux_actuariel(taux_nominal, periodes) -> float:
    """Taux actuariel (effectif annuel) d'un taux NOMINAL annuel capitalisé p fois : (1 + i_n/p)^p − 1.

    taux_nominal réel fini avec i_n/p > −1 ; p entier ≥ 1. Sortie arrondie à 10 chiffres significatifs."""
    if not _est_reel(taux_nominal):
        raise ValueError("taux nominal invalide : un réel fini est requis")
    p = _exige_entier(periodes, 1)
    if taux_nominal / p <= -1.0:
        raise ValueError("taux nominal invalide : le taux par période i_n/p doit rester > -1 (> -100 %)")
    return _sig((1.0 + float(taux_nominal) / p) ** p - 1.0)
