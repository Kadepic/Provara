"""
INGESTION INFORMATIQUE — extension -> langage de programmation, et extension -> type de fichier (OFFLINE).

SOURCE : conventions informatiques de référence. Faits STABLES et CERTAINS (associations standard).

FAUX=0 — discipline : associations NON CONTESTÉES. Clé = extension AVEC le point (« .py ») pour éviter
toute ambiguïté ; le lecteur normalise. Relations fonctionnelles. Les deux relations portent sur des
extensions DISJOINTES (langages de code vs formats de données) -> pas de recouvrement entre elles.

Usage : python3 ingere_informatique.py    (puis non-reg OFFLINE).
"""
from __future__ import annotations

from ingere_wikidata import publie

_LANGAGES = [
    (".py", "Python"), (".js", "JavaScript"), (".ts", "TypeScript"), (".java", "Java"),
    (".c", "C"), (".cpp", "C++"), (".cs", "C#"), (".rb", "Ruby"), (".php", "PHP"),
    (".go", "Go"), (".rs", "Rust"), (".swift", "Swift"), (".kt", "Kotlin"),
    (".sql", "SQL"), (".sh", "Bash"), (".r", "R"), (".scala", "Scala"),
    (".lua", "Lua"), (".dart", "Dart"), (".hs", "Haskell"),
]

_TYPES = [
    (".jpg", "image"), (".jpeg", "image"), (".png", "image"), (".gif", "image"),
    (".bmp", "image"), (".svg", "image"), (".webp", "image"),
    (".mp3", "audio"), (".wav", "audio"), (".flac", "audio"), (".ogg", "audio"),
    (".mp4", "vidéo"), (".avi", "vidéo"), (".mkv", "vidéo"), (".mov", "vidéo"),
    (".pdf", "document"), (".docx", "document"), (".txt", "texte"),
    (".xlsx", "tableur"), (".pptx", "présentation"),
    (".zip", "archive"), (".rar", "archive"), (".tar", "archive"), (".gz", "archive"),
    (".html", "page web"), (".css", "feuille de style"), (".json", "données"), (".xml", "données"),
    (".csv", "données tabulaires"),
]

SRC = "conventions informatiques de référence — associations standard"


def ingere():
    print(f"== INFORMATIQUE — extensions : {len(_LANGAGES)} langages, {len(_TYPES)} types de fichier ==")
    publie("langage_extension", "convention", SRC, _LANGAGES)
    publie("type_fichier", "convention", SRC, _TYPES)


if __name__ == "__main__":
    ingere()
