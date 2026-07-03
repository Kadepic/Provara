# -*- coding: utf-8 -*-
"""OCR BORNÉ — reconnaissance de texte NET par appariement de gabarits, FAUX=0 (2026-07-03).

POURQUOI (mandat Yohan « OCR ») : lire du TEXTE dans une image. La vraie OCR généraliste (photo de document
quelconque) exige un modèle appris — contraire au principe model-free. On livre donc le cas BORNÉ EXACT, comme
partout dans ce projet : reconnaissance de texte NET (fort contraste, police bitmap régulière) par appariement
de GABARITS, avec ABSTENTION honnête (« ? ») sur un glyphe qu'on ne reconnaît pas — jamais une lettre inventée.

Ce module fournit AUSSI le rendu (`rend`) dans la même police bitmap : il permet de générer une image de texte
et de la relire exactement (round-trip vérifiable), et sert de socle honnête extensible (d'autres polices/tailles
= d'autres gabarits). Portée déclarée : texte horizontal, une police 5×7, tailles multiples de l'échelle.

FAUX=0 : `ocr` ne rend un caractère QUE si le gabarit correspond sous un seuil de distance ; sinon « ? ». Aucune
invention. Stdlib pur (réutilise raster_png pour décoder un PNG en pixels).
"""
from __future__ import annotations

# ————————————————— POLICE BITMAP 5×7 (glyphes DISTINCTS ; '#' = encre, ' ' = fond) —————————————————
_FONT = {
    " ": ("     ", "     ", "     ", "     ", "     ", "     ", "     "),
    "A": (" ### ", "#   #", "#   #", "#####", "#   #", "#   #", "#   #"),
    "B": ("#### ", "#   #", "#   #", "#### ", "#   #", "#   #", "#### "),
    "C": (" ####", "#    ", "#    ", "#    ", "#    ", "#    ", " ####"),
    "D": ("#### ", "#   #", "#   #", "#   #", "#   #", "#   #", "#### "),
    "E": ("#####", "#    ", "#    ", "#### ", "#    ", "#    ", "#####"),
    "F": ("#####", "#    ", "#    ", "#### ", "#    ", "#    ", "#    "),
    "G": (" ####", "#    ", "#    ", "#  ##", "#   #", "#   #", " ####"),
    "H": ("#   #", "#   #", "#   #", "#####", "#   #", "#   #", "#   #"),
    "I": ("#####", "  #  ", "  #  ", "  #  ", "  #  ", "  #  ", "#####"),
    "J": ("  ###", "   # ", "   # ", "   # ", "#  # ", "#  # ", " ##  "),
    "K": ("#   #", "#  # ", "# #  ", "##   ", "# #  ", "#  # ", "#   #"),
    "L": ("#    ", "#    ", "#    ", "#    ", "#    ", "#    ", "#####"),
    "M": ("#   #", "## ##", "# # #", "#   #", "#   #", "#   #", "#   #"),
    "N": ("#   #", "##  #", "# # #", "#  ##", "#   #", "#   #", "#   #"),
    "O": (" ### ", "#   #", "#   #", "#   #", "#   #", "#   #", " ### "),
    "P": ("#### ", "#   #", "#   #", "#### ", "#    ", "#    ", "#    "),
    "Q": (" ### ", "#   #", "#   #", "#   #", "# # #", "#  # ", " ## #"),
    "R": ("#### ", "#   #", "#   #", "#### ", "# #  ", "#  # ", "#   #"),
    "S": (" ####", "#    ", "#    ", " ### ", "    #", "    #", "#### "),
    "T": ("#####", "  #  ", "  #  ", "  #  ", "  #  ", "  #  ", "  #  "),
    "U": ("#   #", "#   #", "#   #", "#   #", "#   #", "#   #", " ### "),
    "V": ("#   #", "#   #", "#   #", "#   #", "#   #", " # # ", "  #  "),
    "W": ("#   #", "#   #", "#   #", "#   #", "# # #", "## ##", "#   #"),
    "X": ("#   #", "#   #", " # # ", "  #  ", " # # ", "#   #", "#   #"),
    "Y": ("#   #", "#   #", " # # ", "  #  ", "  #  ", "  #  ", "  #  "),
    "Z": ("#####", "    #", "   # ", "  #  ", " #   ", "#    ", "#####"),
    "0": (" ### ", "#   #", "#  ##", "# # #", "##  #", "#   #", " ### "),
    "1": ("  #  ", " ##  ", "  #  ", "  #  ", "  #  ", "  #  ", " ### "),
    "2": (" ### ", "#   #", "    #", "   # ", "  #  ", " #   ", "#####"),
    "3": ("#####", "   # ", "  #  ", "   # ", "    #", "#   #", " ### "),
    "4": ("   # ", "  ## ", " # # ", "#  # ", "#####", "   # ", "   # "),
    "5": ("#####", "#    ", "#### ", "    #", "    #", "#   #", " ### "),
    "6": (" ### ", "#    ", "#    ", "#### ", "#   #", "#   #", " ### "),
    "7": ("#####", "    #", "   # ", "  #  ", " #   ", " #   ", " #   "),
    "8": (" ### ", "#   #", "#   #", " ### ", "#   #", "#   #", " ### "),
    "9": (" ### ", "#   #", "#   #", " ####", "    #", "    #", " ### "),
    ".": ("     ", "     ", "     ", "     ", "     ", "  ## ", "  ## "),
    "-": ("     ", "     ", "     ", "#####", "     ", "     ", "     "),
    ":": ("     ", "  ## ", "  ## ", "     ", "  ## ", "  ## ", "     "),
    "?": (" ### ", "#   #", "    #", "   # ", "  #  ", "     ", "  #  "),
    "!": ("  #  ", "  #  ", "  #  ", "  #  ", "  #  ", "     ", "  #  "),
}
_H, _W = 7, 5
_ESPACE_INTER = 1           # colonnes de fond entre deux glyphes
_NOIR, _BLANC = (0, 0, 0), (255, 255, 255)


