"""
CALENDRIERS ET FUSEAUX HORAIRES — conversions EXACTES via le JOUR JULIEN (JDN), arithmétique ENTIÈRE pure.

Même posture FAUX=0 que `physique` / `geometries_non_euclidiennes` (la convention publiée juge, jamais un faux) :
  • Le MÉCANISME est un ALGORITHME EXACT publié, pas une corrélation :
      – Grégorien <-> JDN : algorithme de Fliegel & Van Flandern (1968), entièrement en divisions entières
        (aucun flottant, aucune perte). Le JDN est le numéro du jour julien astronomique (jour commençant à
        midi UT) ; JDN(1er janvier 2000 grégorien) = 2451545 (époque J2000, valeur universellement tabulée).
      – Julien <-> JDN : même famille d'algorithmes, sans les termes séculaires (pas de règle des siècles).
        Règle bissextile PROLEPTIQUE régulière (année divisible par 4) : les années bissextiles réellement
        appliquées avant l'an 8 de notre ère furent irrégulières — hors périmètre, on ne le prétend pas.
      – Hijri <-> JDN : calendrier islamique TABULAIRE (cycle arithmétique de 30 ans = 10631 jours,
        11 années abondantes {2,5,7,10,13,16,18,21,24,26,29}, époque civile = vendredi 16 juillet 622 julien
        = JDN 1948440). AVERTISSEMENT HONNÊTE : le calendrier islamique RÉEL est OBSERVATIONNEL (croissant
        lunaire visible) et peut différer de ±1 jour (parfois 2) du tabulaire selon le lieu et l'autorité ;
        ce module calcule le TABULAIRE et ne prétend PAS prédire l'observationnel.
      – Jour de la semaine : jdn % 7 == 0 <=> lundi (propriété arithmétique du JDN, invariante).
      – Écart julien/grégorien : nombre de jours à AJOUTER à une date julienne pour obtenir la grégorienne
        (10 jours en 1582 lors de la réforme, 13 depuis mars 1900) ; calculé comme différence de JDN sur une
        même date nominale, valable du 1er mars de l'année au 28/29 février suivant (l'écart saute au
        29 février julien des années séculaires).
  • FUSEAUX HORAIRES : uniquement des fuseaux NOMMÉS À OFFSET FIXE (« UTC », « UTC+1 », « UTC+5:30 »…),
    dont le nom EST l'offset — aucune ambiguïté possible. Les noms régionaux (« CET », « EST »…) sont
    REFUSÉS : ils dépendent de l'heure d'été et des lois locales.
  • ABSTENTION CAPITALE — heure d'été (DST) : les règles changent par pays ET par année (une base tzdata
    est nécessaire) ; heure_ete(...) lève TOUJOURS ValueError. Jamais une heure d'été devinée.

GARANTIES (vérifiées en adverse par `valide_calendriers.py`) :
  - dates invalides (30 février, mois 13, jour 0, 29 février non bissextile) -> ValueError ;
  - années hors [1, 9999] (grégorien/julien) ou hors [1, 9999] AH (hijri) -> ValueError ;
  - JDN hors du domaine inversible du calendrier visé -> ValueError ;
  - types invalides (bool, float, str, NaN, inf, mauvaise arité) -> ValueError (True n'est PAS 1) ;
  - fuseau inconnu ou régional -> ValueError ; heure/offset hors bornes -> ValueError ;
  - heure_ete(...) -> ValueError inconditionnel (abstention structurelle) ;
  - déterministe ; arithmétique entière EXACTE partout (aucun flottant dans les conversions).

Toutes les fonctions sont PURES et déterministes ; le module n'importe RIEN (stdlib pure, zéro dépendance).
"""
from __future__ import annotations

SOURCE = (
    "Fliegel & Van Flandern (1968), Communications of the ACM 11(10) p.657 (grégorien<->JDN entier) ; "
    "Explanatory Supplement to the Astronomical Almanac (calendriers julien et islamique tabulaire, "
    "cycle 30 ans = 10631 jours, époque civile JDN 1948440)"
)

# Années abondantes du cycle tabulaire de 30 ans (convention civile la plus répandue, dite « type II »).
ANNEES_ABONDANTES_HIJRI = (2, 5, 7, 10, 13, 16, 18, 21, 24, 26, 29)

_JOURS_SEMAINE = ("lundi", "mardi", "mercredi", "jeudi", "vendredi", "samedi", "dimanche")
_MOIS_31_28 = (31, 28, 31, 30, 31, 30, 31, 31, 30, 31, 30, 31)

