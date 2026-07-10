"""
CODES NORMALISÉS — ISO 4217 (monnaies), indicatifs téléphoniques E.164, ISBN, plaques (PARTIE XII, B-CONV).

`bibliotheconomie.py` ne couvrait qu'un des quatre codes cités par la carte (l'ISBN-13). Ce module ajoute
les trois autres, et l'ISBN-10 que personne ne validait.

Ces codes sont bornés par CONVENTION : ce sont des tables publiées (ISO, UIT, ISBN International Agency).
Rien n'est deviné ; ce qui n'est pas dans la table lève une erreur.

TROIS PIÈGES RÉELS, TRAITÉS EXPLICITEMENT (c'est là que se joue le FAUX=0) :

  1. **Toutes les monnaies n'ont pas deux décimales.** Le yen (JPY) et le won (KRW) n'en ont AUCUNE ; le
     dinar koweïtien (KWD), le dinar bahreïni (BHD) et le dinar tunisien (TND) en ont TROIS. Un module qui
     supposerait « 2 » partout produirait des montants faux d'un facteur 10 ou 100. `decimales(code)` est
     donc une donnée de la table, jamais une constante.

  2. **Un indicatif téléphonique n'identifie pas un pays.** Le +1 est partagé par les États-Unis, le Canada
     et une vingtaine de territoires ; le +7 par la Russie et le Kazakhstan. `pays_depuis_indicatif` rend
     donc un ENSEMBLE, et `pays_unique_depuis_indicatif` lève ValueError quand l'indicatif est partagé.
     Rendre « États-Unis » pour +1 serait un faux silencieux.

  3. **Les formats de plaque varient par pays et par époque.** Seule la France est embarquée (système SIV,
     depuis 2009 : « AA-123-AA »), avec la mention explicite que l'ancien système FNI (« 123 ABC 45 ») n'est
     plus attribué. Tout autre pays -> ValueError. Deviner un format de plaque serait gratuit et faux.

GARANTIES (vérifiées en adverse par `valide_codes_normalises.py`) :
  - code monnaie hors table, code numérique hors table, pays hors table -> ValueError ;
  - indicatif partagé -> `pays_unique_depuis_indicatif` lève ValueError (ensemble rendu par l'autre fonction) ;
  - ISBN de mauvaise longueur, à caractère illégal, ou à somme de contrôle fausse -> False (pas d'exception :
    c'est une VALIDATION) ; entrée non-str -> ValueError ;
  - plaque d'un pays non embarqué -> ValueError ;
  - INVARIANTS DURS vérifiés à l'import : codes numériques ISO 4217 tous distincts ; décimales dans {0,2,3} ;
    aucun code alphabétique de longueur ≠ 3 ; sinon RuntimeError ;
  - déterministe, pur, stdlib seule (`re`).
"""
from __future__ import annotations

import re

SOURCE = ("ISO 4217 (codes des monnaies) · UIT-T E.164 (indicatifs téléphoniques) · "
          "ISO 2108 (ISBN) · arrêté du 9 février 2009 (système d'immatriculation des véhicules, France)")

# ── ISO 4217 : (code numérique, nom français, nombre de décimales de la subdivision) ──────────────────────
_MONNAIES = {
    "EUR": (978, "euro", 2),
    "USD": (840, "dollar des États-Unis", 2),
    "GBP": (826, "livre sterling", 2),
    "JPY": (392, "yen", 0),          # PIÈGE : aucune subdivision
    "CHF": (756, "franc suisse", 2),
    "CAD": (124, "dollar canadien", 2),
    "AUD": (36, "dollar australien", 2),
    "CNY": (156, "yuan renminbi", 2),
    "INR": (356, "roupie indienne", 2),
    "BRL": (986, "réal brésilien", 2),
    "RUB": (643, "rouble russe", 2),
    "SEK": (752, "couronne suédoise", 2),
    "NOK": (578, "couronne norvégienne", 2),
    "DKK": (208, "couronne danoise", 2),
    "PLN": (985, "zloty", 2),
    "KRW": (410, "won sud-coréen", 0),    # PIÈGE : aucune subdivision
    "MXN": (484, "peso mexicain", 2),
    "ZAR": (710, "rand", 2),
    "TRY": (949, "livre turque", 2),
    "KWD": (414, "dinar koweïtien", 3),   # PIÈGE : trois décimales
    "BHD": (48, "dinar bahreïni", 3),     # PIÈGE : trois décimales
    "TND": (788, "dinar tunisien", 3),    # PIÈGE : trois décimales
    "CLP": (152, "peso chilien", 0),
    "ISK": (352, "couronne islandaise", 0),
    "VND": (704, "dông vietnamien", 0),
}

