"""paradoxes.py — Paradoxes logiques (menteur, Russell, etc.).

Mécanismes EXACTS et faits ÉTABLIS, FAUX=0 :

1) DÉTECTION D'AUTO-RÉFÉRENCE (`est_autoreferentiel`) : détecteur SYNTAXIQUE
   déterministe. Une phrase est dite auto-référentielle ssi elle contient
   un marqueur d'auto-désignation d'un LEXIQUE FERMÉ (« cette phrase », « this
   sentence », …) OU son propre nom comme jeton autonome. Sa valeur de retour
   est entièrement déterminée par cette définition (aucune sémantique devinée).

2) ARGUMENT DIAGONAL (Russell, barbier, menteur, Grelling) : on prouve la
   contradiction par énumération EXHAUSTIVE des deux valeurs de vérité.
   La compréhension naïve impose  p ⟺ ¬p  ; aucune des deux assignations
   (p=Vrai, p=Faux) n'est cohérente -> contradiction démontrée (renvoie True).
   C'est le mécanisme exact de Russell (1901), résolu par l'axiomatisation ZF
   (restriction du schéma de compréhension).

3) CATALOGUE de paradoxes établis (`catalogue`) : faits sourcés ; tout nom
   hors du catalogue connu -> abstention (ValueError), jamais d'invention.

stdlib uniquement.
"""
import re

# ── Lexique FERMÉ de marqueurs d'auto-désignation (établis) ──
_MARQUEURS = (
    "cette phrase",
    "cette proposition",
    "cette affirmation",
    "cette assertion",
    "cet énoncé",
    "cet enonce",
    "la présente phrase",
    "le présent énoncé",
    "le present enonce",
    "this sentence",
    "this statement",
    "this proposition",
    "the present sentence",
)


def est_autoreferentiel(phrase, nom_phrase=None):
    """True ssi la phrase se désigne elle-même (détecteur syntaxique exact).

    Mécanisme : présence d'un marqueur du lexique fermé `_MARQUEURS`
    (insensible à la casse) OU présence de `nom_phrase` comme jeton autonome.

    Abstention : phrase non-chaîne / vide -> ValueError ;
    nom_phrase fourni mais non-chaîne -> ValueError.
    """
    if not isinstance(phrase, str) or phrase.strip() == "":
        raise ValueError("phrase invalide : chaîne non vide attendue")
    if nom_phrase is not None and not isinstance(nom_phrase, str):
        raise ValueError("nom_phrase invalide : chaîne ou None attendu")
    bas = phrase.lower()
    if any(m in bas for m in _MARQUEURS):
        return True
    if nom_phrase is not None and nom_phrase.strip() != "":
        jetons = {j.lower() for j in re.findall(r"\w+", phrase, re.UNICODE)}
        if nom_phrase.strip().lower() in jetons:
            return True
    return False


def _contradiction_diagonale():
    """Prouve qu'une proposition p contrainte par  p ⟺ ¬p  est contradictoire.

    Énumère les DEUX valeurs de vérité possibles. Pour chacune, la définition
    impose p == (¬p) ; aucune n'est cohérente -> aucune assignation valide.
    """
    for v in (True, False):          # v = valeur supposée de p
        impose = (not v)             # la définition impose  p == ¬p
        if v == impose:              # une assignation cohérente existerait-elle ?
            return False             # -> alors pas de paradoxe (jamais atteint)
    return True                      # aucune cohérente -> contradiction prouvée


def ensemble_russell_paradoxal():
    """Paradoxe de Russell : R = {x : x ∉ x}.

    Par compréhension naïve, (R ∈ R) ⟺ (R ∉ R). Énumération exhaustive :
    aucune valeur de vérité de « R ∈ R » n'est cohérente -> True (paradoxe prouvé).
    """
    for hyp in (True, False):        # hyp = valeur supposée de « R ∈ R »
        implique = (not hyp)         # définition de R : (R ∈ R) ⟺ (R ∉ R)
        if hyp == implique:          # assignation cohérente ?
            return False
    return True


def barbier_paradoxal():
    """Barbier de Russell : le barbier rase exactement ceux qui ne se rasent pas
    eux-mêmes. « Le barbier se rase » ⟺ « le barbier ne se rase pas » -> paradoxe.
    Même structure diagonale que l'ensemble de Russell. Renvoie True."""
    return _contradiction_diagonale()


