"""
ÉLASTICITÉ PRIX — élasticités mesurées sur données (arc / ponctuelle / revenu / croisée).

Même posture FAUX=0 que `physique` / `geometries_non_euclidiennes` (la définition économique exacte juge,
jamais un faux) :
  • Le MÉCANISME est la DÉFINITION exacte de la micro-économie, pas une corrélation :
      – Élasticité d'ARC (méthode du point milieu, formule des arcs) :
            e = ((q2−q1)/((q1+q2)/2)) / ((p2−p1)/((p1+p2)/2)),
        SYMÉTRIQUE par échange des deux points (contrairement à la formule naïve des pourcentages simples
        Δq/q1 ÷ Δp/p1, qui dépend du point de départ) — c'est la formule des arcs qu'il faut.
      – Élasticité PONCTUELLE :  e = (dq/dp) · (p/q).
      – Élasticité REVENU (arc sur le revenu) et élasticité CROISÉE (quantité du bien A vs prix du bien B) :
        croisée > 0 -> biens SUBSTITUABLES ; croisée < 0 -> biens COMPLÉMENTAIRES ; = 0 -> indépendants.
      – Recette totale R = p·q (fait économique exact) : dR/dp = q·(1+e). Pour une DEMANDE (e ≤ 0) :
        si e < −1 une hausse de prix FAIT BAISSER la recette ; si −1 < e ≤ 0 elle la fait MONTER ;
        si e = −1 elle est INCHANGÉE (au premier ordre). Pour e > 0, dR/dp = q·(1+e) > 0 TOUJOURS
        (la recette monterait) — mais un e > 0 reçu est INDISTINGUABLE d'un « |e| d'une demande »
        passé par erreur en valeur absolue (verdict OPPOSÉ) : ABSTENTION (ValueError), jamais un pari.
  • AVERTISSEMENT ÉPISTÉMIQUE (à ne jamais taire) : une élasticité mesurée sur DEUX points suppose
    CETERIS PARIBUS (tout le reste constant entre les deux observations). C'est une MESURE descriptive
    sur les données fournies, PAS une preuve de causalité : si autre chose a bougé (revenu, goûts,
    prix des substituts), le chiffre ne mesure pas la seule réponse au prix.
  • Le calcul interne est EXACT (fractions.Fraction sur la valeur binaire exacte des entrées) ; la sortie
    est ARRONDIE à 10 chiffres significatifs — précision honnête (les données d'entrée sont des mesures).
    La symétrie de la formule des arcs est donc EXACTE, pas approchée.

GARANTIES (vérifiées en adverse par `valide_elasticite_prix.py`) :
  - prix ≤ 0 ou quantité ≤ 0 -> ValueError (un prix/une quantité observés sont strictement positifs ;
    ce garde-fou subsume q1+q2 == 0, refusé aussi explicitement) ;
  - revenu ≤ 0 -> ValueError ;
  - p1 == p2 (variation de prix nulle) -> ValueError : élasticité INDÉFINIE (division par zéro économique),
    on s'abstient plutôt que de rendre un infini ou un faux ; idem r1 == r2 et pB1 == pB2 ;
  - types invalides (bool — True n'est PAS 1 —, str, complexe, NaN, ±inf) -> ValueError ;
  - `classe` et `recette_totale_variation` refusent tout e non réel fini ;
  - `recette_totale_variation` REFUSE e > 0 (ValueError) : ambigu entre « élasticité signée positive »
    (recette monte toujours) et « |e| d'une demande » (verdict opposé possible) — abstention structurelle ;
  - fonctions PURES et déterministes ; conservateur (abstention tolérée, faux POSITIF interdit).

Le module n'importe que `math` et `fractions` (stdlib).
"""
from __future__ import annotations

import math
from fractions import Fraction

SOURCE = ("définition micro-économique de l'élasticité-prix ; formule des arcs (point milieu) "
          "attribuée à R. G. D. Allen, Economica 1934 ; relation élasticité/recette totale R=p·q "
          "(manuel de micro-économie classique)")

_CHIFFRES_SIGNIFICATIFS = 10

ELASTIQUE = "élastique"
INELASTIQUE = "inélastique"
UNITAIRE = "unitaire"
PARFAITEMENT_INELASTIQUE = "parfaitement inélastique"
SUBSTITUABLE = "substituable"
COMPLEMENTAIRE = "complémentaire"
INDEPENDANTS = "indépendants"
RECETTE_BAISSE = "baisse"
RECETTE_HAUSSE = "hausse"
RECETTE_INCHANGEE = "inchangée"


