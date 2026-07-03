"""VALIDE raster_png.py — round-trip pixel-parfait + FAUX=0 (rejet des flux corrompus, abstention hors cadre).

Oracle indépendant : le décodeur re-lit ce que l'encodeur a écrit et on EXIGE l'égalité pixel-à-pixel. Un encodeur
qui mentirait (mauvais octet) casse le round-trip. Contrôles négatifs : signature/CRC/troncature -> ValueError.
"""
import struct
import zlib

import raster_png as R

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


def pixels(img):
    return [img.lit(x, y) for y in range(img.hauteur) for x in range(img.largeur)]


# ── 1) ROUND-TRIP identité sur les 3 modes ──
for mode, coul in (("L", 200), ("RGB", (10, 20, 30)), ("RGBA", (1, 2, 3, 4))):
    img = R.Image(5, 3, mode)
    # motif déterministe non trivial
    for y in range(3):
        for x in range(5):
            if mode == "L":
                img.pixel(x, y, (x * 13 + y * 7) % 256)
            elif mode == "RGB":
                img.pixel(x, y, ((x * 50) % 256, (y * 80) % 256, (x + y) % 256))
            else:
                img.pixel(x, y, ((x * 40) % 256, (y * 60) % 256, (x * y) % 256, 255))
    octets = R.encode(img)
    check(octets[:8] == b"\x89PNG\r\n\x1a\n", f"{mode}: signature")
    redecode = R.decode(octets)
    check(redecode.mode == mode and redecode.largeur == 5 and redecode.hauteur == 3, f"{mode}: dimensions/mode round-trip")
    check(pixels(redecode) == pixels(img), f"{mode}: round-trip pixel-parfait")

# ── 2) DÉTERMINISME : mêmes pixels -> mêmes octets ──
a = R.Image(8, 8, "RGB", fond=(255, 0, 0))
b = R.Image(8, 8, "RGB", fond=(255, 0, 0))
check(R.encode(a) == R.encode(b), "déterminisme : deux images identiques -> octets identiques")
a.pixel(3, 3, (0, 255, 0))
check(R.encode(a) != R.encode(b), "sensibilité : un pixel changé -> octets différents")

# ── 3) DESSIN : rectangle, ligne (Bresenham), remplissage ──
img = R.Image(10, 10, "L", fond=0)
img.rectangle(2, 2, 7, 7, 255, plein=False)
check(img.lit(2, 2) == (255,) and img.lit(7, 7) == (255,) and img.lit(4, 4) == (0,), "rectangle contour : bords posés, intérieur vide")
img2 = R.Image(10, 10, "L", fond=0)
img2.ligne(0, 0, 9, 9, 255)
diag = all(img2.lit(i, i) == (255,) for i in range(10))
check(diag, "ligne diagonale : Bresenham pose la diagonale entière")
img3 = R.Image(4, 4, "RGB")
img3.remplit((7, 8, 9))
check(all(img3.lit(x, y) == (7, 8, 9) for x in range(4) for y in range(4)), "remplit : toute la grille")

# round-trip après dessin
check(pixels(R.decode(R.encode(img2))) == pixels(img2), "round-trip après dessin de ligne")

# ── 4) FAUX=0 : construction / accès invalides -> ValueError ──
check(leve(R.Image, 0, 5), "dimension nulle -> ValueError")
check(leve(R.Image, 5, 5, "CMYK"), "mode inconnu -> ValueError")
check(leve(R.Image(3, 3).pixel, 5, 0, (0, 0, 0)), "pixel hors cadre -> ValueError")
check(leve(R.Image(3, 3, "RGB").pixel, 0, 0, (0, 0)), "pixel mauvais nb de canaux -> ValueError")
check(leve(R.Image(3, 3, "RGB").pixel, 0, 0, (0, 0, 256)), "composante hors [0,255] -> ValueError")
check(leve(R.Image(3, 3, "L").pixel, 0, 0, True), "composante booléenne refusée -> ValueError")
check(leve(R.Image(5, 5).ligne, 0, 0, 9, 0, 0), "ligne extrémité hors cadre -> ValueError")
check(leve(R.Image(5, 5).rectangle, 4, 4, 1, 1, 0), "rectangle bornes inversées -> ValueError")

# ── 5) FAUX=0 : décodage d'un flux corrompu -> ValueError (jamais deviné) ──
bon = R.encode(R.Image(4, 4, "RGB", fond=(1, 2, 3)))
check(leve(R.decode, b"not a png at all!!!!"), "signature fausse -> ValueError")
corrompu_crc = bytearray(bon)
corrompu_crc[-5] ^= 0xFF                        # abîme un octet de data avant l'IEND CRC
check(leve(R.decode, bytes(corrompu_crc)), "CRC faux -> ValueError")
check(leve(R.decode, bon[:20]), "flux tronqué -> ValueError")
check(leve(R.decode, "pas des octets"), "type non-octets -> ValueError")

# ── 6) ORACLE : le CRC de l'IHDR est bien celui de la spec (vérif croisée indépendante) ──
ihdr_data = struct.pack(">IIBBBBB", 4, 4, 8, 2, 0, 0, 0)
crc_dans_fichier, = struct.unpack(">I", bon[8 + 8 + len(ihdr_data):8 + 8 + len(ihdr_data) + 4])
check(crc_dans_fichier == zlib.crc32(b"IHDR" + ihdr_data) & 0xFFFFFFFF, "oracle CRC IHDR conforme spec")


print(f"\n=== valide_raster_png : {ok}/{ok + ko} ===")
import sys
sys.exit(0 if ko == 0 else 1)
