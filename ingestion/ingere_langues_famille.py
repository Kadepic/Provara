"""
INGESTION LINGUISTIQUE — langue -> famille linguistique -> datasets/lecteur/famille_langue.jsonl (OFFLINE).

SOURCE : classification des langues de référence (familles bien établies). Faits STABLES et CERTAINS
pour les grandes langues. On reste sur la GRANDE famille (ou la branche bien établie), pas les
sous-groupes contestés.

FAUX=0 — discipline :
  * UNIQUEMENT des langues à rattachement NON CONTESTÉ.
  * On ÉCARTE les cas débattus (japonais/coréen = familles isolées discutées ; basque = isolat -> exclus).
  * Valeur = famille/branche : romane, germanique, slave, celtique, hellénique, indo-aryenne,
    iranienne, baltique, sémitique, turcique, sino-tibétaine, ouralienne, bantoue, dravidienne, austronésienne.
  * langue -> UNE famille = fonctionnel. Clés = noms FR minuscules.

Usage : python3 ingere_langues_famille.py    (puis non-reg OFFLINE).
"""
from __future__ import annotations

from ingere_wikidata import publie

_PAR_FAMILLE = {
    "romane": ["français", "espagnol", "italien", "portugais", "roumain", "catalan", "occitan",
               "galicien", "corse", "sarde", "wallon"],
    "germanique": ["anglais", "allemand", "néerlandais", "suédois", "danois", "norvégien",
                   "islandais", "afrikaans", "flamand", "luxembourgeois", "yiddish"],
    "slave": ["russe", "polonais", "tchèque", "slovaque", "ukrainien", "biélorusse", "bulgare",
              "serbe", "croate", "slovène", "macédonien"],
    "celtique": ["irlandais", "gallois", "breton", "écossais gaélique", "gaélique"],
    "hellénique": ["grec"],
    "indo-aryenne": ["hindi", "ourdou", "bengali", "pendjabi", "marathi", "gujarati", "népalais",
                     "cinghalais"],
    "iranienne": ["persan", "kurde", "pachto", "tadjik"],
    "baltique": ["lituanien", "letton"],
    "sémitique": ["arabe", "hébreu", "amharique", "araméen", "maltais"],
    "turcique": ["turc", "azéri", "ouzbek", "kazakh", "turkmène", "kirghize"],
    "sino-tibétaine": ["mandarin", "cantonais", "tibétain", "birman"],
    "ouralienne": ["finnois", "hongrois", "estonien"],
    "dravidienne": ["tamoul", "télougou", "kannada", "malayalam"],
    "austronésienne": ["indonésien", "malais", "tagalog", "malgache", "hawaïen", "maori"],
}

SRC = "classification linguistique de référence (famille) — faits certains"


def ingere():
    paires = [(lg, fam) for fam, langues in _PAR_FAMILLE.items() for lg in langues]
    print(f"== LINGUISTIQUE — langue -> famille ({len(paires)} langues, {len(_PAR_FAMILLE)} familles) ==")
    publie("famille_langue", "convention", SRC, paires)


if __name__ == "__main__":
    ingere()
