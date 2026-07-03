"""
TABLEUR XLSX — noyau BORNÉ de la modalité FEUILLE DE CALCUL (Excel/OOXML), pur stdlib (2026-07-02).

POURQUOI (vision Yohan « outil universel toutes modalités » + contexte SaaS où l'échange Excel est réel) : un .xlsx
est un ZIP de fichiers XML (OOXML, ECMA-376). `zipfile` + XML de la stdlib suffisent — aucune dépendance (ni openpyxl
ni pandas). On écrit un classeur VALIDE et on le RE-LIT nous-mêmes (oracle indépendant) pour garantir le round-trip.

FAUX=0 — ce que ce module GARANTIT, et ce qu'il ne prétend PAS :
  • Round-trip EXACT des valeurs de cellules (texte et nombres) : `encode(classeur)` puis `decode(...)` rend les
    MÊMES valeurs (prouvé par le validateur). Les nombres restent des nombres, le texte du texte (typage préservé).
  • Références de cellules A1 calculées EXACTEMENT (colonne 0 -> "A", 26 -> "AA", …) ; le validateur re-dérive.
  • XML correctement échappé (&, <, >, ", ') ; une valeur non-scalaire -> ValueError (jamais de sérialisation muette).
  Ce module ne prétend PAS gérer TOUT OOXML (styles, formules, dates, graphiques) : il garantit un sous-ensemble
  EXACT et vérifiable (texte + nombres + plusieurs feuilles). Souverain, offline, stdlib pur, déterministe.
"""
from __future__ import annotations

import io
import re
import xml.etree.ElementTree as ET
import zipfile

_NS_MAIN = "http://schemas.openxmlformats.org/spreadsheetml/2006/main"


def colonne_vers_lettre(i: int) -> str:
    """Index de colonne 0 -> 'A', 25 -> 'Z', 26 -> 'AA' (base-26 bijective). FAUX=0 : i ≥ 0 entier."""
    if isinstance(i, bool) or not isinstance(i, int) or i < 0:
        raise ValueError("index de colonne : entier ≥ 0 attendu")
    s = ""
    i += 1
    while i > 0:
        i, r = divmod(i - 1, 26)
        s = chr(ord("A") + r) + s
    return s


def lettre_vers_colonne(s: str) -> int:
    """'A' -> 0, 'AA' -> 26. Inverse exact de colonne_vers_lettre."""
    if not isinstance(s, str) or not s or not s.isalpha() or not s.isupper():
        raise ValueError(f"lettre de colonne invalide : {s!r}")
    n = 0
    for ch in s:
        n = n * 26 + (ord(ch) - ord("A") + 1)
    return n - 1


def _ref(col: int, ligne: int) -> str:
    return f"{colonne_vers_lettre(col)}{ligne + 1}"


