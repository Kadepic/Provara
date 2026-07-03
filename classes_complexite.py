"""CLASSES DE COMPLEXITÉ (P, NP, NP-complet, NP-difficile, indécidable) — CATALOGUE de faits ÉTABLIS, FAUX=0
(mission formule/concept 2026-06-29 ; sujet borné « Théorie de la complexité (P, NP, etc.) »).

Complémentaire de `complexite.py` (théorème maître + ordres de croissance) : ici on classe les PROBLÈMES
décisionnels canoniques dans la hiérarchie des classes de complexité, et on énonce les relations ÉTABLIES
entre classes.

POSTURE FAUX=0 (la réalité juge, jamais un faux) :
  • Chaque classification est un THÉORÈME ÉTABLI et SOURCÉ (Cook–Levin 1971, Karp 1972 « 21 problèmes »,
    AKS 2002 pour la primalité, Turing 1936 pour l'indécidabilité de l'arrêt). C'est la classification
    CANONIQUE/STANDARD telle que tout manuel la donne (« SAT est NP-complet », « le tri est dans P »).
  • Les prédicats booléens rapportent cette classification canonique : `est_np_complet('tri') == False`
    signifie « le tri n'est PAS classé NP-complet dans le catalogue établi » (il est dans P) — c'est un
    fait sur la classification standard, pas une résolution d'une séparation ouverte.
  • La SEULE question réellement OUVERTE (P =? NP) n'est JAMAIS tranchée : `p_egal_np()` et
    `relation_classes('NP', 'P')` renvoient 'ouvert'. On n'invente aucune réponse.
  • Toute entrée hors du référentiel connu (problème inconnu, classe inconnue, paire de classes dont la
    relation n'est pas établie, type invalide) -> ValueError (ABSTENTION). Jamais une réponse inventée.
  • Déterministe. Conservateur : abstention tolérée, faux POSITIF interdit.

Remarques de rigueur (établies) :
  - « tri » = tri par comparaisons, O(n log n) ∈ P.
  - « voyageur_commerce / TSP » = version OPTIMISATION, NP-difficile (la version DÉCISION « existe-t-il un
    tour de longueur ≤ k ? » est, elle, NP-complète). On donne la classification d'optimisation demandée.
  - « sac_a_dos / knapsack », « clique », « cycle_hamiltonien »… = versions DÉCISION (cadre où la
    NP-complétude est définie), conformément à Karp 1972.
  - « arret » = problème de l'arrêt, INDÉCIDABLE (aucun algorithme ne le décide ; ce n'est pas une classe
    de temps).
"""
from __future__ import annotations

# ── CLASSES (libellés canoniques) ────────────────────────────────────────────────────────────────────────────
P = "P"
NP = "NP"
NP_COMPLET = "NP-complet"
NP_DIFFICILE = "NP-difficile"
PSPACE = "PSPACE"
INDECIDABLE = "indécidable"

_DESCRIPTIONS = {
    P: "décidable en temps polynomial sur machine déterministe",
    NP: "vérifiable en temps polynomial (certificat) / décidable en temps polynomial non déterministe",
    NP_COMPLET: "dans NP ET NP-difficile (les problèmes les plus durs de NP)",
    NP_DIFFICILE: "au moins aussi dur que tout problème de NP (réduction polynomiale), pas nécessairement dans NP",
    PSPACE: "décidable en espace polynomial",
    INDECIDABLE: "aucun algorithme ne le décide (hors de toute classe de complexité de temps)",
}

