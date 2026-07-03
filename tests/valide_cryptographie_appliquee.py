"""VALIDE cryptographie_appliquee.py — ADVERSE, FAUX=0. Vecteurs connus (César, Vigenère 'LEMON'), réversibilité
chiffre/déchiffre, involution XOR + SOUNDNESS (clé vide -> ValueError)."""
import cryptographie_appliquee as K

ok = 0
ko = 0


def check(c, l):
    global ok, ko
    if c:
        ok += 1
    else:
        ko += 1
        print(f"  FAIL: {l}")


def leve(fn, *a):
    try:
        fn(*a)
        return False
    except ValueError:
        return True
    except Exception:
        return False


# CÉSAR — vecteurs connus + round-trip
check(K.chiffre_cesar("HELLO", 3) == "KHOOR", "César HELLO+3 = KHOOR")
check(K.chiffre_cesar("ABC", 1) == "BCD" and K.chiffre_cesar("XYZ", 3) == "ABC", "César enroulement")
check(K.dechiffre_cesar("KHOOR", 3) == "HELLO", "César déchiffrement")
check(K.dechiffre_cesar(K.chiffre_cesar("ATTACK AT DAWN", 13), 13) == "ATTACK AT DAWN", "César round-trip (ponctuation)")
check(K.chiffre_cesar("HELLO", 26) == "HELLO", "César +26 = identité")

# VIGENÈRE — vecteur canonique de Wikipedia + round-trip
check(K.chiffre_vigenere("ATTACKATDAWN", "LEMON") == "LXFOPVEFRNHR", "Vigenère ATTACKATDAWN/LEMON (canonique)")
check(K.chiffre_vigenere("HELLO", "ABC") == "HFNLP", "Vigenère HELLO/ABC")
check(K.chiffre_vigenere("HELLO", "A") == "HELLO", "Vigenère clé 'A' = identité")
check(K.dechiffre_vigenere(K.chiffre_vigenere("SECRETMESSAGE", "KEY"), "KEY") == "SECRETMESSAGE", "Vigenère round-trip")
check(K.dechiffre_vigenere("LXFOPVEFRNHR", "LEMON") == "ATTACKATDAWN", "Vigenère déchiffrement canonique")

# XOR — involution
c = K.chiffre_xor(b"hello world", b"\x10\x20\x30")
check(K.chiffre_xor(c, b"\x10\x20\x30") == b"hello world", "XOR involutif (2× = clair)")
check(K.chiffre_xor(b"A", b"A") == b"\x00", "XOR avec soi-même = 0")
check(c != b"hello world", "XOR chiffre réellement")

# SOUNDNESS
check(leve(K.chiffre_vigenere, "HELLO", ""), "clé Vigenère vide -> ValueError")
check(leve(K.chiffre_vigenere, "HELLO", "K3Y"), "clé non alphabétique -> ValueError")
check(leve(K.chiffre_xor, b"data", b""), "clé XOR vide -> ValueError")
check(leve(K.chiffre_cesar, "HELLO", 1.5), "décalage non entier -> ValueError")

# DÉTERMINISME
check(K.chiffre_vigenere("TEST", "KEY") == K.chiffre_vigenere("TEST", "KEY"), "déterminisme")

print(f"\n=== valide_cryptographie_appliquee : {ok}/{ok + ko} ===")
import sys
sys.exit(0 if ko == 0 else 1)
