"""
INGESTION BLS OES — l'axe « rémunération médiane (pays et année donnés) » s'ouvre par sa part ÉTATS-UNIS
(mandat « traiter tout le backlog », piste §4 du runbook sondée le 2026-07-12).

POURQUOI BLS ET PAS EUROSTAT. `earn_ses18_25` (écarté au runbook) est une MOYENNE par grand groupe ISCO à
1 chiffre : le publier comme « rémunération médiane du boulanger » serait un DOUBLE faux. L'OEWS du Bureau
of Labor Statistics publie la vraie MÉDIANE, par occupation SOC détaillée (831 occupations, mai 2024).

LA CHAÎNE, ET CE QUE CHAQUE MAILLON AFFIRME (aucun maillon n'est de nous) :
  1. métier -> groupe ISCO-08          — `code_isco_metier` du store (ESCO, gardes d'alignement amont) ;
  2. groupe ISCO-08 -> SOC 2010        — crosswalk OFFICIEL BLS (août 2012, maj juin 2015 — STATIQUE) ;
  3. SOC 2010 -> SOC 2018              — crosswalk OFFICIEL BLS/SOCPC ;
  4. SOC 2018 -> médiane annuelle US   — BLS OEWS mai 2024, champ A_MEDIAN, lignes O_GROUP=detailed.
PERSONNE n'affirme « la médiane du métier M est X » : la médiane est PAR OCCUPATION SOC, et un groupe ISCO
couvre plusieurs SOC (« actuaire » -> groupe 2120 -> Actuaries 125 770 $, mais aussi Mathematicians,
Statisticians…). La valeur liste donc TOUTES les occupations SOC du groupe avec leur médiane, granularité
dite — le nom de la table porte « soc » pour la même raison (leçon Eurostat : nommer honnêtement).

UNE RELATION : `salaire_median_soc_us_metier` — MIX -> PARTIEL, jamais TRAITÉ : seule la part
ÉTATS-UNIS (une année, un pays) est fermée. La rémunération française par métier reste NON couverte
(pistes au runbook : DARES×FAP via le pont ROME, granularité à vérifier).

FAUX=0 :
  • A_MEDIAN « # » signifie « ≥ 239 200 $/an » (plafond de publication BLS) : c'est un FAIT, encodé comme
    tel — jamais jeté, jamais converti en nombre. « * » signifie « non publié » : l'occupation est écartée
    et COMPTÉE. Une occupation sans salaire publié n'a pas de salaire inventé.
  • Liste EXHAUSTIVE des SOC du groupe (jamais un extrait) ; un métier dont AUCUNE occupation n'a de
    médiane publiée (ex. militaires, hors champ OEWS) reste NON TRAITÉ.
  • Gardes de volume à chaque maillon : un référentiel tronqué ne publie rien.

CACHE (`datasets/_raw/`) : `isco08_to_soc2010.csv` + `soc_2010_to_2018_crosswalk.xlsx` + `oesm24nat.zip`.
Le crosswalk ISCO↔SOC n'existe qu'en .xls binaire (BIFF) chez BLS : il a été converti UNE FOIS en CSV
(xlrd 1.2.0, 2026-07-12) — le fichier source est STATIQUE depuis 2015, la conversion n'est pas à rejouer ;
le .xls d'origine est conservé à côté pour la traçabilité. Écrire un parseur BIFF maison risquerait un
faux de parse silencieux : pire que la dépendance ponctuelle. `moissonne()` retélécharge les trois
fichiers ; si le CSV manque ET que xlrd est absent, il LÈVE en expliquant — jamais de conversion devinée.
Les .xlsx se lisent en stdlib pur (zip + XML), comme tout le reste du projet.

Usage :
    python3 ingestion/ingere_bls_oes.py moissonne     # 3 fichiers BLS (~0,7 Mo)
    python3 ingestion/ingere_bls_oes.py publie        # hors ligne, depuis le cache
"""
from __future__ import annotations

import collections
import csv
import json
import os
import re
import sys
import time
import urllib.request
import zipfile
from xml.etree import ElementTree as ET

from ingere_wikidata import RAW, publie