# ── CATALOGUE DES PROBLÈMES (classification canonique établie) ────────────────────────────────────────────────
# Tout est une classification SOURCÉE : P (algorithme polynomial connu), NP-complet (Cook–Levin / Karp),
# NP-difficile (réduction depuis un NP-difficile, optimisation), indécidable (Turing).
_PROBLEMES = {
    # ── P : algorithme polynomial connu ──
    "tri": P,                       # tri par comparaisons O(n log n)
    "plus_court_chemin": P,         # Dijkstra / Bellman-Ford
    "primalite": P,                 # AKS 2002 — PRIMES ∈ P
    "pgcd": P,                      # algorithme d'Euclide
    "arbre_couvrant_minimal": P,    # Kruskal / Prim
    "appariement_maximal": P,       # Edmonds (blossom)
    "flot_maximal": P,              # Ford-Fulkerson / Edmonds-Karp
    "connexite_graphe": P,          # parcours BFS/DFS
    "programmation_lineaire": P,    # Khachiyan 1979 (ellipsoïde) — LP ∈ P
    "tri_topologique": P,           # Kahn / DFS

    # ── NP-complet : Cook–Levin (1971) et Karp (1972, « 21 problèmes ») — versions DÉCISION ──
    "SAT": NP_COMPLET,              # Cook–Levin
    "3SAT": NP_COMPLET,             # Karp
    "clique": NP_COMPLET,           # Karp
    "ensemble_independant": NP_COMPLET,   # independent set — Karp
    "couverture_sommets": NP_COMPLET,     # vertex cover — Karp
    "cycle_hamiltonien": NP_COMPLET,      # Karp (circuit hamiltonien)
    "coloration_graphe": NP_COMPLET,      # 3-coloration / nombre chromatique — Karp
    "sac_a_dos": NP_COMPLET,        # knapsack (décision) — Karp
    "somme_sous_ensemble": NP_COMPLET,    # subset sum — Karp
    "partition": NP_COMPLET,        # Karp
    "couverture_ensembles": NP_COMPLET,   # set cover — Karp

    # ── NP-difficile : version optimisation (non connue dans NP) ──
    "voyageur_commerce": NP_DIFFICILE,    # TSP optimisation (décision -> NP-complet)

    # ── Indécidable : Turing (1936) et conséquences ──
    "arret": INDECIDABLE,           # problème de l'arrêt
    "correspondance_post": INDECIDABLE,   # Post correspondence problem
}

# Synonymes acceptés (mêmes problèmes, autre nom courant).
_ALIAS = {
    "TSP": "voyageur_commerce",
    "tsp": "voyageur_commerce",
    "voyageur": "voyageur_commerce",
    "knapsack": "sac_a_dos",
    "sac": "sac_a_dos",
    "halting": "arret",
    "probleme_arret": "arret",
    "sat": "SAT",
    "satisfiabilite": "SAT",
    "subset_sum": "somme_sous_ensemble",
    "vertex_cover": "couverture_sommets",
    "independent_set": "ensemble_independant",
    "set_cover": "couverture_ensembles",
    "hamiltonien": "cycle_hamiltonien",
    "circuit_hamiltonien": "cycle_hamiltonien",
}

# ── RELATIONS ENTRE CLASSES (paires ordonnées, faits ÉTABLIS) ────────────────────────────────────────────────
# 'egal'   : c1 = c2 (réflexif).
# 'inclus' : c1 ⊆ c2 PROUVÉ (inclusion ; la stricte inclusion peut rester ouverte, on ne la prétend pas).
# 'ouvert' : la relation est une question OUVERTE (P =? NP).
_RELATIONS = {
    (P, P): "egal",
    (NP, NP): "egal",
    (NP_COMPLET, NP_COMPLET): "egal",
    (NP_DIFFICILE, NP_DIFFICILE): "egal",
    (PSPACE, PSPACE): "egal",
    (INDECIDABLE, INDECIDABLE): "egal",
    (P, NP): "inclus",              # P ⊆ NP — prouvé (un solveur polynomial ignore le certificat)
    (NP, P): "ouvert",             # NP ⊆ P ? = la question P vs NP — OUVERTE
    (P, PSPACE): "inclus",         # P ⊆ PSPACE — prouvé
    (NP, PSPACE): "inclus",        # NP ⊆ PSPACE — prouvé (énumération des certificats en espace poly)
    (NP_COMPLET, NP): "inclus",    # NP-complet ⊆ NP — par définition
    (NP_COMPLET, NP_DIFFICILE): "inclus",  # NP-complet ⊆ NP-difficile — par définition
}


def _resout(nom):
    """Normalise un nom de problème vers une clé du catalogue ; ValueError si hors catalogue."""
    if not isinstance(nom, str) or isinstance(nom, bool):
        raise ValueError(f"nom de problème invalide (str attendu) : {nom!r}")
    cle = nom.strip()
    if cle in _PROBLEMES:
        return cle
    if cle in _ALIAS:
        return _ALIAS[cle]
    raise ValueError(f"problème hors catalogue (abstention) : {nom!r}")


