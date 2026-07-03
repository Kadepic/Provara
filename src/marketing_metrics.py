"""
marketing_metrics.py — Efficacité d'une campagne (mesurable) : métriques marketing exactes.

Mécanismes EXACTS / définitions standard (mesures de performance d'une campagne).
Chaque métrique est un RATIO arithmétique exact entre deux quantités observées
(comptages d'événements ou montants monétaires). Aucune estimation, aucune heuristique.

  • taux_conversion(conversions, visiteurs) = conversions / visiteurs
      Part des visiteurs ayant accompli l'action ciblée (achat, inscription…).
      Ex. 50 conversions / 1000 visiteurs = 0.05 (= 5 %).
      Définition : un convertisseur est nécessairement un visiteur -> conversions <= visiteurs,
      donc le taux est dans [0, 1]. (Kotler & Keller, "Marketing Management" ; ISO/usage standard.)

  • ctr(clics, impressions) = clics / impressions
      Click-Through Rate : part des affichages (impressions) ayant donné un clic.
      Ex. 10 clics / 1000 impressions = 0.01 (= 1 %).
      Définition : un clic suppose une impression -> clics <= impressions, taux dans [0, 1].
      (IAB Measurement Guidelines ; Google Ads / définition publicitaire standard.)

  • roi(gain, cout) = (gain - cout) / cout
      Return On Investment : profit net rapporté au coût investi.
      'gain' = retour brut total (chiffre rapporté), 'cout' = montant investi (> 0).
      Ex. (150 - 100) / 100 = 0.5 (= +50 %). Le résultat peut être négatif (perte) si gain < cout,
      borné inférieurement par -1 (perte totale, gain = 0). C'est une mesure EXACTE.

  • cac(cout_total, clients_acquis) = cout_total / clients_acquis
      Customer Acquisition Cost : coût moyen pour acquérir un client.
      Ex. 1000 / 50 = 20.0 (20 unités monétaires par client).

  • roas(revenu, depense_pub) = revenu / depense_pub
      Return On Ad Spend : revenu généré par unité de dépense publicitaire.
      Ex. 400 / 100 = 4.0 (4 unités de revenu par unité dépensée).

ABSTENTION STRUCTURELLE (faux positif INTERDIT, jamais un faux -> ValueError) :
  • Dénominateur <= 0 (visiteurs, impressions, cout, clients_acquis, depense_pub) -> ValueError.
  • Quantité négative en entrée -> ValueError.
  • conversions > visiteurs, ou clics > impressions (taux > 1, impossible) -> ValueError.
  • Toute valeur non finie / non numérique -> ValueError.

Sorties arrondies à 6 décimales. stdlib uniquement, fonctions pures déterministes.
"""

import math

__all__ = [
    "taux_conversion",
    "ctr",
    "roi",
    "cac",
    "roas",
]

_PRECISION = 6


def _reel_fini(x, nom):
    """Convertit en float fini, sinon ValueError (abstention)."""
    try:
        v = float(x)
    except (TypeError, ValueError):
        raise ValueError(f"{nom} non numérique : {x!r}")
    if not math.isfinite(v):
        raise ValueError(f"{nom} non fini : {x!r}")
    return v


def _non_negatif(x, nom):
    """float fini >= 0, sinon ValueError."""
    v = _reel_fini(x, nom)
    if v < 0.0:
        raise ValueError(f"{nom} négatif : {v}")
    return v


def _denominateur_positif(x, nom):
    """float fini > 0 (dénominateur), sinon ValueError."""
    v = _reel_fini(x, nom)
    if v <= 0.0:
        raise ValueError(f"{nom} non strictement positif (dénominateur) : {v}")
    return v


def taux_conversion(conversions, visiteurs):
    """
    Taux de conversion = conversions / visiteurs, dans [0, 1].

    conversions : nombre de conversions, >= 0.
    visiteurs   : nombre de visiteurs, > 0 (dénominateur).
    conversions > visiteurs (taux impossible > 1), valeurs < 0 ou non finies -> ValueError.
    """
    c = _non_negatif(conversions, "conversions")
    v = _denominateur_positif(visiteurs, "visiteurs")
    if c > v:
        raise ValueError(f"conversions ({c}) > visiteurs ({v}) : taux impossible")
    return round(c / v, _PRECISION)


def ctr(clics, impressions):
    """
    Click-Through Rate = clics / impressions, dans [0, 1].

    clics       : nombre de clics, >= 0.
    impressions : nombre d'affichages, > 0 (dénominateur).
    clics > impressions (taux impossible > 1), valeurs < 0 ou non finies -> ValueError.
    """
    cl = _non_negatif(clics, "clics")
    im = _denominateur_positif(impressions, "impressions")
    if cl > im:
        raise ValueError(f"clics ({cl}) > impressions ({im}) : taux impossible")
    return round(cl / im, _PRECISION)


def roi(gain, cout):
    """
    Return On Investment = (gain - cout) / cout.

    gain : retour brut total, >= 0.
    cout : montant investi, > 0 (dénominateur).
    Le résultat peut être négatif (perte). gain < 0, cout <= 0 ou non finis -> ValueError.
    """
    g = _non_negatif(gain, "gain")
    c = _denominateur_positif(cout, "cout")
    return round((g - c) / c, _PRECISION)


def cac(cout_total, clients_acquis):
    """
    Customer Acquisition Cost = cout_total / clients_acquis.

    cout_total      : dépense totale, >= 0.
    clients_acquis  : nombre de clients acquis, > 0 (dénominateur).
    cout_total < 0, clients_acquis <= 0 ou non finis -> ValueError.
    """
    ct = _non_negatif(cout_total, "cout_total")
    cl = _denominateur_positif(clients_acquis, "clients_acquis")
    return round(ct / cl, _PRECISION)


def roas(revenu, depense_pub):
    """
    Return On Ad Spend = revenu / depense_pub.

    revenu       : revenu généré, >= 0.
    depense_pub  : dépense publicitaire, > 0 (dénominateur).
    revenu < 0, depense_pub <= 0 ou non finis -> ValueError.
    """
    r = _non_negatif(revenu, "revenu")
    d = _denominateur_positif(depense_pub, "depense_pub")
    return round(r / d, _PRECISION)
