"""
INGESTION GASTRONOMIE — plat -> pays d'origine  -> datasets/lecteur/pays_plat.jsonl (OFFLINE).

SOURCE : gastronomie de référence. Faits STABLES et CERTAINS pour les origines NON CONTESTÉES.
FAUX=0 : on ÉCARTE les origines disputées (croissant, hamburger, couscous=pays flou, bortsch). 
plat -> UN pays = fonctionnel. Clés FR minuscules.
"""
from __future__ import annotations
from ingere_wikidata import publie

_PLATS = [
    ("pizza", "Italie"), ("risotto", "Italie"), ("tiramisu", "Italie"), ("lasagnes", "Italie"),
    ("sushi", "Japon"), ("ramen", "Japon"), ("sashimi", "Japon"), ("tempura", "Japon"),
    ("paella", "Espagne"), ("gaspacho", "Espagne"), ("tortilla", "Espagne"),
    ("tacos", "Mexique"), ("guacamole", "Mexique"), ("burrito", "Mexique"),
    ("goulash", "Hongrie"), ("kebab", "Turquie"), ("moussaka", "Grèce"),
    ("pad thai", "Thaïlande"), ("dim sum", "Chine"), ("canard laqué", "Chine"),
    ("fondue", "Suisse"), ("raclette", "Suisse"), ("curry", "Inde"),
    ("biryani", "Inde"), ("falafel", "Liban"), ("houmous", "Liban"),
    ("poutine", "Canada"), ("ceviche", "Pérou"), ("feijoada", "Brésil"),
]

def ingere():
    print(f"== PLATS -> PAYS ({len(_PLATS)}) ==")
    publie("pays_plat", "convention", "gastronomie de référence (plat -> pays d'origine) — non contesté", _PLATS)

if __name__ == "__main__":
    ingere()
