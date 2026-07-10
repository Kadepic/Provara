"""
PROBABILITÉS ÉLÉMENTAIRES — probabilité CLASSIQUE exacte + lois discrètes, FAUX=0 (Partie I, B-NEC).

Même posture FAUX=0 que `galois`/`maths_discretes` : le MÉCANISME est un THÉORÈME EXACT (axiomes de
Kolmogorov, formule des probabilités totales, théorème de Bayes), calculé en `fractions.Fraction` SANS
flottant là où l'exactitude est possible. Toute entrée douteuse -> `ValueError` (abstention structurelle) :
le faux NÉGATIF (abstenir) est toléré, le faux POSITIF (rendre une proba inventée) est INTERDIT.

MÉCANISME EXACT :
  • MODÈLE FINI (probabilité classique) : `Modele(univers, poids=None)`. Poids par défaut équiprobables ;
    INVARIANT DUR vérifié à la construction : Σ poids == 1 EXACTEMENT (en Fraction), sinon ValueError.
    `probabilite(modele, evenement)` : événement = ensemble d'issues OU prédicat ; renvoie Σ des poids
    des issues favorables, en Fraction exacte.
  • AXIOMES / RÈGLES (exacts, en Fraction) :
      – union :          P(A∪B) = P(A) + P(B) − P(A∩B)                        (inclusion-exclusion)
      – conditionnelle : P(A|B) = P(A∩B) / P(B)         [P(B)=0 -> ValueError]
      – indépendance :   A⊥B ssi P(A∩B) == P(A)·P(B)    (égalité EXACTE, jamais « ≈ »)
      – Bayes DIRECT :   P(A|B) = P(B|A)·P(A) / P(B)     [P(B)=0 -> ValueError]
      – probabilités totales : P(A) = Σ_i P(B_i)·P(A|B_i) sur une partition (Σ P(B_i)=1 exigé)
  • LOIS DISCRÈTES : uniforme, Bernoulli(p), binomiale(n,p), géométrique(p) -> moments EXACTS en Fraction.
    Poisson(λ) : les moments (polynômes de Touchard en λ) restent EXACTS en Fraction ; SEULE la masse
    ponctuelle `proba_poisson` fait intervenir e^{-λ} (transcendant) et est donc un FLOTTANT MARQUÉ APPROCHÉ.
    Interface commune : `esperance`, `variance`, `moment(k)` (brut, m_0 = 1 par convention), `moment_centre(k)`,
    `ecart_type` (irrationnel en général -> flottant arrondi 10 c.s., MARQUÉ APPROCHÉ).
  • VÉRIFICATION INTERNE (deux chemins) : Var(X) est calculée à la fois par E[X²] − E[X]² (moments bruts)
    ET par la forme fermée propre à la loi ; toute divergence -> RuntimeError (jamais un résultat faux).

ABSTENTION (garanties vérifiées en adverse par `valide_probabilites_elementaires.py`) :
  - p hors [0,1] -> ValueError ; p = 0 pour la géométrique -> ValueError ;
  - flottant fourni pour une loi EXACTE (ou une probabilité exacte) -> ValueError (on exige int/Fraction) ;
  - n < 0 ou non entier -> ValueError ; moment d'ordre < 0 ou non entier -> ValueError (ordre 0 -> 1) ;
  - P(B) = 0 pour la conditionnelle / Bayes -> ValueError ;
  - poids ne sommant pas à 1, longueurs incohérentes, issue hors univers -> ValueError ;
  - bool / str / complexe / NaN / ±inf / mauvaise arité -> ValueError ; déterministe ; sans état global mutable.

SOURCE = "axiomes de Kolmogorov + théorème de Bayes ; lois discrètes classiques (moments via Stirling/Touchard)"
"""
from __future__ import annotations

import math
from collections import namedtuple
from fractions import Fraction

import maths_discretes as _md  # binomial exact + factorielle exacte (réservé, NON modifié)

SOURCE = "axiomes de Kolmogorov + théorème de Bayes ; lois discrètes classiques (moments via Stirling/Touchard)"

_CHIFFRES_SIGNIFICATIFS = 10


