"""
ÉQUATIONS DIFFÉRENTIELLES LINÉAIRES du 2e ORDRE à coefficients CONSTANTS — mécanisme EXACT, FAUX=0.

Le 1er ordre scalaire (y'=k·y, y'=a·y+b) est traité par `equa_diff` (réservé, non modifié) et simplement
DÉLÉGUÉ ici. Ce module résout, EXACTEMENT, l'équation homogène du 2e ordre

        a·y'' + b·y' + c·y = 0      (a ≠ 0)

par l'ÉQUATION CARACTÉRISTIQUE  a·r² + b·r + c = 0. Théorème classique (Euler / d'Alembert), pas une
corrélation : le comportement est entièrement fixé par le discriminant Δ = b² − 4ac, via TROIS régimes.

  • Δ > 0 : deux racines réelles distinctes r1 < r2   ->  y = C1·e^(r1 x) + C2·e^(r2 x)   ('aperiodique')
  • Δ = 0 : racine double r = −b/(2a)               ->  y = (C1 + C2·x)·e^(r x)          ('critique')
  • Δ < 0 : racines complexes α ± iβ                ->  y = e^(α x)·(C1·cos βx + C2·sin βx) ('pseudo-periodique')
            avec α = −b/(2a) et β = √(−Δ)/(2|a|) > 0.

EXACTITUDE : si a, b, c sont donnés en entiers ou `Fraction` (valeurs EXACTES), le discriminant est renvoyé
comme `Fraction` exact, et les racines/constantes le restent quand elles sont rationnelles (√ parfait, racine
double, partie réelle). Là où une racine carrée irrationnelle apparaît, on passe au flottant et la valeur est
alors APPROCHÉE (marquée telle par son type `float`). L'ÉVALUATION numérique de la solution est flottante.

POSTURE FAUX=0 (abstention structurelle, jamais un faux positif) :
  • a = 0  -> ValueError (ce n'est plus une équation du 2e ordre ; le 1er ordre relève de `equa_diff`) ;
  • bool / str / complexe / NaN / ±inf en entrée -> ValueError ;
  • `resout_cauchy` RE-VÉRIFIE que la solution construite satisfait bien y(0)=y0 ET y'(0)=yp0 à 1e-9 près ;
    tout écart -> RuntimeError (on refuse de rendre une solution qui ne respecte pas ses propres conditions) ;
  • `oscillateur_amorti` exige m>0, k>0, c≥0 (sinon ValueError) et rend le régime physique + ω₀ + ζ.

GARANTIES vérifiées en adverse par `valide_edo_lineaires.py` : ancres NON circulaires (y''−3y'+2y=0 -> e^(2x)−e^x,
y''+2y'+y=0 -> (1+x)e^(−x), y''+y=0 -> sin x), ancre CROISÉE (la solution satisfait l'EDO, testée par différences
finies centrées), soundness (bool/str/NaN/inf/a=0/arité), déterminisme.

Toutes les fonctions sont PURES et déterministes ; stdlib uniquement (math, fractions).
"""
from __future__ import annotations

import math
from fractions import Fraction

import equa_diff  # 1er ordre scalaire (réservé) — délégation uniquement, n'importe que math

SOURCE = "équation caractéristique des EDO linéaires à coefficients constants (Euler / d'Alembert, cours classique)"

_CHIFFRES_SIGNIFICATIFS = 10
_TOL_VERIF = 1e-9


def _sig(x: float, n: int = _CHIFFRES_SIGNIFICATIFS) -> float:
    """Arrondit un flottant à n chiffres significatifs (précision honnête, indépendante de la magnitude)."""
    if x == 0:
        return 0.0
    return float(f"{x:.{n}g}")


def _coef(x, nom: str):
    """Coefficient EXACT si int/Fraction (-> Fraction), APPROCHÉ si float fini. bool/str/complexe/NaN/inf -> ValueError."""
    if isinstance(x, bool):
        raise ValueError(f"coefficient {nom} invalide : un booléen n'est pas un nombre")
    if isinstance(x, Fraction):
        return x
    if isinstance(x, int):
        return Fraction(x)
    if isinstance(x, float):
        if not math.isfinite(x):
            raise ValueError(f"coefficient {nom} invalide : NaN/inf refusé")
        return x
    raise ValueError(f"coefficient {nom} invalide : réel (int/float/Fraction) attendu, reçu {x!r}")


