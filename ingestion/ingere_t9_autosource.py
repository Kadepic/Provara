"""
AUTO-SOURCING T9 — TYPOLOGIE DES SYSTÈMES D'ÉCRITURE -> datasets/lecteur/type_systeme_ecriture.jsonl (OFFLINE).

POURQUOI L'AUTO-SOURCING : la source QLever est BRUITÉE ici (P31 des scripts = fonctionnel 40 %, types
hétérogènes mêlant « orthographe », « système de romanisation », « langue dans un système d'écriture »...).
Conformément à la directive (cf. mémoire feedback-claude-peut-etre-source) : quand la source ne convient pas et
que je connais le fait avec CERTITUDE, je deviens la source — sous discipline FAUX=0 intacte.

SOURCE : classification typologique de référence des écritures (Daniels & Bright, *The World's Writing Systems*).
Faits STABLES et CONSENSUELS pour les grands scripts. On reste sur la catégorie typologique INCONTESTÉE.

FAUX=0 — discipline :
  * UNIQUEMENT des scripts à classification NON CONTESTÉE, avec le libellé EXACT déjà présent dans nos données
    (valeurs réelles de systeme_ecriture_langue) -> clés canoniques, pas inventées.
  * On ÉCARTE tout cas débattu/mixte : tifinagh (abjad vs alphabet selon époque), cunéiforme (logo-syllabique),
    syllabaire autochtone canadien (structurellement abugida), hangul (alphabet featural discuté), SignWriting.
  * 5 types fermés : alphabet (voyelles+consonnes notées), abjad (consonantique), abugida/alphasyllabaire
    (consonne à voyelle inhérente), syllabaire, logographique. script -> UN type = fonctionnel.

Usage : python3 ingere_t9_autosource.py    (puis valide_lecteur_t9.py OFFLINE).
"""
from __future__ import annotations

from ingere_wikidata import publie

# Libellés EXACTS lus dans datasets/lecteur/systeme_ecriture_langue.jsonl (clés canoniques réelles).
_PAR_TYPE = {
    "alphabet": ["écriture latine", "écriture cyrillique", "alphabet grec", "alphabet arménien",
                 "écriture copte", "alphabet étrusque", "écriture gotique"],
    "abjad": ["alphabet arabe", "écriture arabe", "alphabet perso-arabe", "écriture hébraïque",
              "alphabet hébreu", "écriture phénicienne", "écriture nabatéenne", "écriture samaritaine"],
    "abugida": ["devanagari", "alphasyllabaire guèze", "écriture tibétaine", "alphasyllabaire odia",
                "alphasyllabaire birman", "écriture birmane", "écriture thaïe", "alphasyllabaire bengali",
                "alphasyllabaire télougou", "écriture laotienne", "écriture khmère", "brahmi",
                "écriture assamaise"],
    "syllabaire": ["hiragana"],
    "logographique": ["sinogrammes", "sinogrammes simplifiés", "kanjis"],
}

SRC = "Claude (connaissances entraînées) — typologie des systèmes d'écriture (réf. Daniels & Bright), faits certains"

# ---------------------------------------------------------------------------------------------------------------
# ORDRE DES MOTS DE BASE (typologie syntaxique). Closed-set des 3 ordres dominants COURANTS {SVO, SOV, VSO}.
# FAUX=0 : UNIQUEMENT les langues à ordre dominant INCONTESTÉ. On ÉCARTE les langues à ordre LIBRE/non dominant
# (latin, russe, hongrois, finnois = flexibles), l'allemand (V2, débattu), l'arabe et l'hébreu MODERNES (SVO vs
# VSO selon registre), le tagalog (verb-initial débattu). Réf. WALS feature 81A, consensuelle pour ces langues.
_PAR_ORDRE = {
    "SVO": ["anglais", "français", "espagnol", "italien", "portugais", "mandarin", "vietnamien", "thaï",
            "indonésien", "malais", "swahili", "haoussa", "yoruba", "zoulou",
            "roumain", "catalan", "galicien", "occitan"],   # +ext romanes SVO (germaniques V2 / slaves flexibles exclus)
    "SOV": ["japonais", "coréen", "turc", "hindi", "ourdou", "bengali", "persan", "pendjabi", "tamoul",
            "télougou", "kannada", "mongol", "birman", "tibétain", "basque", "géorgien", "arménien",
            "pachto", "amharique", "tigrinya"],
    "VSO": ["irlandais", "gallois", "gaélique écossais"],
}