# ── helpers de validation ────────────────────────────────────────────────────────────────────────────────────────
def _est_rationnel(x) -> bool:
    """True ssi x est un rationnel EXACT (int non-bool ou Fraction). Les flottants sont REFUSÉS."""
    return (isinstance(x, int) and not isinstance(x, bool)) or isinstance(x, Fraction)


def _frac(x, nom: str = "valeur") -> Fraction:
    if not _est_rationnel(x):
        raise ValueError(f"{nom} : entier ou Fraction EXACT attendu (flottant/bool/str/complexe refusés), reçu {x!r}")
    return Fraction(x)


def _proba(x, nom: str = "probabilité", strict_pos: bool = False) -> Fraction:
    f = _frac(x, nom)
    if f < 0 or f > 1:
        raise ValueError(f"{nom} hors [0,1] : {f}")
    if strict_pos and f == 0:
        raise ValueError(f"{nom} nulle interdite")
    return f


def _entier(x, mini: int, nom: str) -> int:
    if not isinstance(x, int) or isinstance(x, bool):
        raise ValueError(f"{nom} : entier attendu, reçu {x!r}")
    if x < mini:
        raise ValueError(f"{nom} : entier ≥ {mini} attendu, reçu {x}")
    return x


def _sig(x: float, n: int = _CHIFFRES_SIGNIFICATIFS) -> float:
    """Arrondit à n chiffres significatifs (précision honnête pour les sorties APPROCHÉES)."""
    if x == 0:
        return 0.0
    return float(f"{x:.{n}g}")


# ── nombres de Stirling de 2e espèce (exacts) ────────────────────────────────────────────────────────────────────
def _stirling2(n: int, k: int) -> int:
    """S(n,k) exact : S(0,0)=1, S(n,0)=0 (n>0), S(n,k)=k·S(n-1,k)+S(n-1,k-1)."""
    if k < 0 or k > n:
        return 0
    prev = [0] * (k + 1)
    prev[0] = 1  # S(0,0) = 1
    for _i in range(1, n + 1):
        cur = [0] * (k + 1)
        for j in range(1, k + 1):
            cur[j] = j * prev[j] + prev[j - 1]
        prev = cur
    return prev[k]


# ── (a) MODÈLE FINI (probabilité classique) ──────────────────────────────────────────────────────────────────────
class Modele:
    """Modèle de probabilité fini : univers = issues distinctes, poids = probabilités exactes (Fraction).

    Poids par défaut = équiprobabilité (1/n chacun). INVARIANT DUR : Σ poids == 1 exactement, sinon ValueError.
    Immutable après construction (aucune méthode ne mute l'état)."""

    __slots__ = ("univers", "poids", "_index")

    def __init__(self, univers, poids=None):
        if not isinstance(univers, (list, tuple)):
            raise ValueError("univers : liste/tuple d'issues attendu")
        univers = tuple(univers)
        n = len(univers)
        if n == 0:
            raise ValueError("univers vide interdit")
        try:
            index = {}
            for i, issue in enumerate(univers):
                if issue in index:
                    raise ValueError(f"issue dupliquée dans l'univers : {issue!r}")
                index[issue] = i
        except TypeError:
            raise ValueError("issues non hachables interdites")
        if poids is None:
            poids = tuple(Fraction(1, n) for _ in range(n))
        else:
            if not isinstance(poids, (list, tuple)):
                raise ValueError("poids : liste/tuple attendu")
            if len(poids) != n:
                raise ValueError("poids : longueur ≠ nombre d'issues")
            poids = tuple(_proba(w, "poids") for w in poids)
        if sum(poids) != Fraction(1):
            raise ValueError(f"les poids ne somment pas à 1 exactement (Σ = {sum(poids)})")
        object.__setattr__(self, "univers", univers)
        object.__setattr__(self, "poids", poids)
        object.__setattr__(self, "_index", index)


