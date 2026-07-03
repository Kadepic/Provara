"""
INGESTION BIOLOGIE — animal -> classe zoologique -> datasets/lecteur/classe_animal.jsonl  (OFFLINE).

SOURCE : classification zoologique de référence (niveau scolaire/encyclopédique), faits STABLES et
CERTAINS. Je fournis la donnée moi-même (cf. mandat « je suis une source » pour le certain + borné).

FAUX=0 — discipline appliquée :
  * Uniquement des animaux dont la classe est NON CONTESTÉE.
  * Les cétacés (baleine, dauphin, orque, cachalot, marsouin) et la chauve-souris = MAMMIFÈRES.
  * Requins/raies regroupés sous « poisson » (granularité scolaire FR : poissons cartilagineux) — défendable.
  * On SÉPARE strictement les NON-insectes souvent confondus : araignée/scorpion/tique = ARACHNIDES ;
    crabe/homard/crevette = CRUSTACÉS ; escargot/poulpe/moule = MOLLUSQUES. Ils ne sont PAS dans « insecte ».
  * Mots ambigus ÉCARTÉS (ex. « mulet » = mammifère ET poisson -> on garde mulet=mammifère uniquement).
  * Chaque animal a UNE classe = fonctionnel. Clés = noms FR au singulier, minuscules.

Usage : python3 ingere_biologie.py    (puis non-reg OFFLINE).
"""
from __future__ import annotations

from ingere_wikidata import publie

# classe -> liste d'animaux (noms FR singulier). Chaque entrée VÉRIFIÉE certaine.
_PAR_CLASSE = {
    "mammifère": [
        "chien", "chat", "cheval", "vache", "taureau", "mouton", "chèvre", "cochon", "lapin",
        "souris", "rat", "lion", "tigre", "éléphant", "girafe", "zèbre", "hippopotame",
        "rhinocéros", "ours", "loup", "renard", "cerf", "biche", "sanglier", "baleine",
        "dauphin", "orque", "cachalot", "marsouin", "phoque", "morse", "otarie",
        "chauve-souris", "kangourou", "koala", "panda", "gorille", "chimpanzé", "singe",
        "écureuil", "hérisson", "taupe", "castor", "loutre", "blaireau", "belette", "lynx",
        "guépard", "léopard", "panthère", "jaguar", "antilope", "gazelle", "buffle", "bison",
        "chameau", "dromadaire", "lama", "alpaga", "âne", "mulet", "furet", "hamster",
        "gerbille", "cobaye", "marmotte", "putois", "hermine", "raton laveur", "tapir",
        "okapi", "gnou", "phacochère", "suricate", "ornithorynque", "wallaby", "loir",
    ],
    "oiseau": [
        "aigle", "faucon", "hibou", "chouette", "corbeau", "corneille", "pie", "moineau",
        "pigeon", "colombe", "mésange", "hirondelle", "rouge-gorge", "merle", "pinson",
        "canard", "oie", "cygne", "poule", "coq", "dinde", "paon", "autruche", "émeu",
        "manchot", "flamant", "héron", "cigogne", "grue", "mouette", "goéland", "albatros",
        "pélican", "perroquet", "perruche", "toucan", "colibri", "pic", "pivert", "faisan",
        "perdrix", "caille", "vautour", "condor", "buse", "épervier", "milan", "rossignol",
        "alouette", "étourneau", "geai", "coucou", "martinet", "huppe", "kiwi", "casoar",
    ],
    "poisson": [
        "requin", "thon", "saumon", "truite", "carpe", "brochet", "perche", "sardine",
        "anchois", "morue", "cabillaud", "hareng", "maquereau", "sole", "raie", "anguille",
        "espadon", "barracuda", "murène", "hippocampe", "poisson-chat", "sandre", "gardon",
        "daurade", "bar", "turbot", "flétan", "lotte", "merlu", "églefin", "tanche", "esturgeon",
    ],
    "reptile": [
        "serpent", "cobra", "vipère", "python", "boa", "crocodile", "alligator", "caïman",
        "lézard", "iguane", "gecko", "caméléon", "tortue", "varan", "anaconda", "couleuvre",
        "orvet", "tortue marine", "dragon de komodo",
    ],
    "amphibien": [
        "grenouille", "crapaud", "salamandre", "triton", "axolotl", "rainette",
    ],
    "insecte": [
        "fourmi", "abeille", "guêpe", "frelon", "mouche", "moustique", "papillon", "libellule",
        "coccinelle", "scarabée", "hanneton", "cigale", "sauterelle", "criquet", "grillon",
        "puce", "pou", "termite", "cafard", "blatte", "perce-oreille", "mante religieuse",
        "doryphore", "charançon", "bourdon", "luciole", "éphémère", "punaise", "puceron",
    ],
    "arachnide": [
        "araignée", "scorpion", "tique", "acarien", "mygale", "tarentule", "faucheux",
    ],
    "crustacé": [
        "crabe", "homard", "crevette", "langouste", "écrevisse", "langoustine", "krill",
        "tourteau", "bernard-l'ermite", "cloporte",
    ],
    "mollusque": [
        "escargot", "limace", "poulpe", "pieuvre", "calmar", "seiche", "moule", "huître",
        "palourde", "coque", "bigorneau", "nautile", "ormeau",
    ],
}

SRC = "classification zoologique de référence (classe) — faits certains"


def ingere():
    paires = []
    for classe, animaux in _PAR_CLASSE.items():
        for a in animaux:
            paires.append((a, classe))
    print(f"== BIOLOGIE — animal -> classe ({len(paires)} animaux, {len(_PAR_CLASSE)} classes) ==")
    publie("classe_animal", "convention", SRC, paires)


if __name__ == "__main__":
    ingere()
