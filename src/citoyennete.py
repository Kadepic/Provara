"""
CITOYENNETÉ (DROITS ET DEVOIRS) — catalogue ÉTABLI, pas une invention.

Posture FAUX=0 (la réalité juridique juge, jamais un faux) :
  • Le catalogue est un référentiel CIVIQUE ÉTABLI (démocratie / France). Chaque entrée est un fait sourcé du droit
    constitutionnel français : Déclaration des droits de l'homme et du citoyen de 1789 (DDHC), Préambule de la
    Constitution de 1946 (droits « particulièrement nécessaires à notre temps » = droits sociaux), Constitution de
    1958 et son bloc de constitutionnalité.
  • La CATÉGORISATION (droit civil / politique / social / devoir) suit la typologie classique des droits du citoyen.
  • Toute entrée HORS du catalogue -> ValueError (abstention) : on ne devine JAMAIS la nature d'un élément inconnu.
  • Déterministe, fonctions pures, aucune dépendance.

TYPOLOGIE (référentiel) :
  - droit_civil      : libertés individuelles / civiles (DDHC 1789) — liberté d'expression, propriété, sûreté…
  - droit_politique  : participation à la vie de la cité — voter, être éligible, adhérer à un parti…
  - droit_social     : droits-créances (Préambule 1946) — éducation, santé, travail, grève…
  - devoir           : obligations du citoyen — payer l'impôt (DDHC art. 13), respecter la loi, jury, défense…

age_majorite_civique() = 18 ans : FAIT (France — loi du 5 juillet 1974 abaissant la majorité civile, civique et
électorale de 21 à 18 ans ; art. 414 du Code civil ; art. L2 du Code électoral pour le droit de vote).
"""
from __future__ import annotations

import unicodedata

# Catégories valides du référentiel (les trois familles de droits + les devoirs).
DROIT_CIVIL = "droit_civil"
DROIT_POLITIQUE = "droit_politique"
DROIT_SOCIAL = "droit_social"
DEVOIR = "devoir"

CATEGORIES = (DROIT_CIVIL, DROIT_POLITIQUE, DROIT_SOCIAL, DEVOIR)
_FAMILLES_DROIT = (DROIT_CIVIL, DROIT_POLITIQUE, DROIT_SOCIAL)

SOURCE = "DDHC 1789 ; Préambule 1946 ; Constitution 1958 (bloc de constitutionnalité, France)"

# ── CATALOGUE ÉTABLI ────────────────────────────────────────────────────────────────────────────────────────────
# Libellé canonique (accentué) -> catégorie. Les libellés multiples pointant vers la MÊME catégorie sont des
# synonymes établis (ex. « voter » et « droit de vote »). Aucun libellé ambigu (ex. « défense » seule, qui pourrait
# désigner les « droits de la défense » au procès) n'est admis : on n'inscrit que la forme non équivoque.
_CATALOGUE = {
    # — DROITS CIVILS — libertés fondamentales (DDHC 1789, art. 2/4/10/11/17 ; Constitution 1958).
    "liberté d'expression": DROIT_CIVIL,
    "liberté d'opinion": DROIT_CIVIL,
    "liberté de conscience": DROIT_CIVIL,
    "liberté de religion": DROIT_CIVIL,
    "liberté de culte": DROIT_CIVIL,
    "liberté de la presse": DROIT_CIVIL,
    "liberté de réunion": DROIT_CIVIL,
    "liberté d'association": DROIT_CIVIL,
    "liberté de circulation": DROIT_CIVIL,
    "droit de propriété": DROIT_CIVIL,
    "propriété": DROIT_CIVIL,
    "sûreté": DROIT_CIVIL,
    "présomption d'innocence": DROIT_CIVIL,
    "inviolabilité du domicile": DROIT_CIVIL,
    "secret de la correspondance": DROIT_CIVIL,
    "droit au respect de la vie privée": DROIT_CIVIL,
    "égalité devant la loi": DROIT_CIVIL,

    # — DROITS POLITIQUES — participation à la souveraineté (DDHC art. 6 ; art. 3 Constitution 1958).
    "droit de vote": DROIT_POLITIQUE,
    "voter": DROIT_POLITIQUE,
    "éligibilité": DROIT_POLITIQUE,
    "être élu": DROIT_POLITIQUE,
    "se présenter aux élections": DROIT_POLITIQUE,
    "adhérer à un parti politique": DROIT_POLITIQUE,
    "droit de pétition": DROIT_POLITIQUE,

    # — DROITS SOCIAUX — droits-créances (Préambule de la Constitution de 1946).
    "droit à l'éducation": DROIT_SOCIAL,
    "éducation": DROIT_SOCIAL,
    "droit à la santé": DROIT_SOCIAL,
    "protection de la santé": DROIT_SOCIAL,
    "santé": DROIT_SOCIAL,
    "droit au travail": DROIT_SOCIAL,
    "droit de grève": DROIT_SOCIAL,
    "droit syndical": DROIT_SOCIAL,
    "protection sociale": DROIT_SOCIAL,
    "droit au logement": DROIT_SOCIAL,

    # — DEVOIRS — obligations du citoyen.
    "payer l'impôt": DEVOIR,             # DDHC 1789, art. 13 (contribution commune).
    "payer les impôts": DEVOIR,
    "respecter la loi": DEVOIR,
    "respecter les droits d'autrui": DEVOIR,
    "être juré": DEVOIR,                 # juré d'assises — obligation civique.
    "jury": DEVOIR,
    "défense nationale": DEVOIR,         # Préambule 1946 : « concourir à la défense de la Nation ».
    "concourir à la défense nationale": DEVOIR,
}


