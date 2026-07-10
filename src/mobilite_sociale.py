"""
MOBILITÉ SOCIALE — mécanismes EXACTS de la mobilité intergénérationnelle mesurée sur cohorte (B-FAIT).

Même posture FAUX=0 que `geometries_non_euclidiennes` / `galois` (le mécanisme est un théorème, jamais
une devinette) :
  • TABLE DE MOBILITÉ : effectifs[i][j] = nombre d'enfants d'origine i (classe des parents) arrivés en
    classe j. Les classes sont ORDONNÉES de la plus basse (indice 0) à la plus haute (indice n−1).
  • MATRICE LIGNE : probabilités conditionnelles P(destination j | origine i) = effectifs[i][j] / Σ_j.
    Calculées en `fractions.Fraction` -> EXACTES ; chaque ligne somme à 1 (INVARIANT DUR : RuntimeError
    si violé — jamais une distribution qui ne somme pas à 1).
  • TAUX D'IMMOBILITÉ = Σ diagonale / total (proportion restée dans sa classe d'origine) ; mobilité
    ASCENDANTE = Σ au-dessus de la diagonale (j > i) / total ; DESCENDANTE = Σ au-dessous (j < i) / total.
    Identité structurelle : immobilité + ascendante + descendante = 1 (exact, Fraction).
  • ODDS RATIO entre deux classes i et j :
        OR(i,j) = (n_ii · n_jj) / (n_ij · n_ji).
    POINT THÉORIQUE CENTRAL : le taux brut (immobilité, flux) CONFOND la structure (les marges : tailles
    des classes, qui changent avec l'économie) et la fluidité (l'inégalité des chances relatives).
    L'odds ratio, lui, est INVARIANT par multiplication d'une ligne ou d'une colonne par une constante :
    il mesure la fluidité PURE, indépendamment des marges (sociologie quantitative : tables de mobilité
    log-linéaires, Goodman ; Erikson & Goldthorpe). Sous INDÉPENDANCE statistique (mobilité parfaite,
    toutes les lignes proportionnelles), OR = 1 EXACTEMENT.
  • ÉLASTICITÉ INTERGÉNÉRATIONNELLE DU REVENU (IGE, Solon 1992) : coefficient β de la régression par
    moindres carrés ordinaires de log(y_enfant) sur log(y_parent) :
        β = Σ (x_k − x̄)(z_k − z̄) / Σ (x_k − x̄)²   avec x = log(revenu parent), z = log(revenu enfant).
    β = 0 -> mobilité parfaite (revenu de l'enfant indépendant du parent) ; β = 1 -> reproduction totale.
    Le logarithme impose le flottant : le résultat est ARRONDI à 10 chiffres significatifs et il est
    APPROCHÉ (précision honnête), contrairement aux quantités de table qui sont des Fractions EXACTES.
  • CORRÉLATION intergénérationnelle des log-revenus (Pearson sur les logs) : même posture (flottant
    approché à 10 chiffres significatifs).

GARANTIES (vérifiées en adverse par `valide_mobilite_sociale.py`) :
  - matrice non carrée (ou incohérente avec la liste des classes) -> ValueError ;
  - effectif négatif, non entier, bool, NaN/inf/str -> ValueError ;
  - ligne entièrement nulle -> ValueError (AUCUNE observation pour cette origine : on s'abstient,
    on n'invente pas une distribution) ;
  - odds_ratio : indices hors bornes, i == j, ou cellule croisée nulle (n_ij·n_ji = 0 : OR infini ou
    indéfini) -> ValueError ;
  - élasticité/corrélation : listes de tailles différentes, moins de 2 observations, revenu ≤ 0
    (log indéfini), bool/str/NaN/inf -> ValueError ; variance nulle du régresseur -> ValueError
    (pente indéfinie) ; corrélation : l'une OU l'autre variance nulle -> ValueError ;
  - déterministe ; conservateur (faux négatif/abstention toléré, faux POSITIF interdit).

Toutes les fonctions sont PURES et déterministes ; stdlib uniquement (`math`, `fractions`).
"""
from __future__ import annotations

import math
from fractions import Fraction

SOURCE = ("tables de mobilité et odds ratios (Goodman, modèles log-linéaires ; Erikson & Goldthorpe, "
          "The Constant Flux, 1992) + élasticité intergénérationnelle du revenu β par MCO log-log "
          "(Solon, American Economic Review, 1992)")

_CHIFFRES_SIGNIFICATIFS = 10


def _sig(x: float, n: int = _CHIFFRES_SIGNIFICATIFS) -> float:
    """Arrondit à n chiffres significatifs (précision honnête, indépendante de la magnitude)."""
    if x == 0:
        return 0.0
    return float(f"{x:.{n}g}")


