"""
ALGÈBRE LINÉAIRE EXACTE — systèmes linéaires (pivot de Gauss), déterminant, rang, inverse (B-NEC, PARTIE I).

Posture FAUX=0 (identique à `valeurs_propres` / `geometries_non_euclidiennes` / `galois`) : le MÉCANISME
est un THÉORÈME EXACT en arithmétique rationnelle (`fractions.Fraction`), jamais un flottant déguisé en
vérité, jamais une solution « plausible ». Au moindre doute -> ValueError (abstention structurelle).

Ce module NE DUPLIQUE PAS les primitives déjà exactes de `valeurs_propres` : il les IMPORTE et les
RÉUTILISE (`determinant`, `_echelonne` Gauss-Jordan sur Fraction, `_exige_matrice`, `_exige_scalaire`),
et n'ajoute que ce qui manque à la PARTIE I :

  • `resout_systeme(A, b)` — pivot de Gauss EXACT. Le THÉORÈME DE ROUCHÉ–CAPELLI décide :
        rang(A) < rang([A|b])            -> aucune solution   ('aucune') ;
        rang(A) == rang([A|b]) == m      -> solution UNIQUE    ('unique') ;
        rang(A) == rang([A|b]) < m       -> infinité de solutions ('infinite'),
                                            décrites EXACTEMENT par une solution particulière + une base
                                            du noyau de A (l'espace affine des solutions).
    Après une solution 'unique', on RE-VÉRIFIE A·x == b EXACTEMENT (sinon RuntimeError) : jamais un faux.

  • `inverse(M)` — inverse EXACTE par Gauss-Jordan sur l'augmentée [M | I]. Matrice singulière (det = 0)
    -> ValueError explicite. Après calcul, on RE-VÉRIFIE M·M⁻¹ == I EXACTEMENT (sinon RuntimeError).

  • `determinant`, `rang`, `trace`, `transposee`, `produit`, `est_inversible` — délégués/rendus.

GARANTIES (vérifiées en adverse par `valide_algebre_lineaire.py`) :
  - entrée flottante (0.1 n'est pas exact) / bool / str / complexe / NaN / inf   -> ValueError (int/Fraction) ;
  - matrice vide / lignes de longueurs inégales                                   -> ValueError ;
  - dimensions incohérentes (produit, système A/b, trace/det/inverse non carrés)  -> ValueError ;
  - inverse d'une matrice singulière                                              -> ValueError ;
  - vérifications internes A·x==b et M·M⁻¹==I EXACTES sinon RuntimeError (jamais un faux positif) ;
  - déterministe ; conservateur (abstention/faux négatif toléré, faux POSITIF interdit).

Le module n'importe que la stdlib (`fractions`) et les primitives EXACTES de `valeurs_propres`.
"""
from __future__ import annotations

from fractions import Fraction

from valeurs_propres import (
    _echelonne,
    _exige_matrice,
    _exige_scalaire,
    _N_MAX,
    determinant as _determinant_carre,
)

SOURCE = ("pivot de Gauss / Gauss-Jordan exact sur ℚ · théorème de Rouché–Capelli (existence/unicité) · "
          "inverse par [M|I] · primitives réutilisées de valeurs_propres.py")


# ── VALIDATION DES ENTRÉES ─────────────────────────────────────────────────────────────────────────────────────
def _exige_matrice_rect(M):
    """Matrice RECTANGULAIRE n×m à entrées rationnelles exactes. Renvoie (lignes, n, m).

    Refuse : non-séquence, vide, ligne vide, lignes de longueurs inégales, entrée flottante/bool/str."""
    if not isinstance(M, (list, tuple)) or len(M) == 0:
        raise ValueError("matrice invalide : une séquence non vide de lignes est requise")
    n = len(M)
    if n > _N_MAX:
        raise ValueError("matrice trop grande : n ≤ %d (budget d'exactitude rationnelle honnête)" % _N_MAX)
    m = None
    lignes = []
    for ligne in M:
        if not isinstance(ligne, (list, tuple)) or len(ligne) == 0:
            raise ValueError("matrice invalide : chaque ligne doit être une séquence non vide")
        if m is None:
            m = len(ligne)
            if m > _N_MAX:
                raise ValueError("matrice trop large : m ≤ %d (budget d'exactitude honnête)" % _N_MAX)
        elif len(ligne) != m:
            raise ValueError("matrice invalide : lignes de longueurs inégales (rectangle attendu)")
        lignes.append([_exige_scalaire(x) for x in ligne])
    return lignes, n, m


