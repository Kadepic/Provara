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
    # — MINUSCULES (5×7). Les x-height (a,c,e,m,n,o,r,s,u,v,w,x,z) ont les 2 rangées du haut VIDES : leur boîte
    #   est plus COURTE que les capitales -> la classe de hauteur (cf. _reconnait) les distingue de « O », « C »…
    "a": ("     ", "     ", " ### ", "    #", " ####", "#   #", " ####"),
    "b": ("#    ", "#    ", "#### ", "#   #", "#   #", "#   #", "#### "),
    "c": ("     ", "     ", " ####", "#    ", "#    ", "#    ", " ####"),
    "d": ("    #", "    #", " ####", "#   #", "#   #", "#   #", " ####"),
    "e": ("     ", "     ", " ### ", "#   #", "#####", "#    ", " ####"),
    "f": ("  ## ", " #   ", "###  ", " #   ", " #   ", " #   ", " #   "),
    "g": ("     ", " ####", "#   #", " ####", "    #", "#   #", " ### "),
    "h": ("#    ", "#    ", "#### ", "#   #", "#   #", "#   #", "#   #"),
    "i": ("  #  ", "     ", " ##  ", "  #  ", "  #  ", "  #  ", " ### "),
    "j": ("   # ", "     ", "  ## ", "   # ", "   # ", "#  # ", " ##  "),
    "k": ("#    ", "#    ", "#  # ", "# #  ", "##   ", "# #  ", "#  # "),
    "l": (" ##  ", "  #  ", "  #  ", "  #  ", "  #  ", "  #  ", " ### "),
    "m": ("     ", "     ", "## # ", "# # #", "# # #", "#   #", "#   #"),
    "n": ("     ", "     ", "#### ", "#   #", "#   #", "#   #", "#   #"),
    "o": ("     ", "     ", " ### ", "#   #", "#   #", "#   #", " ### "),
    "p": ("     ", "#### ", "#   #", "#   #", "#### ", "#    ", "#    "),
    "q": ("     ", " ####", "#   #", "#   #", " ####", "    #", "    #"),
    "r": ("     ", "     ", "# ## ", "##   ", "#    ", "#    ", "#    "),
    "s": ("     ", "     ", " ####", "#    ", " ### ", "    #", "#### "),
    "t": (" #   ", " #   ", "###  ", " #   ", " #   ", " #  #", "  ## "),
    "u": ("     ", "     ", "#   #", "#   #", "#   #", "#   #", " ####"),
    "v": ("     ", "     ", "#   #", "#   #", "#   #", " # # ", "  #  "),
    "w": ("     ", "     ", "#   #", "#   #", "# # #", "# # #", " # # "),
    "x": ("     ", "     ", "#   #", " # # ", "  #  ", " # # ", "#   #"),
    "y": ("     ", "#   #", "#   #", "#   #", " ####", "    #", " ### "),
    "z": ("     ", "     ", "#####", "   # ", "  #  ", " #   ", "#####"),
}
# Les minuscules x-height ont le HAUT VIDE : échantillonnées sur la hauteur de LIGNE (cf. _norme_glyphe reçoit
# les bornes de la ligne), leur position verticale distingue « o » de « O », « c » de « C »… sans logique en plus.
_H, _W = 7, 5
_ESPACE_INTER = 1           # colonnes de fond entre deux glyphes
_NOIR, _BLANC = (0, 0, 0), (255, 255, 255)


def rend(texte, echelle: int = 3, marge: int = 4):
    """Rend `texte` (majuscules/chiffres/ponctuation de la police) en une image raster (encre noire sur blanc).
    `echelle` = facteur d'agrandissement de chaque pixel de glyphe. Caractère hors police -> espace."""
    import raster_png
    texte = str(texte)                    # la police couvre MAJUSCULES + minuscules ; on rend la casse telle quelle
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


def _seuil_otsu(hist, total):
    """Seuil de binarisation OPTIMAL (méthode d'Otsu : maximise la variance inter-classes de l'histogramme des
    luminances). Rend l'OCR robuste au CONTRASTE et à la LUMINOSITÉ variables (photos, scans pâles) au lieu d'un
    seuil fixe. Déterministe."""
    somme = sum(i * hist[i] for i in range(256))
    somme_b = 0.0
    poids_b = 0
    var_max, seuil = -1.0, 127
    for t in range(256):
        poids_b += hist[t]
        if poids_b == 0:
            continue
        poids_f = total - poids_b
        if poids_f == 0:
            break
        somme_b += t * hist[t]
        moy_b = somme_b / poids_b
        moy_f = (somme - somme_b) / poids_f
        var = poids_b * poids_f * (moy_b - moy_f) ** 2
        if var > var_max:
            var_max, seuil = var, t
    return seuil


