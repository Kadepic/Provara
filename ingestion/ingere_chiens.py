"""
INGESTION CYNOLOGIE — race de chien -> pays d'origine  -> datasets/lecteur/pays_race_chien.jsonl (OFFLINE).

SOURCE : standards cynologiques de référence (FCI). Faits STABLES et CERTAINS pour les origines NON CONTESTÉES.
FAUX=0 : on ÉCARTE les origines disputées (caniche FR/Allemagne). Fonctionnel. Clés FR minuscules.
"""
from __future__ import annotations
from ingere_wikidata import publie

_PAR_PAYS = {
    "Allemagne": ["berger allemand", "rottweiler", "teckel", "doberman", "boxer", "dogue allemand",
                  "schnauzer", "weimaraner"],
    "France": ["bouledogue français", "basset hound", "braque français", "berger de beauce", "briard"],
    "Royaume-Uni": ["border collie", "beagle", "cocker anglais", "bulldog anglais", "golden retriever",
                    "yorkshire", "bull terrier", "fox terrier"],
    "Canada": ["labrador", "terre-neuve"],
    "Japon": ["akita", "shiba inu"],
    "Chine": ["carlin", "pékinois", "chow-chow", "shar-peï"],
    "Suisse": ["saint-bernard", "bouvier bernois"],
    "Russie": ["husky sibérien", "samoyède", "lévrier barzoï"],
    "Mexique": ["chihuahua"],
    "Croatie": ["dalmatien"],
    "Afghanistan": ["lévrier afghan"],
    "Belgique": ["berger belge"],
}

def ingere():
    paires = [(r, p) for p, races in _PAR_PAYS.items() for r in races]
    print(f"== RACES DE CHIENS -> PAYS ({len(paires)}) ==")
    publie("pays_race_chien", "convention", "cynologie FCI (race -> pays d'origine)", paires)

if __name__ == "__main__":
    ingere()
