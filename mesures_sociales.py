"""
MESURES SOCIALES — faits sociaux MESURABLES (statistiques d'inégalité et de pauvreté, calculs EXACTS).

Même posture que `physique` / `essais_cliniques` (la réalité juge, jamais un faux) :
  • Le MÉCANISME (les définitions statistiques) est EXACT — statistique sociale établie (OCDE, Eurostat, PNUD).
  • Les calculs sont des combinatoires RATIONNELLES sans constante mesurée : on garde la pleine précision flottante
    (aucun arrondi qui simulerait un faux exact ; les égalités exactes — Gini d'une distribution égale = 0 — sont
    structurelles).
  • Toute entrée hors domaine (revenu négatif, population ≤ 0, courbe de Lorenz mal formée, indice ∉ [0,1]…)
    lève ValueError (ABSTENTION) — jamais un nombre absurde, jamais un faux.

DÉFINITIONS (établies — statistique sociale) :
  - Coefficient de Gini d'un échantillon de revenus (formule des rangs, ÉQUIVALENTE à la différence absolue
    moyenne) :
        G = ( 2·Σ_i i·x_(i) − (n+1)·Σ_i x_(i) ) / ( n·Σ_i x_(i) )       x_(i) trié croissant, 1 ≤ i ≤ n
      identité exacte :  G = ( Σ_i Σ_j |x_i − x_j| ) / ( 2·n²·x̄ )      (vérifiée en adverse, non circulaire)
      domaine : G ∈ [0, (n−1)/n] ⊂ [0,1)  (0 = égalité parfaite ; tend vers 1 quand une part détient tout).
  - Gini d'une COURBE DE LORENZ donnée par parts cumulées de revenu de groupes de population ÉGAUX (quantiles) :
        G = 1 − 2·A,  A = aire sous la Lorenz affine par morceaux = (1/(2n))·Σ_{i=1}^n (L_{i-1}+L_i),  L_0 = 0
      soit  G = 1 − (1/n)·Σ_{i=1}^n (L_{i-1}+L_i).
  - Taux de pauvreté        = effectif sous le seuil / population totale                       (proportion ∈ [0,1]).
  - Seuil de pauvreté       = fraction · revenu médian   (convention européenne Eurostat : 60 % du médian ;
                              variantes OCDE 40 %/50 %).
  - Médiane                 = valeur centrale (moyenne des deux centrales si effectif pair).
  - Indice de dimension     = (valeur − min) / (max − min)   (normalisation min–max PNUD sur les bornes fournies).
  - IDH (agrégation 2010+)  = moyenne géométrique des trois indices de dimension  = (I_santé·I_éduc·I_revenu)^(1/3).

PROPRIÉTÉS structurelles (vérifiées en adverse, non circulaires) :
  • Gini invariant par permutation et par mise à l'échelle positive (G(k·x) = G(x), k>0) ;
  • Gini d'une distribution constante = 0 ; Gini de [0,…,0,c] = (n−1)/n (concentration maximale) ;
  • formule des rangs ≡ double somme des écarts absolus (deux algorithmes indépendants) ;
  • IDH ≤ min des trois sous-indices (la moyenne géométrique pénalise le déséquilibre).

SOUNDNESS (vérifiée en adverse par `valide_mesures_sociales.py`) :
  - revenu négatif / non fini / non numérique / booléen          -> ValueError ;
  - revenus totaux nuls (Gini indéfini, 0/0)                     -> ValueError ;
  - liste de revenus vide                                        -> ValueError ;
  - population ≤ 0 ; effectif pauvre > population ; effectif négatif / non entier -> ValueError ;
  - fraction du seuil ∉ (0,1] ; revenu médian négatif            -> ValueError ;
  - parts cumulées non croissantes / hors [0,1] / dernière ≠ 1   -> ValueError ;
  - indice de dimension : max ≤ min, valeur hors [min,max]       -> ValueError ;
  - sous-indice IDH ∉ [0,1]                                      -> ValueError ;
  - déterministe ; conservateur (abstention tolérée, faux POSITIF interdit).
"""
from __future__ import annotations

import math

SOURCE = "statistique sociale établie (Gini, courbe de Lorenz, seuil de pauvreté Eurostat 60 %, IDH PNUD 2010+)"

_TOL = 1e-9


def _num(x, nom: str) -> float:
    """Convertit x en float fini en REFUSANT booléens / non numériques / non finis -> ValueError."""
    if isinstance(x, bool) or not isinstance(x, (int, float)):
        raise ValueError(f"{nom} non numérique : {x!r}")
    f = float(x)
    if not math.isfinite(f):
        raise ValueError(f"{nom} non fini : {x!r}")
    return f


def _proportion(x, nom: str) -> float:
    """Valide une proportion ∈ [0,1] ; sinon ValueError."""
    f = _num(x, nom)
    if f < 0.0 or f > 1.0:
        raise ValueError(f"{nom} doit être ∈ [0,1] : {f!r}")
    return f


