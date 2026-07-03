"""
NOMENCLATURE CHIMIQUE BORNÉE — nommer des composés SIMPLES (règles IUPAC, faits établis).

Mandat Yohan : FAUX=0. Deux mécanismes, tous deux VÉRIFIABLEMENT corrects :

  1) CATALOGUE de FAITS établis (sourcés, certains) — noms traditionnels et composés ioniques à valence
     fixe, où la règle systématique des préfixes NE s'applique PAS ('eau', 'ammoniac', "protoxyde d'azote",
     'chlorure de sodium', 'oxyde de calcium'…). Toute formule HORS de ce catalogue connu et NON
     dérivable par la règle ci-dessous -> abstention (ValueError). JAMAIS un nom inventé.

  2) RÈGLE SYSTÉMATIQUE des composés binaires MOLÉCULAIRES (covalents, deux non-métaux), où la nomenclature
     IUPAC par préfixes multiplicateurs (mono/di/tri/tétra/penta/hexa/hepta) est EXACTE et univoque :
        nom = <préfixe>‹anion›-ure (ou ‹oxyde›)  +  "de/d'"  + <préfixe si >1>‹nom du cation›
     L'anion (2ᵉ élément, plus électronégatif) est nommé d'abord ; le cation ensuite. Le préfixe « mono »
     du cation est toujours omis. Exemples EXACTS : CO2->dioxyde de carbone, SO3->trioxyde de soufre,
     N2O5->pentoxyde de diazote, CCl4->tétrachlorure de carbone, SF6->hexafluorure de soufre.

GARDE-FOUS (abstention structurelle, faux positif INTERDIT) :
  - symbole d'élément hors référentiel réel (chimie.MASSES) -> ValueError ;
  - formule mal formée / non binaire / avec parenthèses, charges, points -> ValueError ;
  - la règle systématique n'est appliquée QUE si : 2 éléments non-métaux distincts, anion ∈ {O,F,Cl,Br,S,Se,Te},
    cation ≠ H, électronégativité(cation) < électronégativité(anion) STRICTEMENT, et comptes dans les bornes ;
    sinon -> abstention (on ne devine pas un nom). Les noms à valence variable (Fe, Cu…), peroxydes (H2O2),
    composés ioniques absents du catalogue -> abstention.

stdlib uniquement ; réutilise chimie.MASSES pour valider que les symboles sont de vrais éléments.
"""
from __future__ import annotations

import re

import chimie  # réutilisé : chimie.MASSES = référentiel des symboles d'éléments RÉELS

# ── Préfixes multiplicateurs IUPAC (mono/di/tri/tétra…), valeurs EXACTES ──
PREFIXES: dict[int, str] = {
    1: "mono", 2: "di", 3: "tri", 4: "tétra", 5: "penta",
    6: "hexa", 7: "hepta", 8: "octa", 9: "nona", 10: "déca",
}

# Forme contractée du préfixe devant « oxyde » (élision conventionnelle IUPAC : mon-oxyde, tétr-oxyde…)
OXYDE_PREFIXE: dict[int, str] = {
    1: "monoxyde", 2: "dioxyde", 3: "trioxyde", 4: "tétroxyde",
    5: "pentoxyde", 6: "hexoxyde", 7: "heptoxyde",
}

# Noms français des éléments (faits établis). Élément absent -> abstention.
NOMS_ELEMENTS: dict[str, str] = {
    "H": "hydrogène", "B": "bore", "C": "carbone", "N": "azote", "O": "oxygène",
    "F": "fluor", "Si": "silicium", "P": "phosphore", "S": "soufre", "Cl": "chlore",
    "Se": "sélénium", "Br": "brome", "Te": "tellure", "I": "iode", "As": "arsenic",
    "Xe": "xénon",
    # cations métalliques à valence fixe (pour le référentiel ; le catalogue les utilise)
    "Li": "lithium", "Na": "sodium", "K": "potassium", "Rb": "rubidium", "Cs": "césium",
    "Mg": "magnésium", "Ca": "calcium", "Sr": "strontium", "Ba": "baryum",
    "Al": "aluminium", "Zn": "zinc", "Ag": "argent",
}

# Racines d'anions monoatomiques (-ure), à initiale CONSONNE (pas d'élision de préfixe à gérer).
ANION_ROOT: dict[str, str] = {
    "F": "fluorure", "Cl": "chlorure", "Br": "bromure",
    "S": "sulfure", "Se": "séléniure", "Te": "tellurure",
}

