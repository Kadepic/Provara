"""
bibliotheconomie.py — Bibliothéconomie / sciences de l'information.

Catalogues et mécanismes ÉTABLIS (faits sourcés/consensus), fonctions pures déterministes, FAUX=0 :

  • classe_dewey(numero_centaine) : classification décimale de Dewey (Dewey Decimal
    Classification, DDC). Les dix classes principales (centaines) :
        000 informatique / généralités        500 sciences (naturelles, maths)
        100 philosophie & psychologie          600 techniques (sciences appliquées)
        200 religion                           700 arts & loisirs
        300 sciences sociales                  800 littérature
        400 langues                            900 histoire & géographie
    SOUNDNESS : centaine hors {0,100,…,900} -> ValueError (jamais inventer une classe).

  • isbn_valide(isbn13) : vérifie la clé de contrôle ISBN-13 (norme ISO 2108).
    Somme pondérée des 13 chiffres avec poids alternés 1,3,1,3,…,1,3 ; le nombre
    est valide si (somme mod 10) == 0. Le 13ᵉ chiffre est la clé de contrôle.
    SOUNDNESS : longueur != 13 (après retrait des tirets/espaces), ou caractère
    non numérique -> ValueError (jamais deviner).

Aucune donnée n'est inventée : Dewey est une taxonomie publiée, ISBN-13 un
algorithme normalisé. Hors référentiel -> abstention (ValueError).
"""

# ── Classification décimale de Dewey : les 10 classes principales (centaines) ──
_DEWEY = {
    0:   "informatique/généralités",
    100: "philosophie",
    200: "religion",
    300: "sciences sociales",
    400: "langues",
    500: "sciences",
    600: "techniques",
    700: "arts",
    800: "littérature",
    900: "histoire/géo",
}


def classes_dewey():
    """Renvoie le catalogue {centaine: libellé} (copie, non mutable de l'extérieur)."""
    return dict(_DEWEY)


def classe_dewey(numero_centaine):
    """
    Libellé de la classe principale Dewey pour une centaine (0,100,…,900).

    >>> classe_dewey(500)
    'sciences'
    >>> classe_dewey(800)
    'littérature'

    SOUNDNESS : centaine hors {0,100,…,900} -> ValueError.
    """
    if isinstance(numero_centaine, bool) or not isinstance(numero_centaine, int):
        raise ValueError(f"centaine Dewey doit être un entier, reçu {numero_centaine!r}")
    if numero_centaine not in _DEWEY:
        raise ValueError(
            f"centaine Dewey inconnue : {numero_centaine} "
            f"(attendu l'une de {sorted(_DEWEY)})"
        )
    return _DEWEY[numero_centaine]


def _normalise_isbn(isbn13):
    """Retire tirets et espaces ; renvoie la chaîne de chiffres brute (non validée)."""
    if isinstance(isbn13, bool):
        raise ValueError("ISBN doit être une chaîne ou une suite de chiffres, pas un booléen")
    if isinstance(isbn13, int):
        isbn13 = str(isbn13)
    if not isinstance(isbn13, str):
        raise ValueError(f"ISBN doit être une chaîne, reçu {type(isbn13).__name__}")
    return isbn13.replace("-", "").replace(" ", "")


def isbn_valide(isbn13):
    """
    Vrai si la clé de contrôle ISBN-13 est correcte (poids alternés 1,3 ; mod 10 == 0).

    >>> isbn_valide("978-0-306-40615-7")
    True

    SOUNDNESS : longueur != 13 (hors tirets/espaces) ou chiffre invalide -> ValueError.
    """
    chiffres = _normalise_isbn(isbn13)
    if len(chiffres) != 13:
        raise ValueError(f"ISBN-13 doit avoir 13 chiffres, reçu {len(chiffres)}")
    if not chiffres.isdigit():
        raise ValueError(f"ISBN-13 ne doit contenir que des chiffres, reçu {chiffres!r}")
    somme = 0
    for i, c in enumerate(chiffres):
        poids = 1 if i % 2 == 0 else 3
        somme += poids * int(c)
    return somme % 10 == 0
