"""
ANATOMIE & PHYSIOLOGIE DESCRIPTIVES — CATALOGUE de FAITS ANATOMIQUES ÉTABLIS, FAUX=0.

À la manière de `classes_complexite.py` (catalogue de faits sourcés) : ici on énonce l'anatomie et la
physiologie de repos de l'ADULTE telles que tout traité d'anatomie les donne (Gray's Anatomy, Netter,
Marieb). Rien n'est calculé ni deviné : chaque entrée est un fait descriptif NON CONTESTÉ.

POSTURE FAUX=0 (la réalité juge, jamais un faux) :
  • Le catalogue ne contient que des faits ÉTABLIS et STABLES (nombre d'os, cavités cardiaques, trajet du
    sang, appartenance organe→système). Ce ne sont pas des mesures individuelles variables.
  • VALEURS DE REPOS ADULTE UNIQUEMENT. Aucune valeur pédiatrique n'est fournie : la physiologie de
    l'enfant/du nouveau-né DIFFÈRE (fréquence cardiaque plus élevée, ~270-300 os chez le nouveau-né qui
    fusionnent avec la croissance jusqu'à 206). Toute demande pédiatrique → ValueError (on le DIT plutôt
    que de rendre une valeur adulte trompeuse).
  • Les valeurs physiologiques normales sont toujours des INTERVALLES (min, max, unité), jamais un scalaire
    (un « normal » est une plage, pas un point).
  • Toute entrée hors catalogue (organe/système/paramètre inconnu, organe inventé, type invalide) →
    ValueError (ABSTENTION). Jamais une réponse inventée.
  • Déterministe, pur, sans état mutable partagé. Conservateur : abstention tolérée, faux POSITIF interdit.

ANCRE DISCRIMINANTE FORTE (piège classique) : l'ARTÈRE PULMONAIRE transporte du sang DÉSOXYGÉNÉ et les
VEINES PULMONAIRES du sang OXYGÉNÉ — l'inverse de la règle mnémotechnique naïve « artère = oxygéné ». Un
module qui l'ignorerait serait FAUX ; `oxygenation()` encode ce fait.

GARANTIES (vérifiées en adverse par `valide_anatomie_systemes.py`) :
  - 206 os chez l'adulte (nouveau-né ~270, non fourni) ; 4 cavités cardiaques ; 12 paires de nerfs crâniens ;
    33 vertèbres (7+12+5+5+4) ; 24 côtes (12 paires) ; 2 reins ; 1 foie ;
  - foie → système digestif, reins → système urinaire, rate → lymphatique/immunitaire (faits d'appartenance) ;
  - trajet du sang exact (petite + grande circulation) ;
  - est_normal('frequence_cardiaque', 72) → True ; 40 → False ;
  - types invalides (bool, str, NaN, ±inf, mauvaise arité) et hors-catalogue → ValueError.

Le module n'importe RIEN (stdlib pure, aucune dépendance).
"""
from __future__ import annotations

SOURCE = "anatomie descriptive classique (Gray's Anatomy ; Netter, Atlas d'anatomie humaine ; Marieb, " \
         "Anatomie et physiologie humaines) — faits établis non contestés"

# ── NORMALISATION DES NOMS (pure, sans import) ───────────────────────────────────────────────────────────────
# Table de translitération des accents français, pour que 'thyroïde'/'thyroide' ou 'œsophage'/'oesophage'
# désignent la même entrée sans dépendre d'unicodedata.
_ACCENTS = {
    "à": "a", "â": "a", "ä": "a",
    "é": "e", "è": "e", "ê": "e", "ë": "e",
    "î": "i", "ï": "i",
    "ô": "o", "ö": "o",
    "û": "u", "ù": "u", "ü": "u",
    "ç": "c",
    "œ": "oe", "æ": "ae",
    "'": " ", "-": " ", "_": " ",
}


