"""
FORMATS LOCAUX — conventions de date/nombre/monnaie/semaine par pays (CLDR/ISO).

Même posture FAUX=0 que `physique` / `geometries_non_euclidiennes` (la convention PUBLIÉE juge, jamais un faux) :
  • Le MÉCANISME est un CATALOGUE FERMÉ de conventions publiées (Unicode CLDR ; ISO 8601 pour la date
    non ambiguë), PAS une heuristique : chaque entrée (ordre de date, séparateur décimal, séparateur de
    milliers, groupement des chiffres, symbole monétaire et sa position, format d'heure 12/24 h, premier
    jour de semaine) est recopiée de la convention de référence, pays par pays.
  • Pays couverts : France, Allemagne, Royaume-Uni, États-Unis, Canada (anglophone), Japon, Chine, Suisse,
    Inde, Brésil, Russie. TOUT AUTRE PAYS -> ValueError : jamais un format « par défaut » deviné — c'est
    précisément l'erreur (03/04 = 3 avril ou 4 mars ?) que ce module existe pour empêcher.
  • PIÈGES RÉELS traités :
      – l'INDE groupe par 2 après le premier groupe de 3 (système lakh/crore) : 1234567 -> « 12,34,567 »
        (le groupement occidental « 1,234,567 » serait FAUX) ;
      – la SUISSE sépare les milliers par l'APOSTROPHE : 1000000 -> « 1'000'000 » ;
      – l'ISO 8601 (AAAA-MM-JJ) est LA SEULE écriture non ambiguë : exposée via FORMAT_ISO_8601 /
        formate_date_iso ; la fonction date_est_ambigue expose l'ambiguïté d'un texte de date entre pays.
  • parse_nombre est l'INVERSE STRICT de formate_nombre : groupement VÉRIFIÉ (un « 1,23 » aux États-Unis
    n'est ni un millier ni un décimal valide -> ValueError), boucle fermée parse(formate(x)) == x.
  • ABSTENTIONS STRUCTURELLES (ValueError) : pays hors catalogue ; date invalide (calendrier grégorien,
    années bissextiles comprises) ; texte non parsable ou groupement incorrect ; bool/str/NaN/±inf ;
    flottant dont la représentation exige la notation scientifique (round-trip exact impossible à garantir).

GARANTIES (vérifiées en adverse par `valide_formats_locaux.py`) :
  - ancres CLDR en dur (France ',', États-Unis '.', Inde « 12,34,567 », Suisse « 1'000'000 », Japon
    AAAA/MM/JJ 24 h, etc.) ;
  - boucle fermée parse_nombre∘formate_nombre = identité sur 200+ valeurs × 11 pays ;
  - « 03/04/2024 » déclaré AMBIGU (France = 3 avril, États-Unis = 4 mars) ; « 2024-04-03 » (ISO) non ambigu ;
  - 29/02 refusé hors année bissextile (2023, 2100) et accepté en 2024, 2000 ;
  - types invalides (bool, str, NaN, ±inf, mauvaise arité) -> ValueError ;
  - déterministe ; conservateur (faux négatif/abstention toléré, faux POSITIF interdit).

Toutes les fonctions sont PURES et déterministes ; le module n'importe que `math` et `unicodedata` (stdlib).
"""
from __future__ import annotations

import math
import unicodedata

SOURCE = "Unicode CLDR (patterns date/heure/nombre + weekData par territoire) + ISO 8601 (date non ambiguë)"

# Format ISO 8601 : la SEULE écriture de date non ambiguë entre tous les pays du catalogue.
FORMAT_ISO_8601 = "AAAA-MM-JJ"

# Espaces insécables acceptés en lecture là où la convention sépare les milliers par une espace
# (CLDR moderne emploie l'espace fine insécable U+202F pour fr ; U+00A0 reste l'espace insécable classique).
_ESPACES = (" ", " ", " ")
_APOSTROPHES = ("'", "’")  # de-CH : CLDR publie U+2019, l'ASCII « ' » est l'écriture usuelle