def _classe_valide(c):
    if not isinstance(c, str) or isinstance(c, bool):
        raise ValueError(f"nom de classe invalide (str attendu) : {c!r}")
    cle = c.strip()
    if cle not in _DESCRIPTIONS:
        raise ValueError(f"classe de complexité inconnue (abstention) : {c!r}")
    return cle


def classe_probleme(nom):
    """Classe de complexité CANONIQUE (établie) du problème `nom`.

    Renvoie l'un de : 'P', 'NP-complet', 'NP-difficile', 'indécidable'.
    Problème hors catalogue -> ValueError (abstention).
    """
    return _PROBLEMES[_resout(nom)]


def est_dans_p(nom):
    """True ssi `nom` est CLASSÉ dans P (algorithme polynomial connu). Hors catalogue -> ValueError."""
    return classe_probleme(nom) == P


def est_np_complet(nom):
    """True ssi `nom` est ÉTABLI NP-complet (Cook–Levin / Karp). Hors catalogue -> ValueError.

    False = non classé NP-complet dans le catalogue établi (p. ex. dans P, NP-difficile ou indécidable).
    """
    return classe_probleme(nom) == NP_COMPLET


def est_np_difficile(nom):
    """True ssi `nom` est ÉTABLI NP-difficile. Hors catalogue -> ValueError.

    Tout problème NP-complet est NP-difficile (par définition), donc classe ∈ {NP-complet, NP-difficile}.
    False = non établi NP-difficile dans le catalogue.
    """
    return classe_probleme(nom) in (NP_COMPLET, NP_DIFFICILE)


def est_indecidable(nom):
    """True ssi `nom` est ÉTABLI indécidable (aucun algorithme ne le décide). Hors catalogue -> ValueError."""
    return classe_probleme(nom) == INDECIDABLE


def dans_np(nom):
    """True ssi `nom` est CLASSÉ dans NP (classe ∈ {P, NP, NP-complet}). Hors catalogue -> ValueError.

    Fondé sur les inclusions prouvées P ⊆ NP et NP-complet ⊆ NP.
    """
    return classe_probleme(nom) in (P, NP, NP_COMPLET)


def verification_polynomiale(nom):
    """Un certificat du problème se vérifie-t-il en temps polynomial ? (⟺ appartenance ÉTABLIE à NP)

    Propriété définitionnelle de NP : tout problème de NP admet un vérificateur de certificat polynomial.
    True pour les problèmes classés dans P/NP/NP-complet (tous ⊆ NP, fait établi).
    False pour les problèmes NP-difficiles non connus dans NP (p. ex. TSP optimisation : vérifier
    l'optimalité d'un tour exigerait de réfuter tout tour plus court) et pour les indécidables.
    Hors catalogue -> ValueError.
    """
    return dans_np(nom)


def relation_classes(c1, c2):
    """Relation ÉTABLIE de la classe `c1` vers `c2` : 'egal', 'inclus' (⊆ prouvé) ou 'ouvert' (P vs NP).

    Exemples établis : ('P','NP') -> 'inclus' (P ⊆ NP) ; ('NP','P') -> 'ouvert' (= question P vs NP).
    Classe inconnue ou paire dont la relation n'est pas établie -> ValueError (abstention).
    """
    a, b = _classe_valide(c1), _classe_valide(c2)
    if (a, b) not in _RELATIONS:
        raise ValueError(f"relation non établie entre {c1!r} et {c2!r} (abstention)")
    return _RELATIONS[(a, b)]


def p_egal_np():
    """Statut de la conjecture P =? NP : 'ouvert' (problème non résolu, prix du millénaire)."""
    return "ouvert"


def p_inclus_np():
    """Statut de l'inclusion P ⊆ NP : 'inclus' (théorème établi)."""
    return relation_classes(P, NP)


def decrit_classe(nom_classe):
    """Description textuelle d'une classe de complexité connue. Classe inconnue -> ValueError."""
    return _DESCRIPTIONS[_classe_valide(nom_classe)]


def classes():
    """Tuple des libellés de classes connus du catalogue (ordre stable)."""
    return (P, NP, NP_COMPLET, NP_DIFFICILE, PSPACE, INDECIDABLE)


def problemes():
    """Tuple trié des noms canoniques de problèmes du catalogue (hors alias)."""
    return tuple(sorted(_PROBLEMES))
