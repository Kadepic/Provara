"""RÉCURRENCES & COMPLEXITÉ — THÉORÈME MAÎTRE et suites récurrentes linéaires, MÉCANISME EXACT, FAUX=0
(partie I & IX, B-NEC : « complexité d'un algorithme donné » + « complexité et coût d'un algorithme donné »).

Posture (identique à `algo_analyse`/`galois`/`geometries_non_euclidiennes`) : ce ne sont PAS des tables
recopiées mais des RÉSULTATS DÉRIVÉS d'un théorème exact. `algo_analyse` catalogue les classes des TRIS
(le n·log n du tri fusion y est CODÉ EN DUR) ; ici on RÉSOUT la récurrence qui les produit.

MÉCANISME (théorèmes EXACTS, pas des corrélations) :
  • THÉORÈME MAÎTRE (CLRS, forme f(n)=Θ(n^k)) pour  T(n) = a·T(n/b) + Θ(n^k),  a≥1 entier, b>1 entier, k≥0 :
        on compare  log_b(a)  à  k. La comparaison est faite de façon EXACTE par arithmétique ENTIÈRE :
        avec k = p/q (Fraction), log_b(a) ⋛ k  ⇔  a^q ⋛ b^p  (b>1 ⇒ log croissant) — AUCUN flottant décisionnel.
          – cas 1 (log_b a > k) : Θ(n^{log_b a})       (coût dominé par les feuilles) ;
          – cas 2 (log_b a = k) : Θ(n^k · log n)        (coûts par niveau égaux) ;
          – cas 3 (log_b a < k) : Θ(n^k)                (coût dominé par la racine).
        Le cas 3 EXIGE la CONDITION DE RÉGULARITÉ  a·f(n/b) ≤ c·f(n) pour un c<1 ; pour f(n)=n^k elle est
        AUTOMATIQUEMENT satisfaite avec  c = a/b^k < 1  (car log_b a < k ⇔ a < b^k) — le module le DIT.
        Pour toute AUTRE forme de f, `theoreme_maitre_general` lève ValueError (le théorème ne s'applique pas
        partout : régularité/polynomialité non garanties) — abstention structurelle.
  • log_b(a) est rendu comme Fraction EXACTE quand a et b sont multiplicativement dépendants (mêmes facteurs
    premiers à exposants proportionnels) ; sinon comme flottant ARRONDI à 10 chiffres significatifs, MARQUÉ approché.
  • SUITES RÉCURRENTES LINÉAIRES à coefficients constants (Fibonacci) par l'ÉQUATION CARACTÉRISTIQUE :
    formule close EXACTE (Fractions) quand les racines sont rationnelles (discriminant carré parfait) ;
    ENCADREMENT rationnel prouvé de la racine dominante sinon (nombre d'or). Le terme F(n) est aussi calculable
    par ITÉRATION EXACTE (`terme_recurrence`), chemin de code indépendant servant de contre-preuve.

GARANTIES (vérifiées en adverse par `valide_recurrences.py`) :
  - b ≤ 1, a < 1, k < 0  -> ValueError (hypothèses du théorème violées) ;
  - bool / str / flottant / NaN / ±inf / mauvaise arité  -> ValueError (True n'est pas 1) ;
  - récurrence hors catalogue (`complexite_diviser_regner`) -> ValueError ;
  - racines complexes (discriminant < 0), degré non supporté, forme de f non polynomiale -> ValueError ;
  - déterministe, pur ; conservateur (faux négatif toléré, faux POSITIF interdit).

Dépendance : `algo_analyse` (stdlib pur, même repo) pour la COMPARAISON asymptotique des classes catalogue.
"""
from __future__ import annotations

import math
from fractions import Fraction

from algo_analyse import ORDRE_ASYMPTOTIQUE
from algo_analyse import compare_asymptotique as _algo_compare

SOURCE = "Théorème maître (Cormen–Leiserson–Rivest–Stein, CLRS ch. 4) + équation caractéristique des suites récurrentes linéaires"

_CHIFFRES_SIGNIFICATIFS = 10


