"""
DIMENSIONNEMENT D'UNE STRUCTURE SOUS CHARGE DONNÉE (PARTIE IX, B-PHY).

Même posture FAUX=0 que `structures_genie` / `physique` (la réalité/la norme juge, jamais un faux) :
  • `structures_genie.py` CALCULE des effets (contrainte, flèche, moment quadratique, charge critique
    d'Euler) depuis une géométrie DONNÉE ; il ne DIMENSIONNE pas (aucune comparaison à un admissible).
    `proprietes_mecaniques_materiaux.py` porte les limites élastiques Re en INTERVALLES (min, majorant).
    CE module ajoute la VÉRIFICATION et le DIMENSIONNEMENT en s'appuyant sur les deux (importés, jamais
    modifiés).

MÉCANISME (formules EXACTES de résistance des matériaux + convention de sécurité) :
  (a) contrainte_admissible(materiau, γ) = Re_min / γ.  On prend le MINIMUM de l'intervalle de limite
      élastique : dimensionner sur la borne HAUTE (Re_max) surestimerait la résistance garantie et serait
      DANGEREUX. Le minimum est la seule borne que TOUTE nuance conforme atteint — c'est la posture sûre.
  (b) verifie_section(materiau, σ_appliquée, γ) -> 'sûr' | 'insuffisant' | 'indéterminé'. On compare σ à
      l'encadrement [Re_min/γ, Re_max/γ] : σ < Re_min/γ -> 'sûr' (même la nuance la plus faible tient avec
      la marge γ) ; σ > Re_max/γ -> 'insuffisant' (même la plus forte n'y arrive pas) ; σ DANS l'encadrement
      -> 'indéterminé' (on ne tranche pas ce que l'intervalle ne tranche pas — cœur du FAUX=0).
  (c) dimensionne_poutre_rectangulaire(M, materiau, γ, b) : plus petite hauteur h telle que la contrainte
      de flexion σ = 6·M/(b·h²) ≤ σ_adm. Inversion EXACTE : h = sqrt(6·M/(b·σ_adm)).
      Unités « ingénieur » cohérentes : M en N·mm, b et h en mm, σ_adm en MPa (= N/mm²).
  (d) verifie_flambement(force, longueur, E, I, mode_appui) : coefficient de sécurité au flambement =
      P_cr / force, où P_cr = π²·E·I / (K·L)² est la charge critique d'Euler (DÉLÉGUÉE à structures_genie
      via une longueur effective K·L). Unités SI (force N, longueur m, E Pa, I m⁴). Facteurs K classiques.
  (e) verifie_fleche(flèche, portée, limite_relative) : critère de SERVICE flèche ≤ portée / limite_relative
      (souvent L/300). C'est une CONVENTION NORMATIVE (confort/fissuration), PAS une loi physique — dit
      explicitement. Renvoie 'conforme' | 'non conforme'.
  (f) INVARIANT FAUX=0 : la hauteur dimensionnée en (c), réinjectée dans structures_genie (conversion SI,
      chemin de code INDÉPENDANT), doit produire une contrainte ≤ σ_adm (à 1e-6 près). Sinon -> RuntimeError.

ABSTENTIONS (structurelles) :
  • matériau fragile/sans limite conventionnelle (béton, verre, fonte, bois) : limite_elastique lève
    ValueError -> propagé (aucune pseudo-limite inventée) ;
  • γ ≤ 1 -> ValueError (un coefficient de sécurité ≤ 1 n'en est pas un) ;
  • M ≤ 0, b ≤ 0, force/longueur/E/I ≤ 0, portée ≤ 0, limite_relative ≤ 0 -> ValueError ;
  • mode d'appui inconnu -> ValueError ;
  • types invalides (bool, str, NaN, ±inf) -> ValueError.

GARANTIES (vérifiées en adverse par `valide_dimensionnement_structure.py`) :
  - boucle fermée dimensionnement -> structures_genie : σ réinjectée ≤ σ_adm ;
  - déterministe, pur, sans état mutable ; conservateur (faux négatif toléré, faux POSITIF interdit).

Sorties APPROCHÉES (sqrt, divisions physiques) arrondies à 10 chiffres significatifs — précision honnête,
jamais un faux « exact ». Le facteur K du cas encastré-rotulé (0.6992) est lui-même APPROCHÉ (racine d'une
équation transcendante) et marqué comme tel.

Stdlib uniquement (math). Importe structures_genie et proprietes_mecaniques_materiaux (non modifiés).
"""
from __future__ import annotations

