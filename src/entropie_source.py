"""
ENTROPIE D'UNE SOURCE (processus stochastique) — PARTIE VII, B-NEC — posture FAUX=0.

DISTINCTION FONDAMENTALE, source du présent module :
  • `information_calcul.entropie(p)` calcule H d'une DISTRIBUTION *déjà donnée* (mécanisme exact).
  • ICI on traite l'entropie d'une SOURCE, c.-à-d. d'un PROCESSUS qui émet des symboles. On n'observe
    jamais la « vraie » distribution : on l'ESTIME à partir d'une séquence finie. Une entropie estimée
    n'est PAS l'entropie de la source — le module refuse de la présenter comme telle.

MÉCANISMES EXACTS (aucune corrélation, aucun modèle appris) :
  (a) ENTROPIE EMPIRIQUE (plug-in) : Ĥ = H(fréquences observées), déléguée à information_calcul.entropie.
      On RENVOIE AUSSI le nombre d'observations N : une entropie estimée sur 10 symboles ne vaut rien.
      `fiable(sequence, alphabet)` = (N ≥ 5·|alphabet|) : règle de pouce classique, on le DIT.
  (b) BIAIS D'ESTIMATION (le point FAUX=0) : l'estimateur plug-in est BIAISÉ VERS LE BAS
      (E[Ĥ_plugin] ≤ H). Correction de Miller–Madow : Ĥ_MM = Ĥ_plugin + (K−1)/(2N), K = nb de symboles
      OBSERVÉS, N = nb d'observations. MÊME corrigée, l'estimation reste APPROCHÉE (marquée telle).
  (c) SOURCE DE MARKOV d'ordre 1 : le TAUX D'ENTROPIE (entropie par symbole du processus) vaut
          h = Σ_i π_i · H(P(·|i))
      où π est la distribution stationnaire (πP = π) et P(·|i) la i-ème ligne de la matrice de transition.
      `distribution_stationnaire(P)` résout πP = π EXACTEMENT sur ℚ (système linéaire, algebre_lineaire)
      quand les lignes somment exactement à 1 ; sinon PUISSANCE ITÉRÉE avec critère d'arrêt (approché).
  (d) `taux_entropie_empirique(sequence, ordre)` : entropie conditionnelle empirique H(X_t | X_{t-ordre..t-1}),
      estimée par les comptes de contextes observés.
  (e) STATIONNARITÉ VÉRIFIÉE (le point FAUX=0 du taux) : la formule h = Σ π_i H(P(·|i)) ne mesure le taux
      de la source QUE si π est LA distribution stationnaire. `entropie_conditionnelle_markov` VÉRIFIE
      donc explicitement πP = π (à 1e-9 près) et ABSTIENT (ValueError) sinon — sans quoi elle rendrait un
      nombre qui n'est pas un taux d'entropie. L'invariant h ≤ H(π) (le conditionnement réduit l'incertitude)
      reste vérifié comme garde-fou secondaire (RuntimeError si jamais violé), mais il découle déjà de la
      stationnarité et n'est plus la garde principale.

GARANTIES vérifiées en adverse par `valide_entropie_source.py` :
  - séquence vide -> ValueError ; élément non hashable -> ValueError ;
  - alphabet vide -> ValueError ;
  - matrice de transition non carrée / entrée hors [0,1] / bool / NaN / inf / str -> ValueError ;
  - ligne ne sommant pas à 1 (tol) -> ValueError (matrice non stochastique) ;
  - distribution stationnaire fournie invalide -> ValueError ;
  - distribution fournie NON stationnaire (πP ≠ π à 1e-9) -> ValueError (la garde qui rend le taux honnête) ;
  - ordre non entier ≥ 1, ou séquence trop courte pour l'ordre -> ValueError ;
  - taux d'entropie > entropie stationnaire -> RuntimeError (invariant secondaire, redondant avec ci-dessus) ;
  - déterministe ; conservateur (faux négatif toléré, faux POSITIF interdit).

Alphabet d'UN SEUL symbole : cas trivial documenté -> entropie = 0 (source déterministe, aucune surprise).
Stdlib uniquement (math, fractions) + réutilisation de information_calcul et algebre_lineaire (mêmes règles).
"""
from __future__ import annotations

import math
from fractions import Fraction

import information_calcul as _ic
import algebre_lineaire as _al

SOURCE = ("entropie de Shannon d'une source (Cover & Thomas, Elements of Information Theory) : "
          "estimateur plug-in + correction de biais de Miller–Madow (1955) ; taux d'entropie d'une "
          "chaîne de Markov h = Σ π_i H(P(·|i)) ; distribution stationnaire πP=π (Perron–Frobenius)")

_TOL = 1e-9
_MAX_ITERS = 200000


