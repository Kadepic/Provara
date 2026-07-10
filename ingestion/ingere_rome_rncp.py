"""
INGESTION ROME + RNCP — l'axe « formation, diplômes » que ni Wikidata ni ESCO ne fermaient (mandat « traiter
tout le backlog », piste §4 du runbook sondée le 2026-07-10 : « RNCP jamais interrogé »).

DEUX SOURCES OFFICIELLES, OUVERTES, SANS CLÉ :
  • ROME v4 (France Travail) — « Toutes les données du ROME », open-data CSV. Le runbook croyait le lien
    métier→référentiel prisonnier d'`api.francetravail.io` (HTTP 401) : FAUX pour les appellations, le zip
    open-data publie `referentiel_appellation` (14 301 appellations → code ROME) librement.
  • RNCP (France Compétences) — export CSV quotidien sur data.gouv. `Standard` porte intitulé + niveau
    CEC + statut ACTIF de chaque fiche ; `Rome` porte fiche → code(s) ROME (67 075 liens).

LA CHAÎNE, ET CE QU'ELLE AFFIRME EXACTEMENT (leçon ESCO : ne jamais voler une réponse d'une granularité
qu'aucune source n'affirme) :
  1. « l'appellation A relève du code ROME C »            — affirmé par France Travail, niveau APPELLATION ;
  2. « la fiche RNCP F est enregistrée sous le code C »    — affirmé par France Compétences, niveau CODE.
PERSONNE n'affirme « la fiche F prépare au métier A ». La valeur publiée dit donc LES DEUX FAITS, code
visible : « code ROME C (libellé) ; certifications RNCP actives enregistrées sous ce code : … ». Exemple
qui impose cette honnêteté : « nanotechnologue » relève de K2402 (recherche en sciences), dont les fiches
vont des neurosciences à la géographie — les présenter comme « les formations du nanotechnologue » serait
le vol de gestes rejoué.

DEUX RELATIONS PUBLIÉES :
  • `code_rome_metier`          — le code ROME du métier (fait France Travail, niveau appellation) ;
  • `certification_rncp_metier` — les certifications RNCP ACTIVES enregistrées sous ce code, intitulé +
                                  niveau CEC + n° de fiche ; ou le fait NÉGATIF attribué et daté (« aucune
                                  certification active sous ce code à l'export du JJ/MM/AAAA ») — le RNCP
                                  est le répertoire EXHAUSTIF français, l'absence y est un fait clos.

CE QUE ÇA NE FERME PAS (le sujet reste MIX -> PARTIEL, jamais TRAITÉ) : la formation d'un métier varie par
PAYS (la PARTIE VI le dit déjà : « programmes et diplômes officiels — varient par pays ET par année »).
Le RNCP ferme la part FRANÇAISE contemporaine. Les métiers historiques/étrangers du store (« Akyn »,
« Busshi ») n'ont pas d'appellation ROME : plafond STRUCTUREL, même famille que le plafond ESCO.

FAUX=0 — les gardes de l'ALIGNEMENT :
  1. EXPANSION GENRÉE STRUCTURELLE, côté ROME seulement. Le référentiel écrit « Abatteur / Abatteuse de
     carrière » : format documenté « masculin / féminin queue-commune ». On reconstruit « Abatteur de
     carrière » en recollant la queue (mots du féminin au-delà du compte de mots du masculin). AUCUNE
     expansion si : ≠ 2 segments « / », virgule présente, ou féminin plus court que le masculin.
     Côté MÉTIER : les variantes ESCO (`ingere_esco._variantes`), une seule définition du doublet de genre
     dans le projet.
  2. UNICITÉ CÔTÉ ROME : une forme portée par PLUSIEURS codes ROME distincts est ÉCARTÉE de l'index.
  3. UNICITÉ CÔTÉ MÉTIER : un métier dont les variantes atteignent PLUSIEURS codes est REJETÉ (ambigu).
     Sans correspondance : NON TRAITÉ, et le dit. Égalité EXACTE (NFC, minuscules), jamais d'accents pliés.
  4. ACTIVES SEULEMENT : `Actif == ACTIVE` dans l'export Standard — le statut est le drapeau de la source,
     pas une inférence sur les dates. JAMAIS de top-N : toutes les fiches actives du code, triées.
  5. UNIVERS = métiers de la CARTE (`genere_sujets.metiers_de_la_carte`, donc l'oracle `est_metier`) :
     on n'invente pas de sujets, on traite ceux qui existent.

Le moissonnage est CACHÉ sur disque (`datasets/_raw/rome_open_data_csv.zip`, `rncp_export_csv.zip`) :
rejouer l'ingestion ne re-télécharge pas. Le réseau ne vit que dans `moissonne()`.

Usage :
    python3 ingestion/ingere_rome_rncp.py moissonne    # 2 zips (~14 Mo), cache sur disque
    python3 ingestion/ingere_rome_rncp.py publie       # hors ligne, depuis le cache
"""
from __future__ import annotations

