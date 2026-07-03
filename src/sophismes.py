"""sophismes.py — Identification de la FORME d'un argument conditionnel et
catalogue de sophismes informels nommés (faits établis, abstention sur l'inconnu).

Mécanisme EXACT (logique propositionnelle classique) :
À partir d'une prémisse majeure conditionnelle A->B, la forme d'inférence est
déterminée de façon BIJECTIVE par ce que la mineure affirme/nie et par la
conclusion :

    A->B , A      ⊢ B      modus_ponens          (VALIDE)
    A->B , ¬B     ⊢ ¬A     modus_tollens         (VALIDE)
    A->B , B      ⊢ A      affirmation_consequent (SOPHISME — invalide)
    A->B , ¬A     ⊢ ¬B     negation_antecedent    (SOPHISME — invalide)

La validité de modus_ponens / modus_tollens et l'invalidité de
l'affirmation du conséquent / la négation de l'antécédent sont des théorèmes
établis de la logique classique (vérifiables par table de vérité).

Toute combinaison hors de ces quatre schémas reconnus -> ValueError (abstention).
stdlib uniquement. Fonctions pures et déterministes.
"""

# ---------------------------------------------------------------------------
# Formes conditionnelles : validité = fait logique établi
# ---------------------------------------------------------------------------

_FORMES_VALIDES = frozenset({"modus_ponens", "modus_tollens"})
_FORMES_SOPHISMES = frozenset({"affirmation_consequent", "negation_antecedent"})
_FORMES = _FORMES_VALIDES | _FORMES_SOPHISMES

# Préfixes de négation acceptés (normalisés vers une négation booléenne).
_PREFIXES_NEG = ("~", "¬", "!", "non ", "not ")


def _parse_litteral(s):
    """Analyse un littéral 'p', 'q', '~p', '¬q'… -> (atome:str, negation:bool).

    L'atome doit être un identifiant simple [A-Za-z0-9_]+.
    Entrée non analysable -> ValueError (abstention)."""
    if not isinstance(s, str):
        raise ValueError("litteral non textuel")
    t = s.strip()
    if not t:
        raise ValueError("litteral vide")
    neg = False
    change = True
    # On retire au plus une négation (une double négation explicite est hors
    # du fragment reconnu -> abstention par échec de l'atome final).
    while change:
        change = False
        for pref in _PREFIXES_NEG:
            if t.lower().startswith(pref):
                if neg:  # double négation : hors fragment reconnu
                    raise ValueError("double negation non reconnue")
                neg = True
                t = t[len(pref):].strip()
                change = True
                break
    if not t or not all(c.isalnum() or c == "_" for c in t):
        raise ValueError("atome invalide: %r" % (s,))
    return t, neg


def _parse_conditionnel(s):
    """Analyse 'A->B' (ou 'A→B') -> (antecedent:str, consequent:str).

    Antécédent et conséquent doivent être des atomes POSITIFS distincts.
    Sinon -> ValueError (hors du fragment reconnu)."""
    if not isinstance(s, str):
        raise ValueError("majeure non textuelle")
    t = s.strip().replace("→", "->")
    if "->" not in t:
        raise ValueError("majeure non conditionnelle (manque '->')")
    parties = t.split("->")
    if len(parties) != 2:
        raise ValueError("conditionnel mal forme")
    a, neg_a = _parse_litteral(parties[0])
    b, neg_b = _parse_litteral(parties[1])
    if neg_a or neg_b:
        raise ValueError("antecedent/consequent negatifs non reconnus")
    if a == b:
        raise ValueError("antecedent et consequent identiques")
    return a, b


def identifie_forme(premisse_majeure, premisse_mineure, conclusion):
    """Identifie la forme d'inférence d'un syllogisme conditionnel.

    Renvoie 'modus_ponens', 'modus_tollens' (valides),
    'affirmation_consequent', 'negation_antecedent' (sophismes formels).

    Toute combinaison non reconnue -> ValueError (abstention structurelle)."""
    ante, cons = _parse_conditionnel(premisse_majeure)
    am, nm = _parse_litteral(premisse_mineure)
    ac, nc = _parse_litteral(conclusion)

    # modus_ponens : mineure = A , conclusion = B
    if am == ante and not nm and ac == cons and not nc:
        return "modus_ponens"
    # affirmation du conséquent : mineure = B , conclusion = A
    if am == cons and not nm and ac == ante and not nc:
        return "affirmation_consequent"
    # négation de l'antécédent : mineure = ¬A , conclusion = ¬B
    if am == ante and nm and ac == cons and nc:
        return "negation_antecedent"
    # modus_tollens : mineure = ¬B , conclusion = ¬A
    if am == cons and nm and ac == ante and nc:
        return "modus_tollens"

    raise ValueError("forme non reconnue")


