"""
BASE DE FAITS VÉRIFIÉS — les JUGES de lookup pour les catégories où la vérité ne se DÉDUIT pas
mais se CONSTATE (cat 2 monde physique), s'est FIGÉE (cat 3 faits passés) ou se CONVIENT (cat 4
convention/langue). Cf. [[project-ia-domaines-realite]].

Anti-LLM : on ne répond QUE si le fait est présent et vérifié ; sinon HORS honnête. Jamais de
dérivation probabiliste, jamais de devinette. Chaque fait porte une CATÉGORIE (la nature de la
contrainte) et une SOURCE (traçabilité = ce qui ancre la vérité).

Soundness : `cherche(relation, entite)` est un lookup EXACT sur clé normalisée -> renvoie un Fait
ou None. `repond_nl(question)` extrait (relation, entite) d'une poignée de gabarits sûrs puis
délègue à `cherche`. Une question hors base ne produit JAMAIS un faux : au pire (HORS, None).

C'est une AMORCE volontairement petite mais 100 % vérifiée à la main. Le mécanisme (lookup-jugé +
HORS) est ce qui compte ; la base s'étend en ajoutant des entrées vérifiées (même boucle).
"""
from __future__ import annotations

import dataclasses
import re
import unicodedata

# Catégories de nature (cf. taxonomie). On les nomme pour que le verdict porte la nature.
CAT_PHYSIQUE = "physique"      # cat 2 : observé, modèles révisables
CAT_PASSE = "passe"           # cat 3 : figé, irréversible
CAT_CONVENTION = "convention"  # cat 4 : fixé par accord (langue, unités, normes)

VERIFIE = "verifie"
HORS = "hors"


@dataclasses.dataclass(frozen=True, slots=True)
class Fait:
    valeur: str
    categorie: str
    source: str


_NORM_PONCT = re.compile(r"[^a-z0-9 ]+")   # OPTIM T9 : pre-compile (evite le cache-lookup re par appel)
_NORM_ESP = re.compile(r"\s+")


def normalise(s: str) -> str:
    """Minuscule, sans accents, sans ponctuation, espaces compactés. Clé canonique robuste."""
    s = s.strip().lower()
    if not s.isascii():                        # OPTIM T9 : NFD = identite sur l'ASCII (aucune marque Mn) -> sortie identique, on saute
        s = "".join(c for c in unicodedata.normalize("NFD", s) if unicodedata.category(c) != "Mn")
    s = _NORM_PONCT.sub(" ", s)
    return _NORM_ESP.sub(" ", s).strip()