def probabilite(modele: Modele, evenement) -> Fraction:
    """P(événement) exacte. `evenement` = prédicat (callable issue -> bool) OU ensemble d'issues ⊆ univers.

    Prédicat devant renvoyer un vrai booléen ; ensemble contenant une issue hors univers -> ValueError."""
    if not isinstance(modele, Modele):
        raise ValueError("modele : instance de Modele attendue")
    total = Fraction(0)
    if callable(evenement):
        for issue, w in zip(modele.univers, modele.poids):
            verdict = evenement(issue)
            if not isinstance(verdict, bool):
                raise ValueError("le prédicat doit renvoyer un booléen (True/False)")
            if verdict:
                total += w
        return total
    if isinstance(evenement, (set, frozenset, list, tuple)):
        favorables = set(evenement)
        for issue in favorables:
            if issue not in modele._index:
                raise ValueError(f"issue hors univers dans l'événement : {issue!r}")
            total += modele.poids[modele._index[issue]]
        return total
    raise ValueError("evenement : prédicat (callable) ou ensemble d'issues attendu")


# ── (b) AXIOMES ET RÈGLES (exacts, en Fraction) ──────────────────────────────────────────────────────────────────
def union(p_a, p_b, p_inter) -> Fraction:
    """P(A∪B) = P(A) + P(B) − P(A∩B) (inclusion-exclusion). Refuse toute configuration incohérente."""
    a = _proba(p_a, "P(A)")
    b = _proba(p_b, "P(B)")
    i = _proba(p_inter, "P(A∩B)")
    if i > a or i > b:
        raise ValueError("P(A∩B) > min(P(A),P(B)) : configuration impossible")
    r = a + b - i
    if r < 0 or r > 1:
        raise ValueError(f"P(A∪B) = {r} hors [0,1] : probabilités incohérentes")
    return r


def conditionnelle(p_inter, p_b) -> Fraction:
    """P(A|B) = P(A∩B) / P(B). P(B) = 0 -> ValueError ; P(A∩B) > P(B) -> ValueError (P(A|B) > 1 impossible)."""
    i = _proba(p_inter, "P(A∩B)")
    b = _proba(p_b, "P(B)")
    if b == 0:
        raise ValueError("P(B) = 0 : conditionnelle indéfinie (abstention)")
    if i > b:
        raise ValueError("P(A∩B) > P(B) : incohérent (P(A|B) > 1)")
    return i / b


def independants(p_a, p_b, p_inter) -> bool:
    """A ⊥ B ssi P(A∩B) == P(A)·P(B) EXACTEMENT (jamais une tolérance)."""
    a = _proba(p_a, "P(A)")
    b = _proba(p_b, "P(B)")
    i = _proba(p_inter, "P(A∩B)")
    return i == a * b


def bayes(p_b_sachant_a, p_a, p_b) -> Fraction:
    """Théorème de Bayes, forme DIRECTE : P(A|B) = P(B|A)·P(A) / P(B). P(B) = 0 -> ValueError.

    ATTENTION au taux de base : P(B) doit inclure la vraisemblance sous ¬A (cf. probabilite_totale)."""
    bsa = _proba(p_b_sachant_a, "P(B|A)")
    a = _proba(p_a, "P(A)")
    b = _proba(p_b, "P(B)")
    if b == 0:
        raise ValueError("P(B) = 0 : Bayes indéfini (abstention)")
    r = bsa * a / b
    if r > 1:
        raise ValueError(f"P(A|B) = {r} > 1 : entrées incohérentes")
    return r


def probabilite_totale(partition) -> Fraction:
    """P(A) = Σ_i P(B_i)·P(A|B_i). `partition` = suite de couples (P(B_i), P(A|B_i)) ; Σ P(B_i) == 1 exigé."""
    if not isinstance(partition, (list, tuple)) or len(partition) == 0:
        raise ValueError("partition : suite non vide de couples (P(B_i), P(A|B_i)) attendue")
    somme_base = Fraction(0)
    total = Fraction(0)
    for couple in partition:
        if not isinstance(couple, (list, tuple)) or len(couple) != 2:
            raise ValueError(f"couple (P(B_i), P(A|B_i)) mal formé : {couple!r}")
        pb = _proba(couple[0], "P(B_i)")
        pcond = _proba(couple[1], "P(A|B_i)")
        somme_base += pb
        total += pb * pcond
    if somme_base != Fraction(1):
        raise ValueError(f"les P(B_i) ne forment pas une partition (Σ = {somme_base} ≠ 1)")
    return total


