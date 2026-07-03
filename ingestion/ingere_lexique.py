"""
INGESTION LEXIQUE FR -> datasets/lecteur/*.jsonl  (OFFLINE — dump local déjà converti, ZÉRO réseau).

SOURCE : datasets/lexique_kaikki_full.jsonl (1,92 M entrées, schéma projet {mot,classe,genre,definition,
hyper,syn,ant} dérivé du Wiktionnaire FR via kaikki.org). Hôte/ressource DISTINCTS de WDQS -> tourne quand
Wikidata est en outage (vrai parallélisme de domaines).

DOMAINE OUVERT ICI : GENRE GRAMMATICAL des noms (borné par la convention linguistique française).

SOUNDNESS (FAUX=0, profil « correct-ou-absent ») :
  • classe == 'nom' ET genre ∈ {masculin, féminin} (on écarte 'masculin ou féminin', vide, etc.).
  • mono-mot, minuscule (noms communs ; on écarte expressions et noms propres au genre moins normé).
  • definition non vide = vraie entrée lexicale (écarte les stubs/artefacts de parsing).
  • FONCTIONNEL : un mot à 2 genres distincts -> rejeté (HORS), jamais un choix arbitraire.
  • SANITÉ STRUCTURELLE (valide_lecteur) : toute valeur ∈ {masculin, féminin}. ANCRES spot-check :
    15/15 justes au sondage, dont des genres-pièges (pétale/ovule/ecchymose/espèce/antre/apogée m.).
  • HORS préservé pour tout mot absent (la couverture a des trous = honnêtes, jamais de faux).

Usage : python3 ingere_lexique.py    (puis non-reg OFFLINE).
"""
from __future__ import annotations

import json
import os
import re

import lecteur as L
from ingere_wikidata import publie

DUMP = os.path.join(os.path.dirname(L._DOSSIER_DATASETS), "lexique_kaikki_full.jsonl")
GENRES = {"masculin", "féminin"}

# Définitions = formes FLÉCHIES (renvois, pas de vrai sens) -> écartées : on ne garde que les LEMMES.
# Couvre noms (pluriel/féminin…), verbes conjugués (Nème personne…, participe…, indicatif/subjonctif…)
# et renvois orthographiques. Le lemme garde sa vraie définition ; la forme fléchie est un renvoi.
_FORME_FLECHIE = (
    "pluriel de ", "singulier de ", "féminin de ", "masculin de ",
    "féminin pluriel de ", "masculin pluriel de ", "féminin singulier de ",
    "masculin singulier de ", "masculin pluriel ", "féminin pluriel ",
    "variante de ", "variante orthographique de ", "ancienne orthographe de ",
    "autre orthographe de ", "graphie ", "diminutif de ", "abréviation de ",
    "première personne ", "deuxième personne ", "troisième personne ",
    "participe passé", "participe présent", "participe ",
    "indicatif ", "subjonctif ", "impératif ", "conjugaison de ", "conjugaison du ",
)


def _est_forme_flechie(d: str) -> bool:
    dl = d.lower()
    return any(dl.startswith(p) for p in _FORME_FLECHIE)


def ingere_genre():
    print("== GENRE GRAMMATICAL DES NOMS (lexique kaikki FR, offline) ==")
    if not os.path.exists(DUMP):
        raise SystemExit(f"dump absent : {DUMP}")
    vu: dict[str, set[str]] = {}
    for ln in open(DUMP, encoding="utf-8"):
        o = json.loads(ln)
        if o.get("classe") != "nom":
            continue
        g = o.get("genre")
        if g not in GENRES:
            continue
        m = o.get("mot") or ""
        if not m or " " in m or not m[:1].islower():
            continue
        if not (o.get("definition") or "").strip():     # vraie entrée lexicale
            continue
        vu.setdefault(m, set()).add(g)
    paires = [(m, next(iter(s))) for m, s in vu.items() if len(s) == 1]
    rejets = sum(1 for s in vu.values() if len(s) > 1)
    print(f"  {len(vu)} noms distincts ; {rejets} rejetés (genre conflictuel).")
    publie("genre_grammatical", "convention",
           "Wiktionnaire FR via kaikki.org — genre grammatical du nom", paires)