import math

import structures_genie as _rdm
import proprietes_mecaniques_materiaux as _mat

SOURCE = ("résistance des matériaux (Euler-Bernoulli, flexion σ=6M/bh², flambement d'Euler) + "
          "convention de sécurité Re_min/γ ; critère de flèche = convention normative (Eurocodes, ~L/300)")

_CHIFFRES_SIGNIFICATIFS = 10

# Facteurs de longueur effective K de l'Euler selon les appuis (théorie classique du flambement).
#   rotulé-rotulé (bi-articulé) : K=1   (EXACT)
#   encastré-encastré           : K=0.5 (EXACT, théorique)
#   encastré-libre (console)    : K=2   (EXACT, théorique)
#   encastré-rotulé             : K≈0.6992 (APPROCHÉ : racine de tan(x)=x -> 0.699…)
_FACTEURS_K = {
    "rotulé-rotulé": 1.0,
    "encastré-encastré": 0.5,
    "encastré-libre": 2.0,
    "encastré-rotulé": 0.6992,   # APPROCHÉ
}


def _sig(x: float, n: int = _CHIFFRES_SIGNIFICATIFS) -> float:
    """Arrondit à n chiffres significatifs (précision honnête, indépendante de la magnitude)."""
    if x == 0:
        return 0.0
    return float(f"{x:.{n}g}")


def _reel_fini(x, nom: str) -> float:
    """Exige un réel FINI (rejette bool — True n'est pas 1 —, str, None, NaN, ±inf)."""
    if isinstance(x, bool) or not isinstance(x, (int, float)):
        raise ValueError(f"{nom} invalide : un nombre réel est requis, reçu {x!r}")
    f = float(x)
    if not math.isfinite(f):
        raise ValueError(f"{nom} invalide : NaN/inf refusés")
    return f


def _positif_strict(x, nom: str) -> float:
    """Exige un réel fini STRICTEMENT positif."""
    f = _reel_fini(x, nom)
    if f <= 0:
        raise ValueError(f"{nom} invalide : une grandeur strictement positive est requise, reçu {x!r}")
    return f


def _positif_ou_nul(x, nom: str) -> float:
    """Exige un réel fini ≥ 0 (flèche, contrainte)."""
    f = _reel_fini(x, nom)
    if f < 0:
        raise ValueError(f"{nom} invalide : une grandeur ≥ 0 est requise, reçu {x!r}")
    return f


def _exige_gamma(gamma) -> float:
    """Coefficient de sécurité : réel fini STRICTEMENT > 1 (γ ≤ 1 n'est pas une sécurité)."""
    g = _reel_fini(gamma, "coefficient de sécurité γ")
    if g <= 1.0:
        raise ValueError(f"coefficient de sécurité γ invalide : γ > 1 requis (reçu {gamma!r} ≤ 1)")
    return g


# ── (a) CONTRAINTE ADMISSIBLE ────────────────────────────────────────────────────────────────────────────────────
def contrainte_admissible(materiau: str, coefficient_securite) -> float:
    """Contrainte admissible σ_adm = Re_min / γ (MPa).

    On prend le MINIMUM de l'intervalle de limite élastique (borne garantie par toute nuance conforme) :
    dimensionner sur la borne haute Re_max serait DANGEREUX. Matériau fragile/sans limite -> ValueError
    (propagé depuis proprietes_mecaniques_materiaux). γ ≤ 1 -> ValueError. Résultat APPROCHÉ (10 c.s.)."""
    g = _exige_gamma(coefficient_securite)
    re_min, _re_max = _mat.limite_elastique(materiau)   # lève ValueError si fragile / hors catalogue
    return _sig(re_min / g)