def est_valide(forme):
    """True ssi la forme d'inférence conditionnelle est logiquement VALIDE.

    Forme non reconnue -> ValueError (abstention)."""
    if forme in _FORMES_VALIDES:
        return True
    if forme in _FORMES_SOPHISMES:
        return False
    raise ValueError("forme inconnue: %r" % (forme,))


def est_sophisme(forme):
    """True ssi la forme est un SOPHISME formel (invalide).

    Forme non reconnue -> ValueError (abstention)."""
    if forme in _FORMES_SOPHISMES:
        return True
    if forme in _FORMES_VALIDES:
        return False
    raise ValueError("forme inconnue: %r" % (forme,))


# ---------------------------------------------------------------------------
# Catalogue de sophismes INFORMELS nommés (définitions = faits établis)
# ---------------------------------------------------------------------------

_SOPHISMES_INFORMELS = {
    "homme_de_paille": (
        "Déformer ou caricaturer la position de l'adversaire pour réfuter "
        "facilement cette version affaiblie plutôt que l'argument réel."
    ),
    "pente_glissante": (
        "Soutenir qu'un premier pas entraîne inévitablement une chaîne de "
        "conséquences néfastes, sans justifier chaque maillon de la chaîne."
    ),
    "ad_hominem": (
        "Attaquer la personne qui avance l'argument (sa personnalité, ses "
        "intérêts) au lieu de répondre à l'argument lui-même."
    ),
    "faux_dilemme": (
        "Présenter seulement deux options exclusives alors qu'il en existe "
        "d'autres, forçant un choix artificiel."
    ),
    "appel_a_l_ignorance": (
        "Conclure qu'une proposition est vraie parce qu'elle n'a pas été "
        "prouvée fausse (ou inversement)."
    ),
    "petition_de_principe": (
        "Tenir pour acquise dans les prémisses la conclusion que l'on prétend "
        "démontrer (raisonnement circulaire)."
    ),
    "appel_a_l_autorite": (
        "Tenir une affirmation pour vraie au seul motif qu'une autorité la "
        "soutient, sans autorité pertinente ni preuve."
    ),
    "generalisation_hative": (
        "Tirer une conclusion générale à partir d'un échantillon trop petit "
        "ou non représentatif."
    ),
    "ad_populum": (
        "Tenir une affirmation pour vraie parce qu'un grand nombre de "
        "personnes y croient (appel à la popularité)."
    ),
    "post_hoc": (
        "Inférer une relation de cause à effet du seul fait qu'un événement "
        "en a suivi un autre (post hoc ergo propter hoc)."
    ),
    "faux_epouvantail": (
        "Variante de l'homme de paille : combattre une position fictive "
        "attribuée à tort à l'adversaire."
    ),
}

# Alias de surface -> clé canonique (formes usuelles écrites par l'utilisateur).
_ALIAS = {
    "homme de paille": "homme_de_paille",
    "epouvantail": "faux_epouvantail",
    "pente glissante": "pente_glissante",
    "ad hominem": "ad_hominem",
    "attaque personnelle": "ad_hominem",
    "faux dilemme": "faux_dilemme",
    "fausse dichotomie": "faux_dilemme",
    "appel a l ignorance": "appel_a_l_ignorance",
    "argument d ignorance": "appel_a_l_ignorance",
    "petition de principe": "petition_de_principe",
    "raisonnement circulaire": "petition_de_principe",
    "appel a l autorite": "appel_a_l_autorite",
    "argument d autorite": "appel_a_l_autorite",
    "generalisation hative": "generalisation_hative",
    "ad populum": "ad_populum",
    "appel a la popularite": "ad_populum",
    "post hoc": "post_hoc",
    "fausse cause": "post_hoc",
}


def _normalise_nom(nom):
    if not isinstance(nom, str):
        raise ValueError("nom non textuel")
    t = nom.strip().lower()
    if not t:
        raise ValueError("nom vide")
    # Uniformise séparateurs et retire ponctuation d'apostrophe.
    for ch in ("'", "’", "-"):
        t = t.replace(ch, " ")
    t = " ".join(t.split())  # espaces multiples -> simple
    cle = t.replace(" ", "_")
    return t, cle


def definition_sophisme(nom):
    """Définition (fait établi) d'un sophisme informel nommé.

    Nom inconnu du catalogue -> ValueError (abstention, jamais d'invention)."""
    surface, cle = _normalise_nom(nom)
    if cle in _SOPHISMES_INFORMELS:
        return _SOPHISMES_INFORMELS[cle]
    if surface in _ALIAS:
        return _SOPHISMES_INFORMELS[_ALIAS[surface]]
    if cle in _ALIAS:
        return _SOPHISMES_INFORMELS[_ALIAS[cle]]
    raise ValueError("sophisme inconnu: %r" % (nom,))


def liste_sophismes():
    """Liste triée des clés canoniques de sophismes informels catalogués."""
    return sorted(_SOPHISMES_INFORMELS)