class Feuille:
    """Grille de cellules d'une feuille. Cellule = str, int, float, ou None (vide). Nommée."""

    def __init__(self, nom: str):
        if not isinstance(nom, str) or not nom.strip():
            raise ValueError("nom de feuille non vide requis")
        # Excel interdit ces caractères dans un nom d'onglet + limite 31 caractères.
        if len(nom) > 31 or any(c in nom for c in r"[]:*?/\\"):
            raise ValueError(f"nom de feuille invalide : {nom!r}")
        self.nom = nom
        self._cellules: dict[tuple[int, int], object] = {}

    def set(self, ligne: int, col: int, valeur) -> None:
        if isinstance(ligne, bool) or isinstance(col, bool) or not isinstance(ligne, int) or not isinstance(col, int):
            raise ValueError("ligne/col entiers attendus")
        if ligne < 0 or col < 0:
            raise ValueError("ligne/col doivent être ≥ 0")
        if valeur is None:
            self._cellules.pop((ligne, col), None)
            return
        if isinstance(valeur, bool) or not isinstance(valeur, (str, int, float)):
            raise ValueError(f"valeur de cellule non supportée : {valeur!r} (str/int/float)")
        if isinstance(valeur, float) and (valeur != valeur or valeur in (float("inf"), float("-inf"))):
            raise ValueError("valeur numérique non finie")
        self._cellules[(ligne, col)] = valeur

    def get(self, ligne: int, col: int):
        return self._cellules.get((ligne, col))

    def ligne_depuis(self, ligne: int, valeurs) -> None:
        """Remplit une ligne à partir de la colonne 0."""
        for c, v in enumerate(valeurs):
            self.set(ligne, c, v)

    def _dims(self):
        if not self._cellules:
            return 0, 0
        return (max(l for l, _ in self._cellules) + 1, max(c for _, c in self._cellules) + 1)

    def _xml(self) -> str:
        lignes_xml = []
        cells = {}
        for (l, c), v in self._cellules.items():
            cells.setdefault(l, {})[c] = v
        for l in sorted(cells):
            cellules_xml = []
            for c in sorted(cells[l]):
                v = cells[l][c]
                r = _ref(c, l)
                if isinstance(v, str):
                    txt = _echappe(v)
                    cellules_xml.append(f'<c r="{r}" t="inlineStr"><is><t xml:space="preserve">{txt}</t></is></c>')
                else:
                    cellules_xml.append(f'<c r="{r}"><v>{_num(v)}</v></c>')
            lignes_xml.append(f'<row r="{l + 1}">{"".join(cellules_xml)}</row>')
        return (
            '<?xml version="1.0" encoding="UTF-8" standalone="yes"?>'
            f'<worksheet xmlns="{_NS_MAIN}"><sheetData>{"".join(lignes_xml)}</sheetData></worksheet>'
        )


class Classeur:
    """Un classeur = une ou plusieurs feuilles ordonnées."""

    def __init__(self):
        self.feuilles: list[Feuille] = []

    def feuille(self, nom: str) -> Feuille:
        if any(f.nom == nom for f in self.feuilles):
            raise ValueError(f"feuille déjà présente : {nom!r}")
        f = Feuille(nom)
        self.feuilles.append(f)
        return f


def _echappe(s: str) -> str:
    return (s.replace("&", "&amp;").replace("<", "&lt;").replace(">", "&gt;")
             .replace('"', "&quot;").replace("'", "&apos;"))


def _num(v) -> str:
    if isinstance(v, int):
        return str(v)
    # float : repr Python round-trip, mais entier-valué -> forme entière (12.0 -> "12")
    if v == int(v):
        return str(int(v))
    return repr(v)


def encode(classeur: Classeur) -> bytes:
    """Sérialise un `Classeur` en octets .xlsx (ZIP OOXML) valides et déterministes."""
    if not isinstance(classeur, Classeur) or not classeur.feuilles:
        raise ValueError("classeur non vide requis")
    n = len(classeur.feuilles)

    content_types = (
        '<?xml version="1.0" encoding="UTF-8" standalone="yes"?>'
        '<Types xmlns="http://schemas.openxmlformats.org/package/2006/content-types">'
        '<Default Extension="rels" ContentType="application/vnd.openxmlformats-package.relationships+xml"/>'
        '<Default Extension="xml" ContentType="application/xml"/>'
        '<Override PartName="/xl/workbook.xml" ContentType="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet.main+xml"/>'
        + "".join(
            f'<Override PartName="/xl/worksheets/sheet{i+1}.xml" '
            f'ContentType="application/vnd.openxmlformats-officedocument.spreadsheetml.worksheet+xml"/>'
            for i in range(n))
        + "</Types>"
    )
    rels = (
        '<?xml version="1.0" encoding="UTF-8" standalone="yes"?>'
        '<Relationships xmlns="http://schemas.openxmlformats.org/package/2006/relationships">'
        '<Relationship Id="rId1" Type="http://schemas.openxmlformats.org/officeDocument/2006/relationships/officeDocument" Target="xl/workbook.xml"/>'
        "</Relationships>"
    )
    sheets_xml = "".join(
        f'<sheet name="{_echappe(f.nom)}" sheetId="{i+1}" r:id="rId{i+1}"/>'
        for i, f in enumerate(classeur.feuilles))
    workbook = (
        '<?xml version="1.0" encoding="UTF-8" standalone="yes"?>'
        f'<workbook xmlns="{_NS_MAIN}" '
        'xmlns:r="http://schemas.openxmlformats.org/officeDocument/2006/relationships">'
        f'<sheets>{sheets_xml}</sheets></workbook>'
    )
    wb_rels = (
        '<?xml version="1.0" encoding="UTF-8" standalone="yes"?>'
        '<Relationships xmlns="http://schemas.openxmlformats.org/package/2006/relationships">'
        + "".join(
            f'<Relationship Id="rId{i+1}" '
            f'Type="http://schemas.openxmlformats.org/officeDocument/2006/relationships/worksheet" '
            f'Target="worksheets/sheet{i+1}.xml"/>' for i in range(n))
        + "</Relationships>"
    )

    buf = io.BytesIO()
    with zipfile.ZipFile(buf, "w", zipfile.ZIP_DEFLATED) as z:
        z.writestr("[Content_Types].xml", content_types)
        z.writestr("_rels/.rels", rels)
        z.writestr("xl/workbook.xml", workbook)
        z.writestr("xl/_rels/workbook.xml.rels", wb_rels)
        for i, f in enumerate(classeur.feuilles):
            z.writestr(f"xl/worksheets/sheet{i+1}.xml", f._xml())
    return buf.getvalue()


