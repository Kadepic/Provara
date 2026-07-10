"""
CINÉMATIQUE UNIFORMÉMENT ACCÉLÉRÉE — mouvement rectiligne à accélération CONSTANTE.

Même posture FAUX=0 que `physique` / `geometries_non_euclidiennes` (la réalité juge, jamais un faux) :
  • Le MÉCANISME est le jeu d'équations EXACTES du mouvement uniformément accéléré (intégration directe
    de a = dv/dt constant, calcul classique depuis Galilée) :
      – v(t)  = v0 + a·t                       (vitesse à l'instant t)
      – x(t)  = x0 + v0·t + ½·a·t²             (position à l'instant t)
      – v²    = v0² + 2·a·Δx                   (équation de Torricelli, indépendante du temps)
      – t     = (v − v0) / a                   (temps pour atteindre une vitesse donnée, a ≠ 0)
      – ½·a·t² + v0·t + (x0 − x) = 0           (temps pour atteindre une position : équation du second
        degré, DISCRIMINANT D = v0² + 2·a·(x − x0) ; a ≠ 0, racines par la forme NUMÉRIQUEMENT STABLE
        q = −(v0 + signe(v0)·√D)/2, t1 = 2·q/a, t2 = (x0 − x)/q — dite « Citardauq » ; la forme naïve
        (−v0 + √D)/a subit une ANNULATION CATASTROPHIQUE quand |v0| ≈ √D et rendrait des temps faux)
  • Les sorties sont ARRONDIES à 10 chiffres significatifs — précision honnête (les entrées sont des
    flottants de mesure, on ne prétend pas à l'exactitude au-delà) ; elles sont donc APPROCHÉES à ce grain.
  • Le RÉSULTAT est EXIGÉ FINI : tout débordement flottant (inf/NaN en sortie ou dans le discriminant)
    -> ValueError. On refuse d'émettre un inf là où le réel est un nombre fini (abstention, jamais un faux).

GARANTIES (vérifiées en adverse par `valide_cinematique_uniformement_acceleree.py`) :
  - t < 0  -> ValueError  (une durée est positive ou nulle ; pas d'extrapolation vers le passé) ;
  - a = 0 dans `temps_pour_vitesse` / `temps_pour_position`  -> ValueError  (la formule DÉGÉNÈRE :
    division par zéro / plus une équation du second degré ; abstention plutôt qu'un résultat trompeur) ;
  - discriminant < 0 dans `temps_pour_position`  -> ValueError  (AUCUN temps réel : la position n'est
    jamais atteinte) ; aucune racine ≥ 0  -> ValueError  (position atteinte seulement dans le passé) ;
  - v² calculé négatif dans `vitesse_carre`  -> ValueError  (aucune vitesse réelle : Δx inatteignable) ;
  - temps calculé négatif dans `temps_pour_vitesse`  -> ValueError  (vitesse jamais atteinte à t ≥ 0) ;
  - DÉBORDEMENT flottant (résultat ou discriminant non fini)  -> ValueError  (le réel est fini ; un inf
    en sortie serait un faux plat, on s'abstient) ;
  - types invalides (bool, str, complexe, NaN, ±inf)  -> ValueError ;
  - déterministe ; conservateur (faux négatif/abstention toléré, faux POSITIF interdit).

Toutes les fonctions sont PURES et déterministes ; le module n'importe que `math` (stdlib).
"""
from __future__ import annotations

import math

SOURCE = "équations du mouvement uniformément accéléré (Galilée) + équation de Torricelli v² = v0² + 2·a·Δx"

_CHIFFRES_SIGNIFICATIFS = 10


def _sig(x: float, n: int = _CHIFFRES_SIGNIFICATIFS) -> float:
    """Arrondit à n chiffres significatifs (précision honnête, indépendante de la magnitude)."""
    if x == 0:
        return 0.0
    return float(f"{x:.{n}g}")