def _norm(nom) -> str:
    """Normalise un nom : minuscules, accents ôtés, séparateurs → espace, blancs compactés.

    Refuse tout ce qui n'est PAS une chaîne (bool/None/nombre → ValueError : pas un nom d'organe)."""
    if not isinstance(nom, str):
        raise ValueError("nom invalide : une chaîne de caractères est requise")
    s = nom.strip().lower()
    out = []
    for ch in s:
        out.append(_ACCENTS.get(ch, ch))
    s = "".join(out)
    return " ".join(s.split())


def _est_reel(x) -> bool:
    """True ssi x est un réel fini (les bool sont REFUSÉS : True n'est pas une mesure, str non plus)."""
    if isinstance(x, bool):
        return False
    if isinstance(x, int):
        return True
    if isinstance(x, float):
        return x == x and x not in (float("inf"), float("-inf"))
    return False


# ── (a) LES 11 SYSTÈMES ──────────────────────────────────────────────────────────────────────────────────────
_SYSTEMES = {
    "cardiovasculaire": {
        "nom": "cardiovasculaire",
        "organes": ["cœur", "artères", "veines", "capillaires"],
        "fonction": "transport du sang : oxygène, dioxyde de carbone, nutriments, hormones, chaleur",
    },
    "respiratoire": {
        "nom": "respiratoire",
        "organes": ["poumons", "trachée", "bronches", "larynx", "pharynx", "diaphragme"],
        "fonction": "échanges gazeux : apport d'oxygène et rejet du dioxyde de carbone (hématose)",
    },
    "digestif": {
        "nom": "digestif",
        "organes": ["bouche", "œsophage", "estomac", "intestin grêle", "gros intestin",
                    "foie", "pancréas", "vésicule biliaire", "rectum", "anus"],
        "fonction": "ingestion, digestion, absorption des nutriments et élimination des déchets solides",
    },
    "nerveux": {
        "nom": "nerveux",
        "organes": ["cerveau", "moelle épinière", "nerfs"],
        "fonction": "réception, traitement et transmission de l'information ; commande motrice et sensorielle",
    },
    "musculaire": {
        "nom": "musculaire",
        "organes": ["muscles squelettiques", "muscles lisses", "muscle cardiaque"],
        "fonction": "mouvement, posture, production de chaleur (contraction)",
    },
    "squelettique": {
        "nom": "squelettique",
        "organes": ["os", "cartilages", "ligaments", "articulations"],
        "fonction": "soutien, protection des organes, mouvement (leviers), hématopoïèse, réserve de calcium",
    },
    "tégumentaire": {
        "nom": "tégumentaire",
        "organes": ["peau", "poils", "ongles", "glandes sudoripares", "glandes sébacées"],
        "fonction": "protection, thermorégulation, sensibilité, synthèse de vitamine D",
    },
    "endocrinien": {
        "nom": "endocrinien",
        "organes": ["hypophyse", "thyroïde", "parathyroïdes", "glandes surrénales",
                    "pancréas (îlots de Langerhans)", "épiphyse (pinéale)", "ovaires", "testicules"],
        "fonction": "régulation par des hormones : métabolisme, croissance, reproduction, homéostasie",
    },
    "lymphatique": {
        "nom": "lymphatique/immunitaire",
        "organes": ["rate", "thymus", "ganglions lymphatiques", "vaisseaux lymphatiques",
                    "moelle osseuse", "amygdales"],
        "fonction": "drainage de la lymphe, défense immunitaire, maturation des lymphocytes",
    },
    "urinaire": {
        "nom": "urinaire",
        "organes": ["reins", "uretères", "vessie", "urètre"],
        "fonction": "filtration du sang, production et évacuation de l'urine, équilibre hydro-électrolytique",
    },
    "reproducteur": {
        "nom": "reproducteur",
        "organes": ["testicules", "prostate", "pénis", "ovaires", "utérus",
                    "trompes de Fallope", "vagin"],
        "fonction": "production des gamètes et des hormones sexuelles, reproduction (système sexuellement "
                    "différencié : organes masculins ET féminins listés)",
    },
}

