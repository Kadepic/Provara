"""
INGESTION ASTRONOMIE (8 planètes du système solaire) -> datasets/lecteur/*.jsonl  (OFFLINE).

SOURCE : valeurs de RÉFÉRENCE NASA/UAI, fournies ici car (a) les API/sites externes sont inaccessibles
(le-systeme-solaire 401, NASA factsheet redirige) et (b) ce sont des faits STABLES et CERTAINS, chacun
VÉRIFIÉ : les diamètres moyens sont CROSS-VALIDÉS par le rayon moyen Wikidata/QLever (P2120) vu en sonde
(Terre r=6371 -> d=12742 ; Mars r=3389,5 -> d=6779 ; etc. -> diamètre = 2×rayon moyen). Le type
(tellurique/gazeuse) et la présence d'anneaux sont des classifications textbook non contestées.

FAUX=0 : uniquement le CERTAIN. On EXCLUT le nombre de lunes (VOLATILE -> change avec les découvertes).
Périmètre = les 8 planètes (Pluton exclue : planète naine, périmètre distinct). Ancres + sanités côté
valide_lecteur. Clés = noms FR (mercure/vénus/.../neptune) ; aucune collision (relations dédiées planète).

Usage : python3 ingere_astronomie.py    (puis non-reg OFFLINE).
"""
from __future__ import annotations

from ingere_wikidata import publie

# (nom_fr, diamètre moyen km [NASA, = 2×rayon moyen, cross-validé QLever P2120], type, anneaux)
_PLANETES = [
    ("mercure", 4879, "tellurique", "non"),
    ("vénus", 12104, "tellurique", "non"),
    ("terre", 12742, "tellurique", "non"),
    ("mars", 6779, "tellurique", "non"),
    ("jupiter", 139820, "gazeuse", "oui"),
    ("saturne", 116460, "gazeuse", "oui"),
    ("uranus", 50724, "gazeuse", "oui"),
    ("neptune", 49244, "gazeuse", "oui"),
]

SRC = "NASA/UAI — valeurs de référence (diamètre moyen ; cross-validé QLever P2120)"

# Planètes naines reconnues par l'UAI (faits certains, ensemble fini fixé par l'UAI).
_NAINES = ["cérès", "pluton", "hauméa", "makémaké", "éris"]

# Lunes MAJEURES -> planète parente (faits certains ; chaque lune orbite UNE planète = fonctionnel).
# (sous-ensemble bien connu et non contesté ; les petites lunes/volatiles ne sont PAS listées.)
_LUNES = [
    ("lune", "terre"),
    ("phobos", "mars"), ("déimos", "mars"),
    ("io", "jupiter"), ("europe", "jupiter"), ("ganymède", "jupiter"), ("callisto", "jupiter"),
    ("titan", "saturne"), ("encelade", "saturne"), ("mimas", "saturne"), ("rhéa", "saturne"),
    ("titania", "uranus"), ("obéron", "uranus"), ("miranda", "uranus"),
    ("triton", "neptune"),
]


def ingere():
    print("== ASTRONOMIE — planètes + naines + lunes (faits certains) ==")
    publie("diametre_moyen_planete", "physique", SRC, [(n, str(d)) for n, d, _, _ in _PLANETES])
    publie("type_planete", "convention", "classification UAI (tellurique/gazeuse)",
           [(n, t) for n, _, t, _ in _PLANETES])
    publie("anneaux_planete", "physique", "présence d'un système d'anneaux (oui/non)",
           [(n, a) for n, _, _, a in _PLANETES])
    publie("planete_naine", "convention", "UAI — planètes naines reconnues",
           [(n, "planète naine") for n in _NAINES])
    publie("planete_parente", "physique", "astre autour duquel orbite la lune (lunes majeures)", _LUNES)


if __name__ == "__main__":
    ingere()
    print("\nFait. Relancer la non-reg OFFLINE :  python3 _nonreg.py --full --jobs 6")
