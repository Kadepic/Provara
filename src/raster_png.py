"""
RASTER PNG — noyau BORNÉ de la modalité IMAGE MATRICIELLE (pixels), pur stdlib (2026-07-02).

POURQUOI (vision Yohan « outil universel toutes modalités ») : la modalité image a deux faces. Le VECTORIEL
(geometrie2d/SVG) est déjà couvert ; il manquait le RASTER (grille de pixels) — le format réel des photos,
captures, sorties de tracé. Ce module écrit un PNG VALIDE et le RE-DÉCODE lui-même, sans dépendance (ni Pillow
ni zlib-C externe : `zlib` est stdlib). Le PNG est le format raster sans perte canonique (RFC 2083).

FAUX=0 — ce que ce module GARANTIT (borné, vérifiable), et ce qu'il ne prétend PAS :
  • L'encodage est EXACT et DÉTERMINISTE : `encode(img)` produit des octets qui, RE-DÉCODÉS par `decode`, rendent
    EXACTEMENT les mêmes pixels (round-trip identité prouvé par le validateur). Mêmes pixels -> mêmes octets.
  • Les CRC-32 de chaque chunk et la signature sont conformes à la spec ; `decode` REJETTE (ValueError) tout flux
    corrompu (signature fausse, CRC faux, chunk tronqué) au lieu de deviner -> pas de « lecture » d'un octet faux.
  • Les opérations de dessin (`pixel`, `remplit`, `rectangle`, `ligne`) sont des poses EXACTES de pixels (Bresenham
    entier pour la ligne) : aucune approximation cachée, coordonnées hors cadre -> ValueError (jamais silencieux).
  Ce module ne prétend PAS qu'une image est « jolie » ou « ressemblante » (non-borné, non jugé) : il garantit la
  VALIDITÉ structurelle du fichier + la fidélité pixel-parfaite de l'aller-retour. Souverain, offline, stdlib pur.

Modes : 'L' (niveaux de gris, 1 canal), 'RGB' (3), 'RGBA' (4), 8 bits/canal. Filtre PNG 0 (None) à l'écriture ;
le décodeur comprend les 5 filtres (0..4) pour re-lire n'importe quel PNG 8 bits non entrelacé.
"""
from __future__ import annotations

import struct
import zlib

_SIGNATURE = b"\x89PNG\r\n\x1a\n"

# mode -> (nb_canaux, color_type PNG)
_MODES = {"L": (1, 0), "RGB": (3, 2), "RGBA": (4, 6)}
_COLOR_TYPE_CANAUX = {0: 1, 2: 3, 6: 4}       # décodage : color_type -> canaux (modes supportés)


def _valide_composante(v) -> int:
    if isinstance(v, bool) or not isinstance(v, int):
        raise ValueError(f"composante de pixel non entière : {v!r}")
    if not (0 <= v <= 255):
        raise ValueError(f"composante hors [0,255] : {v}")
    return v


