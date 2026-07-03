"""
budget_personnel.py — Gestion d'un budget personnel : CALCULS EXACTS + conventions de gestion ÉTABLIES.

Posture FAUX=0 (la réalité/définition juge, jamais un faux) :
  • Chaque fonction est un MÉCANISME ARITHMÉTIQUE EXACT (différence, ratio, pourcentage) entre des montants
    monétaires OBSERVÉS. Aucune estimation, aucune heuristique, aucune valeur inventée : seul le CALCUL est posé.
  • Les deux SEULES constantes conventionnelles sont des RÈGLES de gestion ÉTABLIES et largement sourcées :
      – la règle « 50/30/20 » (Elizabeth Warren, « All Your Worth », 2005 ; reprise par les organismes de
        conseil budgétaire) : 50 % besoins, 30 % envies, 20 % épargne ;
      – le taux d'endettement maximal de 35 % (norme du HCSF — Haut Conseil de Stabilité Financière, France,
        appliquée par les banques depuis 2022 ; assurance comprise) comme plafond de mensualité d'emprunt.
    Ces deux conventions sont des DONNÉES (pas un mécanisme déduit) ; le calcul qui les applique est exact.

DÉFINITIONS (montants en unités monétaires, comptages de valeur) :
  • solde(revenus, depenses) = revenus − depenses
      Différence comptable. Peut être NÉGATIF (déficit) : c'est un résultat réel, pas une abstention.
      Ex. 2000 − 1500 = 500.

  • taux_epargne(epargne, revenus) = epargne / revenus * 100
      Part des revenus mise de côté (« savings rate »). On ne peut pas épargner plus que ses revenus
      -> 0 <= epargne <= revenus, taux dans [0, 100]. Ex. 500/2000 = 25 %.

  • regle_50_30_20(revenus) -> {"besoins": 0.5·R, "envies": 0.3·R, "epargne": 0.2·R}
      Répartition recommandée du revenu net. Les trois parts somment exactement à R (0.5+0.3+0.2 = 1).
      Ex. sur 2000 : besoins 1000, envies 600, épargne 400.

  • capacite_emprunt(revenus_mensuels, taux_endettement=0.35) = revenus_mensuels * taux_endettement
      Mensualité d'emprunt MAXIMALE supportable (plafond HCSF 35 % par défaut). Ce N'EST PAS le capital
      empruntable (qui dépend de la durée et du taux d'intérêt) mais la mensualité maximale.
      Ex. 2000 * 0.35 = 700.

  • reste_a_vivre(revenus, charges_fixes) = revenus − charges_fixes
      Ce qu'il reste après les charges fixes (loyer, crédits, abonnements). Peut être NÉGATIF (déficit).
      Ex. 2000 − 1500 = 500.

ABSTENTION STRUCTURELLE (faux positif INTERDIT, jamais un faux -> ValueError) :
  • revenus <= 0 (pas de revenu -> ratios indéfinis, règles inapplicables) -> ValueError.
  • montant négatif (depenses, charges_fixes, epargne < 0) -> ValueError.
  • epargne > revenus (taux d'épargne > 100 %, impossible) -> ValueError.
  • taux_endettement hors ]0, 1] (0 % ou > 100 % de mensualité, absurde) -> ValueError.
  • valeur non finie (NaN/inf) / non numérique / booléen -> ValueError.

Montants arrondis à 2 décimales (centimes — précision monétaire honnête). stdlib uniquement, fonctions pures
déterministes.
"""

import math

__all__ = [
    "solde",
    "taux_epargne",
    "regle_50_30_20",
    "capacite_emprunt",
    "reste_a_vivre",
]

_PRECISION = 2

# Conventions de gestion ÉTABLIES (données sourcées, pas un mécanisme déduit).
_REGLE_BESOINS = 0.50   # 50 % — besoins essentiels (E. Warren, 2005)
_REGLE_ENVIES = 0.30    # 30 % — envies / loisirs
_REGLE_EPARGNE = 0.20   # 20 % — épargne / remboursement de dettes
_TAUX_ENDETTEMENT_HCSF = 0.35  # 35 % — plafond HCSF (France, 2022)

SOURCE = "règle 50/30/20 (E. Warren, 2005) ; taux d'endettement 35 % (HCSF, France, 2022)"


def _reel_fini(x, nom):
    """Convertit en float fini, sinon ValueError (abstention). Booléen refusé."""
    if isinstance(x, bool):
        raise ValueError(f"{nom} booléen refusé : {x!r}")
    try:
        v = float(x)
    except (TypeError, ValueError):
        raise ValueError(f"{nom} non numérique : {x!r}")
    if not math.isfinite(v):
        raise ValueError(f"{nom} non fini : {x!r}")
    return v


def _revenu(x):
    """Revenu : float fini STRICTEMENT positif, sinon ValueError."""
    v = _reel_fini(x, "revenus")
    if v <= 0:
        raise ValueError(f"revenus doivent être > 0 : {v!r}")
    return v


def _montant(x, nom):
    """Montant monétaire : float fini >= 0, sinon ValueError."""
    v = _reel_fini(x, nom)
    if v < 0:
        raise ValueError(f"{nom} ne peut être négatif : {v!r}")
    return v


def solde(revenus, depenses):
    """solde = revenus − depenses (peut être négatif = déficit)."""
    r = _revenu(revenus)
    d = _montant(depenses, "depenses")
    return round(r - d, _PRECISION)


def taux_epargne(epargne, revenus):
    """taux d'épargne (%) = epargne / revenus * 100, avec 0 <= epargne <= revenus."""
    r = _revenu(revenus)
    e = _montant(epargne, "epargne")
    if e > r:
        raise ValueError(f"epargne ({e}) ne peut excéder les revenus ({r}) : taux > 100 % impossible")
    return round(e / r * 100.0, _PRECISION)


def regle_50_30_20(revenus):
    """Répartition 50/30/20 du revenu (besoins/envies/épargne), somme exacte = revenus."""
    r = _revenu(revenus)
    return {
        "besoins": round(_REGLE_BESOINS * r, _PRECISION),
        "envies": round(_REGLE_ENVIES * r, _PRECISION),
        "epargne": round(_REGLE_EPARGNE * r, _PRECISION),
    }


def capacite_emprunt(revenus_mensuels, taux_endettement=_TAUX_ENDETTEMENT_HCSF):
    """Mensualité d'emprunt maximale = revenus_mensuels * taux_endettement (35 % HCSF par défaut)."""
    r = _revenu(revenus_mensuels)
    t = _reel_fini(taux_endettement, "taux_endettement")
    if not (0.0 < t <= 1.0):
        raise ValueError(f"taux_endettement doit être dans ]0, 1] : {t!r}")
    return round(r * t, _PRECISION)


def reste_a_vivre(revenus, charges_fixes):
    """reste à vivre = revenus − charges_fixes (peut être négatif = déficit)."""
    r = _revenu(revenus)
    c = _montant(charges_fixes, "charges_fixes")
    return round(r - c, _PRECISION)
