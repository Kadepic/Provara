"""
RÉFÉRENCES DE CONVENTION BORNÉES (mandat Yohan 2026-06-23 : compléter « tous les domaines bornés »).

Domaine BORNÉ (cat CONVENTION) : des codes/tables POSÉS par une norme, donc exacts et vérifiables :
  • code Morse international (lettre/chiffre ↔ signal) ;
  • alphabet phonétique OTAN/ITU (lettre -> mot) ;
  • code des couleurs des résistances (couleur -> chiffre 0–9 ; multiplicateurs or/argent) ;
  • fréquence d'une note en gamme tempérée (convention A4 = 440 Hz + formule 12-TET) : exact par construction.

SOUND : entrée hors table -> (HORS, None), jamais devinée. Mécanisme garanti ; tables = données sourcées
(normes ITU/CEI). Vérifié en adverse par `valide_references.py`.
"""
from __future__ import annotations

VERIFIE = "verifie"
HORS = "hors"

# --- Code Morse international (ITU-R M.1677). ---
MORSE = {
    "A": ".-", "B": "-...", "C": "-.-.", "D": "-..", "E": ".", "F": "..-.", "G": "--.",
    "H": "....", "I": "..", "J": ".---", "K": "-.-", "L": ".-..", "M": "--", "N": "-.",
    "O": "---", "P": ".--.", "Q": "--.-", "R": ".-.", "S": "...", "T": "-", "U": "..-",
    "V": "...-", "W": ".--", "X": "-..-", "Y": "-.--", "Z": "--..",
    "0": "-----", "1": ".----", "2": "..---", "3": "...--", "4": "....-",
    "5": ".....", "6": "-....", "7": "--...", "8": "---..", "9": "----.",
}
_MORSE_INV = {v: k for k, v in MORSE.items()}

# --- Alphabet phonétique OTAN / ITU. ---
NATO = {
    "A": "Alfa", "B": "Bravo", "C": "Charlie", "D": "Delta", "E": "Echo", "F": "Foxtrot",
    "G": "Golf", "H": "Hotel", "I": "India", "J": "Juliett", "K": "Kilo", "L": "Lima",
    "M": "Mike", "N": "November", "O": "Oscar", "P": "Papa", "Q": "Quebec", "R": "Romeo",
    "S": "Sierra", "T": "Tango", "U": "Uniform", "V": "Victor", "W": "Whiskey",
    "X": "X-ray", "Y": "Yankee", "Z": "Zulu",
}

# --- Code des couleurs des résistances (CEI 60062) : couleur -> chiffre significatif. ---
COULEUR_CHIFFRE = {
    "noir": 0, "marron": 1, "rouge": 2, "orange": 3, "jaune": 4,
    "vert": 5, "bleu": 6, "violet": 7, "gris": 8, "blanc": 9,
    "black": 0, "brown": 1, "red": 2, "yellow": 4, "green": 5,
    "blue": 6, "grey": 8, "gray": 8, "white": 9,  # 'violet'/'orange' identiques FR/EN (déjà couverts)
}
COULEUR_MULTIPLICATEUR = {  # couleur -> facteur multiplicateur (en plus des 0–9 ci-dessus ×10^chiffre)
    "or": 0.1, "argent": 0.01, "gold": 0.1, "silver": 0.01,
}


def vers_morse(caractere: str) -> tuple[str, str | None]:
    """Lettre/chiffre -> signal Morse. (HORS, None) si hors table."""
    if not isinstance(caractere, str) or len(caractere.strip()) != 1:
        return (HORS, None)
    c = caractere.strip().upper()
    return (VERIFIE, MORSE[c]) if c in MORSE else (HORS, None)


def depuis_morse(code: str) -> tuple[str, str | None]:
    """Signal Morse -> lettre/chiffre. (HORS, None) si signal inconnu."""
    if not isinstance(code, str):
        return (HORS, None)
    c = code.strip()
    return (VERIFIE, _MORSE_INV[c]) if c in _MORSE_INV else (HORS, None)


def nato(caractere: str) -> tuple[str, str | None]:
    """Lettre -> mot OTAN. (HORS, None) si hors A–Z."""
    if not isinstance(caractere, str) or len(caractere.strip()) != 1:
        return (HORS, None)
    c = caractere.strip().upper()
    return (VERIFIE, NATO[c]) if c in NATO else (HORS, None)


def couleur_resistance(couleur: str) -> tuple[str, int | None]:
    """Couleur -> chiffre significatif (0–9). (HORS, None) si couleur hors table des chiffres."""
    if not isinstance(couleur, str):
        return (HORS, None)
    c = couleur.strip().lower()
    return (VERIFIE, COULEUR_CHIFFRE[c]) if c in COULEUR_CHIFFRE else (HORS, None)


_SEMITON = {"C": 0, "C#": 1, "DB": 1, "D": 2, "D#": 3, "EB": 3, "E": 4, "F": 5,
            "F#": 6, "GB": 6, "G": 7, "G#": 8, "AB": 8, "A": 9, "A#": 10, "BB": 10, "B": 11}


def frequence_note(note: str) -> tuple[str, float | None]:
    """Fréquence (Hz) d'une note en gamme tempérée 12-TET, A4 = 440 Hz. Ex. 'A4'->440, 'C4'->261.63.
    (VERIFIE, freq arrondie 2 déc.) ou (HORS, None) si note malformée. Exact par construction (convention)."""
    if not isinstance(note, str):
        return (HORS, None)
    s = note.strip().upper()
    # sépare nom (lettre + éventuel #/B) et octave (entier, possiblement négatif).
    import re
    m = re.match(r"^([A-G])([#B]?)(-?\d+)$", s)
    if not m:
        return (HORS, None)
    nom = m.group(1) + m.group(2)
    if nom not in _SEMITON:
        return (HORS, None)
    octave = int(m.group(3))
    midi = (octave + 1) * 12 + _SEMITON[nom]
    freq = 440.0 * (2.0 ** ((midi - 69) / 12.0))
    return (VERIFIE, round(freq, 2))


if __name__ == "__main__":
    print("Morse S ->", vers_morse("S"), "| <- ... ->", depuis_morse("..."))
    print("NATO Q ->", nato("Q"))
    print("résistance vert ->", couleur_resistance("vert"), "| green ->", couleur_resistance("green"))
    print("A4 ->", frequence_note("A4"), "| C4 ->", frequence_note("C4"), "| A5 ->", frequence_note("A5"))
    print("inconnu : vers_morse('é') ->", vers_morse("é"), "| note 'H9' ->", frequence_note("H9"))