import collections
import csv
import io
import json
import os
import re
import sys
import time
import unicodedata
import urllib.request
import zipfile

from ingere_esco import _variantes as _variantes_metier
from ingere_wikidata import RAW, publie, snapshot_brut

URL_ROME = "https://api.francetravail.fr/api-nomenclatureemploi/v1/open-data/csv"
URL_RNCP_DATASET = "https://www.data.gouv.fr/api/1/datasets/5eebbc067a14b6fecc9c9976/"
UA = "Provara/1.0 (https://github.com/Provara-IA/Provara) offline-knowledge-ingestion"
CACHE_ROME = os.path.join(RAW, "rome_open_data_csv.zip")
CACHE_RNCP = os.path.join(RAW, "rncp_export_csv.zip")

SRC_CODE = ("ROME v4 (France Travail, open-data « Toutes les données du ROME », referentiel_appellation) — "
            "le code ROME dont relève l'appellation exactement égale au libellé du métier (expansion genrée "
            "structurelle « masculin / féminin queue-commune » ; formes ambiguës multi-codes écartées des "
            "deux côtés). Fait de niveau APPELLATION.")
SRC_RNCP = ("RNCP (France Compétences, export CSV data.gouv) × ROME (France Travail). La valeur affirme DEUX "
            "faits attribués et rien de plus : (1) le métier relève du code ROME indiqué (France Travail, "
            "niveau appellation) ; (2) les fiches listées sont les certifications ACTIVES enregistrées sous "
            "ce CODE (France Compétences, niveau code — PAS un lien fiche→métier, qu'aucune source "
            "n'affirme). Liste EXHAUSTIVE des fiches actives du code, jamais un extrait ; l'absence est un "
            "fait clos du répertoire, daté par l'export.")


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


def _url_rncp_csv() -> str:
    """La ressource `export-fiches-csv-*` la plus récente du jeu de données data.gouv (export quotidien)."""
    req = urllib.request.Request(URL_RNCP_DATASET, headers={"User-Agent": UA})
    with urllib.request.urlopen(req, timeout=60) as r:
        ds = json.loads(r.read().decode("utf-8"))
    candidates = sorted((r["title"], r["url"]) for r in ds.get("resources", [])
                        if r.get("title", "").startswith("export-fiches-csv-"))
    if not candidates:
        raise ValueError("data.gouv : aucune ressource export-fiches-csv-* — le format du jeu a changé")
    return candidates[-1][1]


def moissonne() -> None:
    os.makedirs(RAW, exist_ok=True)
    print("== MOISSONNAGE ROME + RNCP ==")
    _telecharge(URL_ROME, CACHE_ROME)
    print("  ROME  -> %s (%.1f Mo)" % (CACHE_ROME, os.path.getsize(CACHE_ROME) / 1e6))
    _telecharge(_url_rncp_csv(), CACHE_RNCP)
    print("  RNCP  -> %s (%.1f Mo)" % (CACHE_RNCP, os.path.getsize(CACHE_RNCP) / 1e6))


# ============================================================================================
#  LECTURE DES CACHES
# ============================================================================================
def _csv_du_zip(chemin_zip: str, motif: str, delim: str) -> list:
    """Les lignes (dict) du premier CSV du zip dont le nom contient `motif`. Lève, en NOMMANT le fichier et
    la commande de remoissonnage, si le zip ou le CSV manquent — une table vide qui ne lève pas est le pire
    des échecs."""
    if not os.path.exists(chemin_zip):
        raise SystemExit("cache absent : %s — lancer : python3 ingestion/ingere_rome_rncp.py moissonne"
                         % chemin_zip)
    with zipfile.ZipFile(chemin_zip) as z:
        noms = [n for n in z.namelist() if motif in n and n.endswith(".csv")]
        if not noms:
            raise SystemExit("aucun CSV « %s » dans %s — le format de l'export a changé" % (motif, chemin_zip))
        with z.open(noms[0]) as fh:
            return list(csv.DictReader(io.TextIOWrapper(fh, encoding="utf-8-sig"), delimiter=delim))