class Image:
    """Grille de pixels mutable, origine (0,0) en haut-gauche. Un pixel = un tuple d'entiers 0..255 de longueur
    `canaux` (1 pour 'L', 3 'RGB', 4 'RGBA'). FAUX=0 : dimensions ≥ 1, composantes bornées, accès dans le cadre."""

    __slots__ = ("largeur", "hauteur", "mode", "canaux", "_px")

    def __init__(self, largeur: int, hauteur: int, mode: str = "RGB", fond=None):
        if isinstance(largeur, bool) or isinstance(hauteur, bool) or not isinstance(largeur, int) or not isinstance(hauteur, int):
            raise ValueError("largeur/hauteur doivent être des entiers")
        if largeur < 1 or hauteur < 1:
            raise ValueError(f"dimensions doivent être ≥ 1 (vu {largeur}×{hauteur})")
        if mode not in _MODES:
            raise ValueError(f"mode inconnu {mode!r} (attendus : {sorted(_MODES)})")
        self.largeur = largeur
        self.hauteur = hauteur
        self.mode = mode
        self.canaux = _MODES[mode][0]
        if fond is None:
            fond = (0,) * self.canaux if self.canaux > 1 else (0,)
        fond = self._norme(fond)
        self._px = [list(fond) for _ in range(largeur * hauteur)]

    def _norme(self, pixel) -> tuple:
        """Valide+normalise un pixel vers un tuple de `canaux` entiers 0..255. Un scalaire est accepté en 'L'."""
        if isinstance(pixel, int) and not isinstance(pixel, bool):
            pixel = (pixel,)
        try:
            comp = tuple(pixel)
        except TypeError:
            raise ValueError(f"pixel non itérable : {pixel!r}")
        if len(comp) != self.canaux:
            raise ValueError(f"pixel de {len(comp)} canaux, attendu {self.canaux} (mode {self.mode})")
        return tuple(_valide_composante(c) for c in comp)

    def _index(self, x: int, y: int) -> int:
        if isinstance(x, bool) or isinstance(y, bool) or not isinstance(x, int) or not isinstance(y, int):
            raise ValueError("coordonnées entières attendues")
        if not (0 <= x < self.largeur and 0 <= y < self.hauteur):
            raise ValueError(f"pixel ({x},{y}) hors cadre {self.largeur}×{self.hauteur}")
        return y * self.largeur + x

    def pixel(self, x: int, y: int, couleur) -> None:
        """Pose un pixel exact. Hors cadre -> ValueError."""
        self._px[self._index(x, y)] = list(self._norme(couleur))

    def lit(self, x: int, y: int) -> tuple:
        return tuple(self._px[self._index(x, y)])

    def remplit(self, couleur) -> None:
        c = list(self._norme(couleur))
        for i in range(len(self._px)):
            self._px[i] = list(c)

    def rectangle(self, x0: int, y0: int, x1: int, y1: int, couleur, *, plein: bool = True) -> None:
        """Rectangle aligné, bornes incluses (x0≤x1, y0≤y1). `plein=False` -> contour d'un pixel."""
        if x0 > x1 or y0 > y1:
            raise ValueError("rectangle : bornes inversées (attendu x0≤x1, y0≤y1)")
        c = self._norme(couleur)
        for y in range(y0, y1 + 1):
            for x in range(x0, x1 + 1):
                if plein or x == x0 or x == x1 or y == y0 or y == y1:
                    self._px[self._index(x, y)] = list(c)

    def ligne(self, x0: int, y0: int, x1: int, y1: int, couleur) -> None:
        """Segment exact par tracé de Bresenham entier (pixels contigus, sans trou ni doublon)."""
        c = list(self._norme(couleur))
        # valide les extrémités d'abord (FAUX=0 : refuse hors cadre avant de tracer)
        self._index(x0, y0); self._index(x1, y1)
        dx = abs(x1 - x0)
        dy = -abs(y1 - y0)
        sx = 1 if x0 < x1 else -1
        sy = 1 if y0 < y1 else -1
        err = dx + dy
        x, y = x0, y0
        while True:
            self._px[y * self.largeur + x] = list(c)
            if x == x1 and y == y1:
                break
            e2 = 2 * err
            if e2 >= dy:
                err += dy
                x += sx
            if e2 <= dx:
                err += dx
                y += sy

    def _scanlines_brutes(self) -> bytes:
        """Octets des scanlines SANS filtre (chaque ligne préfixée du byte de filtre 0)."""
        larg_octets = self.largeur * self.canaux
        out = bytearray()
        for y in range(self.hauteur):
            out.append(0)                                    # filtre 0 = None
            base = y * self.largeur
            for x in range(self.largeur):
                out.extend(self._px[base + x])
        assert len(out) == self.hauteur * (1 + larg_octets)
        return bytes(out)


def _chunk(typ: bytes, data: bytes) -> bytes:
    """Un chunk PNG : longueur(4 BE) + type(4) + data + CRC32(type+data, 4 BE)."""
    corps = typ + data
    return struct.pack(">I", len(data)) + corps + struct.pack(">I", zlib.crc32(corps) & 0xFFFFFFFF)


def encode(img: Image, *, niveau: int = 6) -> bytes:
    """Sérialise une `Image` en octets PNG valides et DÉTERMINISTES. Mêmes pixels -> mêmes octets (à niveau fixé)."""
    if not isinstance(img, Image):
        raise ValueError("encode attend une Image")
    _, color_type = _MODES[img.mode]
    ihdr = struct.pack(">IIBBBBB", img.largeur, img.hauteur, 8, color_type, 0, 0, 0)
    idat = zlib.compress(img._scanlines_brutes(), niveau)
    return _SIGNATURE + _chunk(b"IHDR", ihdr) + _chunk(b"IDAT", idat) + _chunk(b"IEND", b"")


