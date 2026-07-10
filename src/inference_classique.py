"""
INFÉRENCE STATISTIQUE CLASSIQUE (fréquentiste) — test d'hypothèse (p-valeur) + intervalle de confiance.

Distinct de `conformal` (prédiction CONFORME : intervalle pour une observation FUTURE, sans hypothèse de loi) :
ici on teste une HYPOTHÈSE sur un PARAMÈTRE (moyenne, proportion, loi d'une variable catégorielle) et on
construit un intervalle de confiance sur ce PARAMÈTRE, sous les hypothèses de loi classiques (normale, Student,
khi-deux). Même posture FAUX=0 que `geometries_non_euclidiennes` / `galois` : un résultat prouvé, ou une abstention.

MÉCANISMES (exacts / contrôlés) :
  • phi(z)      : fonction de répartition de la loi normale centrée réduite, N(0,1).
                  phi(z) = ½·(1 + erf(z/√2)) — EXACTE à la précision machine (math.erf).
  • phi_inverse(p) : quantile normal, par BISSECTION sur phi (phi est strictement croissante). L'encadrement
                  [lo, hi] garanti (hi − lo ≤ 1e-13) est disponible via `quantile_normal_encadrement`.
  • Student (t) : PAS de tableau approximatif inventé. La p-valeur (probabilité de queue) est obtenue par
                  INTÉGRATION NUMÉRIQUE contrôlée (Simpson ADAPTATIF) de la densité, avec une BORNE D'ERREUR
                  numérique rendue (`borne_erreur`). Le résultat est donc APPROCHÉ et MARQUÉ tel. La queue à
                  l'infini est ramenée à [0,1] par le changement de variable w = seuil/u (intégrale propre) ;
                  la limite exacte en w→0 est injectée (Cauchy pour ν=1). Toute la région u ≥ t (t ≥ 0) est
                  au-delà du mode 0 : densité MONOTONE décroissante, pas de pic interne raté par Simpson.
  • khi-deux (χ²) : la queue P(χ²_k > x²) = Q(k/2, x²/2) est calculée par la fonction GAMMA INCOMPLÈTE
                  RÉGULARISÉE supérieure (série pour x < a+1, fraction continue de Lentz sinon — Numerical
                  Recipes §6.2). C'est EXACT à la précision machine (≈1e-15) et IMMUNISÉ contre le piège
                  d'intégration : l'ancienne intégration par w = x²/u ratait le pic interne étroit du pdf χ²
                  (mode x ≈ k−2) quand la statistique était SOUS le mode, renvoyant ~0 (faux « significatif »)
                  au lieu de ~1. Le passage par Q(a,x) supprime ce faux positif.

TESTS :
  • test_z(moyenne_obs, mu0, sigma, n)          : σ connu, statistique z = (x̄−μ₀)/(σ/√n), loi N(0,1).
  • test_t_student(echantillon, mu0)            : σ inconnu, s estimé, statistique t, loi de Student à n−1 ddl.
  • test_khi2_conformite(observes, attendus)    : adéquation à une loi, statistique Σ(O−E)²/E, loi χ² à k−1 ddl.
  Convention unilatérale : bilateral=False -> hypothèse alternative H1 : μ > μ₀ (queue SUPÉRIEURE, P(·> stat)).

INTERVALLES DE CONFIANCE :
  • ic_moyenne_sigma_connu(moyenne, sigma, n, niveau)   = moyenne ± z_{1−α/2}·σ/√n.
  • ic_moyenne_sigma_inconnu(echantillon, niveau)       = x̄ ± t_{1−α/2, n−1}·s/√n  (Student).
  • ic_proportion_wilson(succes, n, niveau)             : intervalle de WILSON — PAS Wald.
        L'intervalle de WALD  p̂ ± z·√(p̂(1−p̂)/n) est FAUX près de 0 et de 1 : pour p̂=0 il donne le point [0,0]
        (couverture nulle) et peut sortir de [0,1]. WILSON reste TOUJOURS inclus dans [0,1] et couvre correctement
        aux extrêmes. On utilise donc WILSON.

interprete(p_valeur, alpha) -> str : une p-valeur N'EST PAS la probabilité que H0 soit vraie ; le module l'énonce
  et REFUSE de conclure que « H1 est vraie ».

ABSTENTION (ValueError, jamais un faux positif) :
  • n < 2 ; σ ≤ 0 ; niveau (confiance) hors ]0,1[ ;
  • échantillon de VARIANCE NULLE pour Student (t indéfini) ;
  • effectif ATTENDU < 5 pour le khi-deux (condition de validité de l'approximation) ;
  • bool / str / NaN / ±inf / mauvaise arité / probabilité hors domaine -> ValueError.

Toutes les fonctions sont PURES et déterministes ; stdlib uniquement (math). Vérifié en adverse par
`valide_inference_classique.py` (ancres NON circulaires : formes fermées Cauchy/χ², valeurs tabulées, calculs à la main).
"""
from __future__ import annotations