# ── UIT-T E.164 : pays -> indicatif. Plusieurs pays peuvent PARTAGER un indicatif. ────────────────────────
_INDICATIFS = {
    "France": "+33", "Allemagne": "+49", "Royaume-Uni": "+44",
    "États-Unis": "+1", "Canada": "+1",                       # PIÈGE : indicatif PARTAGÉ
    "Russie": "+7", "Kazakhstan": "+7",                       # PIÈGE : indicatif PARTAGÉ
    "Japon": "+81", "Chine": "+86", "Inde": "+91", "Brésil": "+55",
    "Suisse": "+41", "Italie": "+39", "Espagne": "+34", "Belgique": "+32",
    "Pays-Bas": "+31", "Suède": "+46", "Australie": "+61", "Afrique du Sud": "+27",
    "Mexique": "+52", "Corée du Sud": "+82", "Égypte": "+20", "Maroc": "+212",
}

# ── Plaques d'immatriculation : SEULE la France est embarquée. ────────────────────────────────────────────
_PLAQUES = {
    "France": {
        "systeme": "SIV (système d'immatriculation des véhicules), depuis le 15 avril 2009",
        "format": "AA-123-AA",
        "motif": re.compile(r"^[A-HJ-NP-TV-Z]{2}-\d{3}-[A-HJ-NP-TV-Z]{2}$"),
        "note": ("Les lettres I, O et U sont exclues (confusion avec 1, 0 et V). L'ancien système FNI "
                 "(« 123 ABC 45 ») n'est plus attribué mais reste valide sur les véhicules anciens."),
    },
}


def _exige_str(x, nom: str) -> str:
    if isinstance(x, bool) or not isinstance(x, str) or not x.strip():
        raise ValueError("%s : une chaîne non vide est requise" % nom)
    return x.strip()


# ── ISO 4217 ──────────────────────────────────────────────────────────────────────────────────────────────
def monnaies() -> dict:
    """Toutes les monnaies embarquées : code alphabétique -> nom français."""
    return {k: v[1] for k, v in _MONNAIES.items()}


def nom_monnaie(code: str) -> str:
    """Nom français de la monnaie. Code hors table -> ValueError."""
    c = _exige_str(code, "code monnaie").upper()
    if c not in _MONNAIES:
        raise ValueError("code ISO 4217 inconnu : %r (%d monnaies embarquées)" % (c, len(_MONNAIES)))
    return _MONNAIES[c][1]


def code_numerique(code: str) -> int:
    """Code numérique ISO 4217 (ex. EUR -> 978)."""
    c = _exige_str(code, "code monnaie").upper()
    if c not in _MONNAIES:
        raise ValueError("code ISO 4217 inconnu : %r" % c)
    return _MONNAIES[c][0]


def decimales(code: str) -> int:
    """Nombre de décimales de la subdivision. JPY -> 0, EUR -> 2, KWD -> 3.

    Ce n'est PAS toujours 2 : supposer 2 partout fausse les montants d'un facteur 10 ou 100."""
    c = _exige_str(code, "code monnaie").upper()
    if c not in _MONNAIES:
        raise ValueError("code ISO 4217 inconnu : %r" % c)
    return _MONNAIES[c][2]


def formate_montant(montant, code: str) -> str:
    """Formate un montant selon le nombre de décimales de SA monnaie. 1000 JPY -> « 1000 JPY » (0 décimale)."""
    if isinstance(montant, bool) or not isinstance(montant, (int, float)):
        raise ValueError("montant : un nombre est requis")
    n = decimales(code)
    return "%.*f %s" % (n, float(montant), _exige_str(code, "code monnaie").upper())


def monnaie_depuis_numerique(numero: int) -> str:
    """Code alphabétique depuis le code numérique (978 -> EUR)."""
    if isinstance(numero, bool) or not isinstance(numero, int):
        raise ValueError("code numérique : un entier est requis")
    for alpha, (num, _, _) in _MONNAIES.items():
        if num == numero:
            return alpha
    raise ValueError("code numérique ISO 4217 inconnu : %d" % numero)


# ── Indicatifs téléphoniques (E.164) ─────────────────────────────────────────────────────────────────────
def indicatif(pays: str) -> str:
    """Indicatif téléphonique d'un pays. Pays hors table -> ValueError."""
    p = _exige_str(pays, "pays")
    if p not in _INDICATIFS:
        raise ValueError("pays hors table : %r (%d pays embarqués)" % (p, len(_INDICATIFS)))
    return _INDICATIFS[p]


