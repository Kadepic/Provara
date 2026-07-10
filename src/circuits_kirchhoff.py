"""
LOIS DE KIRCHHOFF — solveur GÉNÉRAL de circuits résistifs, arithmétique EXACTE (Fraction).

Même posture FAUX=0 que `physique` / `galois` (la réalité/le théorème juge, jamais un faux) :
  • Le MÉCANISME est un THÉORÈME EXACT, pas une corrélation :
      – Loi des NŒUDS (KCL, Kirchhoff 1845) : en tout nœud, Σ courants entrants = Σ courants sortants
        (conservation de la charge).
      – Loi des MAILLES (KVL) : le long de toute maille, Σ des tensions = 0 ; elle est encodée ici par
        l'existence même des POTENTIELS de nœud (analyse nodale) : chaque branche (a, b, R, E) obéit à
        la loi de branche  V(a) − V(b) + E = R·I,  où I est le courant orienté de a vers b et E la fem
        orientée de a vers b (une fem positive tend à faire circuler un courant positif de a vers b).
      – Résolution : système KCL sur les potentiels (Laplacien pondéré par les conductances 1/R),
        nœud de MASSE = le PREMIER nœud ajouté (potentiel fixé à 0), pivot de Gauss EXACT sur Fraction.
        Pour un graphe CONNEXE à résistances strictement positives, ce système est régulier (Laplacien
        réduit défini positif) — l'unicité de la solution est un théorème, pas une espérance.
  • Arithmétique EXACTE : `fractions.Fraction` de bout en bout. Les flottants sont REFUSÉS en entrée
    (ValueError) : aucune valeur approchée ne peut entrer, aucune ne peut sortir.
  • VÉRIFICATION INTERNE OBLIGATOIRE : après résolution, la KCL est RE-VÉRIFIÉE à chaque nœud
    (Σ courants = 0 EXACTEMENT, en Fraction). Si l'invariant échoue -> RuntimeError : le module
    préfère planter que rendre un résultat faux.

API :
    c = Circuit()
    i = c.ajoute_branche(noeud_a, noeud_b, R, E=0)   # -> indice (int) de la branche
    c.resout() -> {'potentiels': {noeud: Fraction}, 'courants': {indice_branche: Fraction}}
    # courants[i] > 0  <=>  le courant circule de noeud_a vers noeud_b dans la branche i.

GARANTIES (vérifiées en adverse par `valide_circuits_kirchhoff.py`) :
  - R ≤ 0 -> ValueError (une branche purement résistive a R strictement positive ; pas de source idéale) ;
  - float (dont NaN/±inf), bool, str, complex pour R ou E -> ValueError (int/Fraction EXIGÉS) ;
  - nœud invalide (bool, float, None, str vide) -> ValueError ; noeud_a == noeud_b -> ValueError ;
  - circuit VIDE -> ValueError ; circuit NON CONNEXE -> ValueError ; système singulier -> ValueError ;
  - invariant KCL violé après résolution -> RuntimeError (jamais un résultat faux) ;
  - déterministe (masse = premier nœud ajouté ; aucune source d'aléa) ;
  - conservateur : le faux négatif (abstention) est toléré, le faux POSITIF est interdit.

Le module n'importe que `fractions` (stdlib). Fonctions/méthodes pures et déterministes.
"""
from __future__ import annotations

from fractions import Fraction

SOURCE = ("lois de Kirchhoff (G. Kirchhoff, 1845) : loi des nœuds (conservation de la charge) + "
          "loi des mailles ; analyse nodale classique (Laplacien de conductance, unicité pour un "
          "graphe connexe à résistances > 0)")


# ── validation d'entrée ──────────────────────────────────────────────────────────────────────────────────────────
def _exige_fraction(x, nom: str) -> Fraction:
    """int ou Fraction -> Fraction EXACTE ; bool/float/str/complex -> ValueError (aucun flottant n'entre)."""
    if isinstance(x, bool):
        raise ValueError(f"{nom} invalide : bool refusé (True n'est pas un nombre)")
    if isinstance(x, int):
        return Fraction(x)
    if isinstance(x, Fraction):
        return x
    raise ValueError(f"{nom} invalide : int ou fractions.Fraction requis (flottant/str refusés), reçu {type(x).__name__}")


def _exige_noeud(x):
    """Étiquette de nœud : str non vide, ou int (bool refusé). Tout autre type -> ValueError."""
    if isinstance(x, bool):
        raise ValueError("nœud invalide : bool refusé comme étiquette de nœud")
    if isinstance(x, int):
        return x
    if isinstance(x, str):
        if x == "":
            raise ValueError("nœud invalide : chaîne vide refusée comme étiquette de nœud")
        return x
    raise ValueError(f"nœud invalide : str non vide ou int requis, reçu {type(x).__name__}")


# ── pivot de Gauss EXACT (Fraction) ──────────────────────────────────────────────────────────────────────────────
def _gauss_exact(A, b):
    """Résout A·x = b par Gauss-Jordan EXACT sur Fraction. Système singulier -> ValueError."""
    n = len(A)
    M = [list(A[i]) + [b[i]] for i in range(n)]
    for col in range(n):
        piv = None
        for r in range(col, n):
            if M[r][col] != 0:
                piv = r
                break
        if piv is None:
            raise ValueError("système singulier : les lois de Kirchhoff ne déterminent pas ce circuit")
        M[col], M[piv] = M[piv], M[col]
        pivot = M[col][col]
        for r in range(n):
            if r != col and M[r][col] != 0:
                f = M[r][col] / pivot
                for c in range(col, n + 1):
                    M[r][c] -= f * M[col][c]
    return [M[i][n] / M[i][i] for i in range(n)]


