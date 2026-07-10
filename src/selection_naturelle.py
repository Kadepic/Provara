"""
SÉLECTION NATURELLE — génétique des populations, mécanismes EXACTS (PARTIE V, B-PHY).

Même posture FAUX=0 que `galois` / `geometries_non_euclidiennes` (le THÉORÈME juge, jamais un faux) :
  • Le MÉCANISME est un modèle DÉTERMINISTE exact, pas une corrélation :
      – Loi de HARDY-WEINBERG (1908) : sous panmixie, sans sélection/mutation/migration/dérive, les fréquences
        génotypiques d'un locus bi-allélique (A de fréquence p, a de fréquence q = 1 − p) valent
              (AA, Aa, aa) = (p², 2pq, q²),   avec l'invariant  p² + 2pq + q² = (p+q)² = 1.
      – Fréquence allélique estimée sur des EFFECTIFS observés : p = (2·n_AA + n_Aa) / (2·N),  N = n_AA+n_Aa+n_aa.
      – ÉQUATION DE SÉLECTION (Fisher/Haldane/Wright) : avec les fitness relatives w_AA, w_Aa, w_aa,
              p' = (p²·w_AA + p·q·w_Aa) / w̄,   où  w̄ = p²·w_AA + 2pq·w_Aa + q²·w_aa  (fitness moyenne).
        (Le numérateur = contribution des allèles A : AA en donne p²·w_AA, Aa en donne la MOITIÉ, soit pq·w_Aa.)
      – Coefficient de sélection  s = 1 − w  (fitness relative w rapportée à l'optimum 1).
      – Cas classique du RÉCESSIF LÉTAL (w_AA = w_Aa = 1, w_aa = 0) : la fréquence de a décroît selon
              q_n = q0 / (1 + n·q0)   (décroissance hyperbolique, JAMAIS exponentielle).

  • ARITHMÉTIQUE EXACTE : ces quantités sont des RATIOS rationnels. On travaille en `fractions.Fraction` et on
    REFUSE les flottants en entrée (0.9 binaire ≠ 9/10). Aucune approximation : les sorties sont EXACTES.

HORS PÉRIMÈTRE, dit explicitement :
  • La DÉRIVE génétique (`derive_allelique`) est STOCHASTIQUE (échantillonnage aléatoire des allèles d'une
    génération à l'autre). Elle n'a PAS de valeur déterministe : toute demande -> ValueError (abstention).

GARANTIES (vérifiées en adverse par `valide_selection_naturelle.py`) :
  - p (fréquence) hors [0, 1] -> ValueError ;
  - fitness négative -> ValueError ; effectif négatif -> ValueError ;
  - population vide (N = 0) -> ValueError ; w̄ = 0 (population éteinte) -> ValueError ;
  - flottant / str / complexe / bool -> ValueError (bool refusé : True n'est pas 1) ;
  - `generations_pour_frequence` : garde de non-convergence -> ValueError si la fréquence ne PROGRESSE pas
    vers la cible (fitness égales, mauvaise direction) ; plafond de générations -> ValueError ; et surtout
    **garde d'EXPLOSION EXACTE** -> ValueError dès que le dénominateur de p dépasse `_BITS_MAX` bits.
    Cette dernière n'est pas un luxe : en rationnels exacts le dénominateur DOUBLE presque à chaque
    génération, si bien qu'un plafond de 100 000 générations ne protège de rien (bug réel, mesuré le
    2026-07-10 : cinq processus bloqués à 100 % de CPU sur une surdominance dont la cible était au-delà de
    l'équilibre). On abstient plutôt que de tourner sans fin, et on ne rend jamais un résultat approché ;
  - PURES, déterministes, sans état global, sans aléa, sans horloge ; conservateur (faux négatif toléré,
    faux POSITIF interdit).

Stdlib UNIQUEMENT (`fractions`).
"""
from __future__ import annotations

from fractions import Fraction

SOURCE = "génétique des populations : loi de Hardy-Weinberg (1908) + équation de sélection Δp (Fisher/Haldane/Wright), formules classiques"

_UN = Fraction(1)
_ZERO = Fraction(0)


# ── helpers de validation ────────────────────────────────────────────────────────────────────────────────────────
# Borne de TAILLE de l'arithmétique exacte : au-delà, on abstient (cf. generations_pour_frequence).
_BITS_MAX = 4096

def _rationnel(x, nom: str) -> Fraction:
    """Convertit x en Fraction EXACTE. Accepte int (hors bool) ou Fraction. REFUSE float/str/complexe/bool.

    Les flottants sont refusés parce que 0.9 en binaire ne vaut PAS 9/10 : on ne prétend pas à l'exactitude
    sur une valeur déjà corrompue. Un appelant qui a un flottant doit le convertir explicitement (Fraction(k, m))."""
    if isinstance(x, bool):
        raise ValueError(f"{nom} : bool refusé (True n'est pas 1)")
    if isinstance(x, int):
        return Fraction(x)
    if isinstance(x, Fraction):
        return x
    raise ValueError(f"{nom} : entier ou Fraction exact requis, reçu {x!r} (flottant/str/complexe refusés)")


