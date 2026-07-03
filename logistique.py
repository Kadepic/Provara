"""
logistique.py — Logistique / chaîne d'approvisionnement : gestion des stocks,
formules EXACTES et établies, FAUX=0.

Capacité déterministe et pure. Toute entrée invalide (non numérique, NaN/inf,
ou <= 0) lève ValueError (abstention) : on ne renvoie JAMAIS une quantité, un
point de commande ou un coût inventé.

Modèles de gestion des stocks (sources classiques de recherche opérationnelle) :

1) Quantité économique de commande — formule de Wilson (EOQ, Economic Order
   Quantity), Ford W. Harris (1913), R. H. Wilson (1934) :
        EOQ = sqrt( 2 * D * S / H )
   D = demande annuelle (unités/an), S = coût fixe par commande,
   H = coût de stockage par unité et par an. EOQ minimise le coût total
   ordre + stockage (au minimum, coût d'ordre = coût de stockage).

2) Point de commande (reorder point), demande déterministe :
        ROP = d * L
   d = demande par jour, L = délai d'approvisionnement (jours).

3) Stock de sécurité (safety stock), demande aléatoire, délai fixe :
        SS = z * sigma * sqrt(L)
   z = facteur de service (quantile normal ; 1.65 ~ 95 %), sigma = écart-type
   de la demande (par période), L = délai (en mêmes périodes).

4) Coût total annuel des stocks pour une quantité de commande Q :
        TC(Q) = (D / Q) * S + (Q / 2) * H
   coût de passation des commandes + coût de détention moyen. Au point Q = EOQ,
   TC vaut son minimum sqrt(2 * D * S * H).
"""

import math


def _pos(x, nom):
    """Renvoie float(x) si x est un réel fini STRICTEMENT positif ; sinon ValueError.

    Rejette : bool, non numérique, NaN, +/-inf, et toute valeur <= 0 (abstention).
    """
    if isinstance(x, bool) or not isinstance(x, (int, float)):
        raise ValueError(f"{nom} non numérique : {x!r}")
    xf = float(x)
    if xf != xf:  # NaN
        raise ValueError(f"{nom} indéfini (NaN)")
    if xf == float("inf") or xf == float("-inf"):
        raise ValueError(f"{nom} infini")
    if xf <= 0:
        raise ValueError(f"{nom} doit être > 0 : {xf}")
    return xf


def quantite_economique_commande(demande_annuelle, cout_commande, cout_stockage_unite):
    """Quantité économique de commande (EOQ, formule de Wilson) :

        sqrt( 2 * demande_annuelle * cout_commande / cout_stockage_unite )

    Tous les arguments doivent être > 0 (sinon ValueError, abstention).
    Résultat arrondi à 6 décimales.
    """
    D = _pos(demande_annuelle, "demande_annuelle")
    S = _pos(cout_commande, "cout_commande")
    H = _pos(cout_stockage_unite, "cout_stockage_unite")
    return round(math.sqrt(2.0 * D * S / H), 6)


# Alias usuel.
eoq = quantite_economique_commande


def point_commande(demande_jour, delai_jours):
    """Point de commande (reorder point) à demande déterministe :

        demande_jour * delai_jours

    Arguments > 0 (sinon ValueError). Résultat arrondi à 6 décimales.
    """
    d = _pos(demande_jour, "demande_jour")
    L = _pos(delai_jours, "delai_jours")
    return round(d * L, 6)


def stock_securite(ecart_type_demande, delai, z=1.65):
    """Stock de sécurité (safety stock) :

        z * ecart_type_demande * sqrt(delai)

    ecart_type_demande, delai, z doivent être > 0 (sinon ValueError).
    z par défaut 1.65 (~ niveau de service 95 %). Arrondi à 6 décimales.
    """
    sigma = _pos(ecart_type_demande, "ecart_type_demande")
    L = _pos(delai, "delai")
    zf = _pos(z, "z")
    return round(zf * sigma * math.sqrt(L), 6)


def cout_total_stock(demande_annuelle, cout_commande, cout_stockage_unite,
                     quantite_commande):
    """Coût total annuel des stocks pour une quantité de commande Q :

        (demande_annuelle / Q) * cout_commande + (Q / 2) * cout_stockage_unite

    Tous les arguments doivent être > 0 (sinon ValueError). Le minimum, atteint
    en Q = EOQ, vaut sqrt(2 * D * S * H). Résultat arrondi à 6 décimales.
    """
    D = _pos(demande_annuelle, "demande_annuelle")
    S = _pos(cout_commande, "cout_commande")
    H = _pos(cout_stockage_unite, "cout_stockage_unite")
    Q = _pos(quantite_commande, "quantite_commande")
    return round((D / Q) * S + (Q / 2.0) * H, 6)
