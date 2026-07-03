"""
HYDROLOGIE (eaux continentales) — débits et écoulements CALCULABLES par formule établie.

Posture FAUX=0 (la réalité hydraulique juge, jamais un faux) :
  • Le MÉCANISME (la formule) est EXACT et ÉTABLI ; aucune corrélation inventée.
  • Les CONSTANTES de conversion sont DÉRIVÉES (unités) ou SOURCÉES (Kirpich 1940), documentées ci-dessous.
  • La sortie est ARRONDIE à 6 chiffres significatifs (précision honnête, pas un faux exact).
  • Domaine invalide (section ≤ 0, coef. C hors [0,1], n ≤ 0, longueur/pente ≤ 0…) -> ValueError :
    abstention, jamais un nombre absurde. Fonctions PURES, DÉTERMINISTES, stdlib seule.

FORMULES (établies) :
  1. CONTINUITÉ (débit-section)   Q = A · v
        Q (m³/s) = section A (m²) × vitesse moyenne v (m/s). Équation de continuité, débit volumique.
  2. MÉTHODE RATIONNELLE          Q = (1/360) · C · i · A
        Q (m³/s), C = coefficient de ruissellement ∈ [0,1] (sans dim.), i = intensité de pluie (mm/h),
        A = aire du bassin (ha). Le facteur 1/360 = 0,002777… est une CONVERSION D'UNITÉS EXACTE :
        (1 mm/h = 1e-3 m / 3600 s) × (1 ha = 1e4 m²) = 1e-3/3600 × 1e4 = 1/360. (Valeur tabulée usuelle : 0,00278.)
  3. MANNING (vitesse)            v = (1/n) · R^(2/3) · √S
        v (m/s), n = coefficient de rugosité de Manning (s·m^(−1/3)), R = rayon hydraulique (m),
        S = pente de la ligne d'énergie (m/m). Forme SI métrique (coefficient de conversion k = 1).
  4. TEMPS DE CONCENTRATION (Kirpich) t_c = 0,0195 · L^0,77 · S^(−0,385)
        t_c (minutes), L = longueur du plus long cheminement (m), S = pente moyenne (m/m).
        Constante métrique 0,0195 = Kirpich (1940) 0,0078·L_ft^0,77·S^(−0,385) converti en mètres
        (0,0078 × (1/0,3048)^0,77 ≈ 0,01947, conventionnellement arrondi à 0,0195).

`valide_hydrologie.py` vérifie en adverse : ancres CONNUES non circulaires, soundness, déterminisme.
"""
from __future__ import annotations

import math

SOURCE = ("équation de continuité Q=A·v ; méthode rationnelle Q=(1/360)·C·i·A (1/360 = conversion "
          "mm/h·ha→m³/s) ; Manning v=(1/n)·R^(2/3)·√S (forme SI) ; Kirpich 1940 t_c=0.0195·L^0.77·S^(-0.385)")

# ── CONSTANTES ─────────────────────────────────────────────────────────────────────────────────────────────────
_FACTEUR_RATIONNELLE = 1.0 / 360.0     # conversion EXACTE (mm/h, ha) -> m³/s ; valeur tabulée arrondie : 0.00278
_KIRPICH_C = 0.0195                    # constante métrique de Kirpich (1940), t_c en minutes, L en m
_KIRPICH_P_L = 0.77                    # exposant sur la longueur
_KIRPICH_P_S = -0.385                  # exposant sur la pente

_CHIFFRES_SIGNIFICATIFS = 6


def _sig(x: float, n: int = _CHIFFRES_SIGNIFICATIFS) -> float:
    """Arrondit à n chiffres significatifs (précision honnête, indépendante de la magnitude)."""
    if x == 0:
        return 0.0
    return float(f"{x:.{n}g}")