def _date_export_rncp(chemin_zip: str) -> str:
    """« JJ/MM/AAAA » lue dans le NOM des fichiers de l'export (export_fiches_CSV_Standard_2026_07_09.csv) :
    c'est la source qui date, pas l'horloge locale."""
    with zipfile.ZipFile(chemin_zip) as z:
        for n in z.namelist():
            m = re.search(r"(\d{4})_(\d{2})_(\d{2})\.csv$", n)
            if m:
                return "%s/%s/%s" % (m.group(3), m.group(2), m.group(1))
    raise SystemExit("date d'export introuvable dans les noms de fichiers de %s" % chemin_zip)


# ============================================================================================
#  ALIGNEMENT (c'est là que les faux naissent)
# ============================================================================================
def _formes_rome(libelle: str) -> set:
    """Formes d'une appellation ROME : la forme entière + l'expansion genrée STRUCTURELLE.

    « Abatteur / Abatteuse de carrière » -> {« abatteur / abatteuse de carrière », « abatteur de carrière »,
    « abatteuse de carrière »}. La queue commune (« de carrière ») est portée par le féminin ; le masculin
    la récupère en recollant les mots du féminin au-delà de son propre compte de mots. AUCUNE expansion si
    le libellé n'a pas EXACTEMENT deux segments « / », contient une virgule (qualificatif : « écrivain ou
    écrivaine, militaire » a déjà volé des gestes), ou si le féminin est plus court que le masculin."""
    lab = unicodedata.normalize("NFC", (libelle or "").strip())
    if not lab:
        return set()
    formes = {lab.lower()}
    if "," in lab:
        return formes
    parts = lab.split(" / ")
    if len(parts) == 2:
        lw, rw = parts[0].split(), parts[1].split()
        if 1 <= len(lw) <= len(rw):
            formes.add(" ".join(lw + rw[len(lw):]).lower())     # masculin + queue commune
            formes.add(parts[1].strip().lower())                # féminin complet
    return formes


def _nfc_bas(s: str) -> str:
    return unicodedata.normalize("NFC", s.strip()).lower()


def aligne(appellations: list, metiers: list):
    """metier -> code ROME, sous les gardes 2-3. `appellations` = lignes de referentiel_appellation."""
    par_forme = collections.defaultdict(set)
    for r in appellations:
        for lab in (r.get("libelle_appellation_long"), r.get("libelle_appellation_court")):
            if not lab:
                continue
            for f in _formes_rome(lab):
                par_forme[f].add(r["code_rome"])
    ambigues = {f for f, cs in par_forme.items() if len(cs) > 1}                      # GARDE 2
    index = {f: next(iter(cs)) for f, cs in par_forme.items() if len(cs) == 1}

    apparie, ambigus, absents = {}, 0, 0
    for m in metiers:
        cibles = {index[v] for v in _variantes_metier(_nfc_bas(m)) if v in index}
        if len(cibles) == 1:                                                          # GARDE 3
            apparie[m] = next(iter(cibles))
        elif len(cibles) > 1:
            ambigus += 1
        else:
            absents += 1
    print("  formes ROME : %d (dont %d ambiguës multi-codes, écartées)" % (len(par_forme), len(ambigues)))
    print("  métiers appariés : %d | ambigus rejetés : %d | sans appellation ROME : %d"
          % (len(apparie), ambigus, absents))
    return apparie


# ============================================================================================
#  VALEURS (ce que la table affirme, mot à mot)
# ============================================================================================
def _niveau(brut: str) -> str:
    m = re.fullmatch(r"NIV(\d)", (brut or "").strip())
    return " (niveau %s CEC)" % m.group(1) if m else ""


