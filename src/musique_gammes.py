"""
MUSIQUE — HARMONIE ET GAMMES : règles d'un SYSTÈME musical donné (convention explicite, B-CONV).

Même posture FAUX=0 que `geometries_non_euclidiennes` / `galois` (la convention nommée juge, jamais un faux) :
  • Le MÉCANISME est une CONVENTION EXACTE, pas une corrélation — et le SYSTÈME est NOMMÉ à chaque appel,
    jamais implicite :
      – TEMPÉRAMENT ÉGAL À 12 SONS (systeme="tempere_12") : le diapason A4 = 440 Hz EXACTEMENT (norme
        ISO 16) ; chaque demi-ton multiplie la fréquence par 2^(1/12) ; donc
            f(note) = 440 · 2^((m − 69)/12),   m = numéro chromatique (convention MIDI, C4 = 60, A4 = 69).
      – INTONATION JUSTE (systeme="juste") : les intervalles sont des RAPPORTS DE FRACTIONS EXACTES
        (quinte juste 3/2, tierce majeure 5/4, quarte juste 4/3, octave 2/1 — catalogue 5-limite classique).
        Il n'existe PAS de fréquence absolue en intonation juste sans référence supplémentaire : demander
        `frequence(..., systeme="juste")` -> ValueError (abstention structurelle, pas une devinette).
      – COMPARAISON (le point théorique) : l'écart en CENTS entre deux rapports r1, r2 vaut
            1200 · log2(r1/r2).
        La quinte tempérée (700 cents) est PLUS COURTE que la quinte juste (≈ 701.955 cents) d'environ
        1.955 cents. Le COMMA PYTHAGORICIEN — 12 quintes justes ≠ 7 octaves — vaut EXACTEMENT
            (3/2)^12 / 2^7 = 3^12 / 2^19 = 531441/524288   (≈ 23.460 cents) : un FAIT, exposé en Fraction.
  • Les gammes/accords sont des PATRONS D'INTERVALLES conventionnels (majeur = 2,2,1,2,2,2,1 ; accord
    majeur = 0,4,7 ; etc.) ; l'épellation des notes suit la règle classique « une lettre par degré »
    (G majeur -> F#, F majeur -> Bb), jamais une épellation enharmonique fantaisiste.
  • Les fréquences (flottants inévitables) sont ARRONDIES à 10 chiffres significatifs — précision honnête
    et DITE. Les rapports d'intonation juste et le comma sont des `fractions.Fraction` EXACTES.

GARANTIES (vérifiées en adverse par `valide_musique_gammes.py`) :
  - note hors {C,D,E,F,G,A,B} + altération ('','#','##','b','bb') -> ValueError ;
  - octave hors [-1, 9] ou non entier -> ValueError (les bool sont REFUSÉS : True n'est pas 1) ;
  - système non nommé ou hors catalogue {tempere_12, juste} -> ValueError ;
  - mode / qualité d'accord / intervalle hors catalogue -> ValueError ;
  - intonation juste : triton et septième mineure AMBIGUS (plusieurs rapports classiques concurrents)
    -> ValueError (abstention plutôt qu'un choix arbitraire présenté comme LE rapport) ;
  - types invalides (bool, str, NaN, ±inf, rapport ≤ 0) -> ValueError ;
  - déterministe ; conservateur (faux négatif/abstention toléré, faux POSITIF interdit).

Toutes les fonctions sont PURES et déterministes ; le module n'importe que `math` et `fractions` (stdlib).
NB : `audio_wav.py` (encodeur PCM) ne traite PAS de ce sujet ; ici c'est le SYSTÈME musical lui-même.
"""
from __future__ import annotations

import math
from fractions import Fraction

SOURCE = ("ISO 16:1975 (diapason A4 = 440 Hz) + tempérament égal 2^(1/12) (convention occidentale) "
          "+ intonation juste 5-limite (rapports classiques 3/2, 5/4, 4/3, 2/1) "
          "+ comma pythagoricien 3^12/2^19 = 531441/524288")

_CHIFFRES_SIGNIFICATIFS = 10

# Systèmes reconnus — TOUJOURS nommés explicitement par l'appelant.
SYSTEMES = ("tempere_12", "juste")

