# -*- coding: utf-8 -*-
"""VALIDE extrait_pdf : extraction de texte PDF, FAUX=0.

Stratégie sans dépendance : on ÉCRIT des PDF connus (document_pdf, déjà gaté) puis on les RÉ-EXTRAIT et on
vérifie que le texte retrouvé == le texte écrit. On couvre aussi un flux FlateDecode fabriqué à la main (zlib)
et un PDF sans couche texte (page vide honnête)."""
from __future__ import annotations

import os
import sys
import zlib

_ICI = os.path.dirname(os.path.abspath(__file__)) or "."
sys.path.insert(0, os.path.join(os.path.dirname(_ICI), "src"))

import document_pdf as DP
import extrait_pdf as EP

ok = ko = 0


def check(c, label):
    global ok, ko
    if c:
        ok += 1
    else:
        ko += 1
        print("  FAIL: " + label)


# (1) round-trip mono-page, plusieurs lignes
doc = DP.Document()
p = doc.page()
lignes = ["Le memoire porte sur la sobriete energetique.",
          "Chapitre 1 : introduction et problematique.",
          "Les resultats montrent une reduction de 43 pour cent."]
y = 800
for ln in lignes:
    p.texte(72, y, ln, taille=12); y -= 20
octets = DP.encode(doc)
pgs = EP.pages(octets)
check(len(pgs) == 1, "un PDF mono-page -> une page extraite")
for ln in lignes:
    check(ln in pgs[0], "ligne retrouvee VERBATIM : %r" % ln[:30])
check(pgs[0].count("\n") >= 2, "les sauts de ligne (Td) separent les lignes")

# (2) multi-page + ordre + attribution par page
doc = DP.Document()
p1 = doc.page(); p1.texte(72, 800, "PAGE UNE alpha", taille=12)
p2 = doc.page(); p2.texte(72, 800, "PAGE DEUX beta", taille=12)
p3 = doc.page(); p3.texte(72, 800, "PAGE TROIS gamma", taille=12)
pgs = EP.pages(DP.encode(doc))
check(len(pgs) == 3, "trois pages -> trois entrees")
check("alpha" in pgs[0] and "beta" in pgs[1] and "gamma" in pgs[2], "texte attribue a la BONNE page, dans l'ordre")
check("beta" not in pgs[0] and "alpha" not in pgs[1], "pas de fuite de texte entre pages")

# (3) caracteres speciaux : parentheses et backslash echappes dans le flux
doc = DP.Document()
p = doc.page(); p.texte(72, 800, "cout (net) = 50 \\ ou plus", taille=12)
pgs = EP.pages(DP.encode(doc))
check("(net)" in pgs[0], "parentheses echappees correctement decodees")

# (4) FlateDecode : un flux de contenu compresse zlib doit etre lu
flux_clair = b"BT /F1 12 Tf 72 800 Td (Texte compresse FlateDecode) Tj ET"
comp = zlib.compress(flux_clair)
pdf = bytearray()
pdf += b"%PDF-1.4\n"
offs = {}
def ajoute(num, corps):
    offs[num] = len(pdf)
    pdf.extend(("%d 0 obj\n" % num).encode()); pdf.extend(corps); pdf.extend(b"\nendobj\n")
ajoute(1, b"<< /Type /Catalog /Pages 2 0 R >>")
ajoute(2, b"<< /Type /Pages /Kids [3 0 R] /Count 1 >>")
ajoute(3, b"<< /Type /Page /Parent 2 0 R /MediaBox [0 0 595 842] /Contents 4 0 R >>")
ajoute(4, ("<< /Length %d /Filter /FlateDecode >>\nstream\n" % len(comp)).encode() + comp + b"\nendstream")
pdf += b"trailer\n<< /Size 5 /Root 1 0 R >>\n%%EOF"
pgs = EP.pages(bytes(pdf))
check(len(pgs) == 1 and "FlateDecode" in pgs[0], "flux FlateDecode (zlib) decompresse et lu")

# (5) page SANS couche texte -> vide HONNETE (pas d'invention)
doc = DP.Document()
p = doc.page(); p.rectangle(72, 72, 100, 100)      # que du vecteur, aucun Tj
pgs = EP.pages(DP.encode(doc))
check(len(pgs) == 1 and pgs[0] == "", "page sans texte -> chaine vide (honnete, pas d'invention)")
inf = EP.infos(DP.encode(doc))
check(inf["pages"] == 1 and inf["pages_avec_texte"] == 0, "infos signale 0 page avec texte (diagnostic scanne)")

# (6) garde d'entree : non-PDF -> ValueError
try:
    EP.pages(b"ceci n'est pas un pdf"); check(False, "non-PDF doit lever")
except ValueError:
    check(True, "non-PDF -> ValueError (pas de faux texte)")

# (7) texte() joint les pages
doc = DP.Document()
p1 = doc.page(); p1.texte(72, 800, "premier", taille=12)
p2 = doc.page(); p2.texte(72, 800, "second", taille=12)
t = EP.texte(DP.encode(doc))
check("premier" in t and "second" in t, "texte() concatene toutes les pages")

print("=== valide_extrait_pdf : %d/%d ===" % (ok, ok + ko))
sys.exit(0 if ko == 0 else 1)
