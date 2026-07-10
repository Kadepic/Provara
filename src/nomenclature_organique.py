"""
NOMENCLATURE ORGANIQUE BORNÉE — nommer une chaîne carbonée LINÉAIRE et identifier une famille par sa
formule brute (règles IUPAC de nomenclature substitutive, faits établis).

Le module `nomenclature_chimique` (RÉSERVÉ, non modifié ici) nomme les composés BINAIRES (préfixes
multiplicatifs + catalogue ionique). ICI : la nomenclature ORGANIQUE, sur un périmètre STRICTEMENT
DÉLIMITÉ et DIT — chaînes carbonées LINÉAIRES, MONOFONCTIONNELLES, de 1 à 12 carbones.

Posture FAUX=0 (identique à `galois`/`geometries_non_euclidiennes`) : un fait vérifiable, ou une abstention
explicite. JAMAIS un nom inventé, JAMAIS une formule devinée. Le point capital est `identifie` : une même
formule brute correspond en général à PLUSIEURS familles (isomères de fonction), donc `identifie` rend
TOUJOURS une LISTE — jamais un composé unique. C3H6O est compatible avec l'ALDÉHYDE (propanal) ET la
CÉTONE (propanone) ; C2H6O avec l'ALCOOL (éthanol) ET l'ÉTHER (diméthyléther). Rendre « propanal » seul
serait un FAUX POSITIF, interdit.

MÉCANISME (exact, pas une corrélation) :
  • Racines multiplicatives IUPAC pour 1..12 carbones : méth, éth, prop, but, pent, hex, hept, oct, non,
    déc, undéc, dodéc.
  • Nom d'une chaîne monofonctionnelle = [préfixe] + racine(n) + suffixe de fonction :
        alcane -ane, alcène -ène, alcyne -yne, alcool -anol, aldéhyde -anal, cétone -anone,
        acide carboxylique « acide -anoïque », amine -anamine.
    Ces noms sont les noms de la SÉRIE (chaîne + fonction), sans locant ; là où le groupe est
    nécessairement terminal (aldéhyde, acide) le nom est univoque.
  • Formules brutes des séries homologues :
        alcane CnH(2n+2) ; alcène CnH(2n) ; alcyne CnH(2n−2) ; alcool CnH(2n+2)O ; éther CnH(2n+2)O ;
        aldéhyde CnH(2n)O ; cétone CnH(2n)O ; acide CnH(2n)O2 ; amine CnH(2n+3)N.

GARANTIES (vérifiées en adverse par `valide_nomenclature_organique.py`) :
  - n hors [1,12]                         -> ValueError (hors périmètre) ;
  - famille hors catalogue                -> ValueError ;
  - chaîne trop courte pour la fonction   -> ValueError (pas de C1-alcène « méthène », pas de C2-cétone…) ;
  - formule mal formée / élément hors {C,H,O,N} / molécule cyclique ou ramifiée -> ValueError explicite ;
  - `identifie` sans AUCUNE famille compatible -> ValueError (benzène C6H6, CO2, n>12…) ;
  - types invalides (bool, str là où un entier est requis, NaN/inf, mauvaise arité) -> ValueError ;
  - fonctions PURES, DÉTERMINISTES ; faux négatif/abstention toléré, faux POSITIF interdit.

stdlib uniquement (`re`). Aucune dépendance, aucun état mutable global exposé.
"""
from __future__ import annotations

import re

SOURCE = "règles IUPAC de nomenclature substitutive (chaînes linéaires) + formules brutes des séries homologues"

# ── Racines multiplicatives IUPAC, 1..12 carbones (faits établis) ─────────────────────────────────────────
RACINES: dict[int, str] = {
    1: "méth", 2: "éth", 3: "prop", 4: "but", 5: "pent", 6: "hex",
    7: "hept", 8: "oct", 9: "non", 10: "déc", 11: "undéc", 12: "dodéc",
}

_N_MAX = 12

# ── Pliage d'accents pour une comparaison indulgente (jamais un faux positif : « alcene » -> « alcène ») ──
_ACCENTS = str.maketrans("àâäéèêëîïôöùûüç", "aaaeeeeiioouuuc")


def _fold(s: str) -> str:
    return s.translate(_ACCENTS)


