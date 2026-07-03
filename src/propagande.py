"""propagande.py — Catalogue ÉTABLI des techniques de propagande et taxonomie
du désordre informationnel (faits sourcés, abstention sur l'inconnu).

Sources / consensus :
  * Les SEPT techniques courantes de propagande sont celles codifiées par
    l'Institute for Propaganda Analysis (IPA, 1937-1942, « The Fine Art of
    Propaganda » / « ABC's of Propaganda Analysis ») :
        Name Calling, Glittering Generalities, Transfer, Testimonial,
        Plain Folks, Card Stacking, Band Wagon.
  * La trichotomie mis-/dis-/mal-information est celle du cadre
    « Information Disorder » de Wardle & Derakhshan (Conseil de l'Europe, 2017),
    défini par deux axes établis : l'information est-elle FAUSSE, et y a-t-il
    INTENTION de nuire ?

Toute entrée hors de ces référentiels -> ValueError (abstention : on n'invente
jamais une technique ni un type non répertorié).

stdlib uniquement. Fonctions pures et déterministes.
"""

# ---------------------------------------------------------------------------
# Catalogue des 7 techniques de l'Institute for Propaganda Analysis
# (clé canonique -> définition = fait établi)
# ---------------------------------------------------------------------------

_TECHNIQUES = {
    "name_calling": (
        "Name Calling (diabolisation) : accoler à une idée, une personne ou un "
        "groupe une étiquette péjorative (un « mauvais nom ») afin de la faire "
        "rejeter et condamner sans examen des preuves."
    ),
    "generalites_creuses": (
        "Glittering Generalities (généralités creuses/brillantes) : associer une "
        "cause à des mots-vertus vagues et valorisants (liberté, justice, "
        "démocratie, progrès) pour la faire accepter sans examen — l'inverse du "
        "name calling."
    ),
    "transfert": (
        "Transfer (transfert) : reporter sur une idée le prestige, l'autorité ou "
        "le caractère sacré d'une chose respectée (drapeau, religion, science, "
        "nation) — ou le discrédit d'une chose haïe — pour la faire accepter ou "
        "rejeter par association."
    ),
    "temoignage": (
        "Testimonial (témoignage) : faire affirmer par une personne respectée ou "
        "détestée qu'une idée, un produit ou un candidat est bon ou mauvais — on "
        "s'appuie sur la caution de la célébrité plutôt que sur l'argument."
    ),
    "homme_du_peuple": (
        "Plain Folks (homme du peuple / les gens ordinaires) : se présenter comme "
        "une personne ordinaire, « du peuple », pour gagner la confiance — « je "
        "suis comme vous, donc mes idées sont bonnes »."
    ),
    "card_stacking": (
        "Card Stacking (carte biaisée) : sélectionner et n'exposer que les faits "
        "(ou les mensonges, illustrations, distractions) favorables à un camp en "
        "occultant les éléments contraires, pour donner la meilleure — ou la pire "
        "— image possible."
    ),
    "bandwagon": (
        "Band Wagon (train en marche) : pousser à adhérer au motif que « tout le "
        "monde le fait » / « tout le monde y va » — il faut suivre la foule, "
        "rejoindre le groupe, pour ne pas être laissé de côté."
    ),
}

# Alias de surface (formes normalisées sans accents) -> clé canonique.
_ALIAS_TECHNIQUE = {
    "name_calling": "name_calling",
    "diabolisation": "name_calling",
    "etiquetage": "name_calling",
    "name_calling_diabolisation": "name_calling",
    "generalites_creuses": "generalites_creuses",
    "generalites_brillantes": "generalites_creuses",
    "glittering_generalities": "generalites_creuses",
    "transfert": "transfert",
    "transfer": "transfert",
    "temoignage": "temoignage",
    "testimonial": "temoignage",
    "homme_du_peuple": "homme_du_peuple",
    "gens_ordinaires": "homme_du_peuple",
    "plain_folks": "homme_du_peuple",
    "carte_biaisee": "card_stacking",
    "carte_biaisee_card_stacking": "card_stacking",
    "card_stacking": "card_stacking",
    "train_en_marche": "bandwagon",
    "train_en_marche_bandwagon": "bandwagon",
    "bandwagon": "bandwagon",
    "band_wagon": "bandwagon",
}

# ---------------------------------------------------------------------------
# Taxonomie du désordre informationnel (Wardle & Derakhshan, 2017)
# Deux axes établis : faux ? intention de nuire ?
# ---------------------------------------------------------------------------

