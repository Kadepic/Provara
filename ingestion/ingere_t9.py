"""
INGESTION T9 — COULOIR « LANGUE, LEXIQUE & ÉCRITURE » (catégorie `convention`).

Étend les petits sets curatés du lexique linguistique (ecriture_langue=20, code_langue=185 ISO 639-1) à l'échelle
via QLever (miroir Wikidata, hôte distinct de WDQS -> tourne pendant les outages). FAUX=0 strict : `publie`
applique `fonctionnel` (un libellé multi-valeur -> HORS) ; pour les codes, un `motif` ne garde que la forme
canonique. Aucune fabrique redéfinie : on réutilise `ingere_qlever._ingere_x_vers_entite/_ingere_x_vers_code`.

RELATIONS (noms DISJOINTS, collision-check 0) :
  • systeme_ecriture_langue (P282) — langue -> système d'écriture. Ensemble fermé RÉEL (~376 scripts pour ~1876
    langues : ratio 0.20 et fonctionnel 77% = LÉGITIMES, pas du bruit ; le scout générique, calibré « pays »,
    crie REJET mais l'échantillon est PROPRE (russe->cyrillique, judéo-arabe->alphabet hébreu, aucune date/monnaie).
    Les langues multi-scripts (serbe = cyrillique+latin) partent en HORS via `fonctionnel` -> FAUX=0 préservé.
  • code_iso6393_langue (P220) — langue -> code ISO 639-3 (3 lettres minuscules). Définitionnel, fonctionnel 99 %,
    ~7900 langues. Motif ^[a-z]{3}$ écarte tout code mal formé.
  • code_iso6392_langue (P219) — langue -> code ISO 639-2. ~400 langues, fonctionnel 95 % (les codes B/T doubles,
    ex. albanais alb/sqi, partent en HORS). Autre standard que 639-3 -> relation distincte (collision-check 0).
"""
from __future__ import annotations

import ingere_qlever as IQ

_MOTIF_ISO3 = r"[a-z]{3}"          # ISO 639-2 et 639-3 : exactement 3 lettres minuscules
_MOTIF_GLOTTOLOG = r"[a-z]{4}[0-9]{4}"   # Glottolog : 4 lettres minuscules + 4 chiffres (ex. stan1290)
# Identifiants de langue supplémentaires (motifs validés 2026-06-26 sur la distribution complète QLever) :
_MOTIF_IETF = r"[a-z]{2,3}(-[A-Za-z0-9]{1,8})*"   # BCP-47 : sous-tag langue 2-3 lettres + sous-tags (zh-HK). 'i-mingo' (tag hérité) -> HORS
_MOTIF_LINGUASPHERE = r"[0-9]{2}-[A-Z]{2,3}(-[a-z]{1,3})?"   # ex. 99-AUT-fg, 12-AAA, 42-CB
_MOTIF_BABELNET = r"[0-9]{8}[a-z]"                # ex. 02866466n (8 chiffres + 1 lettre POS)
_MOTIF_AIATSIS = r"[A-Z][0-9]+"                  # ex. D17 ; variantes A51.1/A80* -> HORS (sûr)
_MOTIF_FREEBASE = r"/m/[0-9a-z_]+"               # Freebase MID : /m/02hwy1l (100 % des valeurs)
_MOTIF_ENDANGERED = r"[0-9]+"                    # endangeredlanguages.com : identifiant numérique
_MOTIF_WALS = r"[a-z]{2,4}"                      # WALS lect code : 2-4 lettres minuscules (cpa, bzi)
_MOTIF_LCCN = r"(sh|n|no|sj)[0-9]+"             # LCSH/LCCN : préfixe sh/n/no/sj + chiffres
_MOTIF_J9U = r"[0-9]{10,}"                       # J9U (Bibliothèque nationale d'Israël) : long numérique
_MOTIF_UNESCO = r"[0-9]+"                        # UNESCO Atlas of Languages in Danger : identifiant numérique
_MOTIF_BNF = r"[0-9]{8,9}[a-z]?"                # BnF : 8-9 chiffres + lettre de contrôle optionnelle
_MOTIF_GND = r"[0-9]+(X|-[0-9X])?"             # GND (Deutsche Nationalbibliothek) : chiffres + contrôle
_MOTIF_BRITANNICA = r"topic/[A-Za-z0-9%-]+"     # Britannica : topic/Zulu-language (entrées 'art/...' -> HORS)
_MOTIF_AAT = r"300[0-9]+"                        # Getty AAT : identifiant numérique préfixé 300
_MOTIF_NDL = r"[0-9]+"                           # NDL (Diète du Japon) : identifiant numérique
_MOTIF_NKC = r"[a-z]{2}[0-9]+"                  # NKC (Bibliothèque nationale tchèque) : 2 lettres + chiffres


