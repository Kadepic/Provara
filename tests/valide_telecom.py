"""VALIDE telecom.py — ADVERSE, FAUX=0. Capacité de Shannon / Nyquist / gain dB / longueur d'onde CONNUS
+ SOUNDNESS (bande passante ≤ 0, SNR < 0, niveaux < 2, fréquence ≤ 0 -> ValueError)."""
import telecom as T

ok = 0
ko = 0


def check(c, l):
    global ok, ko
    if c:
        ok += 1
    else:
        ko += 1
        print(f"  FAIL: {l}")


def proche(a, b, rel=1e-4):
    return abs(a - b) <= rel * abs(b) + 1e-9


def leve(fn, *a):
    try:
        fn(*a)
        return False
    except ValueError:
        return True
    except Exception:
        return False


# SHANNON-HARTLEY
check(T.capacite_shannon(1000, 1) == 1000.0, "C = B·log₂(2) = B = 1000 b/s")
check(T.capacite_shannon(3000, 7) == 9000.0, "C = 3000·log₂(8) = 9000 b/s")
check(T.capacite_shannon(1000, 3) == 2000.0, "C = 1000·log₂(4) = 2000 b/s")
check(T.capacite_shannon(1000, 0) == 0.0, "SNR=0 -> capacité nulle")

# NYQUIST
check(T.debit_nyquist(3000, 2) == 6000.0, "Nyquist binaire = 2B = 6000 b/s")
check(T.debit_nyquist(3000, 16) == 24000.0, "Nyquist M=16 -> 2·3000·4 = 24000 b/s")
check(T.debit_nyquist(1000, 4) == 4000.0, "M=4 -> 2·1000·2")

# GAIN dB
check(T.gain_db(100, 1) == 20.0, "×100 -> 20 dB")
check(T.gain_db(1000, 1) == 30.0, "×1000 -> 30 dB")
check(T.gain_db(1, 1) == 0.0, "×1 -> 0 dB")
check(proche(T.gain_db(2, 1), 3.0103), "×2 -> 3.01 dB")

# LONGUEUR D'ONDE / SNR
check(proche(T.longueur_onde(T.C_LUMIERE), 1.0), "f=c -> λ=1 m")
check(proche(T.longueur_onde(100e6), 2.99792), "FM 100 MHz -> 3 m")
check(T.snr_depuis_db(30) == 1000.0 and T.snr_depuis_db(0) == 1.0, "SNR 30 dB = 1000, 0 dB = 1")
check(proche(T.snr_depuis_db(10), 10.0), "SNR 10 dB = 10")

# SOUNDNESS
check(leve(T.capacite_shannon, 0, 1), "B=0 -> ValueError")
check(leve(T.capacite_shannon, 1000, -1), "SNR<0 -> ValueError")
check(leve(T.debit_nyquist, 3000, 1), "M=1 -> ValueError")
check(leve(T.debit_nyquist, 3000, 2.5), "M non entier -> ValueError")
check(leve(T.gain_db, 0, 1), "puissance nulle -> ValueError")
check(leve(T.longueur_onde, 0), "f=0 -> ValueError")

# DÉTERMINISME
check(T.capacite_shannon(3000, 7) == T.capacite_shannon(3000, 7), "déterminisme")

print(f"\n=== valide_telecom : {ok}/{ok + ko} ===")
import sys
sys.exit(0 if ko == 0 else 1)