# ── (b) VÉRIFICATION DE SECTION ──────────────────────────────────────────────────────────────────────────────────
def verifie_section(materiau: str, contrainte_appliquee, gamma) -> str:
    """La section tient-elle sous σ_appliquée (MPa), avec le coefficient γ ?

    Compare σ à l'encadrement [Re_min/γ, Re_max/γ] :
      • σ < Re_min/γ   -> 'sûr'          (même la nuance la plus faible garde la marge γ) ;
      • σ > Re_max/γ   -> 'insuffisant'  (même la nuance la plus forte n'y arrive pas) ;
      • σ ∈ [.. , ..]  -> 'indéterminé'  (l'intervalle de Re ne tranche pas -> on ne tranche pas).
    Matériau fragile/sans limite -> ValueError. γ ≤ 1 -> ValueError. σ < 0 ou non réel -> ValueError."""
    g = _exige_gamma(gamma)
    sigma = _positif_ou_nul(contrainte_appliquee, "contrainte appliquée")
    re_min, re_max = _mat.limite_elastique(materiau)     # lève ValueError si fragile / hors catalogue
    adm_min = re_min / g
    adm_max = re_max / g
    if sigma < adm_min:
        return "sûr"
    if sigma > adm_max:
        return "insuffisant"
    return "indéterminé"


# ── (c) DIMENSIONNEMENT D'UNE POUTRE RECTANGULAIRE EN FLEXION ────────────────────────────────────────────────────
def dimensionne_poutre_rectangulaire(moment_flechissant, materiau: str, gamma, largeur) -> float:
    """Hauteur MINIMALE h (mm) d'une section rectangulaire b×h telle que σ = 6·M/(b·h²) ≤ σ_adm.

    Unités « ingénieur » cohérentes : M en N·mm, b (largeur) en mm -> h en mm ; σ_adm = Re_min/γ en MPa.
    Inversion EXACTE de la contrainte de flexion : h = sqrt(6·M/(b·σ_adm)).

    INVARIANT (f) : la hauteur obtenue, réinjectée dans structures_genie (conversion SI, chemin de code
    INDÉPENDANT), doit produire σ ≤ σ_adm (à 1e-6 près). Sinon -> RuntimeError (garde FAUX=0).

    M ≤ 0 -> ValueError ; b ≤ 0 -> ValueError ; γ ≤ 1 -> ValueError ; matériau fragile -> ValueError.
    Résultat APPROCHÉ (sqrt), arrondi à 10 chiffres significatifs."""
    M = _positif_strict(moment_flechissant, "moment fléchissant M")       # N·mm
    b = _positif_strict(largeur, "largeur b")                            # mm
    sigma_adm = contrainte_admissible(materiau, gamma)                   # MPa (= N/mm²) ; valide γ & matériau
    h = math.sqrt(6.0 * M / (b * sigma_adm))                            # mm

    # ── INVARIANT (f) : boucle fermée via structures_genie, en unités SI (chemin indépendant) ──
    M_Nm = M / 1000.0            # N·mm -> N·m  (1 N·m = 1000 N·mm)
    b_m = b / 1000.0            # mm  -> m
    h_m = h / 1000.0            # mm  -> m
    I_m4 = _rdm.moment_quadratique_rectangle(b_m, h_m)                   # b·h³/12  (m⁴)
    sigma_Pa = _rdm.contrainte_flexion(M_Nm, I_m4, h_m / 2.0)           # M·y/I avec y = h/2  (Pa)
    sigma_reinj_MPa = sigma_Pa / 1.0e6
    if sigma_reinj_MPa > sigma_adm * (1.0 + 1.0e-6):
        raise RuntimeError(
            f"INVARIANT VIOLÉ : σ réinjectée {sigma_reinj_MPa} MPa > σ_adm {sigma_adm} MPa "
            f"(h={h} mm) — le dimensionnement ne garantit pas la tenue")
    return _sig(h)


