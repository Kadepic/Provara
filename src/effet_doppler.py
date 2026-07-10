"""
EFFET DOPPLER — acoustique (source/observateur mobiles dans un milieu) et relativiste longitudinal.

Même posture FAUX=0 que `physique` / `geometries_non_euclidiennes` (la réalité/le théorème juge, jamais un faux) :
  • Le MÉCANISME est une LOI EXACTE, pas une corrélation :
      – ACOUSTIQUE : pour des ondes de célérité v dans un milieu au repos,
            f' = f · (v + v_obs) / (v − v_src)
        CONVENTION DOCUMENTÉE : v_obs > 0 si l'OBSERVATEUR s'approche de la source ;
        v_src > 0 si la SOURCE s'approche de l'observateur (mouvements sur la ligne source-observateur).
        L'effet n'est PAS symétrique (le milieu matériel brise la symétrie) : source qui s'approche à u
        et observateur qui s'approche à u donnent des f' différents.
      – RELATIVISTE LONGITUDINAL (lumière, pas de milieu) :
            f' = f · sqrt((1 + β) / (1 − β)),   β = v/c > 0 au RAPPROCHEMENT, β < 0 à l'éloignement.
  • Célérité du son : V_SON_AIR_20C = 343 m/s (air sec à 20 °C — valeur classique des tables acoustiques).
  • PRÉCISION : sorties flottantes arrondies à 10 chiffres significatifs — APPROCHÉES, on le dit.
    Exception honnête : quand le facteur relativiste est un rationnel EXACT (le rapport (1+β)/(1−β) est un
    carré parfait de rationnel, ex. β = 3/5 -> facteur 2), il est appliqué exactement, sans erreur flottante.

GARANTIES (vérifiées en adverse par `valide_effet_doppler.py`) :
  - f ≤ 0 -> ValueError (une fréquence est strictement positive) ;
  - v ≤ 0 -> ValueError (une célérité est strictement positive) ;
  - |v_src| ≥ v -> ValueError : v_src ≥ v est le MUR DU SON (dénominateur nul ou négatif, la formule ment) ;
    v_src ≤ −v (source supersonique en éloignement) est REFUSÉ par conservatisme (cône de Mach, régime
    hors modèle) — abstention au doute, jamais un chiffre douteux ;
  - |v_obs| ≥ v -> ValueError : v_obs ≤ −v donnerait f' ≤ 0 (l'observateur fuit plus vite que l'onde,
    aucun son ne l'atteint) ; le régime supersonique est refusé en bloc par conservatisme ;
  - |β| ≥ 1 -> ValueError (rien ne dépasse c ; β = ±1 rendrait f' nul ou infini) ;
  - types invalides (bool, str, complexe, NaN, ±inf) -> ValueError ;
  - DÉBORDEMENT/SOUS-DÉBORDEMENT FLOTTANT du résultat -> ValueError : le vrai f' est toujours strictement
    positif et fini (démontré par les gardes sur les entrées), donc un résultat qui sort en ±inf ou en 0.0
    est une VALEUR FAUSSE de l'arithmétique flottante, jamais émise — abstention structurelle ;
  - déterministe ; conservateur (faux négatif/abstention toléré, faux POSITIF interdit).

Toutes les fonctions sont PURES et déterministes ; le module n'importe que `math` et `fractions` (stdlib).
"""
from __future__ import annotations

import math
from fractions import Fraction

SOURCE = ("effet Doppler classique f' = f·(v+v_obs)/(v−v_src) (acoustique, milieu au repos) ; "
          "Doppler relativiste longitudinal f' = f·sqrt((1+β)/(1−β)) (relativité restreinte) ; "
          "célérité du son 343 m/s dans l'air sec à 20 °C (tables acoustiques classiques)")

V_SON_AIR_20C = 343.0  # m/s — air sec à 20 °C (valeur classique sourcée, cf. SOURCE)

_CHIFFRES_SIGNIFICATIFS = 10


def _sig(x: float, n: int = _CHIFFRES_SIGNIFICATIFS) -> float:
    """Arrondit à n chiffres significatifs (précision honnête, indépendante de la magnitude)."""
    if x == 0:
        return 0.0
    return float(f"{x:.{n}g}")


def _sortie_hz(brut: float) -> float:
    """Arrondit à 10 chiffres significatifs et REFUSE tout débordement/sous-débordement flottant.

    Le f' mathématiquement vrai est STRICTEMENT POSITIF et FINI (garanti par les gardes d'entrée :
    f > 0, dénominateurs > 0, |β| < 1). Si l'arithmétique flottante rend ±inf (débordement) ou 0.0
    (sous-débordement), c'est un artefact FAUX -> ValueError, jamais une valeur émise (FAUX=0)."""
    arrondi = _sig(brut)
    if not math.isfinite(arrondi) or arrondi <= 0.0:
        raise ValueError("f' hors de la plage flottante représentable (débordement vers inf ou "
                         "sous-débordement vers 0, alors que la vraie valeur est strictement positive "
                         "et finie) -> abstention plutôt qu'une valeur fausse")
    return arrondi


