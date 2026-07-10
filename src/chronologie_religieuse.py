"""CHRONOLOGIE RELIGIEUSE — histoire et datation des faits religieux, FAUX=0
(sujet borné « histoire des faits religieux (datation) », PARTIE X, B-FAIT ; à la manière de
`conjectures_celebres.py` : un CATALOGUE CLOS de faits historiques établis, jamais un moteur).

MÉCANISME — la datation des faits religieux se scinde NETTEMENT en deux régimes, et tout l'intérêt du
module est de les traiter SÉPARÉMENT (jamais de confondre un fait certain avec un fait encadré) :

  (a) ÉVÉNEMENTS DATÉS — documentés par des sources CONTEMPORAINES (actes de conciles, édits, chroniques),
      dont l'année est CERTAINE : édit de Milan 313 ; 1er concile de Nicée 325 ; Chalcédoine 451 ;
      Hégire 622 (départ vers Médine, an 1 du calendrier islamique) ; grand schisme d'Orient 1054 ;
      prise de Jérusalem par la 1re croisade 1099 ; 95 thèses de Luther 1517 ; concile de Trente 1545-1563 ;
      édit de Nantes 1598 et sa révocation 1685 ; concile Vatican I 1869-1870 ; loi française de séparation
      des Églises et de l'État 1905 ; concile Vatican II 1962-1965.
      `date(evenement)` -> int (année) ou (debut, fin) ; `source(evenement)` -> str.

  (b) FAITS À DATATION CONTESTÉE — la source historique fait DÉFAUT ou se contredit ; on ne livre qu'une
      FOURCHETTE encadrante et la RAISON de l'incertitude, jamais une date ponctuelle inventée :
      naissance de Jésus (−6 à −4 : Hérode meurt en −4 ; l'an 0 n'existe pas ; le 25 décembre est une date
      LITURGIQUE fixée au IVᵉ s., pas une date de naissance) ; vie du Bouddha (deux chronologies
      CONCURRENTES, longue ~−560/−480 et courte ~−450/−370 -> consensus=False) ; rédaction du Pentateuque
      (hypothèse documentaire, −900 à −400) ; vie de Zoroastre (fourchette de plus d'un millénaire) ;
      composition des Védas (−1500 à −500). `datation_contestee(fait)` -> {'fourchette','raison','consensus'}.
      Pour CES faits, `date()` LÈVE ValueError et renvoie explicitement vers `datation_contestee`.

  (c) `calendriers_religieux()` : ère chrétienne (Denys le Petit, VIᵉ s., SANS an 0), Hégire (lunaire, 622),
      calendrier hébraïque (ère de la Création).
  (d) `evenements_par_siecle(siecle)` et `catalogue()`.

POSTURE FAUX=0 (l'histoire juge, jamais un faux) :
  • Un module qui daterait « naissance de Jésus » à l'an 1 serait FAUX : ce fait est CONTESTÉ, `date()` s'abstient.
  • Événement HORS catalogue -> ValueError. `date()` d'un fait contesté -> ValueError explicite.
    `datation_contestee()` d'un événement bien daté -> ValueError. Aucune date jamais devinée.
  • VÉRITÉ DATÉE : les fourchettes reflètent le consensus savant à la date de la source (2026), pas une vérité
    éternelle ; le module énonce l'état ÉTABLI de la datation, ses certitudes ET ses incertitudes.

GARANTIES (vérifiées en adverse par `valide_chronologie_religieuse.py`) :
  - Nicée=325, Hégire=622, schisme=1054, 95 thèses=1517, séparation=1905, Vatican II=(1962,1965) ;
  - `date('naissance de Jésus')` -> ValueError ; `datation_contestee('naissance de Jésus')` = (−6,−4) ;
  - Bouddha : consensus=False (deux chronologies concurrentes) ;
  - `datation_contestee('concile de Nicée')` -> ValueError (événement daté avec certitude) ;
  - événement inventé / type invalide (bool, str vide, non-str) -> ValueError ; déterministe ; fonctions pures.

Le module n'importe que `unicodedata` (stdlib). Toutes les fonctions sont PURES et déterministes.
"""
from __future__ import annotations

import unicodedata