# ── (d) VÉRIFICATION AU FLAMBEMENT (EULER) ───────────────────────────────────────────────────────────────────────
def verifie_flambement(force, longueur, E, I, mode_appui: str) -> float:
    """Coefficient de sécurité au flambement = P_cr / force, avec P_cr = π²·E·I/(K·L)² (charge d'Euler).

    Unités SI : force N (compression, > 0), longueur L m, E Pa, I m⁴, tous > 0. La charge critique est
    DÉLÉGUÉE à structures_genie.flambement_euler via la longueur effective K·L. Facteurs K (mode_appui) :
    'rotulé-rotulé'=1, 'encastré-encastré'=0.5, 'encastré-libre'=2 (exacts), 'encastré-rotulé'≈0.6992
    (APPROCHÉ). Mode inconnu -> ValueError. Argument ≤ 0 ou non réel -> ValueError.
    Coefficient > 1 : stable ; < 1 : flambe. Résultat APPROCHÉ (10 c.s.)."""
    P = _positif_strict(force, "force de compression")
    L = _positif_strict(longueur, "longueur L")
    Emod = _positif_strict(E, "module de Young E")
    Imom = _positif_strict(I, "moment quadratique I")
    if isinstance(mode_appui, bool) or not isinstance(mode_appui, str):
        raise ValueError("mode d'appui invalide : un nom (str) est requis")
    cle = " ".join(mode_appui.strip().lower().split())
    if cle not in _FACTEURS_K:
        raise ValueError(f"mode d'appui inconnu : {mode_appui!r} (attendus : {sorted(_FACTEURS_K)})")
    K = _FACTEURS_K[cle]
    L_eff = K * L
    P_cr = _rdm.flambement_euler(Emod, Imom, L_eff)   # π²·E·I/L_eff²  (N)
    return _sig(P_cr / P)


# ── (e) VÉRIFICATION DE FLÈCHE (CRITÈRE DE SERVICE — CONVENTION NORMATIVE) ────────────────────────────────────────
def verifie_fleche(fleche_calculee, portee, limite_relative) -> str:
    """Critère de SERVICE : la flèche reste-t-elle sous portée / limite_relative (souvent L/300) ?

    ATTENTION : ce N'EST PAS une loi physique mais une CONVENTION NORMATIVE (confort, non-fissuration des
    finitions ; valeurs L/250, L/300, L/500 selon les Eurocodes et l'usage). flèche et portée dans la MÊME
    unité. Renvoie 'conforme' si flèche ≤ portée/limite_relative, sinon 'non conforme'.
    portée ≤ 0, limite_relative ≤ 0, flèche < 0 ou non réel -> ValueError."""
    f = _positif_ou_nul(fleche_calculee, "flèche calculée")
    L = _positif_strict(portee, "portée")
    n = _positif_strict(limite_relative, "limite relative (dénominateur, ex. 300)")
    admissible = L / n
    return "conforme" if f <= admissible else "non conforme"


if __name__ == "__main__":
    print("σ_adm acier doux γ=1.5 :", contrainte_admissible("acier doux", 1.5), "MPa")
    print("verifie_section 50 MPa :", verifie_section("acier doux", 50, 1.5))
    print("h poutre (M=1e7 N·mm, b=100 mm) :", dimensionne_poutre_rectangulaire(1e7, "acier doux", 1.5, 100), "mm")
    I_carre = _rdm.moment_quadratique_rectangle(0.05, 0.05)
    print("coef sécurité flambement (F=100kN) :", verifie_flambement(100e3, 3.0, 210e9, I_carre, "rotulé-rotulé"))
    print("verifie_fleche (10mm, 3000mm, 300) :", verifie_fleche(10, 3000, 300))