import math

SOURCE = "inférence fréquentiste classique (Neyman–Pearson) ; Wilson 1927 (intervalle de proportion) ; " \
         "lois N(0,1)/Student/χ² ; intégration de Simpson adaptative"

PI = math.pi
_SQRT2 = math.sqrt(2.0)
_CHIFFRES_SIGNIFICATIFS = 10
# phi (via math.erf) est exacte à la précision machine ; borne d'erreur conservatrice pour les sorties z.
_BORNE_PHI = 1e-12
# Tolérance de l'intégrateur adaptatif (par intégrale) ; la borne rendue est l'estimation d'erreur accumulée.
_TOL_SIMPSON = 1e-13
_PROFONDEUR_MAX = 60
# Gamma incomplète régularisée (χ²) : convergence à la précision machine ; borne d'erreur conservatrice rendue.
_EPS_GAMMA = 3.0e-16
_FPMIN = 1.0e-300  # plancher anti-division-par-zéro de l'algorithme de Lentz
_MAX_ITER_GAMMA = 4000
_BORNE_GAMMA = 1e-12  # borne conservatrice ; la série/fraction continue convergent en réalité à ~1e-15


# ── HELPERS DE VALIDATION ────────────────────────────────────────────────────────────────────────────────────────
def _est_reel(x) -> bool:
    """True ssi x est un réel fini (bool REFUSÉ : True n'est pas 1 ; NaN/inf REFUSÉS ; str/complexe REFUSÉS)."""
    return isinstance(x, (int, float)) and not isinstance(x, bool) and math.isfinite(x)


def _exige_reel(x, nom: str) -> float:
    if not _est_reel(x):
        raise ValueError(f"{nom} invalide : un réel fini est requis (bool/str/NaN/inf refusés), reçu {x!r}")
    return float(x)


def _exige_entier(x, nom: str, mini=None) -> int:
    if not isinstance(x, int) or isinstance(x, bool):
        raise ValueError(f"{nom} invalide : un entier est requis (bool refusé), reçu {x!r}")
    if mini is not None and x < mini:
        raise ValueError(f"{nom} invalide : ≥ {mini} requis, reçu {x}")
    return x


def _exige_bool(x, nom: str) -> bool:
    if not isinstance(x, bool):
        raise ValueError(f"{nom} invalide : un booléen est requis, reçu {x!r}")
    return x


def _exige_n(n, nom: str = "n") -> int:
    """Taille d'échantillon : entier ≥ 2 (n < 2 -> abstention)."""
    return _exige_entier(n, nom, mini=2)


def _exige_sigma(sigma) -> float:
    s = _exige_reel(sigma, "sigma")
    if s <= 0.0:
        raise ValueError("sigma invalide : un écart-type strictement positif est requis (σ ≤ 0 -> abstention)")
    return s


def _exige_niveau(niveau) -> float:
    """Niveau de confiance dans ]0,1[ strict."""
    nv = _exige_reel(niveau, "niveau")
    if not (0.0 < nv < 1.0):
        raise ValueError("niveau invalide : la confiance doit être dans ]0,1[ (ex. 0.95)")
    return nv


def _exige_proba_ouverte(p) -> float:
    pp = _exige_reel(p, "p")
    if not (0.0 < pp < 1.0):
        raise ValueError("probabilité invalide : un réel dans ]0,1[ strict est requis")
    return pp


def _exige_proba_fermee(p) -> float:
    pp = _exige_reel(p, "p_valeur")
    if not (0.0 <= pp <= 1.0):
        raise ValueError("p-valeur invalide : un réel dans [0,1] est requis")
    return pp