# --- LES FAITS (clé = (relation, entité normalisée)). Tout est VÉRIFIÉ + SOURCÉ. -------------
FAITS: dict[tuple[str, str], Fait] = {
    # cat 2 — monde physique / géographie physique (constantes, capitales géographiques)
    ("capitale", "france"): Fait("Paris", CAT_PHYSIQUE, "géographie politique (référence)"),
    ("capitale", "japon"): Fait("Tokyo", CAT_PHYSIQUE, "géographie politique (référence)"),
    ("capitale", "italie"): Fait("Rome", CAT_PHYSIQUE, "géographie politique (référence)"),
    ("capitale", "espagne"): Fait("Madrid", CAT_PHYSIQUE, "géographie politique (référence)"),
    ("capitale", "allemagne"): Fait("Berlin", CAT_PHYSIQUE, "géographie politique (référence)"),
    # Capitales — extension (faits stables, vérifiables ; Mongolie/Australie gardés inconnus = pièges adverses).
    ("capitale", "portugal"): Fait("Lisbonne", CAT_PHYSIQUE, "géographie politique (référence)"),
    ("capitale", "belgique"): Fait("Bruxelles", CAT_PHYSIQUE, "géographie politique (référence)"),
    ("capitale", "pays bas"): Fait("Amsterdam", CAT_PHYSIQUE, "géographie politique (référence)"),
    ("capitale", "suisse"): Fait("Berne", CAT_PHYSIQUE, "géographie politique (référence)"),
    ("capitale", "autriche"): Fait("Vienne", CAT_PHYSIQUE, "géographie politique (référence)"),
    ("capitale", "grece"): Fait("Athènes", CAT_PHYSIQUE, "géographie politique (référence)"),
    ("capitale", "pologne"): Fait("Varsovie", CAT_PHYSIQUE, "géographie politique (référence)"),
    ("capitale", "suede"): Fait("Stockholm", CAT_PHYSIQUE, "géographie politique (référence)"),
    ("capitale", "norvege"): Fait("Oslo", CAT_PHYSIQUE, "géographie politique (référence)"),
    ("capitale", "danemark"): Fait("Copenhague", CAT_PHYSIQUE, "géographie politique (référence)"),
    ("capitale", "finlande"): Fait("Helsinki", CAT_PHYSIQUE, "géographie politique (référence)"),
    ("capitale", "irlande"): Fait("Dublin", CAT_PHYSIQUE, "géographie politique (référence)"),
    ("capitale", "royaume uni"): Fait("Londres", CAT_PHYSIQUE, "géographie politique (référence)"),
    ("capitale", "russie"): Fait("Moscou", CAT_PHYSIQUE, "géographie politique (référence)"),
    ("capitale", "etats unis"): Fait("Washington", CAT_PHYSIQUE, "géographie politique (référence)"),
    ("capitale", "canada"): Fait("Ottawa", CAT_PHYSIQUE, "géographie politique (référence)"),
    ("capitale", "mexique"): Fait("Mexico", CAT_PHYSIQUE, "géographie politique (référence)"),
    ("capitale", "bresil"): Fait("Brasília", CAT_PHYSIQUE, "géographie politique (référence)"),
    ("capitale", "argentine"): Fait("Buenos Aires", CAT_PHYSIQUE, "géographie politique (référence)"),
    ("capitale", "chine"): Fait("Pékin", CAT_PHYSIQUE, "géographie politique (référence)"),
    ("capitale", "inde"): Fait("New Delhi", CAT_PHYSIQUE, "géographie politique (référence)"),
    ("capitale", "egypte"): Fait("Le Caire", CAT_PHYSIQUE, "géographie politique (référence)"),
    ("capitale", "maroc"): Fait("Rabat", CAT_PHYSIQUE, "géographie politique (référence)"),
    ("capitale", "turquie"): Fait("Ankara", CAT_PHYSIQUE, "géographie politique (référence)"),
    ("capitale", "coree du sud"): Fait("Séoul", CAT_PHYSIQUE, "géographie politique (référence)"),
    ("capitale", "thailande"): Fait("Bangkok", CAT_PHYSIQUE, "géographie politique (référence)"),
    ("capitale", "vietnam"): Fait("Hanoï", CAT_PHYSIQUE, "géographie politique (référence)"),
    ("capitale", "indonesie"): Fait("Jakarta", CAT_PHYSIQUE, "géographie politique (référence)"),
    ("capitale", "perou"): Fait("Lima", CAT_PHYSIQUE, "géographie politique (référence)"),
    ("capitale", "chili"): Fait("Santiago", CAT_PHYSIQUE, "géographie politique (référence)"),
    ("capitale", "colombie"): Fait("Bogota", CAT_PHYSIQUE, "géographie politique (référence)"),
    ("capitale", "hongrie"): Fait("Budapest", CAT_PHYSIQUE, "géographie politique (référence)"),
    ("capitale", "roumanie"): Fait("Bucarest", CAT_PHYSIQUE, "géographie politique (référence)"),
    ("capitale", "ukraine"): Fait("Kiev", CAT_PHYSIQUE, "géographie politique (référence)"),
    ("capitale", "nigeria"): Fait("Abuja", CAT_PHYSIQUE, "géographie politique (référence)"),
    ("capitale", "kenya"): Fait("Nairobi", CAT_PHYSIQUE, "géographie politique (référence)"),
    ("capitale", "algerie"): Fait("Alger", CAT_PHYSIQUE, "géographie politique (référence)"),
    ("capitale", "tunisie"): Fait("Tunis", CAT_PHYSIQUE, "géographie politique (référence)"),
    ("capitale", "arabie saoudite"): Fait("Riyad", CAT_PHYSIQUE, "géographie politique (référence)"),
    ("capitale", "iran"): Fait("Téhéran", CAT_PHYSIQUE, "géographie politique (référence)"),
    # Capitales — extension lot #3 (capitales univoques uniquement ; capitales multiples/disputées exclues =
    # Bolivie/Afrique du Sud/Israël laissées inconnues -> HORS honnête).
    ("capitale", "islande"): Fait("Reykjavik", CAT_PHYSIQUE, "géographie politique (référence)"),
    ("capitale", "croatie"): Fait("Zagreb", CAT_PHYSIQUE, "géographie politique (référence)"),
    ("capitale", "bulgarie"): Fait("Sofia", CAT_PHYSIQUE, "géographie politique (référence)"),
    ("capitale", "serbie"): Fait("Belgrade", CAT_PHYSIQUE, "géographie politique (référence)"),
    ("capitale", "slovaquie"): Fait("Bratislava", CAT_PHYSIQUE, "géographie politique (référence)"),
    ("capitale", "slovenie"): Fait("Ljubljana", CAT_PHYSIQUE, "géographie politique (référence)"),
    ("capitale", "lituanie"): Fait("Vilnius", CAT_PHYSIQUE, "géographie politique (référence)"),
    ("capitale", "lettonie"): Fait("Riga", CAT_PHYSIQUE, "géographie politique (référence)"),
    ("capitale", "estonie"): Fait("Tallinn", CAT_PHYSIQUE, "géographie politique (référence)"),
    ("capitale", "luxembourg"): Fait("Luxembourg", CAT_PHYSIQUE, "géographie politique (référence)"),
    ("capitale", "cuba"): Fait("La Havane", CAT_PHYSIQUE, "géographie politique (référence)"),
    ("capitale", "venezuela"): Fait("Caracas", CAT_PHYSIQUE, "géographie politique (référence)"),
    ("capitale", "equateur"): Fait("Quito", CAT_PHYSIQUE, "géographie politique (référence)"),
    ("capitale", "uruguay"): Fait("Montevideo", CAT_PHYSIQUE, "géographie politique (référence)"),
    ("capitale", "paraguay"): Fait("Asuncion", CAT_PHYSIQUE, "géographie politique (référence)"),
    ("capitale", "pakistan"): Fait("Islamabad", CAT_PHYSIQUE, "géographie politique (référence)"),
    ("capitale", "philippines"): Fait("Manille", CAT_PHYSIQUE, "géographie politique (référence)"),
    ("capitale", "malaisie"): Fait("Kuala Lumpur", CAT_PHYSIQUE, "géographie politique (référence)"),
    ("capitale", "singapour"): Fait("Singapour", CAT_PHYSIQUE, "géographie politique (référence)"),
    ("capitale", "nouvelle zelande"): Fait("Wellington", CAT_PHYSIQUE, "géographie politique (référence)"),
    ("capitale", "liban"): Fait("Beyrouth", CAT_PHYSIQUE, "géographie politique (référence)"),
    ("capitale", "irak"): Fait("Bagdad", CAT_PHYSIQUE, "géographie politique (référence)"),
    ("capitale", "jordanie"): Fait("Amman", CAT_PHYSIQUE, "géographie politique (référence)"),
    ("capitale", "qatar"): Fait("Doha", CAT_PHYSIQUE, "géographie politique (référence)"),
    ("capitale", "koweit"): Fait("Koweït", CAT_PHYSIQUE, "géographie politique (référence)"),
    ("capitale", "afghanistan"): Fait("Kaboul", CAT_PHYSIQUE, "géographie politique (référence)"),
    ("capitale", "ethiopie"): Fait("Addis-Abeba", CAT_PHYSIQUE, "géographie politique (référence)"),
    ("capitale", "ghana"): Fait("Accra", CAT_PHYSIQUE, "géographie politique (référence)"),
    ("capitale", "senegal"): Fait("Dakar", CAT_PHYSIQUE, "géographie politique (référence)"),
    ("vitesse_lumiere", ""): Fait("299792458 m/s (dans le vide)", CAT_PHYSIQUE, "SI / CODATA (valeur exacte)"),
    ("ebullition_eau", ""): Fait("100 °C (à 1 atm = 101325 Pa)", CAT_PHYSIQUE, "définition Celsius / point de référence"),
    ("congelation_eau", ""): Fait("0 °C (à 1 atm = 101325 Pa)", CAT_PHYSIQUE, "définition Celsius / point de référence"),
    ("zero_absolu", ""): Fait("0 K = -273,15 °C", CAT_PHYSIQUE, "SI (échelle Kelvin)"),
    ("symbole_chimique", "or"): Fait("Au", CAT_PHYSIQUE, "tableau périodique (IUPAC)"),
    ("symbole_chimique", "fer"): Fait("Fe", CAT_PHYSIQUE, "tableau périodique (IUPAC)"),
    # Symboles chimiques — extension (IUPAC, stables ; plomb gardé inconnu = piège adverse).
    ("symbole_chimique", "hydrogene"): Fait("H", CAT_PHYSIQUE, "tableau périodique (IUPAC)"),
    ("symbole_chimique", "oxygene"): Fait("O", CAT_PHYSIQUE, "tableau périodique (IUPAC)"),
    ("symbole_chimique", "carbone"): Fait("C", CAT_PHYSIQUE, "tableau périodique (IUPAC)"),
    ("symbole_chimique", "azote"): Fait("N", CAT_PHYSIQUE, "tableau périodique (IUPAC)"),
    ("symbole_chimique", "sodium"): Fait("Na", CAT_PHYSIQUE, "tableau périodique (IUPAC)"),
    ("symbole_chimique", "potassium"): Fait("K", CAT_PHYSIQUE, "tableau périodique (IUPAC)"),
    ("symbole_chimique", "calcium"): Fait("Ca", CAT_PHYSIQUE, "tableau périodique (IUPAC)"),
    ("symbole_chimique", "argent"): Fait("Ag", CAT_PHYSIQUE, "tableau périodique (IUPAC)"),
    ("symbole_chimique", "cuivre"): Fait("Cu", CAT_PHYSIQUE, "tableau périodique (IUPAC)"),
    ("symbole_chimique", "zinc"): Fait("Zn", CAT_PHYSIQUE, "tableau périodique (IUPAC)"),
    ("symbole_chimique", "mercure"): Fait("Hg", CAT_PHYSIQUE, "tableau périodique (IUPAC)"),
    ("symbole_chimique", "helium"): Fait("He", CAT_PHYSIQUE, "tableau périodique (IUPAC)"),
    ("symbole_chimique", "chlore"): Fait("Cl", CAT_PHYSIQUE, "tableau périodique (IUPAC)"),
    ("symbole_chimique", "soufre"): Fait("S", CAT_PHYSIQUE, "tableau périodique (IUPAC)"),
    ("symbole_chimique", "aluminium"): Fait("Al", CAT_PHYSIQUE, "tableau périodique (IUPAC)"),
    ("symbole_chimique", "etain"): Fait("Sn", CAT_PHYSIQUE, "tableau périodique (IUPAC)"),
    ("symbole_chimique", "nickel"): Fait("Ni", CAT_PHYSIQUE, "tableau périodique (IUPAC)"),
    ("symbole_chimique", "platine"): Fait("Pt", CAT_PHYSIQUE, "tableau périodique (IUPAC)"),
    ("symbole_chimique", "titane"): Fait("Ti", CAT_PHYSIQUE, "tableau périodique (IUPAC)"),
    ("symbole_chimique", "uranium"): Fait("U", CAT_PHYSIQUE, "tableau périodique (IUPAC)"),
    ("symbole_chimique", "lithium"): Fait("Li", CAT_PHYSIQUE, "tableau périodique (IUPAC)"),
    ("symbole_chimique", "magnesium"): Fait("Mg", CAT_PHYSIQUE, "tableau périodique (IUPAC)"),
    ("symbole_chimique", "phosphore"): Fait("P", CAT_PHYSIQUE, "tableau périodique (IUPAC)"),
    ("symbole_chimique", "fluor"): Fait("F", CAT_PHYSIQUE, "tableau périodique (IUPAC)"),
    ("symbole_chimique", "brome"): Fait("Br", CAT_PHYSIQUE, "tableau périodique (IUPAC)"),
    ("symbole_chimique", "iode"): Fait("I", CAT_PHYSIQUE, "tableau périodique (IUPAC)"),
    ("symbole_chimique", "tungstene"): Fait("W", CAT_PHYSIQUE, "tableau périodique (IUPAC)"),
    # Symboles chimiques — extension lot #3 (IUPAC ; plomb VOLONTAIREMENT exclu = piège adverse de valide_base_faits).
    ("symbole_chimique", "bore"): Fait("B", CAT_PHYSIQUE, "tableau périodique (IUPAC)"),
    ("symbole_chimique", "neon"): Fait("Ne", CAT_PHYSIQUE, "tableau périodique (IUPAC)"),
    ("symbole_chimique", "argon"): Fait("Ar", CAT_PHYSIQUE, "tableau périodique (IUPAC)"),
    ("symbole_chimique", "silicium"): Fait("Si", CAT_PHYSIQUE, "tableau périodique (IUPAC)"),
    ("symbole_chimique", "manganese"): Fait("Mn", CAT_PHYSIQUE, "tableau périodique (IUPAC)"),
    ("symbole_chimique", "cobalt"): Fait("Co", CAT_PHYSIQUE, "tableau périodique (IUPAC)"),
    ("symbole_chimique", "chrome"): Fait("Cr", CAT_PHYSIQUE, "tableau périodique (IUPAC)"),
    ("symbole_chimique", "baryum"): Fait("Ba", CAT_PHYSIQUE, "tableau périodique (IUPAC)"),
    ("symbole_chimique", "palladium"): Fait("Pd", CAT_PHYSIQUE, "tableau périodique (IUPAC)"),
    ("symbole_chimique", "krypton"): Fait("Kr", CAT_PHYSIQUE, "tableau périodique (IUPAC)"),
    ("symbole_chimique", "xenon"): Fait("Xe", CAT_PHYSIQUE, "tableau périodique (IUPAC)"),
    ("symbole_chimique", "cadmium"): Fait("Cd", CAT_PHYSIQUE, "tableau périodique (IUPAC)"),
    ("symbole_chimique", "antimoine"): Fait("Sb", CAT_PHYSIQUE, "tableau périodique (IUPAC)"),
    ("symbole_chimique", "arsenic"): Fait("As", CAT_PHYSIQUE, "tableau périodique (IUPAC)"),
    ("symbole_chimique", "bismuth"): Fait("Bi", CAT_PHYSIQUE, "tableau périodique (IUPAC)"),
    ("symbole_chimique", "gallium"): Fait("Ga", CAT_PHYSIQUE, "tableau périodique (IUPAC)"),
    ("symbole_chimique", "germanium"): Fait("Ge", CAT_PHYSIQUE, "tableau périodique (IUPAC)"),
    ("symbole_chimique", "selenium"): Fait("Se", CAT_PHYSIQUE, "tableau périodique (IUPAC)"),
    ("symbole_chimique", "strontium"): Fait("Sr", CAT_PHYSIQUE, "tableau périodique (IUPAC)"),
    ("symbole_chimique", "vanadium"): Fait("V", CAT_PHYSIQUE, "tableau périodique (IUPAC)"),
    ("symbole_chimique", "scandium"): Fait("Sc", CAT_PHYSIQUE, "tableau périodique (IUPAC)"),
    ("symbole_chimique", "beryllium"): Fait("Be", CAT_PHYSIQUE, "tableau périodique (IUPAC)"),
    ("symbole_chimique", "cesium"): Fait("Cs", CAT_PHYSIQUE, "tableau périodique (IUPAC)"),
    ("symbole_chimique", "rubidium"): Fait("Rb", CAT_PHYSIQUE, "tableau périodique (IUPAC)"),
    ("symbole_chimique", "molybdene"): Fait("Mo", CAT_PHYSIQUE, "tableau périodique (IUPAC)"),
    ("symbole_chimique", "iridium"): Fait("Ir", CAT_PHYSIQUE, "tableau périodique (IUPAC)"),

    # cat 3 — faits passés figés (dates d'événements au noyau factuel incontesté)
    ("annee", "revolution francaise"): Fait("1789 (prise de la Bastille : 14 juillet 1789)", CAT_PASSE, "histoire (noyau factuel)"),
    ("annee", "premier pas sur la lune"): Fait("1969 (Apollo 11, 20-21 juillet)", CAT_PASSE, "histoire (noyau factuel)"),
    ("annee", "chute du mur de berlin"): Fait("1989 (9 novembre)", CAT_PASSE, "histoire (noyau factuel)"),
    ("annee", "declaration independance etats unis"): Fait("1776 (4 juillet)", CAT_PASSE, "histoire (noyau factuel)"),
    ("annee", "premiere guerre mondiale"): Fait("1914-1918", CAT_PASSE, "histoire (noyau factuel)"),
    ("annee", "seconde guerre mondiale"): Fait("1939-1945", CAT_PASSE, "histoire (noyau factuel)"),
    # Dates historiques — extension lot #3 (noyau factuel incontesté, daté à l'année).
    ("annee", "decouverte de l amerique"): Fait("1492 (Christophe Colomb)", CAT_PASSE, "histoire (noyau factuel)"),
    ("annee", "bataille de waterloo"): Fait("1815 (18 juin)", CAT_PASSE, "histoire (noyau factuel)"),
    ("annee", "naufrage du titanic"): Fait("1912 (15 avril)", CAT_PASSE, "histoire (noyau factuel)"),
    ("annee", "revolution russe"): Fait("1917", CAT_PASSE, "histoire (noyau factuel)"),
    ("annee", "creation de l onu"): Fait("1945 (24 octobre)", CAT_PASSE, "histoire (noyau factuel)"),
    ("annee", "chute de l urss"): Fait("1991", CAT_PASSE, "histoire (noyau factuel)"),
    ("annee", "attentats du 11 septembre"): Fait("2001 (11 septembre)", CAT_PASSE, "histoire (noyau factuel)"),

    # cat 4 — convention/langue (pluriels irréguliers, unités, définitions de genre)
    ("pluriel", "cheval"): Fait("chevaux", CAT_CONVENTION, "orthographe française (pluriel en -aux)"),
    ("pluriel", "travail"): Fait("travaux", CAT_CONVENTION, "orthographe française (pluriel en -aux)"),
    ("pluriel", "oeil"): Fait("yeux", CAT_CONVENTION, "orthographe française (pluriel irrégulier)"),
    # Pluriels — extension (règles -oux / -aux / irréguliers, stables).
    ("pluriel", "bijou"): Fait("bijoux", CAT_CONVENTION, "orthographe française (pluriel en -oux)"),
    ("pluriel", "caillou"): Fait("cailloux", CAT_CONVENTION, "orthographe française (pluriel en -oux)"),
    ("pluriel", "chou"): Fait("choux", CAT_CONVENTION, "orthographe française (pluriel en -oux)"),
    ("pluriel", "genou"): Fait("genoux", CAT_CONVENTION, "orthographe française (pluriel en -oux)"),
    ("pluriel", "hibou"): Fait("hiboux", CAT_CONVENTION, "orthographe française (pluriel en -oux)"),
    ("pluriel", "pou"): Fait("poux", CAT_CONVENTION, "orthographe française (pluriel en -oux)"),
    ("pluriel", "journal"): Fait("journaux", CAT_CONVENTION, "orthographe française (pluriel en -aux)"),
    ("pluriel", "vitrail"): Fait("vitraux", CAT_CONVENTION, "orthographe française (pluriel en -aux)"),
    ("pluriel", "bail"): Fait("baux", CAT_CONVENTION, "orthographe française (pluriel en -aux)"),
    ("pluriel", "ciel"): Fait("cieux", CAT_CONVENTION, "orthographe française (pluriel irrégulier)"),
    ("pluriel", "monsieur"): Fait("messieurs", CAT_CONVENTION, "orthographe française (pluriel irrégulier)"),
    ("pluriel", "madame"): Fait("mesdames", CAT_CONVENTION, "orthographe française (pluriel irrégulier)"),
    ("unite", "metre"): Fait("unité SI de longueur (symbole m)", CAT_CONVENTION, "Système international (SI)"),
    ("unite", "kilogramme"): Fait("unité SI de masse (symbole kg)", CAT_CONVENTION, "Système international (SI)"),
    # Unités SI — extension (7 unités de base + dérivées usuelles, stables).
    ("unite", "seconde"): Fait("unité SI de temps (symbole s)", CAT_CONVENTION, "Système international (SI)"),
    ("unite", "ampere"): Fait("unité SI de courant électrique (symbole A)", CAT_CONVENTION, "Système international (SI)"),
    ("unite", "kelvin"): Fait("unité SI de température thermodynamique (symbole K)", CAT_CONVENTION, "Système international (SI)"),
    ("unite", "mole"): Fait("unité SI de quantité de matière (symbole mol)", CAT_CONVENTION, "Système international (SI)"),
    ("unite", "candela"): Fait("unité SI d'intensité lumineuse (symbole cd)", CAT_CONVENTION, "Système international (SI)"),
    ("definition", "capitale"): Fait("ville où siègent le gouvernement et le pouvoir de l'État", CAT_CONVENTION, "définition (Wiktionnaire)"),
}


