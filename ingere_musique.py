"""
INGESTION MUSIQUE — instrument -> famille -> datasets/lecteur/famille_instrument.jsonl  (OFFLINE).

SOURCE : classification pédagogique de référence des instruments (familles enseignées : cordes, bois,
cuivres, percussions, claviers). Faits STABLES et CERTAINS au sein de cette taxonomie standard.

FAUX=0 — discipline :
  * Familles = {cordes, bois, cuivres, percussions, claviers} (taxonomie pédagogique FR usuelle).
  * Le saxophone = BOIS (classé par l'anche, pas le métal) — point standard non contesté.
  * Le piano/clavecin/orgue = CLAVIERS (réponse pédagogique standard FR).
  * On ÉCARTE les cas réellement débattus (accordéon = anche libre ; instruments électroniques).
  * instrument -> UNE famille = fonctionnel. Clés = noms FR minuscules.

Usage : python3 ingere_musique.py    (puis non-reg OFFLINE).
"""
from __future__ import annotations

from ingere_wikidata import publie

_PAR_FAMILLE = {
    "cordes": ["violon", "alto", "violoncelle", "contrebasse", "harpe", "guitare", "mandoline",
               "banjo", "luth", "ukulélé", "violon alto", "balalaïka"],
    "bois": ["flûte", "flûte à bec", "piccolo", "clarinette", "hautbois", "basson", "saxophone",
             "cor anglais", "fifre"],
    "cuivres": ["trompette", "trombone", "cor", "tuba", "cornet", "bugle", "clairon", "soubassophone"],
    "percussions": ["tambour", "batterie", "timbale", "xylophone", "cymbale", "triangle", "maracas",
                    "tambourin", "gong", "marimba", "vibraphone", "djembé", "castagnette", "tam-tam",
                    "glockenspiel", "caisse claire", "grosse caisse"],
    "claviers": ["piano", "orgue", "clavecin", "célesta", "épinette"],
}

SRC = "classification pédagogique des instruments (famille) — faits certains"


def ingere():
    paires = [(i, fam) for fam, instrs in _PAR_FAMILLE.items() for i in instrs]
    print(f"== MUSIQUE — instrument -> famille ({len(paires)} instruments, {len(_PAR_FAMILLE)} familles) ==")
    publie("famille_instrument", "convention", SRC, paires)


if __name__ == "__main__":
    ingere()