def _entier_positif_ou_nul(x, nom: str) -> int:
    """Valide un effectif : entier (ou flottant entier) >= 0 ; sinon ValueError."""
    if isinstance(x, bool):
        raise ValueError(f"{nom} (effectif) ne peut être un booléen : {x!r}")
    if isinstance(x, int):
        n = x
    elif isinstance(x, float):
        if not math.isfinite(x) or not x.is_integer():
            raise ValueError(f"{nom} (effectif) doit être un entier : {x!r}")
        n = int(x)
    else:
        raise ValueError(f"{nom} (effectif) non numérique : {x!r}")
    if n < 0:
        raise ValueError(f"{nom} (effectif) doit être >= 0 : {n}")
    return n


def _revenus(seq, nom: str = "revenus") -> list:
    """Valide une liste non vide de revenus finis >= 0 (REFUSE négatif / booléen / non numérique)."""
    if isinstance(seq, (str, bytes)) or not hasattr(seq, "__iter__"):
        raise ValueError(f"{nom} doit être une liste de nombres : {seq!r}")
    vals = list(seq)
    if len(vals) == 0:
        raise ValueError(f"{nom} : liste vide")
    out = []
    for i, v in enumerate(vals):
        f = _num(v, f"{nom}[{i}]")
        if f < 0.0:
            raise ValueError(f"{nom}[{i}] : revenu négatif interdit : {f!r}")
        out.append(f)
    return out


def mediane(valeurs: list) -> float:
    """Médiane d'une liste non vide de nombres finis (moyenne des deux centrales si effectif pair)."""
    if isinstance(valeurs, (str, bytes)) or not hasattr(valeurs, "__iter__"):
        raise ValueError(f"valeurs doit être une liste de nombres : {valeurs!r}")
    vals = [_num(v, f"valeurs[{i}]") for i, v in enumerate(valeurs)]
    if len(vals) == 0:
        raise ValueError("valeurs : liste vide")
    vals.sort()
    n = len(vals)
    mid = n // 2
    if n % 2 == 1:
        return float(vals[mid])
    return (vals[mid - 1] + vals[mid]) / 2.0


def gini(revenus: list) -> float:
    """
    Coefficient de Gini d'un échantillon de revenus (formule des rangs, exacte) ∈ [0, (n−1)/n].

    0 = égalité parfaite ; tend vers 1 quand une seule part détient tout.
    Revenus négatifs / liste vide / total nul (Gini indéfini) -> ValueError.
    """
    x = sorted(_revenus(revenus))
    n = len(x)
    total = math.fsum(x)
    if total <= 0.0:
        raise ValueError("revenus totaux nuls : coefficient de Gini indéfini (0/0)")
    somme_rangs = math.fsum((i + 1) * x[i] for i in range(n))  # Σ i·x_(i), i de 1 à n
    g = (2.0 * somme_rangs - (n + 1) * total) / (n * total)
    if g < 0.0:  # garde-fou numérique (n'arrive pas pour x >= 0) : jamais une valeur hors [0,1)
        g = 0.0
    return g


def coefficient_gini(parts_cumulees: list) -> float:
    """
    Coefficient de Gini d'une COURBE DE LORENZ : parts cumulées de revenu de groupes de population ÉGAUX
    (quantiles), triées du plus pauvre au plus riche, dernière valeur = 1.0.

    G = 1 − (1/n)·Σ_{i=1}^n (L_{i-1} + L_i),  L_0 = 0.
    Parts non croissantes / hors [0,1] / dernière ≠ 1 -> ValueError.
    """
    if isinstance(parts_cumulees, (str, bytes)) or not hasattr(parts_cumulees, "__iter__"):
        raise ValueError(f"parts_cumulees doit être une liste : {parts_cumulees!r}")
    L = [_proportion(v, f"parts_cumulees[{i}]") for i, v in enumerate(parts_cumulees)]
    n = len(L)
    if n == 0:
        raise ValueError("parts_cumulees : liste vide")
    if abs(L[-1] - 1.0) > _TOL:
        raise ValueError(f"parts_cumulees : la dernière part cumulée doit valoir 1.0 (cumul total) : {L[-1]!r}")
    prec = 0.0
    for i, v in enumerate(L):
        if v < prec - _TOL:
            raise ValueError(f"parts_cumulees non croissantes en {i} : {v!r} < {prec!r}")
        prec = v
    aire2 = 0.0  # Σ (L_{i-1} + L_i)
    Lprev = 0.0
    for v in L:
        aire2 += Lprev + v
        Lprev = v
    g = 1.0 - aire2 / n
    if g < 0.0:
        g = 0.0
    return g