SOURCE = (
    "actes conciliaires (Nicée 325, Chalcédoine 451, Trente 1545-1563, Vatican I 1869-1870, "
    "Vatican II 1962-1965) ; édit de Milan (Lactance, Eusèbe) 313 ; calendrier de l'Hégire an 1 = 622 ; "
    "chroniques de la 1re croisade (prise de Jérusalem 1099) ; 95 thèses de Luther 1517 ; "
    "édit de Nantes 1598 / édit de Fontainebleau (révocation) 1685 ; loi française du 9 décembre 1905 ; "
    "pour les faits contestés : consensus historiographique (Hérode † −4 ; hypothèse documentaire ; "
    "chronologies longue/courte du Bouddha)"
)

# ══ (a) ÉVÉNEMENTS DATÉS (année certaine, source contemporaine citée) ══════════════════════════════════════════
# Champs : enonce, date (int année, ou (debut, fin) pour un événement pluriannuel), source.
_EVENEMENTS = {
    "edit_milan": {
        "enonce": "édit de Milan : liberté de culte accordée aux chrétiens dans l'Empire romain "
                  "(Constantin et Licinius)",
        "date": 313,
        "source": "rapporté par Lactance (De mortibus persecutorum) et Eusèbe de Césarée (Histoire ecclésiastique)",
    },
    "nicee_1": {
        "enonce": "premier concile de Nicée : premier concile œcuménique, symbole de Nicée, condamnation "
                  "de l'arianisme",
        "date": 325,
        "source": "actes et canons du concile ; convoqué par Constantin (Eusèbe, Vie de Constantin)",
    },
    "chalcedoine": {
        "enonce": "concile de Chalcédoine : définition des deux natures du Christ (dyophysisme)",
        "date": 451,
        "source": "actes du IVᵉ concile œcuménique (définition de Chalcédoine)",
    },
    "hegire": {
        "enonce": "Hégire : émigration de Mahomet et des premiers musulmans de La Mecque vers Médine ; "
                  "an 1 du calendrier islamique",
        "date": 622,
        "source": "point de départ (an 1 = 622) du calendrier hégirien lunaire, fixé sous le califat de ʿUmar",
    },
    "schisme_orient": {
        "enonce": "grand schisme d'Orient : excommunications mutuelles entre Rome et Constantinople, "
                  "séparation des Églises catholique et orthodoxe",
        "date": 1054,
        "source": "bulle d'excommunication du légat Humbert de Silva Candida contre Michel Cérulaire",
    },
    "prise_jerusalem_croises": {
        "enonce": "prise de Jérusalem par la première croisade",
        "date": 1099,
        "source": "chroniques de la première croisade (Gesta Francorum, Raymond d'Aguilers) — 15 juillet 1099",
    },
    "theses_luther": {
        "enonce": "95 thèses de Martin Luther contre les indulgences (acte fondateur de la Réforme protestante)",
        "date": 1517,
        "source": "Disputatio pro declaratione virtutis indulgentiarum, 31 octobre 1517 (Wittenberg)",
    },
    "concile_trente": {
        "enonce": "concile de Trente : réponse doctrinale et disciplinaire de la Contre-Réforme catholique",
        "date": (1545, 1563),
        "source": "actes et décrets du concile de Trente (trois périodes, 1545-1563)",
    },
    "edit_nantes": {
        "enonce": "édit de Nantes : Henri IV accorde des droits et places de sûreté aux protestants français",
        "date": 1598,
        "source": "édit de Nantes signé par Henri IV, 13 avril 1598",
    },
    "revocation_edit_nantes": {
        "enonce": "révocation de l'édit de Nantes (édit de Fontainebleau) : interdiction du culte protestant "
                  "en France par Louis XIV",
        "date": 1685,
        "source": "édit de Fontainebleau, Louis XIV, octobre 1685",
    },
    "vatican_i": {
        "enonce": "concile Vatican I : proclamation du dogme de l'infaillibilité pontificale",
        "date": (1869, 1870),
        "source": "actes du concile Vatican I (constitution Pastor aeternus, 1870) ; interrompu en 1870",
    },
    "separation_eglises_etat": {
        "enonce": "loi française de séparation des Églises et de l'État (laïcité de la République)",
        "date": 1905,
        "source": "loi du 9 décembre 1905 concernant la séparation des Églises et de l'État (France)",
    },
    "vatican_ii": {
        "enonce": "concile Vatican II : aggiornamento de l'Église catholique (liturgie en langue vernaculaire, "
                  "œcuménisme)",
        "date": (1962, 1965),
        "source": "actes du concile Vatican II (16 documents, 1962-1965) ; ouvert par Jean XXIII, clos par Paul VI",
    },
}