def _exige_echantillon(ech, nom: str, mini: int = 2):
    if not isinstance(ech, (list, tuple)):
        raise ValueError(f"{nom} invalide : une liste/tuple de réels est requise, reçu {type(ech).__name__}")
    if len(ech) < mini:
        raise ValueError(f"{nom} invalide : au moins {mini} valeurs requises, reçu {len(ech)}")
    return [_exige_reel(v, f"{nom}[i]") for v in ech]


def _sig(x: float, n: int = _CHIFFRES_SIGNIFICATIFS) -> float:
    """Arrondit à n chiffres significatifs (précision honnête)."""
    if x == 0:
        return 0.0
    return float(f"{x:.{n}g}")


# ── INTÉGRATEUR DE SIMPSON ADAPTATIF (avec estimation d'erreur) ──────────────────────────────────────────────────
def _asr(f, a, b, tol, whole, fa, fm, fb, depth):
    m = 0.5 * (a + b)
    lm = 0.5 * (a + m)
    rm = 0.5 * (m + b)
    flm = f(lm)
    frm = f(rm)
    left = (m - a) / 6.0 * (fa + 4.0 * flm + fm)
    right = (b - m) / 6.0 * (fm + 4.0 * frm + fb)
    delta = left + right - whole
    if depth <= 0 or abs(delta) <= 15.0 * tol:
        return left + right + delta / 15.0, abs(delta) / 15.0
    lv, le = _asr(f, a, m, tol / 2.0, left, fa, flm, fm, depth - 1)
    rv, re = _asr(f, m, b, tol / 2.0, right, fm, frm, fb, depth - 1)
    return lv + rv, le + re


def _integre(f, a, b, tol=_TOL_SIMPSON, depth=_PROFONDEUR_MAX):
    """Intègre f sur [a,b] par Simpson adaptatif. Renvoie (valeur, borne_erreur_estimée)."""
    fa = f(a)
    fm = f(0.5 * (a + b))
    fb = f(b)
    whole = (b - a) / 6.0 * (fa + 4.0 * fm + fb)
    return _asr(f, a, b, tol, whole, fa, fm, fb, depth)


# ── LOI NORMALE N(0,1) ───────────────────────────────────────────────────────────────────────────────────────────
def phi(z: float) -> float:
    """Fonction de répartition de N(0,1) : phi(z) = ½·(1 + erf(z/√2)). Exacte à la précision machine.

    phi(0) = 0.5 exactement ; phi(1.96) ≈ 0.975 ; phi(−1.96) ≈ 0.025."""
    z = _exige_reel(z, "z")
    return 0.5 * (1.0 + math.erf(z / _SQRT2))


def quantile_normal_encadrement(p: float):
    """Encadrement [lo, hi] du quantile normal z tel que phi(z) = p, par bissection (hi − lo ≤ 1e-13).

    p dans ]0,1[ strict (0 et 1 -> quantiles infinis -> abstention)."""
    p = _exige_proba_ouverte(p)
    lo, hi = -40.0, 40.0  # phi(−40) ≈ 0, phi(40) ≈ 1 à la précision machine
    for _ in range(300):
        mid = 0.5 * (lo + hi)
        if phi(mid) < p:
            lo = mid
        else:
            hi = mid
        if hi - lo < 1e-13:
            break
    return lo, hi


def phi_inverse(p: float) -> float:
    """Quantile normal z tel que phi(z) = p, par bissection sur phi (encadrement garanti ≤ 1e-13).

    phi_inverse(0.975) ≈ 1.959964 (valeur universellement tabulée). p dans ]0,1[ strict."""
    lo, hi = quantile_normal_encadrement(p)
    return 0.5 * (lo + hi)


# ── LOI DE STUDENT (t) ───────────────────────────────────────────────────────────────────────────────────────────
def _student_log_c(nu: float) -> float:
    return math.lgamma(0.5 * (nu + 1.0)) - math.lgamma(0.5 * nu) - 0.5 * math.log(nu * PI)


def _student_pdf(x: float, nu: float) -> float:
    return math.exp(_student_log_c(nu) - 0.5 * (nu + 1.0) * math.log1p(x * x / nu))