def taux_pauvrete(sous_seuil, population) -> float:
    """
    Taux de pauvreté = effectif sous le seuil / population totale ∈ [0,1].

    Population <= 0 ; effectif pauvre > population ; effectif négatif / non entier -> ValueError.
    """
    pauvres = _entier_positif_ou_nul(sous_seuil, "sous_seuil")
    pop = _entier_positif_ou_nul(population, "population")
    if pop <= 0:
        raise ValueError("population doit être > 0")
    if pauvres > pop:
        raise ValueError(f"effectif pauvre ({pauvres}) > population ({pop})")
    return pauvres / pop


def seuil_pauvrete(revenu_median, fraction: float = 0.6) -> float:
    """
    Seuil de pauvreté monétaire = fraction · revenu médian.

    Convention européenne (Eurostat) : fraction = 0.6 (60 % du revenu médian) ; variantes OCDE 0.4 / 0.5.
    Revenu médian négatif ; fraction ∉ (0,1] -> ValueError.
    """
    med = _num(revenu_median, "revenu_median")
    if med < 0.0:
        raise ValueError(f"revenu_median doit être >= 0 : {med!r}")
    f = _num(fraction, "fraction")
    if f <= 0.0 or f > 1.0:
        raise ValueError(f"fraction doit être ∈ (0,1] : {f!r}")
    return f * med


def indice_dimension(valeur, mini, maxi) -> float:
    """
    Indice de dimension (normalisation min–max PNUD) = (valeur − min) / (max − min) ∈ [0,1].

    max <= min (bornes invalides) ; valeur hors [min,max] -> ValueError.
    """
    v = _num(valeur, "valeur")
    lo = _num(mini, "mini")
    hi = _num(maxi, "maxi")
    if hi <= lo:
        raise ValueError(f"max ({hi}) doit être > min ({lo})")
    if v < lo or v > hi:
        raise ValueError(f"valeur ({v}) hors des bornes [{lo}, {hi}]")
    return (v - lo) / (hi - lo)


def idh(indice_sante, indice_education, indice_revenu) -> float:
    """
    Indice de développement humain (agrégation PNUD 2010+) = moyenne géométrique des trois sous-indices
    de dimension, chacun ∈ [0,1] : IDH = (I_santé · I_éduc · I_revenu)^(1/3) ∈ [0,1].

    Tout sous-indice ∉ [0,1] -> ValueError.
    """
    a = _proportion(indice_sante, "indice_sante")
    b = _proportion(indice_education, "indice_education")
    c = _proportion(indice_revenu, "indice_revenu")
    return (a * b * c) ** (1.0 / 3.0)


def _p_mesures_sociales() -> bool:
    """Preuve auto-portée : vrai sur cas connus + abstention sur entrée invalide."""
    import mesures_sociales as M

    def _leve_v(fn, *a, **k) -> bool:
        try:
            fn(*a, **k)
            return False
        except ValueError:
            return True
        except Exception:
            return False

    return (
        M.gini([10, 10, 10]) == 0.0                       # égalité parfaite
        and abs(M.gini([1, 2]) - 1.0 / 6.0) < 1e-12       # ≡ double somme des écarts
        and abs(M.gini([0, 0, 0, 10]) - 0.75) < 1e-12     # concentration maximale (n−1)/n
        and M.gini([5]) == 0.0                            # un seul individu
        and M.coefficient_gini([0.2, 0.4, 0.6, 0.8, 1.0]) == 0.0   # Lorenz = diagonale
        and abs(M.coefficient_gini([0.05, 0.15, 0.30, 0.55, 1.0]) - 0.38) < 1e-12
        and M.seuil_pauvrete(20000) == 12000.0            # 60 % du médian
        and M.seuil_pauvrete(1000, 0.5) == 500.0          # variante 50 %
        and M.taux_pauvrete(15, 100) == 0.15
        and M.mediane([1, 2, 3]) == 2.0
        and M.mediane([1, 2, 3, 4]) == 2.5
        and abs(M.idh(0.8, 0.8, 0.8) - 0.8) < 1e-12
        and M.indice_dimension(50, 0, 100) == 0.5
        and _leve_v(M.gini, [])                           # liste vide
        and _leve_v(M.gini, [-1, 2])                      # revenu négatif
        and _leve_v(M.gini, [0, 0, 0])                    # total nul -> indéfini
        and _leve_v(M.taux_pauvrete, 150, 100)            # pauvres > population
        and _leve_v(M.taux_pauvrete, 10, 0)               # population <= 0
        and _leve_v(M.seuil_pauvrete, -1)                 # médian négatif
        and _leve_v(M.seuil_pauvrete, 1000, 0)            # fraction = 0
        and _leve_v(M.coefficient_gini, [0.2, 0.4])       # dernière part != 1
        and _leve_v(M.coefficient_gini, [0.5, 0.3, 1.0])  # non croissante
        and _leve_v(M.indice_dimension, 5, 10, 10)        # max == min
        and _leve_v(M.idh, 1.2, 0.5, 0.5)                 # sous-indice > 1
    )