# ══ (b) FAITS À DATATION CONTESTÉE (fourchette encadrante + raison + consensus) ════════════════════════════════
# Champs : enonce, fourchette (min, max) années (négatif = av. J.-C.), raison, consensus (bool).
_CONTESTES = {
    "naissance_jesus": {
        "enonce": "naissance de Jésus de Nazareth",
        "fourchette": (-6, -4),
        "raison": "Hérode le Grand meurt en −4 (Matthieu situe la naissance sous son règne) ; l'an 0 n'existe "
                  "PAS dans l'ère chrétienne (on passe de −1 à +1), l'ère de Denys le Petit décale la naissance "
                  "réelle de quelques années ; le 25 décembre est une date LITURGIQUE fixée au IVᵉ siècle, pas "
                  "une date de naissance historique",
        "consensus": True,
    },
    "bouddha": {
        "enonce": "vie du Bouddha (Siddhārtha Gautama)",
        "fourchette": (-560, -370),
        "raison": "deux chronologies CONCURRENTES sans consensus : chronologie longue (~−560 à −480, "
                  "traditionnelle) et chronologie courte (~−450 à −370, retenue par une partie de la recherche "
                  "moderne à partir des sources sri-lankaises et de la datation d'Ashoka)",
        "consensus": False,
    },
    "pentateuque": {
        "enonce": "rédaction du Pentateuque (Torah)",
        "fourchette": (-900, -400),
        "raison": "l'hypothèse documentaire décrit une compilation progressive de plusieurs sources (J, E, D, P) "
                  "sur des siècles, avec une mise en forme finale à l'époque perse ; ni auteur ni date uniques",
        "consensus": False,
    },
    "zoroastre": {
        "enonce": "vie de Zoroastre (Zarathoustra)",
        "fourchette": (-1700, -600),
        "raison": "estimations réparties sur PLUS D'UN MILLÉNAIRE : datation linguistique haute (~−1700 à −1000, "
                  "langue des Gāthās proche du sanskrit védique) contre datation traditionnelle basse "
                  "(~−600, « 258 ans avant Alexandre »)",
        "consensus": False,
    },
    "vedas": {
        "enonce": "composition des Védas",
        "fourchette": (-1500, -500),
        "raison": "corpus composé oralement sur un millénaire : Rigveda le plus ancien (~−1500/−1200), Védas "
                  "et textes annexes ultérieurs jusque vers −500 ; transmission orale, pas de date de rédaction",
        "consensus": False,
    },
}

# ══ ALIAS EXPLICITES (après normalisation) — aucune correspondance floue ═══════════════════════════════════════
_ALIAS = {
    # ── événements datés ──
    "edit de milan": "edit_milan",
    "premier concile de nicee": "nicee_1",
    "concile de nicee": "nicee_1",
    "nicee": "nicee_1",
    "nicee i": "nicee_1",
    "concile de chalcedoine": "chalcedoine",
    "hegire": "hegire",
    "grand schisme d'orient": "schisme_orient",
    "schisme d'orient": "schisme_orient",
    "grand schisme": "schisme_orient",
    "schisme de 1054": "schisme_orient",
    "prise de jerusalem": "prise_jerusalem_croises",
    "prise de jerusalem par les croises": "prise_jerusalem_croises",
    "prise de jerusalem 1099": "prise_jerusalem_croises",
    "95 theses": "theses_luther",
    "95 theses de luther": "theses_luther",
    "theses de luther": "theses_luther",
    "quatre-vingt-quinze theses": "theses_luther",
    "concile de trente": "concile_trente",
    "edit de nantes": "edit_nantes",
    "revocation de l'edit de nantes": "revocation_edit_nantes",
    "revocation de l edit de nantes": "revocation_edit_nantes",
    "edit de fontainebleau": "revocation_edit_nantes",
    "concile vatican i": "vatican_i",
    "vatican i": "vatican_i",
    "premier concile du vatican": "vatican_i",
    "loi de separation des eglises et de l'etat": "separation_eglises_etat",
    "loi de separation des eglises et de l etat": "separation_eglises_etat",
    "separation des eglises et de l'etat": "separation_eglises_etat",
    "loi de 1905": "separation_eglises_etat",
    "loi de separation": "separation_eglises_etat",
    "concile vatican ii": "vatican_ii",
    "vatican ii": "vatican_ii",
    "deuxieme concile du vatican": "vatican_ii",
    "second concile du vatican": "vatican_ii",
    # ── faits contestés ──
    "naissance de jesus": "naissance_jesus",
    "naissance du christ": "naissance_jesus",
    "nativite": "naissance_jesus",
    "vie du bouddha": "bouddha",
    "bouddha": "bouddha",
    "naissance du bouddha": "bouddha",
    "siddhartha gautama": "bouddha",
    "redaction du pentateuque": "pentateuque",
    "pentateuque": "pentateuque",
    "torah": "pentateuque",
    "vie de zoroastre": "zoroastre",
    "zoroastre": "zoroastre",
    "zarathoustra": "zoroastre",
    "composition des vedas": "vedas",
    "vedas": "vedas",
    "date des vedas": "vedas",
    "veda": "vedas",
}