def _sqrt_frac_exact(f: Fraction):
    """√f exact (Fraction) si f>0 est un carré parfait rationnel, sinon None."""
    p, q = f.numerator, f.denominator
    sp, sq = math.isqrt(p), math.isqrt(q)
    if sp * sp == p and sq * sq == q:
        return Fraction(sp, sq)
    return None


def _analyse(a, b, c) -> dict:
    """Analyse EXACTE de a·y''+b·y'+c·y=0 via a·r²+b·r+c=0. Renvoie discriminant + nature + racines.

    a=0 -> ValueError (pas du 2e ordre). Structure : nature ∈ {reelles_distinctes, reelle_double, complexes}.
    """
    a = _coef(a, "a")
    b = _coef(b, "b")
    c = _coef(c, "c")
    if a == 0:
        raise ValueError("a = 0 : ce n'est pas une équation du 2e ordre (le 1er ordre relève de equa_diff)")
    disc = b * b - 4 * a * c
    if disc > 0:
        # deux racines réelles distinctes ; exactes si Δ carré parfait rationnel
        s = _sqrt_frac_exact(disc) if isinstance(disc, Fraction) else None
        if s is not None:
            r1 = (-b - s) / (2 * a)
            r2 = (-b + s) / (2 * a)
        else:
            sf = math.sqrt(float(disc))
            af, bf = float(a), float(b)
            r1 = (-bf - sf) / (2 * af)
            r2 = (-bf + sf) / (2 * af)
        if r1 > r2:
            r1, r2 = r2, r1
        return {"discriminant": disc, "nature": "reelles_distinctes", "r1": r1, "r2": r2}
    if disc == 0:
        r = -b / (2 * a)  # Fraction si a,b exacts
        return {"discriminant": disc, "nature": "reelle_double", "r": r}
    # disc < 0 : racines complexes α ± iβ
    alpha = -b / (2 * a)
    negd = -disc
    s = _sqrt_frac_exact(negd) if isinstance(negd, Fraction) else None
    if s is not None:
        beta = s / (2 * abs(a))
    else:
        beta = math.sqrt(float(negd)) / (2 * abs(float(a)))
    return {"discriminant": disc, "nature": "complexes", "alpha": alpha, "beta": beta}


# ── (a) ÉQUATION CARACTÉRISTIQUE ────────────────────────────────────────────────────────────────────────────────
def equation_caracteristique(a, b, c) -> dict:
    """Équation caractéristique de a·y''+b·y'+c·y=0 : renvoie {'discriminant','nature','racines'}.

    'discriminant' est EXACT (Fraction) si a,b,c sont exacts. 'racines' :
      • reelles_distinctes -> (r1, r2) avec r1 < r2 ;
      • reelle_double      -> (r, r) ;
      • complexes          -> (α+iβ, α−iβ) sous forme de nombres complexes (β > 0).
    a = 0 -> ValueError.
    """
    d = _analyse(a, b, c)
    nat = d["nature"]
    if nat == "reelles_distinctes":
        racines = (d["r1"], d["r2"])
    elif nat == "reelle_double":
        racines = (d["r"], d["r"])
    else:
        af, bf = float(d["alpha"]), float(d["beta"])
        racines = (complex(af, bf), complex(af, -bf))
    return {"discriminant": d["discriminant"], "nature": nat, "racines": racines}


