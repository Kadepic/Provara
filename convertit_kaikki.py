"""
CONVERTIT_KAIKKI — pont d'un dump kaikki.org (Wiktionnaire structuré) vers le format `charge_lexique` (2026-06-18).

Réalise §6.2 du plan : brancher un lexique MASSIF avec définitions -> genus -> graphe is-a géant, pour franchir
les murs LEXICAUX (irréguliers, sens ouvert) par la DONNÉE et non par la règle. Model-free : aucune invention, on
extrait ce que le dictionnaire dit déjà.

Source : kaikki.org/frwiktionary (Wiktionnaire FRANÇAIS) -> définitions en français, écrites « genus-first »
(« chat = Mammifère carnivore félin… », « capitale = Ville où siègent… »), exactement l'insight de l'oracle.
Chaque entrée kaikki est un JSON : {word, pos, tags, senses:[{glosses:[...]}], hypernyms:[{word}], synonyms, antonyms…}.

Mapping vers {mot, classe, genre, definition, hyper, syn, ant} (cf. charge_lexique.CHAMPS) :
  - mot       = word (minusculisé)
  - classe    = pos traduit (noun->nom, verb->verbe, adj->adjectif, adv->adverbe ; autres -> ignoré)
  - genre     = tags grammaticaux (masculine/feminine ; épicène/inconnu -> None)
  - definition= 1ʳᵉ glose (français, minusculisée)
  - hyper     = GENUS de la définition (1ᵉʳ mot significatif, connectif car présent partout) ;
                à défaut, l'hyperonyme STRUCTURÉ (hypernyms[0]) — plus précis mais épars dans kaikki
  - syn / ant = liens structurés (synonyms / antonyms)

La conversion est une fonction PURE (pas de réseau) : `ingere_kaikki.py` est le CLI qui télécharge/lit un vrai dump.
"""
from __future__ import annotations

import json

# pos kaikki -> classe (None = entrée non retenue pour le lexique noyau).
_POS = {"noun": "nom", "name": "nom", "verb": "verbe", "adj": "adjectif", "adv": "adverbe"}

# Jeux de mots-outils PAR LANGUE (le MÉCANISME genus-first est agnostique ; seules ces listes changent).
# articles = mots-tête non significatifs à sauter ; relatifs = défs « Qui…/Which… » (adjectif/agent -> pas de genus) ;
# meta = cadres « Espèce de Y / A kind of Y » -> le genus est le Y après le « de/of ».
_LANG = {
    "fr": {"articles": {"un", "une", "le", "la", "les", "des", "du", "de", "d", "l", "au", "aux", "ce", "cet", "cette"},
           "relatifs": {"qui", "celui", "celle", "ceux", "celles", "ce", "se", "dont"},
           "meta": {"espèce", "sorte", "genre", "type", "variété", "variete", "forme", "pluriel", "féminin",
                    "feminin", "masculin", "singulier", "diminutif", "ensemble", "groupe"}},
    "en": {"articles": {"a", "an", "the", "of", "to", "any", "some", "each"},
           "relatifs": {"that", "which", "who", "whom", "whose"},
           "meta": {"kind", "sort", "type", "form", "member", "unit", "piece", "part", "group", "act", "action",
                    "instance", "species", "genus", "term", "terms", "set", "collection", "series", "one"}},
}


def _nettoie(mot: str) -> str:
    """Minusculise et retire la ponctuation de bord (mais garde les accents)."""
    return (mot or "").strip().lower().strip(".,;:!?()[]…'’\"")


def _premier_contenu(toks, ignore, articles):
    """1ᵉʳ mot significatif (ni article, ni adjectif-tête connu `ignore`, ni vide), alphabétique."""
    for t in toks:
        if t and t not in articles and t not in ignore and t.replace("-", "").isalpha():
            return t
    return None


def genre_grammatical(entree: dict):
    """Genre depuis les tags kaikki. Épicène (les deux) ou inconnu -> None (honnête, jamais inventé)."""
    tags = entree.get("tags") or []
    m, f = "masculine" in tags, "feminine" in tags
    if m and not f:
        return "masculin"
    if f and not m:
        return "féminin"
    return None