def _resultat(x: float, nom: str) -> float:
    """Garde de SORTIE : exige un résultat FINI puis l'arrondit à 10 chiffres significatifs.

    Un débordement flottant (inf/NaN issu du calcul, ou arrondi qui franchit le plus grand flottant)
    -> ValueError : le réel est fini, émettre un inf serait un faux positif."""
    if not math.isfinite(x):
        raise ValueError(f"{nom} : débordement flottant (résultat non fini) ; abstention plutôt qu'un faux")
    r = _sig(x)
    if not math.isfinite(r):  # arrondi à 10 chiffres qui franchit le plus grand flottant représentable
        raise ValueError(f"{nom} : débordement flottant à l'arrondi ; abstention plutôt qu'un faux")
    return r


def _est_reel(x) -> bool:
    """True ssi x est un réel fini (les bool sont REFUSÉS : True n'est pas une mesure)."""
    return isinstance(x, (int, float)) and not isinstance(x, bool) and math.isfinite(x)


def _exige_reel(x, nom: str) -> float:
    if not _est_reel(x):
        raise ValueError(f"{nom} invalide : un réel fini est requis (bool/str/NaN/inf refusés)")
    return float(x)


def _exige_duree(t) -> float:
    """Une durée t est un réel fini ≥ 0 (pas d'extrapolation vers le passé)."""
    t = _exige_reel(t, "t (durée)")
    if t < 0:
        raise ValueError("t (durée) invalide : un réel positif ou nul est requis")
    return t


# ── VITESSE À L'INSTANT t : v = v0 + a·t ─────────────────────────────────────────────────────────────────────
def vitesse_finale(v0: float, a: float, t: float) -> float:
    """Vitesse à l'instant t : v = v0 + a·t (unités SI cohérentes ; APPROCHÉE à 10 chiffres significatifs).

    t < 0 -> ValueError ; bool/str/NaN/inf -> ValueError ; résultat non fini (débordement) -> ValueError."""
    v0 = _exige_reel(v0, "v0 (vitesse initiale)")
    a = _exige_reel(a, "a (accélération)")
    t = _exige_duree(t)
    return _resultat(v0 + a * t, "v (vitesse finale)")


# ── POSITION À L'INSTANT t : x = x0 + v0·t + ½·a·t² ──────────────────────────────────────────────────────────
def position(x0: float, v0: float, a: float, t: float) -> float:
    """Position à l'instant t : x = x0 + v0·t + ½·a·t² (APPROCHÉE à 10 chiffres significatifs).

    t < 0 -> ValueError ; bool/str/NaN/inf -> ValueError ; résultat non fini (débordement) -> ValueError."""
    x0 = _exige_reel(x0, "x0 (position initiale)")
    v0 = _exige_reel(v0, "v0 (vitesse initiale)")
    a = _exige_reel(a, "a (accélération)")
    t = _exige_duree(t)
    return _resultat(x0 + v0 * t + 0.5 * a * t * t, "x (position)")


# ── ÉQUATION DE TORRICELLI : v² = v0² + 2·a·Δx ───────────────────────────────────────────────────────────────
def vitesse_carre(v0: float, a: float, delta_x: float) -> float:
    """Carré de la vitesse après un déplacement Δx : v² = v0² + 2·a·Δx (Torricelli, sans le temps).

    Renvoie v² (APPROCHÉ à 10 chiffres significatifs). Si v² < 0 -> ValueError (AUCUNE vitesse réelle :
    ce déplacement n'est pas atteignable avec ces conditions). bool/str/NaN/inf -> ValueError ;
    résultat non fini (débordement, p. ex. v0² > plus grand flottant) -> ValueError."""
    v0 = _exige_reel(v0, "v0 (vitesse initiale)")
    a = _exige_reel(a, "a (accélération)")
    delta_x = _exige_reel(delta_x, "delta_x (déplacement)")
    v2 = v0 * v0 + 2.0 * a * delta_x
    if not math.isfinite(v2):
        raise ValueError("v² : débordement flottant (résultat non fini) ; abstention plutôt qu'un faux")
    if v2 < 0:
        raise ValueError("v² < 0 : aucune vitesse réelle (déplacement inatteignable avec ces conditions)")
    return _resultat(v2, "v² (Torricelli)")