def _normalise(nom: str) -> str:
    """Normalisation DÉTERMINISTE : accents retirés (NFD), minuscules, séparateurs unifiés en espaces."""
    decompose = unicodedata.normalize("NFD", nom)
    sans_accent = "".join(c for c in decompose if unicodedata.category(c) != "Mn")
    bas = sans_accent.lower().replace("_", " ").replace("’", "'")
    return " ".join(bas.split())


def _resout(nom):
    """Résout un nom -> (regime, cle, entree) où regime ∈ {'date','conteste'}.

    Hors catalogue -> ValueError (abstention : jamais une date inventée)."""
    if not isinstance(nom, str) or isinstance(nom, bool):
        raise ValueError("nom invalide : une chaîne de caractères non vide est requise")
    cle = _normalise(nom)
    if not cle:
        raise ValueError("nom invalide : une chaîne de caractères non vide est requise")
    cle_soulignee = cle.replace(" ", "_").replace("-", "_")
    if cle_soulignee in _EVENEMENTS:
        return ("date", cle_soulignee, _EVENEMENTS[cle_soulignee])
    if cle_soulignee in _CONTESTES:
        return ("conteste", cle_soulignee, _CONTESTES[cle_soulignee])
    if cle in _ALIAS:
        canon = _ALIAS[cle]
        if canon in _EVENEMENTS:
            return ("date", canon, _EVENEMENTS[canon])
        return ("conteste", canon, _CONTESTES[canon])
    raise ValueError(f"fait religieux hors catalogue : {nom!r} (abstention — aucune date inventée)")


# ══ API — ÉVÉNEMENTS DATÉS ════════════════════════════════════════════════════════════════════════════════════
def date(evenement: str):
    """Date CERTAINE d'un événement religieux : int (année) ou (debut, fin) pour un événement pluriannuel.

    Un fait à datation CONTESTÉE (naissance de Jésus, Bouddha, Pentateuque, Zoroastre, Védas) -> ValueError
    explicite renvoyant vers `datation_contestee`. Événement hors catalogue -> ValueError."""
    regime, cle, e = _resout(evenement)
    if regime == "conteste":
        raise ValueError(
            f"{evenement!r} est un fait à datation CONTESTÉE : pas de date certaine — "
            f"utilisez datation_contestee({cle!r}) pour obtenir la fourchette et la raison")
    return e["date"]


def source(evenement: str) -> str:
    """Source contemporaine attestant la date de l'événement. Fait contesté / hors catalogue -> ValueError."""
    regime, cle, e = _resout(evenement)
    if regime == "conteste":
        raise ValueError(
            f"{evenement!r} est un fait à datation CONTESTÉE (pas de source datante certaine) — "
            f"utilisez datation_contestee({cle!r})")
    return e["source"]


def enonce(evenement: str) -> str:
    """Énoncé canonique du fait (événement daté OU fait contesté). Hors catalogue -> ValueError."""
    _, _, e = _resout(evenement)
    return e["enonce"]


