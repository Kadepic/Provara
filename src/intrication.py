"""
INTRICATION QUANTIQUE — inégalité de Bell / test CHSH (mandat Yohan : couvrir le borné, mécanisme VÉRIFIABLE).

Même posture que `physique` / `chimie` (la réalité juge, jamais un faux) :
  • Le MÉCANISME est EXACT — ce sont des THÉORÈMES établis, pas des opinions :
      - borne_classique_chsh() = 2  : toute théorie à variables cachées LOCALES satisfait |S| ≤ 2
        (inégalité de Bell, forme CHSH — Clauser-Horne-Shimony-Holt 1969, théorème démontré).
      - borne_quantique_chsh() = 2√2 ≈ 2.828 : borne de TSIRELSON (1980), maximum atteignable par la
        mécanique quantique pour S — théorème démontré.
      - valeur_chsh(...) : arithmétique EXACTE de la combinaison CHSH S = |E_ab − E_ab' + E_a'b + E_a'b'|.
      - viole_inegalite_bell(S) : S > 2 signe des corrélations NON reproductibles par variables cachées
        locales (donc signature d'intrication). STRICT : à S = 2 (limite classique) il n'y a PAS violation.
      - etat_bell_correlation(angle) : pour l'état SINGULET |Ψ⁻⟩, la corrélation des spins mesurés selon
        deux directions séparées de `angle` (radians) vaut E = −cos(angle) — prédiction quantique exacte.

GARANTIES (vérifiées en adverse par `valide_intrication.py`) :
  - une corrélation hors de [−1, 1] (physiquement impossible : c'est une espérance de produit de ±1) -> ValueError ;
  - une valeur S de CHSH hors de [0, 4] (max algébrique du module |·| de 4 termes dans [−1,1]) -> ValueError ;
  - type invalide (bool, str, NaN, ±inf) -> ValueError : on ne devine pas, on s'abstient ;
  - déterministe ; faux POSITIF interdit (abstention structurelle au moindre doute).

stdlib uniquement.
"""
from __future__ import annotations

import math

# ── BORNES (théorèmes) ──────────────────────────────────────────────────────────────────────────────────────────
_BORNE_CLASSIQUE = 2.0               # inégalité de Bell/CHSH : |S| ≤ 2 pour variables cachées locales
_BORNE_QUANTIQUE = 2.0 * math.sqrt(2)  # borne de Tsirelson : |S| ≤ 2√2 en mécanique quantique

SOURCE = "Bell-CHSH 1969 (|S|≤2 local) ; Tsirelson 1980 (|S|≤2√2 quantique) ; état singulet E=−cos(angle)"


# ── VALIDATION INTERNE (soundness) ──────────────────────────────────────────────────────────────────────────────
def _nombre_fini(x) -> float:
    """Accepte un réel fini ; REJETTE bool, str, complexe, NaN, ±inf -> ValueError."""
    if isinstance(x, bool):
        raise ValueError("un booléen n'est pas une corrélation")
    if not isinstance(x, (int, float)):
        raise ValueError(f"valeur non numérique : {x!r}")
    v = float(x)
    if not math.isfinite(v):
        raise ValueError("valeur non finie (NaN/inf) interdite")
    return v


def _correlation(E) -> float:
    """Une corrélation E = ⟨A·B⟩ avec A,B = ±1 est NÉCESSAIREMENT dans [−1, 1]. Sinon ValueError."""
    v = _nombre_fini(E)
    if v < -1.0 or v > 1.0:
        raise ValueError(f"corrélation hors [-1, 1] : {v}")
    return v


# ── API ─────────────────────────────────────────────────────────────────────────────────────────────────────────
def borne_classique_chsh() -> float:
    """Borne CHSH des variables cachées LOCALES : exactement 2 (inégalité de Bell)."""
    return _BORNE_CLASSIQUE


def borne_quantique_chsh() -> float:
    """Borne de Tsirelson : 2√2 ≈ 2.8284271247 (maximum quantique de S)."""
    return _BORNE_QUANTIQUE


def valeur_chsh(E_ab: float, E_ab2: float, E_a2b: float, E_a2b2: float) -> float:
    """
    Valeur CHSH S = |E_ab − E_ab' + E_a'b + E_a'b'|.
    Chaque corrélation DOIT être dans [−1, 1] (sinon ValueError).
    """
    e1 = _correlation(E_ab)
    e2 = _correlation(E_ab2)
    e3 = _correlation(E_a2b)
    e4 = _correlation(E_a2b2)
    return abs(e1 - e2 + e3 + e4)


def viole_inegalite_bell(S: float) -> bool:
    """
    True ssi S > 2 : les corrélations dépassent la borne classique -> NON reproductibles par variables
    cachées locales (signature d'intrication). STRICT : S = 2 (limite classique) -> False.
    S doit être une magnitude CHSH valide : 0 ≤ S ≤ 4 (max algébrique). Sinon ValueError.
    """
    s = _nombre_fini(S)
    if s < 0.0 or s > 4.0:
        raise ValueError(f"valeur CHSH hors du domaine [0, 4] : {s}")
    return s > _BORNE_CLASSIQUE


def etat_bell_correlation(angle: float) -> float:
    """
    Corrélation de l'état singulet |Ψ⁻⟩ pour deux directions de mesure séparées de `angle` (radians) :
    E(angle) = −cos(angle).  (angle=0 -> −1 anti-corrélation parfaite ; angle=π -> +1 ; angle=π/2 -> 0.)
    """
    a = _nombre_fini(angle)
    return -math.cos(a)