def _exige_vecteur(b):
    """Vecteur second membre : séquence non vide d'entrées int/Fraction. Renvoie la liste de Fraction."""
    if not isinstance(b, (list, tuple)) or len(b) == 0:
        raise ValueError("second membre invalide : une séquence non vide est requise")
    return [_exige_scalaire(x) for x in b]


# ── OPÉRATIONS DE BASE (rendues/déléguées) ─────────────────────────────────────────────────────────────────────
def determinant(M) -> Fraction:
    """Déterminant EXACT (délégué à valeurs_propres.determinant : Gauss sur Fraction). Non carrée -> ValueError."""
    return _determinant_carre(M)


def trace(M) -> Fraction:
    """Trace EXACTE (somme de la diagonale). Matrice non carrée -> ValueError."""
    A, n = _exige_matrice(M)
    return sum((A[i][i] for i in range(n)), Fraction(0))


def transposee(M):
    """Transposée EXACTE d'une matrice rectangulaire n×m -> m×n."""
    A, n, m = _exige_matrice_rect(M)
    return [[A[i][j] for i in range(n)] for j in range(m)]


def rang(M) -> int:
    """Rang EXACT d'une matrice RECTANGULAIRE (élimination de Gauss-Jordan sur Fraction)."""
    A, n, m = _exige_matrice_rect(M)
    _, r, _, _ = _echelonne(A, n, m)
    return r


def produit(A, B):
    """Produit matriciel EXACT A·B. Dimensions incompatibles (cols(A) ≠ lignes(B)) -> ValueError."""
    a, na, ma = _exige_matrice_rect(A)
    b, nb, mb = _exige_matrice_rect(B)
    if ma != nb:
        raise ValueError("produit impossible : cols(A)=%d ≠ lignes(B)=%d (dimensions incohérentes)" % (ma, nb))
    return [[sum((a[i][k] * b[k][j] for k in range(ma)), Fraction(0)) for j in range(mb)] for i in range(na)]


def est_inversible(M) -> bool:
    """True ssi M est carrée et de déterminant non nul. Non carrée -> ValueError."""
    return _determinant_carre(M) != 0


# ── INVERSE (Gauss-Jordan sur [M | I], EXACTE) ─────────────────────────────────────────────────────────────────
def inverse(M):
    """Inverse EXACTE M⁻¹ par Gauss-Jordan sur l'augmentée [M | I].

    Matrice non carrée -> ValueError ; matrice singulière (det = 0) -> ValueError explicite.
    VÉRIFICATION INTERNE (FAUX=0) : M·M⁻¹ est recalculé et doit égaler I EXACTEMENT, sinon RuntimeError."""
    A, n = _exige_matrice(M)
    if _determinant_carre(M) == 0:
        raise ValueError("déterminant nul : non inversible (matrice singulière)")
    # augmentée [A | I], n × 2n ; comme det ≠ 0, les n pivots tombent dans les n premières colonnes
    aug = [A[i][:] + [Fraction(1) if i == j else Fraction(0) for j in range(n)] for i in range(n)]
    R, r, _, pivots = _echelonne(aug, n, 2 * n)
    if r != n or pivots != list(range(n)):
        raise RuntimeError("inverse : réduction incohérente malgré det ≠ 0 (invariant violé)")
    inv = [R[i][n:2 * n] for i in range(n)]
    # RE-VÉRIFICATION EXACTE : M · M⁻¹ == I
    prod = [[sum((A[i][k] * inv[k][j] for k in range(n)), Fraction(0)) for j in range(n)] for i in range(n)]
    for i in range(n):
        for j in range(n):
            attendu = Fraction(1) if i == j else Fraction(0)
            if prod[i][j] != attendu:
                raise RuntimeError("inverse : M·M⁻¹ ≠ I (invariant violé — jamais rendu au faux)")
    return inv