UA = "Mozilla/5.0 (compatible; Provara/1.0; offline-knowledge-ingestion; contact yohan.fauck@gmail.com)"
URL_XWALK_XLS = "https://www.bls.gov/soc/ISCO_SOC_Crosswalk.xls"
URL_SOC_10_18 = "https://www.bls.gov/soc/2018/soc_2010_to_2018_crosswalk.xlsx"
URL_OES = "https://www.bls.gov/oes/special-requests/oesm24nat.zip"
CACHE_XWALK_XLS = os.path.join(RAW, "ISCO_SOC_Crosswalk.xls")
CACHE_XWALK_CSV = os.path.join(RAW, "isco08_to_soc2010.csv")
CACHE_SOC_10_18 = os.path.join(RAW, "soc_2010_to_2018_crosswalk.xlsx")
CACHE_OES = os.path.join(RAW, "oesm24nat.zip")
MILLESIME_OES = "mai 2024"
PLAFOND = "≥ 239 200 $/an (plafond de publication BLS)"

SRC = ("BLS OEWS %s (médiane salariale annuelle par occupation SOC 2018, États-Unis) × crosswalks OFFICIELS "
       "BLS (ISCO-08→SOC 2010, 2012/2015 ; SOC 2010→2018, SOCPC) × `code_isco_metier` (ESCO). La valeur "
       "affirme : le métier relève du groupe ISCO-08 indiqué (ESCO) ; les occupations SOC listées sont "
       "celles que les crosswalks BLS associent à ce GROUPE (pas au métier précis — granularité dite) ; "
       "chaque médiane est celle de SON occupation SOC. « # » d'OEWS = %s, un fait, jamais un nombre "
       "inventé ; les occupations sans médiane publiée (« * ») sont écartées et comptées. Part ÉTATS-UNIS "
       "seulement." % (MILLESIME_OES, PLAFOND))


# ============================================================================================
#  LECTURE XLSX 100 %% STDLIB (zip + XML) — même esprit que tout le projet
# ============================================================================================
_NS = {"m": "http://schemas.openxmlformats.org/spreadsheetml/2006/main"}


def lit_xlsx(chemin: str, feuille: int = 1) -> list:
    """Lignes d'une feuille xlsx, chacune {lettre_colonne: valeur str}. Chaînes partagées résolues."""
    with zipfile.ZipFile(chemin) as z:
        partagees = []
        if "xl/sharedStrings.xml" in z.namelist():
            for si in ET.fromstring(z.read("xl/sharedStrings.xml")).findall("m:si", _NS):
                partagees.append("".join(t.text or "" for t in si.iter("{%s}t" % _NS["m"])))
        lignes = []
        for row in ET.fromstring(z.read("xl/worksheets/sheet%d.xml" % feuille)).find("m:sheetData", _NS):
            vals = {}
            for c in row:
                col = re.match(r"[A-Z]+", c.get("r")).group(0)
                v = c.find("m:v", _NS)
                if v is not None:
                    vals[col] = partagees[int(v.text)] if c.get("t") == "s" else v.text
                else:                               # chaîne inline (t="inlineStr", <is><t>…) : partie du format
                    est_inline = c.find("m:is", _NS)
                    vals[col] = ("".join(t.text or "" for t in est_inline.iter("{%s}t" % _NS["m"]))
                                 if est_inline is not None else "")
            lignes.append(vals)
        return lignes


# ============================================================================================
#  MOISSONNAGE (le réseau ne vit qu'ici)
# ============================================================================================
def _telecharge(url: str, chemin: str, essais: int = 5, timeout: int = 300) -> None:
    for k in range(essais):
        try:
            req = urllib.request.Request(url, headers={"User-Agent": UA})
            with urllib.request.urlopen(req, timeout=timeout) as r:
                brut = r.read()
            tmp = chemin + ".tmp"
            with open(tmp, "wb") as fh:
                fh.write(brut)
            os.replace(tmp, chemin)
            return
        except OSError:
            if k == essais - 1:
                raise
            time.sleep(4 * (k + 1))