def _sig(x: float, n: int = _CHIFFRES_SIGNIFICATIFS) -> float:
    """Arrondit à n chiffres significatifs (précision honnête, indépendante de la magnitude)."""
    if x == 0:
        return 0.0
    return float(f"{x:.{n}g}")


def _est_reel(x) -> bool:
    """True ssi x est un réel fini (les bool sont REFUSÉS : True n'est pas une mesure)."""
    return isinstance(x, (int, float)) and not isinstance(x, bool) and math.isfinite(x)


def _exige_positif(x, nom: str) -> Fraction:
    """Réel fini strictement positif -> Fraction EXACTE de sa valeur ; sinon ValueError."""
    if not _est_reel(x) or x <= 0:
        raise ValueError(f"{nom} invalide : un réel strictement positif est requis (reçu {x!r})")
    return Fraction(x)


def _exige_reel(x, nom: str) -> Fraction:
    """Réel fini (signe libre) -> Fraction EXACTE de sa valeur ; sinon ValueError."""
    if not _est_reel(x):
        raise ValueError(f"{nom} invalide : un réel fini est requis (bool/str/NaN/inf refusés, reçu {x!r})")
    return Fraction(x)


def _arc(x1: Fraction, x2: Fraction, y1: Fraction, y2: Fraction) -> float:
    """Cœur exact de la formule des arcs : ((y2−y1)/moy_y) / ((x2−x1)/moy_x), simplifié en
    ((y2−y1)·(x1+x2)) / ((x2−x1)·(y1+y2)) — les facteurs 1/2 des moyennes se compensent EXACTEMENT.

    Préconditions (vérifiées par les appelants) : x1 ≠ x2, y1+y2 > 0, x1+x2 > 0."""
    e = ((y2 - y1) * (x1 + x2)) / ((x2 - x1) * (y1 + y2))
    return _sig(float(e))


# ── (a) ÉLASTICITÉ D'ARC (POINT MILIEU) ────────────────────────────────────────────────────────────────────────
def elasticite_arc(p1: float, q1: float, p2: float, q2: float) -> float:
    """Élasticité-prix d'ARC entre (p1,q1) et (p2,q2) : ((q2−q1)/moy_q) / ((p2−p1)/moy_p).

    SYMÉTRIQUE : échanger les deux points rend EXACTEMENT la même valeur (calcul en Fraction).
    Mesure descriptive ceteris paribus sur DEUX points — pas une causalité.
    p ≤ 0, q ≤ 0, q1+q2 = 0, p1 = p2 (élasticité indéfinie) -> ValueError."""
    fp1 = _exige_positif(p1, "p1 (prix)")
    fp2 = _exige_positif(p2, "p2 (prix)")
    fq1 = _exige_positif(q1, "q1 (quantité)")
    fq2 = _exige_positif(q2, "q2 (quantité)")
    if fq1 + fq2 == 0:
        raise ValueError("q1+q2 = 0 : quantité moyenne nulle, élasticité indéfinie")
    if fp1 == fp2:
        raise ValueError("p1 = p2 : variation de prix nulle, élasticité indéfinie (division par zéro)")
    return _arc(fp1, fp2, fq1, fq2)


# ── (b) ÉLASTICITÉ PONCTUELLE ─────────────────────────────────────────────────────────────────────────────────
def elasticite_ponctuelle(dq_dp: float, p: float, q: float) -> float:
    """Élasticité-prix PONCTUELLE : e = (dq/dp) · (p/q).

    dq_dp est la pente LOCALE de la demande (fournie, signe libre) ; p > 0 et q > 0 requis.
    La pente dq/dp est une donnée d'entrée : sa validité empirique n'est pas prouvée ici."""
    fd = _exige_reel(dq_dp, "dq_dp (pente)")
    fp = _exige_positif(p, "p (prix)")
    fq = _exige_positif(q, "q (quantité)")
    return _sig(float(fd * fp / fq))


# ── (c) CLASSE D'ÉLASTICITÉ ───────────────────────────────────────────────────────────────────────────────────
def classe(e: float) -> str:
    """Classe d'une élasticité-prix : |e| > 1 -> 'élastique' ; 0 < |e| < 1 -> 'inélastique' ;
    |e| = 1 -> 'unitaire' ; e = 0 -> 'parfaitement inélastique'. e non réel fini -> ValueError."""
    fe = _exige_reel(e, "e (élasticité)")
    if fe == 0:
        return PARFAITEMENT_INELASTIQUE
    a = abs(fe)
    if a > 1:
        return ELASTIQUE
    if a < 1:
        return INELASTIQUE
    return UNITAIRE