# Alias de systèmes → clé canonique.
_ALIAS_SYSTEME = {
    "cardiovasculaire": "cardiovasculaire", "circulatoire": "cardiovasculaire",
    "cardio vasculaire": "cardiovasculaire",
    "respiratoire": "respiratoire",
    "digestif": "digestif", "gastro intestinal": "digestif",
    "nerveux": "nerveux", "systeme nerveux": "nerveux",
    "musculaire": "musculaire", "musculeux": "musculaire",
    "squelettique": "squelettique", "osseux": "squelettique", "squelette": "squelettique",
    "tegumentaire": "tégumentaire", "cutane": "tégumentaire",
    "endocrinien": "endocrinien", "endocrine": "endocrinien", "hormonal": "endocrinien",
    "lymphatique": "lymphatique", "immunitaire": "lymphatique",
    "lymphatique immunitaire": "lymphatique", "immunologique": "lymphatique",
    "urinaire": "urinaire", "renal": "urinaire", "excreteur": "urinaire",
    "reproducteur": "reproducteur", "genital": "reproducteur", "reproductif": "reproducteur",
}


def systeme(nom) -> dict:
    """systeme(nom) → {'nom', 'organes': [...], 'fonction'}. Système hors des 11 → ValueError."""
    cle = _ALIAS_SYSTEME.get(_norm(nom))
    if cle is None:
        raise ValueError(f"système inconnu (hors des 11 systèmes du catalogue) : {nom!r}")
    src = _SYSTEMES[cle]
    return {"nom": src["nom"], "organes": list(src["organes"]), "fonction": src["fonction"]}


def liste_systemes() -> tuple:
    """Les 11 systèmes (noms canoniques), ordre stable."""
    return tuple(s["nom"] for s in _SYSTEMES.values())


# ── (b) ORGANES ──────────────────────────────────────────────────────────────────────────────────────────────
_ORGANES = {
    "coeur": {
        "nom": "cœur", "systeme": "cardiovasculaire",
        "fonction": "pompe le sang dans les circulations pulmonaire et systémique (4 cavités)",
        "localisation": "médiastin, dans le thorax, entre les deux poumons",
    },
    "poumons": {
        "nom": "poumons", "systeme": "respiratoire",
        "fonction": "échanges gazeux O2/CO2 (hématose) au niveau des alvéoles",
        "localisation": "cavité thoracique, de part et d'autre du médiastin",
    },
    "foie": {
        "nom": "foie", "systeme": "digestif",
        "fonction": "sécrète la bile, métabolisme et détoxification ; glande annexe du tube digestif",
        "localisation": "hypochondre droit, sous le diaphragme",
    },
    "reins": {
        "nom": "reins", "systeme": "urinaire",
        "fonction": "filtrent le sang et produisent l'urine ; régulation hydro-électrolytique",
        "localisation": "rétropéritoine, de part et d'autre de la colonne lombaire",
    },
    "estomac": {
        "nom": "estomac", "systeme": "digestif",
        "fonction": "brassage et digestion (suc gastrique acide, pepsine)",
        "localisation": "épigastre / hypochondre gauche, sous le diaphragme",
    },
    "intestin grele": {
        "nom": "intestin grêle", "systeme": "digestif",
        "fonction": "digestion terminale et absorption des nutriments (duodénum, jéjunum, iléon)",
        "localisation": "cavité abdominale, encadré par le gros intestin",
    },
    "gros intestin": {
        "nom": "gros intestin", "systeme": "digestif",
        "fonction": "réabsorption d'eau et d'électrolytes, formation et stockage des selles (côlon)",
        "localisation": "cavité abdominale, en cadre autour de l'intestin grêle",
    },
    "cerveau": {
        "nom": "cerveau", "systeme": "nerveux",
        "fonction": "traitement de l'information, cognition, commande motrice et sensorielle",
        "localisation": "boîte crânienne (encéphale)",
    },
    "moelle epiniere": {
        "nom": "moelle épinière", "systeme": "nerveux",
        "fonction": "conduction nerveuse et réflexes ; relie l'encéphale aux nerfs spinaux",
        "localisation": "canal vertébral (rachis)",
    },
    "pancreas": {
        "nom": "pancréas", "systeme": "digestif",
        "fonction": "glande MIXTE : exocrine (enzymes digestives) ET endocrine (îlots de Langerhans : "
                    "insuline, glucagon) — rattaché au système endocrinien pour sa fonction hormonale",
        "localisation": "rétropéritoine, en arrière de l'estomac",
    },
    "rate": {
        "nom": "rate", "systeme": "lymphatique/immunitaire",
        "fonction": "filtration du sang, recyclage des hématies âgées, réponse immunitaire",
        "localisation": "hypochondre gauche, sous le diaphragme",
    },
    "vessie": {
        "nom": "vessie", "systeme": "urinaire",
        "fonction": "réservoir de stockage de l'urine avant la miction",
        "localisation": "petit bassin (pelvis), en arrière de la symphyse pubienne",
    },
    "thyroide": {
        "nom": "thyroïde", "systeme": "endocrinien",
        "fonction": "sécrète les hormones thyroïdiennes T3/T4 (métabolisme) et la calcitonine",
        "localisation": "région cervicale antérieure, devant la trachée",
    },
    "oesophage": {
        "nom": "œsophage", "systeme": "digestif",
        "fonction": "conduit le bol alimentaire du pharynx à l'estomac (péristaltisme)",
        "localisation": "médiastin postérieur, du cou à l'abdomen (traverse le diaphragme)",
    },
    "diaphragme": {
        "nom": "diaphragme", "systeme": "respiratoire",
        "fonction": "principal muscle inspiratoire (muscle squelettique) ; sa contraction ventile les poumons",
        "localisation": "cloison musculo-tendineuse entre la cavité thoracique et la cavité abdominale",
    },
    "peau": {
        "nom": "peau", "systeme": "tégumentaire",
        "fonction": "protection, thermorégulation, sensibilité, synthèse de vitamine D",
        "localisation": "recouvre l'ensemble du corps (organe le plus étendu)",
    },
}