def _est_reel(x) -> bool:
    """True ssi x est un réel fini (les bool sont REFUSÉS : True n'est pas une mesure)."""
    return isinstance(x, (int, float)) and not isinstance(x, bool) and math.isfinite(x)


def _exige_effectif(x) -> int:
    """Effectif de table : un ENTIER ≥ 0 (compte d'individus). bool/float/str/négatif -> ValueError."""
    if not isinstance(x, int) or isinstance(x, bool):
        raise ValueError(f"effectif invalide : un entier ≥ 0 est requis (compte d'individus), reçu {x!r}")
    if x < 0:
        raise ValueError(f"effectif négatif interdit : {x} (un compte d'individus est ≥ 0)")
    return x


def _exige_revenu(x) -> float:
    """Revenu : réel fini STRICTEMENT positif (le log l'exige). Sinon ValueError."""
    if not _est_reel(x) or x <= 0:
        raise ValueError(f"revenu invalide : un réel fini strictement positif est requis (log), reçu {x!r}")
    return float(x)


def _exige_indice(i, n: int) -> int:
    if not isinstance(i, int) or isinstance(i, bool):
        raise ValueError(f"indice de classe invalide : un entier est requis, reçu {i!r}")
    if not (0 <= i < n):
        raise ValueError(f"indice de classe hors bornes : {i} (attendu dans [0, {n - 1}])")
    return i


# ── TABLE DE MOBILITÉ ────────────────────────────────────────────────────────────────────────────────────────────
class MatriceTransition:
    """Table de mobilité intergénérationnelle : effectifs[i][j] = enfants d'origine i arrivés en classe j.

    `classes` : séquence d'au moins 2 étiquettes str DISTINCTES, ordonnées de la plus basse à la plus haute.
    `effectifs` : matrice CARRÉE n×n d'entiers ≥ 0 ; aucune ligne entièrement nulle (sinon ValueError :
    aucune observation pour cette origine, on s'abstient). Objet IMMUABLE (tuples), méthodes pures."""

    def __init__(self, classes, effectifs):
        if not isinstance(classes, (list, tuple)) or len(classes) < 2:
            raise ValueError("classes invalide : au moins 2 étiquettes (liste/tuple) sont requises")
        for c in classes:
            if not isinstance(c, str) or not c:
                raise ValueError(f"étiquette de classe invalide : une str non vide est requise, reçu {c!r}")
        if len(set(classes)) != len(classes):
            raise ValueError("étiquettes de classes dupliquées : elles doivent être distinctes")
        n = len(classes)
        if not isinstance(effectifs, (list, tuple)) or len(effectifs) != n:
            raise ValueError(f"matrice non carrée : {n} lignes attendues (une par classe d'origine)")
        lignes = []
        for i, ligne in enumerate(effectifs):
            if not isinstance(ligne, (list, tuple)) or len(ligne) != n:
                raise ValueError(f"matrice non carrée : la ligne {i} doit avoir exactement {n} colonnes")
            ligne_v = tuple(_exige_effectif(x) for x in ligne)
            if sum(ligne_v) == 0:
                raise ValueError(f"ligne {i} ({classes[i]!r}) entièrement nulle : aucune observation "
                                 "pour cette origine -> abstention")
            lignes.append(ligne_v)
        self.classes = tuple(classes)
        self.effectifs = tuple(lignes)
        self.n = n
        self._total = sum(sum(l) for l in lignes)

    # — probabilités conditionnelles —
    def matrice_ligne(self):
        """P(destination j | origine i) = effectifs[i][j] / Σ_j effectifs[i][j], en Fraction EXACTES.

        INVARIANT DUR : chaque ligne somme à 1 exactement, sinon RuntimeError (jamais une distribution
        qui ne somme pas à 1)."""
        probas = []
        for ligne in self.effectifs:
            s = sum(ligne)
            p = tuple(Fraction(x, s) for x in ligne)
            if sum(p) != 1:
                raise RuntimeError("invariant violé : une ligne de probabilités ne somme pas à 1")
            probas.append(p)
        return tuple(probas)

    # — taux bruts (ATTENTION : confondent structure et fluidité — voir odds_ratio) —
    def taux_immobilite(self) -> Fraction:
        """Σ diagonale / total : proportion d'enfants restés dans leur classe d'origine (Fraction exacte)."""
        return Fraction(sum(self.effectifs[i][i] for i in range(self.n)), self._total)

    def mobilite_ascendante(self) -> Fraction:
        """Proportion d'enfants montés (destination j > origine i, au-dessus de la diagonale) — exacte."""
        return Fraction(sum(self.effectifs[i][j] for i in range(self.n)
                            for j in range(self.n) if j > i), self._total)

    def mobilite_descendante(self) -> Fraction:
        """Proportion d'enfants descendus (destination j < origine i, au-dessous de la diagonale) — exacte."""
        return Fraction(sum(self.effectifs[i][j] for i in range(self.n)
                            for j in range(self.n) if j < i), self._total)

    # — fluidité pure —
    def odds_ratio(self, i: int, j: int) -> Fraction:
        """OR(i,j) = (n_ii·n_jj) / (n_ij·n_ji) : rapport des chances relatives entre les classes i et j.

        Mesure de FLUIDITÉ indépendante des marges : invariante par multiplication d'une ligne ou d'une
        colonne par une constante (le taux brut, lui, confond structure et fluidité). Indépendance
        statistique -> OR = 1 exactement. i == j, indice hors bornes, ou n_ij·n_ji = 0 (OR infini/indéfini)
        -> ValueError. Résultat en Fraction EXACTE."""
        i = _exige_indice(i, self.n)
        j = _exige_indice(j, self.n)
        if i == j:
            raise ValueError("odds_ratio exige deux classes DISTINCTES (i != j)")
        n_ii, n_jj = self.effectifs[i][i], self.effectifs[j][j]
        n_ij, n_ji = self.effectifs[i][j], self.effectifs[j][i]
        if n_ij == 0 or n_ji == 0:
            raise ValueError("odds_ratio indéfini : une cellule croisée est nulle (OR infini ou 0/0) "
                             "-> abstention")
        return Fraction(n_ii * n_jj, n_ij * n_ji)


