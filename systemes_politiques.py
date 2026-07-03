"""
SYSTÈMES POLITIQUES (définitions) — conventions politiques ÉTABLIES, fonctions pures déterministes, FAUX=0.

Ce module ne « pense » pas : il restitue des DÉFINITIONS sourcées (sciences politiques / théorie classique des
régimes, d'Aristote à Montesquieu) et applique une CLASSIFICATION par critères établis. Toute entrée hors du
référentiel connu (système inconnu, suffrage inconnu, critères non déterminants, type invalide) -> ValueError
(abstention), JAMAIS une réponse inventée.

RÉFÉRENTIEL (définitions, étymologie grecque/latine entre parenthèses) :
  • democratie  — dêmos (peuple) + kratos (pouvoir) : la souveraineté appartient au peuple.
  • monarchie   — monos (seul) + arkhê (commandement) : pouvoir d'un seul, en règle générale héréditaire et viager.
  • republique  — res publica (la chose publique) : le pouvoir n'est pas héréditaire, le chef de l'État est électif.
  • dictature   — dictator (magistrat romain à pouvoirs exceptionnels) : pouvoir absolu sans contrôle ni séparation.
  • oligarchie  — oligos (peu nombreux) + arkhê : le pouvoir est détenu par un petit groupe.
  • theocratie  — theos (Dieu) + kratos : l'autorité est censée émaner de la divinité, exercée au nom de Dieu.
  • anarchie    — an- (sans) + arkhê : absence de gouvernement et d'autorité politique.

CLASSIFICATION par critères (typologie classique : nombre de gouvernants × mode de dévolution × suffrage) :
  héréditaire + un seul -> monarchie ; suffrage universel -> démocratie ; petit groupe -> oligarchie ;
  un seul non héréditaire sans suffrage -> dictature ; toute combinaison non déterminée -> ValueError.

SÉPARATION DES POUVOIRS (Montesquieu, « De l'esprit des lois », 1748) : exécutif / législatif / judiciaire.
"""
from __future__ import annotations

import unicodedata


def _normalise(nom):
    """Minuscule, sans espaces de bord, sans accents. Lève ValueError si ce n'est pas une chaîne non vide."""
    if not isinstance(nom, str):
        raise ValueError(f"nom attendu de type str, reçu {type(nom).__name__}")
    s = nom.strip().lower()
    if not s:
        raise ValueError("nom vide")
    s = unicodedata.normalize("NFD", s)
    return "".join(c for c in s if unicodedata.category(c) != "Mn")


# ── DÉFINITIONS ÉTABLIES (clés sans accents ; valeurs = formulations sourcées des sciences politiques) ──
_DEFINITIONS = {
    "democratie": (
        "régime politique dans lequel la souveraineté appartient au peuple, qui l'exerce "
        "directement ou par l'intermédiaire de représentants élus (du grec dêmos, « peuple », "
        "et kratos, « pouvoir »)"
    ),
    "monarchie": (
        "régime politique dans lequel le pouvoir est exercé par une seule personne, le monarque, "
        "le plus souvent à titre viager et héréditaire (du grec monos, « seul », et arkhê, « commandement »)"
    ),
    "republique": (
        "régime politique dans lequel le pouvoir n'est pas détenu de façon héréditaire, la fonction "
        "de chef de l'État est élective et la chose publique (res publica) appartient à la collectivité"
    ),
    "dictature": (
        "régime politique dans lequel une personne ou un groupe restreint exerce un pouvoir absolu, "
        "sans contrôle, sans limitation et sans séparation des pouvoirs"
    ),
    "oligarchie": (
        "régime politique dans lequel le pouvoir est détenu par un petit groupe de personnes "
        "(du grec oligos, « peu nombreux », et arkhê, « commandement »)"
    ),
    "theocratie": (
        "régime politique dans lequel l'autorité est considérée comme émanant de Dieu et exercée "
        "au nom de la divinité par une autorité religieuse (du grec theos, « Dieu », et kratos, « pouvoir »)"
    ),
    "anarchie": (
        "absence de gouvernement et d'autorité politique ; doctrine prônant une société organisée "
        "sans État (du grec an-, « sans », et arkhê, « commandement »)"
    ),
}


