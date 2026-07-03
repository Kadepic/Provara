"""
ROUTEUR DE FORMATS DE FICHIERS — « lire et comprendre tous les types de fichiers » (modalité, 2026-07-02).

POURQUOI (vision Yohan) : consulter/comprendre un fichier a un NOYAU BORNÉ et vérifiable — reconnaître son format
et le PARSER en une structure exploitable. La stdlib Python couvre une immense variété de formats TEXTE/structurés
(json/csv/xml/html/ini/sqlite/zip/tar/gzip/plist…). Ce module ROUTE un fichier vers le bon parseur (le « portfolio »
appliqué aux formats) et rend son contenu structuré. Les formats propriétaires/binaires lourds (docx/xlsx via libs,
PDF, images raster) exigent un outil dédié (installé par besoin) — ici, HORS honnête tant que non branché.

FAUX=0 :
  • Le type est déterminé par l'EXTENSION + le contenu (magic bytes) — jamais deviné. Type inconnu / binaire non
    structuré -> statut HORS (on ne fabrique pas un contenu), jamais une interprétation inventée.
  • Un parse qui échoue est rapporté comme ERREUR honnête (avec la raison), pas un contenu partiel silencieux.
  • Déterministe, lecture seule du disque, souverain, stdlib pur.
"""
from __future__ import annotations

import configparser
import csv
import gzip
import io
import json
import os
import sqlite3
import tarfile
import xml.etree.ElementTree as ET
import zipfile

VERIFIE = "verifie"       # le fichier a été parsé en une structure
HORS = "hors"             # format inconnu / binaire non structuré -> on ne devine pas
ERREUR = "erreur"         # format reconnu mais parse échoué (raison donnée)

# extension -> type logique. Source de vérité unique du routage.
_EXT = {
    ".json": "json", ".geojson": "json",
    ".csv": "csv", ".tsv": "tsv",
    ".xml": "xml", ".svg": "xml", ".rss": "xml", ".xsd": "xml",
    ".html": "html", ".htm": "html",
    ".ini": "ini", ".cfg": "ini", ".conf": "ini",
    ".sqlite": "sqlite", ".db": "sqlite", ".sqlite3": "sqlite",
    ".zip": "zip", ".tar": "tar", ".gz": "gzip",
    ".txt": "texte", ".md": "texte", ".log": "texte",
    ".pdf": "pdf",
    ".png": "image",
}


def detecte_type(chemin: str) -> str:
    """Type logique d'un fichier (par extension, corroboré par les magic bytes si possible). 'inconnu' au doute."""
    ext = os.path.splitext(chemin)[1].lower()
    t = _EXT.get(ext)
    # corroboration par magic bytes (sûre pour les conteneurs binaires) — jamais une SUPPOSITION positive au-delà.
    try:
        with open(chemin, "rb") as f:
            tete = f.read(16)
    except OSError:
        return t or "inconnu"
    if tete[:4] == b"PK\x03\x04":
        return "zip"
    if tete[:2] == b"\x1f\x8b":
        return "gzip"
    if tete[:16] == b"SQLite format 3\x00":
        return "sqlite"
    if tete[:5] == b"%PDF-":
        return "pdf"
    if tete[:8] == b"\x89PNG\r\n\x1a\n":
        return "image"
    return t or "inconnu"


def _texte(chemin):
    with open(chemin, encoding="utf-8") as f:
        return f.read()