_FREQUENCE_A4_HZ = 440.0        # ISO 16 : exact par convention
_MIDI_A4 = 69                   # numéro chromatique de A4 (convention MIDI, C4 = 60)

# Demi-tons des 7 lettres naturelles au-dessus de C (convention universelle du clavier).
_NATURELLES = {"C": 0, "D": 2, "E": 4, "F": 5, "G": 7, "A": 9, "B": 11}
_LETTRES = ("C", "D", "E", "F", "G", "A", "B")
_ALTERATIONS = {"": 0, "#": 1, "##": 2, "b": -1, "bb": -2}
_ALT_TEXTE = {-2: "bb", -1: "b", 0: "", 1: "#", 2: "##"}

_OCTAVE_MIN, _OCTAVE_MAX = -1, 9

# Intervalles du tempérament égal (0..12 demi-tons) — noms français classiques.
_NOMS_INTERVALLES = {
    0: "unisson", 1: "seconde mineure", 2: "seconde majeure", 3: "tierce mineure",
    4: "tierce majeure", 5: "quarte juste", 6: "triton", 7: "quinte juste",
    8: "sixte mineure", 9: "sixte majeure", 10: "septième mineure",
    11: "septième majeure", 12: "octave",
}

# Demi-tons par nom d'intervalle (clés canoniques snake_case).
_DEMI_TONS_INTERVALLE = {
    "unisson": 0, "seconde_mineure": 1, "seconde_majeure": 2, "tierce_mineure": 3,
    "tierce_majeure": 4, "quarte_juste": 5, "triton": 6, "quinte_juste": 7,
    "sixte_mineure": 8, "sixte_majeure": 9, "septieme_mineure": 10,
    "septieme_majeure": 11, "octave": 12,
}

# Intonation juste 5-limite : rapports CLASSIQUES non ambigus (Fractions exactes).
# Le triton (45/32 vs 64/45) et la septième mineure (16/9 vs 9/5) ont PLUSIEURS rapports classiques
# concurrents -> ABSENTS du catalogue : demander leur rapport lève ValueError (abstention).
_RAPPORTS_JUSTES = {
    "unisson": Fraction(1, 1), "seconde_mineure": Fraction(16, 15),
    "seconde_majeure": Fraction(9, 8), "tierce_mineure": Fraction(6, 5),
    "tierce_majeure": Fraction(5, 4), "quarte_juste": Fraction(4, 3),
    "quinte_juste": Fraction(3, 2), "sixte_mineure": Fraction(8, 5),
    "sixte_majeure": Fraction(5, 3), "septieme_majeure": Fraction(15, 8),
    "octave": Fraction(2, 1),
}

# Gammes : (patron d'intervalles en demi-tons, avancée de lettre par degré).
# Les 7 modes grecs = rotations du patron majeur ; pentatonique = pentatonique MAJEURE (degrés 1,2,3,5,6).
_GAMMES = {
    "majeur":            ((2, 2, 1, 2, 2, 2, 1), (1, 1, 1, 1, 1, 1)),
    "ionien":            ((2, 2, 1, 2, 2, 2, 1), (1, 1, 1, 1, 1, 1)),
    "dorien":            ((2, 1, 2, 2, 2, 1, 2), (1, 1, 1, 1, 1, 1)),
    "phrygien":          ((1, 2, 2, 2, 1, 2, 2), (1, 1, 1, 1, 1, 1)),
    "lydien":            ((2, 2, 2, 1, 2, 2, 1), (1, 1, 1, 1, 1, 1)),
    "mixolydien":        ((2, 2, 1, 2, 2, 1, 2), (1, 1, 1, 1, 1, 1)),
    "eolien":            ((2, 1, 2, 2, 1, 2, 2), (1, 1, 1, 1, 1, 1)),
    "mineur_naturel":    ((2, 1, 2, 2, 1, 2, 2), (1, 1, 1, 1, 1, 1)),
    "locrien":           ((1, 2, 2, 1, 2, 2, 1), (1, 1, 1, 1, 1, 1)),
    "mineur_harmonique": ((2, 1, 2, 2, 1, 3, 1), (1, 1, 1, 1, 1, 1)),
    "pentatonique":      ((2, 2, 3, 2, 3), (1, 1, 2, 1, 2)),
}