# ── CATALOGUE (conventions publiées, une entrée par pays — closed-set) ─────────────────────────────────────────
# ordre : 'JMA' (JJ/MM/AAAA), 'MJA' (MM/JJ/AAAA), 'AMJ' (AAAA-MM-JJ ou AAAA/MM/JJ)
# groupement : 'standard' (par 3) ou 'inde' (3 puis 2 : lakh/crore)
# monnaie : (symbole, 'avant' | 'apres')
_CATALOGUE = {
    "france": {
        "nom": "France", "ordre": "JMA", "sep_date": "/",
        "sep_dec": ",", "sep_mil": " ", "equiv_mil": _ESPACES, "groupement": "standard",
        "monnaie": ("€", "apres"), "heure": 24, "premier_jour": "lundi",
    },
    "allemagne": {
        "nom": "Allemagne", "ordre": "JMA", "sep_date": ".",
        "sep_dec": ",", "sep_mil": ".", "equiv_mil": (".",), "groupement": "standard",
        "monnaie": ("€", "apres"), "heure": 24, "premier_jour": "lundi",
    },
    "royaume-uni": {
        "nom": "Royaume-Uni", "ordre": "JMA", "sep_date": "/",
        "sep_dec": ".", "sep_mil": ",", "equiv_mil": (",",), "groupement": "standard",
        "monnaie": ("£", "avant"), "heure": 24, "premier_jour": "lundi",
    },
    "etats-unis": {
        "nom": "États-Unis", "ordre": "MJA", "sep_date": "/",
        "sep_dec": ".", "sep_mil": ",", "equiv_mil": (",",), "groupement": "standard",
        "monnaie": ("$", "avant"), "heure": 12, "premier_jour": "dimanche",
    },
    "canada": {  # Canada ANGLOPHONE (en-CA) : date courte ISO-like yyyy-MM-dd (CLDR)
        "nom": "Canada", "ordre": "AMJ", "sep_date": "-",
        "sep_dec": ".", "sep_mil": ",", "equiv_mil": (",",), "groupement": "standard",
        "monnaie": ("$", "avant"), "heure": 12, "premier_jour": "dimanche",
    },
    "japon": {
        "nom": "Japon", "ordre": "AMJ", "sep_date": "/",
        "sep_dec": ".", "sep_mil": ",", "equiv_mil": (",",), "groupement": "standard",
        "monnaie": ("¥", "avant"), "heure": 24, "premier_jour": "dimanche",
    },
    "chine": {  # CLDR zh : heure courte « ah:mm » (12 h avec période du jour)
        "nom": "Chine", "ordre": "AMJ", "sep_date": "/",
        "sep_dec": ".", "sep_mil": ",", "equiv_mil": (",",), "groupement": "standard",
        "monnaie": ("¥", "avant"), "heure": 12, "premier_jour": "dimanche",
    },
    "suisse": {  # PIÈGE RÉEL : apostrophe comme séparateur de milliers (1'000'000)
        "nom": "Suisse", "ordre": "JMA", "sep_date": ".",
        "sep_dec": ".", "sep_mil": "'", "equiv_mil": _APOSTROPHES, "groupement": "standard",
        "monnaie": ("CHF", "avant"), "heure": 24, "premier_jour": "lundi",
    },
    "inde": {  # PIÈGE RÉEL : lakh/crore — 3 chiffres à droite puis groupes de 2 (12,34,567)
        "nom": "Inde", "ordre": "JMA", "sep_date": "/",
        "sep_dec": ".", "sep_mil": ",", "equiv_mil": (",",), "groupement": "inde",
        "monnaie": ("₹", "avant"), "heure": 12, "premier_jour": "dimanche",
    },
    "bresil": {
        "nom": "Brésil", "ordre": "JMA", "sep_date": "/",
        "sep_dec": ",", "sep_mil": ".", "equiv_mil": (".",), "groupement": "standard",
        "monnaie": ("R$", "avant"), "heure": 24, "premier_jour": "dimanche",
    },
    "russie": {
        "nom": "Russie", "ordre": "JMA", "sep_date": ".",
        "sep_dec": ",", "sep_mil": " ", "equiv_mil": _ESPACES, "groupement": "standard",
        "monnaie": ("₽", "apres"), "heure": 24, "premier_jour": "lundi",
    },
}