def _student_tail(t: float, nu: float):
    """P(T > t) pour t ≥ 0, ν ≥ 1, par intégration adaptative. Renvoie (proba, borne_erreur)."""
    if t < 0.0:
        raise ValueError("t doit être ≥ 0 (symétrie gérée en amont)")
    if t == 0.0:
        return 0.5, 0.0  # médiane : P(T > 0) = 1/2 exactement (loi symétrique)
    c = math.exp(_student_log_c(nu))
    # limite en w→0 de g(w) : g ~ c·ν^((ν+1)/2)·t^(−ν)·w^(ν−1) -> non nulle seulement pour ν == 1 (Cauchy : 1/(π t))
    g0 = c / t if nu == 1.0 else 0.0

    def g(w):
        if w <= 0.0:
            return g0
        u = t / w
        return _student_pdf(u, nu) * t / (w * w)

    val, err = _integre(g, 0.0, 1.0)
    val = min(1.0, max(0.0, val))
    return val, err


def _student_cdf(t: float, nu: float):
    """F(t) = P(T ≤ t) et borne d'erreur. Utilise la symétrie de la loi de Student."""
    if t >= 0.0:
        tail, err = _student_tail(t, nu)
        return 1.0 - tail, err
    tail, err = _student_tail(-t, nu)
    return tail, err


def _student_quantile(q: float, nu: float) -> float:
    """Quantile de Student t_{q,ν} par bissection sur la CDF. q dans ]0,1[."""
    q = _exige_proba_ouverte(q)
    lo, hi = -1.0e6, 1.0e6
    for _ in range(200):
        mid = 0.5 * (lo + hi)
        cdf, _ = _student_cdf(mid, nu)
        if cdf < q:
            lo = mid
        else:
            hi = mid
        if hi - lo < 1e-10:
            break
    return 0.5 * (lo + hi)


# ── LOI DU KHI-DEUX (χ²) — via GAMMA INCOMPLÈTE RÉGULARISÉE ──────────────────────────────────────────────────────
# P(χ²_k > x2) = Q(k/2, x2/2), fonction gamma incomplète régularisée SUPÉRIEURE. Calcul EXACT (précision machine)
# par série (x < a+1) et fraction continue de Lentz (x ≥ a+1) — Numerical Recipes §6.2. Aucune intégration : cela
# supprime le faux positif de l'ancienne quadrature (pic interne du pdf χ² raté quand la statistique est sous le mode).
def _gamma_p_serie(a: float, x: float) -> float:
    """P(a,x) régularisée INFÉRIEURE par développement en série (converge vite pour x < a+1). a>0, x>0."""
    gln = math.lgamma(a)
    ap = a
    terme = 1.0 / a
    somme = terme
    for _ in range(_MAX_ITER_GAMMA):
        ap += 1.0
        terme *= x / ap
        somme += terme
        if abs(terme) < abs(somme) * _EPS_GAMMA:
            return somme * math.exp(-x + a * math.log(x) - gln)
    raise ValueError("gamma incomplète (série) non convergente : abstention plutôt qu'un résultat douteux")


def _gamma_q_fraction(a: float, x: float) -> float:
    """Q(a,x) régularisée SUPÉRIEURE par fraction continue (Lentz modifié ; valide pour x ≥ a+1). a>0, x>0."""
    gln = math.lgamma(a)
    b = x + 1.0 - a
    c = 1.0 / _FPMIN
    d = 1.0 / b
    h = d
    for i in range(1, _MAX_ITER_GAMMA):
        an = -i * (i - a)
        b += 2.0
        d = an * d + b
        if abs(d) < _FPMIN:
            d = _FPMIN
        c = b + an / c
        if abs(c) < _FPMIN:
            c = _FPMIN
        d = 1.0 / d
        delta = d * c
        h *= delta
        if abs(delta - 1.0) < _EPS_GAMMA:
            return math.exp(-x + a * math.log(x) - gln) * h
    raise ValueError("gamma incomplète (fraction continue) non convergente : abstention plutôt qu'un résultat douteux")


def _gamma_q(a: float, x: float) -> float:
    """Q(a,x) = 1 − P(a,x), gamma incomplète régularisée supérieure. a>0, x≥0. Exacte à la précision machine."""
    if not (a > 0.0) or x < 0.0:
        raise ValueError("gamma incomplète : a>0 et x≥0 requis")
    if x == 0.0:
        return 1.0
    if x < a + 1.0:
        return 1.0 - _gamma_p_serie(a, x)
    return _gamma_q_fraction(a, x)