# Accords : (demi-tons depuis la fondamentale, avancée de lettre par note).
_ACCORDS = {
    "majeur":              ((0, 4, 7), (0, 2, 4)),
    "mineur":              ((0, 3, 7), (0, 2, 4)),
    "diminue":             ((0, 3, 6), (0, 2, 4)),
    "augmente":            ((0, 4, 8), (0, 2, 4)),
    "septieme_dominante":  ((0, 4, 7, 10), (0, 2, 4, 6)),
}

_COMMA_PYTHAGORICIEN = Fraction(3, 2) ** 12 / Fraction(2, 1) ** 7   # = 531441/524288 (3^12 / 2^19)


# ── helpers internes ───────────────────────────────────────────────────────────────────────────────────────────
def _sig(x: float, n: int = _CHIFFRES_SIGNIFICATIFS) -> float:
    """Arrondit à n chiffres significatifs (précision honnête, indépendante de la magnitude)."""
    if x == 0:
        return 0.0
    return float(f"{x:.{n}g}")


def _exige_systeme(systeme, admis=SYSTEMES) -> str:
    if not isinstance(systeme, str) or systeme not in admis:
        raise ValueError(f"système musical invalide : nommer explicitement l'un de {admis}, reçu {systeme!r}")
    return systeme


def _parse_note(note) -> tuple[int, int]:
    """'C', 'F#', 'Bb', 'F##', 'Cbb' -> (index de lettre 0..6, altération -2..+2). Sinon ValueError."""
    if not isinstance(note, str) or len(note) == 0:
        raise ValueError(f"note invalide : chaîne 'C'..'B' avec altération éventuelle attendue, reçu {note!r}")
    lettre, alt = note[0], note[1:]
    if lettre not in _NATURELLES or alt not in _ALTERATIONS:
        raise ValueError(f"note invalide : lettre dans C,D,E,F,G,A,B + altération '','#','##','b','bb', reçu {note!r}")
    return _LETTRES.index(lettre), _ALTERATIONS[alt]


def _classe_hauteur(note: str) -> int:
    """Classe de hauteur 0..11 (C=0, ..., B=11), altération incluse, modulo l'octave."""
    lettre_idx, alt = _parse_note(note)
    return (_NATURELLES[_LETTRES[lettre_idx]] + alt) % 12


def _exige_entier(x, nom: str) -> int:
    if not isinstance(x, int) or isinstance(x, bool):
        raise ValueError(f"{nom} invalide : un entier est requis (bool refusé), reçu {x!r}")
    return x


def _exige_rapport(x, nom: str) -> float:
    """Rapport de fréquences : int/float/Fraction fini et strictement positif (bool refusé)."""
    if isinstance(x, bool) or not isinstance(x, (int, float, Fraction)):
        raise ValueError(f"{nom} invalide : un rapport numérique (int/float/Fraction) est requis, reçu {x!r}")
    v = float(x)
    if not math.isfinite(v) or v <= 0.0:
        raise ValueError(f"{nom} invalide : un rapport fini strictement positif est requis, reçu {x!r}")
    return v


def _epelle(lettre_idx: int, classe: int) -> str:
    """Épelle la note de lettre donnée atteignant la classe de hauteur `classe` (altération ≤ double)."""
    naturelle = _NATURELLES[_LETTRES[lettre_idx]]
    alt = (classe - naturelle) % 12
    if alt > 6:
        alt -= 12
    if alt not in _ALT_TEXTE:
        raise ValueError("épellation impossible : altération au-delà du double dièse/bémol requise")
    return _LETTRES[lettre_idx] + _ALT_TEXTE[alt]


