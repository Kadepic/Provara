"""
JOURNALISME (DÉONTOLOGIE) — catalogue des devoirs établis du/de la journaliste.

Posture (la réalité juge, jamais un faux) :
  • Ce sont des RÈGLES ÉTABLIES, sourcées par les chartes de référence — pas un avis inventé :
        - Charte de Munich (1971) — « Déclaration des devoirs et des droits des journalistes »,
          adoptée par les syndicats européens, annexée à de nombreuses conventions collectives ;
        - SPJ Code of Ethics (Society of Professional Journalists) :
          « Seek Truth and Report It », « Minimize Harm », « Act Independently »,
          « Be Accountable and Transparent ».
  • principe(nom) ne reconnaît QUE les 7 principes de la charte (closed-set) ; tout autre nom -> ValueError.
  • respecte_deontologie(pratique) ne juge QUE des pratiques cataloguées sans ambiguïté ; toute pratique
    hors catalogue -> ValueError (ABSTENTION). Jamais un verdict inventé sur une pratique inconnue.
  • Fonctions PURES déterministes.

CATALOGUE DES PRINCIPES (devoirs) :
  - verification/exactitude    : respecter la vérité ; vérifier/recouper avant de publier      (Munich d.1 ; SPJ)
  - separation_faits_opinions  : distinguer l'information (faits) du commentaire (opinion)      (codes de presse)
  - protection_sources         : secret professionnel ; ne pas divulguer ses sources           (Munich d.7)
  - droit_de_reponse           : laisser répondre la personne mise en cause (contradictoire)    (déontologie/loi)
  - presomption_innocence      : ne pas présenter comme coupable avant condamnation             (déontologie/loi)
  - independance               : refuser les pressions ; ne pas confondre journalisme/publicité (Munich d.8 ; SPJ)
  - rectification              : corriger toute information publiée qui se révèle inexacte       (Munich d.6 ; SPJ)

CAS DE RÉFÉRENCE (jugés par respecte_deontologie / principe_concerne) :
  - vérifier avant de publier            -> conforme  (principe verification/exactitude)
  - publier sans vérifier                -> violation (principe verification/exactitude)
  - séparer faits et commentaires        -> conforme  (principe separation_faits_opinions)
  - protéger une source                  -> conforme  (principe protection_sources)
  - révéler une source confidentielle    -> violation (principe protection_sources)

SOUNDNESS (vérifiée en adverse par valide_journalisme_deontologie.py) :
  - principe hors charte                  -> ValueError ;
  - pratique hors catalogue / ambiguë     -> ValueError ;
  - argument non-str (booléen inclus)      -> ValueError ;
  - déterministe ; conservateur (abstention tolérée, faux verdict interdit).
"""
from __future__ import annotations

import unicodedata

SOURCE = ("déontologie journalistique — Charte de Munich (1971, Déclaration des devoirs et des droits "
          "des journalistes) ; SPJ Code of Ethics (Society of Professional Journalists)")

# ── 1) PRINCIPES (devoirs) : description EXACTE du devoir, closed-set de 7 ──
_PRINCIPES = {
    "verification/exactitude":
        "Respecter la vérité : vérifier et recouper l'information avant de la publier ; ne diffuser que "
        "des faits dont l'origine est connue, ne pas supprimer d'information essentielle "
        "(Charte de Munich, devoir 1 ; SPJ « Seek Truth and Report It »).",
    "separation_faits_opinions":
        "Distinguer clairement l'information (les faits) du commentaire (l'opinion) ; ne pas présenter "
        "une opinion ou une rumeur comme un fait établi (séparation des faits et des commentaires).",
    "protection_sources":
        "Garder le secret professionnel et ne pas divulguer la source des informations obtenues "
        "confidentiellement (Charte de Munich, devoir 7 ; protection des sources).",
    "droit_de_reponse":
        "Respecter le contradictoire : donner à la personne mise en cause la possibilité de répondre "
        "(droit de réponse) et présenter sa version.",
    "presomption_innocence":
        "Respecter la présomption d'innocence : ne pas présenter ni désigner comme coupable une personne "
        "avant sa condamnation définitive.",
    "independance":
        "Préserver son indépendance : refuser les pressions (politiques, commerciales, des annonceurs) et "
        "ne jamais confondre le métier de journaliste avec la publicité ou la propagande "
        "(Charte de Munich, devoir 8 ; SPJ « Act Independently »).",
    "rectification":
        "Rectifier rapidement toute information publiée qui se révèle inexacte ; rendre des comptes et "
        "corriger ses erreurs (Charte de Munich, devoir 6 ; SPJ « Be Accountable and Transparent »).",
}

