"""
VALIDE references.py — held-out ADVERSE. Exactitude des tables/formule + soundness (hors table -> HORS).
"""
import references as R

ok = 0
ko = 0


def check(cond, label):
    global ok, ko
    if cond:
        ok += 1
    else:
        ko += 1
        print(f"  FAIL: {label}")


# 1) MORSE aller-retour sur quelques cas held-out + intégrité table (36 entrées, bijection).
for c, code in [("E", "."), ("T", "-"), ("Q", "--.-"), ("7", "--..."), ("0", "-----")]:
    check(R.vers_morse(c) == (R.VERIFIE, code), f"morse {c}->{code}")
    check(R.depuis_morse(code) == (R.VERIFIE, c), f"morse {code}->{c}")
check(len(R.MORSE) == 36, "morse 36 symboles (26 lettres + 10 chiffres)")
check(len(set(R.MORSE.values())) == 36, "morse bijectif (codes distincts)")
check(R.vers_morse("é")[0] == R.HORS, "morse hors table -> HORS")
check(R.vers_morse("AB")[0] == R.HORS, "morse 2 caractères -> HORS")
check(R.depuis_morse("......")[0] == R.HORS, "morse signal inconnu -> HORS")
check(R.vers_morse("s") == (R.VERIFIE, "..."), "morse casse minuscule")

# 2) NATO held-out + intégrité (26, mots distincts).
for c, mot in [("A", "Alfa"), ("J", "Juliett"), ("X", "X-ray"), ("Z", "Zulu")]:
    check(R.nato(c) == (R.VERIFIE, mot), f"nato {c}->{mot}")
check(len(R.NATO) == 26 and len(set(R.NATO.values())) == 26, "nato 26 mots distincts")
check(R.nato("0")[0] == R.HORS, "nato chiffre -> HORS")
check(R.nato("é")[0] == R.HORS, "nato hors A-Z -> HORS")

# 3) Couleurs résistances (FR + EN), held-out + HORS.
for coul, ch in [("noir", 0), ("rouge", 2), ("blanc", 9), ("red", 2), ("white", 9), ("GREEN", 5)]:
    check(R.couleur_resistance(coul) == (R.VERIFIE, ch), f"couleur {coul}->{ch}")
check(R.couleur_resistance("rose")[0] == R.HORS, "couleur inconnue -> HORS")
check(R.couleur_resistance("violet") == (R.VERIFIE, 7), "violet (FR/EN) -> 7")

# 4) Fréquences de notes (12-TET, A4=440) — exactitude held-out.
for note, f in [("A4", 440.0), ("A5", 880.0), ("A3", 220.0)]:
    check(R.frequence_note(note) == (R.VERIFIE, f), f"freq {note}={f}")
st, f = R.frequence_note("C4")
check(st == R.VERIFIE and abs(f - 261.63) < 0.01, f"freq C4 ~261.63 (obtenu {f})")
st, f = R.frequence_note("A#4")
check(st == R.VERIFIE and abs(f - 466.16) < 0.05, f"freq A#4 ~466.16 (obtenu {f})")
check(R.frequence_note("Bb4") == R.frequence_note("A#4"), "enharmonie Bb4 == A#4")
st, f = R.frequence_note("E2")
check(st == R.VERIFIE and abs(f - 82.41) < 0.05, f"freq E2 ~82.41 (corde mi grave guitare, obtenu {f})")
# soundness notes malformées -> HORS.
for bad in ["H4", "A", "4A", "A#", "", "Z9", None, 440]:
    check(R.frequence_note(bad)[0] == R.HORS, f"note malformée {bad!r} -> HORS")

# 5) DÉTERMINISME.
check(R.frequence_note("C5") == R.frequence_note("C5"), "déterminisme")

print(f"\n=== valide_references : {ok}/{ok+ko} ===")
import sys
sys.exit(0 if ko == 0 else 1)
