"""decidabilite.py — Décidabilité / indécidabilité d'un énoncé (problème de décision).

CATALOGUE de FAITS mathématiques ÉTABLIS (théorie de la calculabilité / complexité). Chaque entrée est un
résultat PROUVÉ et sourcé ; aucune réponse n'est devinée. Un problème HORS catalogue -> ValueError (abstention
structurelle, faux positif INTERDIT). FAUX=0.

Statuts (faits certains) :
  - 'arret'                        INDÉCIDABLE   (Turing 1936, problème de l'arrêt)
  - 'satisfiabilite_propositionnelle' / 'SAT'  DÉCIDABLE (NP-complet, Cook 1971)
  - 'primalite'                    DÉCIDABLE     (P, AKS 2002)
  - 'equivalence_machines_turing'  INDÉCIDABLE   (corollaire Rice / réduction de l'arrêt)
  - 'correspondance_post' / 'PCP'  INDÉCIDABLE   (Post 1946)
  - 'accessibilite_graphe'         DÉCIDABLE     (P, parcours/Reachability, NL-complet)

stdlib uniquement, fonctions pures et déterministes.
"""

# Catalogue immuable : nom canonique -> (décidable: bool, classe: str, référence: str).
# décidable=True  -> il existe un algorithme qui termine et décide correctement.
# décidable=False -> AUCUN algorithme ne décide le problème (indécidable, prouvé).
_CATALOGUE = {
    "arret": (False, "indecidable", "Turing 1936 — halting problem"),
    "satisfiabilite_propositionnelle": (True, "NP-complet", "Cook 1971 — SAT"),
    "primalite": (True, "P", "AKS 2002 — PRIMES in P"),
    "equivalence_machines_turing": (False, "indecidable", "theoreme de Rice — equivalence de MT"),
    "correspondance_post": (False, "indecidable", "Post 1946 — PCP"),
    "accessibilite_graphe": (True, "P (NL-complet)", "parcours de graphe — st-connectivity"),
}

# Alias / synonymes acceptés -> nom canonique (faits identiques, juste un autre libellé établi).
_ALIAS = {
    "sat": "satisfiabilite_propositionnelle",
    "satisfiabilite": "satisfiabilite_propositionnelle",
    "satisfiabilite_propositionnelle": "satisfiabilite_propositionnelle",
    "pcp": "correspondance_post",
    "correspondance_post": "correspondance_post",
    "post": "correspondance_post",
    "arret": "arret",
    "halt": "arret",
    "halting": "arret",
    "probleme_de_l_arret": "arret",
    "primalite": "primalite",
    "primality": "primalite",
    "equivalence_machines_turing": "equivalence_machines_turing",
    "equivalence_mt": "equivalence_machines_turing",
    "accessibilite_graphe": "accessibilite_graphe",
    "accessibilite": "accessibilite_graphe",
    "reachability": "accessibilite_graphe",
}


def _canon(probleme):
    """Normalise un libellé de problème vers son nom canonique du catalogue.

    Abstention stricte : type non-str ou nom hors catalogue/alias -> ValueError. Jamais de devinette.
    """
    if not isinstance(probleme, str):
        raise ValueError(f"probleme doit etre une chaine, recu {type(probleme).__name__}")
    cle = probleme.strip().lower().replace("-", "_").replace(" ", "_").replace("/", "_")
    while "__" in cle:
        cle = cle.replace("__", "_")
    if not cle:
        raise ValueError("probleme vide")
    if cle in _ALIAS:
        return _ALIAS[cle]
    raise ValueError(f"probleme inconnu hors catalogue: {probleme!r} (abstention)")


def statut_decidabilite(probleme):
    """Renvoie 'decidable' ou 'indecidable' pour un problème du catalogue (fait établi).

    Problème hors catalogue -> ValueError (abstention structurelle).
    """
    decidable, _classe, _ref = _CATALOGUE[_canon(probleme)]
    return "decidable" if decidable else "indecidable"


def est_decidable(probleme):
    """True ssi le problème est décidable (catalogue de faits). Hors catalogue -> ValueError."""
    return _CATALOGUE[_canon(probleme)][0]


def classe_complexite(probleme):
    """Classe établie (P / NP-complet / indecidable …) pour un problème du catalogue.

    Hors catalogue -> ValueError.
    """
    return _CATALOGUE[_canon(probleme)][1]


def reference(probleme):
    """Référence du résultat (auteur/année) pour un problème du catalogue. Hors catalogue -> ValueError."""
    return _CATALOGUE[_canon(probleme)][2]


def catalogue():
    """Liste triée des noms canoniques de problèmes au statut établi (faits certains)."""
    return sorted(_CATALOGUE)