_ARTICLES = {"de", "du", "des", "d", "la", "le", "les", "l"}


def _sans_articles(entite: str) -> str:
    """Retire les déterminants en tête (« la france » -> « france ») pour fiabiliser le lookup."""
    mots = normalise(entite).split()
    while mots and mots[0] in _ARTICLES:
        mots = mots[1:]
    return " ".join(mots)


def cherche(relation: str, entite: str) -> Fait | None:
    """Lookup EXACT sur clé normalisée. Le cœur sound : présent -> Fait, absent -> None (jamais de faux)."""
    return FAITS.get((relation, _sans_articles(entite)))


# --- Gabarits NL -> (relation, entité). Petits, sûrs ; un non-match = HORS (pas de devinette). ---
# Chaque gabarit : (regex sur question normalisée, relation, indice du groupe entité ou "" si fixe).
_GABARITS = [
    (re.compile(r"\bcapitale (?:de |du |des |d |de la |de l )?(.+)$"), "capitale", 1),
    (re.compile(r"\bpluriel (?:de |du |d )?(.+)$"), "pluriel", 1),
    (re.compile(r"\b(?:definition|definir|que veut dire|sens) (?:de |du |d |le mot )?(.+)$"), "definition", 1),
    (re.compile(r"\bvitesse de la lumiere\b"), "vitesse_lumiere", 0),
    (re.compile(r"\b(?:temperature d ebullition|point d ebullition|ebullition) (?:de l )?eau\b"), "ebullition_eau", 0),
    # ⚠ « eau » OBLIGATOIRE : « point de FUSION » seul désigne n'importe quel corps (« point de fusion du FER »
    # = 1538 °C, à ne PAS confondre — régression vécue 2026-07-08).
    (re.compile(r"\b(?:temperature de (?:congelation|fusion|solidification)|point de (?:congelation|fusion))"
                r" (?:de l )?eau\b"
                r"|\b(?:a\s+)?quelle temperature (?:l )?eau (?:gele|congele|se solidifie|se transforme en glace)\b"
                r"|\beau (?:gele|congele) a\b"), "congelation_eau", 0),
    (re.compile(r"\bzero absolu\b"), "zero_absolu", 0),
    (re.compile(r"\bsymbole (?:chimique )?(?:de l |de la |du |de )?(.+)$"), "symbole_chimique", 1),
    (re.compile(r"\bunite (?:de l |de la |du |de )?(.+)$"), "unite", 1),
    (re.compile(r"\b(?:en quelle annee|quelle annee|date)\b.*?\b(revolution francaise|premier pas sur la lune|chute du mur de berlin|declaration independance etats unis|premiere guerre mondiale|seconde guerre mondiale|decouverte de l amerique|bataille de waterloo|naufrage du titanic|revolution russe|creation de l onu|chute de l urss|attentats du 11 septembre)\b"), "annee", 1),
]