_TYPES_DESINFORMATION = {
    "misinformation": {
        "definition": (
            "Misinformation : information FAUSSE diffusée SANS intention de "
            "nuire — erreur involontaire, méprise partagée de bonne foi (rumeur, "
            "contresens, légende relayée par mégarde)."
        ),
        "faux": True,
        "intention_de_nuire": False,
    },
    "disinformation": {
        "definition": (
            "Disinformation : information FAUSSE créée et diffusée DÉLIBÉRÉMENT "
            "pour nuire — tromper ou manipuler une personne, un groupe, une "
            "organisation ou un pays."
        ),
        "faux": True,
        "intention_de_nuire": True,
    },
    "malinformation": {
        "definition": (
            "Malinformation : information VRAIE (fondée sur des faits réels) "
            "diffusée délibérément pour nuire — fuite de données privées, "
            "divulgation malveillante, propos sortis de leur contexte, "
            "harcèlement."
        ),
        "faux": False,
        "intention_de_nuire": True,
    },
}

_ALIAS_TYPE = {
    "misinformation": "misinformation",
    "mesinformation": "misinformation",
    "disinformation": "disinformation",
    "malinformation": "malinformation",
}

# ---------------------------------------------------------------------------
# Normalisation
# ---------------------------------------------------------------------------

_ACCENTS = str.maketrans(
    "àâäáãéèêëíìîïóòôöõúùûüçñ",
    "aaaaaeeeeiiiiooooouuuucn",
)


def _normalise(nom):
    """Normalise un libellé : minuscules, sans accents, séparateurs -> '_'.

    Entrée non textuelle ou vide -> ValueError (abstention)."""
    if not isinstance(nom, str):
        raise ValueError("nom non textuel")
    t = nom.strip().lower().translate(_ACCENTS)
    if not t:
        raise ValueError("nom vide")
    for ch in ("'", "’", "-", "/", " "):
        t = t.replace(ch, "_")
    # underscores multiples -> simple
    while "__" in t:
        t = t.replace("__", "_")
    t = t.strip("_")
    if not t:
        raise ValueError("nom vide apres normalisation")
    return t


# ---------------------------------------------------------------------------
# API publique — techniques
# ---------------------------------------------------------------------------

def technique(nom):
    """Définition (fait établi, IPA) d'une technique de propagande nommée.

    Accepte la clé canonique ou un alias usuel (name_calling/diabolisation,
    transfert, temoignage, homme_du_peuple, carte_biaisee/card_stacking,
    train_en_marche/bandwagon, generalites_creuses).

    Technique hors catalogue -> ValueError (abstention : jamais d'invention)."""
    cle = _normalise(nom)
    if cle in _ALIAS_TECHNIQUE:
        return _TECHNIQUES[_ALIAS_TECHNIQUE[cle]]
    if cle in _TECHNIQUES:
        return _TECHNIQUES[cle]
    raise ValueError("technique hors catalogue: %r" % (nom,))


def liste_techniques():
    """Liste triée des 7 clés canoniques de techniques de propagande (IPA)."""
    return sorted(_TECHNIQUES)


# ---------------------------------------------------------------------------
# API publique — taxonomie du désordre informationnel
# ---------------------------------------------------------------------------

def type_desinformation(nom):
    """Caractérise un type du désordre informationnel (Wardle & Derakhshan).

    Renvoie un dict {definition, faux, intention_de_nuire} pour
    'misinformation' (erreur involontaire), 'disinformation' (fausse +
    intentionnelle) ou 'malinformation' (vraie + intention de nuire).

    Type hors taxonomie -> ValueError (abstention)."""
    cle = _normalise(nom)
    if cle in _ALIAS_TYPE:
        cle = _ALIAS_TYPE[cle]
    if cle not in _TYPES_DESINFORMATION:
        raise ValueError("type de desinformation hors taxonomie: %r" % (nom,))
    d = _TYPES_DESINFORMATION[cle]
    # copie défensive : l'appelant ne doit pas muter le catalogue
    return {
        "definition": d["definition"],
        "faux": d["faux"],
        "intention_de_nuire": d["intention_de_nuire"],
    }


def est_intentionnel(nom):
    """True ssi le type implique une INTENTION de nuire (disinformation,
    malinformation) ; False pour misinformation (erreur involontaire).

    Type hors taxonomie -> ValueError (abstention)."""
    return type_desinformation(nom)["intention_de_nuire"]


def est_faux(nom):
    """True ssi le type repose sur une information FAUSSE (mis-/disinformation) ;
    False pour malinformation (information vraie détournée).

    Type hors taxonomie -> ValueError (abstention)."""
    return type_desinformation(nom)["faux"]


def liste_types_desinformation():
    """Liste triée des 3 types du désordre informationnel."""
    return sorted(_TYPES_DESINFORMATION)