# ── VALIDATION DES ENTRÉES ─────────────────────────────────────────────────────────────────────────────────────
def _est_reel(x) -> bool:
    """True ssi x est un réel fini (les bool sont REFUSÉS : True n'est pas 1)."""
    return isinstance(x, (int, float)) and not isinstance(x, bool) and math.isfinite(x)


def _valide_sequence(sequence):
    """Séquence non vide de symboles HASHABLES. Renvoie la liste des symboles."""
    if not isinstance(sequence, (list, tuple)) or len(sequence) == 0:
        raise ValueError("séquence invalide : une liste/tuple NON VIDE de symboles est requise")
    for s in sequence:
        try:
            hash(s)
        except TypeError:
            raise ValueError(f"symbole non hashable : {s!r} (une source émet des symboles atomiques)")
    return list(sequence)


def _comptes(symboles):
    """Table {symbole: nombre d'occurrences}, déterministe (ordre d'apparition)."""
    c = {}
    for s in symboles:
        c[s] = c.get(s, 0) + 1
    return c


def _to_fraction(x) -> Fraction:
    """Convertit une entrée numérique en Fraction EXACTE (bool refusé ; float via son écriture décimale)."""
    if isinstance(x, bool):
        raise ValueError("entrée invalide : un booléen n'est pas une probabilité (True n'est pas 1)")
    if isinstance(x, int):
        return Fraction(x)
    if isinstance(x, Fraction):
        return x
    if isinstance(x, float):
        if not math.isfinite(x):
            raise ValueError("entrée invalide : NaN/inf refusé")
        return Fraction(str(x))            # 0.9 -> 9/10 (l'intention décimale de l'utilisateur), exact
    raise ValueError(f"entrée numérique attendue, reçu {x!r}")


def _valide_transition(matrice):
    """Matrice de transition n×n STOCHASTIQUE. Renvoie (rows_float, n).

    Refuse : non carrée, entrée non réelle/bool/str/NaN/inf, entrée hors [0,1], ligne ne sommant pas à 1 (tol)."""
    if not isinstance(matrice, (list, tuple)) or len(matrice) == 0:
        raise ValueError("matrice de transition invalide : séquence non vide de lignes requise")
    n = len(matrice)
    rows = []
    for ligne in matrice:
        if not isinstance(ligne, (list, tuple)) or len(ligne) != n:
            raise ValueError("matrice de transition non carrée : chaque ligne doit avoir n entrées")
        row = []
        for x in ligne:
            if isinstance(x, Fraction):
                xf = float(x)
            elif _est_reel(x):
                xf = float(x)
            else:
                raise ValueError(f"entrée de transition invalide (bool/str/NaN/inf refusé) : {x!r}")
            if xf < -_TOL or xf > 1.0 + _TOL:
                raise ValueError(f"probabilité de transition hors [0,1] : {xf}")
            row.append(max(0.0, min(1.0, xf)))
        s = math.fsum(row)
        if abs(s - 1.0) > 1e-6:
            raise ValueError(f"ligne non stochastique : somme = {s} ≠ 1 (matrice non stochastique)")
        rows.append(row)
    return rows, n


def _valide_distribution_donnee(pi, n):
    """Distribution FOURNIE de taille n (probabilités ≥ 0 sommant à 1). Renvoie la liste de floats."""
    if not isinstance(pi, (list, tuple)) or len(pi) != n:
        raise ValueError("distribution stationnaire de taille incompatible avec la matrice")
    xs = []
    for x in pi:
        if isinstance(x, Fraction):
            xf = float(x)
        elif _est_reel(x):
            xf = float(x)
        else:
            raise ValueError(f"probabilité invalide (bool/str/NaN/inf refusé) : {x!r}")
        if xf < -_TOL:
            raise ValueError(f"probabilité négative : {xf}")
        xs.append(max(0.0, xf))
    s = math.fsum(xs)
    if abs(s - 1.0) > 1e-6:
        raise ValueError(f"la distribution stationnaire ne somme pas à 1 (somme = {s})")
    return xs


# ── (a) ENTROPIE EMPIRIQUE (PLUG-IN) + FIABILITÉ ───────────────────────────────────────────────────────────────
def entropie_empirique(sequence):
    """Entropie plug-in de la source, ESTIMÉE par les fréquences observées.

    Renvoie le COUPLE (H_estimée_bits, N) où N = nombre d'observations. Une entropie sans son N ne
    signifie rien : c'est une ESTIMATION, jamais l'entropie de la source (cf. correction_miller_madow)."""
    symboles = _valide_sequence(sequence)
    comptes = _comptes(symboles)
    n = len(symboles)
    dist = [comptes[s] / n for s in comptes]        # fréquences observées (somment à 1 par construction)
    return (_ic.entropie(dist), n)


