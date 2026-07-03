"""VALIDE audio_wav.py — round-trip PCM exact (oracle stdlib `wave`) + FAUX=0 (plage, formats, flux invalide).

Oracle indépendant : ce qu'`encode` écrit, `decode` (via le module `wave` de la stdlib) le relit ; on EXIGE l'égalité
entière. Générateurs re-dérivés à la main. Contrôles négatifs : dépassement de plage, format non supporté, non-RIFF.
"""
import math

import audio_wav as A

ok = 0
ko = 0


def check(cond, label):
    global ok, ko
    if cond:
        ok += 1
    else:
        ko += 1
        print(f"  FAIL: {label}")


def leve(fn, *a, **k):
    try:
        fn(*a, **k)
        return False
    except ValueError:
        return True
    except Exception:
        return False


# ── 1) ROUND-TRIP mono 16 bits ──
sig = [0, 100, -100, 32767, -32768, 12345]
w = A.encode(sig, framerate=8000, sampwidth=2, canaux=1)
d = A.decode(w)
check(d["samples"] == sig, "mono 16b : round-trip exact")
check(d["framerate"] == 8000 and d["canaux"] == 1 and d["sampwidth"] == 2, "mono 16b : en-tête correct")
check(d["frames"] == len(sig), "mono 16b : nb de frames")

# ── 2) ROUND-TRIP stéréo (tuples) ──
st = [(100, -100), (200, -200), (0, 0)]
w = A.encode(st, framerate=44100, sampwidth=2, canaux=2)
d = A.decode(w)
check(d["samples"] == [100, -100, 200, -200, 0, 0], "stéréo : entrelacement round-trip")
check(d["canaux"] == 2 and d["frames"] == 3, "stéréo : 2 canaux, 3 frames")

# ── 3) ROUND-TRIP 8 bits (non signé) et 32 bits ──
w8 = A.encode([0, 128, 255], sampwidth=1, canaux=1)
check(A.decode(w8)["samples"] == [0, 128, 255], "8b non signé : round-trip")
w32 = A.encode([0, 2147483647, -2147483648], sampwidth=4, canaux=1)
check(A.decode(w32)["samples"] == [0, 2147483647, -2147483648], "32b : round-trip aux bornes")

# ── 4) DÉTERMINISME ──
check(A.encode(sig, framerate=8000) == A.encode(sig, framerate=8000), "déterminisme : mêmes échantillons -> mêmes octets")

# ── 5) GÉNÉRATEURS re-dérivés (oracle indépendant) ──
s = A.sinus(440, 0.01, framerate=8000, amplitude=16000)
attendu = [round(16000 * math.sin(2 * math.pi * 440 * i / 8000)) for i in range(int(8000 * 0.01))]
check(s == attendu, "sinus : échantillons = round(A·sin(2πft/fr))")
check(len(s) == 80, "sinus : nb d'échantillons = framerate·duree")
check(A.decode(A.encode(s, framerate=8000))["samples"] == s, "sinus : round-trip après encodage")
sil = A.silence(50, sampwidth=2)
check(sil == [0] * 50 and A.silence(3, sampwidth=1) == [128, 128, 128], "silence : 0 en 16b, 128 en 8b")
carre = A.carre(1000, 0.004, framerate=8000, amplitude=10000)
check(set(carre) == {10000, -10000} and len(carre) == 32, "carré : entiers exacts ±amplitude")

# ── 6) FAUX=0 : entrées invalides -> ValueError ──
check(leve(A.encode, [40000], sampwidth=2), "échantillon hors plage 16b -> ValueError")
check(leve(A.encode, [1.5], sampwidth=2), "échantillon flottant -> ValueError")
check(leve(A.encode, [True], sampwidth=2), "échantillon booléen -> ValueError")
check(leve(A.encode, [], sampwidth=2), "aucun échantillon -> ValueError")
check(leve(A.encode, [1, 2, 3], canaux=2), "nb impair pour stéréo -> ValueError")
check(leve(A.encode, [1], sampwidth=3), "sampwidth non supporté -> ValueError")
check(leve(A.encode, [1], framerate=0), "framerate nul -> ValueError")
check(leve(A.sinus, 440, 0.01, amplitude=40000), "sinus amplitude hors plage -> ValueError")
check(leve(A.sinus, -1, 0.01), "sinus freq négative -> ValueError")
check(leve(A.decode, b"RIFFgarbage"), "flux non-WAV -> ValueError")
check(leve(A.decode, "pas des octets"), "type non-octets -> ValueError")

print(f"\n=== valide_audio_wav : {ok}/{ok + ko} ===")
import sys
sys.exit(0 if ko == 0 else 1)
