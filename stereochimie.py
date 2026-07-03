"""stereochimie.py — Dénombrement de stéréoisomères et relation entre configurations.

MÉCANISME EXACT (faits établis, FAUX=0) :

  Règle de Le Bel–van't Hoff (cas SANS symétrie interne, n centres chiraux
  indépendants, AUCUN composé méso) :
      - nombre de stéréoisomères           = 2^n
      - nombre de paires d'énantiomères    = 2^(n-1)   (n >= 1 ; 0 pour n = 0)
      - chaque stéréoisomère est chiral => possède exactement 1 énantiomère ;
        nombre de formes optiquement actives (= stéréoisomères ayant un
        énantiomère) = 2^n  (0 pour n = 0, molécule achirale unique).

  Relation entre deux configurations données comme suites de descripteurs
  R/S (une lettre par centre stéréogène, même longueur) :
      - 'identiques'      : configurations égales en tout centre ;
      - 'enantiomeres'    : configurations opposées en TOUS les centres
                            (image miroir non superposable) ;
      - 'diastereomeres'  : configurations différentes mais PAS toutes
                            inversées (diffèrent sur certains centres seulement).

Fonctions pures, déterministes, stdlib uniquement.
ABSTENTION STRUCTURELLE : entrée invalide (n < 0, descripteur ≠ R/S,
longueurs différentes, suite vide) -> ValueError. Aucun faux positif.
"""

_OPPOSE = {"R": "S", "S": "R"}


def _verifie_n(n):
    """Valide un nombre de centres chiraux : entier >= 0 (bool refusé)."""
    if isinstance(n, bool) or not isinstance(n, int):
        raise ValueError(f"nombre de centres chiraux entier attendu, reçu {n!r}")
    if n < 0:
        raise ValueError(f"nombre de centres chiraux négatif : {n}")
    return n


def _parse_config(c):
    """Normalise une configuration en tuple de descripteurs 'R'/'S'.

    Accepte une chaîne ('RR', 'rs') ou une suite (['R', 'S'], ('R',)).
    ValueError si vide ou si un élément n'est pas R/S.
    """
    if isinstance(c, str):
        elements = list(c)
    elif isinstance(c, (list, tuple)):
        elements = list(c)
    else:
        raise ValueError(f"configuration : chaîne ou suite R/S attendue, reçu {c!r}")
    if not elements:
        raise ValueError("configuration vide : aucun centre stéréogène")
    out = []
    for e in elements:
        if not isinstance(e, str):
            raise ValueError(f"descripteur non textuel : {e!r}")
        d = e.upper()
        if d not in _OPPOSE:
            raise ValueError(f"descripteur invalide : {e!r} (attendu R ou S)")
        out.append(d)
    return tuple(out)


def nombre_stereoisomeres(n_centres_chiraux):
    """2^n stéréoisomères pour n centres chiraux indépendants (sans symétrie)."""
    n = _verifie_n(n_centres_chiraux)
    return 2 ** n


def paires_enantiomeres(n_centres_chiraux):
    """2^(n-1) paires d'énantiomères (0 si n = 0 : pas de paire)."""
    n = _verifie_n(n_centres_chiraux)
    if n == 0:
        return 0
    return 2 ** (n - 1)


def nombre_enantiomeres(n_centres_chiraux):
    """Nombre de stéréoisomères optiquement actifs (ayant un énantiomère).

    Sans symétrie/composé méso, les 2^n stéréoisomères sont tous chiraux et
    s'apparient en énantiomères : il y en a donc 2^n (0 pour la molécule
    achirale unique à n = 0).
    """
    n = _verifie_n(n_centres_chiraux)
    if n == 0:
        return 0
    return 2 ** n


def classe_relation(config1, config2):
    """Classe la relation stéréochimique entre deux configurations R/S.

    -> 'identiques' | 'enantiomeres' | 'diastereomeres'
    ValueError si descripteurs invalides ou longueurs différentes.
    """
    t1 = _parse_config(config1)
    t2 = _parse_config(config2)
    if len(t1) != len(t2):
        raise ValueError(
            f"longueurs de configuration différentes : {len(t1)} vs {len(t2)}"
        )
    n = len(t1)
    inverses = sum(1 for a, b in zip(t1, t2) if a != b)
    if inverses == 0:
        return "identiques"
    if inverses == n:
        return "enantiomeres"
    return "diastereomeres"