def _est_reel(x) -> bool:
    """True ssi x est un réel fini (les bool sont REFUSÉS : True n'est pas une mesure)."""
    return isinstance(x, (int, float)) and not isinstance(x, bool) and math.isfinite(x)


def _exige_frequence(f) -> float:
    if not _est_reel(f) or f <= 0:
        raise ValueError("fréquence f invalide : un réel strictement positif (Hz) est requis")
    return float(f)


# ── DOPPLER ACOUSTIQUE ─────────────────────────────────────────────────────────────────────────────────────────
def doppler_acoustique(f: float, v_src: float = 0.0, v_obs: float = 0.0,
                       v: float = V_SON_AIR_20C) -> float:
    """Fréquence perçue f' = f·(v + v_obs)/(v − v_src)  (Hz, arrondie à 10 chiffres significatifs).

    CONVENTION : v_obs > 0 si l'observateur s'APPROCHE de la source ; v_src > 0 si la source s'APPROCHE
    de l'observateur ; valeurs négatives = éloignement. v = célérité de l'onde (343 m/s par défaut).

    ABSTENTIONS : f ≤ 0, v ≤ 0, |v_src| ≥ v (mur du son / régime supersonique hors modèle),
    |v_obs| ≥ v (fuite supersonique : aucun son reçu ; approche supersonique refusée par conservatisme),
    bool/str/NaN/±inf, résultat hors plage flottante (débordement/sous-débordement) -> ValueError."""
    f = _exige_frequence(f)
    if not _est_reel(v) or v <= 0:
        raise ValueError("célérité v invalide : un réel strictement positif (m/s) est requis")
    if not _est_reel(v_src):
        raise ValueError("v_src invalide : un réel fini (m/s) est requis (bool/NaN/inf refusés)")
    if not _est_reel(v_obs):
        raise ValueError("v_obs invalide : un réel fini (m/s) est requis (bool/NaN/inf refusés)")
    if abs(v_src) >= v:
        raise ValueError("|v_src| ≥ v : mur du son (dénominateur nul/négatif) ou régime supersonique "
                         "hors du modèle Doppler classique -> abstention")
    if abs(v_obs) >= v:
        raise ValueError("|v_obs| ≥ v : l'observateur atteint ou dépasse la célérité de l'onde "
                         "(fuite = aucun son reçu ; approche supersonique hors modèle) -> abstention")
    return _sortie_hz(f * (v + float(v_obs)) / (v - float(v_src)))


# ── DOPPLER RELATIVISTE LONGITUDINAL ───────────────────────────────────────────────────────────────────────────
def _exige_beta(beta) -> Fraction:
    """β = v/c en Fraction EXACTE (float converti sans perte) ; |β| ≥ 1 ou type invalide -> ValueError."""
    if isinstance(beta, bool) or not isinstance(beta, (int, float, Fraction)):
        raise ValueError("β invalide : un réel (int, float ou Fraction) est requis (bool/str refusés)")
    if isinstance(beta, float) and not math.isfinite(beta):
        raise ValueError("β invalide : NaN/±inf refusés")
    b = Fraction(beta)  # exact (un float EST un rationnel dyadique)
    if not (-1 < b < 1):
        raise ValueError("|β| ≥ 1 : aucune source massive n'atteint c ; f' serait nul ou infini -> abstention")
    return b


def doppler_relativiste_longitudinal(f: float, beta) -> float:
    """Fréquence perçue f' = f·sqrt((1+β)/(1−β))  (Doppler relativiste, mouvement longitudinal).

    CONVENTION : β = v/c > 0 au RAPPROCHEMENT (f' > f, blueshift), β < 0 à l'éloignement (redshift).
    β accepte int, float ou fractions.Fraction (converti exactement).

    EXACTITUDE : si (1+β)/(1−β) est le carré parfait d'un rationnel (ex. β=3/5 -> 4 -> facteur 2),
    le facteur est appliqué EXACTEMENT ; sinon la sortie est APPROCHÉE (10 chiffres significatifs).

    ABSTENTIONS : f ≤ 0, |β| ≥ 1, bool/str/NaN/±inf, résultat hors plage flottante
    (débordement/sous-débordement) -> ValueError."""
    f = _exige_frequence(f)
    b = _exige_beta(beta)
    ratio = (1 + b) / (1 - b)  # Fraction exacte, strictement positive car |β| < 1
    rn, rd = ratio.numerator, ratio.denominator
    sn, sd = math.isqrt(rn), math.isqrt(rd)
    try:
        if sn * sn == rn and sd * sd == rd:
            # carré parfait de rationnel : facteur EXACT, aucune erreur flottante introduite ici
            brut = f * sn / sd
        else:
            brut = f * math.sqrt(rn / rd)
    except OverflowError:
        # entiers de Fraction trop grands pour le flottant (β extrême) : même abstention, jamais un faux
        raise ValueError("f' hors de la plage flottante représentable (facteur relativiste trop extrême "
                         "pour l'arithmétique flottante) -> abstention plutôt qu'une valeur fausse")
    return _sortie_hz(brut)
