"""
ANNEAUX ET CORPS FINIS — vérification EXACTE des axiomes sur deux tables de Cayley, FAUX=0.

Même posture que `geometries_non_euclidiennes` / `galois` (la définition mathématique juge, jamais un faux) :
  • Le MÉCANISME est la DÉFINITION CLASSIQUE (algèbre générale), pas une corrélation :
      – ANNEAU (E, +, ·) : (E, +) est un groupe ABÉLIEN (clôture, associativité, neutre 0, inverses,
        commutativité) ; (E, ·) est clos et associatif ; la DISTRIBUTIVITÉ vaut DES DEUX CÔTÉS :
            a·(b+c) = a·b + a·c   et   (b+c)·a = b·a + c·a.
      – ANNEAU UNITAIRE : anneau + neutre multiplicatif 1.
      – ANNEAU COMMUTATIF : anneau + multiplication commutative.
      – CORPS : anneau commutatif unitaire avec 0 ≠ 1 (le « corps » trivial à 1 élément est EXCLU)
        et tout élément NON NUL inversible pour la multiplication.
      – Théorème d'ancrage externe : ℤ/nℤ est un corps SI ET SEULEMENT SI n est premier.
  • Tout est EXACT (comparaisons d'entiers sur ensembles finis) — aucun flottant, aucune approximation.
  • SECOND CHEMIN DE CODE : le groupe additif est re-vérifié par `groupes.est_groupe` (module distinct,
    NON MODIFIÉ ici) ; toute divergence entre les deux chemins -> ValueError (abstention, jamais un verdict).

GARANTIES (vérifiées en adverse par `valide_anneaux_corps.py`) :
  - `elements` vide, non liste/tuple, avec doublons, ou contenant autre chose que int/str (bool REFUSÉ,
    car True == 1 casserait la distinction des éléments) -> ValueError ;
  - table non carrée, de mauvaise taille, ou contenant une entrée HORS de l'ensemble -> ValueError
    (clôture violée = table mal formée = abstention structurelle, pas un False muet) ;
  - `diagnostic` nomme EXPLICITEMENT chaque axiome violé (jamais un False sans explication) ;
  - niveau de diagnostic inconnu -> ValueError ;
  - déterministe ; fonctions pures ; conservateur (abstention tolérée, faux POSITIF interdit).

Le module n'importe que `groupes` (réutilisation imposée, second chemin) — stdlib uniquement en amont.
"""
from __future__ import annotations

import groupes

SOURCE = ("définitions classiques d'anneau et de corps (algèbre générale, cf. Bourbaki, Algèbre, ch. I) ; "
          "ancre : ℤ/nℤ est un corps ⇔ n premier")

_NIVEAUX = ("anneau", "anneau_unitaire", "anneau_commutatif", "corps")

# Axiomes du groupe additif re-vérifiables par le second chemin (groupes.est_groupe ne teste PAS
# la commutativité : elle est donc hors de cette liste).
_AXIOMES_GROUPE_ADD = ("associativité (addition)", "neutre (addition)", "inverses (addition)")


# ── VALIDATION (abstention structurelle) ─────────────────────────────────────────────────────────────────────
def _exige_element(x):
    """Un élément est un int ou une str ; bool REFUSÉ (True == 1 rendrait deux éléments indistincts)."""
    if isinstance(x, bool) or not isinstance(x, (int, str)):
        raise ValueError(f"élément invalide {x!r} : int ou str requis (bool/float/None refusés)")
    return x


def _matrice_indices(nom: str, table, idx: dict, n: int):
    """Convertit une table de Cayley (valeurs = éléments) en matrice n×n d'indices 0..n-1.

    Non carrée, mauvaise taille, entrée hors ensemble (clôture) -> ValueError."""
    if not isinstance(table, (list, tuple)) or len(table) != n:
        raise ValueError(f"{nom} : matrice carrée {n}x{n} requise (une ligne par élément)")
    mat = []
    for ligne in table:
        if not isinstance(ligne, (list, tuple)) or len(ligne) != n:
            raise ValueError(f"{nom} : chaque ligne doit être une séquence d'exactement {n} entrées")
        rangee = []
        for x in ligne:
            if isinstance(x, bool) or not isinstance(x, (int, str)) or x not in idx:
                raise ValueError(f"{nom} : entrée {x!r} hors de l'ensemble des éléments "
                                 "(clôture non garantie -> abstention)")
            rangee.append(idx[x])
        mat.append(rangee)
    return mat


def _exige_structure(elements, table_add, table_mul):
    """Valide (elements, table_add, table_mul) et renvoie (elts, A, M) en indices. Malformé -> ValueError."""
    if not isinstance(elements, (list, tuple)) or len(elements) == 0:
        raise ValueError("elements : liste/tuple NON VIDE d'éléments requis")
    elts = tuple(_exige_element(x) for x in elements)
    idx = {}
    for i, x in enumerate(elts):
        if x in idx:
            raise ValueError(f"elements : doublon {x!r} — les éléments doivent être deux à deux distincts")
        idx[x] = i
    n = len(elts)
    A = _matrice_indices("table_add", table_add, idx, n)
    M = _matrice_indices("table_mul", table_mul, idx, n)
    return elts, A, M