def _chi2_tail(x2: float, k: float):
    """P(χ²_k > x2) = Q(k/2, x2/2) pour x2 ≥ 0, k ≥ 1. Renvoie (proba, borne_erreur).

    EXACT à la précision machine (gamma incomplète régularisée). borne_erreur = borne conservatrice constante."""
    if x2 == 0.0:
        return 1.0, 0.0  # P(χ² > 0) = 1 exactement
    q = _gamma_q(0.5 * k, 0.5 * x2)
    q = min(1.0, max(0.0, q))
    return q, _BORNE_GAMMA


# ── TESTS D'HYPOTHÈSE ────────────────────────────────────────────────────────────────────────────────────────────
def test_z(moyenne_obs, mu0, sigma, n, bilateral=True) -> dict:
    """Test z (σ connu) : z = (x̄ − μ₀)/(σ/√n), loi N(0,1).

    Renvoie {'statistique': z, 'p_valeur', 'borne_erreur'}. p bilatérale = 2·(1 − phi(|z|)) ;
    unilatérale (bilateral=False, H1 : μ > μ₀) = 1 − phi(z). n < 2 ou σ ≤ 0 -> ValueError."""
    xbar = _exige_reel(moyenne_obs, "moyenne_obs")
    mu0 = _exige_reel(mu0, "mu0")
    sigma = _exige_sigma(sigma)
    n = _exige_n(n)
    _exige_bool(bilateral, "bilateral")
    z = (xbar - mu0) / (sigma / math.sqrt(n))
    if bilateral:
        p = 2.0 * (1.0 - phi(abs(z)))
    else:
        p = 1.0 - phi(z)
    p = min(1.0, max(0.0, p))
    return {"statistique": _sig(z), "p_valeur": _sig(p), "borne_erreur": _BORNE_PHI}


def test_t_student(echantillon, mu0, bilateral=True) -> dict:
    """Test t de Student (σ inconnu) : t = (x̄ − μ₀)/(s/√n), s = écart-type corrigé (n−1 ddl).

    Renvoie {'statistique', 'p_valeur', 'borne_erreur', 'ddl'}. La p-valeur est APPROCHÉE (Simpson adaptatif),
    borne_erreur = estimation d'erreur numérique. Variance nulle -> ValueError ; n < 2 -> ValueError."""
    ech = _exige_echantillon(echantillon, "echantillon", mini=2)
    mu0 = _exige_reel(mu0, "mu0")
    _exige_bool(bilateral, "bilateral")
    n = len(ech)
    moy = math.fsum(ech) / n
    var = math.fsum((x - moy) ** 2 for x in ech) / (n - 1)
    if var <= 0.0:
        raise ValueError("variance nulle : statistique t indéfinie (échantillon constant) -> abstention")
    s = math.sqrt(var)
    se = s / math.sqrt(n)
    t = (moy - mu0) / se
    nu = float(n - 1)
    tail, err = _student_tail(abs(t), nu)  # P(T > |t|)
    if bilateral:
        p = 2.0 * tail
        be = 2.0 * err
    else:
        # H1 : μ > μ₀  -> p = P(T > t)
        p = tail if t >= 0.0 else 1.0 - tail
        be = err
    p = min(1.0, max(0.0, p))
    return {"statistique": _sig(t), "p_valeur": _sig(p), "borne_erreur": be, "ddl": n - 1}


def test_khi2_conformite(observes, attendus) -> dict:
    """Test du khi-deux d'adéquation : X² = Σ (Oᵢ − Eᵢ)²/Eᵢ, loi χ² à (k−1) ddl.

    Renvoie {'statistique', 'p_valeur', 'borne_erreur', 'ddl'}. Condition de validité : chaque effectif ATTENDU
    ≥ 5 (sinon ValueError). Observés = comptages réels ≥ 0 ; longueurs égales ≥ 2. p-valeur APPROCHÉE (borne rendue)."""
    obs = _exige_echantillon(observes, "observes", mini=2)
    att = _exige_echantillon(attendus, "attendus", mini=2)
    if len(obs) != len(att):
        raise ValueError("observes et attendus doivent avoir la même longueur")
    for o in obs:
        if o < 0.0:
            raise ValueError("effectif observé négatif : abstention")
    for e in att:
        if e < 5.0:
            raise ValueError("effectif attendu < 5 : condition de validité du khi-deux non remplie -> abstention")
    x2 = math.fsum((o - e) ** 2 / e for o, e in zip(obs, att))
    k = len(obs) - 1  # degrés de liberté
    tail, err = _chi2_tail(x2, float(k))
    return {"statistique": _sig(x2), "p_valeur": _sig(tail), "borne_erreur": err, "ddl": k}