# ── (c) LOIS DISCRÈTES ───────────────────────────────────────────────────────────────────────────────────────────
_Loi = namedtuple("_Loi", ["famille", "params"])


def uniforme(valeurs) -> _Loi:
    """Loi uniforme sur un support fini d'ENTIERS distincts (chacun de probabilité 1/n)."""
    if not isinstance(valeurs, (list, tuple)) or len(valeurs) == 0:
        raise ValueError("uniforme : suite non vide d'entiers attendue")
    vals = []
    vus = set()
    for v in valeurs:
        if not isinstance(v, int) or isinstance(v, bool):
            raise ValueError(f"uniforme : entier attendu, reçu {v!r}")
        if v in vus:
            raise ValueError(f"uniforme : valeur dupliquée {v}")
        vus.add(v)
        vals.append(v)
    return _Loi("uniforme", {"valeurs": tuple(vals)})


def uniforme_intervalle(a: int, b: int) -> _Loi:
    """Loi uniforme sur les entiers {a, a+1, …, b} (a ≤ b)."""
    _entier(a, -10**18, "a")
    _entier(b, -10**18, "b")
    if b < a:
        raise ValueError("uniforme_intervalle : b < a")
    return uniforme(tuple(range(a, b + 1)))


def bernoulli(p) -> _Loi:
    """Loi de Bernoulli(p) : support {0,1}, P(1)=p. p ∈ [0,1] exact (Fraction/int)."""
    return _Loi("bernoulli", {"p": _proba(p, "p")})


def binomiale(n: int, p) -> _Loi:
    """Loi binomiale(n,p) : nb de succès sur n épreuves indépendantes. n ≥ 0 entier, p ∈ [0,1] exact."""
    _entier(n, 0, "n")
    return _Loi("binomiale", {"n": n, "p": _proba(p, "p")})


def geometrique(p) -> _Loi:
    """Loi géométrique(p) sur {1,2,3,…} (nombre d'épreuves jusqu'au 1er succès). p ∈ ]0,1] exact ; E = 1/p."""
    return _Loi("geometrique", {"p": _proba(p, "p", strict_pos=True)})


def poisson(lam) -> _Loi:
    """Loi de Poisson(λ), λ > 0 exact (Fraction/int). Moments EXACTS (Touchard) ; masse ponctuelle -> approchée."""
    l = _frac(lam, "λ")
    if l <= 0:
        raise ValueError("λ : réel strictement positif exact attendu")
    return _Loi("poisson", {"lam": l})


def _exige_loi(loi) -> _Loi:
    if not isinstance(loi, _Loi):
        raise ValueError("loi : construite par uniforme/bernoulli/binomiale/geometrique/poisson attendue")
    return loi


def _paires_finies(loi: _Loi):
    """Liste (valeur:Fraction, poids:Fraction) pour les lois à SUPPORT FINI ; somme des poids == 1 exact."""
    fam = loi.famille
    if fam == "uniforme":
        vals = loi.params["valeurs"]
        w = Fraction(1, len(vals))
        return [(Fraction(v), w) for v in vals]
    if fam == "bernoulli":
        p = loi.params["p"]
        return [(Fraction(0), 1 - p), (Fraction(1), p)]
    if fam == "binomiale":
        n = loi.params["n"]
        p = loi.params["p"]
        q = 1 - p
        return [(Fraction(j), _md.binomial(n, j) * p ** j * q ** (n - j)) for j in range(n + 1)]
    raise ValueError(f"support non fini : {fam}")