def lit(chemin: str) -> dict:
    """Lit un fichier et renvoie {statut, type, contenu, meta}. statut ∈ {VERIFIE, HORS, ERREUR}.
    HORS = type non pris en charge (jamais deviné) ; ERREUR = parse échoué (raison) ; VERIFIE = contenu structuré."""
    if not os.path.isfile(chemin):
        return {"statut": ERREUR, "type": None, "contenu": None, "meta": "fichier introuvable"}
    t = detecte_type(chemin)
    try:
        if t == "json":
            return {"statut": VERIFIE, "type": t, "contenu": json.loads(_texte(chemin)), "meta": {}}
        if t in ("csv", "tsv"):
            delim = "\t" if t == "tsv" else ","
            with open(chemin, newline="", encoding="utf-8") as f:
                lignes = list(csv.reader(f, delimiter=delim))
            return {"statut": VERIFIE, "type": t, "contenu": lignes, "meta": {"lignes": len(lignes)}}
        if t in ("xml", "html"):
            racine = ET.fromstring(_texte(chemin))
            return {"statut": VERIFIE, "type": t, "contenu": racine,
                    "meta": {"racine": racine.tag, "enfants": len(racine)}}
        if t == "ini":
            cp = configparser.ConfigParser()
            cp.read(chemin, encoding="utf-8")
            return {"statut": VERIFIE, "type": t,
                    "contenu": {s: dict(cp[s]) for s in cp.sections()}, "meta": {"sections": cp.sections()}}
        if t == "sqlite":
            con = sqlite3.connect(chemin)
            try:
                tables = [r[0] for r in con.execute("SELECT name FROM sqlite_master WHERE type='table'")]
            finally:
                con.close()
            return {"statut": VERIFIE, "type": t, "contenu": {"tables": tables}, "meta": {"tables": len(tables)}}
        if t == "zip":
            with zipfile.ZipFile(chemin) as z:
                noms = z.namelist()
            return {"statut": VERIFIE, "type": t, "contenu": {"entrees": noms}, "meta": {"entrees": len(noms)}}
        if t == "tar":
            with tarfile.open(chemin) as tf:
                noms = tf.getnames()
            return {"statut": VERIFIE, "type": t, "contenu": {"entrees": noms}, "meta": {"entrees": len(noms)}}
        if t == "gzip":
            with gzip.open(chemin, "rb") as f:
                data = f.read()
            return {"statut": VERIFIE, "type": t, "contenu": data, "meta": {"octets": len(data)}}
        if t == "texte":
            txt = _texte(chemin)
            return {"statut": VERIFIE, "type": t, "contenu": txt,
                    "meta": {"lignes": txt.count("\n") + 1, "octets": len(txt.encode("utf-8"))}}
        if t == "pdf":
            import extrait_pdf                    # extraction de la couche TEXTE (Tj/TJ, FlateDecode) — FAUX=0
            with open(chemin, "rb") as f:
                octets = f.read()
            pages = extrait_pdf.pages(octets)
            avec = sum(1 for p in pages if p.strip())
            # honnêteté : un PDF SANS couche texte (scanné) rend des pages vides -> on le DIT (OCR = autre brique)
            meta = {"pages": len(pages), "pages_avec_texte": avec,
                    "caracteres": sum(len(p) for p in pages)}
            if avec == 0:
                meta["note"] = "aucune couche texte (PDF probablement scanné/image — OCR non disponible)"
            return {"statut": VERIFIE, "type": t, "contenu": {"pages": pages,
                    "texte": "\n\n".join(pages).strip()}, "meta": meta}
        if t == "image":
            import ocr                             # OCR BORNÉ : texte NET (police régulière) -> texte ; sinon HORS honnête
            with open(chemin, "rb") as f:
                octets = f.read()
            texte = ocr.ocr(octets)
            reconnu = any(c not in " ?\n" for c in texte)
            return {"statut": VERIFIE, "type": t,
                    "contenu": {"texte": texte if reconnu else ""},
                    "meta": {"texte_reconnu": reconnu,
                             "note": ("" if reconnu else
                                      "aucun texte net reconnu (photo/police non standard — OCR borné au texte "
                                      "régulier ; jamais deviné)")}}
    except Exception as ex:                      # format reconnu mais parse échoué -> ERREUR honnête (pas un faux)
        return {"statut": ERREUR, "type": t, "contenu": None, "meta": f"{type(ex).__name__}: {ex}"}
    # format non pris en charge -> HORS (on ne devine JAMAIS le contenu d'un binaire inconnu)
    return {"statut": HORS, "type": t, "contenu": None,
            "meta": "format non pris en charge (installer un outil dédié : PDF/docx/xlsx/image…)"}


def formats_supportes() -> list:
    """Les types logiques que ce module sait parser (pour se décrire honnêtement)."""
    return sorted(set(_EXT.values()))