def _proba(x, nom: str = "fréquence") -> Fraction:
    """Fréquence allélique : rationnel exact dans [0, 1]."""
    p = _rationnel(x, nom)
    if p < 0 or p > 1:
        raise ValueError(f"{nom} hors [0, 1] : {p} (une fréquence est une proportion)")
    return p


def _fitness(x, nom: str = "fitness") -> Fraction:
    """Fitness relative : rationnel exact >= 0 (une fitness négative n'a pas de sens biologique)."""
    w = _rationnel(x, nom)
    if w < 0:
        raise ValueError(f"{nom} négative : {w} (une fitness est >= 0)")
    return w


def _effectif(x, nom: str) -> int:
    """Effectif : entier >= 0 (hors bool). Les comptages sont des entiers, jamais des flottants."""
    if isinstance(x, bool):
        raise ValueError(f"{nom} : bool refusé")
    if not isinstance(x, int):
        raise ValueError(f"{nom} : entier attendu, reçu {x!r}")
    if x < 0:
        raise ValueError(f"{nom} négatif : {x}")
    return x


# ── (a) HARDY-WEINBERG ───────────────────────────────────────────────────────────────────────────────────────────
def frequences_genotypiques(p) -> tuple:
    """Fréquences génotypiques (AA, Aa, aa) = (p², 2pq, q²) avec q = 1 − p (loi de Hardy-Weinberg).

    Renvoie un triplet de Fraction EXACT. Invariant : la somme vaut exactement 1. p hors [0,1] -> ValueError."""
    p = _proba(p)
    q = _UN - p
    return (p * p, 2 * p * q, q * q)


def frequence_allelique(n_AA, n_Aa, n_aa) -> Fraction:
    """Fréquence de l'allèle A estimée sur les effectifs : p = (2·n_AA + n_Aa) / (2·N), N = n_AA+n_Aa+n_aa.

    Renvoie une Fraction EXACTE. Effectif négatif -> ValueError ; population vide (N=0) -> ValueError."""
    a = _effectif(n_AA, "n_AA")
    h = _effectif(n_Aa, "n_Aa")
    b = _effectif(n_aa, "n_aa")
    N = a + h + b
    if N == 0:
        raise ValueError("population vide (N = 0) : fréquence indéfinie (abstention)")
    return Fraction(2 * a + h, 2 * N)


def ecart_hw(n_AA, n_Aa, n_aa) -> Fraction:
    """Écart MAXIMAL (en effectif) entre les génotypes observés et les attendus sous Hardy-Weinberg.

    Chemin de code INDÉPENDANT du test d'équilibre : estime p sur les observés, calcule les attendus
    N·(p², 2pq, q²), et renvoie max|observé − attendu| (Fraction exacte, >= 0). Population vide -> ValueError."""
    a = _effectif(n_AA, "n_AA")
    h = _effectif(n_Aa, "n_Aa")
    b = _effectif(n_aa, "n_aa")
    N = a + h + b
    if N == 0:
        raise ValueError("population vide (N = 0) : écart indéfini (abstention)")
    p = Fraction(2 * a + h, 2 * N)
    fAA, fAa, faa = frequences_genotypiques(p)
    att = (N * fAA, N * fAa, N * faa)
    obs = (Fraction(a), Fraction(h), Fraction(b))
    return max(abs(o - e) for o, e in zip(obs, att))


def equilibre_hw(n_AA, n_Aa, n_aa, tol=0) -> bool:
    """La population est-elle CONFORME à Hardy-Weinberg ? Test de conformité EXACT, sans p-valeur devinée.

    Compare chaque génotype observé à son attendu N·(p², 2pq, q²) (p estimé sur les observés) et renvoie True
    ssi le plus grand écart en effectif est <= tol. `tol` est une tolérance en effectif (entier/Fraction >= 0,
    défaut 0 = conformité exacte). Effectif négatif / N=0 / tol négatif -> ValueError."""
    t = _rationnel(tol, "tol")
    if t < 0:
        raise ValueError(f"tol négative : {t}")
    return ecart_hw(n_AA, n_Aa, n_aa) <= t


# ── (b) SÉLECTION ────────────────────────────────────────────────────────────────────────────────────────────────
def w_moyen(p, w_AA, w_Aa, w_aa) -> Fraction:
    """Fitness moyenne de la population : w̄ = p²·w_AA + 2pq·w_Aa + q²·w_aa (q = 1 − p).

    Renvoie une Fraction EXACTE >= 0. p hors [0,1] -> ValueError ; fitness négative -> ValueError."""
    p = _proba(p)
    q = _UN - p
    a = _fitness(w_AA, "w_AA")
    h = _fitness(w_Aa, "w_Aa")
    b = _fitness(w_aa, "w_aa")
    return p * p * a + 2 * p * q * h + q * q * b