# Alias d'organes → clé canonique (synonymes usuels).
_ALIAS_ORGANE = {
    "poumon": "poumons",
    "rein": "reins",
    "colon": "gros intestin", "gros intestin colon": "gros intestin",
    "intestin grele": "intestin grele",
    "encephale": "cerveau",
    "moelle": "moelle epiniere", "moelle spinale": "moelle epiniere",
    "glande thyroide": "thyroide", "corps thyroide": "thyroide",
    "myocarde": "coeur",
}


def organe(nom) -> dict:
    """organe(nom) → {'nom', 'systeme', 'fonction', 'localisation'}. Organe hors catalogue → ValueError."""
    n = _norm(nom)
    cle = n if n in _ORGANES else _ALIAS_ORGANE.get(n)
    if cle is None or cle not in _ORGANES:
        raise ValueError(f"organe inconnu (hors catalogue ou inventé) : {nom!r}")
    src = _ORGANES[cle]
    return dict(src)


def liste_organes() -> tuple:
    """Les organes canoniques du catalogue (noms d'affichage), ordre stable."""
    return tuple(o["nom"] for o in _ORGANES.values())


# ── (c) CHIFFRES ANATOMIQUES ÉTABLIS (ADULTE) ────────────────────────────────────────────────────────────────
# valeur exacte pour l'ADULTE, unité, note. Toutes non contestées.
_COMPTES = {
    "os_adulte":            (206, "os", "adulte ; le nouveau-né en a ~270 qui fusionnent avec la croissance"),
    "cavites_cardiaques":   (4, "cavités", "2 oreillettes (droite, gauche) + 2 ventricules (droit, gauche)"),
    "oreillettes":          (2, "oreillettes", "droite et gauche"),
    "ventricules":          (2, "ventricules", "droit et gauche"),
    "paires_nerfs_craniens": (12, "paires", "nerfs crâniens numérotés I à XII"),
    "vertebres":            (33, "vertèbres", "7 cervicales + 12 thoraciques + 5 lombaires + "
                                              "5 sacrées (fusionnées) + 4 coccygiennes (fusionnées)"),
    "reins":                (2, "reins", "droit et gauche"),
    "foie":                 (1, "foie", "organe impair"),
    "cotes":                (24, "côtes", "12 paires (7 vraies, 3 fausses, 2 flottantes)"),
    "paires_cotes":         (12, "paires", "24 côtes au total"),
    "poumons":              (2, "poumons", "droit (3 lobes) et gauche (2 lobes)"),
}

