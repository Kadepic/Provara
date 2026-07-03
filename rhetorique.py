"""
RHÉTORIQUE / PERSUASION (techniques) — CATALOGUE ÉTABLI (consensus, source : Aristote « Rhétorique » + traités de
figures de style).

Posture FAUX=0 (même invariant que les autres catalogues du harnais : la réalité/source juge, jamais un faux) :
  • Les trois MODES de persuasion (ethos / pathos / logos) et leur définition sont le consensus classique
    établi par Aristote (Rhétorique, livre I, 1356a) — fait SOURCÉ, pas une opinion.
  • Les FIGURES de style (métaphore, anaphore, hyperbole, litote, antithèse, chiasme) ont une définition
    établie en rhétorique/stylistique — fait SOURCÉ.
  • Tout terme HORS de ces référentiels fermés -> ValueError (abstention). On n'INVENTE jamais une définition.
  • `identifie_mode` ne classe QUE des descriptions dont le marqueur appartient à une table fermée de
    correspondances établies (appel à l'autorité -> ethos, appel à la peur/aux émotions -> pathos, argument
    chiffré/preuve logique -> logos). Description sans marqueur reconnu -> ValueError (jamais de devinette).

Déterministe, fonctions pures. Conservateur : faux négatif (abstention) toléré, faux POSITIF interdit.
"""
from __future__ import annotations

import unicodedata


# ── Normalisation (insensible à la casse / aux accents / aux espaces) ───────────────────────────────────────────
def _norme(t: str) -> str:
    if not isinstance(t, str):
        raise ValueError("terme non textuel")
    s = unicodedata.normalize("NFD", t.strip().lower())
    s = "".join(c for c in s if unicodedata.category(c) != "Mn")  # retire les diacritiques
    # ponctuation (apostrophes, tirets…) -> espace, pour que « l'autorité » == « l autorite »
    s = "".join(c if (c.isalnum() or c.isspace()) else " " for c in s)
    return " ".join(s.split())


# ── 1) MODES DE PERSUASION — les trois moyens d'Aristote (Rhétorique I, 1356a) ──────────────────────────────────
_MODES = {
    "ethos": (
        "Ethos : moyen de persuasion fondé sur la CRÉDIBILITÉ et le caractère de l'orateur "
        "(autorité, honnêteté, compétence perçues) ; on adhère parce qu'on fait confiance à celui qui parle."
    ),
    "pathos": (
        "Pathos : moyen de persuasion fondé sur les ÉMOTIONS de l'auditoire "
        "(peur, pitié, colère, espoir, indignation) ; on adhère parce qu'on est ému."
    ),
    "logos": (
        "Logos : moyen de persuasion fondé sur la LOGIQUE et la RAISON "
        "(arguments, preuves, chiffres, déductions, faits) ; on adhère parce que le raisonnement convainc."
    ),
}


def mode_persuasion(nom: str) -> str:
    """Définition d'un des trois modes d'Aristote. Terme hors catalogue -> ValueError."""
    cle = _norme(nom)
    if cle not in _MODES:
        raise ValueError(f"mode de persuasion hors catalogue : {nom!r}")
    return _MODES[cle]


def modes() -> tuple:
    """Les trois modes établis, ordre canonique."""
    return ("ethos", "pathos", "logos")


# ── 2) FIGURES DE STYLE — définitions établies (stylistique / rhétorique) ────────────────────────────────────────
_FIGURES = {
    "metaphore": (
        "Métaphore : figure d'analogie qui désigne une chose par le nom d'une autre, sans outil de comparaison "
        "(« cet homme est un lion »)."
    ),
    "anaphore": (
        "Anaphore : figure de répétition d'un même mot ou groupe de mots EN DÉBUT de propositions ou de vers "
        "successifs (« Mon bras… Mon bras… »)."
    ),
    "hyperbole": (
        "Hyperbole : figure d'EXAGÉRATION qui amplifie la réalité pour frapper l'esprit "
        "(« mourir de rire », « un géant »)."
    ),
    "litote": (
        "Litote : figure d'ATTÉNUATION qui dit moins pour suggérer plus, souvent par négation du contraire "
        "(« ce n'est pas mauvais » pour « c'est très bon »)."
    ),
    "antithese": (
        "Antithèse : figure d'OPPOSITION qui rapproche deux termes ou idées contraires dans une même phrase "
        "(« ici tout n'est qu'ordre et beauté »… opposé au désordre)."
    ),
    "chiasme": (
        "Chiasme : figure de construction croisée en miroir, sur le schéma AB / BA "
        "(« il faut manger pour vivre et non vivre pour manger »)."
    ),
}


def figure_style(nom: str) -> str:
    """Définition établie d'une figure de style. Terme hors catalogue -> ValueError."""
    cle = _norme(nom)
    if cle not in _FIGURES:
        raise ValueError(f"figure de style hors catalogue : {nom!r}")
    return _FIGURES[cle]


def figures() -> tuple:
    """Les figures cataloguées, ordre canonique."""
    return ("métaphore", "anaphore", "hyperbole", "litote", "antithèse", "chiasme")


# ── 3) IDENTIFICATION DU MODE — table FERMÉE de marqueurs établis -> mode ─────────────────────────────────────────
# Chaque marqueur est un indice NON ambigu rattachant une description à l'un des trois modes (consensus rhétorique).
_MARQUEURS = {
    # ethos — crédibilité / autorité de la source
    "appel a l autorite": "ethos",
    "argument d autorite": "ethos",
    "appel a l expert": "ethos",
    "credibilite de l orateur": "ethos",
    "credibilite de la source": "ethos",
    "experience personnelle de l orateur": "ethos",
    "reputation": "ethos",
    # pathos — émotions de l'auditoire
    "appel a la peur": "pathos",
    "appel a l emotion": "pathos",
    "appel aux emotions": "pathos",
    "appel a la pitie": "pathos",
    "appel a la colere": "pathos",
    "appel a la compassion": "pathos",
    "susciter la peur": "pathos",
    "susciter l emotion": "pathos",
    # logos — logique / raison / preuve
    "argument chiffre": "logos",
    "argument logique": "logos",
    "preuve statistique": "logos",
    "donnees chiffrees": "logos",
    "raisonnement deductif": "logos",
    "appel a la raison": "logos",
    "appel a la logique": "logos",
    "preuve factuelle": "logos",
}


def identifie_mode(description: str) -> str:
    """
    Classe une description dans un mode (ethos/pathos/logos) UNIQUEMENT si elle contient un marqueur établi
    de la table fermée. Aucun marqueur reconnu -> ValueError (jamais de devinette).
    Ambiguïté (marqueurs de modes différents) -> ValueError.
    """
    d = _norme(description)
    trouves = {mode for marq, mode in _MARQUEURS.items() if marq in d}
    if len(trouves) == 1:
        return trouves.pop()
    if len(trouves) == 0:
        raise ValueError(f"description sans marqueur de mode reconnu : {description!r}")
    raise ValueError(f"description ambiguë (plusieurs modes) : {description!r}")
