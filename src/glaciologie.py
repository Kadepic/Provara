"""
glaciologie.py — Glaciologie : mécanismes EXACTS / lois établies (glaciers, glace, icebergs).

Fonctions pures déterministes (stdlib uniquement). Sortie arrondie à ~6 chiffres significatifs.
FAUX=0 : toute entrée physiquement invalide -> ValueError (abstention, jamais un faux résultat).

Mécanismes / constantes sourcés :

  • bilan_massique(accumulation, ablation) = accumulation − ablation
      Bilan de masse glaciaire = gain (accumulation : neige, regel) − perte (ablation : fonte,
      sublimation, vêlage). Résultat > 0 -> le glacier CROÎT ; < 0 -> il décroît ; = 0 -> stable.
      Identité comptable exacte. accumulation et ablation sont des masses/épaisseurs >= 0.
      Ex. accumulation 2, ablation 1 -> +1 (croît).

  • vitesse_deformation_glace(contrainte, A=2.4e-24, n=3) = A · σⁿ   (LOI DE GLEN)
      Loi de fluage de la glace (Glen 1955) : ε̇ = A · τⁿ, avec n ≈ 3 et A le paramètre de
      fluidité dépendant de la température. À 0 °C, A ≈ 2.4e-24 Pa⁻³·s⁻¹ (Cuffey & Paterson,
      "The Physics of Glaciers", 4e éd., tableau du paramètre de Glen). σ = contrainte
      déviatorique (Pa) >= 0. Ex. σ = 1e5 Pa -> ε̇ = 2.4e-24·(1e5)³ = 2.4e-9 s⁻¹.

  • epaisseur_equilibre(angle_pente_deg, tau0=1e5, rho_glace=917, g=9.81)
        = tau0 / (rho_glace · g · sin(angle))     (modèle de plasticité parfaite)
      À l'équilibre, la contrainte de cisaillement basale τ_b = ρ·g·h·sin(α) égale la
      contrainte seuil de la glace τ0 ≈ 100 kPa (1 bar) ; d'où l'épaisseur d'équilibre
      h = τ0 / (ρ·g·sin α). α = pente du lit en DEGRÉS, 0 < α < 90.
      Ex. α = 30°, τ0 = 1e5 -> h ≈ 22.23 m (et ρ·g·h·sin α redonne τ0).

  • fraction_emergee_iceberg(rho_glace=917, rho_eau=1025) = 1 − rho_glace/rho_eau
      Principe d'Archimède : un iceberg flotte avec une fraction immergée = ρ_glace/ρ_eau, donc
      une fraction ÉMERGÉE = 1 − ρ_glace/ρ_eau. Glace 917 kg/m³, eau de mer 1025 kg/m³ ->
      ≈ 0.105 (≈ 10 % émergé, « la partie cachée de l'iceberg »). Exige ρ_glace < ρ_eau (flotte).

ABSTENTION STRUCTURELLE (faux positif INTERDIT -> ValueError) :
  • accumulation < 0 ou ablation < 0 -> ValueError.
  • contrainte < 0, A <= 0, n <= 0, ou résultat non fini (débordement) -> ValueError.
  • angle hors ]0, 90[°, tau0 <= 0, rho_glace <= 0, g <= 0 -> ValueError.
  • densités <= 0, ou rho_glace >= rho_eau (ne flotte pas) -> ValueError.
  • toute valeur non numérique / non finie -> ValueError.
"""

import math

__all__ = [
    "bilan_massique",
    "vitesse_deformation_glace",
    "epaisseur_equilibre",
    "fraction_emergee_iceberg",
    "RHO_GLACE",
    "RHO_EAU_MER",
    "A_GLEN",
    "N_GLEN",
    "TAU0_GLACE",
]

# ── Constantes sourcées ──
RHO_GLACE = 917.0     # masse volumique de la glace de glacier (kg/m³)
RHO_EAU_MER = 1025.0  # masse volumique de l'eau de mer (kg/m³)
A_GLEN = 2.4e-24      # paramètre de fluidité de Glen à 0 °C (Pa⁻³·s⁻¹, Cuffey & Paterson)
N_GLEN = 3            # exposant de la loi de Glen (sans dimension)
TAU0_GLACE = 1.0e5    # contrainte seuil (plasticité parfaite) ≈ 100 kPa = 1 bar


def _reel_fini(x, nom):
    """Convertit en float fini, sinon ValueError (abstention)."""
    try:
        v = float(x)
    except (TypeError, ValueError):
        raise ValueError(f"{nom} non numérique : {x!r}")
    if not math.isfinite(v):
        raise ValueError(f"{nom} non fini : {x!r}")
    return v


def _arr(x):
    """Arrondit à ~6 chiffres significatifs (déterministe)."""
    if x == 0.0:
        return 0.0
    d = 6 - int(math.floor(math.log10(abs(x)))) - 1
    return round(x, d)