_ALIAS_COMPTE = {
    "os": "os_adulte", "nombre d os": "os_adulte", "os adulte": "os_adulte",
    "cavites du coeur": "cavites_cardiaques", "cavites cardiaques": "cavites_cardiaques",
    "chambres cardiaques": "cavites_cardiaques",
    "nerfs craniens": "paires_nerfs_craniens", "paires de nerfs craniens": "paires_nerfs_craniens",
    "vertebres totales": "vertebres", "colonne vertebrale": "vertebres",
    "cotes totales": "cotes", "paires de cotes": "paires_cotes",
}

# Clés à contenu PÉDIATRIQUE explicitement refusées (le catalogue est adulte).
_PEDIATRIQUE = {
    "os nouveau ne", "os nouveau ne bebe", "os bebe", "os nourrisson", "os enfant",
    "os pediatrique", "os naissance", "os du nouveau ne", "os du bebe",
}


# Index normalisé (les clés canoniques ont des underscores que _norm convertit en espaces).
_COMPTES_NORM = {_norm(k): k for k in _COMPTES}


def _cle_compte(nom) -> str:
    n = _norm(nom)
    if n in _PEDIATRIQUE:
        raise ValueError("valeur pédiatrique non fournie : le nouveau-né a ~270 os (approché, variable) "
                         "qui fusionnent jusqu'à 206 chez l'adulte — catalogue = adulte uniquement")
    cle = _COMPTES_NORM.get(n) or _ALIAS_COMPTE.get(n)
    if cle is None:
        raise ValueError(f"compte anatomique inconnu (hors catalogue) : {nom!r}")
    return cle


def chiffre_anatomique(nom) -> int:
    """chiffre_anatomique(nom) → entier (compte anatomique établi de l'ADULTE).

    Ex. 'os_adulte'→206, 'cavites_cardiaques'→4, 'vertebres'→33, 'cotes'→24. Pédiatrique → ValueError
    (variable, non fourni). Inconnu → ValueError."""
    return _COMPTES[_cle_compte(nom)][0]


def detail_chiffre(nom) -> dict:
    """detail_chiffre(nom) → {'valeur', 'unite', 'note'} pour un compte établi. Inconnu/pédiatrique → ValueError."""
    v, u, note = _COMPTES[_cle_compte(nom)]
    return {"valeur": v, "unite": u, "note": note}


def vertebres() -> dict:
    """Répartition des 33 vertèbres de l'adulte (fait établi ; sacrum et coccyx fusionnés)."""
    return {
        "total": 33,
        "cervicales": 7,
        "thoraciques": 12,
        "lombaires": 5,
        "sacrees": 5,        # fusionnées en un sacrum chez l'adulte
        "coccygiennes": 4,   # fusionnées en un coccyx chez l'adulte
        "note": "sacrées (5) et coccygiennes (4) fusionnées chez l'adulte ; 7+12+5+5+4 = 33",
    }


# ── (d) PHYSIOLOGIE — VALEURS NORMALES DE REPOS, ADULTE (INTERVALLES) ─────────────────────────────────────────
# (min, max, unité). ADULTE au repos. Les valeurs de l'enfant DIFFÈRENT et ne sont pas fournies.
_NORMALES = {
    "frequence_cardiaque":     (60.0, 100.0, "bpm"),
    "pression_systolique":     (90.0, 120.0, "mmHg"),
    "frequence_respiratoire":  (12.0, 20.0, "/min"),
    "temperature":             (36.1, 37.2, "°C"),
    "debit_cardiaque":         (4.0, 8.0, "L/min"),
}

_ALIAS_PARAM = {
    "frequence cardiaque": "frequence_cardiaque", "pouls": "frequence_cardiaque",
    "fc": "frequence_cardiaque", "rythme cardiaque": "frequence_cardiaque",
    "pression systolique": "pression_systolique", "pas": "pression_systolique",
    "pression arterielle systolique": "pression_systolique", "tension systolique": "pression_systolique",
    "frequence respiratoire": "frequence_respiratoire", "fr": "frequence_respiratoire",
    "temperature": "temperature", "temperature corporelle": "temperature",
    "debit cardiaque": "debit_cardiaque", "dc": "debit_cardiaque",
}