def ecris(img: Image, chemin: str, *, niveau: int = 6) -> int:
    """Écrit le PNG sur disque (atomique : tmp + os.replace). Renvoie le nombre d'octets écrits."""
    import os
    octets = encode(img, niveau=niveau)
    tmp = f"{chemin}.tmp.{os.getpid()}"
    with open(tmp, "wb") as f:
        f.write(octets)
    os.replace(tmp, chemin)
    return len(octets)


def _defiltre(scan: bytes, hauteur: int, larg_octets: int, bpp: int) -> list[list[int]]:
    """Inverse les filtres PNG (0..4) ligne par ligne. Renvoie `hauteur` lignes de `larg_octets` entiers."""
    lignes = []
    precedente = [0] * larg_octets
    pos = 0
    for _ in range(hauteur):
        if pos >= len(scan):
            raise ValueError("scanlines tronquées")
        filtre = scan[pos]; pos += 1
        brute = list(scan[pos:pos + larg_octets]); pos += larg_octets
        if len(brute) != larg_octets:
            raise ValueError("scanline incomplète")
        cur = [0] * larg_octets
        for i in range(larg_octets):
            a = cur[i - bpp] if i >= bpp else 0                       # gauche (Recon a)
            b = precedente[i]                                          # haut (Recon b)
            c = precedente[i - bpp] if i >= bpp else 0                # haut-gauche (Recon c)
            x = brute[i]
            if filtre == 0:
                val = x
            elif filtre == 1:
                val = x + a
            elif filtre == 2:
                val = x + b
            elif filtre == 3:
                val = x + (a + b) // 2
            elif filtre == 4:
                p = a + b - c
                pa, pb, pc = abs(p - a), abs(p - b), abs(p - c)
                pr = a if (pa <= pb and pa <= pc) else (b if pb <= pc else c)
                val = x + pr
            else:
                raise ValueError(f"filtre PNG inconnu : {filtre}")
            cur[i] = val & 0xFF
        lignes.append(cur)
        precedente = cur
    return lignes


def decode(octets: bytes) -> Image:
    """RE-LIT un PNG (8 bits, non entrelacé, modes L/RGB/RGBA) en `Image`. FAUX=0 : signature/CRC/structure vérifiés,
    tout défaut -> ValueError (jamais de pixel deviné). Sert d'oracle indépendant pour prouver le round-trip."""
    if not isinstance(octets, (bytes, bytearray)):
        raise ValueError("decode attend des octets")
    octets = bytes(octets)
    if octets[:8] != _SIGNATURE:
        raise ValueError("signature PNG invalide")
    pos = 8
    largeur = hauteur = color_type = None
    idat = bytearray()
    fin = False
    while pos < len(octets):
        if pos + 8 > len(octets):
            raise ValueError("en-tête de chunk tronqué")
        (longueur,) = struct.unpack(">I", octets[pos:pos + 4])
        typ = octets[pos + 4:pos + 8]
        data = octets[pos + 8:pos + 8 + longueur]
        if len(data) != longueur:
            raise ValueError("données de chunk tronquées")
        (crc_attendu,) = struct.unpack(">I", octets[pos + 8 + longueur:pos + 12 + longueur])
        if zlib.crc32(typ + data) & 0xFFFFFFFF != crc_attendu:
            raise ValueError(f"CRC invalide pour chunk {typ!r}")
        pos += 12 + longueur
        if typ == b"IHDR":
            largeur, hauteur, prof, color_type, comp, filtre, entrelace = struct.unpack(">IIBBBBB", data)
            if prof != 8:
                raise ValueError(f"profondeur {prof} non supportée (8 attendu)")
            if color_type not in _COLOR_TYPE_CANAUX:
                raise ValueError(f"color_type {color_type} non supporté")
            if comp != 0 or filtre != 0 or entrelace != 0:
                raise ValueError("compression/filtre/entrelacement non standard")
        elif typ == b"IDAT":
            idat.extend(data)
        elif typ == b"IEND":
            fin = True
            break
    if largeur is None:
        raise ValueError("IHDR manquant")
    if not fin:
        raise ValueError("IEND manquant")
    canaux = _COLOR_TYPE_CANAUX[color_type]
    mode = {1: "L", 3: "RGB", 4: "RGBA"}[canaux]
    scan = zlib.decompress(bytes(idat))
    larg_octets = largeur * canaux
    lignes = _defiltre(scan, hauteur, larg_octets, canaux)
    img = Image(largeur, hauteur, mode)
    for y in range(hauteur):
        ligne = lignes[y]
        base = y * largeur
        for x in range(largeur):
            img._px[base + x] = ligne[x * canaux:(x + 1) * canaux]
    return img