# ── INTERVALLES DE CONFIANCE ─────────────────────────────────────────────────────────────────────────────────────
def ic_moyenne_sigma_connu(moyenne, sigma, n, niveau) -> tuple:
    """IC de la moyenne, σ CONNU : moyenne ± z_{1−α/2}·σ/√n. Renvoie (bas, haut).

    niveau = confiance dans ]0,1[ (ex. 0.95) ; n ≥ 2 ; σ > 0 ; sinon ValueError."""
    m = _exige_reel(moyenne, "moyenne")
    sigma = _exige_sigma(sigma)
    n = _exige_n(n)
    nv = _exige_niveau(niveau)
    z = phi_inverse(0.5 * (1.0 + nv))  # z_{1−α/2}, α = 1 − niveau
    demi = z * sigma / math.sqrt(n)
    return (_sig(m - demi), _sig(m + demi))


def ic_moyenne_sigma_inconnu(echantillon, niveau) -> tuple:
    """IC de la moyenne, σ INCONNU (Student) : x̄ ± t_{1−α/2, n−1}·s/√n. Renvoie (bas, haut).

    Variance nulle -> ValueError ; n ≥ 2 ; niveau dans ]0,1[. Bornes APPROCHÉES (quantile de Student numérique)."""
    ech = _exige_echantillon(echantillon, "echantillon", mini=2)
    nv = _exige_niveau(niveau)
    n = len(ech)
    moy = math.fsum(ech) / n
    var = math.fsum((x - moy) ** 2 for x in ech) / (n - 1)
    if var <= 0.0:
        raise ValueError("variance nulle : intervalle de Student indéfini (échantillon constant) -> abstention")
    s = math.sqrt(var)
    tq = _student_quantile(0.5 * (1.0 + nv), float(n - 1))
    demi = tq * s / math.sqrt(n)
    return (_sig(moy - demi), _sig(moy + demi))


def ic_proportion_wilson(succes, n, niveau) -> tuple:
    """IC d'une proportion par la méthode de WILSON (jamais Wald). Renvoie (bas, haut) ⊂ [0,1].

    Wald (p̂ ± z√(p̂(1−p̂)/n)) est FAUX aux extrêmes : pour succes=0 il donne [0,0]. Wilson reste dans [0,1] et
    couvre correctement. succes entier dans [0,n] ; n ≥ 1 ; niveau dans ]0,1[."""
    n = _exige_entier(n, "n", mini=1)
    succes = _exige_entier(succes, "succes", mini=0)
    if succes > n:
        raise ValueError("succes > n : impossible -> abstention")
    nv = _exige_niveau(niveau)
    z = phi_inverse(0.5 * (1.0 + nv))
    phat = succes / n
    z2 = z * z
    denom = 1.0 + z2 / n
    centre = (phat + z2 / (2.0 * n)) / denom
    demi = (z / denom) * math.sqrt(phat * (1.0 - phat) / n + z2 / (4.0 * n * n))
    bas = max(0.0, centre - demi)
    haut = min(1.0, centre + demi)
    return (_sig(bas), _sig(haut))


# ── INTERPRÉTATION HONNÊTE D'UNE P-VALEUR ────────────────────────────────────────────────────────────────────────
def interprete(p_valeur, alpha) -> str:
    """Interprète une p-valeur au seuil α, SANS erreur épistémique.

    Une p-valeur N'EST PAS P(H0 vraie) ; on ne conclut JAMAIS que « H1 est vraie ». p_valeur dans [0,1] ; α dans ]0,1[."""
    p = _exige_proba_fermee(p_valeur)
    a = _exige_niveau(alpha)
    rappel = (" Rappel : la p-valeur est P(observer un écart au moins aussi extrême | H0 vraie) — ce n'est PAS la "
              "probabilité que H0 soit vraie, et on ne conclut jamais à la vérité de l'hypothèse alternative H1.")
    if p <= a:
        return (f"p = {p:.4g} ≤ α = {a:.4g} : on REJETTE H0 au seuil α (résultat statistiquement significatif)."
                + rappel)
    return (f"p = {p:.4g} > α = {a:.4g} : on NE REJETTE PAS H0 (preuve insuffisante contre H0 ; cela ne prouve "
            f"pas que H0 est vraie)." + rappel)
