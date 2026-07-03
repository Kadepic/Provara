"""
PHYSIQUE BORNÉE — grandeurs CALCULABLES par formule (mandat Yohan : couvrir le borné, bloc #2 « FORMULE » B-PHY).

Même posture que `chimie` / `coherence_physique` (la réalité juge, jamais un faux) :
  • Le MÉCANISME (la formule physique) est EXACT — c'est la garantie structurelle.
  • Les CONSTANTES fondamentales sont des DONNÉES SOURCÉES (SI 2019 exactes, ou CODATA 2018 mesurées). Comme les
    masses atomiques de `chimie` : le mécanisme est garanti, la constante est sourcée.
  • La sortie est ARRONDIE à 6 chiffres significatifs — précision HONNÊTE, pas un faux exact (la physique réelle
    porte des incertitudes sur G, k_e… ; on ne prétend pas à l'exactitude au-delà de la source).

GARANTIES (vérifiées en adverse par `valide_physique.py`) :
  - grandeur INCONNUE -> (HORS, None, None) : jamais une formule inventée ;
  - paramètre MANQUANT -> (HORS, …) : on ne devine pas une entrée ;
  - DOMAINE invalide (masse < 0, r ≤ 0, Th ≤ Tc, concentration ≤ 0…) -> (HORS, …) : jamais un nombre absurde ;
  - déterministe ; conservateur (faux négatif/HORS toléré, faux POSITIF interdit).

Ce module calcule la grandeur ; `coherence_physique` juge l'IMPOSSIBILITÉ (les deux faces du borné-physique).
"""
from __future__ import annotations

import math

VERIFIE = "verifie"
HORS = "hors"

# ── CONSTANTES SOURCÉES ────────────────────────────────────────────────────────────────────────────────────────
# SI 2019 = valeurs EXACTES par définition ; CODATA 2018 = valeurs MESURÉES (incertitude sur les derniers chiffres).
C_LUMIERE = 299_792_458.0           # m/s — EXACT (définition SI du mètre)
G_NEWTON = 6.674_30e-11             # m^3 kg^-1 s^-2 — CODATA 2018 (mesurée)
K_COULOMB = 8.987_551_787e9         # N m^2 C^-2 — constante de Coulomb (1/4πε0)
G_PESANTEUR = 9.806_65              # m/s^2 — gravité standard (BIPM, conventionnelle)
H_PLANCK = 6.626_070_15e-34         # J s — EXACT (SI 2019)
E_CHARGE = 1.602_176_634e-19        # C — EXACT (SI 2019)
N_AVOGADRO = 6.022_140_76e23        # mol^-1 — EXACT (SI 2019)
R_GAZ = 8.314_462_618               # J mol^-1 K^-1 — CODATA 2018
K_BOLTZMANN = 1.380_649e-23         # J/K — EXACT (SI 2019)

SOURCE = "constantes SI 2019 (exactes) / CODATA 2018 (mesurées)"

_CHIFFRES_SIGNIFICATIFS = 6


def _sig(x: float, n: int = _CHIFFRES_SIGNIFICATIFS) -> float:
    """Arrondit à n chiffres significatifs (précision honnête, indépendante de la magnitude)."""
    if x == 0:
        return 0.0
    return float(f"{x:.{n}g}")


def _pos(*xs) -> bool:
    return all(isinstance(x, (int, float)) and not isinstance(x, bool) and x > 0 for x in xs)


def _nb(*xs) -> bool:
    return all(isinstance(x, (int, float)) and not isinstance(x, bool) for x in xs)


