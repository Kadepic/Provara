"""
ALGÈBRE DIMENSIONNELLE — brique fondatrice (Vague 1, socle de représentation).

POURQUOI : c'est le premier filtre anti-absurdité de la machine. Une combinaison de lois dont les dimensions ne
s'accordent pas est physiquement IMPOSSIBLE et doit être éliminée SANS calcul. « Penser comme une machine » commence
ici : on énumère des relations, on rejette d'emblée les non-homogènes. Fan-out maximal — grandeur typée, lois
manipulables, évaluation par formule, juge de bornes, bilans de conservation, calcul d'écart au théorique en dépendent.

MODÈLE : toute grandeur physique a une DIMENSION = un vecteur d'exposants sur les 7 dimensions de base SI
(M masse, L longueur, T temps, I courant, Θ température, N quantité de matière, J intensité lumineuse). Ex. une force
= M·L·T⁻². Une unité = (dimension, facteur vers l'unité SI de base, décalage affine éventuel — °C, °F).

FAUX=0 (soundness, pas d'approximation) :
  • Arithmétique des exposants EXACTE via Fraction (jamais de dérive flottante ; les exposants fractionnaires sont gérés).
  • Additionner/comparer deux grandeurs de dimensions DIFFÉRENTES est une ERREUR que la brique DÉTECTE (renvoie None =
    HORS), jamais un calcul silencieux. C'est le cœur du filtre.
  • Convertir entre unités INCOMMENSURABLES (mètre vs seconde) -> None (HORS). Jamais un nombre inventé.
  • Les facteurs des unités DÉFINIES exactement (km, pouce=0.0254 m, heure, °C=+273.15 K) sont des Fraction exactes ->
    1 km = 1000 m EXACT, 0 °C = 273.15 K EXACT. Aucune constante mesurée ici (celles-là portent une incertitude ->
    voir grandeur.py / propagation).

Souverain, stdlib pur (fractions). Déterministe.
"""
from __future__ import annotations

from fractions import Fraction

# Ordre canonique des 7 dimensions de base SI.
_BASE = ("M", "L", "T", "I", "Θ", "N", "J")
_NOMS = {"M": "masse", "L": "longueur", "T": "temps", "I": "courant électrique",
         "Θ": "température", "N": "quantité de matière", "J": "intensité lumineuse"}
_EXPOSANTS = str.maketrans("-0123456789", "⁻⁰¹²³⁴⁵⁶⁷⁸⁹")


class Dimension:
    """Vecteur d'exposants (Fraction) sur (M, L, T, I, Θ, N, J). Immuable, hachable. Produit = somme des exposants."""

    __slots__ = ("exp",)

    def __init__(self, exp=None):
        if exp is None:
            self.exp = (Fraction(0),) * 7
        else:
            if len(exp) != 7:
                raise ValueError("une dimension a exactement 7 exposants (M,L,T,I,Θ,N,J)")
            self.exp = tuple(Fraction(e) for e in exp)

    def __mul__(self, autre: "Dimension") -> "Dimension":
        return Dimension(tuple(a + b for a, b in zip(self.exp, autre.exp)))

    def __truediv__(self, autre: "Dimension") -> "Dimension":
        return Dimension(tuple(a - b for a, b in zip(self.exp, autre.exp)))

    def __pow__(self, r) -> "Dimension":
        f = Fraction(r)
        return Dimension(tuple(a * f for a in self.exp))

    def __eq__(self, autre) -> bool:
        return isinstance(autre, Dimension) and self.exp == autre.exp

    def __hash__(self):
        return hash(self.exp)

    def sans_dimension(self) -> bool:
        return all(e == 0 for e in self.exp)

    def formule(self) -> str:
        """Écriture lisible, ex. « M·L·T⁻² » ; « 1 » si sans dimension."""
        morceaux = []
        for sym, e in zip(_BASE, self.exp):
            if e == 0:
                continue
            if e == 1:
                morceaux.append(sym)
            else:
                s = (str(e.numerator) if e.denominator == 1 else f"{e.numerator}/{e.denominator}")
                morceaux.append(sym + s.translate(_EXPOSANTS))
        return "·".join(morceaux) if morceaux else "1"

    def __repr__(self):
        return f"Dimension({self.formule()})"


