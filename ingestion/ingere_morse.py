"""
INGESTION COMMUNICATION — caractère -> code Morse international  -> datasets/lecteur/code_morse.jsonl (OFFLINE).

SOURCE : code Morse international (UIT). Faits STABLES et CERTAINS. Fonctionnel.

⚠️ On écrit via `ecrit_jsonl` DIRECT (pas `publie`) : `fonctionnel` réduit « d » et « l » (élisions d', l')
à "" et les fusionnerait. Données déjà fonctionnelles. articles=False.
"""
from __future__ import annotations
from ingere_wikidata import ecrit_jsonl

_MORSE = [
    ("a", ".-"), ("b", "-..."), ("c", "-.-."), ("d", "-.."), ("e", "."),
    ("f", "..-."), ("g", "--."), ("h", "...."), ("i", ".."), ("j", ".---"),
    ("k", "-.-"), ("l", ".-.."), ("m", "--"), ("n", "-."), ("o", "---"),
    ("p", ".--."), ("q", "--.-"), ("r", ".-."), ("s", "..."), ("t", "-"),
    ("u", "..-"), ("v", "...-"), ("w", ".--"), ("x", "-..-"), ("y", "-.--"), ("z", "--.."),
    ("1", ".----"), ("2", "..---"), ("3", "...--"), ("4", "....-"), ("5", "....."),
    ("6", "-...."), ("7", "--..."), ("8", "---.."), ("9", "----."), ("0", "-----"),
]

def ingere():
    n = ecrit_jsonl("code_morse", "convention",
                    "code Morse international UIT (caractère -> code)", _MORSE, articles=False)
    print(f"== CODE MORSE ({n}) ==")

if __name__ == "__main__":
    ingere()
