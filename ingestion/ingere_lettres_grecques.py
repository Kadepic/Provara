"""
INGESTION GREC — lettre grecque (nom) -> symbole minuscule  -> datasets/lecteur/symbole_grec.jsonl (OFFLINE).

SOURCE : alphabet grec de référence. Faits STABLES et CERTAINS.
FAUX=0 : on clé par le NOM (le symbole seul -> "" par normalise). Fonctionnel.
"""
from __future__ import annotations
from ingere_wikidata import publie

_LETTRES = [
    ("alpha", "α"), ("bêta", "β"), ("gamma", "γ"), ("delta", "δ"), ("epsilon", "ε"),
    ("zêta", "ζ"), ("êta", "η"), ("thêta", "θ"), ("iota", "ι"), ("kappa", "κ"),
    ("lambda", "λ"), ("mu", "μ"), ("nu", "ν"), ("xi", "ξ"), ("omicron", "ο"),
    ("pi", "π"), ("rhô", "ρ"), ("sigma", "σ"), ("tau", "τ"), ("upsilon", "υ"),
    ("phi", "φ"), ("chi", "χ"), ("psi", "ψ"), ("oméga", "ω"),
]

def ingere():
    print(f"== LETTRES GRECQUES — nom -> symbole ({len(_LETTRES)}) ==")
    publie("symbole_grec", "convention", "alphabet grec (nom -> symbole)", _LETTRES, articles=False)

if __name__ == "__main__":
    ingere()
