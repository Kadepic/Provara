"""
LIMITES USUELLES — limites de suites et fonctions usuelles (PARTIE I, B-NEC).

Même posture FAUX=0 que `geometries_non_euclidiennes` / `galois` (le théorème juge, jamais un faux) :
  • Le MÉCANISME est un THÉORÈME EXACT, pas une corrélation :
      – Fraction rationnelle en ±∞ : P(x)/Q(x) avec deg P = n, deg Q = m et dominants a, b se comporte
        comme (a/b)·x^(n−m) quand x → +∞. Donc :  n < m -> 0 ;  n = m -> a/b (EXACT, Fraction) ;
        n > m -> +∞ si a/b > 0, −∞ si a/b < 0.  (Théorème du terme dominant, analyse classique.)
      – Suite géométrique rⁿ : |r| < 1 -> 0 ; r = 1 -> 1 ; r > 1 -> +∞ ; r ≤ −1 -> divergente sans limite
        (oscillation non amortie).  (Convergence des suites géométriques, analyse classique.)
      – CATALOGUE de limites usuelles ÉTABLIES (faits sourcés, cours d'analyse classique) :
            sin(x)/x -> 1 (x→0) ; (1−cos x)/x² -> 1/2 (x→0) ; (eˣ−1)/x -> 1 (x→0) ; ln(1+x)/x -> 1 (x→0) ;
            (1+1/n)ⁿ -> e ; ln(x)/x -> 0 (x→+∞) ; x·ln(x) -> 0 (x→0⁺) ; eˣ/xⁿ -> +∞ (x→+∞) ;
            n!^(1/n)/n -> 1/e (Stirling).
  • La partie EXACTE (rationnelles, géométrique) travaille en fractions.Fraction : les FLOTTANTS sont
    REFUSÉS en entrée (ValueError). Aucun flottant n'intervient dans le calcul exact.
  • Dans le catalogue, e et 1/e sont IRRATIONNELS : la valeur numérique rendue est APPROCHÉE, arrondie à
    10 chiffres significatifs, et MARQUÉE `approchee=True`. Les limites rationnelles du catalogue
    (1, 1/2, 0) sont EXACTES (Fraction) ; '+inf' est un symbole, pas un nombre.

GARANTIES (vérifiées en adverse par `valide_limites_usuelles.py`) :
  - dénominateur nul (tous coefficients nuls) -> ValueError ;
  - coefficients flottants, bool, str, NaN, inf -> ValueError (la partie exacte refuse le flottant) ;
  - listes de coefficients vides ou non-séquences -> ValueError ;
  - raison géométrique flottante / bool / str -> ValueError ;
  - forme HORS catalogue -> ValueError (abstention : on ne devine JAMAIS une limite) ;
  - déterministe ; conservateur (faux négatif/abstention toléré, faux POSITIF interdit).

Toutes les fonctions sont PURES et déterministes ; le module n'importe que `math` et `fractions` (stdlib).
NOTE : `limite.py` de ce repo traite de bornes PHYSIQUES (Carnot/Betz) — rien à voir ; il n'est pas importé.
"""
from __future__ import annotations

import math
from fractions import Fraction

SOURCE = ("théorème du terme dominant (limites de fractions rationnelles en ±∞) ; convergence des suites "
          "géométriques ; limites remarquables classiques (sin x/x, e, Stirling) — analyse réelle standard")

PLUS_INF = "+inf"
MOINS_INF = "-inf"
DIVERGENTE = "divergente_sans_limite"

_CHIFFRES_SIGNIFICATIFS = 10


def _sig(x: float, n: int = _CHIFFRES_SIGNIFICATIFS) -> float:
    """Arrondit à n chiffres significatifs (précision honnête d'une valeur APPROCHÉE)."""
    if x == 0:
        return 0.0
    return float(f"{x:.{n}g}")


def _exige_exact(c) -> Fraction:
    """Coefficient EXACT : int ou Fraction uniquement. bool/float/str/complexe -> ValueError."""
    if isinstance(c, bool):
        raise ValueError("coefficient invalide : bool refusé (True n'est pas 1)")
    if isinstance(c, (int, Fraction)):
        return Fraction(c)
    raise ValueError("coefficient invalide : int ou fractions.Fraction requis "
                     "(flottant REFUSÉ — la partie exacte n'admet aucun flottant)")


def _exige_coeffs(coeffs, nom: str) -> list:
    """Séquence non vide de coefficients exacts, degré DÉCROISSANT (dominant en tête)."""
    if not isinstance(coeffs, (list, tuple)) or len(coeffs) == 0:
        raise ValueError(f"{nom} invalide : liste/tuple non vide de coefficients requis "
                         "(degré décroissant, coefficient dominant en tête)")
    return [_exige_exact(c) for c in coeffs]