def ingere_systeme_ecriture():
    IQ._ingere_x_vers_entite(
        "systeme_ecriture_langue", "P282", "convention",
        "Wikidata/QLever — système d'écriture de la langue P282 (ensemble fermé de scripts ; multi-scripts -> HORS)",
        classe_qid="Q34770")


def ingere_code_iso6393():
    IQ._ingere_x_vers_code(
        "code_iso6393_langue", "Q34770", "P220",
        "CODE ISO 639-3 DE LA LANGUE", motif=_MOTIF_ISO3)


def ingere_code_iso6392():
    IQ._ingere_x_vers_code(
        "code_iso6392_langue", "Q34770", "P219",
        "CODE ISO 639-2 DE LA LANGUE", motif=_MOTIF_ISO3)


def ingere_code_glottolog():
    # Glottolog : identifiant définitionnel d'une langue (~8000 langues, fonctionnel 98 %). Une langue à 2 codes
    # (rare) -> HORS via `fonctionnel`. Motif ^[a-z]{4}[0-9]{4}$ écarte tout identifiant non canonique.
    IQ._ingere_x_vers_code(
        "code_glottolog_langue", "Q34770", "P1394",
        "CODE GLOTTOLOG DE LA LANGUE", motif=_MOTIF_GLOTTOLOG)


def ingere_code_ethnologue():
    # Ethnologue (SIL) : identifiant de langue sur ethnologue.com (P1627). Scout 2026-06-26 : 5451 langues,
    # fonctionnel 99 %, format 100 % [a-z]{3} (aucune valeur hors-motif). Standard DISTINCT d'ISO 639-3 (la
    # valeur peut différer ; relation au nom distinct, collision-check 0). Les ~73 langues multi-codes partent
    # en HORS via `fonctionnel`. Motif ^[a-z]{3}$ écarte tout identifiant non canonique -> FAUX=0.
    IQ._ingere_x_vers_code(
        "code_ethnologue_langue", "Q34770", "P1627",
        "CODE ETHNOLOGUE DE LA LANGUE", motif=_MOTIF_ISO3)


def ingere_statut_vitalite():
    # Statut de vitalité Ethnologue/EGIDS (P3823) : échelle bornée RÉELLE de la transmission intergénérationnelle
    # (scout 2026-06-26 : 16 statuts distincts FR propres -- « 6a vivace », « 6b menacé », « 10 éteint »,
    # « 1 national »... -- sur 5361 langues, fonctionnel 99 %). Ensemble fermé -> _ingere_x_vers_entite récupère
    # le libellé FR du statut. `fonctionnel` rejette toute langue à statuts multiples -> HORS. FAUX=0.
    IQ._ingere_x_vers_entite(
        "statut_vitalite_langue", "P3823", "convention",
        "Wikidata/QLever — statut de vitalité Ethnologue/EGIDS P3823 (échelle fermée ; multi-valeur -> HORS)",
        classe_qid="Q34770")


