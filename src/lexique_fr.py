"""
LEXIQUE_FR — graine de dictionnaire français CERTIFIÉ (2026-06-18, idée Yohan « la définition officielle = la vérité »).

La définition d'un mot est ACTÉE, OFFICIELLE → c'est une vérité de référence (un ORACLE de sens), pas la vision d'un
modèle (donc pas de boîte noire : la réalité humaine juge). Chaque entrée porte tous les AXES vérifiables du mot :
définition, classe grammaticale, genre, hyperonyme (est-une-sorte-de), synonymes, antonymes.

Graine restreinte mais RÉELLE, certifiée par le professeur. Elle s'étendra (Wiktionnaire…) ; la STRUCTURE est ce qui
compte : elle rend la compréhension VÉRIFIABLE (les relations se contrôlent par la brique relation-lexicale + juge).
"""
from __future__ import annotations

# mot -> {classe, genre, definition, hyper (hyperonyme direct ou None), syn, ant}
LEXIQUE = {
    "chat":       {"classe": "nom", "genre": "masculin", "definition": "petit mammifère félin domestique",
                   "hyper": "félin", "syn": ["matou"], "ant": []},
    "félin":      {"classe": "nom", "genre": "masculin", "definition": "mammifère carnivore aux griffes rétractiles",
                   "hyper": "mammifère", "syn": [], "ant": []},
    "mammifère":  {"classe": "nom", "genre": "masculin", "definition": "animal vertébré qui allaite ses petits",
                   "hyper": "animal", "syn": [], "ant": []},
    "animal":     {"classe": "nom", "genre": "masculin", "definition": "être vivant doué de sensibilité et de mouvement",
                   "hyper": None, "syn": ["bête"], "ant": []},
    "chien":      {"classe": "nom", "genre": "masculin", "definition": "mammifère domestique de la famille des canidés",
                   "hyper": "canidé", "syn": ["toutou"], "ant": []},
    "canidé":     {"classe": "nom", "genre": "masculin", "definition": "mammifère carnivore au museau allongé",
                   "hyper": "mammifère", "syn": [], "ant": []},
    "voiture":    {"classe": "nom", "genre": "féminin", "definition": "véhicule à moteur à quatre roues",
                   "hyper": "véhicule", "syn": ["auto", "automobile"], "ant": []},
    "véhicule":   {"classe": "nom", "genre": "masculin", "definition": "engin servant au transport",
                   "hyper": None, "syn": [], "ant": []},
    "grand":      {"classe": "adjectif", "genre": None, "definition": "de taille élevée",
                   "hyper": None, "syn": [], "ant": ["petit"]},
    "petit":      {"classe": "adjectif", "genre": None, "definition": "de taille réduite",
                   "hyper": None, "syn": [], "ant": ["grand"]},
    "chaud":      {"classe": "adjectif", "genre": None, "definition": "qui a une température élevée",
                   "hyper": None, "syn": [], "ant": ["froid"]},
    "froid":      {"classe": "adjectif", "genre": None, "definition": "qui a une température basse",
                   "hyper": None, "syn": [], "ant": ["chaud"]},
    # --- domaine animal élargi ---
    "lion":       {"classe": "nom", "genre": "masculin", "definition": "grand félin d'Afrique",
                   "hyper": "félin", "syn": [], "ant": []},
    "tigre":      {"classe": "nom", "genre": "masculin", "definition": "grand félin rayé d'Asie",
                   "hyper": "félin", "syn": [], "ant": []},
    "oiseau":     {"classe": "nom", "genre": "masculin", "definition": "animal vertébré couvert de plumes",
                   "hyper": "animal", "syn": [], "ant": []},
    "poisson":    {"classe": "nom", "genre": "masculin", "definition": "animal vertébré aquatique à nageoires",
                   "hyper": "animal", "syn": [], "ant": []},
    "souris":     {"classe": "nom", "genre": "féminin", "definition": "petit mammifère rongeur",
                   "hyper": "mammifère", "syn": [], "ant": []},
    # --- véhicules ---
    "camion":     {"classe": "nom", "genre": "masculin", "definition": "grand véhicule de transport de marchandises",
                   "hyper": "véhicule", "syn": [], "ant": []},
    "moto":       {"classe": "nom", "genre": "féminin", "definition": "véhicule à deux roues à moteur",
                   "hyper": "véhicule", "syn": ["motocyclette"], "ant": []},
    "avion":      {"classe": "nom", "genre": "masculin", "definition": "véhicule volant à moteur",
                   "hyper": "véhicule", "syn": [], "ant": []},
    # --- plantes ---
    "plante":     {"classe": "nom", "genre": "féminin", "definition": "être vivant végétal",
                   "hyper": None, "syn": [], "ant": []},
    "arbre":      {"classe": "nom", "genre": "masculin", "definition": "grande plante ligneuse à tronc",
                   "hyper": "plante", "syn": [], "ant": []},
    "fleur":      {"classe": "nom", "genre": "féminin", "definition": "partie colorée d'une plante",
                   "hyper": "plante", "syn": [], "ant": []},
    "rose":       {"classe": "nom", "genre": "féminin", "definition": "fleur ornementale parfumée",
                   "hyper": "fleur", "syn": [], "ant": []},
    "chêne":      {"classe": "nom", "genre": "masculin", "definition": "grand arbre à glands",
                   "hyper": "arbre", "syn": [], "ant": []},
    # --- aliments ---
    "aliment":    {"classe": "nom", "genre": "masculin", "definition": "substance qui nourrit",
                   "hyper": None, "syn": ["nourriture"], "ant": []},
    "fruit":      {"classe": "nom", "genre": "masculin", "definition": "organe comestible issu de la fleur",
                   "hyper": "aliment", "syn": [], "ant": []},
    "pomme":      {"classe": "nom", "genre": "féminin", "definition": "fruit rond du pommier",
                   "hyper": "fruit", "syn": [], "ant": []},
    # --- adjectifs / antonymes ---
    "rapide":     {"classe": "adjectif", "genre": None, "definition": "qui va vite",
                   "hyper": None, "syn": [], "ant": ["lent"]},
    "lent":       {"classe": "adjectif", "genre": None, "definition": "qui va doucement",
                   "hyper": None, "syn": [], "ant": ["rapide"]},
    "clair":      {"classe": "adjectif", "genre": None, "definition": "qui a beaucoup de lumière",
                   "hyper": None, "syn": [], "ant": ["sombre"]},
    "sombre":     {"classe": "adjectif", "genre": None, "definition": "qui a peu de lumière",
                   "hyper": None, "syn": [], "ant": ["clair"]},
    "jeune":      {"classe": "adjectif", "genre": None, "definition": "qui a peu d'âge",
                   "hyper": None, "syn": [], "ant": ["vieux"]},
    "vieux":      {"classe": "adjectif", "genre": None, "definition": "qui a beaucoup d'âge",
                   "hyper": None, "syn": [], "ant": ["jeune"]},
    "fort":       {"classe": "adjectif", "genre": None, "definition": "qui a de la force",
                   "hyper": None, "syn": [], "ant": ["faible"]},
    "faible":     {"classe": "adjectif", "genre": None, "definition": "qui a peu de force",
                   "hyper": None, "syn": [], "ant": ["fort"]},
}


def edges_isa(lex=LEXIQUE):
    """Arêtes dirigées mot -> hyperonyme (pour la closure « est-une-sorte-de »)."""
    return [(m, d["hyper"]) for m, d in lex.items() if d["hyper"]]


def edges_syn(lex=LEXIQUE):
    """Arêtes de synonymie (traitées NON dirigées par la brique)."""
    return [(m, s) for m, d in lex.items() for s in d["syn"]]


def ancetres(mot, lex=LEXIQUE):
    """Tous les hyperonymes transitifs d'un mot (en suivant la chaîne `hyper`)."""
    out, cur = [], lex.get(mot, {}).get("hyper")
    while cur:
        out.append(cur)
        cur = lex.get(cur, {}).get("hyper")
    return out
