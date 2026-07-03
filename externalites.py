"""
ÉCONOMIE DES EXTERNALITÉS — mécanisme + catalogue d'exemples sourcés (consensus manuel de microéconomie).

Une EXTERNALITÉ est un effet (bénéfice ou coût) d'une activité économique subi par un TIERS qui ne participe pas à la
transaction et n'est ni rémunéré ni dédommagé pour cet effet :
  • POSITIVE  : bénéfice non rémunéré reçu par les tiers (ex. vaccination → immunité collective ; abeilles → pollinisation).
  • NEGATIVE  : coût non payé imposé aux tiers (ex. pollution ; tabagisme passif ; congestion routière).

CONSÉQUENCES (faits établis) :
  • coût social = coût privé + coût externe  (le marché ne « voit » que le coût privé) ;
  • taxe pigouvienne corrigeant une externalité NÉGATIVE = coût externe marginal (aligne coût privé sur coût social) ;
  • défaillance de marché : externalité non internalisée ⇒ négative → SURPRODUCTION (coût social > privé),
                                                          ⇒ positive → SOUS-PRODUCTION (bénéfice social > privé).

FAUX=0 : déterministe, mécanisme exact. Tout exemple hors catalogue, type inconnu, impact nul ou coût négatif ⇒ ValueError
(abstention, jamais d'invention). Pur Python.
"""
from __future__ import annotations

POSITIVE = "positive"
NEGATIVE = "negative"

# ─── Catalogue d'exemples canoniques de manuel (sourcés/consensus). Hors-catalogue ⇒ abstention. ───
EXEMPLES = {
    "pollution": NEGATIVE,
    "tabagisme passif": NEGATIVE,
    "congestion routiere": NEGATIVE,
    "embouteillage": NEGATIVE,
    "pluies acides": NEGATIVE,
    "deforestation": NEGATIVE,
    "vaccination": POSITIVE,
    "pollinisation": POSITIVE,
    "abeilles": POSITIVE,
    "apiculture": POSITIVE,
    "education": POSITIVE,
    "recherche fondamentale": POSITIVE,
}


def _num(x, nom):
    """Convertit en float réel ; bool ou non-numérique ⇒ ValueError (abstention)."""
    if isinstance(x, bool) or not isinstance(x, (int, float)):
        raise ValueError(f"{nom} doit être un nombre : {x!r}")
    return float(x)


def type_externalite(impact_tiers):
    """Type de l'externalité d'après l'impact sur les tiers.

    - chaîne : exemple canonique du catalogue (sinon ValueError = abstention) ;
    - nombre : signe de l'impact net sur les tiers (bénéfice>0 ⇒ 'positive', coût<0 ⇒ 'negative').
    Impact nul (pas d'externalité) ⇒ ValueError.
    """
    if isinstance(impact_tiers, str):
        cle = impact_tiers.strip().lower()
        if cle in EXEMPLES:
            return EXEMPLES[cle]
        raise ValueError(f"exemple d'externalité hors catalogue : {impact_tiers!r}")
    v = _num(impact_tiers, "impact_tiers")
    if v > 0:
        return POSITIVE
    if v < 0:
        return NEGATIVE
    raise ValueError("impact sur les tiers nul : pas d'externalité")


def cout_social(cout_prive, cout_externe):
    """Coût social = coût privé + coût externe. Coûts négatifs ⇒ ValueError (abstention)."""
    cp = _num(cout_prive, "cout_prive")
    ce = _num(cout_externe, "cout_externe")
    if cp < 0 or ce < 0:
        raise ValueError("coûts négatifs invalides")
    return cp + ce


def taxe_pigou(cout_externe_marginal):
    """Taxe pigouvienne corrigeant une externalité négative = coût externe MARGINAL. Négatif ⇒ ValueError."""
    ce = _num(cout_externe_marginal, "cout_externe_marginal")
    if ce < 0:
        raise ValueError("coût externe marginal négatif invalide")
    return ce


def defaillance_marche(type_ext):
    """Sens de la défaillance quand l'externalité n'est PAS internalisée :
    'negative' → 'surproduction' ; 'positive' → 'sous-production'. Type inconnu ⇒ ValueError (abstention)."""
    if type_ext == NEGATIVE:
        return "surproduction"
    if type_ext == POSITIVE:
        return "sous-production"
    raise ValueError(f"type d'externalité inconnu : {type_ext!r}")


def internalisee(cout_prive_per, cout_externe, prise_en_compte):
    """L'externalité est-elle internalisée ? True si l'agent supporte le coût externe (taxe, droit de propriété, fusion).
    Pédagogique : renvoie le coût pris en compte par l'agent. Coûts négatifs ⇒ ValueError."""
    cp = _num(cout_prive_per, "cout_prive")
    ce = _num(cout_externe, "cout_externe")
    if cp < 0 or ce < 0:
        raise ValueError("coûts négatifs invalides")
    if not isinstance(prise_en_compte, bool):
        raise ValueError("prise_en_compte doit être un booléen")
    return cp + (ce if prise_en_compte else 0.0)


if __name__ == "__main__":
    print("=== ÉCONOMIE DES EXTERNALITÉS ===\n")
    print("  pollution      →", type_externalite("pollution"), "→ défaillance :", defaillance_marche(type_externalite("pollution")))
    print("  vaccination    →", type_externalite("vaccination"), "→ défaillance :", defaillance_marche(type_externalite("vaccination")))
    print("  coût social (privé 10 + externe 4) =", cout_social(10.0, 4.0))
    print("  taxe de Pigou (coût externe marginal 4) =", taxe_pigou(4.0))
