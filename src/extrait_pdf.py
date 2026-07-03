# -*- coding: utf-8 -*-
"""EXTRACTION DE TEXTE PDF — lecture d'un PDF TIERS, pur stdlib (2026-07-03).

POURQUOI (mandat Yohan « l'IA doit lire et comprendre un mémoire de 200 pages ») : `parseur_fichiers` savait lire
json/csv/xml/txt mais rendait HORS pour le PDF ; `document_pdf` sait ÉCRIRE un PDF, pas lire un PDF arbitraire.
Ce module EXTRAIT le texte réellement présent dans un PDF (opérateurs de texte Tj/TJ), flux compressés FlateDecode
(zlib) compris. Il rend le texte PAR PAGE, dans l'ordre du document.

FAUX=0 — ce que ce module GARANTIT et ce qu'il ne prétend PAS :
  • Il ne rend QUE le texte littéralement encodé dans les opérateurs de texte du PDF (chaînes des Tj/TJ,
    échappements PDF décodés) — jamais une invention, jamais une reconstruction « probable ».
  • Un PDF SANS couche texte (page scannée = image) rend une page VIDE : c'est HONNÊTE (l'OCR est une autre
    brique, non encore là). L'appelant sait distinguer « pas de texte » de « texte extrait ».
  • Filtres gérés : aucun (flux clair) et FlateDecode (zlib). Un filtre non géré (LZW, DCT/image…) -> ce flux
    est ignoré (pas de texte inventé). Aucune dépendance externe (stdlib re + zlib).
"""
from __future__ import annotations

import re
import zlib

# Un objet indirect : « N G obj … endobj ». On indexe par numéro (offset du dernier « N 0 obj » gagne, comme xref).
_OBJ_RE = re.compile(rb"(\d+)\s+\d+\s+obj\b")
# Opérateurs de texte : (chaine) Tj  |  [ ... ] TJ  |  déplacements de ligne Td/TD/T*  |  fin de bloc ET.
_STR_RE = re.compile(rb"\((?:\\.|[^\\()]|\((?:\\.|[^\\()])*\))*\)", re.S)


def _decode_chaine_pdf(brut: bytes) -> str:
    """Décode une chaîne littérale PDF « ( ... ) » (sans les parenthèses externes) : échappements \\n \\t \\( \\)
    \\\\ et octal \\ddd. Encodage PDFDocEncoding ≈ latin-1 pour les polices standard (Helvetica...)."""
    out = bytearray()
    i, n = 0, len(brut)
    while i < n:
        c = brut[i]
        if c == 0x5C and i + 1 < n:                         # backslash
            d = brut[i + 1]
            simple = {0x6E: 0x0A, 0x72: 0x0D, 0x74: 0x09, 0x62: 0x08, 0x66: 0x0C,
                      0x28: 0x28, 0x29: 0x29, 0x5C: 0x5C}
            if d in simple:
                out.append(simple[d]); i += 2; continue
            if 0x30 <= d <= 0x37:                           # octal \ddd (1 à 3 chiffres)
                j = i + 1; val = 0; k = 0
                while j < n and k < 3 and 0x30 <= brut[j] <= 0x37:
                    val = val * 8 + (brut[j] - 0x30); j += 1; k += 1
                out.append(val & 0xFF); i = j; continue
            if d == 0x0A:                                   # backslash + saut = continuation (rien)
                i += 2; continue
            out.append(d); i += 2; continue
        out.append(c); i += 1
    return out.decode("latin-1", "replace")


def _texte_du_contenu(flux: bytes) -> str:
    """Extrait le texte d'un flux de contenu de page (déjà décompressé). On lit les chaînes des Tj/TJ dans
    l'ordre ; un déplacement de ligne (Td/TD/T*/apostrophe) insère un saut de ligne. Positionnement ignoré."""
    lignes: list[list[str]] = [[]]
    i, n = 0, len(flux)
    while i < n:
        c = flux[i]
        if c == 0x28:                                       # début d'une chaîne littérale « ( »
            m = _STR_RE.match(flux, i)
            if m:
                lignes[-1].append(_decode_chaine_pdf(m.group(0)[1:-1]))
                i = m.end(); continue
            i += 1; continue
        # opérateurs de nouvelle ligne : Td, TD, T*, ' (apostrophe), " (guillemet)
        if c in (0x54, 0x27, 0x22):                         # T.. / ' / "
            if c == 0x54 and i + 1 < n and flux[i + 1] in (0x64, 0x44, 0x2A):   # Td TD T*
                lignes.append([]); i += 2; continue
            if c in (0x27, 0x22):
                lignes.append([]); i += 1; continue
        i += 1
    return "\n".join(" ".join(seg for seg in ln if seg) for ln in lignes).strip()


