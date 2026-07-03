"""
MUTATION TESTING — mesurer l'ADÉQUATION d'une suite de tests (code avancé, 2026-07-02).

POURQUOI : une suite de tests qui « passe » ne prouve rien si elle ne DÉTECTE pas les bugs. Le mutation testing
injecte des variantes fautives (mutants) et vérifie que la suite les TUE (échoue dessus). Un mutant SURVIVANT
révèle une lacune RÉELLE de la suite. C'est la mesure honnête de « mes tests exercent-ils vraiment le code ? ».

FAUX=0 :
  • Un mutant qui calcule EXACTEMENT la même fonction que la référence (mutant ÉQUIVALENT) est CORRECT : il ne peut
    pas être tué et ne doit PAS compter comme survivant. On les filtre via equivalence_semantique (preuve sur domaine
    fini) — sinon le score de mutation serait faussement bas.
  • Un SURVIVANT (non équivalent) est un FAIT vérifiable : un mutant PROUVÉ différent que la suite ne détecte pas =
    lacune réelle. Le score = tués / (mutants non équivalents). Aucun jugement inventé.
Stdlib pur, déterministe, souverain. Compose equivalence_semantique.
"""
from __future__ import annotations

import equivalence_semantique as _E

TUE = "tue"
SURVIVANT = "survivant"
EQUIVALENT = "equivalent"


def analyse(reference, mutants, teste, domaine) -> dict:
    """Analyse de mutation. `reference` = fonction correcte ; `mutants` = variantes ; `teste(fn) -> bool` = la suite
    de tests (True si fn passe) ; `domaine` = domaine FINI pour prouver l'équivalence. Renvoie
      {score, tues, survivants, equivalents, verdicts:[(mutant, statut)]}.
    score = tués / (mutants NON équivalents) ∈ [0,1] (None si aucun mutant non équivalent). Un SURVIVANT est prouvé
    différent de la référence ET non détecté = lacune réelle de la suite."""
    verdicts = []
    tues, survivants, equivalents = 0, 0, 0
    for m in mutants:
        # 1) mutant équivalent à la référence ? (preuve exhaustive sur le domaine fini)
        if _E.sur_domaine(reference, m, domaine)["statut"] == _E.EQUIVALENTES:
            verdicts.append((m, EQUIVALENT))
            equivalents += 1
            continue
        # 2) non équivalent : la suite le détecte-t-elle ? (teste False = échec = mutant TUÉ)
        if not teste(m):
            verdicts.append((m, TUE))
            tues += 1
        else:
            verdicts.append((m, SURVIVANT))          # non équivalent MAIS non détecté = lacune RÉELLE
            survivants += 1
    non_equiv = tues + survivants
    score = (tues / non_equiv) if non_equiv else None
    return {"score": score, "tues": tues, "survivants": survivants,
            "equivalents": equivalents, "verdicts": verdicts}


def suite_adequate(reference, mutants, teste, domaine, seuil: float = 1.0) -> bool:
    """La suite est ADÉQUATE si elle tue au moins `seuil` (fraction) des mutants non équivalents. seuil=1.0 = tuer
    TOUS les mutants fautifs. FAUX=0 : False dès qu'un mutant non équivalent SURVIT (lacune démontrée)."""
    r = analyse(reference, mutants, teste, domaine)
    return r["score"] is not None and r["score"] >= seuil
