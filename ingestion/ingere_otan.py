"""
INGESTION COMMUNICATION — lettre -> mot de l'alphabet phonétique OTAN/OACI  -> datasets/lecteur/alphabet_otan.jsonl (OFFLINE).

SOURCE : alphabet radiotéléphonique international OACI/OTAN. Faits STABLES et CERTAINS. Fonctionnel.

⚠️ On écrit via `ecrit_jsonl` DIRECT (pas `publie`) : le dédoublonnage de `publie`/`fonctionnel` passe par
`_sans_articles`, qui réduit les lettres-élisions « d » et « l » (= d', l') à "" -> elles se fusionneraient
et seraient rejetées. Données déjà fonctionnelles (1 mot/lettre). articles=False (lettres ≠ articles au load).
"""
from __future__ import annotations
from ingere_wikidata import ecrit_jsonl

_OTAN = [
    ("a", "Alpha"), ("b", "Bravo"), ("c", "Charlie"), ("d", "Delta"), ("e", "Echo"),
    ("f", "Foxtrot"), ("g", "Golf"), ("h", "Hotel"), ("i", "India"), ("j", "Juliett"),
    ("k", "Kilo"), ("l", "Lima"), ("m", "Mike"), ("n", "November"), ("o", "Oscar"),
    ("p", "Papa"), ("q", "Quebec"), ("r", "Romeo"), ("s", "Sierra"), ("t", "Tango"),
    ("u", "Uniform"), ("v", "Victor"), ("w", "Whiskey"), ("x", "X-ray"), ("y", "Yankee"), ("z", "Zulu"),
]

def ingere():
    n = ecrit_jsonl("alphabet_otan", "convention",
                    "alphabet radiotéléphonique OACI/OTAN (lettre -> mot)", _OTAN, articles=False)
    print(f"== ALPHABET OTAN ({n}) ==")

if __name__ == "__main__":
    ingere()