def ingere_code_ietf():
    # IETF / BCP-47 (P305) : tag de langue standard du web/Unicode. Scout 2026-06-26 : 5631 langues, fonctionnel
    # 99 %, 6824/6825 valeurs au format BCP-47 (seul 'i-mingo', tag hérité irrégulier, -> HORS via motif). FAUX=0.
    IQ._ingere_x_vers_code(
        "code_ietf_langue", "Q34770", "P305",
        "CODE IETF/BCP-47 DE LA LANGUE", motif=_MOTIF_IETF)


def ingere_code_linguasphere():
    # Linguasphere (P1396) : identifiant de l'Observatoire linguistique. 270 langues, fonctionnel 100 %,
    # format \d\d-AAA(-aa) (ex. 99-AUT-fg). Motif écarte tout code non canonique -> HORS.
    IQ._ingere_x_vers_code(
        "code_linguasphere_langue", "Q34770", "P1396",
        "CODE LINGUASPHERE DE LA LANGUE", motif=_MOTIF_LINGUASPHERE)


def ingere_code_babelnet():
    # BabelNet (P2581) : identifiant du synset BabelNet de la langue. 336 langues, fonctionnel 100 %,
    # format 8 chiffres + lettre (ex. 02866466n). Motif strict -> FAUX=0.
    IQ._ingere_x_vers_code(
        "code_babelnet_langue", "Q34770", "P2581",
        "CODE BABELNET DE LA LANGUE", motif=_MOTIF_BABELNET)


def ingere_code_aiatsis():
    # AIATSIS (P1252) : identifiant des langues aborigènes d'Australie (AUSTLANG). 374 langues, fonctionnel 93 %
    # (28 multi -> HORS), format lettre+chiffres (ex. D17). Variantes A51.1/A80* -> HORS via motif. FAUX=0.
    IQ._ingere_x_vers_code(
        "code_aiatsis_langue", "Q34770", "P1252",
        "CODE AIATSIS DE LA LANGUE", motif=_MOTIF_AIATSIS)


def ingere_code_freebase():
    # Freebase MID (P646) : identifiant historique Google Freebase. 5237 langues, fonctionnel 98 %, format /m/...
    # à 100 %. Freebase est fermé (2016) mais le MID reste un fait borné vérifiable. Motif -> FAUX=0.
    IQ._ingere_x_vers_code(
        "code_freebase_langue", "Q34770", "P646",
        "CODE FREEBASE (MID) DE LA LANGUE", motif=_MOTIF_FREEBASE)


def ingere_code_endangered():
    # endangeredlanguages.com (P2192) : identifiant du Catalogue of Endangered Languages. 2834 langues,
    # fonctionnel 98 %, identifiant numérique 100 %. Motif strict -> FAUX=0.
    IQ._ingere_x_vers_code(
        "code_endangered_langue", "Q34770", "P2192",
        "CODE ENDANGEREDLANGUAGES DE LA LANGUE", motif=_MOTIF_ENDANGERED)


def ingere_code_wals():
    # WALS lect code (P1466) : identifiant du World Atlas of Language Structures. 1914 langues, fonctionnel 98 %,
    # format 2-4 lettres minuscules 100 %. (P5036 « WALS » donnait 0 ; P1466 est le bon.) Motif -> FAUX=0.
    IQ._ingere_x_vers_code(
        "code_wals_langue", "Q34770", "P1466",
        "CODE WALS DE LA LANGUE", motif=_MOTIF_WALS)


def ingere_code_lccn():
    # LCSH/LCCN (P244) : identifiant Library of Congress de la langue (vedette-matière). 598 langues,
    # fonctionnel 99 %, préfixe sh/n/no/sj + chiffres 100 %. Motif -> FAUX=0.
    IQ._ingere_x_vers_code(
        "code_lccn_langue", "Q34770", "P244",
        "CODE LCCN/LCSH DE LA LANGUE", motif=_MOTIF_LCCN)