def moissonne() -> None:
    os.makedirs(RAW, exist_ok=True)
    print("== MOISSONNAGE BLS (crosswalks + OEWS) ==")
    for url, chemin in ((URL_XWALK_XLS, CACHE_XWALK_XLS), (URL_SOC_10_18, CACHE_SOC_10_18),
                        (URL_OES, CACHE_OES)):
        _telecharge(url, chemin)
        print("  %s (%.0f Ko)" % (os.path.basename(chemin), os.path.getsize(chemin) / 1e3))
    if not os.path.exists(CACHE_XWALK_CSV):
        try:
            import xlrd                                             # dev-only, conversion du .xls STATIQUE
        except ImportError:
            raise SystemExit("le crosswalk ISCO↔SOC n'existe qu'en .xls (BIFF) : convertir UNE FOIS avec "
                             "xlrd==1.2.0 (pip install --user xlrd==1.2.0) puis relancer — on ne devine "
                             "jamais une conversion")
        wb = xlrd.open_workbook(CACHE_XWALK_XLS)
        sh = wb.sheet_by_name("ISCO-08 to 2010 SOC")
        with open(CACHE_XWALK_CSV, "w", newline="", encoding="utf-8") as fh:
            w = csv.writer(fh)
            for i in range(sh.nrows):
                w.writerow([sh.cell_value(i, j) for j in range(sh.ncols)])
        print("  conversion .xls -> %s (%d lignes)" % (os.path.basename(CACHE_XWALK_CSV), sh.nrows))


# ============================================================================================
#  LES QUATRE MAILLONS
# ============================================================================================
def _exige(chemin: str) -> str:
    if not os.path.exists(chemin):
        raise SystemExit("cache absent : %s — lancer : python3 ingestion/ingere_bls_oes.py moissonne"
                         % chemin)
    return chemin


def isco_vers_soc2010() -> dict:
    """groupe ISCO-08 (4 chiffres) -> {codes SOC 2010}, depuis le CSV converti du crosswalk BLS."""
    table = collections.defaultdict(set)
    with open(_exige(CACHE_XWALK_CSV), encoding="utf-8") as fh:
        for row in csv.reader(fh):
            if len(row) >= 4 and re.fullmatch(r"\d{4}(\.0)?", (row[0] or "").strip()):
                soc = row[3].strip()
                if re.fullmatch(r"\d{2}-\d{4}", soc):
                    table[row[0].strip().split(".")[0]].add(soc)
    return table


def soc2010_vers_2018() -> dict:
    lignes = lit_xlsx(_exige(CACHE_SOC_10_18))
    i_hdr = next(i for i, r in enumerate(lignes) if "2010 SOC Code" in r.values())
    col = {v: k for k, v in lignes[i_hdr].items()}
    table = collections.defaultdict(set)
    for r in lignes[i_hdr + 1:]:
        a = (r.get(col["2010 SOC Code"]) or "").strip()
        b = (r.get(col["2018 SOC Code"]) or "").strip()
        if a and b:
            table[a].add(b)
    return table


def medianes_oes() -> dict:
    """code SOC 2018 -> (titre, médiane annuelle str) pour les lignes détaillées d'OEWS. « # » devient le
    fait de plafond ; « * » (non publié) est ABSENT du dict (écarté en aval, compté)."""
    with zipfile.ZipFile(_exige(CACHE_OES)) as z:
        interne = [n for n in z.namelist() if n.endswith(".xlsx")]
        if not interne:
            raise SystemExit("aucun .xlsx dans %s — le format de l'export OEWS a changé" % CACHE_OES)
        tmp = os.path.join(RAW, "_oes_extrait.xlsx")
        with open(tmp, "wb") as fh:
            fh.write(z.read(interne[0]))
    lignes = lit_xlsx(tmp)
    os.remove(tmp)
    col = {v: k for k, v in lignes[0].items()}
    table = {}
    for r in lignes[1:]:
        if (r.get(col["O_GROUP"]) or "") != "detailed":
            continue
        code = (r.get(col["OCC_CODE"]) or "").strip()
        brut = (r.get(col["A_MEDIAN"]) or "").strip()
        if not code or brut in ("", "*"):
            continue
        if brut == "#":
            table[code] = (r.get(col["OCC_TITLE"]) or "?", PLAFOND)
        else:
            table[code] = (r.get(col["OCC_TITLE"]) or "?",
                           "{:,.0f} $/an".format(float(brut)).replace(",", " "))
    return table


