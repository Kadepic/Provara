"""
DOCUMENT PDF — noyau BORNÉ de la modalité DOCUMENT IMPRIMABLE (PDF 1.4), pur stdlib (2026-07-02).

POURQUOI (vision Yohan « outil universel toutes modalités » ; sortir un rapport/facture imprimable) : un PDF a un
NOYAU exact et vérifiable — sa STRUCTURE (objets numérotés, table de références croisées `xref` dont chaque entrée
est le décalage-octet EXACT de l'objet, trailer). C'est précisément la partie facile à corrompre ; ce module la
calcule au bon octet près et la RE-VÉRIFIE. Texte (polices standard, pas d'embarquement) + vecteur (lignes,
rectangles). Aucune dépendance (ni reportlab ni fpdf).

FAUX=0 — ce que ce module GARANTIT, et ce qu'il ne prétend PAS :
  • La table `xref` est EXACTE : l'offset annoncé de chaque objet == sa position réelle en octets (le validateur
    re-scanne indépendamment « N 0 obj » et exige l'égalité). `startxref` pointe le vrai début de la table.
  • Syntaxe conforme (header %PDF-1.4, objets bien formés, trailer /Root, %%EOF) ; chaînes de texte échappées
    (antislash, parenthèses ouvrante/fermante). Sortie DÉTERMINISTE (mêmes appels -> mêmes octets).
  • Coordonnées en points PDF (origine bas-gauche), placées EXACTEMENT ; hors page ou non finies -> ValueError.
  Ce module ne prétend PAS gérer TOUT PDF (images, polices embarquées, transparence, formulaires) : il garantit un
  sous-ensemble EXACT et structurellement valide (texte + vecteur simple, multi-page). Souverain, offline, stdlib pur.
"""
from __future__ import annotations

import math

_A4 = (595, 842)          # points (72 dpi) : largeur, hauteur A4


def _fini(x, nom):
    if isinstance(x, bool) or not isinstance(x, (int, float)) or not math.isfinite(x):
        raise ValueError(f"{nom} doit être un nombre fini (vu {x!r})")
    return float(x)


def _echappe(s: str) -> str:
    if not isinstance(s, str):
        raise ValueError("texte : str attendu")
    return s.replace("\\", r"\\").replace("(", r"\(").replace(")", r"\)")


def _nb(v) -> str:
    v = float(v)
    return str(int(v)) if v == int(v) else f"{v:.3f}".rstrip("0").rstrip(".")


class Page:
    """Une page. Coordonnées en points, origine BAS-gauche (convention PDF). Accumule des opérateurs de contenu."""

    def __init__(self, largeur: float = _A4[0], hauteur: float = _A4[1]):
        self.largeur = _fini(largeur, "largeur")
        self.hauteur = _fini(hauteur, "hauteur")
        if self.largeur <= 0 or self.hauteur <= 0:
            raise ValueError("dimensions de page > 0 requises")
        self._ops: list[str] = []

    def _dans(self, x, y):
        x = _fini(x, "x"); y = _fini(y, "y")
        if not (0 <= x <= self.largeur and 0 <= y <= self.hauteur):
            raise ValueError(f"point ({x},{y}) hors page {self.largeur}×{self.hauteur}")
        return x, y

    def texte(self, x: float, y: float, chaine: str, *, taille: float = 12) -> None:
        x, y = self._dans(x, y)
        taille = _fini(taille, "taille")
        if taille <= 0:
            raise ValueError("taille de police > 0 requise")
        self._ops.append(f"BT /F1 {_nb(taille)} Tf {_nb(x)} {_nb(y)} Td ({_echappe(chaine)}) Tj ET")

    def ligne(self, x0, y0, x1, y1, *, epaisseur: float = 1) -> None:
        x0, y0 = self._dans(x0, y0)
        x1, y1 = self._dans(x1, y1)
        self._ops.append(f"{_nb(epaisseur)} w {_nb(x0)} {_nb(y0)} m {_nb(x1)} {_nb(y1)} l S")

    def rectangle(self, x, y, largeur, hauteur, *, plein: bool = False, epaisseur: float = 1) -> None:
        x, y = self._dans(x, y)
        self._dans(x + largeur, y + hauteur)                # coin opposé dans la page
        op = "f" if plein else "S"
        self._ops.append(f"{_nb(epaisseur)} w {_nb(x)} {_nb(y)} {_nb(largeur)} {_nb(hauteur)} re {op}")

    def _contenu(self) -> bytes:
        return ("\n".join(self._ops)).encode("latin-1")