# ── TEMPS POUR ATTEINDRE UNE VITESSE : t = (v − v0)/a ────────────────────────────────────────────────────────
def temps_pour_vitesse(v0: float, v: float, a: float) -> float:
    """Temps pour passer de v0 à v : t = (v − v0)/a (APPROCHÉ à 10 chiffres significatifs).

    a = 0 -> ValueError (la formule dégénère : division par zéro) ;
    t calculé < 0 -> ValueError (la vitesse n'est jamais atteinte pour t ≥ 0) ;
    bool/str/NaN/inf -> ValueError ; résultat non fini (débordement) -> ValueError."""
    v0 = _exige_reel(v0, "v0 (vitesse initiale)")
    v = _exige_reel(v, "v (vitesse visée)")
    a = _exige_reel(a, "a (accélération)")
    if a == 0:
        raise ValueError("a = 0 : la formule t = (v − v0)/a dégénère (division par zéro) ; abstention")
    t = (v - v0) / a
    if not math.isfinite(t):
        raise ValueError("t : débordement flottant (résultat non fini) ; abstention plutôt qu'un faux")
    if t < 0:
        raise ValueError("t < 0 : la vitesse visée n'est jamais atteinte pour t ≥ 0 ; abstention")
    return _resultat(t, "t (temps pour vitesse)")


# ── TEMPS POUR ATTEINDRE UNE POSITION : discriminant de ½·a·t² + v0·t + (x0 − x) = 0 ─────────────────────────
def temps_pour_position(x0: float, v0: float, a: float, x: float) -> float:
    """PLUS PETIT temps t ≥ 0 tel que x0 + v0·t + ½·a·t² = x (APPROCHÉ à 10 chiffres significatifs).

    Résolution par discriminant : ½·a·t² + v0·t + (x0 − x) = 0, D = v0² + 2·a·(x − x0), racines par la
    forme NUMÉRIQUEMENT STABLE (« Citardauq ») : q = −(v0 + signe(v0)·√D)/2, t1 = 2·q/a, t2 = (x0 − x)/q.
    (La forme naïve (−v0 + √D)/a subit une annulation catastrophique quand |v0| ≈ √D — elle rendrait par
    exemple t = 0 au lieu de t ≈ 10 s pour x0=0, v0=1, a=1e-300, x=10 : un faux plat. Ici, chaque racine
    est calculée SANS soustraction de quantités proches.) ABSTENTIONS :
      a = 0 -> ValueError (plus une équation du second degré : la formule dégénère) ;
      D < 0 -> ValueError (AUCUN temps réel : la position n'est jamais atteinte) ;
      D non fini (débordement flottant) -> ValueError (le calcul déborde, on ne devine pas) ;
      aucune racine ≥ 0 -> ValueError (position atteinte seulement dans le passé) ;
      plus petite racine ≥ 0 non finie (débordement) -> ValueError ;
      bool/str/NaN/inf -> ValueError."""
    x0 = _exige_reel(x0, "x0 (position initiale)")
    v0 = _exige_reel(v0, "v0 (vitesse initiale)")
    a = _exige_reel(a, "a (accélération)")
    x = _exige_reel(x, "x (position visée)")
    if a == 0:
        raise ValueError("a = 0 : plus une équation du second degré (formule dégénérée) ; abstention")
    discriminant = v0 * v0 + 2.0 * a * (x - x0)
    if not math.isfinite(discriminant):
        raise ValueError("discriminant : débordement flottant (non fini) ; abstention plutôt qu'un faux")
    if discriminant < 0:
        raise ValueError("discriminant < 0 : aucun temps réel (la position n'est jamais atteinte) ; abstention")
    racine = math.sqrt(discriminant)
    # Forme STABLE (Citardauq) : q additionne v0 et √D de MÊME SIGNE (aucune annulation possible) ;
    # t1 = 2·q/a et t2 = (x0 − x)/q donnent les deux racines (produit des racines = 2·(x0 − x)/a).
    q = -(v0 + math.copysign(racine, v0)) / 2.0
    if q == 0.0:
        # q = 0 ssi v0 = 0 ET D = 0, donc x = x0 : la position est atteinte à t = 0 (racine double).
        return 0.0
    t1 = 2.0 * q / a
    t2 = (x0 - x) / q
    candidats = [t for t in (t1, t2) if t >= 0]
    if not candidats:
        raise ValueError("aucune racine ≥ 0 : la position n'est atteinte que dans le passé ; abstention")
    return _resultat(min(candidats), "t (temps pour position)")