_PATRONS_DATE = {("JMA", "/"): "JJ/MM/AAAA", ("JMA", "."): "JJ.MM.AAAA",
                 ("MJA", "/"): "MM/JJ/AAAA", ("AMJ", "-"): "AAAA-MM-JJ", ("AMJ", "/"): "AAAA/MM/JJ"}

_JOURS_PAR_MOIS = (31, 28, 31, 30, 31, 30, 31, 31, 30, 31, 30, 31)


# ── VALIDATION D'ENTRÉE ────────────────────────────────────────────────────────────────────────────────────────
def _normalise(nom: str) -> str:
    """Minuscule + accents retirés (é->e) : « États-Unis » et « etats-unis » désignent la même entrée."""
    decompose = unicodedata.normalize("NFD", nom)
    return "".join(c for c in decompose if not unicodedata.combining(c)).lower().strip()


def _exige_pays(pays) -> dict:
    """Entrée du catalogue, ou ValueError (closed-set : JAMAIS un format deviné pour un pays inconnu)."""
    if not isinstance(pays, str) or not pays:
        raise ValueError("pays invalide : une chaîne non vide est requise")
    cle = _normalise(pays)
    if cle not in _CATALOGUE:
        connus = ", ".join(sorted(e["nom"] for e in _CATALOGUE.values()))
        raise ValueError(f"pays hors catalogue : {pays!r} (couverts : {connus}) — abstention, jamais un défaut deviné")
    return _CATALOGUE[cle]


def _exige_entier(x, nom: str, mini: int, maxi: int) -> int:
    """Entier strict (bool REFUSÉ : True n'est pas 1) dans [mini, maxi]."""
    if not isinstance(x, int) or isinstance(x, bool) or not (mini <= x <= maxi):
        raise ValueError(f"{nom} invalide : un entier dans [{mini}, {maxi}] est requis")
    return x


def _est_bissextile(annee: int) -> bool:
    """Règle grégorienne exacte : divisible par 4, sauf siècles non divisibles par 400."""
    return annee % 4 == 0 and (annee % 100 != 0 or annee % 400 == 0)


def _exige_date(annee, mois, jour) -> tuple:
    annee = _exige_entier(annee, "annee", 1, 9999)
    mois = _exige_entier(mois, "mois", 1, 12)
    maxi = _JOURS_PAR_MOIS[mois - 1] + (1 if mois == 2 and _est_bissextile(annee) else 0)
    jour = _exige_entier(jour, "jour", 1, maxi)
    return (annee, mois, jour)


# ── CATALOGUE : ACCESSEURS ─────────────────────────────────────────────────────────────────────────────────────
def format_date(pays: str) -> str:
    """Patron de date du pays : 'JJ/MM/AAAA', 'JJ.MM.AAAA', 'MM/JJ/AAAA', 'AAAA-MM-JJ' ou 'AAAA/MM/JJ'."""
    e = _exige_pays(pays)
    return _PATRONS_DATE[(e["ordre"], e["sep_date"])]


def separateur_decimal(pays: str) -> str:
    """Séparateur décimal du pays (CLDR) : ',' ou '.'."""
    return _exige_pays(pays)["sep_dec"]


def separateur_milliers(pays: str) -> str:
    """Séparateur de milliers du pays (CLDR) : ',', '.', espace insécable ou apostrophe (Suisse)."""
    return _exige_pays(pays)["sep_mil"]


def symbole_monetaire(pays: str) -> tuple:
    """(symbole, position) — position ∈ {'avant', 'apres'} par rapport au montant."""
    return _exige_pays(pays)["monnaie"]


def format_heure(pays: str) -> int:
    """12 ou 24 : cycle horaire du format court CLDR du pays."""
    return _exige_pays(pays)["heure"]


def premier_jour_semaine(pays: str) -> str:
    """'lundi' ou 'dimanche' (CLDR weekData, firstDay du territoire)."""
    return _exige_pays(pays)["premier_jour"]