# ── helpers de validation (les bool sont REFUSÉS ; les flottants aussi là où l'exactitude est requise) ────────────
def _entier(x, mini):
    if not isinstance(x, int) or isinstance(x, bool):
        raise ValueError(f"entier attendu (bool/flottant refusés), reçu {x!r}")
    if x < mini:
        raise ValueError(f"entier ≥ {mini} attendu, reçu {x}")
    return x


def _exige_k(k) -> Fraction:
    """Exposant k ≥ 0 : entier ou Fraction EXACTS (les flottants sont refusés — décision par entiers)."""
    if isinstance(k, bool):
        raise ValueError("k booléen refusé (True n'est pas 1)")
    if isinstance(k, int):
        K = Fraction(k)
    elif isinstance(k, Fraction):
        K = k
    else:
        raise ValueError(f"k invalide : entier ou Fraction attendu (flottant/str refusés), reçu {k!r}")
    if K < 0:
        raise ValueError("k < 0 : hors des hypothèses du théorème maître -> abstention")
    return K


def _exige_num(x) -> Fraction:
    """Coefficient/valeur initiale EXACT : entier ou Fraction (bool/flottant/str refusés)."""
    if isinstance(x, bool):
        raise ValueError("valeur booléenne refusée")
    if isinstance(x, int):
        return Fraction(x)
    if isinstance(x, Fraction):
        return x
    raise ValueError(f"valeur invalide : entier ou Fraction attendu, reçu {x!r}")


def _sig(x: float, n: int = _CHIFFRES_SIGNIFICATIFS) -> float:
    """Arrondit un flottant à n chiffres significatifs (précision honnête)."""
    if x == 0:
        return 0.0
    return float(f"{x:.{n}g}")


def _facteurs(n: int) -> dict:
    """Factorisation en nombres premiers de n ≥ 2 -> {p: exposant}."""
    f = {}
    m = n
    p = 2
    while p * p <= m:
        while m % p == 0:
            f[p] = f.get(p, 0) + 1
            m //= p
        p += 1
    if m > 1:
        f[m] = f.get(m, 0) + 1
    return f


def _log_rationnel(a: int, b: int):
    """log_b(a) EXACT (Fraction) ssi a,b multiplicativement dépendants, sinon None (irrationnel).

    a = ∏ p^{e_p}, b = ∏ p^{f_p} : log_b(a) = r ⇔ e_p = r·f_p ∀p ⇒ r = e_p/f_p, identique pour tout p.
    """
    if a == 1:
        return Fraction(0)
    fa = _facteurs(a)
    fb = _facteurs(b)
    if set(fa) != set(fb):
        return None
    ratio = None
    for p in fa:
        r = Fraction(fa[p], fb[p])
        if ratio is None:
            ratio = r
        elif r != ratio:
            return None
    return ratio


# ── formatage des classes de coût (bare = étiquette d'ORDRE_ASYMPTOTIQUE si reconnue, sinon None) ─────────────────
def _bare_puissance(expo: Fraction) -> str:
    if expo == 0:
        return "1"
    if expo == 1:
        return "n"
    if expo.denominator == 1:
        return f"n^{expo.numerator}"
    return f"n^{expo}"


def _bare_puissance_log(expo: Fraction) -> str:
    if expo == 0:
        return "log n"
    if expo == 1:
        return "n log n"
    if expo.denominator == 1:
        return f"n^{expo.numerator} log n"
    return f"n^{expo} log n"


def _classe_reconnue(bare: str):
    return bare if bare in ORDRE_ASYMPTOTIQUE else None