# ── CIRCUIT ──────────────────────────────────────────────────────────────────────────────────────────────────────
class Circuit:
    """Circuit résistif : branches (noeud_a, noeud_b, R, E), résolu par analyse nodale exacte.

    Masse = PREMIER nœud ajouté (potentiel 0, déterministe). Convention de signe : dans la branche
    (a, b, R, E), le courant renvoyé est orienté de a vers b et vaut I = (V(a) − V(b) + E) / R."""

    def __init__(self) -> None:
        self._branches: list[tuple] = []      # (a, b, R: Fraction, E: Fraction)
        self._noeuds: list = []               # ordre d'apparition (le 1er = masse)
        self._vus: set = set()

    def _enregistre_noeud(self, n) -> None:
        if n not in self._vus:
            self._vus.add(n)
            self._noeuds.append(n)

    def ajoute_branche(self, noeud_a, noeud_b, resistance, fem=0) -> int:
        """Ajoute une branche résistive (+ fem éventuelle orientée a->b). Renvoie son indice.

        resistance : int/Fraction STRICTEMENT positive ; fem : int/Fraction (0 par défaut).
        noeud_a == noeud_b -> ValueError (boucle sur soi-même : mal posé)."""
        a = _exige_noeud(noeud_a)
        b = _exige_noeud(noeud_b)
        if a == b:
            raise ValueError("branche invalide : noeud_a == noeud_b (boucle sur un même nœud)")
        R = _exige_fraction(resistance, "resistance")
        if R <= 0:
            raise ValueError("resistance invalide : strictement positive requise (pas de source idéale R=0)")
        E = _exige_fraction(fem, "fem")
        self._enregistre_noeud(a)
        self._enregistre_noeud(b)
        self._branches.append((a, b, R, E))
        return len(self._branches) - 1

    def _exige_connexe(self) -> None:
        """Le graphe des branches doit être CONNEXE, sinon les potentiels relatifs à la masse
        ne sont pas définis pour la composante isolée -> ValueError (abstention)."""
        adj: dict = {n: [] for n in self._noeuds}
        for (a, b, _R, _E) in self._branches:
            adj[a].append(b)
            adj[b].append(a)
        atteints = {self._noeuds[0]}
        pile = [self._noeuds[0]]
        while pile:
            n = pile.pop()
            for v in adj[n]:
                if v not in atteints:
                    atteints.add(v)
                    pile.append(v)
        if len(atteints) != len(self._noeuds):
            raise ValueError("circuit non connexe : une partie du circuit est isolée de la masse")

    def resout(self) -> dict:
        """Résout le circuit : {'potentiels': {noeud: Fraction}, 'courants': {indice: Fraction}}.

        Circuit vide/non connexe/singulier -> ValueError. Après résolution, la KCL est re-vérifiée
        EXACTEMENT à chaque nœud ; toute violation -> RuntimeError (jamais un résultat faux)."""
        if not self._branches:
            raise ValueError("circuit vide : aucune branche à résoudre")
        self._exige_connexe()

        masse = self._noeuds[0]
        inconnues = self._noeuds[1:]                       # potentiels à déterminer (masse = 0)
        pos = {n: i for i, n in enumerate(inconnues)}
        n = len(inconnues)
        A = [[Fraction(0)] * n for _ in range(n)]
        rhs = [Fraction(0)] * n

        # KCL à chaque nœud non-masse : Σ courants SORTANTS = 0, avec I(a->b) = g·(V(a) − V(b)) + g·E.
        for (a, b, R, E) in self._branches:
            g = Fraction(1) / R
            if a != masse:
                ia = pos[a]
                A[ia][ia] += g
                if b != masse:
                    A[ia][pos[b]] -= g
                rhs[ia] -= g * E
            if b != masse:
                ib = pos[b]
                A[ib][ib] += g
                if a != masse:
                    A[ib][pos[a]] -= g
                rhs[ib] += g * E

        solution = _gauss_exact(A, rhs) if n else []
        potentiels = {masse: Fraction(0)}
        for i, noeud in enumerate(inconnues):
            potentiels[noeud] = solution[i]

        # loi de branche : I = (V(a) − V(b) + E) / R, orienté de a vers b (Fraction exacte).
        courants = {}
        for idx, (a, b, R, E) in enumerate(self._branches):
            courants[idx] = (potentiels[a] - potentiels[b] + E) / R

        # ── VÉRIFICATION INTERNE OBLIGATOIRE (FAUX=0) : KCL exacte à CHAQUE nœud, masse comprise ──
        bilan = {noeud: Fraction(0) for noeud in self._noeuds}
        for idx, (a, b, _R, _E) in enumerate(self._branches):
            bilan[a] -= courants[idx]                      # le courant a->b SORT de a
            bilan[b] += courants[idx]                      # et ENTRE en b
        for noeud, somme in bilan.items():
            if somme != 0:
                raise RuntimeError(
                    f"invariant KCL violé au nœud {noeud!r} (Σ courants = {somme}) : résolution rejetée")

        return {"potentiels": potentiels, "courants": courants}