# ── NOMBRES : formate_nombre / parse_nombre (inverses stricts) ─────────────────────────────────────────────────
def _groupe(chiffres: str, groupement: str) -> list:
    """Découpe une suite de chiffres en groupes, de droite à gauche.

    'standard' : groupes de 3. 'inde' : 3 à droite puis groupes de 2 (lakh/crore)."""
    groupes = []
    i = len(chiffres)
    taille = 3
    while i > 0:
        groupes.append(chiffres[max(0, i - taille):i])
        i -= taille
        if groupement == "inde":
            taille = 2
    return list(reversed(groupes))


def _groupes_valides(groupes: list, groupement: str) -> bool:
    """Vérifie le groupement (l'INVERSE de _groupe) : refuse '1,234,567' en Inde, '1,23' partout."""
    if any(not g or not g.isdigit() for g in groupes):
        return False
    if groupement == "inde":
        if len(groupes[-1]) != 3:
            return False
        if any(len(g) != 2 for g in groupes[1:-1]):
            return False
        return 1 <= len(groupes[0]) <= (2 if len(groupes) > 1 else 3)
    if any(len(g) != 3 for g in groupes[1:]):
        return False
    return 1 <= len(groupes[0]) <= 3


def formate_nombre(valeur, pays: str) -> str:
    """Écrit `valeur` (int ou float fini, bool REFUSÉ) selon la convention du pays.

    Le flottant est restitué via sa représentation décimale EXACTE la plus courte (repr Python, round-trip
    garanti) ; s'il exigerait la notation scientifique (|x| ≥ 1e16 ou trop petit) -> ValueError (abstention :
    on ne garantit plus l'inversion exacte). Pays hors catalogue -> ValueError."""
    e = _exige_pays(pays)
    if isinstance(valeur, bool) or not isinstance(valeur, (int, float)):
        raise ValueError("valeur invalide : un int ou un float est requis (bool refusé : True n'est pas 1)")
    if isinstance(valeur, float) and not math.isfinite(valeur):
        raise ValueError("valeur invalide : NaN/±inf refusés")
    signe = "-" if valeur < 0 else ""
    if isinstance(valeur, int):
        entier, frac = str(abs(valeur)), None
    else:
        texte = repr(abs(valeur))
        if "e" in texte or "E" in texte:
            raise ValueError("flottant en notation scientifique : hors périmètre (round-trip exact non garanti)")
        entier, frac = texte.split(".")
    corps = e["sep_mil"].join(_groupe(entier, e["groupement"]))
    if frac is not None:
        corps += e["sep_dec"] + frac
    return signe + corps


def parse_nombre(texte: str, pays: str) -> float:
    """INVERSE strict de formate_nombre : relit un nombre écrit selon la convention du pays.

    Le groupement des milliers est VÉRIFIÉ (s'il y a des séparateurs, ils doivent être exactement aux bonnes
    places — « 1,23 » aux États-Unis n'est ni un millier ni un décimal valide -> ValueError). Une suite de
    chiffres sans séparateur est acceptée. Texte non parsable -> ValueError (jamais une valeur devinée)."""
    e = _exige_pays(pays)
    if not isinstance(texte, str) or not texte:
        raise ValueError("texte invalide : une chaîne non vide est requise")
    if texte != texte.strip():
        raise ValueError("texte invalide : espaces de tête/queue refusés (écriture stricte)")
    corps = texte
    signe = 1.0
    if corps.startswith("-"):
        signe, corps = -1.0, corps[1:]
    if not corps:
        raise ValueError("texte invalide : signe sans chiffres")
    sep_dec = e["sep_dec"]
    frac = ""
    if corps.count(sep_dec) > 1:
        raise ValueError(f"texte invalide : séparateur décimal {sep_dec!r} présent plusieurs fois")
    if sep_dec in corps:
        corps, frac = corps.split(sep_dec)
        if not frac or not frac.isdigit():
            raise ValueError("partie décimale invalide : des chiffres sont requis après le séparateur décimal")
    if not corps:
        raise ValueError("partie entière vide : écriture stricte requise (ex. 0,5 et non ,5)")
    canonique = corps
    for equiv in e["equiv_mil"]:
        canonique = canonique.replace(equiv, "\x00")
    if "\x00" in canonique:
        groupes = canonique.split("\x00")
        if not _groupes_valides(groupes, e["groupement"]):
            raise ValueError(f"groupement des milliers invalide pour {e['nom']} : {texte!r}")
        chiffres = "".join(groupes)
    elif corps.isdigit():
        chiffres = corps
    else:
        raise ValueError(f"texte non parsable comme nombre ({e['nom']}) : {texte!r}")
    return signe * float(chiffres + ("." + frac if frac else ""))


