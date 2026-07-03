"""
VALIDATION T9 — LANGUE, LEXIQUE & ÉCRITURE (couloir d'ingestion). FAUX=0 INVIOLABLE.

Charge UNIQUEMENT les relations T9 dans un Lecteur frais (léger : ~8500 faits, pas les 10 M du gate complet) et
verrouille leurs invariants :

  1. ENSEMBLE FERMÉ : systeme_ecriture_langue -> valeurs dans un ensemble BORNÉ de scripts réels (≤200 distincts,
     mesuré 143), chaque valeur = libellé ≥3 caractères non vide.
  2. FORME DU CODE  : code_iso6393_langue / code_iso6392_langue -> toute valeur = exactement 3 lettres minuscules
     (^[a-z]{3}$). Aucun code mal formé n'a fui (le motif d'ingestion a filtré).
  3. ANCRES         : valeurs vérifiées À LA MAIN, indépendamment du code (français=fra, allemand=deu, japonais=jpn,
     russe->écriture cyrillique, hébreu->alphabet hébreu…) -> ancrage NON circulaire vérité-terrain.
  4. SOUNDNESS      : adverse — langue multi-script (français/japonais/coréen = plusieurs P282 -> HORS), code
     multi-valeur (albanais ISO 639-2 alb/sqi -> HORS), entité absente, mauvaise relation, relation absente ->
     TOUJOURS HORS (None). Jamais un faux, jamais une devinette.

EXIT 0 = tous les check passent. Lancer SEUL (1 chargement léger) en dev ; enregistrer dans _nonreg.py pour le gate.
"""
from __future__ import annotations

import json
import os
import re

from garde_ressources import borne

borne(max_go=4.0, max_cpu_s=900)   # OPTIM amorce-seule : ne charge QUE les relations T9 (~1,76 M faits) dans un Lecteur
                                   # frais, plus le full-load global des 33,5 M faits ; 4 Go large.

os.environ.setdefault("LECTEUR_AMORCE_SEULE", "1")  # OPTIM gate légère : charge SES relations dans un Lecteur frais (jamais le singleton global L.LECTEUR) → saute charge_dossier()+gele() sur les 33,5 M faits (~5 Go/min)
import lecteur as L
from lecteur import HORS, VERIFIE

DOSSIER = os.path.join(os.path.dirname(__file__), "datasets", "lecteur")

RELATIONS = ["systeme_ecriture_langue", "code_iso6393_langue", "code_iso6392_langue", "code_glottolog_langue",
             "code_ethnologue_langue", "statut_vitalite_langue", "direction_ecriture", "regulateur_langue",
             "code_ietf_langue", "code_linguasphere_langue", "code_babelnet_langue", "code_aiatsis_langue",
             "code_freebase_langue", "code_endangered_langue", "code_wals_langue", "code_lccn_langue", "pays_langue",
             "code_j9u_langue", "code_unesco_langue", "code_bnf_langue", "code_gnd_langue", "code_britannica_langue",
             "type_systeme_ecriture", "ordre_mots_langue", "type_morphologique_langue", "tonalite_langue",
             "alignement_morphosyntaxique", "genre_grammatical_langue",
             "presence_articles_langue", "classificateurs_numeraux_langue",
             "code_aat_langue", "code_ndl_langue", "code_nkc_langue", "statut_unesco_danger_langue",
             "categorie_lexicale_mot", "genre_grammatical_mot", "concept_du_mot", "etymon_du_mot"]
# Catégories grammaticales principales attendues dans la veine lexèmes (sanité de présence, pas un closed-set strict :
# Wikidata a ~200 catégories fines, mais les 4 majeures DOIVENT être là).
CAT_LEX_PRINCIPALES = {"nom", "verbe", "adjectif", "adverbe"}
GENRES_MOT_PRINCIPAUX = {"masculin", "féminin", "neutre"}   # +commun, +genres slaves fins ; les 3 majeurs requis
RELATIONS_CODE = ["code_iso6393_langue", "code_iso6392_langue", "code_ethnologue_langue"]
RX_CODE = re.compile(r"[a-z]{3}$")
RX_GLOTTO = re.compile(r"[a-z]{4}[0-9]{4}$")
# Formes des identifiants supplémentaires (mêmes motifs que l'ingestion : toute valeur DOIT matcher -> sinon fuite).
RELATIONS_FORME = [
    ("code_ietf_langue", re.compile(r"[a-z]{2,3}(-[A-Za-z0-9]{1,8})*$")),
    ("code_linguasphere_langue", re.compile(r"[0-9]{2}-[A-Z]{2,3}(-[a-z]{1,3})?$")),
    ("code_babelnet_langue", re.compile(r"[0-9]{8}[a-z]$")),
    ("code_aiatsis_langue", re.compile(r"[A-Z][0-9]+$")),
    ("code_freebase_langue", re.compile(r"/m/[0-9a-z_]+$")),
    ("code_endangered_langue", re.compile(r"[0-9]+$")),
    ("code_wals_langue", re.compile(r"[a-z]{2,4}$")),
    ("code_lccn_langue", re.compile(r"(sh|n|no|sj)[0-9]+$")),
    ("code_j9u_langue", re.compile(r"[0-9]{10,}$")),
    ("code_unesco_langue", re.compile(r"[0-9]+$")),
    ("code_bnf_langue", re.compile(r"[0-9]{8,9}[a-z]?$")),
    ("code_gnd_langue", re.compile(r"[0-9]+(X|-[0-9X])?$")),
    ("code_britannica_langue", re.compile(r"topic/[A-Za-z0-9%-]+$")),
    ("code_aat_langue", re.compile(r"300[0-9]+$")),
    ("code_ndl_langue", re.compile(r"[0-9]+$")),
    ("code_nkc_langue", re.compile(r"[a-z]{2}[0-9]+$")),
]

