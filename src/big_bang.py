"""
BIG BANG — cosmologie établie (formules/faits sourcés). Même posture FAUX=0 que `physique`/`chimie` :
  • Le MÉCANISME (formule cosmologique) est EXACT — garantie structurelle.
  • Les CONSTANTES (G, parsec, année julienne) et FAITS (T_CMB, abondances BBN) sont des DONNÉES SOURCÉES.
  • Sortie déterministe ; entrée invalide/inconnue -> ValueError (abstention, JAMAIS un faux).

Contenu :
  - age_univers_hubble(H0)  : temps de Hubble 1/H0 en années (H0 en km/s/Mpc). H0=70 -> ~1.40e10 ans.
  - abondance_primordiale() : fractions de MASSE primordiales BBN {'H':0.75, 'He':0.25} (~75%/~25%, fait).
  - temperature_cmb()       : 2.725 K (température du fond diffus cosmologique, fait mesuré COBE/FIRAS).
  - densite_critique(H0)    : ρ_c = 3·H0²/(8πG) en kg/m³ (H0 en km/s/Mpc). H0=70 -> ~9.20e-27 kg/m³.

Garanties (vérifiées en adverse par `valide_big_bang.py`) :
  - H0 <= 0, NaN/inf, non numérique, booléen -> ValueError ;
  - déterministe ; faits renvoyés à l'identique.
"""
from __future__ import annotations

import math

# ── CONSTANTES SOURCÉES ────────────────────────────────────────────────────────────────────────────────────────
G_NEWTON = 6.674_30e-11                 # m^3 kg^-1 s^-2 — CODATA 2018 (mesurée)
KM_PAR_MPC = 3.085_677_581_491_3673e19  # km par mégaparsec (1 pc = 3.0856775814913673e16 m)
SECONDES_PAR_AN = 3.155_76e7            # année julienne = 365.25 j × 86400 s (convention astronomique)

# Faits cosmologiques mesurés
T_CMB = 2.725                           # K — fond diffus cosmologique (COBE/FIRAS, Fixsen 2009 : 2.7255 ± 0.0006)
FRACTION_MASSE_H = 0.75                 # ~75 % d'hydrogène en masse (nucléosynthèse primordiale BBN)
FRACTION_MASSE_HE = 0.25                # ~25 % d'hélium-4 en masse (Y_p ≈ 0.245–0.25)

SOURCE = "cosmologie standard : CODATA 2018 (G), IAU (parsec/an julienne), COBE/FIRAS (T_CMB), BBN (abondances)"


def _h0_valide(H0_km_s_Mpc) -> float:
    """Valide H0 (km/s/Mpc) strictement positif et fini ; sinon ValueError (abstention, jamais un faux)."""
    if isinstance(H0_km_s_Mpc, bool) or not isinstance(H0_km_s_Mpc, (int, float)):
        raise ValueError(f"H0 doit être numérique, reçu {type(H0_km_s_Mpc).__name__}")
    H0 = float(H0_km_s_Mpc)
    if not math.isfinite(H0) or H0 <= 0.0:
        raise ValueError(f"H0 doit être fini et strictement positif, reçu {H0_km_s_Mpc!r}")
    return H0


def age_univers_hubble(H0_km_s_Mpc) -> float:
    """Temps de Hubble t_H = 1/H0, exprimé en ANNÉES. H0 en km/s/Mpc (ex. 70 -> ~1.40e10 ans)."""
    H0 = _h0_valide(H0_km_s_Mpc)
    # H0 [km/s/Mpc] -> s^-1 : on divise par le nombre de km dans un Mpc. 1/H0 en s, puis en années.
    t_hubble_s = KM_PAR_MPC / H0
    return t_hubble_s / SECONDES_PAR_AN


def abondance_primordiale() -> dict:
    """Fractions de MASSE primordiales (BBN) : ~75 % H, ~25 % He-4. Fait sourcé (copie défensive)."""
    return {"H": FRACTION_MASSE_H, "He": FRACTION_MASSE_HE}


def temperature_cmb() -> float:
    """Température du fond diffus cosmologique : 2.725 K (fait mesuré)."""
    return T_CMB


def densite_critique(H0_km_s_Mpc) -> float:
    """Densité critique de l'univers ρ_c = 3·H0²/(8πG) en kg/m³. H0 en km/s/Mpc (70 -> ~9.20e-27)."""
    H0 = _h0_valide(H0_km_s_Mpc)
    # km/s/Mpc -> s^-1 : km->m (×1000) au numérateur et Mpc->m (×1000·KM_PAR_MPC) au dénominateur => H0/KM_PAR_MPC
    H0_si = H0 / KM_PAR_MPC
    return 3.0 * H0_si ** 2 / (8.0 * math.pi * G_NEWTON)