# ── Catalogue des familles : brute (C,H,O,N à partir de n), carbones minimum, suffixe de nom ──────────────
# 'nom' = (préfixe, suffixe) accolés à la racine ; None quand la famille n'est PAS nommée par nom_chaine
# (l'éther linéaire est ambigu dès 3 carbones : méthoxyéthane… -> hors périmètre du nom systématique).
FAMILLES: dict[str, dict] = {
    "alcane":              {"brute": lambda n: (n, 2 * n + 2, 0, 0), "min": 1, "nom": ("", "ane")},
    "alcène":              {"brute": lambda n: (n, 2 * n,     0, 0), "min": 2, "nom": ("", "ène")},
    "alcyne":              {"brute": lambda n: (n, 2 * n - 2, 0, 0), "min": 2, "nom": ("", "yne")},
    "alcool":              {"brute": lambda n: (n, 2 * n + 2, 1, 0), "min": 1, "nom": ("", "anol")},
    "éther":               {"brute": lambda n: (n, 2 * n + 2, 1, 0), "min": 2, "nom": None},
    "aldéhyde":            {"brute": lambda n: (n, 2 * n,     1, 0), "min": 1, "nom": ("", "anal")},
    "cétone":              {"brute": lambda n: (n, 2 * n,     1, 0), "min": 3, "nom": ("", "anone")},
    "acide carboxylique":  {"brute": lambda n: (n, 2 * n,     2, 0), "min": 1, "nom": ("acide ", "anoïque")},
    "amine":               {"brute": lambda n: (n, 2 * n + 3, 0, 1), "min": 1, "nom": ("", "anamine")},
}

# ── Groupe fonctionnel (formule du groupe) — l'alcane (hydrocarbure saturé) n'en a PAS. ───────────────────
GROUPES: dict[str, str] = {
    "alcène": "C=C",
    "alcyne": "C≡C",
    "alcool": "-OH",
    "éther": "-O-",
    "aldéhyde": "-CHO",
    "cétone": ">C=O",
    "acide carboxylique": "-COOH",
    "amine": "-NH2",
}

# Table inverse des noms d'alcanes (repliée sans accents), pour carbones_depuis_nom.
_ALCANE_INV: dict[str, int] = {_fold(RACINES[n] + "ane"): n for n in RACINES}


# ── Validations ───────────────────────────────────────────────────────────────────────────────────────────
def _n_valide(n) -> int:
    """Nombre de carbones : entier de 1 à 12 (bool REFUSÉ ; float/str REFUSÉS)."""
    if isinstance(n, bool) or not isinstance(n, int):
        raise ValueError("n (carbones) doit être un entier")
    if not (1 <= n <= _N_MAX):
        raise ValueError(f"hors périmètre : n doit être dans [1,{_N_MAX}], reçu {n}")
    return n


def _famille_valide(famille) -> str:
    """Résout un nom de famille (indulgent aux accents) vers sa clé canonique ; sinon ValueError."""
    if not isinstance(famille, str):
        raise ValueError(f"famille (chaîne) attendue, reçu {famille!r}")
    cle = _fold(famille.strip().lower())
    table = {_fold(f): f for f in FAMILLES}
    if cle not in table:
        raise ValueError(f"famille hors catalogue (abstention) : {famille!r}")
    return table[cle]


# ── (a) ALCANES LINÉAIRES ─────────────────────────────────────────────────────────────────────────────────
def nom_alcane(n: int) -> str:
    """Nom de l'alcane linéaire à n carbones (méthane…dodécane). n ∈ [1,12] sinon ValueError."""
    n = _n_valide(n)
    return RACINES[n] + "ane"


def carbones_depuis_nom(nom: str) -> int:
    """Inverse de nom_alcane : nombre de carbones d'un nom d'alcane linéaire. Inconnu -> ValueError."""
    if not isinstance(nom, str):
        raise ValueError(f"nom (chaîne) attendu, reçu {nom!r}")
    cle = _fold(nom.strip().lower())
    if cle not in _ALCANE_INV:
        raise ValueError(f"nom d'alcane linéaire inconnu (n≤{_N_MAX}) : {nom!r}")
    return _ALCANE_INV[cle]


# ── (b) NOM D'UNE CHAÎNE MONOFONCTIONNELLE ────────────────────────────────────────────────────────────────
def nom_chaine(n: int, famille: str) -> str:
    """Nom IUPAC de la chaîne linéaire à n carbones portant la fonction `famille`.

    Ex. nom_chaine(2,'alcène')='éthène' ; nom_chaine(3,'cétone')='propanone' ;
    nom_chaine(2,'acide carboxylique')='acide éthanoïque'. Chaîne trop courte pour la fonction,
    n hors [1,12], famille inconnue, ou famille non nommable systématiquement (éther) -> ValueError."""
    fam = _famille_valide(famille)
    n = _n_valide(n)
    spec = FAMILLES[fam]
    if spec["nom"] is None:
        raise ValueError(f"{fam} : pas de nom systématique (linéaire ambigu) -> hors périmètre du nom")
    if n < spec["min"]:
        raise ValueError(f"{fam} : au moins {spec['min']} carbones requis (aucun composé plus court)")
    pre, suf = spec["nom"]
    return pre + RACINES[n] + suf