def _objets(octets: bytes) -> dict:
    """Indexe {num_objet: (dict_brut, flux_brut|None)} par balayage « N 0 obj … endobj »."""
    objets = {}
    for m in _OBJ_RE.finditer(octets):
        num = int(m.group(1))
        fin = octets.find(b"endobj", m.end())
        corps = octets[m.end():fin if fin >= 0 else len(octets)]
        s = corps.find(b"stream")
        flux = None
        entete = corps
        if s >= 0:
            entete = corps[:s]
            deb = s + len(b"stream")
            if deb < len(corps) and corps[deb] == 0x0D:     # CRLF ou LF après « stream »
                deb += 1
            if deb < len(corps) and corps[deb] == 0x0A:
                deb += 1
            e = corps.find(b"endstream", deb)
            flux = corps[deb:e if e >= 0 else len(corps)]
            if flux.endswith(b"\n"):
                flux = flux[:-1]
            if flux.endswith(b"\r"):
                flux = flux[:-1]
        objets[num] = (entete, flux)
    return objets


def _decompresse(entete: bytes, flux: bytes) -> bytes | None:
    """Rend le flux clair : FlateDecode -> zlib ; aucun filtre -> tel quel ; filtre non géré -> None (jamais
    d'invention)."""
    if flux is None:
        return None
    if b"/FlateDecode" in entete:
        try:
            return zlib.decompress(flux)
        except zlib.error:
            try:
                return zlib.decompressobj().decompress(flux)   # flux légèrement tronqué : ce qu'on peut
            except zlib.error:
                return None
    if b"/Filter" in entete:                                # filtre présent mais non FlateDecode -> non géré
        return None
    return flux


_REF_RE = re.compile(rb"(\d+)\s+\d+\s+R")


def _pages_ordonnees(objets: dict) -> list:
    """Ordre des pages via l'arbre Catalog->Pages->Kids. Repli : tous les objets /Type /Page dans l'ordre
    numérique. Renvoie la liste des numéros d'objets Page."""
    # racine des pages : un objet « /Type /Pages » avec /Kids
    def kids_de(num, vus):
        if num in vus:
            return []
        vus.add(num)
        entete = objets.get(num, (b"", None))[0]
        out = []
        if b"/Type" in entete and b"/Page" in entete and b"/Kids" not in entete:
            return [num]
        mk = re.search(rb"/Kids\s*\[(.*?)\]", entete, re.S)
        if mk:
            for r in _REF_RE.finditer(mk.group(1)):
                out.extend(kids_de(int(r.group(1)), vus))
        return out
    racines = [num for num, (e, _) in objets.items()
               if b"/Type" in e and b"/Pages" in e and b"/Kids" in e and b"/Parent" not in e]
    ordre = []
    for r in racines:
        ordre.extend(kids_de(r, set()))
    if ordre:
        return ordre
    return sorted(num for num, (e, _) in objets.items()
                  if b"/Type" in e and b"/Page" in e and b"/Kids" not in e)


def pages(octets: bytes) -> list:
    """Texte du PDF, PAGE PAR PAGE : renvoie une liste de str (une par page, '' si la page n'a pas de couche
    texte). FAUX=0 : uniquement le texte réellement encodé. Lève ValueError si ce ne sont pas des octets PDF."""
    if not isinstance(octets, (bytes, bytearray)):
        raise ValueError("octets attendus")
    octets = bytes(octets)
    if not octets.startswith(b"%PDF-"):
        raise ValueError("en-tête PDF absent")
    objets = _objets(octets)
    res = []
    for pnum in _pages_ordonnees(objets):
        entete = objets.get(pnum, (b"", None))[0]
        refs = []
        mc = re.search(rb"/Contents\s*(\[[^\]]*\]|\d+\s+\d+\s+R)", entete)
        if mc:
            refs = [int(r.group(1)) for r in _REF_RE.finditer(mc.group(1))]
        txt = []
        for cref in refs:
            clair = _decompresse(*objets.get(cref, (b"", None)))
            if clair:
                txt.append(_texte_du_contenu(clair))
        res.append("\n".join(t for t in txt if t).strip())
    return res


def texte(octets: bytes, separateur_page: str = "\n\n") -> str:
    """Tout le texte du PDF, pages jointes. Pratique pour la recherche plein-texte / le résumé."""
    return separateur_page.join(pages(octets)).strip()


def infos(octets: bytes) -> dict:
    """Métadonnées utiles à l'appelant : nb de pages, nb de pages AVEC texte, longueur totale (diagnostic
    « scanné sans couche texte » = pages > 0 mais avec_texte == 0 -> l'OCR serait requis)."""
    ps = pages(octets)
    avec = sum(1 for p in ps if p.strip())
    return {"pages": len(ps), "pages_avec_texte": avec, "caracteres": sum(len(p) for p in ps)}