SRC_ORDRE = "Claude (connaissances entraînées) — ordre des mots de base (réf. WALS 81A, langues à ordre incontesté)"

# ---------------------------------------------------------------------------------------------------------------
# TYPE MORPHOLOGIQUE. La morphologie est un CONTINUUM -> on ne prend QUE les PROTOTYPES incontestés de chaque type.
# Exclus : l'anglais/français (mixtes), l'arabe (introflexionnel/templatique débattu), le japonais (entre les deux).
_PAR_MORPHO = {
    "isolante": ["mandarin", "cantonais", "vietnamien", "thaï"],
    "agglutinante": ["turc", "finnois", "hongrois", "japonais", "coréen", "swahili", "basque", "mongol", "tamoul"],
    "flexionnelle": ["latin", "sanskrit", "grec ancien", "russe", "polonais", "allemand",
                     "grec moderne", "ukrainien", "slovaque", "serbe", "croate"],   # +ext slaves/grec fusionnels
    "polysynthétique": ["inuktitut", "groenlandais", "mohawk", "nahuatl"],
}
SRC_MORPHO = "Claude (connaissances entraînées) — type morphologique (prototypes typologiques incontestés)"

# TONALITÉ (binaire). Prototypes clairs uniquement. Exclus : japonais/suédois/norvégien (accent de hauteur, ni
# vraiment tonal ni atonal -> débattu).
_PAR_TON = {
    "tonale": ["mandarin", "cantonais", "vietnamien", "thaï", "lao", "birman", "yoruba", "igbo", "zoulou",
               "haoussa", "pendjabi"],
    "non-tonale": ["français", "anglais", "espagnol", "allemand", "russe", "arabe", "turc", "hindi", "italien",
                   "portugais", "finnois", "hongrois",
                   "néerlandais", "grec moderne", "roumain", "catalan", "galicien", "occitan", "ukrainien",
                   "slovaque", "danois"],   # +ext (serbe/croate/suédois/norvégien = accent tonal -> exclus)
}
SRC_TON = "Claude (connaissances entraînées) — présence d'un système tonal (prototypes clairs ; accent de hauteur exclu)"

# ALIGNEMENT MORPHOSYNTAXIQUE. Closed-set {accusatif, ergatif}. On ÉCARTE les langues à alignement SPLIT (hindi/
# géorgien/tibétain = ergatif partiel) -> seuls les alignements DOMINANTS non-split. Ergatif pur = très rare.
_PAR_ALIGN = {
    "accusatif": ["anglais", "français", "espagnol", "italien", "portugais", "allemand", "latin", "grec ancien",
                  "russe", "polonais", "japonais", "turc", "finnois", "hongrois", "mandarin",
                  "néerlandais", "grec moderne", "roumain", "catalan", "galicien", "occitan", "ukrainien",
                  "slovaque", "serbe", "croate", "danois"],   # +ext (toutes accusatives non-split)
    "ergatif": ["basque", "inuktitut", "groenlandais"],
}
SRC_ALIGN = "Claude (connaissances entraînées) — alignement morphosyntaxique dominant (langues non-split incontestées)"