# ── SYSTÈME LINÉAIRE (pivot de Gauss, Rouché–Capelli, EXACT) ───────────────────────────────────────────────────
def _noyau_rect(A, n, m):
    """Base EXACTE du noyau de A (n×m). Liste de vecteurs de longueur m (à coefficients Fraction)."""
    R, r, _, pivots = _echelonne(A, n, m)
    libres = [c for c in range(m) if c not in pivots]
    base = []
    for c in libres:
        v = [Fraction(0)] * m
        v[c] = Fraction(1)
        for i, pc in enumerate(pivots):
            v[pc] = -R[i][c]
        base.append(v)
    return base


def resout_systeme(A, b) -> dict:
    """Résout A·x = b EXACTEMENT (pivot de Gauss sur Fraction), classifié par ROUCHÉ–CAPELLI.

    A : matrice n×m ; b : vecteur de longueur n. Renvoie un dict :
      'type'  : 'unique' | 'infinite' | 'aucune' ;
      'rang'  : rang(A) (int) ;
      si 'unique'   : 'solution' = [x_1, ..., x_m] (Fractions), RE-VÉRIFIÉ A·x == b ;
      si 'infinite' : 'solution_particuliere' + 'base_noyau' (base du noyau de A) ;
      si 'aucune'   : ni solution ni base.

    Dimensions incohérentes (len(b) ≠ n) -> ValueError ; entrées flottantes/bool -> ValueError."""
    A_f, n, m = _exige_matrice_rect(A)
    b_f = _exige_vecteur(b)
    if len(b_f) != n:
        raise ValueError("dimensions incohérentes : b a %d entrées, A a %d lignes" % (len(b_f), n))

    rA = rang(A_f)
    aug = [A_f[i][:] + [b_f[i]] for i in range(n)]
    rAb = rang(aug)

    if rA < rAb:
        # Rouché–Capelli : rang(A) < rang([A|b]) -> système incompatible
        return {"type": "aucune", "rang": rA}

    # rA == rAb ; réduction de l'augmentée pour lire la solution
    R, r, _, pivots = _echelonne(aug, n, m + 1)
    if r != rA:
        raise RuntimeError("résolution : rang de l'augmentée incohérent (invariant violé)")
    if m in pivots:
        raise RuntimeError("résolution : pivot dans la colonne du second membre malgré compatibilité (invariant)")

    # solution particulière : variables libres à 0, variables pivots = dernière colonne
    x_part = [Fraction(0)] * m
    for i, pc in enumerate(pivots):
        x_part[pc] = R[i][m]

    # VÉRIFICATION EXACTE A·x_part == b
    for i in range(n):
        s = sum((A_f[i][j] * x_part[j] for j in range(m)), Fraction(0))
        if s != b_f[i]:
            raise RuntimeError("résolution : A·x ≠ b (invariant violé — jamais rendu au faux)")

    if rA == m:
        return {"type": "unique", "rang": rA, "solution": x_part}

    base = _noyau_rect(A_f, n, m)
    if len(base) != m - rA:
        raise RuntimeError("résolution : dim(noyau) ≠ m − rang (invariant violé)")
    # VÉRIFICATION EXACTE : chaque vecteur du noyau annule A
    for v in base:
        for i in range(n):
            s = sum((A_f[i][j] * v[j] for j in range(m)), Fraction(0))
            if s != 0:
                raise RuntimeError("résolution : A·noyau ≠ 0 (invariant violé)")
    return {"type": "infinite", "rang": rA, "solution_particuliere": x_part, "base_noyau": base}