_ANNEE_MIN = 1
_ANNEE_MAX = 9999

# Fuseaux à offset FIXE uniquement : le NOM encode l'offset (aucun fait extérieur à trahir).
# Offsets en MINUTES. Couvre UTC-12..UTC+14 + les offsets fractionnaires réellement en usage (fixes).
_FUSEAUX: dict[str, int] = {"UTC": 0, "UTC+0": 0, "UTC-0": 0}
for _h in range(1, 15):
    _FUSEAUX[f"UTC+{_h}"] = 60 * _h
for _h in range(1, 13):
    _FUSEAUX[f"UTC-{_h}"] = -60 * _h
_FUSEAUX.update({
    "UTC+3:30": 210, "UTC+4:30": 270, "UTC+5:30": 330, "UTC+5:45": 345,
    "UTC+6:30": 390, "UTC+8:45": 525, "UTC+9:30": 570, "UTC+10:30": 630,
    "UTC+12:45": 765, "UTC-3:30": -210, "UTC-9:30": -570,
})
del _h


# ── VALIDATION D'ENTRÉE ──────────────────────────────────────────────────────────────────────────────────────
def _exige_entier(x, nom: str) -> int:
    """Entier strict : bool REFUSÉ (True n'est pas 1), float/str/None REFUSÉS."""
    if isinstance(x, bool) or not isinstance(x, int):
        raise ValueError(f"{nom} invalide : un entier (int) est requis — bool/float/str refusés")
    return x


def _exige_annee(a, nom: str = "annee") -> int:
    a = _exige_entier(a, nom)
    if not (_ANNEE_MIN <= a <= _ANNEE_MAX):
        raise ValueError(f"{nom} hors domaine : [{_ANNEE_MIN}, {_ANNEE_MAX}] requis (proleptique borné)")
    return a


def _exige_date(a, m, j, jours_du_mois) -> tuple[int, int, int]:
    """Valide (annee, mois, jour) contre les longueurs de mois données par jours_du_mois(a, m)."""
    a = _exige_annee(a)
    m = _exige_entier(m, "mois")
    if not (1 <= m <= 12):
        raise ValueError("mois invalide : 1..12 requis (mois 13 n'existe pas)")
    j = _exige_entier(j, "jour")
    maxi = jours_du_mois(a, m)
    if not (1 <= j <= maxi):
        raise ValueError(f"jour invalide : 1..{maxi} requis pour ce mois de cette année")
    return a, m, j


# ── ANNÉES BISSEXTILES (règles DISTINCTES) ──────────────────────────────────────────────────────────────────
def est_bissextile_gregorien(a: int) -> bool:
    """Grégorien : divisible par 4, SAUF les siècles non divisibles par 400 (1900 non, 2000 oui)."""
    a = _exige_annee(a)
    return a % 4 == 0 and (a % 100 != 0 or a % 400 == 0)


def est_bissextile_julien(a: int) -> bool:
    """Julien proleptique régulier : divisible par 4 (1900 EST bissextile en julien)."""
    a = _exige_annee(a)
    return a % 4 == 0


def _jours_mois_gregorien(a: int, m: int) -> int:
    if m == 2 and est_bissextile_gregorien(a):
        return 29
    return _MOIS_31_28[m - 1]


def _jours_mois_julien(a: int, m: int) -> int:
    if m == 2 and est_bissextile_julien(a):
        return 29
    return _MOIS_31_28[m - 1]


# ── GRÉGORIEN <-> JDN (Fliegel & Van Flandern, entier pur) ──────────────────────────────────────────────────
def gregorien_vers_jdn(a: int, m: int, j: int) -> int:
    """JDN du jour grégorien (proleptique) (a, m, j). Date invalide -> ValueError."""
    a, m, j = _exige_date(a, m, j, _jours_mois_gregorien)
    x = (14 - m) // 12
    y = a + 4800 - x
    mm = m + 12 * x - 3
    return j + (153 * mm + 2) // 5 + 365 * y + y // 4 - y // 100 + y // 400 - 32045