# ── ÉLASTICITÉ INTERGÉNÉRATIONNELLE (IGE) ────────────────────────────────────────────────────────────────────────
def _logs_apparies(revenus_parents, revenus_enfants):
    """Valide les deux listes de revenus et renvoie (logs parents, logs enfants)."""
    for nom, seq in (("revenus_parents", revenus_parents), ("revenus_enfants", revenus_enfants)):
        if not isinstance(seq, (list, tuple)):
            raise ValueError(f"{nom} invalide : une liste/tuple de revenus est requise")
    if len(revenus_parents) != len(revenus_enfants):
        raise ValueError("listes de tailles différentes : chaque enfant doit être apparié à son parent")
    if len(revenus_parents) < 2:
        raise ValueError("au moins 2 paires parent/enfant sont requises pour une régression")
    xs = [math.log(_exige_revenu(v)) for v in revenus_parents]
    zs = [math.log(_exige_revenu(v)) for v in revenus_enfants]
    return xs, zs


def elasticite_intergenerationnelle(revenus_parents, revenus_enfants) -> float:
    """β (IGE) : pente MCO de log(y_enfant) sur log(y_parent) — β = Σ(x−x̄)(z−z̄) / Σ(x−x̄)².

    β = 0 -> mobilité parfaite ; β = 1 -> reproduction totale du revenu. Variance nulle des log-revenus
    parents -> ValueError (pente indéfinie). Résultat flottant APPROCHÉ, arrondi à 10 chiffres significatifs."""
    xs, zs = _logs_apparies(revenus_parents, revenus_enfants)
    m = len(xs)
    xbar = sum(xs) / m
    zbar = sum(zs) / m
    sxx = sum((x - xbar) ** 2 for x in xs)
    if sxx == 0.0:
        raise ValueError("variance nulle des log-revenus parents : pente de régression indéfinie -> abstention")
    sxz = sum((x - xbar) * (z - zbar) for x, z in zip(xs, zs))
    return _sig(sxz / sxx)


def correlation_log_revenus(revenus_parents, revenus_enfants) -> float:
    """Corrélation de Pearson entre log(y_parent) et log(y_enfant) — r = Sxz / √(Sxx·Szz), dans [−1, 1].

    Variance nulle de L'UNE OU L'AUTRE série de logs -> ValueError (corrélation indéfinie).
    Résultat flottant APPROCHÉ, arrondi à 10 chiffres significatifs."""
    xs, zs = _logs_apparies(revenus_parents, revenus_enfants)
    m = len(xs)
    xbar = sum(xs) / m
    zbar = sum(zs) / m
    sxx = sum((x - xbar) ** 2 for x in xs)
    szz = sum((z - zbar) ** 2 for z in zs)
    if sxx == 0.0 or szz == 0.0:
        raise ValueError("variance nulle d'une série de log-revenus : corrélation indéfinie -> abstention")
    sxz = sum((x - xbar) * (z - zbar) for x, z in zip(xs, zs))
    r = sxz / math.sqrt(sxx * szz)
    # garde numérique : |r| ≤ 1 par Cauchy-Schwarz ; on borne les dépassements d'arrondi flottant
    if r > 1.0:
        r = 1.0
    elif r < -1.0:
        r = -1.0
    return _sig(r)
