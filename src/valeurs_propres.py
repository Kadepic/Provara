"""
VALEURS PROPRES d'une matrice donnée — spectre EXACT, FAUX=0 (sujet B-NEC, PARTIE I).

Posture (identique à `geometries_non_euclidiennes` / `galois` / `topologie`) : le MÉCANISME est un THÉORÈME
EXACT, jamais une approximation flottante déguisée en vérité.

  • Le polynôme caractéristique  p(λ) = det(λI − A)  est calculé en ARITHMÉTIQUE RATIONNELLE EXACTE
    (Faddeev–LeVerrier sur `Fraction`) : aucun arrondi, aucun flottant nulle part dans la chaîne.
    Il est vérifiable indépendamment par le théorème de CAYLEY–HAMILTON : p(A) = 0 (matrice nulle).

  • Les valeurs propres RATIONNELLES sont rendues EXACTEMENT (théorème des racines rationnelles +
    déflation), et chacune est CERTIFIÉE par le test exact  det(A − λI) = 0.

  • Les valeurs propres réelles IRRATIONNELLES ne sont JAMAIS inventées : on rend un INTERVALLE RATIONNEL
    [lo, hi] qui les ENCADRE de façon PROUVÉE (suites de STURM + dichotomie, arithmétique exacte), de
    largeur ≤ `tol`. La valeur flottante fournie est explicitement marquée « approchée », et l'intervalle
    exact reste la vérité. C'est l'inverse d'un faux : on dit ce qu'on sait, avec sa borne d'erreur.

  • Les valeurs propres NON RÉELLES (complexes) ne sont pas énumérées : on en donne le NOMBRE exact
    (deg − nombre de racines réelles comptées avec multiplicité). Abstention structurelle, jamais un faux.

  • Les MULTIPLICITÉS algébriques sont exactes (décomposition sans carré de Yun, exacte en caractéristique 0).
    La multiplicité GÉOMÉTRIQUE (dim ker(A − λI)) est exacte pour λ rationnel — la distinction alg > géom
    (bloc de Jordan) est donc dite, pas masquée.

GARANTIES (vérifiées en adverse par `valide_valeurs_propres.py`) :
  - matrice non carrée / vide / lignes de longueurs inégales      -> ValueError ;
  - entrée flottante (0.1 n'est pas un rationnel exact) / bool /
    str / complexe / NaN / inf                                    -> ValueError (exiger int ou Fraction) ;
  - n > _N_MAX                                                    -> ValueError (budget d'exactitude honnête) ;
  - `vecteur_propre` sur un λ qui n'est PAS valeur propre         -> ValueError ;
  - `vecteur_propre` sur un λ irrationnel                         -> ValueError (le noyau exact n'est pas
                                                                    représentable dans ℚ : on le DIT) ;
  - INVARIANT dur : Σ multiplicités (rationnelles + réelles irrationnelles + complexes) = n, sinon
    RuntimeError — jamais un spectre silencieusement incomplet ;
  - déterministe ; conservateur (abstention tolérée, faux POSITIF interdit).

Le module n'importe que la stdlib (`fractions`, `math`).
"""
from __future__ import annotations

import math
from fractions import Fraction

SOURCE = ("Faddeev–LeVerrier (polynôme caractéristique exact) · Cayley–Hamilton (vérification) · "
          "théorème des racines rationnelles · suites de Sturm (isolation certifiée) · "
          "décomposition sans carré de Yun (multiplicités)")

_N_MAX = 12                      # au-delà, l'exactitude rationnelle explose en taille : on le DIT (ValueError)
_TOL_DEFAUT = Fraction(1, 10 ** 12)
_CAP_DIVISEURS = 10 ** 12        # au-delà, la recherche de racines rationnelles est SIGNALÉE incomplète