# ── BIBLIOTHÈQUE DE GRANDEURS ──────────────────────────────────────────────────────────────────────────────────
# Chaque entrée : nom -> (clés requises, garde de domaine, formule, unité). La garde renvoie False -> HORS (jamais
# un nombre hors domaine physique). La formule reçoit le dict de paramètres validés.
_GRANDEURS: dict[str, tuple] = {
    # ── Mécanique classique (II.1) ──
    "quantite_mouvement": (("m", "v"), lambda p: _nb(p["m"], p["v"]) and p["m"] >= 0,
                           lambda p: p["m"] * p["v"], "kg·m/s"),
    "energie_cinetique": (("m", "v"), lambda p: _nb(p["m"], p["v"]) and p["m"] >= 0,
                          lambda p: 0.5 * p["m"] * p["v"] ** 2, "J"),
    "energie_potentielle_pesanteur": (("m", "h"), lambda p: _nb(p["m"], p["h"]) and p["m"] >= 0,
                                      lambda p: p["m"] * G_PESANTEUR * p["h"], "J"),
    "force_poids": (("m",), lambda p: _nb(p["m"]) and p["m"] >= 0,
                    lambda p: p["m"] * G_PESANTEUR, "N"),
    "force_newton": (("m", "a"), lambda p: _nb(p["m"], p["a"]) and p["m"] >= 0,
                     lambda p: p["m"] * p["a"], "N"),
    "travail": (("force", "deplacement"), lambda p: _nb(p["force"], p["deplacement"]),
                lambda p: p["force"] * p["deplacement"], "J"),
    "energie_repos": (("m",), lambda p: _nb(p["m"]) and p["m"] >= 0,
                      lambda p: p["m"] * C_LUMIERE ** 2, "J"),
    "moment_force": (("force", "bras_levier"), lambda p: _nb(p["force"], p["bras_levier"]),
                     lambda p: p["force"] * p["bras_levier"], "N·m"),
    # ── Thermodynamique (II.2) ──
    "rendement_carnot": (("Tc", "Th"), lambda p: _pos(p["Tc"], p["Th"]) and p["Th"] > p["Tc"],
                         lambda p: 1 - p["Tc"] / p["Th"], "(sans unité)"),
    "cop_carnot_pompe": (("Tc", "Th"), lambda p: _pos(p["Tc"], p["Th"]) and p["Th"] > p["Tc"],
                         lambda p: p["Th"] / (p["Th"] - p["Tc"]), "(sans unité)"),
    "cop_carnot_froid": (("Tc", "Th"), lambda p: _pos(p["Tc"], p["Th"]) and p["Th"] > p["Tc"],
                         lambda p: p["Tc"] / (p["Th"] - p["Tc"]), "(sans unité)"),
    "energie_gaz_parfait": (("n", "T"), lambda p: _pos(p["T"]) and _nb(p["n"]) and p["n"] >= 0,
                            lambda p: 1.5 * p["n"] * R_GAZ * p["T"], "J"),
    "premier_principe": (("Q", "W"), lambda p: _nb(p["Q"], p["W"]),
                         lambda p: p["Q"] - p["W"], "J"),
    # ── Électromagnétisme (II.3) ──
    "force_coulomb": (("q1", "q2", "r"), lambda p: _nb(p["q1"], p["q2"]) and _pos(p["r"]),
                      lambda p: K_COULOMB * p["q1"] * p["q2"] / p["r"] ** 2, "N"),
    "champ_electrique": (("q", "r"), lambda p: _nb(p["q"]) and _pos(p["r"]),
                         lambda p: K_COULOMB * p["q"] / p["r"] ** 2, "N/C"),
    "energie_photon": (("frequence",), lambda p: _pos(p["frequence"]),
                       lambda p: H_PLANCK * p["frequence"], "J"),
    "vitesse_onde": (("frequence", "longueur_onde"), lambda p: _pos(p["frequence"], p["longueur_onde"]),
                     lambda p: p["frequence"] * p["longueur_onde"], "m/s"),
    "loi_ohm_tension": (("R", "I"), lambda p: _nb(p["R"], p["I"]) and p["R"] >= 0,
                        lambda p: p["R"] * p["I"], "V"),
    "puissance_electrique": (("U", "I"), lambda p: _nb(p["U"], p["I"]),
                             lambda p: p["U"] * p["I"], "W"),
    # ── Astronomie / mécanique céleste (VII.1) ──
    "vitesse_liberation": (("M", "r"), lambda p: _pos(p["M"], p["r"]),
                           lambda p: math.sqrt(2 * G_NEWTON * p["M"] / p["r"]), "m/s"),
    "gravite_surface": (("M", "r"), lambda p: _pos(p["M"], p["r"]),
                        lambda p: G_NEWTON * p["M"] / p["r"] ** 2, "m/s²"),
    "periode_orbitale": (("a", "M"), lambda p: _pos(p["a"], p["M"]),
                         lambda p: 2 * math.pi * math.sqrt(p["a"] ** 3 / (G_NEWTON * p["M"])), "s"),
    # ── Physique nucléaire (II.5) ──
    "energie_masse_defaut": (("delta_m",), lambda p: _nb(p["delta_m"]) and p["delta_m"] >= 0,
                             lambda p: p["delta_m"] * C_LUMIERE ** 2, "J"),
    "decroissance_radioactive": (("N0", "t", "demi_vie"),
                                 lambda p: _nb(p["N0"]) and p["N0"] >= 0 and _nb(p["t"]) and p["t"] >= 0
                                 and _pos(p["demi_vie"]),
                                 lambda p: p["N0"] * 0.5 ** (p["t"] / p["demi_vie"]), "(nombre)"),
    # ── Chimie physique (III.1) ──
    "ph": (("concentration_H",), lambda p: _pos(p["concentration_H"]),
           lambda p: -math.log10(p["concentration_H"]), "(sans unité)"),
    "poh": (("concentration_OH",), lambda p: _pos(p["concentration_OH"]),
            lambda p: -math.log10(p["concentration_OH"]), "(sans unité)"),
}


def grandeurs() -> list[str]:
    """Liste des grandeurs calculables (pour introspection / routage)."""
    return sorted(_GRANDEURS)


def calcule(grandeur: str, params: dict) -> tuple[str, float | None, str | None]:
    """Calcule une grandeur physique. Renvoie (VERIFIE, valeur_arrondie, unité) ou (HORS, None, None).

    Conservateur : grandeur inconnue, paramètre manquant ou domaine invalide -> HORS (jamais un nombre faux).
    """
    spec = _GRANDEURS.get(grandeur)
    if spec is None:
        return (HORS, None, None)                       # grandeur inconnue : jamais une formule inventée
    cles, garde, formule, unite = spec
    if not isinstance(params, dict) or any(k not in params for k in cles):
        return (HORS, None, None)                       # paramètre manquant : on ne devine pas
    try:
        if not garde(params):
            return (HORS, None, None)                   # domaine physique invalide
        val = formule(params)
    except (ValueError, ZeroDivisionError, OverflowError, TypeError):
        return (HORS, None, None)
    if not math.isfinite(val):
        return (HORS, None, None)
    return (VERIFIE, _sig(val), unite)