def _isco_du_store() -> dict:
    """metier -> groupe ISCO-08 4 chiffres, depuis `code_isco_metier` (ESCO ajoute un suffixe « .n »)."""
    chemin = os.path.join(os.environ.get("LECTEUR_DATASETS_DIR",
                          os.path.join(os.path.expanduser("~"), ".verax", "datasets", "lecteur")),
                          "code_isco_metier.jsonl")
    if not os.path.exists(chemin):
        raise SystemExit("table `code_isco_metier` absente du store — lancer d'abord ingere_esco.py")
    table = {}
    with open(chemin, encoding="utf-8") as fh:
        for ligne in fh:
            if ligne.startswith('{"_relation"'):
                continue
            o = json.loads(ligne)
            g = o["valeur"].split(".")[0]
            if re.fullmatch(r"\d{4}", g):
                table[o["entite"]] = g
    return table


def valeur_oes(groupe: str, socs: list, medianes: dict) -> tuple:
    """(valeur, nb d'occupations écartées faute de médiane publiée). `socs` = SOC 2018 du groupe, triés.
    Liste EXHAUSTIVE ; None si AUCUNE occupation n'a de médiane publiée (le métier reste non traité)."""
    connus = [(s, medianes[s]) for s in sorted(socs) if s in medianes]
    if not connus:
        return None, len(socs)
    corps = " ; ".join("%s « %s » : %s" % (s, titre, mediane) for s, (titre, mediane) in connus)
    tete = ("groupe ISCO-08 %s ; médianes salariales annuelles ÉTATS-UNIS (BLS OEWS %s) des occupations "
            "SOC 2018 que les crosswalks BLS associent à ce groupe (médiane PAR OCCUPATION SOC, pas par "
            "métier précis) : %s") % (groupe, MILLESIME_OES, corps)
    ecartees = len(socs) - len(connus)
    if ecartees:
        tete += " ; %d occupation(s) du groupe sans médiane publiée par OEWS" % ecartees
    return tete, ecartees


def publie_depuis_cache() -> None:
    print("== BLS OEWS — axe « rémunération médiane » (part États-Unis, MIX) ==")
    i2s = isco_vers_soc2010()
    s18 = soc2010_vers_2018()
    med = medianes_oes()
    if len(i2s) < 300 or len(s18) < 700 or len(med) < 700:
        raise ValueError("maillon tronqué : %d groupes ISCO, %d codes SOC2010, %d médianes — refus de "
                         "publier" % (len(i2s), len(s18), len(med)))
    print("  maillons : %d groupes ISCO -> SOC2010 · %d SOC2010 -> 2018 · %d médianes détaillées"
          % (len(i2s), len(s18), len(med)))

    isco = _isco_du_store()
    sys.path.insert(0, os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "outils"))
    from genere_sujets import metiers_de_la_carte
    metiers, _, _ = metiers_de_la_carte()
    print("  univers : %d métiers de la carte, %d avec code ISCO (plafond ESCO amont)"
          % (len(metiers), sum(1 for m in metiers if m in isco)))

    paires, sans_mediane = [], 0
    for m in metiers:
        g = isco.get(m)
        if not g:
            continue
        socs = {b for a in i2s.get(g, ()) for b in s18.get(a, ())}
        if not socs:
            continue
        v, _e = valeur_oes(g, sorted(socs), med)
        if v is None:
            sans_mediane += 1                     # ex. militaires : OEWS ne les couvre pas -> non traité
            continue
        paires.append((m, v))
    if len(paires) < 300:
        raise ValueError("chaîne suspecte : %d métiers seulement — maillons à réauditer" % len(paires))
    print("  métiers publiés : %d | sans AUCUNE médiane publiée (restent non traités) : %d"
          % (len(paires), sans_mediane))
    publie("salaire_median_soc_us_metier", "convention", SRC, sorted(paires))


if __name__ == "__main__":
    mode = sys.argv[1] if len(sys.argv) > 1 else "publie"
    if mode == "moissonne":
        moissonne()
    elif mode == "publie":
        publie_depuis_cache()
    else:
        raise SystemExit("usage : ingere_bls_oes.py [moissonne|publie]")
