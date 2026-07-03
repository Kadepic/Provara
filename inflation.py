"""
INFLATION — définitions et calculs EXACTS (mécanisme établi, FAUX=0).

Ce module n'invente AUCUNE donnée-pays (pas de « taux d'inflation de la France 2024 » codé en dur). Il implémente
seulement les FORMULES exactes et déterministes de l'économie monétaire, à partir d'indices/taux fournis par l'appelant.

FORMULES (toutes établies, recoupables à la main) :
  • taux_inflation(IPC_initial, IPC_final)      = (final − initial) / initial · 100        [%]   (variation relative d'indice)
  • pouvoir_achat(montant, taux_inflation_pct)  = montant / (1 + taux/100)                  [unité monétaire]
        (valeur réelle d'une somme nominale après une inflation cumulée de `taux` %)
  • valeur_reelle(valeur_nominale, IPC_base, IPC_courant) = nominale · IPC_base / IPC_courant       (déflation par indice)
  • taux_reel(taux_nominal, inflation)          = nominal − inflation                       [%]   (Fisher, APPROXIMATION)
  • taux_reel_exact(taux_nominal, inflation)    = ((1+nominal/100)/(1+inflation/100) − 1)·100 [%]  (Fisher EXACT)

ABSTENTION (ValueError, jamais un faux) :
  • tout IPC ≤ 0 (un indice des prix est strictement positif) ;
  • dénominateur (1 + taux/100) ≤ 0 — soit taux ≤ −100 % (une inflation < −100 % rendrait les prix négatifs : impossible) ;
  • entrée booléenne, non numérique, ou non finie (NaN/inf).

Sorties arrondies (défaut 2 décimales, cf. monnaie/pourcentage). Fonctions pures déterministes, pur Python.
"""
from __future__ import annotations

import math

_DEC = 2  # décimales par défaut (monnaie / point de pourcentage)


def _num(x, nom):
    """Valide un réel fini non booléen, sinon ValueError (abstention)."""
    if isinstance(x, bool) or not isinstance(x, (int, float)):
        raise ValueError(f"{nom} doit être un nombre réel (reçu {type(x).__name__})")
    xf = float(x)
    if not math.isfinite(xf):
        raise ValueError(f"{nom} doit être fini (reçu {x})")
    return xf


def _ndigits(ndigits):
    if not isinstance(ndigits, int) or isinstance(ndigits, bool) or ndigits < 0:
        raise ValueError("ndigits doit être un entier >= 0")
    return ndigits


def _ipc(x, nom):
    """Un indice des prix est strictement positif."""
    v = _num(x, nom)
    if v <= 0.0:
        raise ValueError(f"{nom} doit être > 0 (un indice des prix est strictement positif), reçu {v}")
    return v


def taux_inflation(IPC_initial, IPC_final, ndigits=_DEC):
    """Taux d'inflation entre deux relevés d'indice : (final − initial)/initial · 100, en %."""
    nd = _ndigits(ndigits)
    i0 = _ipc(IPC_initial, "IPC_initial")
    i1 = _ipc(IPC_final, "IPC_final")
    return round((i1 - i0) / i0 * 100.0, nd)


def pouvoir_achat(montant, taux_inflation_pct, ndigits=_DEC):
    """Pouvoir d'achat réel d'une somme nominale après inflation cumulée de `taux_inflation_pct` % : montant/(1+taux/100)."""
    nd = _ndigits(ndigits)
    m = _num(montant, "montant")
    t = _num(taux_inflation_pct, "taux_inflation_pct")
    facteur = 1.0 + t / 100.0
    if facteur <= 0.0:
        raise ValueError(f"taux_inflation_pct <= -100 % impossible (facteur {facteur} <= 0)")
    return round(m / facteur, nd)


def valeur_reelle(valeur_nominale, IPC_base, IPC_courant, ndigits=_DEC):
    """Déflation par indice : ramène une valeur nominale aux prix de la période de base : nominale·IPC_base/IPC_courant."""
    nd = _ndigits(ndigits)
    v = _num(valeur_nominale, "valeur_nominale")
    b = _ipc(IPC_base, "IPC_base")
    c = _ipc(IPC_courant, "IPC_courant")
    return round(v * b / c, nd)


def taux_reel(taux_nominal, inflation, ndigits=_DEC):
    """Taux d'intérêt réel — APPROXIMATION de Fisher : nominal − inflation, en %."""
    nd = _ndigits(ndigits)
    rn = _num(taux_nominal, "taux_nominal")
    inf = _num(inflation, "inflation")
    return round(rn - inf, nd)


def taux_reel_exact(taux_nominal, inflation, ndigits=_DEC):
    """Taux d'intérêt réel — équation de Fisher EXACTE : ((1+nominal/100)/(1+inflation/100) − 1)·100, en %."""
    nd = _ndigits(ndigits)
    rn = _num(taux_nominal, "taux_nominal")
    inf = _num(inflation, "inflation")
    den = 1.0 + inf / 100.0
    if den <= 0.0:
        raise ValueError(f"inflation <= -100 % impossible (1+inflation/100 = {den} <= 0)")
    return round(((1.0 + rn / 100.0) / den - 1.0) * 100.0, nd)


if __name__ == "__main__":
    print("=== INFLATION — formules exactes ===\n")
    print(f"  IPC 100 -> 105 : taux_inflation = {taux_inflation(100, 105)} %")
    print(f"  100 € après 5 % d'inflation : pouvoir d'achat = {pouvoir_achat(100, 5)} €")
    print(f"  valeur nominale 100, IPC base 100 -> courant 125 : valeur réelle = {valeur_reelle(100, 100, 125)}")
    print(f"  taux réel (nominal 5 %, inflation 2 %) : approx = {taux_reel(5, 2)} % ; exact = {taux_reel_exact(5, 2)} %")
