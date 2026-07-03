"""
RELATIVITÉ RESTREINTE — cinématique et énergie d'Einstein, MÉCANISME EXACT (mandat Yohan : couvrir le borné, bloc
« FORMULE » de physique). Même posture que `physique` / `chimie` (la réalité juge, jamais un faux) :

  • Le MÉCANISME (les formules de la relativité restreinte) est EXACT — garantie structurelle.
  • La seule constante est c, la vitesse de la lumière dans le vide, valeur EXACTE par définition du SI 2019
    (le mètre est défini à partir de c). Aucune autre donnée mesurée n'entre : la math est donc exacte à la
    précision flottante près.
  • La sortie est ARRONDIE à 10 chiffres significatifs — précision honnête (pas de faux exact au-delà du double).

FONCTIONS (toutes PURES, déterministes) :
  - facteur_lorentz(v)            = 1/√(1−(v/c)²)            (γ ; v vitesse, 0 ≤ v < c)
  - dilatation_temps(t_propre, v) = γ·t_propre               (durée mesurée dans le référentiel « mobile »)
  - contraction_longueur(L0, v)   = L0/γ                      (longueur mesurée en mouvement)
  - energie_totale(m, v)          = γ·m·c²                    (énergie relativiste totale)
  - energie_repos(m)              = m·c²                      (E = mc²)
  - addition_vitesses(u, w)       = (u+w)/(1+u·w/c²)          (composition relativiste, |u|,|w| ≤ c)

ABSTENTION STRUCTURELLE (vérifiée en adverse par `valide_relativite_restreinte.py`) :
  - v ≥ c  -> ValueError  (vitesse luminale/supraluminique : γ divergerait ou serait imaginaire) ;
  - v < 0  -> ValueError  (une vitesse-paramètre des fonctions cinématiques est un module ≥ 0) ;
  - masse, longueur ou temps propre négatif -> ValueError ;
  - |u| ou |w| > c dans l'addition -> ValueError ; dénominateur nul (u=c, w=−c) -> ValueError ;
  - argument non numérique ou booléen -> ValueError ;
  - déterministe ; conservateur (faux négatif/abstention toléré, faux POSITIF interdit).

CAS CONNUS (ancres) : γ(0)=1 ; γ(0.6c)=1.25 ; γ(0.8c)=5/3 ; addition(0.5c,0.5c)=0.8c ; addition(c,c)=c.
"""
from __future__ import annotations

import math

# ── CONSTANTE SOURCÉE ──────────────────────────────────────────────────────────────────────────────────────────
C_LUMIERE = 299_792_458.0   # m/s — EXACT (définition SI 2019 du mètre)
SOURCE = "c = 299 792 458 m/s (exact, SI 2019)"

_CHIFFRES_SIGNIFICATIFS = 10


def _sig(x: float, n: int = _CHIFFRES_SIGNIFICATIFS) -> float:
    """Arrondit à n chiffres significatifs (précision honnête, indépendante de la magnitude)."""
    if x == 0.0:
        return 0.0
    return float(f"{x:.{n}g}")


def _reel(x) -> float:
    """Valide un réel fini (rejette bool, complexe, str, NaN, inf) — sinon ValueError (abstention)."""
    if isinstance(x, bool) or not isinstance(x, (int, float)):
        raise ValueError(f"argument non réel : {x!r}")
    xf = float(x)
    if not math.isfinite(xf):
        raise ValueError(f"argument non fini : {x!r}")
    return xf


def _vitesse_module(v) -> float:
    """Une vitesse-paramètre cinématique est un module : 0 ≤ v < c (sinon abstention)."""
    vf = _reel(v)
    if vf < 0.0:
        raise ValueError(f"vitesse négative : {vf}")
    if vf >= C_LUMIERE:
        raise ValueError(f"vitesse ≥ c : {vf}")
    return vf


# ── FORMULES ───────────────────────────────────────────────────────────────────────────────────────────────────
def facteur_lorentz(v: float) -> float:
    """Facteur de Lorentz γ = 1/√(1−(v/c)²)."""
    vf = _vitesse_module(v)
    beta = vf / C_LUMIERE
    return _sig(1.0 / math.sqrt(1.0 - beta * beta))


def dilatation_temps(t_propre: float, v: float) -> float:
    """Durée mesurée = γ·t_propre (t_propre ≥ 0)."""
    t = _reel(t_propre)
    if t < 0.0:
        raise ValueError(f"temps propre négatif : {t}")
    vf = _vitesse_module(v)
    beta = vf / C_LUMIERE
    gamma = 1.0 / math.sqrt(1.0 - beta * beta)
    return _sig(gamma * t)


def contraction_longueur(L0: float, v: float) -> float:
    """Longueur en mouvement = L0/γ (L0 ≥ 0)."""
    l = _reel(L0)
    if l < 0.0:
        raise ValueError(f"longueur propre négative : {l}")
    vf = _vitesse_module(v)
    beta = vf / C_LUMIERE
    gamma = 1.0 / math.sqrt(1.0 - beta * beta)
    return _sig(l / gamma)


def energie_totale(m: float, v: float) -> float:
    """Énergie relativiste totale = γ·m·c² (m ≥ 0)."""
    mf = _reel(m)
    if mf < 0.0:
        raise ValueError(f"masse négative : {mf}")
    vf = _vitesse_module(v)
    beta = vf / C_LUMIERE
    gamma = 1.0 / math.sqrt(1.0 - beta * beta)
    return _sig(gamma * mf * C_LUMIERE * C_LUMIERE)


def energie_repos(m: float) -> float:
    """Énergie de masse au repos = m·c² (m ≥ 0)."""
    mf = _reel(m)
    if mf < 0.0:
        raise ValueError(f"masse négative : {mf}")
    return _sig(mf * C_LUMIERE * C_LUMIERE)


def addition_vitesses(u: float, w: float) -> float:
    """Composition relativiste des vitesses = (u+w)/(1+u·w/c²), |u| ≤ c et |w| ≤ c."""
    uf = _reel(u)
    wf = _reel(w)
    if abs(uf) > C_LUMIERE:
        raise ValueError(f"|u| > c : {uf}")
    if abs(wf) > C_LUMIERE:
        raise ValueError(f"|w| > c : {wf}")
    denom = 1.0 + (uf * wf) / (C_LUMIERE * C_LUMIERE)
    if denom == 0.0:
        raise ValueError("dénominateur nul (u=c, w=−c) : indéterminé")
    return _sig((uf + wf) / denom)