# Électronégativités de Pauling (sous-ensemble non-métaux), pour ordonner cation/anion. Source : valeurs de référence.
_EN: dict[str, float] = {
    "H": 2.20, "B": 2.04, "C": 2.55, "N": 3.04, "O": 3.44, "F": 3.98,
    "Si": 1.90, "P": 2.19, "S": 2.58, "Cl": 3.16, "Se": 2.55, "Br": 2.96,
    "Te": 2.10, "I": 2.66, "As": 2.18, "Xe": 2.60,
}

# Non-métaux : seuls ces éléments peuvent former un composé MOLÉCULAIRE nommé par la règle des préfixes.
_NON_METAUX = {"H", "B", "C", "N", "O", "F", "Si", "P", "S", "Cl", "Se", "Br", "Te", "I", "As", "Xe"}

# Anions admis par la règle systématique (racine consonne pour -ure, ou oxyde).
_ANIONS_REGLE = {"O", "F", "Cl", "Br", "S", "Se", "Te"}

_VOYELLES = set("aeiouéèêëàâîïôûy")

# ── CATALOGUE de faits établis (autorité ; consulté AVANT la règle) ──
# Noms traditionnels + composés ioniques à valence fixe (pas de préfixes) + binaires y=1 (monoxyde, etc.).
CATALOGUE: dict[str, str] = {
    # — exigés par la spécification —
    "CO2": "dioxyde de carbone",
    "CO": "monoxyde de carbone",
    "H2O": "eau",
    "NaCl": "chlorure de sodium",
    "CaO": "oxyde de calcium",
    "NH3": "ammoniac",
    "SO2": "dioxyde de soufre",
    "N2O": "protoxyde d'azote",
    # — autres noms traditionnels / y=1 établis —
    "NO": "monoxyde d'azote",
    "H2S": "sulfure d'hydrogène",
    "HCl": "chlorure d'hydrogène",
    "HF": "fluorure d'hydrogène",
    "HBr": "bromure d'hydrogène",
    "HI": "iodure d'hydrogène",
    # — composés ioniques à valence FIXE (alcalins/alcalino-terreux/Al/Zn/Ag : pas de préfixes) —
    "NaF": "fluorure de sodium",
    "NaBr": "bromure de sodium",
    "NaI": "iodure de sodium",
    "KCl": "chlorure de potassium",
    "KF": "fluorure de potassium",
    "KBr": "bromure de potassium",
    "KI": "iodure de potassium",
    "LiCl": "chlorure de lithium",
    "CaCl2": "chlorure de calcium",
    "CaF2": "fluorure de calcium",
    "MgCl2": "chlorure de magnésium",
    "MgO": "oxyde de magnésium",
    "Li2O": "oxyde de lithium",
    "Na2O": "oxyde de sodium",
    "K2O": "oxyde de potassium",
    "BaO": "oxyde de baryum",
    "Al2O3": "oxyde d'aluminium",
    "ZnO": "oxyde de zinc",
    "ZnS": "sulfure de zinc",
}


def prefixe(n: int) -> str:
    """Préfixe multiplicateur IUPAC pour n ∈ [1..10] ('mono','di',...,'déca'). Hors borne -> ValueError."""
    if isinstance(n, bool) or not isinstance(n, int):
        raise ValueError("n doit être un entier")
    if n not in PREFIXES:
        raise ValueError(f"préfixe non défini pour n={n!r} (borné 1..10)")
    return PREFIXES[n]


def nom_element(symbole: str) -> str:
    """Nom français d'un élément du référentiel. Symbole inconnu -> ValueError."""
    if not isinstance(symbole, str) or symbole not in NOMS_ELEMENTS:
        raise ValueError(f"élément inconnu: {symbole!r}")
    return NOMS_ELEMENTS[symbole]


