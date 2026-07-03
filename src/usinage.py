"""
USINAGE BORNÉ — paramètres de coupe (machining), formules EXACTES et établies.

Posture FAUX=0 (même esprit que `physique`/`chimie` : la réalité/la définition juge, jamais un faux) :
  • Le MÉCANISME est une formule d'usinage STANDARD, universelle (ISO/manuels d'atelier) — garantie structurelle.
  • Toute entrée hors domaine physique (dimension, vitesse, avance ≤ 0) -> ValueError : on ne renvoie JAMAIS un
    nombre absurde (vitesse de coupe négative, débit nul inventé…).
  • Déterministe, fonctions pures, stdlib uniquement.

FORMULES (paramètres de coupe) :
  - vitesse_coupe(D, N)        = π·D·N / 1000           [m/min]   (D en mm, N en tr/min)
        La circonférence π·D (mm) parcourue N fois par minute = π·D·N mm/min ; /1000 -> m/min.
  - rotation_broche(Vc, D)     = 1000·Vc / (π·D)        [tr/min]  (inverse — fixer Vc, trouver N)
  - taux_enlevement_matiere(ae, ap, vf) = ae·ap·vf      [unités cohérentes]  (MRR = largeur·profondeur·avance)
        En fraisage : ae (mm) · ap (mm) · vf (mm/min) -> mm³/min.
  - temps_usinage(L, f)        = L / f                  [min]     (longueur / avance par minute)
  - avance_par_minute(fz, z, N)= fz·z·N                 [mm/min]  (avance/dent · nb dents · tr/min) -> vf

ANCRES : Vc(D=50, N=1000) = π·50 ≈ 157.08 m/min.
"""
from __future__ import annotations

import math


def _pos(x, nom: str) -> float:
    """Valide un réel STRICTEMENT positif (refuse bool, str, None, ≤ 0, NaN/inf). Sinon ValueError."""
    if isinstance(x, bool) or not isinstance(x, (int, float)):
        raise ValueError(f"{nom} doit être un nombre réel, reçu {x!r}")
    xf = float(x)
    if not math.isfinite(xf):
        raise ValueError(f"{nom} doit être fini, reçu {x!r}")
    if xf <= 0:
        raise ValueError(f"{nom} doit être > 0, reçu {x!r}")
    return xf


def vitesse_coupe(diametre_mm: float, rotation_rpm: float) -> float:
    """Vitesse de coupe Vc = π·D·N/1000 (m/min). D en mm, N en tr/min. Entrées ≤ 0 -> ValueError."""
    d = _pos(diametre_mm, "diametre_mm")
    n = _pos(rotation_rpm, "rotation_rpm")
    return math.pi * d * n / 1000.0


def rotation_broche(vitesse_coupe_m_min: float, diametre_mm: float) -> float:
    """Régime broche N = 1000·Vc/(π·D) (tr/min) — inverse de vitesse_coupe. Entrées ≤ 0 -> ValueError."""
    vc = _pos(vitesse_coupe_m_min, "vitesse_coupe_m_min")
    d = _pos(diametre_mm, "diametre_mm")
    return 1000.0 * vc / (math.pi * d)


def taux_enlevement_matiere(largeur: float, profondeur: float, avance: float) -> float:
    """MRR = ae·ap·vf (largeur de coupe · profondeur · avance). Produit des trois. Entrées ≤ 0 -> ValueError."""
    ae = _pos(largeur, "largeur")
    ap = _pos(profondeur, "profondeur")
    vf = _pos(avance, "avance")
    return ae * ap * vf


def temps_usinage(longueur: float, avance_par_min: float) -> float:
    """Temps d'usinage t = L / f (min). Longueur / avance par minute. Entrées ≤ 0 -> ValueError."""
    L = _pos(longueur, "longueur")
    f = _pos(avance_par_min, "avance_par_min")
    return L / f


def avance_par_minute(avance_par_dent: float, nb_dents: float, rotation_rpm: float) -> float:
    """Avance de table vf = fz·z·N (mm/min). avance/dent · nb dents · régime. Entrées ≤ 0 -> ValueError."""
    fz = _pos(avance_par_dent, "avance_par_dent")
    z = _pos(nb_dents, "nb_dents")
    n = _pos(rotation_rpm, "rotation_rpm")
    return fz * z * n
