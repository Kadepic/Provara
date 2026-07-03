"""industrie40.py — Automatisation / Industrie 4.0.

Taux de Rendement Synthétique (TRS) / Overall Equipment Effectiveness (OEE).

Mécanisme EXACT et établi (norme de fait industrielle, "OEE = A x P x Q") :
    OEE = Disponibilite x Performance x Qualite
avec chaque facteur dans [0, 1] :
    Disponibilite = temps de fonctionnement / temps requis
    Performance   = production reelle / production theorique
    Qualite       = bonnes pieces / total pieces

Faits de référence (établis, sourcés — littérature OEE / Lean / TPM) :
    - OEE "classe mondiale" (world class)  : OEE >= 0.85
    - OEE parfait                          : 1.0 (100 %)
    - exemple canonique 0.90 x 0.95 x 0.99 ~= 0.846

Discipline FAUX=0 :
    - tout facteur hors [0, 1]        -> ValueError (abstention)
    - tout dénominateur nul ou négatif -> ValueError (abstention)
    - entrées non numériques          -> ValueError (abstention)

stdlib uniquement, fonctions pures et déterministes.
"""

# Seuil "classe mondiale" établi dans la littérature OEE/TPM.
SEUIL_CLASSE_MONDIALE = 0.85


def _num(x, nom):
    """Exige un réel fini (int/float, pas bool) ; sinon ValueError (abstention)."""
    if isinstance(x, bool) or not isinstance(x, (int, float)):
        raise ValueError(f"{nom} : valeur non numérique")
    v = float(x)
    if v != v or v in (float("inf"), float("-inf")):
        raise ValueError(f"{nom} : valeur non finie")
    return v


def _facteur(x, nom):
    """Valide un facteur (ratio) : doit être un réel dans [0, 1]."""
    v = _num(x, nom)
    if v < 0.0 or v > 1.0:
        raise ValueError(f"{nom} : facteur hors [0, 1] ({v})")
    return v


def _ratio(numerateur, denominateur, nom):
    """Ratio borné dans [0, 1] : dénominateur > 0, 0 <= num <= den."""
    n = _num(numerateur, nom + ".numerateur")
    d = _num(denominateur, nom + ".denominateur")
    if d <= 0.0:
        raise ValueError(f"{nom} : dénominateur nul ou négatif")
    if n < 0.0:
        raise ValueError(f"{nom} : numérateur négatif")
    if n > d:
        raise ValueError(f"{nom} : numérateur > dénominateur (ratio > 1)")
    return n / d


def disponibilite(temps_fonctionnement, temps_requis):
    """Disponibilité = temps de fonctionnement / temps requis, dans [0, 1]."""
    return _ratio(temps_fonctionnement, temps_requis, "disponibilite")


def performance(production_reelle, production_theorique):
    """Performance = production réelle / production théorique, dans [0, 1]."""
    return _ratio(production_reelle, production_theorique, "performance")


def qualite(bonnes_pieces, total_pieces):
    """Qualité = bonnes pièces / total pièces, dans [0, 1]."""
    return _ratio(bonnes_pieces, total_pieces, "qualite")


def oee(disponibilite_f, performance_f, qualite_f):
    """OEE / TRS = Disponibilité x Performance x Qualité.

    Chaque facteur doit être dans [0, 1] ; le résultat est dans [0, 1].
    """
    d = _facteur(disponibilite_f, "disponibilite")
    p = _facteur(performance_f, "performance")
    q = _facteur(qualite_f, "qualite")
    return d * p * q


# Alias français explicite (TRS = OEE).
trs = oee


def est_classe_mondiale(valeur_oee):
    """Vrai ssi l'OEE atteint le seuil 'classe mondiale' (>= 0.85)."""
    v = _facteur(valeur_oee, "oee")
    return v >= SEUIL_CLASSE_MONDIALE