def menteur_paradoxal():
    """Paradoxe du menteur : « Cette phrase est fausse ». Sa valeur de vérité p
    vérifie p ⟺ ¬p -> ni vraie ni fausse sans contradiction. Renvoie True."""
    return _contradiction_diagonale()


def grelling_paradoxal():
    """Paradoxe de Grelling–Nelson : l'adjectif « hétérologique » (qui ne se
    décrit pas lui-même) est-il hétérologique ? hét. ⟺ ¬hét. -> paradoxe. True."""
    return _contradiction_diagonale()


def est_heterologique(adjectif, se_decrit_lui_meme):
    """Grelling : un adjectif est hétérologique ssi il NE se décrit PAS lui-même.

    Cas ordinaire (mécanisme exact) : renvoie  not se_decrit_lui_meme.
    Cas auto-sapant « hétérologique » lui-même -> abstention (ValueError) :
    établi paradoxal, ni hétérologique ni autologique sans contradiction.
    """
    if not isinstance(adjectif, str) or adjectif.strip() == "":
        raise ValueError("adjectif invalide : chaîne non vide attendue")
    if not isinstance(se_decrit_lui_meme, bool):
        raise ValueError("se_decrit_lui_meme invalide : booléen attendu")
    if adjectif.strip().lower() in ("hétérologique", "heterologique", "heterological"):
        raise ValueError("paradoxal : « hétérologique » n'a pas de valeur cohérente")
    return not se_decrit_lui_meme


# ── CATALOGUE de paradoxes ÉTABLIS (faits sourcés) ──
_CATALOGUE = {
    "menteur": {
        "nom": "Paradoxe du menteur",
        "famille": "sémantique",
        "enonce": "« Cette phrase est fausse »",
        "auto_referentiel": True,
        "paradoxal": True,
        "note": "Auto-référence + négation : p ⟺ ¬p (Eubulide ; Tarski : "
                "vérité indéfinissable dans le langage lui-même).",
    },
    "russell": {
        "nom": "Paradoxe de Russell",
        "famille": "théorie des ensembles",
        "enonce": "R = {x : x ∉ x} ; R ∈ R ⟺ R ∉ R",
        "auto_referentiel": True,
        "paradoxal": True,
        "note": "Russell, 1901. Réfute la compréhension naïve ; résolu par "
                "l'axiomatisation ZF (schéma de séparation/fondation).",
    },
    "barbier": {
        "nom": "Barbier de Russell",
        "famille": "théorie des ensembles",
        "enonce": "Le barbier rase exactement ceux qui ne se rasent pas eux-mêmes",
        "auto_referentiel": True,
        "paradoxal": True,
        "note": "Illustration concrète du paradoxe de Russell : un tel barbier "
                "ne peut exister.",
    },
    "berry": {
        "nom": "Paradoxe de Berry",
        "famille": "définissabilité",
        "enonce": "« le plus petit entier non définissable en moins de quinze mots »",
        "auto_referentiel": True,
        "paradoxal": True,
        "note": "Cette description définit pourtant cet entier en moins de quinze "
                "mots. Paradoxe de définissabilité (G. G. Berry).",
    },
    "grelling": {
        "nom": "Paradoxe de Grelling–Nelson",
        "famille": "sémantique",
        "enonce": "« hétérologique » (qui ne se décrit pas) est-il hétérologique ?",
        "auto_referentiel": True,
        "paradoxal": True,
        "note": "Grelling & Nelson, 1908. Variante sémantique du paradoxe de Russell.",
    },
}


def catalogue(nom):
    """Description d'un paradoxe ÉTABLI (dict de faits). Nom hors catalogue
    -> ValueError (abstention, jamais d'invention).

    Noms connus : 'menteur', 'russell', 'barbier', 'berry', 'grelling'.
    """
    if not isinstance(nom, str):
        raise ValueError("nom invalide : chaîne attendue")
    cle = nom.strip().lower()
    if cle not in _CATALOGUE:
        raise ValueError(f"paradoxe inconnu : {nom!r} (abstention)")
    return dict(_CATALOGUE[cle])