_NORMALES_NORM = {_norm(k): k for k in _NORMALES}


def _cle_param(parametre) -> str:
    n = _norm(parametre)
    cle = _NORMALES_NORM.get(n) or _ALIAS_PARAM.get(n)
    if cle is None:
        raise ValueError(f"paramètre physiologique inconnu (hors catalogue) : {parametre!r}")
    return cle


def valeur_normale(parametre) -> tuple:
    """valeur_normale(parametre) → (min, max, unité) — plage normale de REPOS de l'ADULTE.

    Toujours un INTERVALLE, jamais un scalaire. Paramètre hors catalogue → ValueError."""
    lo, hi, unite = _NORMALES[_cle_param(parametre)]
    return (lo, hi, unite)


def est_normal(parametre, valeur) -> bool:
    """est_normal(parametre, valeur) → True ssi min ≤ valeur ≤ max (repos, adulte).

    Ex. est_normal('frequence_cardiaque', 72) → True ; 40 → False. Paramètre inconnu ou valeur non
    numérique (bool/str/NaN/inf) → ValueError."""
    lo, hi, _ = _NORMALES[_cle_param(parametre)]
    if not _est_reel(valeur):
        raise ValueError("valeur invalide : un réel fini est requis (bool/str/NaN/inf refusés)")
    return lo <= float(valeur) <= hi


def liste_parametres() -> tuple:
    """Les paramètres physiologiques catalogués (noms canoniques)."""
    return tuple(_NORMALES.keys())


# ── (e) CIRCULATION SANGUINE — TRAJET EXACT ──────────────────────────────────────────────────────────────────
_CIRCULATION = (
    "oreillette droite",     # sang désoxygéné revenu par les veines caves
    "ventricule droit",
    "artère pulmonaire",     # SEULE artère à transporter du sang DÉSOXYGÉNÉ (petite circulation)
    "poumons",               # hématose : le sang se recharge en O2
    "veines pulmonaires",    # SEULES veines à transporter du sang OXYGÉNÉ
    "oreillette gauche",
    "ventricule gauche",
    "aorte",                 # sang oxygéné vers la grande circulation
)


def circulation_sanguine() -> tuple:
    """Trajet exact du sang dans le cœur et les circulations pulmonaire puis systémique.

    (oreillette droite → ventricule droit → artère pulmonaire → poumons → veines pulmonaires →
     oreillette gauche → ventricule gauche → aorte)."""
    return tuple(_CIRCULATION)


# Oxygénation des grands vaisseaux — encode l'ANCRE DISCRIMINANTE (artère pulmonaire = désoxygéné).
_OXYGENATION = {
    "artere pulmonaire": "désoxygéné",     # contre-intuitif : la seule artère à sang désoxygéné
    "veines pulmonaires": "oxygéné",       # les seules veines à sang oxygéné
    "veine pulmonaire": "oxygéné",
    "aorte": "oxygéné",
    "veine cave": "désoxygéné",
    "veines caves": "désoxygéné",
    "veine cave superieure": "désoxygéné",
    "veine cave inferieure": "désoxygéné",
    "arteres systemiques": "oxygéné",
}


def oxygenation(vaisseau) -> str:
    """oxygenation(vaisseau) → 'oxygéné' | 'désoxygéné' (contenu sanguin normal du vaisseau).

    RÈGLE ANTI-PIÈGE : l'artère pulmonaire est DÉSOXYGÉNÉE, les veines pulmonaires OXYGÉNÉES (l'inverse
    du mnémonique naïf « artère = oxygéné »). Vaisseau hors catalogue → ValueError."""
    n = _norm(vaisseau)
    if n not in _OXYGENATION:
        raise ValueError(f"vaisseau hors catalogue d'oxygénation : {vaisseau!r}")
    return _OXYGENATION[n]