def ingere_code_j9u():
    # J9U (P8189) : identifiant d'autorité de la Bibliothèque nationale d'Israël. 2053 langues, fonctionnel 99 %,
    # long numérique 100 %. Motif -> FAUX=0.
    IQ._ingere_x_vers_code(
        "code_j9u_langue", "Q34770", "P8189",
        "CODE J9U (BIBLIOTHÈQUE NATIONALE D'ISRAËL) DE LA LANGUE", motif=_MOTIF_J9U)


def ingere_code_unesco():
    # UNESCO Atlas of the World's Languages in Danger (P2355) : identifiant. 1803 langues, fonctionnel 91 %,
    # identifiant numérique 100 %. Motif -> FAUX=0.
    IQ._ingere_x_vers_code(
        "code_unesco_langue", "Q34770", "P2355",
        "CODE UNESCO ATLAS DES LANGUES EN DANGER DE LA LANGUE", motif=_MOTIF_UNESCO)


def ingere_code_bnf():
    # BnF (P268) : identifiant de la Bibliothèque nationale de France. 463 langues, fonctionnel 100 %,
    # 8-9 chiffres + lettre de contrôle. Motif -> FAUX=0.
    IQ._ingere_x_vers_code(
        "code_bnf_langue", "Q34770", "P268",
        "CODE BNF DE LA LANGUE", motif=_MOTIF_BNF)


def ingere_code_gnd():
    # GND (P227) : identifiant d'autorité de la Deutsche Nationalbibliothek. 247 langues, fonctionnel 99 %.
    # Motif (chiffres + caractère de contrôle X ou -n) -> FAUX=0.
    IQ._ingere_x_vers_code(
        "code_gnd_langue", "Q34770", "P227",
        "CODE GND DE LA LANGUE", motif=_MOTIF_GND)


def ingere_code_britannica():
    # Encyclopædia Britannica (P1417) : identifiant d'article. 357 langues, fonctionnel 97 %, forme topic/Slug.
    # Les entrées non-'topic/' (ex. art/...) -> HORS via motif. FAUX=0.
    IQ._ingere_x_vers_code(
        "code_britannica_langue", "Q34770", "P1417",
        "CODE BRITANNICA DE LA LANGUE", motif=_MOTIF_BRITANNICA)


def ingere_code_aat():
    # Getty AAT (P1014) : Art & Architecture Thesaurus. 1100 langues, fonctionnel 99 %, format 300+chiffres 100 %.
    IQ._ingere_x_vers_code(
        "code_aat_langue", "Q34770", "P1014", "CODE GETTY AAT DE LA LANGUE", motif=_MOTIF_AAT)


def ingere_code_ndl():
    # NDL (P349) : Bibliothèque de la Diète nationale du Japon. 85 langues, fonctionnel 100 %, numérique.
    IQ._ingere_x_vers_code(
        "code_ndl_langue", "Q34770", "P349", "CODE NDL (JAPON) DE LA LANGUE", motif=_MOTIF_NDL)


def ingere_code_nkc():
    # NKC (P691) : Bibliothèque nationale tchèque. 176 langues, fonctionnel 100 %, 2 lettres + chiffres.
    IQ._ingere_x_vers_code(
        "code_nkc_langue", "Q34770", "P691", "CODE NKC (TCHÉQUIE) DE LA LANGUE", motif=_MOTIF_NKC)


def ingere_statut_unesco_danger():
    # Degré de mise en danger UNESCO (P1999) : échelle fermée RÉELLE de l'Atlas UNESCO des langues en danger
    # (scout 2026-06-26 : 6 niveaux « 1 sûre »…« 6 éteinte », 1956 langues, fonctionnel 98 %). DISTINCT de l'EGIDS
    # (statut_vitalite_langue/P3823). `fonctionnel` -> multi-valeur HORS. Ensemble fermé.
    IQ._ingere_x_vers_entite(
        "statut_unesco_danger_langue", "P1999", "convention",
        "Wikidata/QLever — degré de mise en danger UNESCO P1999 (échelle fermée 6 niveaux ; multi -> HORS)",
        classe_qid="Q34770")