def _base(sym: str) -> Dimension:
    return Dimension(tuple(1 if b == sym else 0 for b in _BASE))


# — Les 7 dimensions de base —
SANS = Dimension()
MASSE = _base("M")
LONGUEUR = _base("L")
TEMPS = _base("T")
COURANT = _base("I")
TEMPERATURE = _base("Θ")
QUANTITE = _base("N")
INTENSITE_LUMINEUSE = _base("J")

# — Dérivées usuelles (construites par l'algèbre, donc exactes par construction) —
AIRE = LONGUEUR ** 2
VOLUME = LONGUEUR ** 3
VITESSE = LONGUEUR / TEMPS
ACCELERATION = LONGUEUR / TEMPS ** 2
FREQUENCE = TEMPS ** -1
FORCE = MASSE * ACCELERATION                       # M·L·T⁻²  (newton)
PRESSION = FORCE / AIRE                             # M·L⁻¹·T⁻² (pascal)
ENERGIE = FORCE * LONGUEUR                          # M·L²·T⁻²  (joule)
PUISSANCE = ENERGIE / TEMPS                         # M·L²·T⁻³  (watt)
MASSE_VOLUMIQUE = MASSE / VOLUME
DEBIT_VOLUMIQUE = VOLUME / TEMPS
CHARGE = COURANT * TEMPS                            # A·s (coulomb)
TENSION = PUISSANCE / COURANT                       # volt
RESISTANCE = TENSION / COURANT                      # ohm
CAPACITE_ELEC = CHARGE / TENSION                    # farad
QUANTITE_MOUVEMENT = MASSE * VITESSE
CONDUCTIVITE_THERMIQUE = PUISSANCE / (LONGUEUR * TEMPERATURE)   # W·m⁻¹·K⁻¹


# ─────────────────────────────────────────────────────────────────────────────────────────
#  HOMOGÉNÉITÉ — le filtre FAUX=0
# ─────────────────────────────────────────────────────────────────────────────────────────
def homogene(*dims: Dimension) -> bool:
    """True ssi toutes les dimensions sont ÉGALES (donc additionnables/comparables). Vide/singleton -> True."""
    if not dims:
        return True
    ref = dims[0]
    return all(d == ref for d in dims)


def verifie_somme(d1: Dimension, d2: Dimension):
    """Dimension de d1+d2 (=d1) si homogènes, sinon None (HORS : addition dimensionnellement impossible)."""
    return d1 if d1 == d2 else None


def verifie_egalite(*membres: Dimension) -> bool:
    """Une équation `a = b = c …` n'est dimensionnellement VALIDE que si tous les membres ont la même dimension.
    C'est ce qui rejette une loi mal formée (ex. « force = masse × vitesse ») avant tout calcul."""
    return homogene(*membres)


# ─────────────────────────────────────────────────────────────────────────────────────────
#  UNITÉS & CONVERSION — facteurs EXACTS (Fraction) ; None (HORS) si incommensurable
# ─────────────────────────────────────────────────────────────────────────────────────────
class Unite:
    """Unité de mesure : dimension + facteur vers l'unité SI de base (valeur_SI = valeur*facteur + décalage).
    `decalage` != 0 seulement pour les échelles AFFINES (°C, °F) : la conversion porte alors sur une valeur ABSOLUE.
    (Une DIFFÉRENCE de température se convertit au facteur seul — hors périmètre de convertit(), qui traite l'absolu.)"""

    __slots__ = ("symbole", "dimension", "facteur", "decalage")

    def __init__(self, symbole, dimension, facteur, decalage=0):
        self.symbole = symbole
        self.dimension = dimension
        self.facteur = Fraction(facteur)
        self.decalage = Fraction(decalage)

    def vers_si(self, valeur):
        return valeur * self.facteur + self.decalage

    def depuis_si(self, valeur_si):
        return (valeur_si - self.decalage) / self.facteur

    def __repr__(self):
        return f"Unite({self.symbole}, {self.dimension.formule()})"