def rend(texte, echelle: int = 3, marge: int = 4):
    """Rend `texte` (majuscules/chiffres/ponctuation de la police) en une image raster (encre noire sur blanc).
    `echelle` = facteur d'agrandissement de chaque pixel de glyphe. Caractère hors police -> espace."""
    import raster_png
    texte = str(texte).upper()
    n = len(texte)
    larg = marge * 2 + n * _W * echelle + max(0, n - 1) * _ESPACE_INTER * echelle
    haut = marge * 2 + _H * echelle
    img = raster_png.Image(larg, haut, mode="RGB", fond=_BLANC)
    x0 = marge
    for ch in texte:
        glyphe = _FONT.get(ch, _FONT[" "])
        for gy in range(_H):
            for gx in range(_W):
                if glyphe[gy][gx] == "#":
                    for dy in range(echelle):
                        for dx in range(echelle):
                            img.pixel(x0 + gx * echelle + dx, marge + gy * echelle + dy, _NOIR)
        x0 += (_W + _ESPACE_INTER) * echelle
    return img


def _grille_encre(img):
    """Matrice booléenne encre/fond (encre = luminance < 128). Renvoie (largeur, hauteur, get(x,y))."""
    L, H = img.largeur, img.hauteur

    def encre(x, y):
        r, g, b = img.lit(x, y)[:3]
        return (0.299 * r + 0.587 * g + 0.114 * b) < 128
    return L, H, encre


def _bornes_lignes(L, H, encre):
    """Lignes de texte = bandes de rangées contenant de l'encre (projection horizontale)."""
    rangee_encree = [any(encre(x, y) for x in range(L)) for y in range(H)]
    lignes, deb = [], None
    for y in range(H):
        if rangee_encree[y] and deb is None:
            deb = y
        elif not rangee_encree[y] and deb is not None:
            lignes.append((deb, y)); deb = None
    if deb is not None:
        lignes.append((deb, H))
    return lignes


def _glyphes_de_ligne(L, encre, y0, y1):
    """Boîtes de glyphes dans une ligne = colonnes d'encre séparées par des colonnes vides (projection verticale).
    Renvoie une liste de (x0, x1) + les LARGEURS d'espace pour insérer les espaces mots."""
    col_encree = [any(encre(x, y) for y in range(y0, y1)) for x in range(L)]
    boites, deb = [], None
    for x in range(L):
        if col_encree[x] and deb is None:
            deb = x
        elif not col_encree[x] and deb is not None:
            boites.append((deb, x)); deb = None
    if deb is not None:
        boites.append((deb, L))
    return boites