# ── THÉORÈME MAÎTRE ──────────────────────────────────────────────────────────────────────────────────────────────
def theoreme_maitre(a, b, k) -> dict:
    """Résout T(n) = a·T(n/b) + Θ(n^k) par le théorème maître (a≥1 entier, b>1 entier, k≥0).

    Renvoie {'cas': 1|2|3, 'complexite': str Θ(...), 'classe': str|None, 'log_b_a': Fraction|float,
             'justification': str}. Décision par arithmétique entière (a^q vs b^p) — aucun flottant décisionnel.
    b ≤ 1 / a < 1 / k < 0 -> ValueError.
    """
    A = _entier(a, 1)      # a ≥ 1
    B = _entier(b, 2)      # b > 1  (entier ⇒ b ≥ 2 ; b ≤ 1 rejeté)
    K = _exige_k(k)        # k ≥ 0

    p, q = K.numerator, K.denominator          # q ≥ 1, p ≥ 0
    gauche = A ** q                            # comparaison EXACTE : a^q ⋛ b^p ⇔ log_b(a) ⋛ k
    droite = B ** p

    lba = _log_rationnel(A, B)                 # Fraction si rationnel, sinon None
    lba_report = lba if lba is not None else _sig(math.log(A) / math.log(B))

    if gauche > droite:
        cas = 1
        if lba is not None:
            bare = _bare_puissance(lba)
            complexite = f"Θ({bare})"
            classe = _classe_reconnue(bare)
            just = (f"log_{B}({A}) = {lba} > k = {K} -> cas 1 : coût dominé par les feuilles, "
                    f"Θ(n^log_b(a)) = {complexite}.")
        else:
            complexite = f"Θ(n^{lba_report}) [exposant irrationnel, approché ~10 c.s.]"
            classe = None
            just = (f"log_{B}({A}) ≈ {lba_report} > k = {K} (car {A} > {B}^{K} au sens a^q > b^p) "
                    f"-> cas 1 : Θ(n^log_b(a)), exposant irrationnel MARQUÉ approché.")
    elif gauche == droite:
        cas = 2
        bare = _bare_puissance_log(K)
        complexite = f"Θ({bare})"
        classe = _classe_reconnue(bare)
        just = (f"log_{B}({A}) = {K} = k -> cas 2 : coûts par niveau égaux, Θ(n^k·log n) = {complexite}.")
    else:
        cas = 3
        bare = _bare_puissance(K)
        complexite = f"Θ({bare})"
        classe = _classe_reconnue(bare)
        just = (f"log_{B}({A}) < k = {K} (car {A} < {B}^{K}) -> cas 3 : Θ(n^k) = {complexite}. "
                f"Condition de régularité a·f(n/b) ≤ c·f(n) AUTOMATIQUEMENT satisfaite pour f(n)=n^k "
                f"avec c = a/b^k < 1.")

    return {"cas": cas, "complexite": complexite, "classe": classe,
            "log_b_a": lba_report, "justification": just}


def theoreme_maitre_general(a, b, f) -> dict:
    """Théorème maître pour une f donnée sous forme de chaîne. N'accepte que f POLYNOMIALE 'n^k' (ou '1','n').

    Pour f(n)=n^k, délègue à `theoreme_maitre` (régularité garantie). Toute autre f (ex. 'n log n', '2^n',
    'log n', 'n!') -> ValueError : le théorème maître de base ne s'y applique pas -> abstention structurelle.
    """
    _entier(a, 1)
    _entier(b, 2)
    if not isinstance(f, str):
        raise ValueError(f"f (chaîne, ex. 'n^2') attendu, reçu {f!r}")
    s = "".join(f.split()).lower()
    if s == "1":
        m = 0
    elif s == "n":
        m = 1
    elif s.startswith("n^") and s[2:].isdigit():
        m = int(s[2:])
    else:
        raise ValueError(f"f = {f!r} non polynomiale n^k : théorème maître (forme de base) non applicable "
                         f"(régularité/polynomialité non garanties) -> abstention")
    res = theoreme_maitre(a, b, m)
    res["justification"] += (f" [f={f!r} = n^{m} : forme polynomiale, condition de régularité vérifiée.]")
    return res


# ── SUITES RÉCURRENTES LINÉAIRES À COEFFICIENTS CONSTANTS ─────────────────────────────────────────────────────────
def _sqrt_exact(x: Fraction):
    """√x EXACT (Fraction) ssi x est un carré parfait rationnel, sinon None. x ≥ 0."""
    num, den = x.numerator, x.denominator      # x ≥ 0 ⇒ num ≥ 0, den > 0
    sn, sd = math.isqrt(num), math.isqrt(den)
    if sn * sn == num and sd * sd == den:
        return Fraction(sn, sd)
    return None