# Registre curé. Facteurs EXACTS uniquement (définitions, pas de constantes mesurées).
UNITES = {
    # longueur
    "m": Unite("m", LONGUEUR, 1),
    "km": Unite("km", LONGUEUR, 1000),
    "cm": Unite("cm", LONGUEUR, Fraction(1, 100)),
    "mm": Unite("mm", LONGUEUR, Fraction(1, 1000)),
    "pouce": Unite("pouce", LONGUEUR, Fraction(254, 10000)),      # 0.0254 m EXACT
    "pied": Unite("pied", LONGUEUR, Fraction(3048, 10000)),       # 0.3048 m EXACT
    "mile": Unite("mile", LONGUEUR, Fraction(1609344, 1000)),     # 1609.344 m EXACT
    # masse
    "kg": Unite("kg", MASSE, 1),
    "g": Unite("g", MASSE, Fraction(1, 1000)),
    "t": Unite("t", MASSE, 1000),
    "livre": Unite("livre", MASSE, Fraction(45359237, 100000000)),  # 0.45359237 kg EXACT
    # temps
    "s": Unite("s", TEMPS, 1),
    "min": Unite("min", TEMPS, 60),
    "h": Unite("h", TEMPS, 3600),
    "jour": Unite("jour", TEMPS, 86400),
    # vitesse
    "m/s": Unite("m/s", VITESSE, 1),
    "km/h": Unite("km/h", VITESSE, Fraction(1000, 3600)),
    # dérivées SI cohérentes (facteur 1)
    "N": Unite("N", FORCE, 1),
    "J": Unite("J", ENERGIE, 1),
    "W": Unite("W", PUISSANCE, 1),
    "Pa": Unite("Pa", PRESSION, 1),
    "Hz": Unite("Hz", FREQUENCE, 1),
    "C": Unite("C", CHARGE, 1),
    "V": Unite("V", TENSION, 1),
    "Ω": Unite("Ω", RESISTANCE, 1),
    # énergie non-SI usuelle (définitions exactes)
    "kWh": Unite("kWh", ENERGIE, 3600000),                       # 3.6e6 J EXACT
    "kJ": Unite("kJ", ENERGIE, 1000),
    # pression usuelle
    "bar": Unite("bar", PRESSION, 100000),
    "hPa": Unite("hPa", PRESSION, 100),
    # température (affines)
    "K": Unite("K", TEMPERATURE, 1),
    "°C": Unite("°C", TEMPERATURE, 1, Fraction(27315, 100)),      # K = °C + 273.15
    "°F": Unite("°F", TEMPERATURE, Fraction(5, 9), Fraction(45967, 180)),  # K = (°F-32)*5/9 + 273.15
}


def convertit(valeur, source, cible):
    """Convertit `valeur` de l'unité `source` vers `cible` (symboles ou objets Unite). EXACT si l'entrée est
    exacte (int/Fraction). Renvoie None (HORS) si les unités sont INCOMMENSURABLES (dimensions différentes) ou
    inconnues — jamais un nombre fabriqué. FAUX=0."""
    u1 = UNITES.get(source) if isinstance(source, str) else source
    u2 = UNITES.get(cible) if isinstance(cible, str) else cible
    if not isinstance(u1, Unite) or not isinstance(u2, Unite):
        return None                                              # unité inconnue -> HORS
    if u1.dimension != u2.dimension:
        return None                                              # incommensurable -> HORS
    return u2.depuis_si(u1.vers_si(valeur))


def dimension_de(symbole: str):
    """Dimension d'une unité connue, ou None si inconnue."""
    u = UNITES.get(symbole)
    return u.dimension if isinstance(u, Unite) else None


def commensurables(a: str, b: str) -> bool:
    """True ssi les deux unités connues partagent la même dimension (donc convertibles)."""
    da, db = dimension_de(a), dimension_de(b)
    return da is not None and da == db