def jdn_vers_gregorien(jdn: int) -> tuple[int, int, int]:
    """(annee, mois, jour) grégoriens du JDN. Inverse exact de gregorien_vers_jdn sur [1..9999]."""
    jdn = _exige_entier(jdn, "jdn")
    if not (_JDN_GREG_MIN <= jdn <= _JDN_GREG_MAX):
        raise ValueError(f"jdn hors domaine grégorien inversible : [{_JDN_GREG_MIN}, {_JDN_GREG_MAX}]")
    a = jdn + 32044
    b = (4 * a + 3) // 146097
    c = a - (146097 * b) // 4
    d = (4 * c + 3) // 1461
    e = c - (1461 * d) // 4
    m = (5 * e + 2) // 153
    jour = e - (153 * m + 2) // 5 + 1
    mois = m + 3 - 12 * (m // 10)
    annee = 100 * b + d - 4800 + m // 10
    return (annee, mois, jour)


# ── JULIEN <-> JDN ──────────────────────────────────────────────────────────────────────────────────────────
def julien_vers_jdn(a: int, m: int, j: int) -> int:
    """JDN du jour julien (proleptique régulier) (a, m, j). Date invalide -> ValueError."""
    a, m, j = _exige_date(a, m, j, _jours_mois_julien)
    x = (14 - m) // 12
    y = a + 4800 - x
    mm = m + 12 * x - 3
    return j + (153 * mm + 2) // 5 + 365 * y + y // 4 - 32083


def jdn_vers_julien(jdn: int) -> tuple[int, int, int]:
    """(annee, mois, jour) juliens du JDN. Inverse exact de julien_vers_jdn sur [1..9999]."""
    jdn = _exige_entier(jdn, "jdn")
    if not (_JDN_JUL_MIN <= jdn <= _JDN_JUL_MAX):
        raise ValueError(f"jdn hors domaine julien inversible : [{_JDN_JUL_MIN}, {_JDN_JUL_MAX}]")
    c = jdn + 32082
    d = (4 * c + 3) // 1461
    e = c - (1461 * d) // 4
    m = (5 * e + 2) // 153
    jour = e - (153 * m + 2) // 5 + 1
    mois = m + 3 - 12 * (m // 10)
    annee = d - 4800 + m // 10
    return (annee, mois, jour)


# ── HIJRI TABULAIRE <-> JDN ─────────────────────────────────────────────────────────────────────────────────
def est_abondante_hijri(a: int) -> bool:
    """Année abondante (355 j) du cycle tabulaire de 30 ans : reste dans {2,5,7,10,13,16,18,21,24,26,29}.

    Équivalent arithmétique exact : (11·a + 14) mod 30 < 11."""
    a = _exige_annee(a, "annee hijri")
    return (11 * a + 14) % 30 < 11


def _jours_mois_hijri(a: int, m: int) -> int:
    if m % 2 == 1:
        return 30            # mois impairs : 30 jours
    if m < 12:
        return 29            # mois pairs 2..10 : 29 jours
    return 30 if est_abondante_hijri(a) else 29   # Dhou al-hijja : 30 si abondante


def _jours_avant_annee_hijri(a: int) -> int:
    """Jours écoulés depuis l'époque (1/1/1 AH) avant le 1 Muharram de l'année a (entier exact)."""
    return 354 * (a - 1) + (11 * a + 3) // 30


def hijri_vers_jdn(a: int, m: int, j: int) -> int:
    """JDN du jour (a, m, j) du calendrier islamique TABULAIRE (époque civile, JDN(1/1/1 AH) = 1948440).

    ATTENTION : tabulaire = arithmétique ; le calendrier OBSERVATIONNEL réel peut différer de ±1 jour."""
    a, m, j = _exige_date(a, m, j, _jours_mois_hijri)
    # (59·(m-1)+1)//2 = jours cumulés des mois précédents (alternance exacte 30/29)
    return j + (59 * (m - 1) + 1) // 2 + _jours_avant_annee_hijri(a) + 1948439


def jdn_vers_hijri(jdn: int) -> tuple[int, int, int]:
    """(annee, mois, jour) du calendrier islamique TABULAIRE pour ce JDN. Inverse exact de hijri_vers_jdn."""
    jdn = _exige_entier(jdn, "jdn")
    if not (_JDN_HIJRI_MIN <= jdn <= _JDN_HIJRI_MAX):
        raise ValueError(f"jdn hors domaine hijri tabulaire inversible : [{_JDN_HIJRI_MIN}, {_JDN_HIJRI_MAX}]")
    jours = jdn - 1948440                       # 0 <=> 1 Muharram 1 AH
    a = (30 * jours + 10646) // 10631           # estimation (cycle 30 ans = 10631 jours), puis ajustement borné
    while _jours_avant_annee_hijri(a) > jours:
        a -= 1
    while _jours_avant_annee_hijri(a + 1) <= jours:
        a += 1
    reste = jours - _jours_avant_annee_hijri(a)
    m = 1
    while reste >= _jours_mois_hijri(a, m):
        reste -= _jours_mois_hijri(a, m)
        m += 1
    return (a, m, reste + 1)


# ── JOUR DE LA SEMAINE ──────────────────────────────────────────────────────────────────────────────────────
def jour_semaine(jdn: int) -> str:
    """Jour de la semaine du JDN : jdn % 7 == 0 <=> lundi (propriété arithmétique du jour julien)."""
    jdn = _exige_entier(jdn, "jdn")
    if jdn < 0:
        raise ValueError("jdn invalide : un entier >= 0 est requis")
    return _JOURS_SEMAINE[jdn % 7]


# ── ÉCART JULIEN / GRÉGORIEN ────────────────────────────────────────────────────────────────────────────────
def ecart_julien_gregorien(annee: int) -> int:
    """Jours à AJOUTER à une date julienne pour la date grégorienne (10 en 1582, 13 depuis mars 1900).

    Calculé comme différence de JDN sur la même date nominale (1er juin) : exact du 1er mars de `annee`
    au 28/29 février suivant. Peut être négatif ou nul pour les premiers siècles (les deux calendriers
    coïncident nominalement de mars 200 à février 300)."""
    annee = _exige_annee(annee)
    return julien_vers_jdn(annee, 6, 1) - gregorien_vers_jdn(annee, 6, 1)


# ── FUSEAUX HORAIRES À OFFSET FIXE ──────────────────────────────────────────────────────────────────────────
def decalage_utc(fuseau: str) -> int:
    """Offset FIXE en MINUTES du fuseau nommé (« UTC », « UTC+1 », « UTC-9:30 », « UTC+5:45 »…).

    Seuls les noms encodant leur offset sont acceptés ; les noms régionaux (CET, EST…) sont REFUSÉS
    car ambigus (heure d'été, lois locales) -> ValueError."""
    if not isinstance(fuseau, str):
        raise ValueError("fuseau invalide : une chaîne (str) est requise")
    if fuseau not in _FUSEAUX:
        raise ValueError(
            "fuseau inconnu ou régional : seuls les fuseaux à offset fixe explicite (UTC, UTC+1, "
            "UTC+5:30, ...) sont acceptés — les noms régionaux dépendent de l'heure d'été"
        )
    return _FUSEAUX[fuseau]


def heure_locale(heure_utc: int, decalage: int) -> tuple[int, int]:
    """Heure locale (minutes depuis minuit, report de jour) pour heure_utc (minutes UTC) + decalage (minutes).

    heure_utc dans [0, 1439] ; decalage dans [-720, +840] (UTC-12..UTC+14) et multiple de 15 (tous les
    offsets fixes réels le sont). Renvoie (minutes_locales dans [0, 1439], report_jour dans {-1, 0, +1})."""
    heure_utc = _exige_entier(heure_utc, "heure_utc")
    if not (0 <= heure_utc <= 1439):
        raise ValueError("heure_utc invalide : minutes depuis minuit UTC, dans [0, 1439]")
    decalage = _exige_entier(decalage, "decalage")
    if not (-720 <= decalage <= 840) or decalage % 15 != 0:
        raise ValueError("decalage invalide : minutes dans [-720, +840], multiple de 15 (UTC-12..UTC+14)")
    total = heure_utc + decalage
    return (total % 1440, total // 1440)


def heure_ete(*_args, **_kwargs):
    """ABSTENTION STRUCTURELLE : lève TOUJOURS ValueError — l'heure d'été n'est pas calculable ici."""
    raise ValueError("règles DST non embarquées : dépendent du pays et de l'année (base tzdata requise)")


# ── DOMAINES INVERSIBLES (bornes calculées une fois, arithmétique entière) ─────────────────────────────────
_JDN_GREG_MIN = gregorien_vers_jdn(_ANNEE_MIN, 1, 1)      # 1721426
_JDN_GREG_MAX = gregorien_vers_jdn(_ANNEE_MAX, 12, 31)    # 5373484
_JDN_JUL_MIN = julien_vers_jdn(_ANNEE_MIN, 1, 1)          # 1721424
_JDN_JUL_MAX = julien_vers_jdn(_ANNEE_MAX, 12, 31)        # 5373557
_JDN_HIJRI_MIN = hijri_vers_jdn(_ANNEE_MIN, 1, 1)         # 1948440
_JDN_HIJRI_MAX = hijri_vers_jdn(_ANNEE_MAX, 12, 29)       # dernier jour sûr de 9999 AH
