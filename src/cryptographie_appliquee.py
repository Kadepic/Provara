"""CRYPTOGRAPHIE APPLIQUÉE — chiffrements symétriques, FAUX=0 (mission formule/concept 2026-06-29).

Chiffrement de César (décalage), de Vigenère (clé répétée), XOR (à clé répétée, involutif). Propriété fondamentale
GARANTIE : déchiffrer(chiffrer(m, k), k) = m (réversibilité exacte). Mécanisme déterministe. Abstention STRUCTURELLE :
clé vide, caractère hors alphabet (Vigenère) -> ValueError.

Couvre le sujet borné « Cryptographie appliquée » (chiffrement symétrique ; le volet RSA/asymétrique est dans
`arithmetique_modulaire`). Vérifié en adverse par `valide_cryptographie_appliquee.py` (vecteurs connus + round-trip).
"""
from __future__ import annotations

_A = ord("A")


def _maj(texte):
    if not isinstance(texte, str):
        raise ValueError("texte (chaîne) attendu")
    return texte.upper()


def chiffre_cesar(texte: str, decalage: int) -> str:
    """Chiffrement de César : décale chaque lettre de `decalage` (mod 26). Non-lettres inchangées."""
    if not isinstance(decalage, int) or isinstance(decalage, bool):
        raise ValueError("décalage entier requis")
    out = []
    for c in _maj(texte):
        if "A" <= c <= "Z":
            out.append(chr((ord(c) - _A + decalage) % 26 + _A))
        else:
            out.append(c)
    return "".join(out)


def dechiffre_cesar(texte: str, decalage: int) -> str:
    return chiffre_cesar(texte, -decalage)


def chiffre_vigenere(texte: str, cle: str) -> str:
    """Chiffrement de Vigenère : décalage variable donné par la clé (lettres A-Z) répétée. Non-lettres inchangées
    (la clé n'avance que sur les lettres)."""
    cle = _maj(cle)
    if not cle or any(not ("A" <= c <= "Z") for c in cle):
        raise ValueError("clé non vide composée de lettres A-Z requise")
    out = []
    j = 0
    for c in _maj(texte):
        if "A" <= c <= "Z":
            d = ord(cle[j % len(cle)]) - _A
            out.append(chr((ord(c) - _A + d) % 26 + _A))
            j += 1
        else:
            out.append(c)
    return "".join(out)


def dechiffre_vigenere(texte: str, cle: str) -> str:
    cle = _maj(cle)
    if not cle or any(not ("A" <= c <= "Z") for c in cle):
        raise ValueError("clé non vide composée de lettres A-Z requise")
    inverse = "".join(chr((26 - (ord(c) - _A)) % 26 + _A) for c in cle)
    return chiffre_vigenere(texte, inverse)


def chiffre_xor(donnees: bytes, cle: bytes) -> bytes:
    """Chiffrement XOR à clé répétée (involutif : appliqué deux fois -> texte clair). `donnees`/`cle` = bytes."""
    if not isinstance(donnees, (bytes, bytearray)) or not isinstance(cle, (bytes, bytearray)):
        raise ValueError("donnees et clé en bytes attendues")
    if not cle:
        raise ValueError("clé non vide requise")
    return bytes(b ^ cle[i % len(cle)] for i, b in enumerate(donnees))


if __name__ == "__main__":
    print("César 'HELLO' +3 :", chiffre_cesar("HELLO", 3))
    print("César round-trip :", dechiffre_cesar(chiffre_cesar("ATTACK AT DAWN", 5), 5))
    print("Vigenère 'HELLO'/'ABC' :", chiffre_vigenere("HELLO", "ABC"))
    print("Vigenère 'ATTACKATDAWN'/'LEMON' :", chiffre_vigenere("ATTACKATDAWN", "LEMON"))
    print("Vigenère round-trip :", dechiffre_vigenere(chiffre_vigenere("SECRET MESSAGE", "KEY"), "KEY"))
    c = chiffre_xor(b"hello", b"\x10\x20")
    print("XOR involutif :", chiffre_xor(c, b"\x10\x20"))