# ── DATES : formate_date / parse_date / ambiguïté ──────────────────────────────────────────────────────────────
def formate_date(annee: int, mois: int, jour: int, pays: str) -> str:
    """Écrit la date selon l'ordre du pays (jour/mois sur 2 chiffres, année sur 4).

    Date invalide (30 février, 29/02 hors bissextile, mois 13…) -> ValueError. Pays inconnu -> ValueError."""
    e = _exige_pays(pays)
    annee, mois, jour = _exige_date(annee, mois, jour)
    a, m, j, s = f"{annee:04d}", f"{mois:02d}", f"{jour:02d}", e["sep_date"]
    if e["ordre"] == "JMA":
        return f"{j}{s}{m}{s}{a}"
    if e["ordre"] == "MJA":
        return f"{m}{s}{j}{s}{a}"
    return f"{a}{s}{m}{s}{j}"


def formate_date_iso(annee: int, mois: int, jour: int) -> str:
    """ISO 8601 (AAAA-MM-JJ) : la SEULE écriture non ambiguë entre tous les pays du catalogue."""
    annee, mois, jour = _exige_date(annee, mois, jour)
    return f"{annee:04d}-{mois:02d}-{jour:02d}"


def parse_date(texte: str, pays: str) -> tuple:
    """Relit une date écrite STRICTEMENT au format du pays -> (annee, mois, jour).

    Longueurs exigées : jour/mois sur 2 chiffres, année sur 4 (l'écriture de formate_date). Texte non
    conforme ou date invalide -> ValueError."""
    e = _exige_pays(pays)
    if not isinstance(texte, str) or not texte:
        raise ValueError("texte invalide : une chaîne non vide est requise")
    parts = texte.split(e["sep_date"])
    if len(parts) != 3 or any(not p.isdigit() for p in parts):
        raise ValueError(f"date non conforme au format {format_date(pays)} : {texte!r}")
    longueurs = {"JMA": (2, 2, 4), "MJA": (2, 2, 4), "AMJ": (4, 2, 2)}[e["ordre"]]
    if tuple(len(p) for p in parts) != longueurs:
        raise ValueError(f"date non conforme au format {format_date(pays)} : {texte!r}")
    if e["ordre"] == "JMA":
        jour, mois, annee = (int(p) for p in parts)
    elif e["ordre"] == "MJA":
        mois, jour, annee = (int(p) for p in parts)
    else:
        annee, mois, jour = (int(p) for p in parts)
    return _exige_date(annee, mois, jour)


def interpretations_date(texte: str) -> dict:
    """Toutes les lectures possibles de `texte` : {nom du pays: (annee, mois, jour)}.

    C'est la fonction qui EXPOSE l'ambiguïté : « 03/04/2024 » se lit (2024, 4, 3) en France
    mais (2024, 3, 4) aux États-Unis. Aucune lecture possible -> ValueError (jamais un vide silencieux)."""
    if not isinstance(texte, str) or not texte:
        raise ValueError("texte invalide : une chaîne non vide est requise")
    lectures = {}
    for e in _CATALOGUE.values():
        try:
            lectures[e["nom"]] = parse_date(texte, e["nom"])
        except ValueError:
            continue
    if not lectures:
        raise ValueError(f"aucun pays du catalogue ne lit cette date : {texte!r}")
    return lectures


def date_est_ambigue(texte: str) -> bool:
    """True ssi `texte` désigne DES DATES DIFFÉRENTES selon le pays (ex. « 03/04/2024 »).

    Une écriture lue par plusieurs pays mais donnant LA MÊME date (ex. « 31/12/2024 », « 2024/04/03 »)
    n'est PAS ambiguë. Illisible partout -> ValueError."""
    return len(set(interpretations_date(texte).values())) >= 2