def genus(definition: str, ignore=frozenset(), langue="fr"):
    """Le genre is-a = mot-tête de la définition (dicos écrits genus-first), garde-fous par RÈGLE (pas une liste
    lexicale) : déf relative « Qui…/Which… » -> None honnête ; cadre méta « Espèce de Y / A kind of Y » -> Y.
    `ignore` = adjectifs-tête connus à sauter (2ᵉ passe). `langue` choisit le jeu de mots-outils."""
    L = _LANG.get(langue, _LANG["fr"])
    toks = [t for t in (_nettoie(x) for x in (definition or "").replace(",", " ").replace(";", " ").split()) if t]
    i = 0
    while i < len(toks) and toks[i] in L["articles"]:  # « A kind of… » : l'article de tête précède le mot-clé
        i += 1
    toks = toks[i:]
    if not toks:
        return None
    if toks[0] in L["relatifs"]:                      # « Qui se nourrit… / Which… » -> pas de genus nominal fiable
        return None
    if toks[0] in L["meta"]:                           # « Espèce de Y », « A kind of Y » -> genus = Y
        rest = toks[1:]
        if rest and rest[0] in L["articles"]:
            rest = rest[1:]
        return _premier_contenu(rest, ignore, L["articles"])
    return _premier_contenu(toks, ignore, L["articles"])


def convertit_entree(entree: dict, ignore=frozenset(), langue="fr", hyper_prioritaire=False):
    """Une entrée kaikki -> (mot, attrs) au format charge_lexique, ou None si non retenue.
    `hyper_prioritaire` = préférer l'hyperonyme STRUCTURÉ au genus (utile en anglais où il est riche/fiable)."""
    mot = _nettoie(entree.get("word", ""))
    classe = _POS.get(entree.get("pos"))
    if not mot or classe is None:
        return None
    gloss = ""
    for s in entree.get("senses") or []:
        gl = s.get("glosses") or []
        if gl:
            gloss = gl[0]
            break
    definition = (gloss or "").strip().lower()
    struct = next((_nettoie(h.get("word")) for h in (entree.get("hypernyms") or []) if h.get("word")), None)
    g_def = genus(definition, ignore, langue) if classe in ("nom", "verbe", "adjectif") else None
    g = (struct or g_def) if hyper_prioritaire else (g_def or struct)
    if g == mot:                      # pas d'auto-boucle « X est une sorte de X »
        g = None
    syn = [_nettoie(s.get("word")) for s in (entree.get("synonyms") or []) if s.get("word")]
    ant = [_nettoie(a.get("word")) for a in (entree.get("antonyms") or []) if a.get("word")]
    return mot, {"classe": classe, "genre": genre_grammatical(entree),
                 "definition": definition, "hyper": g, "syn": syn, "ant": ant}


def _passe(entrees, ignore, langue="fr", hyper_prioritaire=False) -> dict:
    lex = {}
    for e in entrees:
        r = convertit_entree(e, ignore, langue, hyper_prioritaire)
        if r:
            lex[r[0]] = r[1]
    return lex


def convertit(lignes, langue="fr", hyper_prioritaire=False) -> dict:
    """JSONL kaikki -> dict mot->attrs (format charge_lexique). DEUX passes : la 1ʳᵉ découvre les adjectifs ;
    la 2ᵉ les saute comme mots-tête (« Grand félin… » -> félin). Data-driven (pas de liste codée en dur).
    `langue`/`hyper_prioritaire` : voir convertit_entree. Lignes invalides ignorées."""
    entrees = []
    for ligne in lignes:
        ligne = (ligne or "").strip()
        if not ligne:
            continue
        try:
            entrees.append(json.loads(ligne))
        except json.JSONDecodeError:
            continue
    base = _passe(entrees, frozenset(), langue, hyper_prioritaire)
    adjs = frozenset(m for m, d in base.items() if d["classe"] == "adjectif")
    return _passe(entrees, adjs, langue, hyper_prioritaire) if adjs else base


def aretes_isa(lex: dict):
    """Extrait les arêtes is-a (mot -> hyper) du lexique converti, pour nourrir relation-lexicale."""
    return [(m, d["hyper"]) for m, d in lex.items() if d.get("hyper")]