def valeur_rncp(code: str, lib_code: str, fiches: list, date_export: str) -> str:
    """`fiches` = [(numero, intitule, niveau_brut)] ACTIVES du code, déjà filtrées. Liste EXHAUSTIVE triée
    par numéro de fiche ; ou le fait négatif clos, daté par l'export."""
    tete = "code ROME %s (%s)" % (code, lib_code)
    if not fiches:
        return ("%s ; aucune certification RNCP active enregistrée sous ce code "
                "(export France Compétences du %s)") % (tete, date_export)
    tri = sorted(fiches, key=lambda f: int(re.sub(r"\D", "", f[0]) or 0))
    corps = " ; ".join("%s « %s »%s" % (num, intit, _niveau(niv)) for num, intit, niv in tri)
    return ("%s ; %d certification(s) RNCP active(s) enregistrée(s) sous ce code "
            "(export France Compétences du %s) : %s") % (tete, len(tri), date_export, corps)


def fiches_actives_par_code(lignes_standard: list, lignes_rome: list):
    """(actives {num: (intitulé, niveau)}, par_code {code: [(num, intitulé, niveau)]}, nb liens écartés).
    Le statut ACTIF est le drapeau de la SOURCE (`Actif == "ACTIVE"`), jamais une inférence sur les dates.
    Un lien vers une fiche inactive ou absente de Standard est écarté ET compté."""
    actives = {r["Numero_Fiche"]: (r["Intitule"], r["Nomenclature_Europe_Niveau"])
               for r in lignes_standard if r.get("Actif") == "ACTIVE"}
    par_code, ecartes = collections.defaultdict(list), 0
    for r in lignes_rome:
        num, code = r.get("Numero_Fiche", ""), r.get("Codes_Rome_Code", "")
        if num in actives and code:
            par_code[code].append((num, actives[num][0], actives[num][1]))
        elif num and num not in actives:
            ecartes += 1
    return actives, par_code, ecartes


def publie_depuis_cache() -> None:
    print("== ROME + RNCP — axe « formation, diplômes » (part française) ==")
    sys.path.insert(0, os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "outils"))
    from genere_sujets import metiers_de_la_carte
    metiers, n_oracle, _ = metiers_de_la_carte()
    print("  univers : %d métiers de la carte (oracle %d)" % (len(metiers), n_oracle))

    appellations = _csv_du_zip(CACHE_ROME, "referentiel_appellation", ",")
    codes = {r["code_rome"]: r["libelle_rome"] for r in _csv_du_zip(CACHE_ROME, "referentiel_code_rome_v", ",")
             if r.get("code_rome")}
    if len(appellations) < 10000 or len(codes) < 500:
        raise ValueError("ROME suspect : %d appellations, %d codes — refus de publier depuis un référentiel "
                         "tronqué" % (len(appellations), len(codes)))

    date_export = _date_export_rncp(CACHE_RNCP)
    actives, par_code, orphelines = fiches_actives_par_code(
        _csv_du_zip(CACHE_RNCP, "_Standard_", ";"), _csv_du_zip(CACHE_RNCP, "_Rome_", ";"))
    if not actives or not par_code:
        raise ValueError("RNCP suspect : %d fiches actives, %d codes liés — refus de publier"
                         % (len(actives), len(par_code)))
    print("  RNCP : %d fiches actives · %d codes ROME liés · %d liens écartés (fiche non active)"
          % (len(actives), len(par_code), orphelines))

    apparie = aligne(appellations, metiers)
    if len(apparie) < 300:
        raise ValueError("alignement suspect : %d métiers seulement — gardes ou format à réauditer"
                         % len(apparie))

    p_code = sorted((m, "%s — %s" % (c, codes.get(c, "?"))) for m, c in apparie.items())
    p_rncp = sorted((m, valeur_rncp(c, codes.get(c, "?"), par_code.get(c, []), date_export))
                    for m, c in apparie.items())
    avec = sum(1 for m, c in apparie.items() if par_code.get(c))
    print("  dont %d métiers avec >=1 fiche active, %d avec fait négatif daté" % (avec, len(apparie) - avec))

    snapshot_brut("rome_rncp_stats", [{"metiers_carte": len(metiers), "apparies": len(apparie),
                                       "avec_fiches": avec, "fiches_actives": len(actives),
                                       "date_export_rncp": date_export}])
    publie("code_rome_metier", "convention", SRC_CODE, p_code)
    publie("certification_rncp_metier", "convention", SRC_RNCP, p_rncp)


if __name__ == "__main__":
    mode = sys.argv[1] if len(sys.argv) > 1 else "publie"
    if mode == "moissonne":
        moissonne()
    elif mode == "publie":
        publie_depuis_cache()
    else:
        raise SystemExit("usage : ingere_rome_rncp.py [moissonne|publie]")