class Document:
    """Un PDF = une ou plusieurs pages."""

    def __init__(self):
        self.pages: list[Page] = []

    def page(self, largeur: float = _A4[0], hauteur: float = _A4[1]) -> Page:
        p = Page(largeur, hauteur)
        self.pages.append(p)
        return p


def encode(doc: Document) -> bytes:
    """Sérialise un `Document` en octets PDF 1.4 valides, `xref` exacte, déterministe."""
    if not isinstance(doc, Document) or not doc.pages:
        raise ValueError("document non vide requis")
    n_pages = len(doc.pages)

    # Numérotation : 1=Catalog, 2=Pages, 3=Font, puis page i -> (4+2i)=Page, (5+2i)=Content.
    obj_font = 3
    page_obj = lambda i: 4 + 2 * i
    cont_obj = lambda i: 5 + 2 * i
    n_objets = 3 + 2 * n_pages

    corps = bytearray()
    corps += b"%PDF-1.4\n"
    offsets = {}                                            # numéro d'objet -> décalage octet

    def ajoute(num: int, contenu: bytes):
        offsets[num] = len(corps)
        corps.extend(f"{num} 0 obj\n".encode("latin-1"))
        corps.extend(contenu)
        corps.extend(b"\nendobj\n")

    kids = " ".join(f"{page_obj(i)} 0 R" for i in range(n_pages))
    ajoute(1, b"<< /Type /Catalog /Pages 2 0 R >>")
    ajoute(2, f"<< /Type /Pages /Kids [{kids}] /Count {n_pages} >>".encode("latin-1"))
    ajoute(obj_font, b"<< /Type /Font /Subtype /Type1 /BaseFont /Helvetica >>")
    for i, p in enumerate(doc.pages):
        mb = f"[0 0 {_nb(p.largeur)} {_nb(p.hauteur)}]"
        page_dict = (f"<< /Type /Page /Parent 2 0 R /MediaBox {mb} "
                     f"/Resources << /Font << /F1 {obj_font} 0 R >> >> /Contents {cont_obj(i)} 0 R >>")
        ajoute(page_obj(i), page_dict.encode("latin-1"))
        flux = p._contenu()
        cont = bytearray()
        cont.extend(f"<< /Length {len(flux)} >>\nstream\n".encode("latin-1"))
        cont.extend(flux)
        cont.extend(b"\nendstream")
        ajoute(cont_obj(i), bytes(cont))

    # table xref
    debut_xref = len(corps)
    xref = bytearray()
    xref.extend(f"xref\n0 {n_objets + 1}\n".encode("latin-1"))
    xref.extend(b"0000000000 65535 f \n")                   # objet libre 0
    for num in range(1, n_objets + 1):
        xref.extend(f"{offsets[num]:010d} 00000 n \n".encode("latin-1"))
    corps.extend(xref)
    corps.extend(f"trailer\n<< /Size {n_objets + 1} /Root 1 0 R >>\nstartxref\n{debut_xref}\n%%EOF".encode("latin-1"))
    return bytes(corps)


def ecris(doc: Document, chemin: str) -> int:
    import os
    data = encode(doc)
    tmp = f"{chemin}.tmp.{os.getpid()}"
    with open(tmp, "wb") as f:
        f.write(data)
    os.replace(tmp, chemin)
    return len(data)


def lit_xref(octets: bytes) -> dict:
    """Re-lit la table xref déclarée : renvoie {num_objet: offset_déclaré} + startxref. FAUX=0 : structure invalide
    -> ValueError. (Le validateur croise ces offsets avec un scan indépendant de « N 0 obj ».)"""
    if not isinstance(octets, (bytes, bytearray)):
        raise ValueError("octets attendus")
    octets = bytes(octets)
    if not octets.startswith(b"%PDF-1."):
        raise ValueError("en-tête PDF absent")
    i = octets.rfind(b"startxref")
    if i < 0:
        raise ValueError("startxref absent")
    try:
        debut = int(octets[i + len(b"startxref"):].split(b"%%EOF")[0].strip())
    except ValueError:
        raise ValueError("startxref illisible")
    if octets[debut:debut + 4] != b"xref":
        raise ValueError("startxref ne pointe pas sur 'xref'")
    lignes = octets[debut:].split(b"\n")
    if not lignes[1].strip().startswith(b"0 "):
        raise ValueError("section xref mal formée")
    n = int(lignes[1].split()[1])
    offs = {}
    for k in range(n):
        entree = lignes[2 + k]
        if len(entree.rstrip()) < 18:
            raise ValueError("entrée xref tronquée")
        champs = entree.split()
        if champs[2] == b"n":
            offs[k] = int(champs[0])
    return {"startxref": debut, "offsets": offs, "taille": n}