# ── VALIDATION DES ENTRÉES ─────────────────────────────────────────────────────────────────────────────────────
def _exige_scalaire(x) -> Fraction:
    """Entrée de matrice : int ou Fraction UNIQUEMENT. Le flottant est refusé (0.1 n'est pas exact)."""
    if isinstance(x, bool):
        raise ValueError("entrée invalide : un booléen n'est pas un nombre (True n'est pas 1)")
    if isinstance(x, int):
        return Fraction(x)
    if isinstance(x, Fraction):
        return x
    raise ValueError(
        "entrée invalide : int ou Fraction exigé (le flottant est refusé — 0.1 n'est pas un rationnel exact ; "
        "utiliser Fraction(1, 10))")


def _exige_matrice(M):
    """Matrice carrée n×n à entrées rationnelles exactes. Renvoie (lignes, n)."""
    if not isinstance(M, (list, tuple)) or len(M) == 0:
        raise ValueError("matrice invalide : une séquence non vide de lignes est requise")
    n = len(M)
    if n > _N_MAX:
        raise ValueError("matrice trop grande : n ≤ %d (au-delà, l'exactitude rationnelle n'est pas tenue "
                         "dans un budget honnête)" % _N_MAX)
    lignes = []
    for ligne in M:
        if not isinstance(ligne, (list, tuple)) or len(ligne) != n:
            raise ValueError("matrice invalide : elle doit être CARRÉE (n lignes de n entrées)")
        lignes.append([_exige_scalaire(x) for x in ligne])
    return lignes, n


def _exige_rationnel(x) -> Fraction:
    if isinstance(x, bool):
        raise ValueError("valeur invalide : un booléen n'est pas un nombre")
    if isinstance(x, int):
        return Fraction(x)
    if isinstance(x, Fraction):
        return x
    raise ValueError("valeur invalide : int ou Fraction exigé (exactitude requise)")


def _exige_tol(tol) -> Fraction:
    tol = _exige_rationnel(tol)
    if tol <= 0:
        raise ValueError("tol invalide : un rationnel strictement positif est requis")
    return tol


# ── ALGÈBRE MATRICIELLE EXACTE ─────────────────────────────────────────────────────────────────────────────────
def _identite(n):
    return [[Fraction(1) if i == j else Fraction(0) for j in range(n)] for i in range(n)]


def _produit(A, B, n):
    return [[sum((A[i][k] * B[k][j] for k in range(n)), Fraction(0)) for j in range(n)] for i in range(n)]


def _trace(A, n) -> Fraction:
    return sum((A[i][i] for i in range(n)), Fraction(0))


def _echelonne(A, n, m):
    """Élimination de Gauss-Jordan EXACTE. Renvoie (RREF, rang, signe_permutation, pivots)."""
    R = [ligne[:] for ligne in A]
    rang = 0
    signe = 1
    pivots = []
    for col in range(m):
        piv = None
        for r in range(rang, n):
            if R[r][col] != 0:
                piv = r
                break
        if piv is None:
            continue
        if piv != rang:
            R[rang], R[piv] = R[piv], R[rang]
            signe = -signe
        p = R[rang][col]
        R[rang] = [x / p for x in R[rang]]
        for r in range(n):
            if r != rang and R[r][col] != 0:
                f = R[r][col]
                R[r] = [a - f * b for a, b in zip(R[r], R[rang])]
        pivots.append(col)
        rang += 1
        if rang == n:
            break
    return R, rang, signe, pivots


def determinant(M) -> Fraction:
    """Déterminant EXACT (élimination de Gauss sur Fraction). Aucun flottant."""
    A, n = _exige_matrice(M)
    # triangularisation (on ne normalise pas : on accumule le produit des pivots)
    R = [ligne[:] for ligne in A]
    det = Fraction(1)
    for col in range(n):
        piv = None
        for r in range(col, n):
            if R[r][col] != 0:
                piv = r
                break
        if piv is None:
            return Fraction(0)
        if piv != col:
            R[col], R[piv] = R[piv], R[col]
            det = -det
        det *= R[col][col]
        inv = R[col][col]
        for r in range(col + 1, n):
            if R[r][col] != 0:
                f = R[r][col] / inv
                R[r] = [a - f * b for a, b in zip(R[r], R[col])]
    return det