def p_generation_suivante(p, w_AA, w_Aa, w_aa) -> Fraction:
    """Fréquence de A à la génération suivante sous sélection : p' = (p²·w_AA + p·q·w_Aa) / w̄.

    Renvoie une Fraction EXACTE dans [0,1]. p hors [0,1] / fitness négative -> ValueError ;
    w̄ = 0 (population éteinte) -> ValueError (on n'invente jamais une fréquence 0/0)."""
    p = _proba(p)
    q = _UN - p
    a = _fitness(w_AA, "w_AA")
    h = _fitness(w_Aa, "w_Aa")
    b = _fitness(w_aa, "w_aa")
    wbar = p * p * a + 2 * p * q * h + q * q * b
    if wbar == 0:
        raise ValueError("fitness moyenne nulle (population éteinte) : fréquence indéfinie 0/0 (abstention)")
    return (p * p * a + p * q * h) / wbar


def coefficient_selection(w) -> Fraction:
    """Coefficient de sélection s = 1 − w (w = fitness relative rapportée à l'optimum 1).

    Renvoie une Fraction EXACTE. Fitness négative -> ValueError. (s < 0 possible si w > 1 : allèle avantagé.)"""
    return _UN - _fitness(w, "w")


# ── (c) DÉRIVE : hors périmètre (stochastique) ───────────────────────────────────────────────────────────────────
def derive_allelique(*args, **kwargs):
    """DÉRIVE GÉNÉTIQUE — HORS PÉRIMÈTRE. La dérive est STOCHASTIQUE (échantillonnage aléatoire des allèles) :

    elle n'a pas de trajectoire déterministe, seulement une DISTRIBUTION. Ce module ne fournit que des
    mécanismes exacts et déterministes ; il s'ABSTIENT donc systématiquement (jamais une valeur inventée)."""
    raise ValueError(
        "dérive allélique : processus STOCHASTIQUE hors périmètre (aucune valeur déterministe ; abstention)"
    )


# ── (e) NOMBRE DE GÉNÉRATIONS POUR ATTEINDRE UNE FRÉQUENCE ──────────────────────────────────────────────────────-
def generations_pour_frequence(p0, p_cible, w_AA, w_Aa, w_aa, max_generations: int = 100000) -> int:
    """Nombre de générations de SÉLECTION pour que p passe de p0 à p_cible (première génération atteinte).

    Itère p_{n+1} = p_generation_suivante(p_n, ...) et renvoie le plus petit n tel que p a atteint/dépassé la
    cible (>= si croissant, <= si décroissant). GARDE DE NON-CONVERGENCE : si à une étape la fréquence ne se
    rapproche PAS strictement de la cible (fitness toutes égales -> p constant, ou mauvaise direction),
    -> ValueError. PLAFOND `max_generations` (jamais de boucle infinie) : cible non atteinte -> ValueError.
    p0 == p_cible -> 0. Entrées hors domaine -> ValueError."""
    p = _proba(p0, "p0")
    cible = _proba(p_cible, "p_cible")
    a = _fitness(w_AA, "w_AA")
    h = _fitness(w_Aa, "w_Aa")
    b = _fitness(w_aa, "w_aa")
    if isinstance(max_generations, bool) or not isinstance(max_generations, int) or max_generations < 1:
        raise ValueError("max_generations : entier >= 1 requis")

    if p == cible:
        return 0
    croissant = cible > p

    n = 0
    while n < max_generations:
        if (croissant and p >= cible) or (not croissant and p <= cible):
            return n
        p_next = p_generation_suivante(p, a, h, b)
        if abs(cible - p_next) >= abs(cible - p):
            raise ValueError(
                "non-convergence : la fréquence ne progresse pas vers la cible "
                "(fitness égales ou sélection dans la mauvaise direction)"
            )
        # GARDE D'EXPLOSION EXACTE (bug réel, mesuré 2026-07-10 : 5 processus à 100 % de CPU).
        # En arithmétique rationnelle EXACTE, le dénominateur de p double à peu près à chaque génération :
        # au bout de ~1000 générations il compte des milliers de bits et chaque opération devient
        # astronomique. Le plafond `max_generations` ne protège donc de RIEN à lui seul — c'est une garde
        # de papier. On borne la TAILLE de l'exact, et on ABSTIENT plutôt que de tourner sans fin.
        if p_next.denominator.bit_length() > _BITS_MAX:
            raise ValueError(
                "explosion de la représentation exacte à la génération %d (dénominateur > %d bits) : "
                "la trajectoire converge trop lentement pour être suivie en rationnels exacts. "
                "Abstention — un résultat approché ne serait pas prouvé." % (n + 1, _BITS_MAX)
            )
        p = p_next
        n += 1
    raise ValueError(f"cible non atteinte en {max_generations} générations (abstention, pas de boucle infinie)")