def fiable(sequence, alphabet) -> bool:
    """True ssi la séquence porte assez d'observations pour une estimation raisonnable : N ≥ 5·|alphabet|.

    Règle de pouce classique (≈5 observations par symbole possible) — indicative, on le DIT. Alphabet vide
    -> ValueError. Ne lève PAS pour une séquence trop courte : renvoie simplement False."""
    symboles = _valide_sequence(sequence)
    if not isinstance(alphabet, (list, tuple, set, frozenset)) or len(alphabet) == 0:
        raise ValueError("alphabet invalide : une collection NON VIDE de symboles possibles est requise")
    distincts = set()
    for a in alphabet:
        try:
            distincts.add(a)
        except TypeError:
            raise ValueError(f"symbole d'alphabet non hashable : {a!r}")
    return len(symboles) >= 5 * len(distincts)


# ── (b) CORRECTION DE BIAIS DE MILLER–MADOW ────────────────────────────────────────────────────────────────────
def correction_miller_madow(sequence) -> float:
    """Estimation d'entropie CORRIGÉE du biais : Ĥ_MM = Ĥ_plugin + (K−1)/(2N).

    K = nombre de symboles OBSERVÉS (distincts), N = nombre d'observations. Le plug-in sous-estime H
    (biais vers le bas) ; cette correction le remonte. RESTE APPROCHÉE : ce n'est toujours PAS l'entropie
    exacte de la source, seulement une estimation moins biaisée. Marquée approchée par ce docstring.

    UNITÉS (FAUX=0) : le terme de Miller–Madow (K−1)/(2N) est dérivé en NATS (entropie en logₑ). Ce module
    exprime toute entropie en BITS (log₂, via information_calcul) ; la correction doit donc être convertie
    en bits en la divisant par ln 2, soit (K−1)/(2N·ln2). Omettre ce facteur rendrait un nombre qui n'est
    PAS l'estimateur de Miller–Madow."""
    symboles = _valide_sequence(sequence)
    comptes = _comptes(symboles)
    n = len(symboles)
    k = len(comptes)
    h_plugin, _ = entropie_empirique(symboles)
    correction = (k - 1) / (2.0 * n * math.log(2.0))       # nats -> bits (h_plugin est en bits, log2)
    return round(h_plugin + correction, 12)


# ── (c) SOURCE DE MARKOV : DISTRIBUTION STATIONNAIRE ───────────────────────────────────────────────────────────
def _stationnaire_exacte(matrice, n):
    """Résout πP = π, Σπ = 1 EXACTEMENT sur ℚ si toutes les lignes somment exactement à 1 (sinon None).

    Système (Pᵀ − I)π = 0 augmenté de la contrainte de normalisation ; résolu par algebre_lineaire."""
    try:
        rows_frac = [[_to_fraction(x) for x in ligne] for ligne in matrice]
    except ValueError:
        return None
    for ligne in rows_frac:
        if sum(ligne, Fraction(0)) != 1:
            return None                                   # pas exactement normalisée -> voie itérée
    # équation j : Σ_i π_i·P[i][j] − π_j = 0 ; coefficient de π_i = P[i][j] − δ_ij
    A = [[rows_frac[i][j] - (Fraction(1) if i == j else Fraction(0)) for i in range(n)] for j in range(n)]
    A.append([Fraction(1)] * n)                           # ligne de normalisation Σ π_i = 1
    b = [Fraction(0)] * n + [Fraction(1)]
    res = _al.resout_systeme(A, b)
    if res.get("type") != "unique":
        return None
    pi = res["solution"]
    if any(p < 0 for p in pi):
        return None                                       # stationnaire non-positive (chaîne réductible) -> abstention
    # VÉRIFICATION EXACTE πP = π (FAUX=0)
    for j in range(n):
        if sum((pi[i] * rows_frac[i][j] for i in range(n)), Fraction(0)) != pi[j]:
            return None
    if sum(pi, Fraction(0)) != 1:
        return None
    return pi


def _stationnaire_iteree(rows, n):
    """Puissance itérée π ← πP jusqu'à stabilité (critère d'arrêt). Résultat APPROCHÉ (floats).

    Non convergence (chaîne périodique/réductible) -> ValueError : on ABSTIENT plutôt que rendre un faux."""
    pi = [1.0 / n] * n
    for _ in range(_MAX_ITERS):
        nxt = [0.0] * n
        for i in range(n):
            pii = pi[i]
            ri = rows[i]
            for j in range(n):
                nxt[j] += pii * ri[j]
        s = math.fsum(nxt)
        if s <= 0.0:
            raise ValueError("distribution stationnaire non déterminable (masse nulle) — abstention")
        nxt = [x / s for x in nxt]
        diff = max(abs(nxt[k] - pi[k]) for k in range(n))
        pi = nxt
        if diff < 1e-14:
            return pi
    raise ValueError("distribution stationnaire non convergente (chaîne périodique/réductible) — abstention")