# ── (d) ÉLASTICITÉ REVENU ET ÉLASTICITÉ CROISÉE ───────────────────────────────────────────────────────────────
def elasticite_revenu(q1: float, q2: float, r1: float, r2: float) -> float:
    """Élasticité-REVENU d'arc : ((q2−q1)/moy_q) / ((r2−r1)/moy_r), r = revenu.

    r ≤ 0, q ≤ 0, r1 = r2 (variation de revenu nulle) -> ValueError. Ceteris paribus, pas une causalité."""
    fq1 = _exige_positif(q1, "q1 (quantité)")
    fq2 = _exige_positif(q2, "q2 (quantité)")
    fr1 = _exige_positif(r1, "r1 (revenu)")
    fr2 = _exige_positif(r2, "r2 (revenu)")
    if fr1 == fr2:
        raise ValueError("r1 = r2 : variation de revenu nulle, élasticité-revenu indéfinie")
    return _arc(fr1, fr2, fq1, fq2)


def elasticite_croisee(qA1: float, qA2: float, pB1: float, pB2: float) -> float:
    """Élasticité CROISÉE d'arc : ((qA2−qA1)/moy_qA) / ((pB2−pB1)/moy_pB) — quantité du bien A
    en réponse au prix du bien B. > 0 -> substituables ; < 0 -> complémentaires (voir relation_biens).

    p ≤ 0, q ≤ 0, pB1 = pB2 -> ValueError. Ceteris paribus, pas une causalité."""
    fq1 = _exige_positif(qA1, "qA1 (quantité de A)")
    fq2 = _exige_positif(qA2, "qA2 (quantité de A)")
    fp1 = _exige_positif(pB1, "pB1 (prix de B)")
    fp2 = _exige_positif(pB2, "pB2 (prix de B)")
    if fp1 == fp2:
        raise ValueError("pB1 = pB2 : variation du prix de B nulle, élasticité croisée indéfinie")
    return _arc(fp1, fp2, fq1, fq2)


def relation_biens(e_croisee: float) -> str:
    """Relation entre deux biens d'après l'élasticité croisée : > 0 -> 'substituable' ;
    < 0 -> 'complémentaire' ; = 0 -> 'indépendants'. e non réel fini -> ValueError."""
    fe = _exige_reel(e_croisee, "e_croisee (élasticité croisée)")
    if fe > 0:
        return SUBSTITUABLE
    if fe < 0:
        return COMPLEMENTAIRE
    return INDEPENDANTS


# ── (e) RECETTE TOTALE ────────────────────────────────────────────────────────────────────────────────────────
def recette_totale_variation(e: float) -> str:
    """Effet d'une HAUSSE de prix sur la recette totale R = p·q (fait économique exact, au premier ordre),
    pour une élasticité-prix de DEMANDE SIGNÉE e ≤ 0 UNIQUEMENT :
    e < −1 -> la recette BAISSE ('baisse') ; −1 < e ≤ 0 -> elle MONTE ('hausse') ;
    e = −1 -> INCHANGÉE ('inchangée'). e non réel fini -> ValueError.

    Dérivation : dR/dp = q·(1+e) avec e = (dq/dp)·(p/q) ; pour e ≤ 0, signe de 1+e = signe de 1−|e|.
    e > 0 -> ValueError (ABSTENTION) : pour un e signé positif, dR/dp = q·(1+e) > 0 toujours (la recette
    monterait), mais un appel avec e > 0 est INDISTINGUABLE d'un « |e| d'une demande » passé en valeur
    absolue, dont le verdict peut être l'OPPOSÉ (ex. |e| = 2.2 -> baisse). FAUX=0 : on s'abstient."""
    fe = _exige_reel(e, "e (élasticité)")
    if fe > 0:
        raise ValueError(
            "e > 0 ambigu : élasticité signée positive (recette monte toujours) ou |e| d'une demande "
            "(verdict opposé possible) — passer l'élasticité de demande SIGNÉE (e ≤ 0) ; abstention")
    if fe < -1:
        return RECETTE_BAISSE
    if fe > -1:
        return RECETTE_HAUSSE
    return RECETTE_INCHANGEE
