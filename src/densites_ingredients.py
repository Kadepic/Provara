"""
DENSITÉS D'INGRÉDIENTS — masses volumiques APPARENTES culinaires (conversions volume↔masse).

Posture FAUX=0 (identique à `recettes`/`geometries_non_euclidiennes` : la CONVENTION juge, jamais un faux) :
  • `recettes.py` (RÉSERVÉ, seulement importé ici) ne convertit volume↔masse que pour l'EAU (densité 1) ;
    pour tout autre ingrédient il ABSTIENT. Ce module lève cette abstention pour les ingrédients COURANTS en
    fournissant un CATALOGUE de masses volumiques apparentes conventionnelles (livres de cuisine).
  • Ces masses volumiques sont APPARENTES (elles dépendent du tassement, de l'humidité, de la granulométrie) :
    une valeur nue serait MALHONNÊTE. Le module rend donc TOUJOURS un COUPLE
        (valeur_g_par_ml, incertitude_relative)                     [masse_volumique]
        (masse_g, incertitude_g) / (volume_ml, incertitude_ml)      [conversions]
    jamais un scalaire nu. Une tasse de farine TASSÉE pèse jusqu'à ~30 % de plus qu'une tasse aérée :
    l'incertitude rendue le reflète (on refuse une précision qu'on n'a pas).
  • Les sorties flottantes sont ARRONDIES à 10 chiffres significatifs (précision honnête : jamais une
    précision qu'on n'a pas). Le round-trip masse↔volume N'EST PAS exact en général — arrondir le produit
    v·d à 10 chiffres PUIS le quotient à 10 chiffres peut s'écarter du départ (contre-exemple mesuré :
    farine t55, 651.593321 mL -> 651.5933209 mL, écart 1e-7). Il est EXACT pour l'eau (densité 1) et
    STABLE ailleurs à ~10 chiffres significatifs (|Δ| ≤ 1e-9·|v|). La valeur rendue est MARQUÉE arrondie,
    on ne SUR-affirme jamais une exactitude qu'on n'a pas.

MESURES ANGLO-SAXONNES : DEUX conventions de « cup » coexistent — cup US LÉGALE = 240 mL (exact) et cup US
COUTUMIÈRE = 236.588 mL. Le module REFUSE (ValueError) `cup_vers_ml` sans convention nommée : il ne DEVINE pas.
tablespoon US = 14.787 mL, teaspoon US = 4.929 mL.

GARANTIES (vérifiées en adverse par `valide_densites_ingredients.py`) :
  - ingrédient hors catalogue -> ValueError (JAMAIS une densité devinée) ;
  - volume ≤ 0 / masse ≤ 0 -> ValueError ;
  - convention de cup non précisée / inconnue -> ValueError ;
  - types invalides (bool, str là où un nombre est attendu, non-str comme ingrédient, NaN, ±inf) -> ValueError ;
  - couple TOUJOURS rendu (jamais un scalaire nu) ; incertitude ≥ 0 ;
  - déterministe ; conservateur (abstention/faux négatif toléré, faux POSITIF interdit).

stdlib uniquement (math). Importe `recettes` (délégation de la règle de trois) — aucun dataset chargé.
"""
from __future__ import annotations

import math

import recettes

SOURCE = (
    "masses volumiques apparentes conventionnelles de cuisine (livres de recettes) ; "
    "cup US légale=240 mL, cup US coutumière=236.588 mL, tablespoon US=14.787 mL, teaspoon US=4.929 mL"
)

_CHIFFRES_SIGNIFICATIFS = 10

# ── CATALOGUE : ingrédient -> (masse_volumique_g_par_ml, incertitude_RELATIVE) ───────────────────────────────────
# Valeurs CONVENTIONNELLES (g/mL). L'incertitude relative traduit la variabilité APPARENTE (tassement/humidité) :
# élevée pour les poudres aérées (farine, cacao, sucre glace), faible pour les liquides.
_CATALOGUE = {
    "eau":              (1.00, 0.005),
    "lait":             (1.03, 0.01),
    "huile":            (0.92, 0.01),
    "farine t55":       (0.53, 0.15),   # poudre très variable (tassée ↔ aérée : ~±15 %+)
    "sucre en poudre":  (0.85, 0.05),
    "sucre glace":      (0.56, 0.10),
    "sel fin":          (1.20, 0.05),
    "beurre":           (0.91, 0.03),
    "miel":             (1.42, 0.02),
    "riz cru":          (0.85, 0.05),
    "cacao en poudre":  (0.41, 0.15),
    "levure chimique":  (0.72, 0.10),
    "creme liquide":    (1.01, 0.01),
}