# GENRE GRAMMATICAL (binaire). « avec » = système de genre/classe à accord ; « sans » = pas de genre nominal. On
# ÉCARTE le swahili (classes nominales = système distinct débattu comme « genre »).
_PAR_GENRE = {
    "avec genre grammatical": ["français", "espagnol", "italien", "portugais", "allemand", "russe", "polonais",
                               "arabe", "hébreu", "hindi", "latin", "grec ancien",
                               "néerlandais", "grec moderne", "roumain", "catalan", "galicien", "occitan",
                               "ukrainien", "slovaque", "serbe", "croate", "danois"],   # +ext (toutes à genre)
    "sans genre grammatical": ["anglais", "turc", "finnois", "hongrois", "japonais", "coréen", "mandarin",
                               "vietnamien", "persan", "basque"],
}
SRC_GENRE = "Claude (connaissances entraînées) — présence d'un genre grammatical (prototypes ; classes nominales exclues)"

# PRÉSENCE D'ARTICLES (binaire). Prototypes nets. Exclus : turc (indéfini seul), bulgare/macédonien (article postposé,
# atypique parmi les slaves) -> on ne garde que les cas tranchés.
_PAR_ARTICLE = {
    "avec articles": ["anglais", "français", "espagnol", "italien", "portugais", "allemand", "grec ancien",
                      "arabe", "hébreu", "néerlandais", "hongrois",
                      "grec moderne", "roumain", "catalan", "galicien", "occitan", "danois"],   # +ext
    "sans articles": ["russe", "polonais", "tchèque", "latin", "japonais", "coréen", "mandarin", "finnois",
                      "hindi",
                      "ukrainien", "slovaque", "serbe", "croate"],   # +ext slaves sans articles
}
SRC_ARTICLE = "Claude (connaissances entraînées) — présence d'un système d'articles (prototypes nets)"

# CLASSIFICATEURS NUMÉRAUX (binaire). Est-asiatique = avec ; européen/sémitique = sans. Prototypes consensuels.
_PAR_CLASSIF = {
    "avec classificateurs": ["mandarin", "cantonais", "japonais", "coréen", "vietnamien", "thaï", "birman",
                             "indonésien", "malais"],
    "sans classificateurs": ["français", "anglais", "espagnol", "allemand", "russe", "arabe", "turc", "hindi",
                             "italien", "portugais", "finnois", "hongrois",
                             "néerlandais", "grec moderne", "roumain", "catalan", "galicien", "occitan",
                             "ukrainien", "slovaque", "serbe", "croate", "danois"],   # +ext
}
SRC_CLASSIF = "Claude (connaissances entraînées) — présence de classificateurs numéraux (prototypes consensuels)"

# EXTENSION 2 (2026-06-26, charge basse) : langues européennes supplémentaires, table PAR-LANGUE (1 ligne = audit).
# Cellule présente = CERTAINE ; cellule OMISE = doute -> exclue (FAUX=0). Exclusions appliquées : suédois/norvégien/
# slovène/lituanien/letton ont un ACCENT TONAL -> PAS dans la tonalité ; toutes V2/flexibles -> PAS dans l'ordre ;
# bulgare/macédonien analytiques -> PAS dans la morphologie. bulgare/macédonien = SEULS slaves à article (postposé).
_EXT2 = {
    "islandais":  {"morpho": "flexionnelle", "ton": "non-tonale", "align": "accusatif",
                   "genre": "avec genre grammatical", "article": "avec articles", "classif": "sans classificateurs"},
    "suédois":    {"align": "accusatif", "genre": "avec genre grammatical",
                   "article": "avec articles", "classif": "sans classificateurs"},
    "norvégien":  {"align": "accusatif", "genre": "avec genre grammatical",
                   "article": "avec articles", "classif": "sans classificateurs"},
    "slovène":    {"morpho": "flexionnelle", "align": "accusatif", "genre": "avec genre grammatical",
                   "article": "sans articles", "classif": "sans classificateurs"},
    "bulgare":    {"ton": "non-tonale", "align": "accusatif", "genre": "avec genre grammatical",
                   "article": "avec articles", "classif": "sans classificateurs"},
    "macédonien": {"ton": "non-tonale", "align": "accusatif", "genre": "avec genre grammatical",
                   "article": "avec articles", "classif": "sans classificateurs"},
    "estonien":   {"morpho": "agglutinante", "ton": "non-tonale", "align": "accusatif",
                   "genre": "sans genre grammatical", "article": "sans articles", "classif": "sans classificateurs"},
    "lituanien":  {"morpho": "flexionnelle", "align": "accusatif", "genre": "avec genre grammatical",
                   "article": "sans articles", "classif": "sans classificateurs"},
    "letton":     {"morpho": "flexionnelle", "align": "accusatif", "genre": "avec genre grammatical",
                   "article": "sans articles", "classif": "sans classificateurs"},
}
_DIM = {"morpho": _PAR_MORPHO, "ton": _PAR_TON, "align": _PAR_ALIGN,
        "genre": _PAR_GENRE, "article": _PAR_ARTICLE, "classif": _PAR_CLASSIF}