# ── (a) TEMPÉRAMENT ÉGAL : fréquences ─────────────────────────────────────────────────────────────────────────
def frequence(note: str, octave: int, systeme: str) -> float:
    """Fréquence (Hz) de la note à l'octave donnée, dans le SYSTÈME nommé.

    systeme="tempere_12" : A4 = 440 Hz (ISO 16), demi-ton = 2^(1/12), notation scientifique (C4 = do central).
    L'octave s'attache à la LETTRE : B#3 sonne comme C4, Cb4 sonne comme B3 (convention d'épellation).
    systeme="juste" -> ValueError : pas de fréquence absolue sans référence supplémentaire (abstention).
    octave hors [-1, 9] -> ValueError. Résultat arrondi à 10 chiffres significatifs (approché, et dit)."""
    _exige_systeme(systeme)
    if systeme == "juste":
        raise ValueError("intonation juste : pas de fréquence absolue définie ici (abstention) ; "
                         "utiliser rapport_juste/rapport_intervalle pour les rapports exacts")
    lettre_idx, alt = _parse_note(note)
    octave = _exige_entier(octave, "octave")
    if not (_OCTAVE_MIN <= octave <= _OCTAVE_MAX):
        raise ValueError(f"octave hors domaine [{_OCTAVE_MIN}, {_OCTAVE_MAX}] : reçu {octave}")
    m = 12 * (octave + 1) + _NATURELLES[_LETTRES[lettre_idx]] + alt   # numéro chromatique (MIDI)
    return _sig(_FREQUENCE_A4_HZ * 2.0 ** ((m - _MIDI_A4) / 12.0))


# ── (b) INTERVALLES ───────────────────────────────────────────────────────────────────────────────────────────
def intervalle_demi_tons(note1: str, note2: str) -> int:
    """Intervalle ASCENDANT de note1 vers note2 en demi-tons, entre classes de hauteur (résultat 0..11).

    Convention : on monte de note1 à note2 dans la même octave ou la suivante ; ex. C->G = 7, E->C = 8."""
    return (_classe_hauteur(note2) - _classe_hauteur(note1)) % 12


def nom_intervalle(demi_tons: int) -> str:
    """Nom français classique de l'intervalle (0 unisson ... 7 quinte juste ... 12 octave).

    demi_tons hors [0, 12] -> ValueError (au-delà de l'octave : hors catalogue, abstention)."""
    demi_tons = _exige_entier(demi_tons, "demi_tons")
    if demi_tons not in _NOMS_INTERVALLES:
        raise ValueError(f"intervalle hors catalogue [0, 12] demi-tons : reçu {demi_tons}")
    return _NOMS_INTERVALLES[demi_tons]


def demi_tons_intervalle(intervalle: str) -> int:
    """Nombre de demi-tons tempérés d'un intervalle nommé ('quinte_juste' -> 7). Hors catalogue -> ValueError."""
    if not isinstance(intervalle, str) or intervalle not in _DEMI_TONS_INTERVALLE:
        raise ValueError(f"intervalle inconnu : l'un de {sorted(_DEMI_TONS_INTERVALLE)}, reçu {intervalle!r}")
    return _DEMI_TONS_INTERVALLE[intervalle]


# ── (c) GAMMES ────────────────────────────────────────────────────────────────────────────────────────────────
def intervalles_gamme(mode: str) -> tuple:
    """Patron d'intervalles (demi-tons) du mode nommé ; ex. 'majeur' -> (2,2,1,2,2,2,1). Sinon ValueError."""
    if not isinstance(mode, str) or mode not in _GAMMES:
        raise ValueError(f"mode inconnu : l'un de {sorted(_GAMMES)}, reçu {mode!r}")
    return _GAMMES[mode][0]


def gamme(tonique: str, mode: str) -> list:
    """Notes de la gamme (épellation classique : une lettre par degré). Ex. gamme('C','majeur') -> C D E F G A B.

    tonique = note avec altération éventuelle ; mode hors catalogue -> ValueError ;
    épellation exigeant plus qu'un double dièse/bémol -> ValueError (abstention, pas d'enharmonie inventée)."""
    intervalles = intervalles_gamme(mode)          # valide le mode (ValueError sinon)
    pas_lettres = _GAMMES[mode][1]
    lettre_idx, alt = _parse_note(tonique)
    classe = (_NATURELLES[_LETTRES[lettre_idx]] + alt) % 12
    notes = [_epelle(lettre_idx, classe)]
    for demi, pas in zip(intervalles[:-1], pas_lettres):
        lettre_idx = (lettre_idx + pas) % 7
        classe = (classe + demi) % 12
        notes.append(_epelle(lettre_idx, classe))
    return notes