# Alias -> clé canonique du catalogue (formes courtes usuelles).
_ALIAS = {
    "farine": "farine t55",
    "sucre": "sucre en poudre",
    "sucre poudre": "sucre en poudre",
    "sel": "sel fin",
    "cacao": "cacao en poudre",
    "levure": "levure chimique",
    "riz": "riz cru",
    "creme": "creme liquide",
    "water": "eau",
}

# ── CONVENTIONS DE « CUP » (mL) : les DEUX existent, il faut la NOMMER ────────────────────────────────────────────
_CUP_ML = {
    "legale": 240.0,        # cup US légale (FDA) = 240 mL exact
    "coutumiere": 236.588,  # cup US customary = 236.588 mL
}
_CUP_ALIAS = {
    "legal": "legale", "us_legale": "legale", "fda": "legale",
    "customary": "coutumiere", "coutumier": "coutumiere", "us_customary": "coutumiere",
}

_TABLESPOON_US_ML = 14.787  # tablespoon US
_TEASPOON_US_ML = 4.929     # teaspoon US


# ── helpers internes ─────────────────────────────────────────────────────────────────────────────────────────────
def _sig(x: float, n: int = _CHIFFRES_SIGNIFICATIFS) -> float:
    """Arrondit à n chiffres significatifs (précision honnête, magnitude-indépendante)."""
    if x == 0:
        return 0.0
    return float(f"{x:.{n}g}")


def _est_reel(x) -> bool:
    """True ssi x est un réel FINI (bool REFUSÉ : True n'est pas une mesure)."""
    return isinstance(x, (int, float)) and not isinstance(x, bool) and math.isfinite(x)


def _exige_positif(x, nom: str) -> float:
    """Réel strictement positif requis (volume/masse d'un ingrédient réel). Sinon ValueError."""
    if not _est_reel(x) or x <= 0:
        raise ValueError(f"{nom} invalide : un réel strictement positif est requis (reçu {x!r})")
    return float(x)


def _refuse_non_fini(x, nom: str) -> None:
    """FAUX=0 : un réel NON fini (NaN/±inf) est REFUSÉ (recettes._verifie_reel ne teste pas isfinite).

    Ne juge QUE la finitude ; le type (bool/str) et la positivité restent délégués à `recettes`."""
    if isinstance(x, float) and not math.isfinite(x):
        raise ValueError(f"{nom} non fini (NaN/±inf) refusé (abstention) : {x!r}")


def _normalise(nom):
    """Normalise un libellé d'ingrédient (str non vide) : minuscule, accents ôtés, espaces compactés."""
    if not isinstance(nom, str):
        raise ValueError(f"ingrédient non textuel : {nom!r}")
    cle = nom.strip().lower()
    for a, b in (("à", "a"), ("â", "a"), ("é", "e"), ("è", "e"), ("ê", "e"),
                 ("ï", "i"), ("î", "i"), ("ô", "o"), ("û", "u"), ("ù", "u"), ("ç", "c")):
        cle = cle.replace(a, b)
    cle = " ".join(cle.split())  # compacte les espaces
    if not cle:
        raise ValueError("ingrédient vide")
    return cle


def _cle_catalogue(nom) -> str:
    """Clé canonique du catalogue, via alias. Hors catalogue -> ValueError (jamais deviné)."""
    cle = _normalise(nom)
    cle = _ALIAS.get(cle, cle)
    if cle not in _CATALOGUE:
        raise ValueError(
            f"ingrédient hors catalogue : {nom!r} — aucune masse volumique conventionnelle, abstention"
        )
    return cle


# ── (a) MASSE VOLUMIQUE (couple) ─────────────────────────────────────────────────────────────────────────────────
def masse_volumique(ingredient):
    """Masse volumique apparente d'un ingrédient -> COUPLE (valeur_g_par_ml, incertitude_relative).

    Hors catalogue -> ValueError. Rend TOUJOURS un couple (jamais un scalaire nu)."""
    cle = _cle_catalogue(ingredient)
    d, inc_rel = _CATALOGUE[cle]
    return (_sig(d), _sig(inc_rel))


# ── (b) VOLUME -> MASSE (couple) ─────────────────────────────────────────────────────────────────────────────────
def volume_vers_masse(volume_ml, ingredient):
    """Convertit un volume (mL) en masse (g) -> COUPLE (masse_g, incertitude_g).

    masse = volume · densité ; incertitude_g = masse · incertitude_relative.
    volume ≤ 0 -> ValueError ; ingrédient hors catalogue -> ValueError."""
    v = _exige_positif(volume_ml, "volume_ml")
    cle = _cle_catalogue(ingredient)
    d, inc_rel = _CATALOGUE[cle]
    masse = v * d
    return (_sig(masse), _sig(masse * inc_rel))