def _norme_glyphe(encre, x0, x1, y0, y1):
    """Ré-échantillonne la boîte du glyphe sur la grille 5×7 (plus proche voisin) -> tuple de lignes '#'/' '."""
    bw, bh = max(1, x1 - x0), max(1, y1 - y0)
    lignes = []
    for gy in range(_H):
        row = []
        sy = y0 + (gy * bh) // _H
        for gx in range(_W):
            sx = x0 + (gx * bw) // _W
            row.append("#" if encre(sx, sy) else " ")
        lignes.append("".join(row))
    return tuple(lignes)


def _distance(a, b):
    return sum(1 for ya, yb in zip(a, b) for ca, cb in zip(ya, yb) if ca != cb)


def _largeur_resample(lignes):
    """Normalise la LARGEUR sur la boîte d'encre (répare les glyphes étroits comme « 1 »), MAIS garde la HAUTEUR
    telle quelle (position verticale préservée : distingue « - » au milieu de « . » en bas). Ré-échantillonne
    seulement les colonnes en 5, laisse les 7 rangées."""
    xs = [x for y in range(len(lignes)) for x in range(len(lignes[y])) if lignes[y][x] == "#"]
    if not xs:
        return tuple(" " * _W for _ in range(_H))
    x0, x1 = min(xs), max(xs) + 1
    bw = x1 - x0
    out = []
    for gy in range(_H):
        row = []
        src = lignes[gy] if gy < len(lignes) else " " * len(lignes[0])
        for gx in range(_W):
            sx = x0 + (gx * bw) // _W
            row.append("#" if sx < len(src) and src[sx] == "#" else " ")
        out.append("".join(row))
    return tuple(out)


_TEMPLATES = None


def _templates():
    """Gabarits normalisés en largeur (colonnes -> encre, rangées inchangées), calculés une fois."""
    global _TEMPLATES
    if _TEMPLATES is None:
        _TEMPLATES = {ch: _largeur_resample(gab) for ch, gab in _FONT.items() if ch != " "}
    return _TEMPLATES


def _reconnait(grille, seuil: int = 6):
    """Caractère dont le gabarit (largeur normalisée) est le plus proche sous le seuil de Hamming, sinon '?'."""
    cible = _largeur_resample(grille)
    best, bestd = "?", 10 ** 9
    for ch, gab in _templates().items():
        d = _distance(cible, gab)
        if d < bestd:
            best, bestd = ch, d
    return best if bestd <= seuil else "?"


def ocr(source, *, seuil: int = 6):
    """Reconnaît le texte d'une image NETTE (objet raster_png.Image OU octets PNG). Renvoie le texte reconnu ;
    un glyphe non reconnu -> « ? » (jamais inventé). Lignes séparées par des sauts de ligne, espaces mots
    déduits des grands intervalles entre glyphes."""
    import raster_png
    img = raster_png.decode(source) if isinstance(source, (bytes, bytearray)) else source
    L, H, encre = _grille_encre(img)
    lignes_txt = []
    for (y0, y1) in _bornes_lignes(L, H, encre):
        boites = _glyphes_de_ligne(L, encre, y0, y1)
        if not boites:
            continue
        # espace MOT = PAS manquant. On mesure le PAS régulier via l'écart médian entre DÉBUTS de glyphes
        # (invariant à l'étendue d'encre — la ponctuation centrée n'insère plus de faux espace). Une case vide
        # (espace) fait sauter le début du glyphe suivant d'environ deux pas.
        pas = sorted(boites[i][0] - boites[i - 1][0] for i in range(1, len(boites)))
        pitch = pas[len(pas) // 2] if pas else 0
        out = []
        prev_deb = None
        for (x0, x1) in boites:
            if prev_deb is not None and pitch and (x0 - prev_deb) > 1.6 * pitch:
                out.append(" ")
            out.append(_reconnait(_norme_glyphe(encre, x0, x1, y0, y1), seuil))
            prev_deb = x0
        lignes_txt.append("".join(out))
    return "\n".join(lignes_txt).strip()


def contient_texte(source, *, seuil: int = 6) -> bool:
    """True si l'image contient du texte reconnaissable (≥1 caractère non-« ? »)."""
    txt = ocr(source, seuil=seuil)
    return any(c not in " ?\n" for c in txt)