# ── (a) FRACTION RATIONNELLE EN +∞ ─────────────────────────────────────────────────────────────────────────────
def limite_rationnelle_infini(num_coeffs, den_coeffs):
    """Limite en x → +∞ de P(x)/Q(x), coefficients EXACTS en degré DÉCROISSANT (dominant en tête).

    Théorème du terme dominant :
      deg P < deg Q -> Fraction(0) ;  deg P = deg Q -> rapport EXACT des dominants (Fraction) ;
      deg P > deg Q -> '+inf' ou '-inf' selon le signe du rapport des dominants.
    Dénominateur nul (tous coefficients nuls) -> ValueError. Flottants -> ValueError."""
    num = _exige_coeffs(num_coeffs, "num_coeffs")
    den = _exige_coeffs(den_coeffs, "den_coeffs")
    # degré réel : on retire les zéros de tête (un coefficient dominant nul n'est pas dominant)
    while num and num[0] == 0:
        num = num[1:]
    while den and den[0] == 0:
        den = den[1:]
    if not den:
        raise ValueError("den_coeffs nul : le polynôme dénominateur est identiquement nul (division par zéro)")
    if not num:
        return Fraction(0)          # numérateur identiquement nul : P/Q = 0 partout où Q ≠ 0
    deg_num = len(num) - 1
    deg_den = len(den) - 1
    if deg_num < deg_den:
        return Fraction(0)
    if deg_num == deg_den:
        return num[0] / den[0]      # rapport EXACT des coefficients dominants (Fraction)
    # deg_num > deg_den : divergence, signe donné par le rapport des dominants (x → +∞, x^(n−m) > 0)
    return PLUS_INF if num[0] / den[0] > 0 else MOINS_INF


# ── (b) SUITE GÉOMÉTRIQUE rⁿ ───────────────────────────────────────────────────────────────────────────────────
def limite_suite_geometrique(r):
    """Limite de la suite géométrique (rⁿ), raison r EXACTE (int ou Fraction ; flottant REFUSÉ).

    |r| < 1 -> Fraction(0) ; r = 1 -> Fraction(1) ; r > 1 -> '+inf' ; r ≤ −1 -> 'divergente_sans_limite'."""
    r = _exige_exact(r)
    if abs(r) < 1:
        return Fraction(0)
    if r == 1:
        return Fraction(1)
    if r > 1:
        return PLUS_INF
    return DIVERGENTE               # r ≤ −1 : (−1)ⁿ oscille, |r|>1 oscille en explosant — pas de limite


# ── (c) CATALOGUE DE LIMITES USUELLES ÉTABLIES ─────────────────────────────────────────────────────────────────
# Chaque entrée : (point, valeur, approchee, référence). Les valeurs irrationnelles (e, 1/e) sont APPROCHÉES
# à 10 chiffres significatifs et marquées comme telles ; les rationnelles sont EXACTES (Fraction).
_E_APPROCHE = _sig(math.e)          # e ≈ 2.718281828 — APPROCHÉ (e est irrationnel, Hermite 1873 : transcendant)
_INV_E_APPROCHE = _sig(1.0 / math.e)  # 1/e ≈ 0.3678794412 — APPROCHÉ

_CATALOGUE = {
    "sin(x)/x": ("x->0", Fraction(1), False,
                 "limite remarquable sin(x)/x -> 1 en 0 (encadrement cos x < sin x / x < 1)"),
    "(1-cos(x))/x^2": ("x->0", Fraction(1, 2), False,
                       "limite remarquable (1-cos x)/x² -> 1/2 en 0 (développement cos x = 1 - x²/2 + o(x²))"),
    "(exp(x)-1)/x": ("x->0", Fraction(1), False,
                     "limite remarquable (e^x - 1)/x -> 1 en 0 (dérivée de exp en 0)"),
    "ln(1+x)/x": ("x->0", Fraction(1), False,
                  "limite remarquable ln(1+x)/x -> 1 en 0 (dérivée de ln en 1)"),
    "(1+1/n)^n": ("n->+inf", _E_APPROCHE, True,
                  "définition classique du nombre e : (1+1/n)^n -> e (valeur APPROCHÉE, e irrationnel)"),
    "ln(x)/x": ("x->+inf", Fraction(0), False,
                "croissance comparée : ln(x)/x -> 0 en +∞ (le logarithme est négligeable devant x)"),
    "x*ln(x)": ("x->0+", Fraction(0), False,
                "croissance comparée : x·ln(x) -> 0 en 0⁺ (x l'emporte sur ln x)"),
    "exp(x)/x^n": ("x->+inf", PLUS_INF, False,
                   "croissance comparée : e^x/x^n -> +∞ en +∞ pour tout n fixé (l'exponentielle domine)"),
    "n!^(1/n)/n": ("n->+inf", _INV_E_APPROCHE, True,
                   "formule de Stirling : (n!)^(1/n)/n -> 1/e (valeur APPROCHÉE, 1/e irrationnel)"),
}


def catalogue_limites() -> tuple:
    """Noms des formes du catalogue (tuple trié, déterministe)."""
    return tuple(sorted(_CATALOGUE))


def limite_usuelle(nom: str) -> dict:
    """Limite usuelle ÉTABLIE pour la forme `nom` (clé exacte du catalogue).

    Renvoie {'forme', 'point', 'valeur', 'approchee', 'reference'}. La valeur est une Fraction EXACTE,
    ou un flottant MARQUÉ approché (e, 1/e), ou le symbole '+inf'.
    Forme HORS catalogue -> ValueError (abstention : on ne devine jamais une limite)."""
    if not isinstance(nom, str) or isinstance(nom, bool):
        raise ValueError("nom invalide : une chaîne (clé du catalogue) est requise")
    if nom not in _CATALOGUE:
        raise ValueError(f"forme inconnue du catalogue : {nom!r} — abstention "
                         f"(formes connues : {', '.join(sorted(_CATALOGUE))})")
    point, valeur, approchee, reference = _CATALOGUE[nom]
    return {"forme": nom, "point": point, "valeur": valeur, "approchee": approchee, "reference": reference}