def _encadre_sqrt(x: Fraction, digits: int):
    """Encadrement PROUVÉ (low ≤ √x < high) à 10^-digits près, par arithmétique entière (isqrt). x ≥ 0."""
    N, D = x.numerator, x.denominator
    ech = 10 ** digits
    floorval = (N * ech * ech) // D            # floorval ≤ x·10^{2d} < floorval+1
    m = math.isqrt(floorval)                    # m² ≤ floorval ≤ x·10^{2d} ⇒ (m/10^d)² ≤ x
    # (m+1)² > floorval ≥ x·10^{2d} - 1, et (m+1)² entier > x·10^{2d} ⇒ ((m+1)/10^d)² > x
    return Fraction(m, ech), Fraction(m + 1, ech)


def resout_recurrence_lineaire(coeffs, initiaux) -> dict:
    """Résout une suite F(n) = c1·F(n-1) + … + cd·F(n-d) par l'équation caractéristique (degré 1 ou 2).

    `coeffs` = [c1, …, cd] (entiers/Fractions), `initiaux` = [F(0), …, F(d-1)]. Renvoie un dict décrivant
    le polynôme caractéristique, les RACINES (Fractions exactes si rationnelles, ENCADREMENT sinon) et la
    formule close exacte quand elle existe. Racines complexes / degré non supporté -> ValueError.
    """
    if not isinstance(coeffs, (list, tuple)) or not isinstance(initiaux, (list, tuple)):
        raise ValueError("coeffs et initiaux doivent être des listes/tuples")
    d = len(coeffs)
    if d not in (1, 2):
        raise ValueError(f"degré {d} non supporté (seuls 1 et 2 sont résolus exactement) -> abstention")
    if len(initiaux) != d:
        raise ValueError(f"initiaux : exactement {d} valeur(s) requise(s), reçu {len(initiaux)}")
    c = [_exige_num(x) for x in coeffs]
    f0 = [_exige_num(x) for x in initiaux]

    if d == 1:
        r = c[0]                                # F(n) = c1·F(n-1) ⇒ racine r = c1, F(n) = F0·r^n
        return {"degre": 1, "exact": True, "polynome_caract": f"x - {r}",
                "racines": (r,),
                "formule": f"F(n) = {f0[0]}·({r})^n",
                "note": "récurrence géométrique : racine rationnelle, formule close exacte"}

    # degré 2 : x² - c1·x - c2 = 0
    c1, c2 = c
    disc = c1 * c1 + 4 * c2                      # discriminant
    poly = f"x^2 - ({c1})·x - ({c2})"
    if disc < 0:
        raise ValueError("discriminant < 0 : racines complexes (suite oscillante) -> hors périmètre, abstention")

    sq = _sqrt_exact(disc)
    if sq is not None:
        r1 = (c1 + sq) / 2
        r2 = (c1 - sq) / 2
        if r1 == r2:                            # racine double : F(n) = (A + B·n)·r^n
            r = r1
            A = f0[0]
            if r == 0:
                raise ValueError("racine double nulle -> dégénéré, abstention")
            B = f0[1] / r - A
            return {"degre": 2, "exact": True, "polynome_caract": poly, "discriminant": disc,
                    "racines": (r, r), "racine_double": True,
                    "coeffs_formule": (A, B),
                    "formule": f"F(n) = ({A} + ({B})·n)·({r})^n",
                    "note": "racine double rationnelle, formule close exacte"}
        # racines distinctes rationnelles : F(n) = A·r1^n + B·r2^n
        A = (f0[1] - f0[0] * r2) / (r1 - r2)
        B = f0[0] - A
        return {"degre": 2, "exact": True, "polynome_caract": poly, "discriminant": disc,
                "racines": (r1, r2),
                "coeffs_formule": (A, B),
                "formule": f"F(n) = ({A})·({r1})^n + ({B})·({r2})^n",
                "note": "racines rationnelles distinctes, formule close exacte"}

    # racines irrationnelles : encadrement rationnel PROUVÉ de la racine dominante (c1 + √disc)/2
    slow, shigh = _encadre_sqrt(disc, 9)
    dom_low = (c1 + slow) / 2
    dom_high = (c1 + shigh) / 2
    return {"degre": 2, "exact": False, "polynome_caract": poly, "discriminant": disc,
            "racines": ("(c1 + √Δ)/2", "(c1 - √Δ)/2"),
            "racine_dominante_encadree": (dom_low, dom_high),
            "croissance": "F(n) = Θ(r^n), r = racine dominante (nombre d'or φ pour Fibonacci)",
            "note": "racines irrationnelles : pas de formule rationnelle close, ENCADREMENT prouvé de r"}