def distribution_stationnaire(matrice):
    """Distribution stationnaire π (πP = π, Σπ = 1) de la source de Markov de matrice de transition P.

    EXACTE sur ℚ (liste de Fraction) lorsque les lignes somment exactement à 1 ; sinon PUISSANCE ITÉRÉE
    (liste de floats, APPROCHÉE). Matrice non stochastique -> ValueError ; stationnaire non déterminable
    (chaîne réductible/périodique sans limite) -> ValueError."""
    rows, n = _valide_transition(matrice)
    exacte = _stationnaire_exacte(matrice, n)
    if exacte is not None:
        return exacte
    return _stationnaire_iteree(rows, n)


# ── (c/e) TAUX D'ENTROPIE D'UNE SOURCE DE MARKOV + INVARIANT ───────────────────────────────────────────────────
def entropie_conditionnelle_markov(matrice_transition, distribution_stationnaire) -> float:
    """Taux d'entropie d'une source de Markov d'ordre 1 : h = Σ_i π_i · H(P(·|i)) (bits/symbole).

    STATIONNARITÉ (e) : la formule n'est un TAUX D'ENTROPIE que si π est LA distribution stationnaire.
    On VÉRIFIE donc πP = π (à 1e-9 près) et on ABSTIENT (ValueError) sinon — un π non stationnaire donnerait
    un nombre dénué de sens. INVARIANT secondaire : h ≤ H(π) (RuntimeError si violé, redondant en pratique).
    Matrice non stochastique / π invalide / π non stationnaire -> ValueError."""
    rows, n = _valide_transition(matrice_transition)
    pi = _valide_distribution_donnee(distribution_stationnaire, n)
    # π DOIT satisfaire πP = π : (πP)[j] = Σ_i π_i·P[i][j]. Sinon la formule ne mesure pas le taux de la source.
    for j in range(n):
        colonne = math.fsum(pi[i] * rows[i][j] for i in range(n))
        if abs(colonne - pi[j]) > 1e-9:
            raise ValueError(
                f"distribution fournie NON stationnaire : (πP)[{j}]={colonne} ≠ π[{j}]={pi[j]} — "
                "le taux d'entropie n'est défini que pour la distribution stationnaire (πP=π) ; abstention")
    taux = 0.0
    for i in range(n):
        taux += pi[i] * _ic.entropie(rows[i])             # H de la i-ème ligne (distribution conditionnelle)
    h_stationnaire = _ic.entropie(pi)
    if taux > h_stationnaire + 1e-9:
        raise RuntimeError(
            f"invariant violé : taux d'entropie {taux} > entropie stationnaire {h_stationnaire} "
            "(le conditionnement ne peut PAS augmenter l'incertitude)")
    return round(taux, 12)


# ── (d) TAUX D'ENTROPIE EMPIRIQUE (conditionnel, ordre donné) ──────────────────────────────────────────────────
def taux_entropie_empirique(sequence, ordre: int = 1) -> float:
    """Entropie conditionnelle empirique H(X_t | X_{t-ordre .. t-1}) estimée sur les contextes observés.

    Pour ordre = 1 : entropie conditionnelle d'ordre 1 (source de Markov empirique). ESTIMATION (biaisée
    vers le bas comme tout plug-in). ordre non entier ≥ 1 ou séquence trop courte -> ValueError."""
    symboles = _valide_sequence(sequence)
    if isinstance(ordre, bool) or not isinstance(ordre, int) or ordre < 1:
        raise ValueError("ordre invalide : un entier ≥ 1 est requis")
    if len(symboles) <= ordre:
        raise ValueError(f"séquence trop courte : au moins {ordre + 1} symboles requis pour l'ordre {ordre}")
    # comptes des transitions (contexte -> symbole suivant)
    contextes = {}                                        # contexte -> {suivant: compte}
    total = 0
    for i in range(ordre, len(symboles)):
        ctx = tuple(symboles[i - ordre:i])
        nxt = symboles[i]
        d = contextes.setdefault(ctx, {})
        d[nxt] = d.get(nxt, 0) + 1
        total += 1
    taux = 0.0
    for ctx, d in contextes.items():
        cnt_ctx = sum(d.values())
        cond = [c / cnt_ctx for c in d.values()]          # distribution conditionnelle du contexte
        taux += (cnt_ctx / total) * _ic.entropie(cond)
    return round(taux, 12)


if __name__ == "__main__":
    print("H empirique(a,b,a,b) :", entropie_empirique(["a", "b", "a", "b"]))
    print("Miller-Madow(a,b,a,b) :", correction_miller_madow(["a", "b", "a", "b"]))
    P = [[0.9, 0.1], [0.1, 0.9]]
    pi = distribution_stationnaire(P)
    print("π stationnaire :", pi)
    print("taux d'entropie Markov :", entropie_conditionnelle_markov(P, pi))