def rang(M) -> int:
    """Rang EXACT de la matrice."""
    A, n = _exige_matrice(M)
    _, r, _, _ = _echelonne(A, n, n)
    return r


# ── POLYNÔMES À COEFFICIENTS RATIONNELS (liste, indice = degré, exacte) ────────────────────────────────────────
def _p_norm(p):
    p = list(p)
    while p and p[-1] == 0:
        p.pop()
    return p


def _p_deg(p) -> int:
    return len(p) - 1                     # polynôme nul -> -1


def _p_add(a, b):
    n = max(len(a), len(b))
    return _p_norm([(a[i] if i < len(a) else Fraction(0)) + (b[i] if i < len(b) else Fraction(0))
                    for i in range(n)])


def _p_sub(a, b):
    n = max(len(a), len(b))
    return _p_norm([(a[i] if i < len(a) else Fraction(0)) - (b[i] if i < len(b) else Fraction(0))
                    for i in range(n)])


def _p_mul(a, b):
    if not a or not b:
        return []
    out = [Fraction(0)] * (len(a) + len(b) - 1)
    for i, x in enumerate(a):
        if x == 0:
            continue
        for j, y in enumerate(b):
            out[i + j] += x * y
    return _p_norm(out)


def _p_derive(p):
    return _p_norm([p[i] * i for i in range(1, len(p))])


def _p_divmod(a, b):
    b = _p_norm(b)
    if not b:
        raise ZeroDivisionError("division polynomiale par le polynôme nul")
    a = _p_norm(a)
    q = [Fraction(0)] * max(0, len(a) - len(b) + 1)
    r = list(a)
    while _p_norm(r) and _p_deg(_p_norm(r)) >= _p_deg(b):
        r = _p_norm(r)
        d = _p_deg(r) - _p_deg(b)
        c = r[-1] / b[-1]
        q[d] = c
        for i, y in enumerate(b):
            r[i + d] -= c * y
        r = _p_norm(r)
    return _p_norm(q), _p_norm(r)


def _p_monique(p):
    p = _p_norm(p)
    if not p:
        return []
    c = p[-1]
    return [x / c for x in p]


def _p_pgcd(a, b):
    a, b = _p_norm(a), _p_norm(b)
    while b:
        _, r = _p_divmod(a, b)
        a, b = b, r
    return _p_monique(a)


def _p_eval(p, x: Fraction) -> Fraction:
    acc = Fraction(0)
    for c in reversed(p):
        acc = acc * x + c
    return acc


# ── POLYNÔME CARACTÉRISTIQUE (Faddeev–LeVerrier, EXACT) ────────────────────────────────────────────────────────
def polynome_caracteristique(M) -> tuple:
    """p(λ) = det(λI − A), monique, coefficients EXACTS du degré le PLUS HAUT au plus bas.

    Ex. [[1,2],[3,4]] -> (1, -5, -2)  c.-à-d.  λ² − 5λ − 2.
    Vérifiable indépendamment : Cayley–Hamilton  p(A) = 0."""
    A, n = _exige_matrice(M)
    c = [Fraction(1)]                                   # c[0] = 1 (coeff de λⁿ)
    Mk = _identite(n)
    for k in range(1, n + 1):
        AMk = _produit(A, Mk, n)
        ck = -_trace(AMk, n) / k
        c.append(ck)
        if k < n:
            Mk = [[AMk[i][j] + (ck if i == j else Fraction(0)) for j in range(n)] for i in range(n)]
    return tuple(c)


def _carac_bas_en_haut(M):
    """Le polynôme caractéristique en représentation interne (indice = degré)."""
    return _p_norm(list(reversed(polynome_caracteristique(M))))