# ── (b) SOLUTION HOMOGÈNE (les trois régimes) ───────────────────────────────────────────────────────────────────
def solution_homogene(a, b, c) -> dict:
    """Solution générale de a·y''+b·y'+c·y=0 : {'regime','racines','forme','discriminant'}.

    regime ∈ {'aperiodique','critique','pseudo-periodique'} ; 'forme' = expression littérale de la solution
    générale (avec constantes libres C1, C2). a = 0 -> ValueError.
    """
    d = _analyse(a, b, c)
    nat = d["nature"]
    if nat == "reelles_distinctes":
        r1, r2 = d["r1"], d["r2"]
        return {
            "regime": "aperiodique",
            "racines": (r1, r2),
            "forme": "C1*exp(r1*x) + C2*exp(r2*x)",
            "discriminant": d["discriminant"],
        }
    if nat == "reelle_double":
        r = d["r"]
        return {
            "regime": "critique",
            "racines": (r, r),
            "forme": "(C1 + C2*x)*exp(r*x)",
            "discriminant": d["discriminant"],
        }
    alpha, beta = d["alpha"], d["beta"]
    return {
        "regime": "pseudo-periodique",
        "racines": (complex(float(alpha), float(beta)), complex(float(alpha), -float(beta))),
        "forme": "exp(alpha*x)*(C1*cos(beta*x) + C2*sin(beta*x))",
        "discriminant": d["discriminant"],
    }


# ── (c) PROBLÈME DE CAUCHY (conditions initiales) ───────────────────────────────────────────────────────────────
def _exige_ic(v, nom: str):
    return _coef(v, nom)


def resout_cauchy(a, b, c, y0, yp0) -> dict:
    """Résout le problème de Cauchy a·y''+b·y'+c·y=0, y(0)=y0, y'(0)=yp0.

    Détermine C1, C2 par le système 2×2 (exact si tout est exact) et renvoie
        {'regime', 'racines', 'C1', 'C2', 'solution'}
    où 'solution' est une fonction x -> y(x) (flottante). VÉRIFICATION INTERNE : on re-teste que la solution
    satisfait y(0)=y0 et y'(0)=yp0 à 1e-9 près ; sinon RuntimeError. a = 0 -> ValueError.
    """
    d = _analyse(a, b, c)
    y0 = _exige_ic(y0, "y0")
    yp0 = _exige_ic(yp0, "yp0")
    nat = d["nature"]

    if nat == "reelles_distinctes":
        r1, r2 = d["r1"], d["r2"]
        # C1+C2=y0 ; r1 C1 + r2 C2 = yp0  ->  C2=(yp0 - r1 y0)/(r2-r1), C1=y0-C2
        C2 = (yp0 - r1 * y0) / (r2 - r1)
        C1 = y0 - C2
        r1f, r2f, C1f, C2f = float(r1), float(r2), float(C1), float(C2)

        def solution(x):
            return C1f * math.exp(r1f * x) + C2f * math.exp(r2f * x)

        yp_at_0 = C1f * r1f + C2f * r2f
        racines = (r1, r2)

    elif nat == "reelle_double":
        r = d["r"]
        # y(0)=C1=y0 ; y'(0)=C2 + r C1 = yp0  ->  C2 = yp0 - r y0
        C1 = y0
        C2 = yp0 - r * y0
        rf, C1f, C2f = float(r), float(C1), float(C2)

        def solution(x):
            return (C1f + C2f * x) * math.exp(rf * x)

        yp_at_0 = C2f + C1f * rf
        racines = (r, r)

    else:  # complexes
        alpha, beta = d["alpha"], d["beta"]
        # y(0)=C1=y0 ; y'(0)=α C1 + β C2 = yp0  ->  C2=(yp0 - α y0)/β
        C1 = y0
        C2 = (yp0 - alpha * y0) / beta
        af, bf, C1f, C2f = float(alpha), float(beta), float(C1), float(C2)

        def solution(x):
            return math.exp(af * x) * (C1f * math.cos(bf * x) + C2f * math.sin(bf * x))

        yp_at_0 = af * C1f + bf * C2f
        racines = (complex(af, bf), complex(af, -bf))

    # VÉRIFICATION INTERNE FAUX=0 : la solution respecte-t-elle ses propres conditions initiales ?
    y_at_0 = solution(0.0)
    if abs(y_at_0 - float(y0)) > _TOL_VERIF or abs(yp_at_0 - float(yp0)) > _TOL_VERIF:
        raise RuntimeError(
            f"vérification interne échouée : y(0)={y_at_0} (attendu {float(y0)}), "
            f"y'(0)={yp_at_0} (attendu {float(yp0)})"
        )

    return {
        "regime": {"reelles_distinctes": "aperiodique",
                   "reelle_double": "critique",
                   "complexes": "pseudo-periodique"}[nat],
        "racines": racines,
        "C1": C1,
        "C2": C2,
        "solution": solution,
    }