for _lg, _cells in _EXT2.items():
    for _dim, _val in _cells.items():
        _lst = _DIM[_dim].setdefault(_val, [])
        if _lg not in _lst:
            _lst.append(_lg)


def ingere():
    paires = [(script, typ) for typ, scripts in _PAR_TYPE.items() for script in scripts]
    print(f"== AUTO-SOURCE — système d'écriture -> type ({len(paires)} scripts, {len(_PAR_TYPE)} types) ==")
    publie("type_systeme_ecriture", "convention", SRC, paires)


def ingere_ordre():
    paires = [(lg, ordre) for ordre, langues in _PAR_ORDRE.items() for lg in langues]
    print(f"== AUTO-SOURCE — langue -> ordre des mots ({len(paires)} langues, {len(_PAR_ORDRE)} ordres) ==")
    publie("ordre_mots_langue", "convention", SRC_ORDRE, paires)


def ingere_morpho():
    paires = [(lg, m) for m, langues in _PAR_MORPHO.items() for lg in langues]
    print(f"== AUTO-SOURCE — langue -> type morphologique ({len(paires)} langues, {len(_PAR_MORPHO)} types) ==")
    publie("type_morphologique_langue", "convention", SRC_MORPHO, paires)


def ingere_ton():
    paires = [(lg, t) for t, langues in _PAR_TON.items() for lg in langues]
    print(f"== AUTO-SOURCE — langue -> tonalité ({len(paires)} langues) ==")
    publie("tonalite_langue", "convention", SRC_TON, paires)


def ingere_align():
    paires = [(lg, a) for a, langues in _PAR_ALIGN.items() for lg in langues]
    print(f"== AUTO-SOURCE — langue -> alignement ({len(paires)} langues) ==")
    publie("alignement_morphosyntaxique", "convention", SRC_ALIGN, paires)


def ingere_genre():
    paires = [(lg, g) for g, langues in _PAR_GENRE.items() for lg in langues]
    print(f"== AUTO-SOURCE — langue -> genre grammatical ({len(paires)} langues) ==")
    publie("genre_grammatical_langue", "convention", SRC_GENRE, paires)


def ingere_article():
    paires = [(lg, a) for a, langues in _PAR_ARTICLE.items() for lg in langues]
    print(f"== AUTO-SOURCE — langue -> articles ({len(paires)} langues) ==")
    publie("presence_articles_langue", "convention", SRC_ARTICLE, paires)


def ingere_classif():
    paires = [(lg, c) for c, langues in _PAR_CLASSIF.items() for lg in langues]
    print(f"== AUTO-SOURCE — langue -> classificateurs ({len(paires)} langues) ==")
    publie("classificateurs_numeraux_langue", "convention", SRC_CLASSIF, paires)


_CIBLES = {"type": ingere, "ordre": ingere_ordre, "morpho": ingere_morpho, "ton": ingere_ton,
           "align": ingere_align, "genre": ingere_genre, "article": ingere_article, "classif": ingere_classif}

if __name__ == "__main__":
    import sys
    for c in (sys.argv[1:] or list(_CIBLES)):
        if c in _CIBLES:
            _CIBLES[c]()
        else:
            print(f"cible inconnue : {c} (dispo : {sorted(_CIBLES)})")