def _norm(x) -> str:
    """Normalise un libellé : minuscule, apostrophes unifiées, accents pliés, espaces compactés.

    Lève ValueError si l'entrée n'est pas un texte non vide. Conservateur : on ne fait que canoniser la forme,
    jamais inférer le sens.
    """
    if not isinstance(x, str):
        raise ValueError(f"élément non textuel : {type(x).__name__}")
    s = x.strip().lower()
    for ap in ("’", "‘", "ʼ", "´", "`"):
        s = s.replace(ap, "'")
    s = " ".join(s.split())
    s = unicodedata.normalize("NFKD", s)
    s = "".join(c for c in s if not unicodedata.combining(c))
    if not s:
        raise ValueError("élément vide")
    return s


# Index normalisé construit une fois. Garde de SOUNDNESS du catalogue lui-même : si deux libellés se normalisaient
# vers la même forme avec des catégories DIFFÉRENTES, c'est une collision -> on refuse de charger (jamais d'ambiguïté
# silencieuse). Vérifié au chargement du module.
_INDEX: dict[str, str] = {}
for _lib, _cat in _CATALOGUE.items():
    _k = _norm(_lib)
    if _k in _INDEX and _INDEX[_k] != _cat:
        raise RuntimeError(f"collision de catalogue sur « {_k} » : {_INDEX[_k]} vs {_cat}")
    _INDEX[_k] = _cat


def categorie(element) -> str:
    """Catégorie civique d'un élément du catalogue (l'une de CATEGORIES).

    SOUNDNESS : élément hors catalogue (ou entrée invalide) -> ValueError. On n'invente jamais de catégorie.
    """
    k = _norm(element)
    if k not in _INDEX:
        raise ValueError(f"élément hors catalogue : {element!r}")
    return _INDEX[k]


def est_droit(x) -> bool:
    """True si l'élément est un DROIT (civil, politique ou social), False si c'est un devoir.

    SOUNDNESS : élément hors catalogue -> ValueError (jamais deviné).
    """
    return categorie(x) in _FAMILLES_DROIT


def est_devoir(x) -> bool:
    """True si l'élément est un DEVOIR, False si c'est un droit. Complément exact de est_droit sur le catalogue.

    SOUNDNESS : élément hors catalogue -> ValueError (jamais deviné).
    """
    return categorie(x) == DEVOIR


def age_majorite_civique() -> int:
    """Âge de la majorité civique en France : 18 ans (loi du 5 juillet 1974 ; art. 414 Code civil). FAIT."""
    return 18


def elements() -> tuple[str, ...]:
    """Libellés canoniques du catalogue (ordre stable d'insertion). Lecture seule."""
    return tuple(_CATALOGUE.keys())
