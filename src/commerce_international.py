"""
COMMERCE INTERNATIONAL — identités et lois EXACTES des échanges internationaux (mécanisme, jamais une valeur-pays
inventée). Même posture FAUX=0 que `pib` / `physique` / `chimie`.

  • Le MÉCANISME est une IDENTITÉ COMPTABLE / une LOI ÉTABLIE (Ricardo) exacte. On NE stocke AUCUNE donnée-pays
    « inventée » : on calcule sur les composantes fournies par l'appelant.
  • balance_commerciale(X, M) = X − M  (>0 EXCÉDENT, <0 DÉFICIT, =0 ÉQUILIBRE).
  • taux_couverture(X, M)     = X / M · 100  (en %, M > 0 obligatoire).
  • avantage_comparatif(coA, coB) : LOI DE RICARDO — l'avantage comparatif est sur le bien (ou au pays) au plus
    FAIBLE coût d'opportunité. coûts égaux ⇒ pas d'avantage comparatif (autarcie, aucun gain à l'échange).
  • termes_echange(Px, Pm) = indice prix export / indice prix import · 100 (termes nets de l'échange ;
    >100 amélioration/favorable, <100 dégradation).
  • La sortie numérique est ARRONDIE (6 décimales) — déterministe, sans bruit flottant.
  • Entrée invalide (non numérique, NaN/inf, valeur négative, importations ≤ 0, coût d'opportunité ≤ 0,
    indice de prix ≤ 0) -> ValueError. On S'ABSTIENT, jamais un faux.

Toutes les fonctions sont pures et déterministes. Aucune ne devine une donnée manquante.
"""
from __future__ import annotations

import math

_DECIMALES = 6

EXCEDENT = "excédent"
DEFICIT = "déficit"
EQUILIBRE = "équilibre"
AUCUN = "aucun"


def _num(x, nom: str) -> float:
    """Exige un réel fini (rejette bool, NaN, inf, non-numérique) -> ValueError sinon."""
    if isinstance(x, bool):
        raise ValueError(f"{nom} : booléen interdit")
    if not isinstance(x, (int, float)):
        raise ValueError(f"{nom} : type non numérique ({type(x).__name__})")
    xf = float(x)
    if not math.isfinite(xf):
        raise ValueError(f"{nom} : valeur non finie (NaN/inf)")
    return xf


def _flux(x, nom: str) -> float:
    """Un flux commercial (exportations/importations) est un montant >= 0 -> ValueError si < 0."""
    xf = _num(x, nom)
    if xf < 0:
        raise ValueError(f"{nom} : un flux commercial ne peut être négatif")
    return xf


def _positif(x, nom: str) -> float:
    """Exige un réel fini strictement positif -> ValueError sinon."""
    xf = _num(x, nom)
    if xf <= 0:
        raise ValueError(f"{nom} : doit être strictement positif")
    return xf


def _arr(x: float) -> float:
    """Arrondi déterministe à 6 décimales (normalise -0.0 en 0.0)."""
    r = round(x, _DECIMALES)
    return 0.0 if r == 0.0 else r


def balance_commerciale(exportations: float, importations: float) -> float:
    """Solde / balance commerciale (des biens) : X − M.

    > 0 EXCÉDENT, < 0 DÉFICIT, = 0 ÉQUILIBRE. Les flux X et M sont des montants >= 0 (négatif -> ValueError).
    Identité exacte.
    """
    x = _flux(exportations, "exportations")
    m = _flux(importations, "importations")
    return _arr(x - m)


def nature_balance(exportations: float, importations: float) -> str:
    """Qualifie le solde commercial : EXCÉDENT (X>M), DÉFICIT (X<M) ou ÉQUILIBRE (X=M)."""
    b = balance_commerciale(exportations, importations)
    if b > 0:
        return EXCEDENT
    if b < 0:
        return DEFICIT
    return EQUILIBRE


def taux_couverture(exportations: float, importations: float) -> float:
    """Taux de couverture en % : X / M · 100.

    > 100 % : excédentaire (X>M) ; < 100 % : déficitaire. importations <= 0 -> ValueError (division
    impossible / sans sens). exportations >= 0 (négatif -> ValueError ; 0 donne 0 %).
    """
    x = _flux(exportations, "exportations")
    m = _positif(importations, "importations")
    return _arr(x / m * 100.0)


def avantage_comparatif(cout_opportunite_A: float, cout_opportunite_B: float) -> str:
    """LOI DE RICARDO — l'avantage comparatif appartient au plus FAIBLE coût d'opportunité.

    Compare deux coûts d'opportunité (p.ex. produire le même bien dans le pays A vs le pays B, OU les deux
    biens d'un même pays) : renvoie "A" si coA < coB, "B" si coB < coA, "aucun" si égaux (pas d'avantage
    comparatif ⇒ aucun gain à l'échange). Les coûts d'opportunité doivent être strictement positifs
    (<= 0 -> ValueError).
    """
    a = _positif(cout_opportunite_A, "cout_opportunite_A")
    b = _positif(cout_opportunite_B, "cout_opportunite_B")
    if a < b:
        return "A"
    if b < a:
        return "B"
    return AUCUN


def termes_echange(indice_prix_exportations: float, indice_prix_importations: float) -> float:
    """Termes (nets) de l'échange : indice de prix des exportations / indice de prix des importations · 100.

    > 100 : amélioration (les exportations s'échangent contre davantage d'importations) ; < 100 : dégradation.
    Les indices de prix doivent être strictement positifs (<= 0 -> ValueError).
    """
    px = _positif(indice_prix_exportations, "indice_prix_exportations")
    pm = _positif(indice_prix_importations, "indice_prix_importations")
    return _arr(px / pm * 100.0)
