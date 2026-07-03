"""
AUDIOLOGIE (audition) — échelle décibel, classification de la perte auditive, faits (mandat Yohan : couvrir le
borné, bloc « FORMULE »).

Même posture que `physique` / `aerodynamique` (la réalité juge, jamais un faux) :
  • Le MÉCANISME (les formules de l'acoustique / l'échelle décibel logarithmique) est EXACT — garantie structurelle.
  • La classification de la perte auditive est la GRILLE OMS (donnée conventionnelle sourcée), pas un avis inventé.
  • La sortie numérique est ARRONDIE à 6 chiffres significatifs — précision HONNÊTE, pas un faux exact.
  • Toute entrée hors domaine physique lève ValueError (ABSTENTION) — jamais un nombre / une classe absurde.

FORMULES & FAITS (établis, acoustique) :
  - Niveau sonore     L = 10·log10(I/I0)            (dB SPL) — échelle décibel d'intensité acoustique
                      I0 = 1e-12 W/m² = seuil de référence (seuil d'audition à 1 kHz)
  - Addition de niveaux L = 10·log10(10^(L1/10)+10^(L2/10))  (dB) — sommation INCOHÉRENTE de deux sources
                      (deux sources d'égal niveau -> +3 dB exactement : 10·log10(2) = 3.0103 dB)
  - Plage audible     20 Hz – 20 000 Hz  (fait : audition humaine jeune nominale)
  - Classification de la perte auditive (grille OMS, sur le seuil d'audition en dB HL) :
        < 25      -> normale
        25 – 40   -> légère
        40 – 55   -> moyenne (modérée)
        55 – 70   -> modérément sévère
        70 – 90   -> sévère
        > 90      -> profonde

REPÈRES (documentaires, non utilisés dans le calcul) :
  • Seuil d'audition ≈ 0 dB SPL ; conversation ≈ 60 dB ; seuil de douleur ≈ 120–130 dB SPL.
  • I = 1 W/m² -> 10·log10(1/1e-12) = 120 dB (ordre du seuil de douleur).

SOUNDNESS (vérifiée en adverse par `valide_audiologie.py`) :
  - intensite ≤ 0, intensite_ref ≤ 0      -> ValueError (log10 d'un rapport ≤ 0 indéfini) ;
  - seuil_db < 0 (classification)          -> ValueError (seuil d'audition négatif hors grille) ;
  - tout argument non numérique / booléen / non fini -> ValueError ;
  - déterministe ; conservateur (abstention tolérée, faux POSITIF interdit).
"""
from __future__ import annotations

import math

INTENSITE_REFERENCE = 1e-12          # W/m² — seuil de référence d'intensité acoustique (dB SPL)
PLAGE_AUDIBLE_HZ = (20, 20000)       # Hz — plage audible humaine nominale (jeune adulte)
SEUIL_DOULEUR_DB = (120, 130)        # dB SPL — ordre de grandeur du seuil de douleur (repère)
SOURCE = "acoustique (échelle décibel d'intensité) ; classification OMS de la perte auditive"

_CHIFFRES_SIGNIFICATIFS = 6


def _sig(x: float, n: int = _CHIFFRES_SIGNIFICATIFS) -> float:
    """Arrondit à n chiffres significatifs (précision honnête, indépendante de la magnitude)."""
    if x == 0:
        return 0.0
    return float(f"{x:.{n}g}")


def _num(x) -> float:
    """Convertit x en float fini en REFUSANT booléens / non numériques / non finis -> ValueError."""
    if isinstance(x, bool) or not isinstance(x, (int, float)):
        raise ValueError(f"argument non numérique : {x!r}")
    f = float(x)
    if not math.isfinite(f):
        raise ValueError(f"argument non fini : {x!r}")
    return f


def niveau_db(intensite, intensite_ref=INTENSITE_REFERENCE) -> float:
    """Niveau sonore L = 10·log10(I/I0) en dB SPL. I ≤ 0 ou I0 ≤ 0 -> ValueError (log indéfini)."""
    i = _num(intensite)
    i0 = _num(intensite_ref)
    if i <= 0:
        raise ValueError("intensite doit être > 0")
    if i0 <= 0:
        raise ValueError("intensite_ref doit être > 0")
    return _sig(10.0 * math.log10(i / i0))


def classe_perte_auditive(seuil_db) -> str:
    """Classe OMS d'après le seuil d'audition (dB HL). seuil_db < 0 -> ValueError (hors grille)."""
    s = _num(seuil_db)
    if s < 0:
        raise ValueError("seuil_db doit être >= 0")
    if s < 25:
        return "normale"
    if s < 40:
        return "légère"
    if s < 55:
        return "moyenne"
    if s < 70:
        return "modérément sévère"
    if s <= 90:
        return "sévère"
    return "profonde"


def plage_audible_hz() -> tuple:
    """Plage audible humaine nominale (fait) : (20, 20000) Hz."""
    return PLAGE_AUDIBLE_HZ


def addition_db(db1, db2) -> float:
    """Somme de deux niveaux sonores L = 10·log10(10^(L1/10)+10^(L2/10)) en dB (sources incohérentes).

    Les niveaux peuvent être négatifs (source sous la référence) ; seules les valeurs non finies sont refusées.
    Deux sources d'égal niveau -> +3 dB (10·log10(2) = 3.0103 dB)."""
    l1 = _num(db1)
    l2 = _num(db2)
    return _sig(10.0 * math.log10(10.0 ** (l1 / 10.0) + 10.0 ** (l2 / 10.0)))