def repond_nl(question: str):
    """(statut, Fait|None). Extrait (relation, entité) d'un gabarit sûr puis lookup. Non-match/absent -> (HORS, None)."""
    q = normalise(question)
    for rx, relation, gi in _GABARITS:
        m = rx.search(q)
        if not m:
            continue
        entite = m.group(gi) if gi else ""
        f = cherche(relation, entite)
        if f is not None:
            return (VERIFIE, f)
        return (HORS, None)   # gabarit reconnu mais entité inconnue : HORS honnête (jamais inventer)
    return (HORS, None)


if __name__ == "__main__":
    print("=== BASE DE FAITS VÉRIFIÉS (lookup-jugé, HORS si inconnu) ===\n")
    essais = [
        "Quelle est la capitale de la France ?",
        "capitale du Japon",
        "Quel est le pluriel de cheval ?",
        "Quelle est la vitesse de la lumière ?",
        "En quelle année a eu lieu la révolution française ?",
        "Quelle est la capitale de la Mongolie ?",   # absent -> HORS honnête
        "Quel est ton plat préféré ?",               # hors gabarit -> HORS
    ]
    for q in essais:
        statut, f = repond_nl(q)
        if statut == VERIFIE:
            print(f"  [VÉRIFIÉ {f.categorie:10s}] {q}\n      -> {f.valeur}   (source : {f.source})")
        else:
            print(f"  [HORS    {'':10s}] {q}\n      -> je n'ai pas ce fait vérifié (pas de devinette)")