def ingere_pays_langue():
    # Pays de la langue (P17, classe Q34770) : valeur = État (vocab fermé d'entités-pays). Scout 2026-06-26 :
    # 5951 langues, fonctionnel 87 % -> les langues transfrontalières (plusieurs P17) partent en HORS, ~5174
    # langues mono-pays conservées (langues locales). Échantillon PROPRE (uniquement des pays, ≠ P2341 mêlé).
    IQ._ingere_x_vers_entite(
        "pays_langue", "P17", "convention",
        "Wikidata/QLever — pays de la langue P17 (vocab fermé pays ; langue multi-pays -> HORS)",
        classe_qid="Q34770")


def ingere_direction_ecriture():
    # Direction d'écriture d'un SYSTÈME D'ÉCRITURE (P1406, classe Q8192) : ensemble fermé RÉEL (scout 2026-06-26 :
    # 58 systèmes, 7 directions distinctes -- « de gauche à droite », « de droite à gauche », boustrophédon... --
    # fonctionnel 84 %). Entité-source = système d'écriture (couloir ÉCRITURE). `fonctionnel` rejette les multi -> HORS.
    IQ._ingere_x_vers_entite(
        "direction_ecriture", "P1406", "convention",
        "Wikidata/QLever — direction d'écriture du système d'écriture P1406 (ensemble fermé ; multi -> HORS)",
        classe_qid="Q8192")


def ingere_regulateur_langue():
    # Régulateur/académie d'une langue (P1018, classe Q34770) : vocab ouvert d'organismes (Académie française...).
    # Scout 2026-06-26 : 53 langues, fonctionnel 79 % -> les langues à régulateurs multiples (arabe, biélorusse...)
    # partent en HORS, ~42 faits mono-régulateur conservés. `fonctionnel` garantit FAUX=0.
    IQ._ingere_x_vers_entite(
        "regulateur_langue", "P1018", "convention",
        "Wikidata/QLever — régulateur/académie de la langue P1018 (multi-régulateur -> HORS)",
        classe_qid="Q34770")


_DOMAINES = {
    "ecriture": ingere_systeme_ecriture,
    "iso3": ingere_code_iso6393,
    "iso2": ingere_code_iso6392,
    "glottolog": ingere_code_glottolog,
    "ethnologue": ingere_code_ethnologue,
    "vitalite": ingere_statut_vitalite,
    "direction": ingere_direction_ecriture,
    "regulateur": ingere_regulateur_langue,
    "ietf": ingere_code_ietf,
    "linguasphere": ingere_code_linguasphere,
    "babelnet": ingere_code_babelnet,
    "aiatsis": ingere_code_aiatsis,
    "freebase": ingere_code_freebase,
    "endangered": ingere_code_endangered,
    "wals": ingere_code_wals,
    "lccn": ingere_code_lccn,
    "pays": ingere_pays_langue,
    "j9u": ingere_code_j9u,
    "unesco": ingere_code_unesco,
    "bnf": ingere_code_bnf,
    "gnd": ingere_code_gnd,
    "britannica": ingere_code_britannica,
    "aat": ingere_code_aat,
    "ndl": ingere_code_ndl,
    "nkc": ingere_code_nkc,
    "unesco_danger": ingere_statut_unesco_danger,
}


if __name__ == "__main__":
    import sys
    cibles = sys.argv[1:] or list(_DOMAINES)
    for c in cibles:
        if c not in _DOMAINES:
            print(f"domaine inconnu : {c} (dispo : {sorted(_DOMAINES)})")
            continue
        _DOMAINES[c]()
    print("\nFait.")