# ── (d) OSCILLATEUR AMORTI (régime physique) ────────────────────────────────────────────────────────────────────
def _reel_phys(x, nom: str) -> float:
    """Réel fini pour la physique (bool/str/NaN/inf refusés). Renvoie un float."""
    if isinstance(x, bool):
        raise ValueError(f"{nom} invalide : un booléen n'est pas une mesure")
    if isinstance(x, Fraction):
        return float(x)
    if isinstance(x, (int, float)):
        v = float(x)
        if not math.isfinite(v):
            raise ValueError(f"{nom} invalide : NaN/inf refusé")
        return v
    raise ValueError(f"{nom} invalide : réel attendu, reçu {x!r}")


def oscillateur_amorti(m, c, k) -> dict:
    """Régime de l'oscillateur m·y''+c·y'+k·y=0 (masse-ressort-amortisseur).

    Renvoie {'regime','pulsation_propre','facteur_amortissement'} avec
        ω₀ = √(k/m)   (pulsation propre, rad/s, APPROCHÉE, 10 chiffres significatifs)
        ζ  = c/(2√(m·k))   (facteur d'amortissement, sans dimension)
    Régime par le discriminant c²−4mk : >0 'sur-amorti', =0 'critique', <0 'sous-amorti'.
    Exige m>0, k>0, c≥0 (sinon ValueError). La détection du régime est EXACTE quand m,c,k sont exacts.
    """
    # Détection EXACTE du régime quand les entrées sont exactes (int/Fraction) : évite les faux critiques flottants.
    mm = _coef(m, "m")
    cc = _coef(c, "c")
    kk = _coef(k, "k")
    mf, cf, kf = _reel_phys(m, "m"), _reel_phys(c, "c"), _reel_phys(k, "k")
    if mf <= 0:
        raise ValueError("m invalide : masse strictement positive requise")
    if kf <= 0:
        raise ValueError("k invalide : raideur strictement positive requise")
    if cf < 0:
        raise ValueError("c invalide : amortissement ≥ 0 requis")

    disc = cc * cc - 4 * mm * kk  # Fraction si tout exact, float sinon
    if disc > 0:
        regime = "sur-amorti"
    elif disc == 0:
        regime = "critique"
    else:
        regime = "sous-amorti"

    omega0 = math.sqrt(kf / mf)
    zeta = cf / (2.0 * math.sqrt(mf * kf))
    return {
        "regime": regime,
        "pulsation_propre": _sig(omega0),
        "facteur_amortissement": _sig(zeta),
    }


# ── (e) 1er ORDRE — DÉLÉGATION à equa_diff (réservé) ────────────────────────────────────────────────────────────
def resout_premier_ordre(y0, k, t) -> float:
    """1er ordre y'=k·y : y(t)=y₀·e^(k·t). Délégué EXACTEMENT à equa_diff.solution_exponentielle."""
    return equa_diff.solution_exponentielle(y0, k, t)


def resout_premier_ordre_affine(y0, a, b, t) -> float:
    """1er ordre y'=a·y+b : délégué EXACTEMENT à equa_diff.solution_affine (point d'équilibre −b/a)."""
    return equa_diff.solution_affine(y0, a, b, t)


if __name__ == "__main__":
    print("y''-3y'+2y=0 :", equation_caracteristique(1, -3, 2))
    print("y''+2y'+y=0  :", equation_caracteristique(1, 2, 1))
    print("y''+y=0      :", equation_caracteristique(1, 0, 1))
    s = resout_cauchy(1, -3, 2, 0, 1)
    print("e^2-e ~ 4.6707742705 -> ", s["solution"](1.0), "C1,C2 =", s["C1"], s["C2"])
    print("oscillateur (1,2,1) :", oscillateur_amorti(1, 2, 1))