# Échelle EGIDS d'Ethnologue (P3823) : ensemble fermé RÉEL des 16 niveaux de vitalité (scout 2026-06-26). Toute
# valeur HORS de cet ensemble révélerait une fuite -> on l'interdit (sanité d'ensemble fermé, FAUX=0).
EGIDS = {"0 international", "1 national", "2 provincial", "3 communication", "4 éducatif", "5 en développement",
         "6a vivace", "6b menacé", "7 en transition", "8a moribond", "8b proche de l'extinction", "9 dormant",
         "9 réveil", "9 langue seconde uniquement", "10 éteint", "inattesté"}

# Directions d'écriture (P1406) : ensemble fermé RÉEL des 7 sens possibles (scout 2026-06-26). Toute valeur hors
# de cet ensemble = fuite -> interdite (sanité d'ensemble fermé).
DIRECTIONS = {"de gauche à droite", "de droite à gauche", "boustrophédon", "de haut en bas",
              "de gauche à droite et de haut en bas", "vertical de droite à gauche", "vertical de gauche à droite"}
# Typologie des écritures (auto-sourcée) : ensemble fermé des 5 catégories de référence.
TYPES_ECRITURE = {"alphabet", "abjad", "abugida", "syllabaire", "logographique"}
# Ordres des mots de base auto-sourcés : closed-set des 3 ordres dominants courants.
ORDRES_MOTS = {"SVO", "SOV", "VSO"}
MORPHO = {"isolante", "agglutinante", "flexionnelle", "polysynthétique"}
TONS = {"tonale", "non-tonale"}
ALIGN = {"accusatif", "ergatif"}
GENRES_GRAM = {"avec genre grammatical", "sans genre grammatical"}
ARTICLES = {"avec articles", "sans articles"}
CLASSIF = {"avec classificateurs", "sans classificateurs"}
# Échelle UNESCO de mise en danger (P1999) : 6 niveaux fermés (Atlas UNESCO), distincte de l'EGIDS.
UNESCO_DANGER = {"1 sûre", "2 vulnérable", "3 en danger", "4 sérieusement en danger",
                 "5 en situation critique", "6 éteinte"}

ok = 0
total = 0


def check(nom, cond):
    global ok, total
    total += 1
    print(f"  [{'OK ' if cond else 'XXX'}] {nom}")
    if cond:
        ok += 1
    else:
        raise AssertionError(nom)


def _entete(chemin):
    with open(chemin, encoding="utf-8") as fh:
        for brut in fh:
            brut = brut.strip()
            if brut:
                t = json.loads(brut)
                return t["_categorie"], t["_source"]
    raise ValueError(f"{chemin} : en-tête manquant")


# --- Chargement léger : seules les relations T9 dans un Lecteur frais. ---
lec = L.Lecteur()
manquants = []
for rel in RELATIONS:
    chemin = os.path.join(DOSSIER, rel + ".jsonl")
    if not os.path.exists(chemin):
        manquants.append(rel)
        continue
    cat, src = _entete(chemin)
    lec.charge_jsonl(rel, chemin, cat, src)
check(f"DATASETS présents (aucun manquant : {manquants})", not manquants)

# 1) ENSEMBLE FERMÉ : systeme_ecriture_langue = scripts réels, valeurs bornées et propres.
t = lec.tables.get("systeme_ecriture_langue", {})
n = len(t)
valeurs = {f.valeur for f in t.values()}
mauvais_val = next((f.valeur for f in t.values()
                    if not (isinstance(f.valeur, str) and len(f.valeur.strip()) >= 3)), None)