# ── (c) FORMULE BRUTE ─────────────────────────────────────────────────────────────────────────────────────
def _formule_str(c: int, h: int, o: int, azote: int) -> str:
    """Compose une formule brute lisible C…H…O…N… (compte 1 omis)."""
    parts = []
    for sym, cnt in (("C", c), ("H", h), ("O", o), ("N", azote)):
        if cnt < 0:
            raise ValueError("compte d'atome négatif")  # défensif : ne devrait jamais arriver
        if cnt > 0:
            parts.append(sym + (str(cnt) if cnt > 1 else ""))
    return "".join(parts)


def formule_brute(n: int, famille: str) -> str:
    """Formule brute de la chaîne linéaire à n carbones de la famille `famille`.

    alcane CnH(2n+2) ; alcène CnH(2n) ; alcyne CnH(2n−2) ; alcool/éther CnH(2n+2)O ;
    aldéhyde/cétone CnH(2n)O ; acide CnH(2n)O2 ; amine CnH(2n+3)N. Chaîne trop courte, n hors [1,12]
    ou famille inconnue -> ValueError."""
    fam = _famille_valide(famille)
    n = _n_valide(n)
    spec = FAMILLES[fam]
    if n < spec["min"]:
        raise ValueError(f"{fam} : au moins {spec['min']} carbones requis (aucun composé plus court)")
    c, h, o, azote = spec["brute"](n)
    return _formule_str(c, h, o, azote)


# ── (d) IDENTIFICATION PAR FORMULE BRUTE (LISTE de familles compatibles — jamais une seule) ───────────────
def _parse_brute(formule: str) -> tuple[int, int, int, int]:
    """Parse une formule brute en (C,H,O,N). Élément hors {C,H,O,N}, répétition, casse ou parasite
    (parenthèse, charge, point) -> ValueError."""
    if not isinstance(formule, str):
        raise ValueError(f"formule (chaîne) attendue, reçu {formule!r}")
    s = formule.strip()
    if not s or not re.fullmatch(r"(?:[A-Z][a-z]?\d*)+", s):
        raise ValueError(f"formule mal formée : {formule!r}")
    counts = {"C": 0, "H": 0, "O": 0, "N": 0}
    vus = set()
    for sym, dig in re.findall(r"([A-Z][a-z]?)(\d*)", s):
        if sym not in counts:
            raise ValueError(f"élément hors périmètre organique (C,H,O,N seuls) : {sym!r}")
        if sym in vus:
            raise ValueError(f"élément répété (formule brute mal formée) : {sym!r}")
        vus.add(sym)
        k = int(dig) if dig else 1
        if k < 1:
            raise ValueError("compte d'atome nul")
        counts[sym] = k
    return (counts["C"], counts["H"], counts["O"], counts["N"])


def identifie(formule: str) -> list[str]:
    """TOUTES les familles linéaires monofonctionnelles compatibles avec la formule brute donnée.

    Rend TOUJOURS une LISTE (triée). Point FAUX=0 : plusieurs familles peuvent partager une formule
    (isomères de fonction) — identifie('C3H6O') -> ['aldéhyde','cétone'] ; identifie('C2H6O') ->
    ['alcool','éther']. Aucune famille compatible (benzène C6H6, n>12, molécule cyclique/ramifiée…)
    -> ValueError explicite."""
    c, h, o, azote = _parse_brute(formule)
    res: list[str] = []
    for fam, spec in FAMILLES.items():
        if not (spec["min"] <= c <= _N_MAX):
            continue
        if spec["brute"](c) == (c, h, o, azote):
            res.append(fam)
    if not res:
        raise ValueError(
            "hors du périmètre : seules les chaînes linéaires monofonctionnelles "
            f"(C,H,O,N ; n≤{_N_MAX}) sont couvertes — molécule ramifiée/cyclique ou hors catalogue"
        )
    return sorted(res)


# ── (e) GROUPE FONCTIONNEL ────────────────────────────────────────────────────────────────────────────────
def groupe_fonctionnel(famille: str) -> str:
    """Formule du groupe fonctionnel de la famille (ex. alcool -> '-OH', acide -> '-COOH').

    L'alcane est un hydrocarbure saturé SANS groupe fonctionnel -> ValueError (abstention).
    Famille inconnue -> ValueError."""
    fam = _famille_valide(famille)
    if fam not in GROUPES:
        raise ValueError(f"{fam} : hydrocarbure saturé sans groupe fonctionnel (abstention)")
    return GROUPES[fam]


def familles() -> tuple:
    """Liste triée des familles du catalogue organique couvert."""
    return tuple(sorted(FAMILLES))


if __name__ == "__main__":
    for n in range(1, 13):
        print(f"C{n}: {nom_alcane(n)}")
    for f in ("C3H6O", "C2H6O", "CH4", "C3H6", "C2H4O2"):
        try:
            print(f"{f:8s} -> {identifie(f)}")
        except ValueError as e:
            print(f"{f:8s} -> (abstention) {e}")