def bilan_massique(accumulation, ablation):
    """
    Bilan de masse glaciaire = accumulation − ablation.

    > 0 : le glacier croît ; < 0 : il décroît ; = 0 : stable.
    accumulation, ablation >= 0 (masses ou épaisseurs équivalentes en eau).
    Valeur < 0 ou non finie -> ValueError.
    """
    acc = _reel_fini(accumulation, "accumulation")
    abl = _reel_fini(ablation, "ablation")
    if acc < 0.0:
        raise ValueError(f"accumulation négative : {acc}")
    if abl < 0.0:
        raise ValueError(f"ablation négative : {abl}")
    return _arr(acc - abl)


def vitesse_deformation_glace(contrainte, A=A_GLEN, n=N_GLEN):
    """
    Vitesse de déformation (fluage) de la glace — LOI DE GLEN : ε̇ = A · σⁿ.

    contrainte σ : contrainte déviatorique (Pa), >= 0.
    A : paramètre de fluidité (Pa⁻ⁿ·s⁻¹), > 0 (défaut 2.4e-24 à 0 °C).
    n : exposant de Glen, > 0 (défaut 3).
    Renvoie le taux de déformation (s⁻¹).
    σ < 0, A <= 0, n <= 0, valeurs non finies, ou débordement -> ValueError.
    """
    sigma = _reel_fini(contrainte, "contrainte")
    a = _reel_fini(A, "A")
    nn = _reel_fini(n, "n")
    if sigma < 0.0:
        raise ValueError(f"contrainte négative : {sigma}")
    if a <= 0.0:
        raise ValueError(f"A non strictement positif : {a}")
    if nn <= 0.0:
        raise ValueError(f"n non strictement positif : {nn}")
    try:
        val = a * (sigma ** nn)
    except OverflowError:
        raise ValueError("débordement numérique dans la loi de Glen")
    if not math.isfinite(val):
        raise ValueError("résultat non fini (débordement) dans la loi de Glen")
    return _arr(val)


def epaisseur_equilibre(angle_pente_deg, tau0=TAU0_GLACE, rho_glace=RHO_GLACE, g=9.81):
    """
    Épaisseur d'équilibre d'un glacier (modèle de plasticité parfaite) :
        h = τ0 / (ρ·g·sin α).

    À l'équilibre la contrainte basale ρ·g·h·sin α égale la contrainte seuil τ0 (≈100 kPa).
    angle_pente_deg : pente du lit en DEGRÉS, 0 < α < 90.
    tau0 : contrainte seuil (Pa), > 0 (défaut 1e5).
    rho_glace : masse volumique de la glace (kg/m³), > 0 (défaut 917).
    g : pesanteur (m/s²), > 0 (défaut 9.81).
    Renvoie l'épaisseur (m).
    angle hors ]0,90[, tau0/rho/g <= 0, valeurs non finies -> ValueError.
    """
    alpha = _reel_fini(angle_pente_deg, "angle_pente_deg")
    t0 = _reel_fini(tau0, "tau0")
    rho = _reel_fini(rho_glace, "rho_glace")
    gg = _reel_fini(g, "g")
    if not (0.0 < alpha < 90.0):
        raise ValueError(f"angle hors ]0, 90[ degrés : {alpha}")
    if t0 <= 0.0:
        raise ValueError(f"tau0 non strictement positif : {t0}")
    if rho <= 0.0:
        raise ValueError(f"rho_glace non strictement positif : {rho}")
    if gg <= 0.0:
        raise ValueError(f"g non strictement positif : {gg}")
    h = t0 / (rho * gg * math.sin(math.radians(alpha)))
    if not math.isfinite(h):
        raise ValueError("résultat non fini")
    return _arr(h)


def fraction_emergee_iceberg(rho_glace=RHO_GLACE, rho_eau=RHO_EAU_MER):
    """
    Fraction ÉMERGÉE d'un iceberg flottant (principe d'Archimède) :
        f = 1 − ρ_glace/ρ_eau.

    Glace 917, eau de mer 1025 -> ≈ 0.105 (≈10 % émergé).
    rho_glace, rho_eau > 0 ; exige rho_glace < rho_eau (sinon ne flotte pas).
    Densités <= 0, ou rho_glace >= rho_eau, ou non finies -> ValueError.
    """
    rg = _reel_fini(rho_glace, "rho_glace")
    re = _reel_fini(rho_eau, "rho_eau")
    if rg <= 0.0:
        raise ValueError(f"rho_glace non strictement positif : {rg}")
    if re <= 0.0:
        raise ValueError(f"rho_eau non strictement positif : {re}")
    if rg >= re:
        raise ValueError(f"rho_glace >= rho_eau : la glace ne flotte pas ({rg} >= {re})")
    return _arr(1.0 - rg / re)