def terme_recurrence(coeffs, initiaux, n) -> Fraction:
    """F(n) par ITÉRATION EXACTE (chemin indépendant de `resout_recurrence_lineaire`).

    F(i) = Σ_{j=0..d-1} coeffs[j]·F(i-1-j). Renvoie une valeur EXACTE (int/Fraction). n ≥ 0.
    """
    if not isinstance(coeffs, (list, tuple)) or not isinstance(initiaux, (list, tuple)):
        raise ValueError("coeffs et initiaux doivent être des listes/tuples")
    d = len(coeffs)
    if d < 1:
        raise ValueError("degré ≥ 1 requis")
    if len(initiaux) != d:
        raise ValueError(f"initiaux : exactement {d} valeur(s) requise(s)")
    c = [_exige_num(x) for x in coeffs]
    vals = [_exige_num(x) for x in initiaux]
    _entier(n, 0)
    if n < d:
        return vals[n]
    fenetre = list(vals)
    for i in range(d, n + 1):
        nxt = Fraction(0)
        for j in range(d):
            nxt += c[j] * fenetre[i - 1 - j]
        fenetre.append(nxt)
    return fenetre[n]


# ── DIVISER-POUR-RÉGNER : catalogue de récurrences classiques RÉSOLUES par le théorème maître ────────────────────
# (a, b, k) de T(n) = a·T(n/b) + Θ(n^k). AUCUNE classe n'est lue dans une table : tout passe par theoreme_maitre.
_DIVISER_REGNER = {
    "recherche_dichotomique": (1, 2, 0),   # T(n)=T(n/2)+O(1)   -> Θ(log n)
    "tri_fusion":             (2, 2, 1),   # T(n)=2T(n/2)+O(n)  -> Θ(n log n)
    "karatsuba":              (3, 2, 1),   # T(n)=3T(n/2)+O(n)  -> Θ(n^{log2 3}) ≈ n^1.585
    "strassen":               (7, 2, 2),   # T(n)=7T(n/2)+O(n²) -> Θ(n^{log2 7}) ≈ n^2.807
}


def complexite_diviser_regner(nom: str) -> dict:
    """Complexité d'un algorithme diviser-pour-régner classique, RÉSOLUE par le théorème maître (pas de table).

    `nom` ∈ {recherche_dichotomique, tri_fusion, karatsuba, strassen}. Hors catalogue -> ValueError.
    """
    if not isinstance(nom, str):
        raise ValueError(f"nom (chaîne) attendu, reçu {nom!r}")
    cle = "".join(nom.split()).lower()
    if cle not in _DIVISER_REGNER:
        raise ValueError(f"algorithme diviser-pour-régner hors catalogue : {nom!r} -> abstention")
    a, b, k = _DIVISER_REGNER[cle]
    res = theoreme_maitre(a, b, k)             # RÉSOLU, jamais recopié
    res["nom"] = cle
    res["a"], res["b"], res["k"] = a, b, k
    return res


def exposant_inferieur(a, b, k_ref) -> bool:
    """Décide EXACTEMENT si log_b(a) < k_ref (a^q < b^p avec k_ref=p/q). Preuve d'optimalité asymptotique.

    Ex. Karatsuba : log_2(3) < 2 car 3 < 2² = 4 (sous-quadratique). Strassen : log_2(7) < 3 car 7 < 2³ = 8
    (sous-cubique). a≥1 entier, b>1 entier, k_ref≥0. Décision par entiers, aucun flottant.
    """
    A = _entier(a, 1)
    B = _entier(b, 2)
    K = _exige_k(k_ref)
    p, q = K.numerator, K.denominator
    return A ** q < B ** p


def compare_asymptotique(c1: str, c2: str) -> str:
    """Classe dominante entre deux étiquettes catalogue (délègue à `algo_analyse.compare_asymptotique`).

    Sert à situer une classe RÉSOLUE ici (ex. 'n log n') dans l'ordre de croissance établi. Classe inconnue
    d'`algo_analyse` -> ValueError (abstention).
    """
    return _algo_compare(c1, c2)
