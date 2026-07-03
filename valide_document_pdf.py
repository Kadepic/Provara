"""VALIDE document_pdf.py — xref exacte (scan indépendant des offsets) + structure + FAUX=0.

Oracle indépendant : on re-scanne « N 0 obj » dans les octets et on EXIGE que chaque offset trouvé == l'offset
déclaré par la table xref. C'est le contrat le plus facile à corrompre ; le prouver = PDF structurellement valide.
Négatifs : hors page, dimensions ≤ 0, document vide -> ValueError.
"""
import re

import document_pdf as D

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


# ── Document de test : 2 pages, texte + vecteur ──
doc = D.Document()
p1 = doc.page()
p1.texte(72, 800, "Rapport (test) : a\\b", taille=14)
p1.ligne(72, 780, 523, 780)
p1.rectangle(72, 700, 200, 50, plein=False)
p2 = doc.page(400, 300)
p2.texte(20, 250, "Page 2")
p2.rectangle(10, 10, 100, 100, plein=True)
octets = D.encode(doc)

# ── 1) Structure de base ──
check(octets.startswith(b"%PDF-1.4"), "en-tête %PDF-1.4")
check(octets.rstrip().endswith(b"%%EOF"), "se termine par %%EOF")
check(b"/Type /Catalog" in octets and b"/Root 1 0 R" in octets, "catalog + trailer /Root")
check(octets.count(b"/Type /Page ") == 2 or octets.count(b"/Type /Page\n") + octets.count(b"/Type /Page ") == 2, "2 objets Page")

# ── 2) ORACLE xref : offset déclaré == position réelle de « N 0 obj » (scan indépendant) ──
declare = D.lit_xref(octets)["offsets"]
reels = {}
for m in re.finditer(rb"(\d+) 0 obj", octets):
    num = int(m.group(1))
    reels.setdefault(num, m.start())
check(set(declare) == set(reels), f"xref : mêmes objets déclarés que trouvés ({len(declare)} vs {len(reels)})")
tous = all(declare[k] == reels[k] for k in declare)
check(tous, "xref : chaque offset déclaré == position réelle de l'objet")

# startxref pointe bien sur 'xref'
sx = D.lit_xref(octets)["startxref"]
check(octets[sx:sx + 4] == b"xref", "startxref pointe sur la table xref")

# nombre d'objets = 3 + 2·pages = 7 (pour 2 pages)
check(declare and max(declare) == 7 and len(declare) == 7, "7 objets pour 2 pages (1 Catalog+1 Pages+1 Font+2×(Page+Content))")

# ── 3) Contenu : opérateurs texte/vecteur présents et échappement ──
check(b"(Rapport \\(test\\) : a\\\\b) Tj" in octets, "texte échappé (parenthèses + backslash)")
check(b" re S" in octets and b" re f" in octets, "rectangles contour (S) et plein (f)")
check(b" l S" in octets, "ligne tracée (l S)")
check(b"/BaseFont /Helvetica" in octets, "police standard Helvetica")

# ── 4) Déterminisme ──
doc2 = D.Document()
q = doc2.page()
q.texte(72, 800, "Rapport (test) : a\\b", taille=14)
q.ligne(72, 780, 523, 780)
q.rectangle(72, 700, 200, 50, plein=False)
r = doc2.page(400, 300)
r.texte(20, 250, "Page 2")
r.rectangle(10, 10, 100, 100, plein=True)
check(D.encode(doc2) == octets, "déterminisme : mêmes appels -> mêmes octets")

# ── 5) FAUX=0 ──
check(leve(D.encode, D.Document()), "document sans page -> ValueError")
check(leve(D.Page().texte, -1, 100, "x"), "texte hors page (x<0) -> ValueError")
check(leve(D.Page().texte, 100, 100, "x", taille=0), "taille de police nulle -> ValueError")
check(leve(D.Page().ligne, 0, 0, 9999, 0), "ligne hors page -> ValueError")
check(leve(D.Page().rectangle, 500, 800, 500, 500), "rectangle débordant -> ValueError")
check(leve(D.Page, 0, 100), "page de largeur nulle -> ValueError")
check(leve(D.Page().texte, 100, 100, 12345), "texte non-str -> ValueError")
check(leve(D.lit_xref, b"pas un pdf"), "lit_xref sur non-PDF -> ValueError")

print(f"\n=== valide_document_pdf : {ok}/{ok + ko} ===")
import sys
sys.exit(0 if ko == 0 else 1)
