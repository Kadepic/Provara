"""
INVENTION DIVERGENTE — câblage des 6 briques qui inventent HORS de la recombinaison de l'existant (2026-07-02).

POURQUOI (priorité #1 de Yohan : « proposer des innovations SANS suivre les concepts existants ») : le moteur
d'invention câblé (`moteur_invention.examine_cible`) tranche EXISTE/INVENTION/AMBIGU/BRIQUE_MANQUANTE en RECOMBINANT
le registre des capacités CONNUES — c'est inventer EN COMBINANT le déjà-là. Six briques génériques, sound et validées,
faisaient un geste DIFFÉRENT — mais restaient ORPHELINES (importées seulement par leur validateur). Ce module les
EXPOSE comme des MODES d'invention distincts (leurs formats d'entrée diffèrent d'une fonction-cible I/O, donc on ne
les fond pas dans examine_cible : on les rend atteignables comme capacités de 1re classe).

Les 6 gestes divergents :
  • APPRENDRE UNE LOI NEUVE du monde depuis l'observation (régression symbolique, `decouverte_loi`).
  • LEVER LA CONTRAINTE qui bloque un design pour rouvrir l'espace (TRIZ, `relaxation`).
  • TRANSFÉRER une structure d'un domaine à un autre (analogie, `structure_mapping`).
  • ARBITRER des objectifs concurrents (front de compromis, `pareto`).
  • EXPLIQUER un phénomène par ses causes amont (abduction, `abduction`).
  • ENCHAÎNER des actions vers un but / un procédé (planification STRIPS, `planification`).

FAUX=0 : ce module n'ajoute AUCUNE logique de décision — il délègue à des briques déjà sound (chacune ABSTIENT/
renvoie None sans preuve, re-vérifie sa sortie). Il n'émet donc jamais un faux ; au pire un « pas de résultat »
honnête. Stdlib pur, souverain. C'est du CÂBLAGE (rendre le divergent accessible), pas une réécriture.
"""
from __future__ import annotations


# ————————————————————————————— 1. APPRENDRE UNE LOI (data → f(x)) —————————————————————————————
def apprend_loi(donnees, tol: float = 1e-6):
    """Découvre la loi la plus simple y=f(x) qui colle à TOUS les points (held-out inclus), ou None (abstention).
    « Apprendre une loi NEUVE du monde depuis l'observation » — pas la retrouver dans un catalogue. FAUX=0 délégué
    à `decouverte_loi` (loi rendue seulement si elle colle partout ; None sinon). Renvoie {forme, params} ou None."""
    import decouverte_loi
    r = decouverte_loi.decouvre(donnees, tol)
    return None if r is None else {"forme": r["forme"], "params": r["params"], "predit": r["predit"]}


# ————————————————————————————— 2. LEVER UNE CONTRAINTE (TRIZ) —————————————————————————————
def leve_contrainte(variables: dict, contraintes):
    """Sur un problème de design SUR-CONTRAINT (aucune solution), trouve le PLUS PETIT ensemble de contraintes à
    LEVER pour rouvrir l'espace — le geste d'invention TRIZ que l'esprit fixé ne fait pas. `variables` = {nom: domaine
    fini itérable} ; `contraintes` = [(portée=tuple de noms, prédicat=callable positionnel, nom)]. Renvoie
    {contraintes_a_relacher: [noms], solution: dict} ({[], solution} si déjà satisfiable), ou None si insoluble même
    tout relâché. FAUX=0 délégué à `relaxation` (solution du CSP réduit RE-VÉRIFIÉE)."""
    from contrainte import CSP
    import relaxation
    csp = CSP()
    for nom, domaine in variables.items():
        csp.variable(nom, domaine)
    for portee, predicat, nom in contraintes:
        csp.contrainte(portee, predicat, nom)
    return relaxation.relache_minimal(csp)


# ————————————————————————————— 3. TRANSFÉRER UNE STRUCTURE (analogie) —————————————————————————————
def transfere_analogie(source, cible):
    """Cherche la correspondance STRUCTURELLE (bijection d'objets préservant les prédicats) entre deux domaines —
    le transfert de solution inter-domaines (chaleur↔électricité↔eau). `source`/`cible` = listes de tuples
    (prédicat, *args). Renvoie {mapping, alignees, couverture} ou None (aucune structure alignable). FAUX=0 délégué à
    `structure_mapping` (jamais un appariement forcé)."""
    import structure_mapping
    r = structure_mapping.trouve(source, cible)
    if r is None:
        return None
    mapping, alignees = r
    cov = structure_mapping.couverture(source, cible)
    return {"mapping": mapping, "alignees": alignees, "couverture": cov}


# ————————————————————————————— 4. ARBITRER DES COMPROMIS (Pareto) —————————————————————————————
def arbitre_compromis(candidats, sens):
    """Front de Pareto : les designs qu'AUCUN autre ne domine (pas d'amélioration d'un objectif sans en dégrader un
    autre) = l'ensemble des choix rationnels. `candidats` = [(étiquette, objectifs=tuple)] ; `sens` = tuple de
    'min'/'max'. Renvoie la sous-liste non dominée (exacte, aucun point interpolé inventé). FAUX=0 délégué à `pareto`."""
    import pareto
    return pareto.front(candidats, sens)


# ————————————————————————————— 5. EXPLIQUER UN PHÉNOMÈNE (abduction) —————————————————————————————
def explique_observations(graphe, observations, taille_max: int = 3):
    """Meilleure explication : plus PETIT ensemble de causes (nœuds d'un `causalite.GrapheCausal`) dont les effets
    couvrent TOUTES les observations — l'étape amont du diagnostic/invention. Renvoie {hypotheses, couvre,
    inexpliquees} ou None. FAUX=0 délégué à `abduction` (une cause n'explique que par un chemin causal RÉEL ;
    observations inexplicables signalées ; proposé, non affirmé)."""
    import abduction
    return abduction.meilleure_explication(graphe, observations, taille_max)


# ————————————————————————————— 6. PLANIFIER UN PROCÉDÉ (STRIPS) —————————————————————————————
def plan_procede(etat_initial, but, operateurs, max_etats: int = 100000):
    """Séquence d'actions (procédé/assemblage) menant de `etat_initial` (itérable de littéraux) à `but` via des
    `planification.Operateur` STRIPS. Renvoie la liste des noms d'opérateurs (plan minimal, RE-JOUÉ avant renvoi)
    ou None (pas de plan / budget épuisé). FAUX=0 délégué à `planification` (jamais un plan qui ne se déroule pas)."""
    import planification
    return planification.plan(etat_initial, but, operateurs, max_etats)


# Ré-export de l'Operateur STRIPS pour que l'appelant construise un procédé sans importer planification.
def Operateur(nom, pre=(), ajoute=(), retire=()):
    """Fabrique d'opérateur STRIPS (nom, préconditions, ajouts, retraits) — cf. planification.Operateur."""
    import planification
    return planification.Operateur(nom, pre, ajoute, retire)
