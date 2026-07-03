"""
BRAILLE — noyau BORNÉ de l'écriture tactile (convention FIXE, bijective), pur stdlib (2026-07-02).

POURQUOI (sujet borné B-CONV « Braille / écritures tactiles ») : le braille est une CONVENTION fermée et bijective —
chaque lettre correspond à une combinaison FIXE de points dans une cellule 6 points. La réalité (la norme) fixe la
réponse ; c'est vérifiable et réversible. On code la table canonique (alphabet latin de base, grade 1, lettre à
lettre) + le mapping Unicode (bloc Braille Patterns U+2800..U+28FF).

FAUX=0 — ce que ce module GARANTIT, et ce qu'il ne prétend PAS :
  • Bijection EXACTE lettre <-> points <-> caractère Unicode : `texte_vers_braille` puis `braille_vers_texte` rend le
    texte d'origine (round-trip prouvé) sur le domaine supporté.
  • Domaine EXPLICITE : lettres a–z + espace (grade 1). Tout caractère hors domaine -> ValueError (jamais deviné) —
    on n'invente pas une cellule pour un caractère non conventionné (ponctuation avancée, contractions grade 2 exclues).
  • Numérotation des points selon la convention (colonnes : 1-2-3 à gauche, 4-5-6 à droite) ; le bit Unicode d'un
    point i est 1<<(i-1) (spec Unicode) — le validateur re-dérive.
  Ce module ne prétend PAS couvrir le braille intégral (grade 2 contracté, notations mathématique/musicale, langues à
  signes spéciaux) : il garantit l'alphabet de base EXACT et réversible. Souverain, offline, stdlib pur, déterministe.
"""
from __future__ import annotations

_BASE = 0x2800          # début du bloc Unicode Braille Patterns

# Table canonique : lettre -> points allumés (convention Louis Braille, alphabet latin de base).
# a–j (points hauts 1245), k–t = a–j + point 3, u–z = a–j + points 3+6 (w est l'exception historique = 2456).
_LETTRE_POINTS = {
    "a": (1,), "b": (1, 2), "c": (1, 4), "d": (1, 4, 5), "e": (1, 5),
    "f": (1, 2, 4), "g": (1, 2, 4, 5), "h": (1, 2, 5), "i": (2, 4), "j": (2, 4, 5),
    "k": (1, 3), "l": (1, 2, 3), "m": (1, 3, 4), "n": (1, 3, 4, 5), "o": (1, 3, 5),
    "p": (1, 2, 3, 4), "q": (1, 2, 3, 4, 5), "r": (1, 2, 3, 5), "s": (2, 3, 4), "t": (2, 3, 4, 5),
    "u": (1, 3, 6), "v": (1, 2, 3, 6), "w": (2, 4, 5, 6), "x": (1, 3, 4, 6),
    "y": (1, 3, 4, 5, 6), "z": (1, 3, 5, 6),
    " ": (),
}
_POINTS_LETTRE = {v: k for k, v in _LETTRE_POINTS.items()}


def _masque(points) -> int:
    m = 0
    for p in points:
        if not isinstance(p, int) or not (1 <= p <= 8):
            raise ValueError(f"numéro de point invalide : {p!r} (1..8)")
        m |= 1 << (p - 1)
    return m


def lettre_vers_points(c: str) -> tuple:
    """Points allumés d'une lettre (a–z ou espace). Hors domaine -> ValueError."""
    if not isinstance(c, str) or len(c) != 1:
        raise ValueError("un caractère unique attendu")
    cl = c.lower()
    if cl not in _LETTRE_POINTS:
        raise ValueError(f"caractère hors alphabet braille de base : {c!r}")
    return _LETTRE_POINTS[cl]


def points_vers_lettre(points) -> str:
    """Inverse : combinaison de points -> lettre. Combinaison inconnue -> ValueError."""
    cle = tuple(sorted(set(points)))
    if cle not in _POINTS_LETTRE:
        raise ValueError(f"combinaison de points sans lettre conventionnée : {cle}")
    return _POINTS_LETTRE[cle]


def lettre_vers_unicode(c: str) -> str:
    """Caractère Unicode Braille correspondant (U+2800 + masque des points)."""
    return chr(_BASE + _masque(lettre_vers_points(c)))


def unicode_vers_lettre(ch: str) -> str:
    """Inverse : un caractère Braille Unicode -> lettre. Hors bloc/hors table -> ValueError."""
    if not isinstance(ch, str) or len(ch) != 1:
        raise ValueError("un caractère unique attendu")
    code = ord(ch)
    if not (_BASE <= code <= 0x28FF):
        raise ValueError(f"hors du bloc Braille Unicode : {ch!r}")
    masque = code - _BASE
    points = tuple(i for i in range(1, 9) if masque & (1 << (i - 1)))
    return points_vers_lettre(points)


def texte_vers_braille(texte: str) -> str:
    """Transcrit un texte (lettres a–z + espace) en caractères Braille Unicode. Caractère hors domaine -> ValueError."""
    if not isinstance(texte, str):
        raise ValueError("texte : str attendu")
    return "".join(lettre_vers_unicode(c) for c in texte)


def braille_vers_texte(braille: str) -> str:
    """Inverse : chaîne de caractères Braille Unicode -> texte (minuscules). Round-trip de texte_vers_braille."""
    if not isinstance(braille, str):
        raise ValueError("braille : str attendu")
    return "".join(unicode_vers_lettre(c) for c in braille)


def cellule_ascii(c: str) -> str:
    """Rendu visuel 2×3 d'une cellule (● point allumé, · éteint) — pour inspection. Convention 1-4 / 2-5 / 3-6."""
    pts = set(lettre_vers_points(c))
    p = lambda n: "●" if n in pts else "·"
    return f"{p(1)}{p(4)}\n{p(2)}{p(5)}\n{p(3)}{p(6)}"