def _ingere_definition(classe: str, relation: str, etiquette: str, minuscule: bool = True):
    print(f"== DÉFINITION DES {etiquette.upper()} (lexique kaikki FR, offline) ==")
    if not os.path.exists(DUMP):
        raise SystemExit(f"dump absent : {DUMP}")
    vu: dict[str, set[str]] = {}
    for ln in open(DUMP, encoding="utf-8"):
        o = json.loads(ln)
        if o.get("classe") != classe:
            continue
        m = o.get("mot") or ""
        d = (o.get("definition") or "").strip()
        if not m or " " in m or not d:
            continue
        if minuscule and not m[:1].islower():
            continue
        if sum(c.isalpha() for c in d) < 2:              # « … », ponctuation seule -> pas un sens
            continue
        if _est_forme_flechie(d):                        # forme fléchie/conjuguée -> pas un lemme
            continue
        vu.setdefault(m, set()).add(d)
    paires = [(m, next(iter(s))) for m, s in vu.items() if len(s) == 1]
    rejets = sum(1 for s in vu.values() if len(s) > 1)
    print(f"  {len(vu)} {etiquette} distincts ; {rejets} rejetés (définitions divergentes).")
    publie(relation, "convention", f"Wiktionnaire FR via kaikki.org — définition ({etiquette})", paires)


def ingere_definition():
    _ingere_definition("nom", "definition_nom", "noms")


def ingere_definition_verbe():
    _ingere_definition("verbe", "definition_verbe", "verbes")


def ingere_definition_adjectif():
    _ingere_definition("adjectif", "definition_adjectif", "adjectifs")


def ingere_definition_adverbe():
    _ingere_definition("adverbe", "definition_adverbe", "adverbes")


_RX_PLURIEL = re.compile(r"^pluriel de ([a-zàâäéèêëîïôöùûüçœæ'\-]+)\.?$", re.I)


def ingere_pluriel():
    """Extrait singulier->pluriel depuis les définitions « pluriel de X » (le mot fléchi EST le pluriel).
    Étend la relation `pluriel` de base_faits (extension sans contradiction : réconciliation amorce).
    Fonctionnel : un singulier à 2 formes plurielles (travail->travails/travaux) -> rejeté (HORS)."""
    print("== PLURIEL DES NOMS (lexique kaikki FR, offline) ==")
    if not os.path.exists(DUMP):
        raise SystemExit(f"dump absent : {DUMP}")
    pl: dict[str, set[str]] = {}
    for ln in open(DUMP, encoding="utf-8"):
        o = json.loads(ln)
        if o.get("classe") != "nom":
            continue
        m = o.get("mot") or ""
        d = (o.get("definition") or "").strip()
        if not m or " " in m or not m[:1].islower():
            continue
        mo = _RX_PLURIEL.match(d)
        if mo:
            pl.setdefault(mo.group(1), set()).add(m)        # singulier -> forme plurielle (= le mot courant)
    paires = [(s, next(iter(v))) for s, v in pl.items() if len(v) == 1]
    rejets = sum(1 for v in pl.values() if len(v) > 1)
    print(f"  {len(pl)} singuliers ; {rejets} rejetés (pluriels multiples).")
    publie("pluriel", "convention", "Wiktionnaire FR via kaikki.org — pluriel du nom", paires)


_DOMAINES = {
    "genre": ingere_genre,
    "definition": ingere_definition,
    "verbe": ingere_definition_verbe,
    "adjectif": ingere_definition_adjectif,
    "adverbe": ingere_definition_adverbe,
    "pluriel": ingere_pluriel,
}


if __name__ == "__main__":
    import sys
    cibles = sys.argv[1:] or list(_DOMAINES)
    for c in cibles:
        if c not in _DOMAINES:
            print(f"domaine inconnu : {c} (dispo : {sorted(_DOMAINES)})")
            continue
        _DOMAINES[c]()
    print("\nFait. Relancer la non-reg OFFLINE :  python3 _nonreg.py --full --jobs 6")