def _tokens(formule: str) -> list[tuple[str, int]]:
    """Parse une formule SIMPLE en liste ordonnée (symbole, compte). Lève ValueError si malformée,
    si un caractère parasite (parenthèse, charge, point, espace interne) traîne, ou si un symbole n'est
    pas un élément RÉEL (chimie.MASSES)."""
    if not isinstance(formule, str):
        raise ValueError("formule doit être une chaîne")
    s = formule.strip()
    if not s or not re.fullmatch(r"(?:[A-Z][a-z]?\d*)+", s):
        raise ValueError(f"formule mal formée: {formule!r}")
    toks: list[tuple[str, int]] = []
    for sym, dig in re.findall(r"([A-Z][a-z]?)(\d*)", s):
        if sym not in chimie.MASSES:
            raise ValueError(f"symbole hors référentiel d'éléments réels: {sym!r}")
        n = int(dig) if dig else 1
        if n < 1:
            raise ValueError("compte d'atome nul")
        toks.append((sym, n))
    return toks


def _de(mot: str) -> str:
    """Particule 'de'/'d'' avec élision devant voyelle (aucun nom d'élément non-métal n'a de h aspiré)."""
    return ("d'" + mot) if mot[:1].lower() in _VOYELLES else ("de " + mot)


def _nom_systematique(toks: list[tuple[str, int]]) -> str:
    """Nom IUPAC d'un binaire MOLÉCULAIRE par la règle des préfixes, SEULEMENT si le cas est univoque.
    Sinon ValueError (abstention). Pré-condition : exactement 2 tokens distincts."""
    if len(toks) != 2:
        raise ValueError("la règle systématique exige exactement deux éléments")
    (cat, x), (an, y) = toks
    if cat == an:
        raise ValueError("un seul élément : pas un composé binaire")
    # garde-fous de soundness : domaine strictement covalent et ordonné
    if cat not in _NON_METAUX or an not in _NON_METAUX:
        raise ValueError("composé non moléculaire (métal présent) : hors règle des préfixes")
    if cat == "H":
        raise ValueError("hydrures/hydracides : noms traditionnels, hors règle (voir catalogue)")
    if an not in _ANIONS_REGLE:
        raise ValueError("anion hors du domaine sûr de la règle")
    if cat not in _EN or an not in _EN:
        raise ValueError("électronégativité indisponible : abstention")
    if not (_EN[cat] < _EN[an]):
        raise ValueError("ordre cation/anion non garanti (électronégativité) : abstention")
    if not (1 <= x <= 10):
        raise ValueError("nombre de cations hors borne")
    # mot de l'anion (premier mot)
    if an == "O":
        if y not in OXYDE_PREFIXE or y < 2:
            raise ValueError("nombre d'oxygènes hors borne sûre")
        mot_anion = OXYDE_PREFIXE[y]
    else:
        if not (2 <= y <= 10):
            raise ValueError("nombre d'anions hors borne (y>=2 requis hors catalogue)")
        mot_anion = PREFIXES[y] + ANION_ROOT[an]
    # mot du cation (second mot)
    nom_cat = NOMS_ELEMENTS[cat]
    if x == 1:
        mot_cation = nom_cat
    else:
        pre = PREFIXES[x]
        # 'di'/'tri' n'élident jamais (diazote). Les préfixes en -a/-o (tétra, penta…) PEUVENT contracter
        # devant voyelle : cas rare et ambigu -> abstention plutôt que deviner.
        if pre[-1] in "ao" and nom_cat[:1].lower() in _VOYELLES:
            raise ValueError("contraction de préfixe ambiguë : abstention")
        mot_cation = pre + nom_cat
    return f"{mot_anion} {_de(mot_cation)}"


def nom_compose_binaire(formule: str) -> str:
    """Nom IUPAC d'un composé binaire SIMPLE. Catalogue de faits établis d'abord, puis règle systématique
    des binaires moléculaires. Formule inconnue / complexe / hors domaine sûr -> ValueError (abstention)."""
    if not isinstance(formule, str):
        raise ValueError("formule doit être une chaîne")
    s = formule.strip()
    if s in CATALOGUE:
        return CATALOGUE[s]
    toks = _tokens(s)  # valide format + éléments réels (lève ValueError sinon)
    return _nom_systematique(toks)


def formules_connues() -> list[str]:
    """Liste triée des formules du catalogue (faits établis explicites)."""
    return sorted(CATALOGUE)


if __name__ == "__main__":
    for f in ("CO2", "CO", "H2O", "NaCl", "CaO", "NH3", "SO2", "N2O",
              "SO3", "N2O5", "CCl4", "SF6", "PCl3", "P2O5", "OF2"):
        try:
            print(f"{f:6s} -> {nom_compose_binaire(f)}")
        except ValueError as e:
            print(f"{f:6s} -> (abstention) {e}")