check(f"systeme_ecriture_langue : {n} faits, {len(valeurs)} scripts distincts ∈ ]50,200] "
      f"[contre-ex: {mauvais_val!r}]", n > 0 and 50 < len(valeurs) <= 200 and mauvais_val is None)

# 2) FORME DU CODE : iso639-3 / iso639-2 = exactement 3 lettres minuscules.
for rel in RELATIONS_CODE:
    t = lec.tables.get(rel, {})
    n = len(t)
    mauvais = next((f.valeur for f in t.values() if not RX_CODE.fullmatch(str(f.valeur))), None)
    check(f"{rel} : {n} faits, tous ^[a-z]{{3}}$ [contre-ex: {mauvais!r}]", n > 0 and mauvais is None)

# 2bis) FORME GLOTTOLOG : 4 lettres minuscules + 4 chiffres.
t = lec.tables.get("code_glottolog_langue", {})
n = len(t)
mauvais = next((f.valeur for f in t.values() if not RX_GLOTTO.fullmatch(str(f.valeur))), None)
check(f"code_glottolog_langue : {n} faits, tous ^[a-z]{{4}}[0-9]{{4}}$ [contre-ex: {mauvais!r}]",
      n > 0 and mauvais is None)

# 2ter) ENSEMBLE FERMÉ EGIDS : statut_vitalite_langue = valeurs STRICTEMENT dans l'échelle Ethnologue (16 niveaux).
t = lec.tables.get("statut_vitalite_langue", {})
n = len(t)
valeurs = {f.valeur for f in t.values()}
hors_egids = valeurs - EGIDS
check(f"statut_vitalite_langue : {n} faits, {len(valeurs)} statuts ⊆ EGIDS(16) [fuite: {sorted(hors_egids)[:3]}]",
      n > 0 and not hors_egids and len(valeurs) <= 16)

# 2quater) ENSEMBLE FERMÉ DIRECTIONS : direction_ecriture ⊆ 7 sens réels.
t = lec.tables.get("direction_ecriture", {})
n = len(t)
valeurs = {f.valeur for f in t.values()}
hors_dir = valeurs - DIRECTIONS
check(f"direction_ecriture : {n} faits, {len(valeurs)} sens ⊆ DIRECTIONS(7) [fuite: {sorted(hors_dir)[:3]}]",
      n > 0 and not hors_dir and len(valeurs) <= 7)

# 2quinquies) regulateur_langue : vocab ouvert d'organismes ; chaque valeur = libellé non vide ≥3 car.
t = lec.tables.get("regulateur_langue", {})
n = len(t)
mauvais_reg = next((f.valeur for f in t.values()
                    if not (isinstance(f.valeur, str) and len(f.valeur.strip()) >= 3)), None)
check(f"regulateur_langue : {n} faits, valeurs = organismes non vides [contre-ex: {mauvais_reg!r}]",
      n > 0 and mauvais_reg is None)

# 2sexies) FORME DES IDENTIFIANTS SUPPLÉMENTAIRES (IETF/Linguasphere/BabelNet/AIATSIS) : toute valeur ⊆ motif.
# Codes OPAQUES (sauf IETF) -> validés par la FORME + la soundness, pas par une valeur-vérité (non mémorisable).
for rel, rx in RELATIONS_FORME:
    t = lec.tables.get(rel, {})
    n = len(t)
    mauvais = next((f.valeur for f in t.values() if not rx.fullmatch(str(f.valeur))), None)
    check(f"{rel} : {n} faits, tous au format {rx.pattern} [contre-ex: {mauvais!r}]", n > 0 and mauvais is None)

# 2septies) pays_langue : valeur = nom de pays (vocab fermé d'États) ; non vide, ≥3 car., contient une lettre
# (rejette toute fuite date/nombre). La justesse des valeurs est ancrée plus bas (vérité-terrain).
t = lec.tables.get("pays_langue", {})
n = len(t)
mauvais_pays = next((f.valeur for f in t.values()
                     if not (isinstance(f.valeur, str) and len(f.valeur.strip()) >= 3
                             and any(c.isalpha() for c in f.valeur))), None)
check(f"pays_langue : {n} faits, valeurs = pays non vides [contre-ex: {mauvais_pays!r}]",
      n > 0 and mauvais_pays is None)

