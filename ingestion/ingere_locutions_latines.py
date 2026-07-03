"""
INGESTION LATIN — locution latine -> sens en français  -> datasets/lecteur/sens_locution_latine.jsonl (OFFLINE).

SOURCE : locutions latines courantes de référence. Faits STABLES et CERTAINS (traduction établie).
FAUX=0 : traductions NON CONTESTÉES. locution -> UN sens = fonctionnel. Clés FR minuscules.
"""
from __future__ import annotations
from ingere_wikidata import publie

_LOCUTIONS = [
    ("carpe diem", "cueille le jour (profite du moment présent)"),
    ("veni vidi vici", "je suis venu, j'ai vu, j'ai vaincu"),
    ("alea jacta est", "le sort en est jeté"),
    ("cogito ergo sum", "je pense donc je suis"),
    ("et cetera", "et le reste"),
    ("mea culpa", "par ma faute"),
    ("in vino veritas", "la vérité est dans le vin"),
    ("tempus fugit", "le temps fuit"),
    ("memento mori", "souviens-toi que tu vas mourir"),
    ("vox populi", "voix du peuple"),
    ("persona non grata", "personne indésirable"),
    ("status quo", "l'état actuel des choses"),
    ("ad vitam aeternam", "pour la vie éternelle"),
    ("post mortem", "après la mort"),
    ("a priori", "avant toute expérience"),
    ("a posteriori", "après l'expérience"),
    ("nota bene", "notez bien"),
    ("curriculum vitae", "déroulement de la vie"),
    ("modus operandi", "mode opératoire"),
    ("ad hoc", "fait pour cela"),
]

def ingere():
    print(f"== LOCUTIONS LATINES ({len(_LOCUTIONS)}) ==")
    publie("sens_locution_latine", "convention", "locutions latines courantes (locution -> sens)", _LOCUTIONS)

if __name__ == "__main__":
    ingere()