def moment(loi, k: int):
    """Moment BRUT d'ordre k : E[X^k]. Convention m_0 = 1 (documentée). Exact en Fraction (Poisson inclus).

    Fini (uniforme/Bernoulli/binomiale) : somme directe Σ p_i·x_i^k.
    Géométrique : E[X^k] = Σ_{j=1}^k S(k,j)·j!·q^{j-1}/p^j (via moments factoriels + Stirling).
    Poisson : E[X^k] = Σ_{j=1}^k S(k,j)·λ^j (polynôme de Touchard)."""
    loi = _exige_loi(loi)
    _entier(k, 0, "ordre k")
    if k == 0:
        return Fraction(1)
    fam = loi.famille
    if fam in ("uniforme", "bernoulli", "binomiale"):
        return sum((poids * (val ** k) for val, poids in _paires_finies(loi)), Fraction(0))
    if fam == "geometrique":
        p = loi.params["p"]
        q = 1 - p
        total = Fraction(0)
        for j in range(1, k + 1):
            total += _stirling2(k, j) * _md.factorielle(j) * q ** (j - 1) / p ** j
        return total
    if fam == "poisson":
        lam = loi.params["lam"]
        total = Fraction(0)
        for j in range(1, k + 1):
            total += _stirling2(k, j) * lam ** j
        return total
    raise ValueError(f"loi inconnue : {fam}")


def esperance(loi):
    """E[X] = moment brut d'ordre 1. Exact en Fraction."""
    return moment(loi, 1)


def moment_centre(loi, k: int):
    """Moment CENTRÉ d'ordre k : E[(X−E[X])^k] = Σ_{i=0}^k C(k,i)·(−μ)^{k−i}·m_i. Convention ordre 0 -> 1."""
    loi = _exige_loi(loi)
    _entier(k, 0, "ordre k")
    if k == 0:
        return Fraction(1)
    mu = esperance(loi)
    total = Fraction(0)
    for i in range(0, k + 1):
        total += _md.binomial(k, i) * ((-mu) ** (k - i)) * moment(loi, i)
    return total


def _variance_fermee(loi: _Loi):
    """Forme FERMÉE de la variance, chemin de calcul DISTINCT des moments bruts (pour la vérif interne)."""
    fam = loi.famille
    if fam == "bernoulli":
        p = loi.params["p"]
        return p * (1 - p)
    if fam == "binomiale":
        p = loi.params["p"]
        return loi.params["n"] * p * (1 - p)
    if fam == "geometrique":
        p = loi.params["p"]
        return (1 - p) / (p * p)
    if fam == "poisson":
        return loi.params["lam"]
    if fam == "uniforme":
        # chemin distinct : Σ p_i·(x_i − μ)²  (forme par déviation, pas E[X²]−E[X]²)
        paires = _paires_finies(loi)
        mu = sum((w * v for v, w in paires), Fraction(0))
        return sum((w * (v - mu) ** 2 for v, w in paires), Fraction(0))
    return None


def variance(loi):
    """Var(X), avec VÉRIFICATION INTERNE à deux chemins : E[X²]−E[X]² == forme fermée, sinon RuntimeError."""
    loi = _exige_loi(loi)
    v_moments = moment(loi, 2) - moment(loi, 1) ** 2
    v_ferme = _variance_fermee(loi)
    if v_ferme is not None and v_ferme != v_moments:
        raise RuntimeError(
            f"incohérence interne Var : moments {v_moments} ≠ forme fermée {v_ferme} (loi {loi.famille})")
    return v_moments


def ecart_type(loi) -> float:
    """Écart-type σ = √Var. Irrationnel en général -> FLOTTANT arrondi à 10 c.s., MARQUÉ APPROCHÉ."""
    var = variance(loi)
    if var < 0:
        raise RuntimeError("variance négative : impossible")
    return _sig(math.sqrt(float(var)))  # APPROCHÉ (racine irrationnelle en général)


def proba_poisson(lam, k: int) -> float:
    """Masse ponctuelle P(X=k) d'une Poisson(λ) = e^{-λ}·λ^k / k!.

    FLOTTANT MARQUÉ APPROCHÉ : e^{-λ} est transcendant, donc cette valeur N'EST PAS exacte (≈ à 10 c.s.)."""
    l = _frac(lam, "λ")
    if l <= 0:
        raise ValueError("λ : réel strictement positif exact attendu")
    _entier(k, 0, "k")
    val = math.exp(-float(l)) * (float(l) ** k) / math.factorial(k)
    return _sig(val)  # APPROCHÉ