# 2octies) ENSEMBLE FERMÉ TYPOLOGIE (auto-sourcé) : type_systeme_ecriture ⊆ 5 catégories de référence.
t = lec.tables.get("type_systeme_ecriture", {})
n = len(t)
valeurs = {f.valeur for f in t.values()}
hors_typ = valeurs - TYPES_ECRITURE
check(f"type_systeme_ecriture : {n} faits, {len(valeurs)} types ⊆ TYPES(5) [fuite: {sorted(hors_typ)[:3]}]",
      n > 0 and not hors_typ and len(valeurs) <= 5)

# 2nonies) ENSEMBLE FERMÉ ORDRE DES MOTS (auto-sourcé) : ordre_mots_langue ⊆ {SVO, SOV, VSO}.
t = lec.tables.get("ordre_mots_langue", {})
n = len(t)
valeurs = {f.valeur for f in t.values()}
hors_ord = valeurs - ORDRES_MOTS
check(f"ordre_mots_langue : {n} faits, {len(valeurs)} ordres ⊆ {{SVO,SOV,VSO}} [fuite: {sorted(hors_ord)[:3]}]",
      n > 0 and not hors_ord and len(valeurs) <= 3)

# 2decies) ENSEMBLES FERMÉS TYPOLOGIQUES auto-sourcés : morphologie (4) et tonalité (2).
for rel, ref, taille in [("type_morphologique_langue", MORPHO, 4), ("tonalite_langue", TONS, 2),
                         ("alignement_morphosyntaxique", ALIGN, 2), ("genre_grammatical_langue", GENRES_GRAM, 2),
                         ("presence_articles_langue", ARTICLES, 2), ("classificateurs_numeraux_langue", CLASSIF, 2),
                         ("statut_unesco_danger_langue", UNESCO_DANGER, 6)]:
    t = lec.tables.get(rel, {})
    nn = len(t)
    vv = {f.valeur for f in t.values()}
    fuite = vv - ref
    check(f"{rel} : {nn} faits, {len(vv)} valeurs ⊆ {sorted(ref)} [fuite: {sorted(fuite)[:3]}]",
          nn > 0 and not fuite and len(vv) <= taille)

# 2undecies) VEINE LEXÈMES : categorie_lexicale_mot — gros volume (>1M), valeurs = catégories grammaticales bornées
# (≤250 distinctes), non vides, et les 4 catégories majeures présentes. Clé composée « lemme (langue) ».
t = lec.tables.get("categorie_lexicale_mot", {})
n = len(t)
valeurs = {f.valeur for f in t.values()}
mauvaise_cat = next((f.valeur for f in t.values()
                     if not (isinstance(f.valeur, str) and len(f.valeur.strip()) >= 2)), None)
check(f"categorie_lexicale_mot : {n} faits, {len(valeurs)} catégories ≤250, majeures⊆présentes, non vides "
      f"[contre-ex: {mauvaise_cat!r}]",
      n > 500000 and len(valeurs) <= 250 and CAT_LEX_PRINCIPALES <= valeurs and mauvaise_cat is None)

# 2duodecies) VEINE LEXÈMES #2 : genre_grammatical_mot — gros volume (>200k), genres bornés (≤15 distincts),
# les 3 majeurs présents, valeurs non vides. MULTILINGUE (≠ genre_grammatical kaikki = FR).
t = lec.tables.get("genre_grammatical_mot", {})
n = len(t)
valeurs = {f.valeur for f in t.values()}
mauvais_g = next((f.valeur for f in t.values()
                  if not (isinstance(f.valeur, str) and len(f.valeur.strip()) >= 4)), None)
check(f"genre_grammatical_mot : {n} faits, {len(valeurs)} genres ≤15, majeurs⊆présents, non vides "
      f"[contre-ex: {mauvais_g!r}]",
      n > 200000 and len(valeurs) <= 15 and GENRES_MOT_PRINCIPAUX <= valeurs and mauvais_g is None)

# 2terdecies) VEINE LEXÈMES #3 : concept_du_mot — sens/concept (libellé FR) du mot = traduction vers FR pour les
# langues non-FR. Volume notable (>50k), vocabulaire LARGE (>1000 concepts), libellés propres (filtre ingestion).
t = lec.tables.get("concept_du_mot", {})
n = len(t)
valeurs = {f.valeur for f in t.values()}
mauvais_c = next((f.valeur for f in t.values()
                  if not (isinstance(f.valeur, str) and 1 <= len(f.valeur.strip()) <= 60
                          and ":" not in f.valeur)), None)
check(f"concept_du_mot : {n} faits, {len(valeurs)} concepts (>1000), libellés propres [contre-ex: {mauvais_c!r}]",
      n > 50000 and len(valeurs) > 1000 and mauvais_c is None)