def evalue_polynome_en_matrice(M, coeffs):
    """p(A) pour p donné du degré le plus haut au plus bas — le test de CAYLEY–HAMILTON."""
    A, n = _exige_matrice(M)
    acc = [[Fraction(0)] * n for _ in range(n)]
    for c in coeffs:
        c = _exige_rationnel(c)
        acc = _produit(A, acc, n)
        for i in range(n):
            acc[i][i] += c
    return acc


# ── DÉCOMPOSITION SANS CARRÉ (Yun) — multiplicités EXACTES ─────────────────────────────────────────────────────
def _sans_carre(p):
    """Yun : renvoie [(facteur_i, i)] où facteur_i = produit des racines de multiplicité EXACTEMENT i."""
    p = _p_monique(p)
    if _p_deg(p) < 1:
        return []
    dp = _p_derive(p)
    a = _p_pgcd(p, dp)
    b, _ = _p_divmod(p, a)
    c, _ = _p_divmod(dp, a)
    d = _p_sub(c, _p_derive(b))
    out = []
    i = 1
    while _p_deg(b) > 0:
        f = _p_pgcd(b, d)
        if _p_deg(f) > 0:
            out.append((f, i))
        b, _ = _p_divmod(b, f)
        c, _ = _p_divmod(d, f)
        d = _p_sub(c, _p_derive(b))
        i += 1
        if i > _N_MAX + 1:                              # garde-fou : jamais de boucle infinie silencieuse
            raise RuntimeError("décomposition sans carré : non convergence (invariant violé)")
    return out