def table_en_indices(elements, table):
    """Convertit UNE table de Cayley en matrice d'indices 0..n-1 (format attendu par `groupes.est_groupe`).

    Sert de pont vers le second chemin de vérification. Table mal formée -> ValueError."""
    _, A, _ = _exige_structure(elements, table, table)
    return A


# ── AXIOMES (calcul exact sur matrices d'indices) ────────────────────────────────────────────────────────────
def _neutre(mat, n: int):
    """Indice du neutre bilatère de la loi `mat`, ou None s'il n'existe pas."""
    for e in range(n):
        if all(mat[e][x] == x and mat[x][e] == x for x in range(n)):
            return e
    return None


def _est_associative(mat, n: int) -> bool:
    return all(mat[mat[a][b]][c] == mat[a][mat[b][c]]
               for a in range(n) for b in range(n) for c in range(n))


def _est_commutative(mat, n: int) -> bool:
    return all(mat[a][b] == mat[b][a] for a in range(n) for b in range(n))


def _diagnostic_indices(A, M, n: int, niveau: str):
    """Liste EXPLICITE des axiomes violés au niveau demandé (jamais un False muet).

    La CLÔTURE des deux lois est garantie en amont par la validation (entrée hors ensemble -> ValueError)."""
    v = []
    # (E, +) groupe abélien
    if not _est_associative(A, n):
        v.append("associativité (addition)")
    zero = _neutre(A, n)
    if zero is None:
        v.append("neutre (addition)")
    elif any(not any(A[a][b] == zero and A[b][a] == zero for b in range(n)) for a in range(n)):
        v.append("inverses (addition)")
    if not _est_commutative(A, n):
        v.append("commutativité (addition)")
    # (E, ·) clos (garanti par validation) et associatif
    if not _est_associative(M, n):
        v.append("associativité (multiplication)")
    # distributivité des deux côtés
    if any(M[a][A[b][c]] != A[M[a][b]][M[a][c]]
           for a in range(n) for b in range(n) for c in range(n)):
        v.append("distributivité (gauche)")
    if any(M[A[b][c]][a] != A[M[b][a]][M[c][a]]
           for a in range(n) for b in range(n) for c in range(n)):
        v.append("distributivité (droite)")
    # niveaux supérieurs
    un = _neutre(M, n)
    if niveau in ("anneau_unitaire", "corps") and un is None:
        v.append("neutre (multiplication)")
    if niveau in ("anneau_commutatif", "corps") and not _est_commutative(M, n):
        v.append("commutativité (multiplication)")
    if niveau == "corps" and zero is not None and un is not None:
        if zero == un:
            v.append("corps trivial (0 = 1) exclu")
        elif any(a != zero and not any(M[a][b] == un and M[b][a] == un for b in range(n))
                 for a in range(n)):
            v.append("inversibilité des non nuls (multiplication)")
    return v


def _verdict(elements, table_add, table_mul, niveau: str):
    """Valide, diagnostique, et CONFRONTE le groupe additif au second chemin `groupes.est_groupe`."""
    if niveau not in _NIVEAUX:
        raise ValueError(f"niveau inconnu {niveau!r} : un de {_NIVEAUX} requis")
    elts, A, M = _exige_structure(elements, table_add, table_mul)
    v = _diagnostic_indices(A, M, len(elts), niveau)
    # SECOND CHEMIN : groupes.est_groupe (associativité + neutre + inverses, PAS la commutativité).
    mien = not any(axiome in v for axiome in _AXIOMES_GROUPE_ADD)
    if groupes.est_groupe(A) != mien:
        raise ValueError("incohérence interne : les deux chemins de vérification du groupe additif "
                         "divergent (abstention plutôt qu'un verdict douteux)")
    return v


# ── API PUBLIQUE ─────────────────────────────────────────────────────────────────────────────────────────────
def diagnostic(elements, table_add, table_mul, niveau: str = "corps"):
    """Liste des axiomes violés (chaînes explicites), au niveau demandé parmi
    'anneau' | 'anneau_unitaire' | 'anneau_commutatif' | 'corps'. Liste vide = tous les axiomes tiennent."""
    return _verdict(elements, table_add, table_mul, niveau)


def est_anneau(elements, table_add, table_mul) -> bool:
    """Vrai ssi (E, +, ·) est un ANNEAU : (E,+) groupe abélien, (E,·) clos associatif, distributivité bilatère."""
    return not _verdict(elements, table_add, table_mul, "anneau")


def est_anneau_unitaire(elements, table_add, table_mul) -> bool:
    """Vrai ssi anneau POSSÉDANT un neutre multiplicatif (unité)."""
    return not _verdict(elements, table_add, table_mul, "anneau_unitaire")


def est_anneau_commutatif(elements, table_add, table_mul) -> bool:
    """Vrai ssi anneau à multiplication COMMUTATIVE."""
    return not _verdict(elements, table_add, table_mul, "anneau_commutatif")


def est_corps(elements, table_add, table_mul) -> bool:
    """Vrai ssi CORPS : anneau commutatif unitaire, 0 ≠ 1, tout élément non nul inversible pour ·."""
    return not _verdict(elements, table_add, table_mul, "corps")