def systemes():
    """Tuple trié des systèmes politiques du référentiel (clés sans accents)."""
    return tuple(sorted(_DEFINITIONS))


def definition(systeme):
    """Définition établie d'un système politique. Système hors référentiel -> ValueError."""
    cle = _normalise(systeme)
    if cle not in _DEFINITIONS:
        raise ValueError(f"système hors référentiel : {systeme!r}")
    return _DEFINITIONS[cle]


# ── CLASSIFICATION PAR CRITÈRES ÉTABLIS ──
SUFFRAGES = ("universel", "restreint", "aucun")
SEUIL_PETIT_GROUPE = 40  # convention : « les quelques-uns » (oligarchie) vs un corps nombreux


def classe_par_criteres(nb_gouvernants, est_hereditaire, suffrage):
    """
    Classe un régime selon la typologie classique (nombre de gouvernants × dévolution × suffrage).
      • héréditaire + un seul gouvernant            -> 'monarchie'  (prioritaire ; cas de la monarchie constitutionnelle)
      • suffrage universel (non héréditaire)         -> 'democratie' (le pouvoir au peuple)
      • petit groupe (2..SEUIL, non universel)       -> 'oligarchie'
      • un seul, non héréditaire, sans suffrage      -> 'dictature'
    Type invalide, suffrage hors référentiel ou combinaison non déterminée par les critères -> ValueError.
    """
    if isinstance(nb_gouvernants, bool) or not isinstance(nb_gouvernants, int):
        raise ValueError("nb_gouvernants doit être un entier")
    if nb_gouvernants < 1:
        raise ValueError("nb_gouvernants doit être >= 1")
    if not isinstance(est_hereditaire, bool):
        raise ValueError("est_hereditaire doit être un booléen")
    if not isinstance(suffrage, str) or suffrage not in SUFFRAGES:
        raise ValueError(f"suffrage hors référentiel : {suffrage!r} (attendus : {SUFFRAGES})")

    if est_hereditaire and nb_gouvernants == 1:
        return "monarchie"
    if (not est_hereditaire) and suffrage == "universel":
        return "democratie"
    if (not est_hereditaire) and suffrage != "universel" and 2 <= nb_gouvernants <= SEUIL_PETIT_GROUPE:
        return "oligarchie"
    if (not est_hereditaire) and suffrage == "aucun" and nb_gouvernants == 1:
        return "dictature"
    raise ValueError("combinaison non déterminée par les critères établis")


# ── SÉPARATION DES POUVOIRS (Montesquieu) ──
_POUVOIRS = ("executif", "legislatif", "judiciaire")
_ATTRIBUTIONS = {
    "executif": "applique et fait exécuter les lois ; conduit la politique de l'État",
    "legislatif": "délibère, propose et vote les lois",
    "judiciaire": "interprète et applique les lois, tranche les litiges et sanctionne les infractions",
}


def separation_pouvoirs():
    """Les trois pouvoirs de l'État selon Montesquieu, dans l'ordre canonique."""
    return _POUVOIRS


def attribution_pouvoir(pouvoir):
    """Attribution établie d'un des trois pouvoirs. Pouvoir hors référentiel -> ValueError."""
    cle = _normalise(pouvoir)
    if cle not in _ATTRIBUTIONS:
        raise ValueError(f"pouvoir hors référentiel : {pouvoir!r} (attendus : {_POUVOIRS})")
    return _ATTRIBUTIONS[cle]


if __name__ == "__main__":
    print("Systèmes :", systemes())
    for s in systemes():
        print(f"  {s} : {definition(s)}")
    print("\nClassification par critères :")
    for args in [(1, True, "aucun"), (500, False, "universel"), (3, False, "restreint"), (1, False, "aucun")]:
        print(f"  classe_par_criteres{args} -> {classe_par_criteres(*args)}")
    print("\nSéparation des pouvoirs (Montesquieu) :")
    for p in separation_pouvoirs():
        print(f"  {p} : {attribution_pouvoir(p)}")