def _grille_encre(img):
    """Matrice booléenne encre/fond. Le seuil est calculé par Otsu sur l'histogramme (robuste au contraste),
    avec repli à 128 sur une image quasi-uniforme. L'encre est la classe SOMBRE (< seuil)."""
    L, H = img.largeur, img.hauteur

    def lum(x, y):
        r, g, b = img.lit(x, y)[:3]
        return int(0.299 * r + 0.587 * g + 0.114 * b)

    hist = [0] * 256
    for y in range(H):
        for x in range(L):
            hist[lum(x, y)] += 1
    total = L * H
    # écart de luminance : s'il est réel (fond vs encre séparables), Otsu ; sinon image ~uniforme -> seuil neutre.
    niveaux = [i for i in range(256) if hist[i]]
    ecart = (niveaux[-1] - niveaux[0]) if niveaux else 0
    seuil = _seuil_otsu(hist, total) if ecart >= 8 else 128

    def encre(x, y):
        return lum(x, y) <= seuil
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


def _reconnait(grille, seuil: int = 6, marge: int = 2):
    """Caractère dont le gabarit (largeur normalisée) est le plus proche — SI sous le seuil de Hamming ET
    nettement séparé du 2e candidat (marge). FAUX=0 : un glyphe AMBIGU (deux gabarits proches, ex. un caractère
    déformé qui ressemble autant à E qu'à !) -> '?' plutôt qu'un choix arbitraire."""
    cible = _largeur_resample(grille)
    ds = sorted((_distance(cible, gab), ch) for ch, gab in _templates().items())
    if not ds:
        return "?"
    d1, c1 = ds[0]
    d2 = next((d for d, c in ds if c != c1), d1 + 10)
    return c1 if (d1 <= seuil and (d2 - d1) >= marge) else "?"


# ————————————————— RECONNAISSANCE PAR CARACTÉRISTIQUES (model-free, robuste aux polices) —————————————————
# Jeu de traits CLASSIQUE de l'OCR sans modèle (littérature) : STRUCTURELS (nombre de TROUS = Euler, extrémités)
# + STATISTIQUES (zonage NxM, profils de projection H/V, croisements H/V, ratio d'aspect) + MOMENTS DE HU
# (invariants à l'échelle/rotation/translation). Comparaison au plus proche PROTOTYPE (nos gabarits + variantes
# dilatée/érodée pour la variation d'épaisseur). Abstention STRICTE (FAUX=0) : « ? » dès que l'écart au 2e
# candidat est faible ou la distance élevée -> jamais une lettre fausse. Ne remplace PAS le gabarit (précis sur
# la police de référence) : c'est un REPLI quand le gabarit s'abstient, pour les polices voisines.
import math as _math

_CW, _CH = 14, 18            # grille canonique haute résolution pour les traits


