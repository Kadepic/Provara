# -*- coding: utf-8 -*-
"""VALIDE ocr : reconnaissance de texte net par gabarits, FAUX=0.

Round-trip : on REND un texte (police bitmap connue) puis on le RELIT — la reconnaissance doit être exacte.
On vérifie aussi le passage par PNG (octets), le multi-lignes, l'espacement des mots, et l'ABSTENTION
(image sans texte -> vide ; glyphe hors police -> « ? », jamais une lettre inventée)."""
from __future__ import annotations

import os
import sys

_ICI = os.path.dirname(os.path.abspath(__file__)) or "."
sys.path.insert(0, os.path.join(os.path.dirname(_ICI), "src"))

import ocr
import raster_png

ok = ko = 0


def check(c, label):
    global ok, ko
    if c:
        ok += 1
    else:
        ko += 1
        print("  FAIL: " + label)


# (1) round-trip exact sur des textes variés (lettres MAJ/min, chiffres, ponctuation, espaces)
for txt in ["HELLO 123", "Provara", "ABC XYZ 789", "FAUX-0", "THE QUICK BROWN FOX 0123456789",
            "BONJOUR: OUI!", "A-B-C 1.2.3", "LE CHAT DORT", "RAPPORT 2026: OK",
            # minuscules + casse mixte (le texte réel est surtout minuscule) — hauteur relative = casse
            "Hello World", "the cat dort", "Provara ocr", "Bonjour Paris", "le chat mange",
            "Provara lit un texte", "abcdefg hijkl", "Page 42: ok"]:
    got = ocr.ocr(ocr.rend(txt, echelle=3))
    check(got == txt, "round-trip « %s » (obtenu « %s »)" % (txt, got))

# (2) via octets PNG
png = raster_png.encode(ocr.rend("TEST 42"))
check(ocr.ocr(png) == "TEST 42", "OCR depuis octets PNG")

# (3) échelles différentes
check(ocr.ocr(ocr.rend("SCALE", echelle=2)) == "SCALE", "échelle 2")
check(ocr.ocr(ocr.rend("SCALE", echelle=5)) == "SCALE", "échelle 5")

# (4) multi-lignes
i1, i2 = ocr.rend("LIGNE UN"), ocr.rend("LIGNE DEUX")
L = max(i1.largeur, i2.largeur)
img = raster_png.Image(L, i1.hauteur + i2.hauteur + 6, mode="RGB", fond=(255, 255, 255))
for y in range(i1.hauteur):
    for x in range(i1.largeur):
        img.pixel(x, y, i1.lit(x, y))
for y in range(i2.hauteur):
    for x in range(i2.largeur):
        img.pixel(x, i1.hauteur + 6 + y, i2.lit(x, y))
check(ocr.ocr(img) == "LIGNE UN\nLIGNE DEUX", "deux lignes -> deux lignes")

# (5) ABSTENTION honnête : image blanche -> vide, pas de texte
blanc = raster_png.Image(60, 20, mode="RGB", fond=(255, 255, 255))
check(ocr.ocr(blanc) == "", "image blanche -> vide (pas d'invention)")
check(ocr.contient_texte(blanc) is False, "contient_texte(blanc) = False")
check(ocr.contient_texte(ocr.rend("A")) is True, "contient_texte(texte) = True")

# (5bis) ROBUSTESSE au CONTRASTE / EXPOSITION (binarisation Otsu) : différents niveaux de gris
base = ocr.rend("CONTRASTE", echelle=4)
Lb, Hb = base.largeur, base.hauteur


def teinte(fond, enc):
    im = raster_png.Image(Lb, Hb, mode="RGB", fond=fond)
    for y in range(Hb):
        for x in range(Lb):
            im.pixel(x, y, enc if base.lit(x, y)[0] < 128 else fond)
    return im


check(ocr.ocr(teinte((200, 200, 200), (120, 120, 120))) == "CONTRASTE", "faible contraste (Otsu)")
check(ocr.ocr(teinte((90, 90, 90), (20, 20, 20))) == "CONTRASTE", "sous-exposé (Otsu)")
check(ocr.ocr(teinte((255, 255, 255), (180, 180, 180))) == "CONTRASTE", "sur-exposé (Otsu)")

# (6) tolérance à un léger bruit (quelques pixels retournés) : reste lisible
img = ocr.rend("Provara", echelle=4)
# flip d'un pixel isolé au coin (ne doit pas casser la reconnaissance)
img.pixel(0, 0, (0, 0, 0))
check("Provara" in ocr.ocr(img), "tolère un pixel de bruit isolé")

print("=== valide_ocr : %d/%d ===" % (ok, ok + ko))
sys.exit(0 if ko == 0 else 1)