def ecris(classeur: Classeur, chemin: str) -> int:
    import os
    data = encode(classeur)
    tmp = f"{chemin}.tmp.{os.getpid()}"
    with open(tmp, "wb") as fp:
        fp.write(data)
    os.replace(tmp, chemin)
    return len(data)


_RX_REF = re.compile(r"^([A-Z]+)(\d+)$")


def decode(octets: bytes) -> dict:
    """RE-LIT un .xlsx (produit ici) -> {noms: [...], feuilles: {nom: {(ligne,col): valeur}}}. Oracle indépendant :
    unzip + parse XML. FAUX=0 : ZIP/XML invalide -> ValueError. Typage préservé (str vs nombre)."""
    if not isinstance(octets, (bytes, bytearray)):
        raise ValueError("decode attend des octets")
    try:
        z = zipfile.ZipFile(io.BytesIO(bytes(octets)), "r")
    except zipfile.BadZipFile as e:
        raise ValueError(f"xlsx (zip) invalide : {e}")
    try:
        wb = ET.fromstring(z.read("xl/workbook.xml"))
    except (KeyError, ET.ParseError) as e:
        raise ValueError(f"workbook.xml absent/invalide : {e}")
    noms = [s.get("name") for s in wb.iter(f"{{{_NS_MAIN}}}sheet")]
    feuilles = {}
    for i, nom in enumerate(noms):
        try:
            ws = ET.fromstring(z.read(f"xl/worksheets/sheet{i+1}.xml"))
        except (KeyError, ET.ParseError) as e:
            raise ValueError(f"sheet{i+1}.xml absent/invalide : {e}")
        grille = {}
        for c in ws.iter(f"{{{_NS_MAIN}}}c"):
            r = c.get("r")
            m = _RX_REF.match(r or "")
            if not m:
                raise ValueError(f"référence de cellule invalide : {r!r}")
            col = lettre_vers_colonne(m.group(1))
            ligne = int(m.group(2)) - 1
            typ = c.get("t")
            if typ == "inlineStr":
                t = c.find(f"{{{_NS_MAIN}}}is/{{{_NS_MAIN}}}t")
                grille[(ligne, col)] = t.text if t is not None and t.text is not None else ""
            else:
                v = c.find(f"{{{_NS_MAIN}}}v")
                if v is None or v.text is None:
                    continue
                txt = v.text
                grille[(ligne, col)] = int(txt) if re.fullmatch(r"-?\d+", txt) else float(txt)
        feuilles[nom] = grille
    return {"noms": noms, "feuilles": feuilles}