def _num(x, nom: str) -> float:
    """x est un réel (ni booléen, ni complexe, ni NaN/inf) -> float ; sinon ValueError."""
    if isinstance(x, bool) or not isinstance(x, (int, float)):
        raise ValueError(f"{nom} doit être un nombre réel, reçu {type(x).__name__}")
    xf = float(x)
    if not math.isfinite(xf):
        raise ValueError(f"{nom} doit être fini, reçu {x!r}")
    return xf


def _pos(x, nom: str) -> float:
    """Réel STRICTEMENT positif (> 0) -> float ; sinon ValueError."""
    xf = _num(x, nom)
    if xf <= 0:
        raise ValueError(f"{nom} doit être > 0, reçu {xf}")
    return xf


def _nonneg(x, nom: str) -> float:
    """Réel NON négatif (≥ 0) -> float ; sinon ValueError."""
    xf = _num(x, nom)
    if xf < 0:
        raise ValueError(f"{nom} doit être ≥ 0, reçu {xf}")
    return xf


# ── 1) CONTINUITÉ : débit = section · vitesse ─────────────────────────────────────────────────────────────────
def debit(section_m2, vitesse_ms) -> float:
    """Débit volumique par continuité Q = A·v (m³/s). section_m2 > 0, vitesse_ms ≥ 0 ; sinon ValueError."""
    a = _pos(section_m2, "section_m2")          # spec : section <= 0 -> ValueError
    v = _nonneg(vitesse_ms, "vitesse_ms")
    return _sig(a * v)


# ── 2) MÉTHODE RATIONNELLE : ruissellement de pointe ──────────────────────────────────────────────────────────
def methode_rationnelle(coef_C, intensite_mm_h, aire_ha) -> float:
    """Débit de pointe Q = (1/360)·C·i·A (m³/s). C ∈ [0,1], i ≥ 0 (mm/h), A > 0 (ha) ; sinon ValueError."""
    c = _num(coef_C, "coef_C")
    if c < 0.0 or c > 1.0:                       # spec : coef C hors [0,1] -> ValueError
        raise ValueError(f"coef_C doit être ∈ [0,1], reçu {c}")
    i = _nonneg(intensite_mm_h, "intensite_mm_h")
    a = _pos(aire_ha, "aire_ha")
    return _sig(_FACTEUR_RATIONNELLE * c * i * a)


# Alias demandé par la spécification (méthode_rationnelle / ruissellement = même mécanisme).
def ruissellement(coef_C, intensite_mm_h, aire_ha) -> float:
    """Synonyme de methode_rationnelle : Q = (1/360)·C·i·A (m³/s)."""
    return methode_rationnelle(coef_C, intensite_mm_h, aire_ha)


# ── 3) MANNING : vitesse moyenne d'écoulement à surface libre ─────────────────────────────────────────────────
def manning_vitesse(n, rayon_hydraulique, pente) -> float:
    """Vitesse de Manning v = (1/n)·R^(2/3)·√S (m/s). n > 0, R > 0, pente ≥ 0 ; sinon ValueError."""
    nn = _pos(n, "n")                            # spec : n <= 0 -> ValueError
    r = _pos(rayon_hydraulique, "rayon_hydraulique")
    s = _nonneg(pente, "pente")
    return _sig((1.0 / nn) * (r ** (2.0 / 3.0)) * math.sqrt(s))


# ── 4) TEMPS DE CONCENTRATION (Kirpich) ───────────────────────────────────────────────────────────────────────
def temps_concentration(longueur_m, pente) -> float:
    """Temps de concentration de Kirpich t_c = 0,0195·L^0,77·S^(−0,385) (minutes).
    L > 0 (m), pente > 0 (m/m) ; sinon ValueError (pente=0 -> exposant négatif indéfini)."""
    l = _pos(longueur_m, "longueur_m")
    s = _pos(pente, "pente")
    return _sig(_KIRPICH_C * (l ** _KIRPICH_P_L) * (s ** _KIRPICH_P_S))