def _canon_encre(encre, x0, x1, y0, y1):
    bw, bh = max(1, x1 - x0), max(1, y1 - y0)
    return [[bool(encre(x0 + (gx * bw) // _CW, y0 + (gy * bh) // _CH)) for gx in range(_CW)] for gy in range(_CH)]


def _canon_lignes(lignes):
    ys = [y for y in range(len(lignes)) if "#" in lignes[y]]
    xs = [x for y in range(len(lignes)) for x in range(len(lignes[y])) if lignes[y][x] == "#"]
    if not ys or not xs:
        return [[False] * _CW for _ in range(_CH)]
    y0, y1, x0, x1 = min(ys), max(ys) + 1, min(xs), max(xs) + 1
    bw, bh = x1 - x0, y1 - y0
    g = []
    for gy in range(_CH):
        sy = y0 + (gy * bh) // _CH
        row = lignes[sy] if sy < len(lignes) else ""
        g.append([(x0 + (gx * bw) // _CW) < len(row) and row[x0 + (gx * bw) // _CW] == "#" for gx in range(_CW)])
    return g


def _dilate(g):
    H, W = len(g), len(g[0])
    return [[g[y][x] or (x > 0 and g[y][x - 1]) or (x < W - 1 and g[y][x + 1])
             or (y > 0 and g[y - 1][x]) or (y < H - 1 and g[y + 1][x]) for x in range(W)] for y in range(H)]


def _erode(g):
    H, W = len(g), len(g[0])
    return [[g[y][x] and (x == 0 or g[y][x - 1]) and (x == W - 1 or g[y][x + 1])
             and (y == 0 or g[y - 1][x]) and (y == H - 1 or g[y + 1][x]) for x in range(W)] for y in range(H)]


def _euler_trous(g):
    """Nombre de régions de fond ENCERCLÉES (topologie, robuste à la police)."""
    H, W = len(g), len(g[0])
    att = [[False] * W for _ in range(H)]
    pile = [(x, y) for x in range(W) for y in (0, H - 1) if not g[y][x]]
    pile += [(x, y) for y in range(H) for x in (0, W - 1) if not g[y][x]]
    while pile:
        x, y = pile.pop()
        if 0 <= x < W and 0 <= y < H and not att[y][x] and not g[y][x]:
            att[y][x] = True
            pile += [(x + 1, y), (x - 1, y), (x, y + 1), (x, y - 1)]
    trous, vus = 0, [[False] * W for _ in range(H)]
    for y in range(H):
        for x in range(W):
            if not g[y][x] and not att[y][x] and not vus[y][x]:
                trous += 1
                p = [(x, y)]
                while p:
                    a, b = p.pop()
                    if 0 <= a < W and 0 <= b < H and not vus[b][a] and not g[b][a] and not att[b][a]:
                        vus[b][a] = True
                        p += [(a + 1, b), (a - 1, b), (a, b + 1), (a, b - 1)]
    return trous


def _hu(g):
    """7 moments de Hu (invariants) sur la grille, log-transformés pour l'échelle."""
    pts = [(x, y) for y in range(len(g)) for x in range(len(g[0])) if g[y][x]]
    if not pts:
        return [0.0] * 7
    n = len(pts)
    xb = sum(p[0] for p in pts) / n
    yb = sum(p[1] for p in pts) / n

    def mu(p, q):
        return sum((x - xb) ** p * (y - yb) ** q for x, y in pts)
    m00 = float(n)

    def eta(p, q):
        return mu(p, q) / (m00 ** (((p + q) / 2.0) + 1.0))
    e20, e02, e11 = eta(2, 0), eta(0, 2), eta(1, 1)
    e30, e03, e21, e12 = eta(3, 0), eta(0, 3), eta(2, 1), eta(1, 2)
    h = [0.0] * 7
    h[0] = e20 + e02
    h[1] = (e20 - e02) ** 2 + 4 * e11 ** 2
    h[2] = (e30 - 3 * e12) ** 2 + (3 * e21 - e03) ** 2
    h[3] = (e30 + e12) ** 2 + (e21 + e03) ** 2
    h[4] = ((e30 - 3 * e12) * (e30 + e12) * ((e30 + e12) ** 2 - 3 * (e21 + e03) ** 2)
            + (3 * e21 - e03) * (e21 + e03) * (3 * (e30 + e12) ** 2 - (e21 + e03) ** 2))
    h[5] = ((e20 - e02) * ((e30 + e12) ** 2 - (e21 + e03) ** 2) + 4 * e11 * (e30 + e12) * (e21 + e03))
    h[6] = ((3 * e21 - e03) * (e30 + e12) * ((e30 + e12) ** 2 - 3 * (e21 + e03) ** 2)
            - (e30 - 3 * e12) * (e21 + e03) * (3 * (e30 + e12) ** 2 - (e21 + e03) ** 2))
    return [(-1 if v < 0 else 1) * _math.log10(abs(v) + 1e-30) for v in h]


def _features(g):
    """Vecteur de traits d'un glyphe : trous(Euler), zonage 4×4, profils H/V, croisements H/V, aspect, Hu."""
    H, W = len(g), len(g[0])
    trous = _euler_trous(g)
    zones = []
    for zr in range(4):
        for zc in range(4):
            y0, y1 = zr * H // 4, (zr + 1) * H // 4
            x0, x1 = zc * W // 4, (zc + 1) * W // 4
            aire = max(1, (y1 - y0) * (x1 - x0))
            zones.append(sum(g[y][x] for y in range(y0, y1) for x in range(x0, x1)) / aire)
    prof_c = [sum(g[y][x] for y in range(H)) / H for x in range(W)]
    prof_r = [sum(g[y][x] for x in range(W)) / W for y in range(H)]
    crois_r = [sum(1 for x in range(1, W) if g[y][x] != g[y][x - 1]) / 2.0 for y in range(H)]
    crois_c = [sum(1 for y in range(1, H) if g[y][x] != g[y - 1][x]) / 2.0 for x in range(W)]
    xs = [x for y in range(H) for x in range(W) if g[y][x]]
    ys = [y for y in range(H) for x in range(W) if g[y][x]]
    aspect = ((max(xs) - min(xs) + 1) / (max(ys) - min(ys) + 1)) if xs else 1.0
    return {"trous": trous, "zones": zones, "pc": prof_c, "pr": prof_r,
            "cr": crois_r, "cc": crois_c, "aspect": aspect, "hu": _hu(g)}


def _dist_features(a, b):
    d = 5.0 * abs(a["trous"] - b["trous"])
    d += sum((u - v) ** 2 for u, v in zip(a["zones"], b["zones"]))
    d += 0.3 * sum((u - v) ** 2 for u, v in zip(a["pc"], b["pc"]))
    d += 0.3 * sum((u - v) ** 2 for u, v in zip(a["pr"], b["pr"]))
    d += 0.15 * sum((u - v) ** 2 for u, v in zip(a["cr"], b["cr"]))
    d += 0.15 * sum((u - v) ** 2 for u, v in zip(a["cc"], b["cc"]))
    d += 0.3 * (a["aspect"] - b["aspect"]) ** 2
    d += 0.05 * sum((u - v) ** 2 for u, v in zip(a["hu"], b["hu"]))
    return d


_PROTOS = None


def _prototypes():
    """Prototypes de traits : chaque glyphe de la police + variantes dilatée/érodée (variation d'épaisseur)."""
    global _PROTOS
    if _PROTOS is None:
        _PROTOS = []
        # on EXCLUT les glyphes triviaux (barre/point : ! . : - I 1) : trop permissifs, ils matchent le moindre
        # blob et produiraient des lettres fausses. La reconnaissance par traits sert les LETTRES/CHIFFRES riches.
        _TRIVIAUX = set("!.:-I1|")
        for ch, gab in _FONT.items():
            if ch == " " or ch in _TRIVIAUX:
                continue
            g = _canon_lignes(gab)
            for variante in (g, _dilate(g), _erode(g)):
                _PROTOS.append((ch, _features(variante)))
    return _PROTOS


def _reconnait_features(encre, x0, x1, y0, y1, seuil=0.38, marge=0.30):
    """Caractère du prototype de traits le plus proche, SOUS conditions STRICTES (FAUX=0) :
    (1) même nombre de TROUS que le prototype (filtre topologique fort) ; (2) distance faible ; (3) nettement
    séparé du 2e caractère. Sinon '?' — on préfère l'abstention à une lettre fausse."""
    f = _features(_canon_encre(encre, x0, x1, y0, y1))
    # ne compare qu'aux prototypes de MÊME topologie (même nombre de trous)
    cand = [(_dist_features(f, ft), ch) for ch, ft in _prototypes() if ft["trous"] == f["trous"]]
    if not cand:
        return "?"
    cand.sort()
    d1, c1 = cand[0]
    d2 = next((d for d, c in cand if c != c1), d1 + 1)
    return c1 if (d1 <= seuil and (d2 - d1) >= marge) else "?"


def ocr(source, *, seuil: int = 6, traits: bool = True):
    """Reconnaît le texte d'une image NETTE (objet raster_png.Image OU octets PNG). Renvoie le texte reconnu ;
    un glyphe non reconnu -> « ? » (jamais inventé). `traits`=True active le REPLI par caractéristiques
    (robuste aux polices voisines) quand le gabarit s'abstient. Lignes séparées par des sauts de ligne, espaces
    mots déduits des grands intervalles entre glyphes."""
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
            car = _reconnait(_norme_glyphe(encre, x0, x1, y0, y1), seuil)
            if car == "?" and traits:                # gabarit s'abstient -> repli par caractéristiques (police voisine)
                car = _reconnait_features(encre, x0, x1, y0, y1)
            out.append(car)
            prev_deb = x0
        lignes_txt.append("".join(out))
    return "\n".join(lignes_txt).strip()


def contient_texte(source, *, seuil: int = 6) -> bool:
    """True si l'image contient du texte reconnaissable (≥1 caractère non-« ? »)."""
    txt = ocr(source, seuil=seuil)
    return any(c not in " ?\n" for c in txt)