# ── (d) ACCORDS ───────────────────────────────────────────────────────────────────────────────────────────────
def intervalles_accord(qualite: str) -> tuple:
    """Demi-tons de l'accord depuis la fondamentale ; ex. 'majeur' -> (0,4,7). Hors catalogue -> ValueError."""
    if not isinstance(qualite, str) or qualite not in _ACCORDS:
        raise ValueError(f"qualité d'accord inconnue : l'une de {sorted(_ACCORDS)}, reçu {qualite!r}")
    return _ACCORDS[qualite][0]


def accord(tonique: str, qualite: str) -> list:
    """Notes de l'accord (épellation par tierces) ; ex. accord('C','majeur') -> ['C','E','G']."""
    demi_tons = intervalles_accord(qualite)        # valide la qualité (ValueError sinon)
    pas_lettres = _ACCORDS[qualite][1]
    lettre_idx, alt = _parse_note(tonique)
    classe0 = (_NATURELLES[_LETTRES[lettre_idx]] + alt) % 12
    return [_epelle((lettre_idx + pas) % 7, (classe0 + demi) % 12)
            for demi, pas in zip(demi_tons, pas_lettres)]


# ── (e) INTONATION JUSTE : rapports EXACTS ────────────────────────────────────────────────────────────────────
def rapport_juste(intervalle: str) -> Fraction:
    """Rapport de fréquences EXACT (Fraction) de l'intervalle en intonation juste 5-limite.

    quinte_juste -> 3/2, tierce_majeure -> 5/4, quarte_juste -> 4/3, octave -> 2/1, etc.
    'triton' et 'septieme_mineure' sont AMBIGUS en intonation juste (plusieurs rapports classiques)
    -> ValueError (abstention structurelle). Intervalle inconnu -> ValueError."""
    if not isinstance(intervalle, str) or intervalle not in _RAPPORTS_JUSTES:
        raise ValueError(f"intervalle sans rapport juste UNIQUE au catalogue "
                         f"(triton/septième mineure : ambigus -> abstention) : reçu {intervalle!r}")
    return _RAPPORTS_JUSTES[intervalle]


def rapport_intervalle(intervalle: str, systeme: str):
    """Rapport de fréquences de l'intervalle nommé, dans le SYSTÈME nommé (jamais implicite).

    systeme="tempere_12" -> float 2^(n/12) (approché, 10 chiffres significatifs) ;
    systeme="juste"      -> Fraction exacte (via rapport_juste ; ambigus -> ValueError)."""
    _exige_systeme(systeme)
    if systeme == "juste":
        return rapport_juste(intervalle)
    return _sig(2.0 ** (demi_tons_intervalle(intervalle) / 12.0))


# ── (f) COMPARAISON tempéré / juste : cents et comma ──────────────────────────────────────────────────────────
def ecart_cents(tempere, juste) -> float:
    """Écart en cents entre deux rapports de fréquences : 1200·log2(tempere/juste).

    Négatif si le rapport tempéré est PLUS COURT que le juste (quinte : ≈ −1.955 cents).
    Rapports ≤ 0, NaN, inf, bool, str -> ValueError. Résultat approché (10 chiffres significatifs)."""
    t = _exige_rapport(tempere, "rapport tempéré")
    j = _exige_rapport(juste, "rapport juste")
    return _sig(1200.0 * (math.log2(t) - math.log2(j)))


def ecart_tempere_juste(intervalle: str) -> float:
    """Écart en cents (tempéré − juste) pour un intervalle nommé ; ex. quinte_juste -> ≈ −1.955 cents.

    = 100·n − 1200·log2(rapport juste). Intervalle ambigu ou inconnu -> ValueError (via rapport_juste)."""
    n = demi_tons_intervalle(intervalle)
    return _sig(100.0 * n - 1200.0 * math.log2(float(rapport_juste(intervalle))))


def comma_pythagoricien() -> Fraction:
    """COMMA PYTHAGORICIEN, EXACT : (3/2)^12 / 2^7 = 3^12/2^19 = 531441/524288 (12 quintes ≠ 7 octaves).

    C'est un FAIT arithmétique : douze quintes justes empilées dépassent sept octaves de ce rapport."""
    return _COMMA_PYTHAGORICIEN


def comma_pythagoricien_cents() -> float:
    """Le comma pythagoricien en cents : 1200·log2(531441/524288) ≈ 23.460 cents (approché, et dit)."""
    return _sig(1200.0 * math.log2(float(_COMMA_PYTHAGORICIEN)))