# ── 2) PRATIQUES cataloguées : clé canonique -> (statut, principe concerné) ──
#    statut ∈ {'conforme', 'violation'} ; principe ∈ clés de _PRINCIPES.
#    Chaque entrée : (clé_canonique, statut, principe, [alias en langage naturel]).
_DEF = [
    # verification / exactitude
    ("verifier_avant_publier", "conforme", "verification/exactitude",
        ["verifier avant publier", "verifier avant de publier",
         "verifier l'information avant publication", "recouper avant de publier",
         "recouper les sources avant publication"]),
    ("publier_sans_verifier", "violation", "verification/exactitude",
        ["publier sans verifier", "publier sans verification", "publier une information sans la verifier",
         "diffuser sans verifier", "publier une rumeur sans verification"]),
    # separation faits / opinions
    ("separer_faits_et_commentaires", "conforme", "separation_faits_opinions",
        ["separer faits et commentaires", "separer les faits et les commentaires",
         "separer faits et opinions", "distinguer faits et opinions",
         "distinguer l'information du commentaire"]),
    ("meler_faits_et_opinions", "violation", "separation_faits_opinions",
        ["meler faits et opinions", "presenter une opinion comme un fait",
         "confondre faits et commentaires", "faire passer un commentaire pour une information"]),
    # protection des sources
    ("proteger_une_source", "conforme", "protection_sources",
        ["proteger une source", "proteger ses sources", "proteger une source confidentielle",
         "garder le secret des sources", "respecter le secret des sources"]),
    ("reveler_source_confidentielle", "violation", "protection_sources",
        ["reveler une source confidentielle", "reveler une source", "reveler ses sources",
         "divulguer une source", "divulguer ses sources", "devoiler une source confidentielle"]),
    # droit de reponse
    ("accorder_droit_de_reponse", "conforme", "droit_de_reponse",
        ["accorder un droit de reponse", "accorder le droit de reponse",
         "publier un droit de reponse", "donner la parole a la personne mise en cause"]),
    ("refuser_droit_de_reponse", "violation", "droit_de_reponse",
        ["refuser un droit de reponse", "refuser le droit de reponse",
         "refuser de publier la reponse de la personne mise en cause"]),
    # presomption d'innocence
    ("respecter_presomption_innocence", "conforme", "presomption_innocence",
        ["respecter la presomption d'innocence", "respecter la presomption d innocence",
         "presenter un suspect comme presume innocent"]),
    ("designer_coupable_avant_jugement", "violation", "presomption_innocence",
        ["designer un coupable avant jugement", "presenter un suspect comme coupable",
         "presenter un accuse comme coupable avant condamnation", "violer la presomption d'innocence"]),
    # independance
    ("refuser_pression_annonceur", "conforme", "independance",
        ["refuser la pression d'un annonceur", "refuser une pression commerciale",
         "preserver son independance", "refuser une consigne du proprietaire"]),
    ("ceder_pression_annonceur", "violation", "independance",
        ["ceder a la pression d'un annonceur", "publier un publireportage deguise",
         "confondre journalisme et publicite", "ecrire un article sur commande d'un annonceur"]),
    # rectification
    ("rectifier_information_inexacte", "conforme", "rectification",
        ["rectifier une information inexacte", "publier un rectificatif", "corriger une erreur publiee",
         "rectifier une erreur publiee"]),
    ("refuser_de_rectifier", "violation", "rectification",
        ["refuser de rectifier", "refuser de corriger une erreur", "laisser une erreur sans correction",
         "ne pas corriger une information inexacte"]),
]


def _strip_accents(s: str) -> str:
    return "".join(c for c in unicodedata.normalize("NFD", s) if unicodedata.category(c) != "Mn")


def _norm(x) -> str:
    """Normalise une chaîne (minuscules, sans accents, espaces compactés). Non-str / booléen -> ValueError."""
    if isinstance(x, bool) or not isinstance(x, str):
        raise ValueError(f"argument non textuel : {x!r}")
    s = _strip_accents(x).lower().replace("’", "'").replace("`", "'")
    return " ".join(s.split()).strip()


# Construction des index (closed-set) : pratique normalisée -> (statut, principe).
_PRATIQUES: dict[str, tuple[str, str]] = {}
_ALIAS: dict[str, str] = {}
for _cle, _statut, _princ, _aliases in _DEF:
    assert _statut in ("conforme", "violation")
    assert _princ in _PRINCIPES
    _PRATIQUES[_cle] = (_statut, _princ)
    for _a in [_cle] + list(_aliases):
        _na = _norm(_a)
        # garde anti-collision : un alias ne peut pointer vers deux pratiques différentes
        assert _na not in _ALIAS or _ALIAS[_na] == _cle, f"collision d'alias : {_na!r}"
        _ALIAS[_na] = _cle


def liste_principes() -> tuple:
    """Les 7 principes (devoirs) de la charte, dans l'ordre canonique (fait)."""
    return tuple(_PRINCIPES.keys())


def principe(nom) -> str:
    """Description EXACTE du devoir `nom` (closed-set de 7). Principe hors charte -> ValueError."""
    if isinstance(nom, bool) or not isinstance(nom, str):
        raise ValueError(f"nom de principe non textuel : {nom!r}")
    if nom not in _PRINCIPES:
        raise ValueError(f"principe hors charte : {nom!r}")
    return _PRINCIPES[nom]


def _resout(pratique) -> str:
    """Clé canonique de la pratique. Hors catalogue -> ValueError (abstention)."""
    cle = _ALIAS.get(_norm(pratique))
    if cle is None:
        raise ValueError(f"pratique hors catalogue (abstention) : {pratique!r}")
    return cle


def respecte_deontologie(pratique) -> str:
    """Verdict déontologique : 'conforme' ou 'violation'. Pratique hors catalogue -> ValueError.

    Ex. : 'publier sans vérifier' -> 'violation' ; 'protéger une source' -> 'conforme' ;
          'révéler une source confidentielle' -> 'violation'."""
    return _PRATIQUES[_resout(pratique)][0]


def est_conforme(pratique) -> bool:
    """True si la pratique est conforme, False si elle est une violation. Hors catalogue -> ValueError."""
    return respecte_deontologie(pratique) == "conforme"


def principe_concerne(pratique) -> str:
    """Principe (devoir) mis en jeu par la pratique. Hors catalogue -> ValueError.

    Ex. : 'vérifier avant publier' -> 'verification/exactitude' ;
          'séparer faits et commentaires' -> 'separation_faits_opinions'."""
    return _PRATIQUES[_resout(pratique)][1]


def evalue(pratique) -> tuple:
    """(statut, principe) pour une pratique cataloguée. Hors catalogue -> ValueError."""
    statut, princ = _PRATIQUES[_resout(pratique)]
    return (statut, princ)