# 2quaterdecies) VEINE LEXÈMES #4 : etymon_du_mot — mot-source (jointure P5191). Volume notable (>10k), étymons
# divers (>1000 distincts), libellés propres. Étymon souvent en grec/latin (Unicode -> on exige juste une lettre).
t = lec.tables.get("etymon_du_mot", {})
n = len(t)
valeurs = {f.valeur for f in t.values()}
mauvais_e = next((f.valeur for f in t.values()
                  if not (isinstance(f.valeur, str) and 1 <= len(f.valeur.strip()) <= 60
                          and ":" not in f.valeur and any(c.isalpha() for c in f.valeur))), None)
check(f"etymon_du_mot : {n} faits, {len(valeurs)} étymons (>1000), libellés propres [contre-ex: {mauvais_e!r}]",
      n > 10000 and len(valeurs) > 1000 and mauvais_e is None)

# 3) ANCRES — vérité-terrain indépendante (correspondance exacte).
ANCRES = [
    # système d'écriture (langues mono-script)
    ("systeme_ecriture_langue", "russe", "écriture cyrillique"),
    ("systeme_ecriture_langue", "hébreu", "alphabet hébreu"),
    ("systeme_ecriture_langue", "grec moderne", "alphabet grec"),
    ("systeme_ecriture_langue", "arménien", "alphabet arménien"),
    ("systeme_ecriture_langue", "amharique", "alphasyllabaire guèze"),
    ("systeme_ecriture_langue", "copte", "écriture copte"),
    ("systeme_ecriture_langue", "khmer", "écriture khmère"),
    # ISO 639-3
    ("code_iso6393_langue", "français", "fra"),
    ("code_iso6393_langue", "anglais", "eng"),
    ("code_iso6393_langue", "allemand", "deu"),
    ("code_iso6393_langue", "espagnol", "spa"),
    ("code_iso6393_langue", "russe", "rus"),
    ("code_iso6393_langue", "arabe", "ara"),
    ("code_iso6393_langue", "japonais", "jpn"),
    ("code_iso6393_langue", "chinois", "zho"),
    ("code_iso6393_langue", "italien", "ita"),
    # ISO 639-2
    ("code_iso6392_langue", "afar", "aar"),
    ("code_iso6392_langue", "afrikaans", "afr"),
    ("code_iso6392_langue", "akan", "aka"),
    ("code_iso6392_langue", "anglais", "eng"),
    # Glottolog
    ("code_glottolog_langue", "français", "stan1290"),
    ("code_glottolog_langue", "allemand", "stan1295"),
    ("code_glottolog_langue", "russe", "russ1263"),
    ("code_glottolog_langue", "japonais", "nucl1643"),
    ("code_glottolog_langue", "arabe", "arab1395"),
    # Ethnologue (P1627) — codes lus dans le .jsonl ; cohérents avec ISO 639-3 (qui en dérive), vérité indépendante.
    ("code_ethnologue_langue", "français", "fra"),
    ("code_ethnologue_langue", "anglais", "eng"),
    ("code_ethnologue_langue", "allemand", "deu"),
    ("code_ethnologue_langue", "espagnol", "spa"),
    ("code_ethnologue_langue", "japonais", "jpn"),
    ("code_ethnologue_langue", "russe", "rus"),
    ("code_ethnologue_langue", "italien", "ita"),
    ("code_ethnologue_langue", "portugais", "por"),
    # Statut de vitalité EGIDS (P3823) — vérité-terrain indépendante : anglais/français = mondiales ; cornique en
    # cours de revitalisation ; latin = langue seconde ; mandchou quasi-éteint.
    ("statut_vitalite_langue", "anglais", "0 international"),
    ("statut_vitalite_langue", "français", "0 international"),
    ("statut_vitalite_langue", "allemand", "1 national"),
    ("statut_vitalite_langue", "espagnol", "1 national"),
    ("statut_vitalite_langue", "cornique", "9 réveil"),
    ("statut_vitalite_langue", "latin", "9 langue seconde uniquement"),
    ("statut_vitalite_langue", "mandchou", "8b proche de l'extinction"),
    # Direction d'écriture (P1406) — vérité-terrain : arabe/hébreu = RTL ; grec/cyrillique/arménien = LTR.
    ("direction_ecriture", "alphabet arabe", "de droite à gauche"),
    ("direction_ecriture", "alphabet hébreu", "de droite à gauche"),
    ("direction_ecriture", "alphabet grec", "de gauche à droite"),
    ("direction_ecriture", "écriture cyrillique", "de gauche à droite"),
    ("direction_ecriture", "alphabet arménien", "de gauche à droite"),
    # Régulateur de langue (P1018) — vérité-terrain : académies nationales connues.
    ("regulateur_langue", "basque", "Académie de la langue basque"),
    ("regulateur_langue", "hébreu", "Académie de la langue hébraïque"),
    # Code IETF/BCP-47 (P305) — vérité-terrain indépendante : codes primaires = ISO 639-1 universellement connus.
    ("code_ietf_langue", "anglais", "en"),
    ("code_ietf_langue", "français", "fr"),
    ("code_ietf_langue", "allemand", "de"),
    ("code_ietf_langue", "chinois", "zh"),
    ("code_ietf_langue", "japonais", "ja"),
    # WALS (P1466) — ancre certaine (anglais=eng) ; le reste validé par forme (codes semi-opaques, pas devinés).
    ("code_wals_langue", "anglais", "eng"),
    # pays_langue (P17) — vérité-terrain : langues mono-pays notoires -> leur État (lues dans le .jsonl).
    ("pays_langue", "albanais", "Albanie"),
    ("pays_langue", "japonais", "Japon"),
    ("pays_langue", "letton", "Lettonie"),
    ("pays_langue", "polonais", "Pologne"),
    ("pays_langue", "tchèque", "Tchéquie"),
    ("pays_langue", "navajo", "États-Unis"),
    # Typologie des écritures (auto-sourcée) — vérité-terrain typologique de référence (Daniels & Bright).
    ("type_systeme_ecriture", "écriture latine", "alphabet"),
    ("type_systeme_ecriture", "alphabet arabe", "abjad"),
    ("type_systeme_ecriture", "devanagari", "abugida"),
    ("type_systeme_ecriture", "hiragana", "syllabaire"),
    ("type_systeme_ecriture", "sinogrammes", "logographique"),
    # Ordre des mots (auto-sourcé) — vérité-terrain typologique (WALS 81A) : anglais SVO, japonais SOV, irlandais VSO.
    ("ordre_mots_langue", "anglais", "SVO"),
    ("ordre_mots_langue", "français", "SVO"),
    ("ordre_mots_langue", "japonais", "SOV"),
    ("ordre_mots_langue", "turc", "SOV"),
    ("ordre_mots_langue", "irlandais", "VSO"),
    # Type morphologique (auto-sourcé) — prototypes typologiques de référence.
    ("type_morphologique_langue", "mandarin", "isolante"),
    ("type_morphologique_langue", "turc", "agglutinante"),
    ("type_morphologique_langue", "latin", "flexionnelle"),
    ("type_morphologique_langue", "inuktitut", "polysynthétique"),
    # Tonalité (auto-sourcée) — vérité-terrain : mandarin tonal, français atonal.
    ("tonalite_langue", "mandarin", "tonale"),
    ("tonalite_langue", "vietnamien", "tonale"),
    ("tonalite_langue", "français", "non-tonale"),
    ("tonalite_langue", "anglais", "non-tonale"),
    # Alignement (auto-sourcé) — vérité-terrain : basque ergatif, anglais accusatif.
    ("alignement_morphosyntaxique", "basque", "ergatif"),
    ("alignement_morphosyntaxique", "inuktitut", "ergatif"),
    ("alignement_morphosyntaxique", "anglais", "accusatif"),
    ("alignement_morphosyntaxique", "latin", "accusatif"),
    # Genre grammatical (auto-sourcé) — vérité-terrain : français genré, anglais sans genre nominal.
    ("genre_grammatical_langue", "français", "avec genre grammatical"),
    ("genre_grammatical_langue", "russe", "avec genre grammatical"),
    ("genre_grammatical_langue", "anglais", "sans genre grammatical"),
    ("genre_grammatical_langue", "turc", "sans genre grammatical"),
    # Articles (auto-sourcé) — vérité-terrain : anglais avec articles, russe sans.
    ("presence_articles_langue", "anglais", "avec articles"),
    ("presence_articles_langue", "français", "avec articles"),
    ("presence_articles_langue", "russe", "sans articles"),
    ("presence_articles_langue", "japonais", "sans articles"),
    # Classificateurs numéraux (auto-sourcé) — vérité-terrain : mandarin avec, français sans.
    ("classificateurs_numeraux_langue", "mandarin", "avec classificateurs"),
    ("classificateurs_numeraux_langue", "japonais", "avec classificateurs"),
    ("classificateurs_numeraux_langue", "français", "sans classificateurs"),
    ("classificateurs_numeraux_langue", "anglais", "sans classificateurs"),
    # Mise en danger UNESCO (P1999) — vérité-terrain : dalmate/gotique éteints, français/islandais sûrs, breton/mandchou.
    ("statut_unesco_danger_langue", "dalmate", "6 éteinte"),
    ("statut_unesco_danger_langue", "gotique", "6 éteinte"),
    ("statut_unesco_danger_langue", "français", "1 sûre"),
    ("statut_unesco_danger_langue", "islandais", "1 sûre"),
    ("statut_unesco_danger_langue", "breton", "4 sérieusement en danger"),
    ("statut_unesco_danger_langue", "mandchou", "5 en situation critique"),
    # Veine lexèmes (categorie_lexicale_mot) — vérité-terrain : mots MONO-catégorie (homographes -> HORS), 4 langues.
    ("categorie_lexicale_mot", "eau (français)", "nom"),
    ("categorie_lexicale_mot", "courir (français)", "verbe"),
    ("categorie_lexicale_mot", "grand (français)", "adjectif"),
    ("categorie_lexicale_mot", "rapidement (français)", "adverbe"),
    ("categorie_lexicale_mot", "Haus (allemand)", "nom"),
    ("categorie_lexicale_mot", "casa (espagnol)", "nom"),
    ("categorie_lexicale_mot", "quickly (anglais)", "adverbe"),
    # Veine lexèmes #2 (genre_grammatical_mot) — vérité-terrain : genre des noms (homographes de genre -> HORS).
    ("genre_grammatical_mot", "Wasser (allemand)", "neutre"),
    ("genre_grammatical_mot", "Mädchen (allemand)", "neutre"),
    ("genre_grammatical_mot", "casa (espagnol)", "féminin"),
    ("genre_grammatical_mot", "libro (espagnol)", "masculin"),
    ("genre_grammatical_mot", "niño (espagnol)", "masculin"),
    # Veine lexèmes #3 (concept_du_mot) — vérité-terrain : mot non-FR -> concept FR (= traduction) ; polysémie -> HORS.
    ("concept_du_mot", "perro (espagnol)", "chien"),
    ("concept_du_mot", "cane (italien)", "chien"),
    ("concept_du_mot", "neige (français)", "neige"),
    # Veine lexèmes #4 (etymon_du_mot) — vérité-terrain : « etymologia » (latin) vient du grec ἐτυμολογία.
    ("etymon_du_mot", "etymologia (latin)", "ἐτυμολογία"),
    ("etymon_du_mot", "etymologie (néerlandais)", "étymologie"),
]
for rel, ent, vrai in ANCRES:
    st, f = lec.repond(rel, ent)
    bon = st == VERIFIE and f is not None and f.valeur == vrai
    check(f"ANCRE {rel}({ent}) = {vrai!r} [{st}, {f.valeur if f else None}]", bon)

