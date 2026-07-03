"""
petrochimie.py — Raffinage du pétrole : faits sourcés + calculs EXACTS, FAUX=0.

Capacité déterministe et pure. Toute entrée invalide / hors référentiel lève
ValueError (abstention) : on ne renvoie JAMAIS une coupe ou un indice inventé.

Faits établis (distillation atmosphérique du pétrole brut) :
les coupes pétrolières sont définies par des plages de température d'ébullition.
Référence : intervalles de distillation standard (raffinage industriel).
    < 30 °C       -> gaz (GPL : méthane, éthane, propane, butane)
    30 - 200 °C   -> essence (naphta / gasoline)
    200 - 300 °C  -> kérosène (jet fuel)
    300 - 400 °C  -> diesel / gazole (fioul léger)
    > 400 °C      -> résidu / bitume (fiouls lourds, asphalte)

Calcul : l'indice d'octane d'un mélange est la MOYENNE VOLUMIQUE des indices
des constituants (loi de mélange volumique, base de la formulation des essences).
"""

# Catalogue des coupes pétrolières (faits). Bornes en °C ; intervalle semi-ouvert
# [borne_inf, borne_sup) pour une partition exacte et sans ambiguïté.
# (borne_inf, borne_sup, nom_de_coupe)
COUPES_PETROLIERES = (
    (float("-inf"), 30.0, "gaz"),
    (30.0, 200.0, "essence"),
    (200.0, 300.0, "kerosene"),
    (300.0, 400.0, "diesel/gazole"),
    (400.0, float("inf"), "residu/bitume"),
)


def _num(x, nom):
    """Renvoie float(x) si x est un réel fini-ou-infini bien défini ; sinon ValueError."""
    if isinstance(x, bool) or not isinstance(x, (int, float)):
        raise ValueError(f"{nom} non numérique : {x!r}")
    xf = float(x)
    if xf != xf:  # NaN
        raise ValueError(f"{nom} indéfini (NaN)")
    return xf


def fraction_distillation(temp_ebullition_C):
    """Coupe pétrolière obtenue par distillation atmosphérique pour une
    température d'ébullition donnée (°C).

    Partition établie (intervalles semi-ouverts [inf, sup)) :
        < 30 -> 'gaz' ; [30,200) -> 'essence' ; [200,300) -> 'kerosene' ;
        [300,400) -> 'diesel/gazole' ; >= 400 -> 'residu/bitume'.

    ValueError si la température n'est pas numérique (abstention).
    """
    t = _num(temp_ebullition_C, "temperature")
    for inf, sup, nom in COUPES_PETROLIERES:
        if inf <= t < sup:
            return nom
    # Inatteignable (la partition couvre R) ; garde-fou : jamais de faux.
    raise ValueError(f"temperature hors partition : {t}")


def indice_octane_melange(o1, v1, o2, v2):
    """Indice d'octane d'un mélange de deux essences (moyenne volumique) :

        (o1*v1 + o2*v2) / (v1 + v2)

    o1, o2 : indices d'octane des constituants ; v1, v2 : volumes (> 0).
    ValueError si un volume <= 0 (ou non numérique) ou un octane non numérique.
    """
    o1 = _num(o1, "octane_1")
    o2 = _num(o2, "octane_2")
    v1 = _num(v1, "volume_1")
    v2 = _num(v2, "volume_2")
    if v1 <= 0:
        raise ValueError(f"volume_1 doit être > 0 : {v1}")
    if v2 <= 0:
        raise ValueError(f"volume_2 doit être > 0 : {v2}")
    return (o1 * v1 + o2 * v2) / (v1 + v2)


def coupes():
    """Liste des coupes pétrolières du catalogue (faits)."""
    return [nom for _, _, nom in COUPES_PETROLIERES]