def pays_depuis_indicatif(code: str) -> set:
    """TOUS les pays partageant cet indicatif. « +1 » -> {États-Unis, Canada}.

    Un indicatif n'identifie PAS un pays : on rend l'ensemble, jamais un représentant choisi au hasard."""
    c = _exige_str(code, "indicatif")
    if not c.startswith("+"):
        c = "+" + c
    trouves = {p for p, i in _INDICATIFS.items() if i == c}
    if not trouves:
        raise ValueError("indicatif inconnu : %r" % c)
    return trouves


def pays_unique_depuis_indicatif(code: str) -> str:
    """Le pays, SI l'indicatif n'est pas partagé. « +33 » -> France ; « +1 » -> ValueError.

    C'est l'abstention centrale de ce module : rendre « États-Unis » pour +1 serait un faux silencieux."""
    trouves = pays_depuis_indicatif(code)
    if len(trouves) > 1:
        raise ValueError("indicatif PARTAGÉ par %d pays (%s) : aucun pays unique"
                         % (len(trouves), ", ".join(sorted(trouves))))
    return next(iter(trouves))


def indicatifs_partages() -> dict:
    """Les indicatifs portés par plus d'un pays embarqué : indicatif -> ensemble des pays."""
    par_code: dict = {}
    for p, i in _INDICATIFS.items():
        par_code.setdefault(i, set()).add(p)
    return {i: pays for i, pays in par_code.items() if len(pays) > 1}


# ── ISBN ─────────────────────────────────────────────────────────────────────────────────────────────────
def _chiffres(texte: str) -> str:
    return texte.replace("-", "").replace(" ", "").upper()


def isbn13_valide(isbn: str) -> bool:
    """Somme de contrôle ISBN-13 (ISO 2108) : Σ dᵢ·(1 ou 3 alterné) ≡ 0 mod 10."""
    s = _chiffres(_exige_str(isbn, "ISBN"))
    if len(s) != 13 or not s.isdigit():
        return False
    total = sum(int(c) * (1 if i % 2 == 0 else 3) for i, c in enumerate(s))
    return total % 10 == 0


def isbn10_valide(isbn: str) -> bool:
    """Somme de contrôle ISBN-10 : Σ dᵢ·(10−i) ≡ 0 mod 11. Le dernier caractère peut être « X » (= 10)."""
    s = _chiffres(_exige_str(isbn, "ISBN"))
    if len(s) != 10:
        return False
    if not s[:9].isdigit() or not (s[9].isdigit() or s[9] == "X"):
        return False
    total = sum(int(c) * (10 - i) for i, c in enumerate(s[:9]))
    total += 10 if s[9] == "X" else int(s[9])
    return total % 11 == 0


def isbn_valide(isbn: str) -> bool:
    """Valide un ISBN de 10 ou de 13 chiffres. Toute autre longueur -> False."""
    s = _chiffres(_exige_str(isbn, "ISBN"))
    if len(s) == 13:
        return isbn13_valide(isbn)
    if len(s) == 10:
        return isbn10_valide(isbn)
    return False


# ── Plaques d'immatriculation ────────────────────────────────────────────────────────────────────────────
def format_plaque(pays: str) -> dict:
    """Format d'immatriculation d'un pays EMBARQUÉ. Tout autre pays -> ValueError (deviner serait faux)."""
    p = _exige_str(pays, "pays")
    if p not in _PLAQUES:
        raise ValueError("format de plaque non embarqué pour %r : seuls %s le sont "
                         "(les formats varient par pays et par époque — abstention)"
                         % (p, ", ".join(sorted(_PLAQUES))))
    d = dict(_PLAQUES[p])
    d.pop("motif")
    return d


def plaque_valide(plaque: str, pays: str = "France") -> bool:
    """Une plaque respecte-t-elle le format du pays ? Pays non embarqué -> ValueError."""
    p = _exige_str(pays, "pays")
    if p not in _PLAQUES:
        raise ValueError("format de plaque non embarqué pour %r" % p)
    return bool(_PLAQUES[p]["motif"].match(_exige_str(plaque, "plaque").upper()))


def _verifie_invariants() -> None:
    numeriques = [v[0] for v in _MONNAIES.values()]
    if len(set(numeriques)) != len(numeriques):
        raise RuntimeError("ISO 4217 : deux monnaies partagent le même code numérique")
    for code, (_, _, dec) in _MONNAIES.items():
        if len(code) != 3 or not code.isalpha():
            raise RuntimeError("ISO 4217 : code alphabétique invalide %r" % code)
        if dec not in (0, 2, 3):
            raise RuntimeError("ISO 4217 : nombre de décimales inattendu (%d) pour %s" % (dec, code))
    for pays, ind in _INDICATIFS.items():
        if not ind.startswith("+") or not ind[1:].isdigit():
            raise RuntimeError("E.164 : indicatif invalide %r pour %s" % (ind, pays))


_verifie_invariants()