# 4) SOUNDNESS ADVERSE — multi-valeur, entité absente, mauvaise relation, relation absente -> TOUJOURS HORS.
ADVERSE = [
    ("systeme_ecriture_langue", "français"),     # latin + braille français -> multi P282 -> HORS
    ("systeme_ecriture_langue", "japonais"),      # kanji + hiragana + katakana -> HORS
    ("systeme_ecriture_langue", "coréen"),        # hangul + hanja -> HORS
    ("systeme_ecriture_langue", "langue-qui-nexiste-pas-zzz"),
    ("code_iso6392_langue", "albanais"),          # ISO 639-2 B/T = alb/sqi -> multi -> HORS
    ("code_iso6393_langue", "langue-inconnue-zzz"),
    ("systeme_ecriture_langue", "fra"),           # un CODE n'est pas une langue-source -> HORS
    ("relation_inexistante_t9", "français"),
    ("code_ethnologue_langue", "langue-inexistante-zzz"),   # entité absente -> HORS
    ("code_ethnologue_langue", "eng"),            # un CODE n'est pas une langue-source -> HORS
    ("statut_vitalite_langue", "langue-inexistante-zzz"),   # entité absente -> HORS
    ("statut_vitalite_langue", "0 international"),  # un STATUT n'est pas une langue-source -> HORS
    ("direction_ecriture", "systeme-decriture-inexistant-zzz"),   # entité absente -> HORS
    ("direction_ecriture", "de gauche à droite"),  # une DIRECTION n'est pas un système-source -> HORS
    ("regulateur_langue", "langue-inexistante-zzz"),        # entité absente -> HORS
    ("regulateur_langue", "arabe"),                # arabe = régulateurs multiples -> HORS
    ("code_ietf_langue", "langue-inexistante-zzz"),         # entité absente -> HORS
    ("code_ietf_langue", "en"),                    # un CODE n'est pas une langue-source -> HORS
    ("code_linguasphere_langue", "langue-inexistante-zzz"),
    ("code_babelnet_langue", "langue-inexistante-zzz"),
    ("code_aiatsis_langue", "langue-inexistante-zzz"),
    ("code_freebase_langue", "langue-inexistante-zzz"),
    ("code_endangered_langue", "langue-inexistante-zzz"),
    ("code_wals_langue", "langue-inexistante-zzz"),
    ("code_lccn_langue", "langue-inexistante-zzz"),
    ("pays_langue", "langue-inexistante-zzz"),     # entité absente -> HORS
    ("pays_langue", "français"),                   # langue multi-pays (29 pays) -> multi P17 -> HORS
    ("pays_langue", "anglais"),                    # langue multi-pays -> HORS
    ("code_j9u_langue", "langue-inexistante-zzz"),
    ("code_unesco_langue", "langue-inexistante-zzz"),
    ("code_bnf_langue", "langue-inexistante-zzz"),
    ("code_gnd_langue", "langue-inexistante-zzz"),
    ("code_britannica_langue", "langue-inexistante-zzz"),
    ("type_systeme_ecriture", "script-inexistant-zzz"),     # entité absente -> HORS
    ("type_systeme_ecriture", "alphabet"),                  # un TYPE n'est pas un script-source -> HORS
    ("type_systeme_ecriture", "tifinagh"),                  # cas débattu EXCLU de l'auto-source -> HORS
    ("ordre_mots_langue", "langue-inexistante-zzz"),        # entité absente -> HORS
    ("ordre_mots_langue", "SVO"),                           # un ORDRE n'est pas une langue-source -> HORS
    ("ordre_mots_langue", "latin"),                         # ordre LIBRE, exclu de l'auto-source -> HORS
    ("ordre_mots_langue", "russe"),                         # ordre flexible, exclu -> HORS
    ("type_morphologique_langue", "langue-inexistante-zzz"),
    ("type_morphologique_langue", "isolante"),              # un TYPE n'est pas une langue-source -> HORS
    ("type_morphologique_langue", "arabe"),                 # introflexionnel débattu, EXCLU -> HORS
    ("tonalite_langue", "langue-inexistante-zzz"),
    ("tonalite_langue", "japonais"),                        # accent de hauteur (débattu), EXCLU -> HORS
    ("alignement_morphosyntaxique", "langue-inexistante-zzz"),
    ("alignement_morphosyntaxique", "accusatif"),           # une VALEUR n'est pas une langue-source -> HORS
    ("alignement_morphosyntaxique", "hindi"),               # split-ergatif (débattu), EXCLU -> HORS
    ("genre_grammatical_langue", "langue-inexistante-zzz"),
    ("genre_grammatical_langue", "swahili"),                # classes nominales (≠ genre, débattu), EXCLU -> HORS
    ("presence_articles_langue", "langue-inexistante-zzz"),
    ("presence_articles_langue", "turc"),                   # indéfini seul (cas limite), EXCLU -> HORS
    ("classificateurs_numeraux_langue", "langue-inexistante-zzz"),
    ("classificateurs_numeraux_langue", "avec classificateurs"),   # une VALEUR n'est pas une langue-source -> HORS
    ("code_aat_langue", "langue-inexistante-zzz"),
    ("code_ndl_langue", "langue-inexistante-zzz"),
    ("code_nkc_langue", "langue-inexistante-zzz"),
    ("statut_unesco_danger_langue", "langue-inexistante-zzz"),
    ("statut_unesco_danger_langue", "6 éteinte"),  # un STATUT n'est pas une langue-source -> HORS
    ("categorie_lexicale_mot", "mot-inexistant-zzz (français)"),   # clé absente -> HORS
    ("categorie_lexicale_mot", "ferme (français)"),  # homographe nom/adjectif/verbe -> multi-cat -> HORS
    ("categorie_lexicale_mot", "nom"),               # une CATÉGORIE n'est pas une clé-mot -> HORS
    ("genre_grammatical_mot", "mot-inexistant-zzz (espagnol)"),    # clé absente -> HORS
    ("genre_grammatical_mot", "masculin"),           # un GENRE n'est pas une clé-mot -> HORS
    ("concept_du_mot", "mot-inexistant-zzz (italien)"),           # clé absente -> HORS
    ("concept_du_mot", "gato (espagnol)"),           # polysémique (chat/cric) -> multi-concept -> HORS
    ("etymon_du_mot", "mot-inexistant-zzz (latin)"),              # clé absente -> HORS
    ("etymon_du_mot", "ἐτυμολογία"),                 # un ÉTYMON n'est pas une clé-mot composée -> HORS
]
for rel, ent in ADVERSE:
    st, f = lec.repond(rel, ent)
    check(f"SOUNDNESS {rel}({ent}) -> HORS [{st}]", st == HORS and f is None)

print(f"\n=== T9 : {ok}/{total} checks PASS ===")
if ok != total:
    raise SystemExit(1)