# ── (c) MASSE -> VOLUME (couple) ─────────────────────────────────────────────────────────────────────────────────
def masse_vers_volume(masse_g, ingredient):
    """Convertit une masse (g) en volume (mL) -> COUPLE (volume_ml, incertitude_ml).

    volume = masse / densité ; incertitude_ml = volume · incertitude_relative.
    masse ≤ 0 -> ValueError ; ingrédient hors catalogue -> ValueError."""
    m = _exige_positif(masse_g, "masse_g")
    cle = _cle_catalogue(ingredient)
    d, inc_rel = _CATALOGUE[cle]
    volume = m / d
    return (_sig(volume), _sig(volume * inc_rel))


# ── (d) MESURES ANGLO-SAXONNES ───────────────────────────────────────────────────────────────────────────────────
def cup_vers_ml(nombre, convention=None):
    """Convertit un nombre de « cups » US en mL. La CONVENTION doit être NOMMÉE (aucune n'est devinée) :
        convention="legale"      -> 240 mL exact (cup US légale / FDA)
        convention="coutumiere"  -> 236.588 mL   (cup US customary)
    convention absente/inconnue -> ValueError ; nombre ≤ 0 -> ValueError."""
    n = _exige_positif(nombre, "nombre de cups")
    if not isinstance(convention, str):
        raise ValueError(
            "convention de cup non précisée : préciser 'legale' (240 mL) ou 'coutumiere' (236.588 mL)"
        )
    c = convention.strip().lower()
    for a, b in (("é", "e"), ("è", "e"), (" ", "_")):
        c = c.replace(a, b)
    c = _CUP_ALIAS.get(c, c)
    if c not in _CUP_ML:
        raise ValueError(f"convention de cup inconnue : {convention!r} — attendu 'legale' ou 'coutumiere'")
    return _sig(n * _CUP_ML[c])


def tablespoon_us_vers_ml(nombre):
    """Convertit un nombre de tablespoons US en mL (1 tbsp = 14.787 mL). nombre ≤ 0 -> ValueError."""
    n = _exige_positif(nombre, "nombre de tablespoons")
    return _sig(n * _TABLESPOON_US_ML)


def teaspoon_us_vers_ml(nombre):
    """Convertit un nombre de teaspoons US en mL (1 tsp = 4.929 mL). nombre ≤ 0 -> ValueError."""
    n = _exige_positif(nombre, "nombre de teaspoons")
    return _sig(n * _TEASPOON_US_ML)


# ── (e) MISE À L'ÉCHELLE (règle de trois, DÉLÉGUÉE à recettes.py) ─────────────────────────────────────────────────
def adapte_recette(ingredients, portions_origine, portions_cible):
    """Adapte les quantités d'une recette d'un nombre de portions à un autre (règle de trois).

    La proportionnalité est DÉLÉGUÉE à `recettes.adapte_quantite` (module réservé). `ingredients` est un dict
    {nom: quantite} ou une liste de couples (nom, quantite) ; le résultat conserve la structure.

    portions_origine ≤ 0, portions_cible < 0, quantité < 0 -> ValueError (via recettes).
    quantité / portions NaN ou ±inf -> ValueError (garde de finitude LOCALE : recettes ne la fait pas)."""
    _refuse_non_fini(portions_origine, "portions_origine")
    _refuse_non_fini(portions_cible, "portions_cible")
    if isinstance(ingredients, dict):
        items = list(ingredients.items())
        rendre_dict = True
    elif isinstance(ingredients, (list, tuple)):
        items = []
        for paire in ingredients:
            if not isinstance(paire, (list, tuple)) or len(paire) != 2:
                raise ValueError(f"couple (nom, quantite) attendu, reçu {paire!r}")
            items.append((paire[0], paire[1]))
        rendre_dict = False
    else:
        raise ValueError("ingredients doit être un dict {nom: quantite} ou une liste de couples (nom, quantite)")

    if not items:
        raise ValueError("recette vide : aucun ingrédient à adapter")

    adapte = []
    for nom, quantite in items:
        if not isinstance(nom, str) or not nom.strip():
            raise ValueError(f"nom d'ingrédient invalide : {nom!r}")
        _refuse_non_fini(quantite, f"quantité de {nom!r}")
        q = recettes.adapte_quantite(quantite, portions_origine, portions_cible)
        adapte.append((nom, _sig(q)))

    if rendre_dict:
        return dict(adapte)
    return adapte