# ── RACINES RATIONNELLES EXACTES (théorème des racines rationnelles + déflation) ───────────────────────────────
def _diviseurs(n: int):
    n = abs(n)
    if n == 0:
        return []
    out = []
    i = 1
    while i * i <= n:
        if n % i == 0:
            out.append(i)
            if i != n // i:
                out.append(n // i)
        i += 1
    return sorted(out)


def _racines_rationnelles(f):
    """Racines rationnelles EXACTES d'un polynôme sans carré f. Renvoie (racines, reste, complet)."""
    f = _p_norm(f)
    racines = []
    # racine 0 : terme constant nul
    while f and f[0] == 0:
        racines.append(Fraction(0))
        f = f[1:]
    if _p_deg(f) < 1:
        return racines, f, True
    L = 1
    for c in f:
        L = L * c.denominator // math.gcd(L, c.denominator)
    ent = [int(c * L) for c in f]
    g = 0
    for c in ent:
        g = math.gcd(g, abs(c))
    if g > 1:
        ent = [c // g for c in ent]
    a0, an = abs(ent[0]), abs(ent[-1])
    if a0 > _CAP_DIVISEURS or an > _CAP_DIVISEURS:
        return racines, f, False                        # honnête : extraction rationnelle INCOMPLÈTE
    for p in _diviseurs(a0):
        for q in _diviseurs(an):
            for s in (1, -1):
                cand = Fraction(s * p, q)
                if _p_eval(f, cand) == 0:
                    racines.append(cand)
                    f, r = _p_divmod(f, [-cand, Fraction(1)])
                    if r:
                        raise RuntimeError("déflation impossible (invariant violé)")
                    if _p_deg(f) < 1:
                        return racines, f, True
                    a0 = abs(int(f[0] * 1)) if f[0].denominator == 1 else a0
                    break
    return racines, f, True


# ── ISOLATION CERTIFIÉE DES RACINES RÉELLES (suites de Sturm, arithmétique exacte) ─────────────────────────────
def _sturm(g):
    chaine = [_p_norm(g), _p_derive(g)]
    while _p_deg(chaine[-1]) > 0:
        _, r = _p_divmod(chaine[-2], chaine[-1])
        if not r:
            break
        chaine.append([-x for x in r])
    return chaine


def _variations(chaine, x: Fraction) -> int:
    prec = 0
    v = 0
    for p in chaine:
        if not p:
            continue
        s = _p_eval(p, x)
        if s == 0:
            continue
        s = 1 if s > 0 else -1
        if prec != 0 and s != prec:
            v += 1
        prec = s
    return v


def _borne_cauchy(g) -> Fraction:
    an = g[-1]
    b = max((abs(c) / abs(an) for c in g[:-1]), default=Fraction(0))
    return 1 + b


def _racines_reelles(g, tol: Fraction):
    """Racines réelles de g (SANS CARRÉ, sans racine rationnelle connue) : liste d'intervalles [lo,hi]
    PROUVÉS contenir exactement une racine, de largeur ≤ tol. Les racines rationnelles rencontrées
    exactement (évaluation nulle) sont rendues comme intervalle dégénéré [r, r]."""
    g = _p_norm(g)
    if _p_deg(g) < 1:
        return []
    chaine = _sturm(g)
    B = _borne_cauchy(g)

    def compte(a, b):
        return _variations(chaine, a) - _variations(chaine, b)

    exactes = []
    a0, b0 = -B, B
    # les bornes ne doivent pas être racines (B > toute racine en module, strict)
    total = compte(a0, b0)
    pile = [(a0, b0, total)]
    out = []
    garde = 0
    while pile:
        garde += 1
        if garde > 200000:
            raise RuntimeError("isolation des racines : non convergence (invariant violé)")
        a, b, k = pile.pop()
        if k <= 0:
            continue
        if k == 1 and (b - a) <= tol:
            out.append((a, b))
            continue
        m = (a + b) / 2
        if _p_eval(g, m) == 0:                          # racine rationnelle EXACTE tombée sur le milieu
            exactes.append(m)
            eps = min(tol, (b - a) / 4)
            ga, gb = m - eps, m + eps
            if _p_eval(g, ga) != 0:
                pile.append((a, ga, compte(a, ga)))
            if _p_eval(g, gb) != 0:
                pile.append((gb, b, compte(gb, b)))
            continue
        kg, kd = compte(a, m), compte(m, b)
        if kg > 0:
            pile.append((a, m, kg))
        if kd > 0:
            pile.append((m, b, kd))
    for r in exactes:
        out.append((r, r))
    return sorted(out)


# ── API PUBLIQUE ───────────────────────────────────────────────────────────────────────────────────────────────
def est_valeur_propre(M, lam) -> bool:
    """True ssi λ (rationnel) est valeur propre : det(A − λI) = 0, testé EXACTEMENT."""
    A, n = _exige_matrice(M)
    lam = _exige_rationnel(lam)
    B = [[A[i][j] - (lam if i == j else Fraction(0)) for j in range(n)] for i in range(n)]
    return determinant(B) == 0


def multiplicite_algebrique(M, lam) -> int:
    """Multiplicité ALGÉBRIQUE exacte de λ (rationnel) : plus grand m tel que (X − λ)^m divise p(λ)."""
    lam = _exige_rationnel(lam)
    p = _carac_bas_en_haut(M)
    if _p_eval(p, lam) != 0:
        return 0
    m = 0
    while True:
        q, r = _p_divmod(p, [-lam, Fraction(1)])
        if r:
            break
        p = q
        m += 1
        if _p_deg(p) < 1:
            break
    return m


def noyau(M):
    """Base EXACTE du noyau de M (liste de vecteurs à coefficients Fraction). [] si noyau trivial."""
    A, n = _exige_matrice(M)
    R, r, _, pivots = _echelonne(A, n, n)
    libres = [c for c in range(n) if c not in pivots]
    base = []
    for c in libres:
        v = [Fraction(0)] * n
        v[c] = Fraction(1)
        for i, pc in enumerate(pivots):
            v[pc] = -R[i][c]
        base.append(v)
    return base


def vecteur_propre(M, lam):
    """Base EXACTE du sous-espace propre de λ (rationnel). λ non valeur propre -> ValueError.

    Refuse explicitement un λ irrationnel : son noyau n'est pas représentable dans ℚ (on le DIT)."""
    A, n = _exige_matrice(M)
    lam = _exige_rationnel(lam)
    B = [[A[i][j] - (lam if i == j else Fraction(0)) for j in range(n)] for i in range(n)]
    if determinant(B) != 0:
        raise ValueError("λ n'est pas valeur propre de M : det(A − λI) ≠ 0 (aucun vecteur propre)")
    base = noyau(B)
    if not base:
        raise RuntimeError("λ valeur propre mais noyau trivial (invariant violé)")
    return base


def multiplicite_geometrique(M, lam) -> int:
    """dim ker(A − λI), EXACTE, pour λ rationnel. 0 si λ n'est pas valeur propre."""
    A, n = _exige_matrice(M)
    lam = _exige_rationnel(lam)
    B = [[A[i][j] - (lam if i == j else Fraction(0)) for j in range(n)] for i in range(n)]
    _, r, _, _ = _echelonne(B, n, n)
    return n - r


def valeurs_propres(M, tol=_TOL_DEFAUT) -> dict:
    """SPECTRE EXACT de M.

    Renvoie un dict :
      'polynome_caracteristique' : coefficients exacts (haut -> bas), monique ;
      'trace', 'determinant'     : Fraction exactes ;
      'rationnelles'             : [(Fraction λ, multiplicité)] — EXACTES et certifiées det(A−λI)=0 ;
      'reelles_irrationnelles'   : [{'intervalle': (lo, hi) Fractions PROUVÉ encadrant, 'approx': float
                                     (marqué approché), 'multiplicite': m}] ;
      'nb_complexes_non_reelles' : nombre exact de valeurs propres non réelles (avec multiplicité) ;
      'exactitude_rationnelle_complete' : False si la recherche de racines rationnelles a été bornée
                                          (très grands coefficients) — honnêteté, pas un faux.

    INVARIANT : Σ multiplicités = n, sinon RuntimeError (jamais un spectre silencieusement incomplet)."""
    A, n = _exige_matrice(M)
    tol = _exige_tol(tol)
    coeffs = polynome_caracteristique(M)
    p = _p_norm(list(reversed(coeffs)))

    rationnelles = {}
    irrationnelles = []
    complexes = 0
    complet = True

    for facteur, mult in _sans_carre(p):
        rats, reste, ok = _racines_rationnelles(facteur)
        complet = complet and ok
        for r in rats:
            rationnelles[r] = rationnelles.get(r, 0) + mult
        if _p_deg(reste) >= 1:
            brackets = _racines_reelles(reste, tol)
            for lo, hi in brackets:
                if lo == hi:                            # racine rationnelle attrapée par le milieu
                    rationnelles[lo] = rationnelles.get(lo, 0) + mult
                else:
                    irrationnelles.append({"intervalle": (lo, hi),
                                           "approx": float((lo + hi) / 2),
                                           "multiplicite": mult})
            nb_reelles = len(brackets)
            complexes += (_p_deg(reste) - nb_reelles) * mult

    somme = sum(rationnelles.values()) + sum(d["multiplicite"] for d in irrationnelles) + complexes
    if somme != n:
        raise RuntimeError("spectre incomplet : Σ multiplicités = %d ≠ n = %d (invariant violé)" % (somme, n))
    for lam in rationnelles:
        if not est_valeur_propre(M, lam):
            raise RuntimeError("valeur propre rationnelle non certifiée : det(A − λI) ≠ 0 (invariant violé)")

    return {
        "polynome_caracteristique": coeffs,
        "trace": _trace(A, n),
        "determinant": determinant(M),
        "rationnelles": sorted(rationnelles.items()),
        "reelles_irrationnelles": sorted(irrationnelles, key=lambda d: d["intervalle"][0]),
        "nb_complexes_non_reelles": complexes,
        "exactitude_rationnelle_complete": complet,
    }