# ══ API — FAITS À DATATION CONTESTÉE ══════════════════════════════════════════════════════════════════════════
def datation_contestee(fait: str) -> dict:
    """Encadrement d'un fait fondateur à datation contestée :
        {'fourchette': (min, max), 'raison': str, 'consensus': bool}.

    Un événement DATÉ avec certitude (Nicée, Hégire, etc.) -> ValueError : sa date est certaine, utilisez `date`.
    Fait hors catalogue -> ValueError."""
    regime, cle, e = _resout(fait)
    if regime == "date":
        raise ValueError(
            f"{fait!r} est un événement DATÉ avec certitude : sa datation n'est pas contestée — "
            f"utilisez date({cle!r})")
    return {
        "fourchette": e["fourchette"],
        "raison": e["raison"],
        "consensus": e["consensus"],
    }


# ══ API — CALENDRIERS ═════════════════════════════════════════════════════════════════════════════════════════
def calendriers_religieux() -> dict:
    """Les trois grandes ères religieuses et leur point de départ (faits de convention, établis) :
        'ere_chretienne', 'hegire', 'calendrier_hebraique'. Structure immuable (copie neuve à chaque appel)."""
    return {
        "ere_chretienne": {
            "nom": "ère chrétienne (anno Domini)",
            "type": "solaire",
            "origine": "conçue par Denys le Petit au VIᵉ siècle pour compter depuis l'Incarnation",
            "an_zero": False,
            "note": "il n'y a PAS d'an 0 : l'année −1 (1 av. J.-C.) est immédiatement suivie de l'année +1 "
                    "(1 apr. J.-C.) ; le comput de Denys décale d'ailleurs la naissance réelle de Jésus",
        },
        "hegire": {
            "nom": "calendrier de l'Hégire (calendrier islamique)",
            "type": "lunaire",
            "origine": "an 1 = 622 (émigration de Mahomet vers Médine)",
            "an_zero": False,
            "note": "année lunaire d'environ 354 jours : les années hégiriennes ne coïncident pas avec les "
                    "années grégoriennes (décalage d'environ 11 jours par an)",
        },
        "calendrier_hebraique": {
            "nom": "calendrier hébraïque",
            "type": "luni-solaire",
            "origine": "ère de la Création (Anno Mundi), comput traditionnel plaçant la Création vers −3761",
            "an_zero": False,
            "note": "ère de la Création (Anno Mundi) : l'an grégorien 2000 correspond approximativement à "
                    "l'an hébraïque 5760/5761",
        },
    }


# ══ API — INDEX / CATALOGUE ═══════════════════════════════════════════════════════════════════════════════════
def _siecle_de(annee: int) -> int:
    """Siècle (numéro, base 1) contenant une année POSITIVE. Ex. 325 -> 4, 622 -> 7, 1905 -> 20."""
    return (annee - 1) // 100 + 1


def _annee_debut(entree) -> int:
    """Année de départ d'un événement (int direct, ou debut d'un couple pluriannuel)."""
    d = entree["date"]
    return d if isinstance(d, int) else d[0]


def evenements_par_siecle(siecle: int) -> tuple:
    """Noms canoniques (triés) des ÉVÉNEMENTS DATÉS dont l'année de départ tombe dans ce siècle (base 1).

    `siecle` : entier ≥ 1 (le catalogue ne couvre que l'ère chrétienne positive). bool / non-int / ≤ 0 ->
    ValueError. Aucun siècle deviné : un siècle sans événement renvoie un tuple vide."""
    if not isinstance(siecle, int) or isinstance(siecle, bool):
        raise ValueError("siècle invalide : un entier ≥ 1 est requis")
    if siecle < 1:
        raise ValueError("siècle invalide : un entier ≥ 1 est requis (le catalogue couvre l'ère positive)")
    trouves = [cle for cle, e in _EVENEMENTS.items() if _siecle_de(_annee_debut(e)) == siecle]
    return tuple(sorted(trouves))


def catalogue() -> tuple:
    """Tuple TRIÉ des noms canoniques des ÉVÉNEMENTS DATÉS (datation certaine)."""
    return tuple(sorted(_EVENEMENTS))


def faits_contestes() -> tuple:
    """Tuple TRIÉ des noms canoniques des FAITS À DATATION CONTESTÉE."""
    return tuple(sorted(_CONTESTES))
