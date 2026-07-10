"""
TEMPS GÉOLOGIQUES — CATALOGUE de la charte ICS (International Chronostratigraphic Chart).

Posture FAUX=0 identique à `galois` / `geometries_non_euclidiennes` : on n'expose QUE des faits
CONVENTIONNELS publiés (B-CONV), jamais une devinette. Le mécanisme n'est pas une corrélation :
c'est un CATALOGUE fermé, la hiérarchie chronostratigraphique officielle de la Commission
Internationale de Stratigraphie, avec ses bornes en millions d'années (Ma).

  • Hiérarchie : éon > ère > période > époque.
  • Chaque intervalle est (début_Ma, fin_Ma) avec début STRICTEMENT plus vieux (grand) que fin.
    Convention d'appartenance d'un âge : fin ≤ âge < début (on inclut la borne JEUNE, on exclut la
    borne VIEILLE, qui est la « base » de l'unité vieille voisine). Ainsi l'instant présent (0 Ma)
    appartient à l'Holocène, et l'âge 66.0 Ma (base du Paléogène) appartient au Crétacé.
  • Bornes stockées en `fractions.Fraction` (exactes) : le pavage se prouve à l'égalité EXACTE, sans
    erreur de flottant. `intervalle`/`duree` renvoient donc des Fraction (Ma).

INVARIANTS DURS vérifiés au CHARGEMENT du module (RuntimeError si violés — le catalogue serait corrompu) :
  • pour tout intervalle : début > fin ;
  • les enfants d'un intervalle PAVENT exactement leur parent : contigus, sans trou ni recouvrement
    (enfant le plus vieux commence au début du parent, le plus jeune finit à la fin du parent, et
    chaque fin d'enfant = début de l'enfant suivant).

ABSTENTION (ValueError, jamais un faux positif) :
  • nom hors charte -> ValueError ;
  • âge non réel fini / bool / str / NaN / inf -> ValueError ;
  • âge < 0 ou > 4567 (au-delà de l'âge de la Terre) -> ValueError ;
  • âge sans unité définie au rang demandé (ex. une période avant le Phanérozoïque) -> ValueError.

GARANTIES (vérifiées en adverse par `valide_temps_geologiques.py`) :
  ancres non circulaires (limites K/Pg 66.0, P/T 251.902, base Cambrien 538.8, base Holocène 0.0117),
  routage d'âge (periode_a/ere_a/eon_a), pavage (somme des durées des périodes du Phanérozoïque =
  538.8 Ma par un chemin d'addition indépendant), soundness complète, déterminisme.
"""
from __future__ import annotations

from fractions import Fraction

SOURCE = "International Chronostratigraphic Chart, International Commission on Stratigraphy (ICS) v2023/09"

# Âge de la Terre (borne haute du domaine des âges acceptés), en Ma.
_AGE_MAX = Fraction("4567")

# Rangs de la hiérarchie, du plus englobant au plus fin.
EON, ERE, PERIODE, EPOQUE = "éon", "ère", "période", "époque"
_RANGS = (EON, ERE, PERIODE, EPOQUE)

# ── DONNÉES BRUTES : (nom, rang, début_Ma, fin_Ma, parent) — bornes ICS publiées ─────────────────────────────
# début = borne VIEILLE (grande), fin = borne JEUNE (petite). Les chaînes -> Fraction exacte.
_BRUT = [
    # Éons
    ("Hadéen",          EON, "4567",   "4031",    None),
    ("Archéen",         EON, "4031",   "2500",    None),
    ("Protérozoïque",   EON, "2500",   "538.8",   None),
    ("Phanérozoïque",   EON, "538.8",  "0",       None),
    # Ères du Phanérozoïque
    ("Paléozoïque",     ERE, "538.8",  "251.902", "Phanérozoïque"),
    ("Mésozoïque",      ERE, "251.902", "66.0",   "Phanérozoïque"),
    ("Cénozoïque",      ERE, "66.0",   "0",       "Phanérozoïque"),
    # Périodes du Paléozoïque
    ("Cambrien",        PERIODE, "538.8",  "486.85",  "Paléozoïque"),
    ("Ordovicien",      PERIODE, "486.85", "443.8",   "Paléozoïque"),
    ("Silurien",        PERIODE, "443.8",  "419.2",   "Paléozoïque"),
    ("Dévonien",        PERIODE, "419.2",  "358.9",   "Paléozoïque"),
    ("Carbonifère",     PERIODE, "358.9",  "298.9",   "Paléozoïque"),
    ("Permien",         PERIODE, "298.9",  "251.902", "Paléozoïque"),
    # Périodes du Mésozoïque
    ("Trias",           PERIODE, "251.902", "201.4", "Mésozoïque"),
    ("Jurassique",      PERIODE, "201.4",  "145.0",   "Mésozoïque"),
    ("Crétacé",         PERIODE, "145.0",  "66.0",    "Mésozoïque"),
    # Périodes du Cénozoïque
    ("Paléogène",       PERIODE, "66.0",   "23.03",   "Cénozoïque"),
    ("Néogène",         PERIODE, "23.03",  "2.58",    "Cénozoïque"),
    ("Quaternaire",     PERIODE, "2.58",   "0",       "Cénozoïque"),
    # Époques du Quaternaire
    ("Pléistocène",     EPOQUE, "2.58",   "0.0117",  "Quaternaire"),
    ("Holocène",        EPOQUE, "0.0117", "0",       "Quaternaire"),
]


class _Unite:
    __slots__ = ("nom", "rang", "debut", "fin", "parent")

    def __init__(self, nom, rang, debut, fin, parent):
        self.nom = nom
        self.rang = rang
        self.debut = debut          # Fraction, borne vieille
        self.fin = fin              # Fraction, borne jeune
        self.parent = parent        # nom du parent ou None


def _construire():
    unites = {}
    for nom, rang, deb, fin, parent in _BRUT:
        if nom in unites:
            raise RuntimeError(f"catalogue corrompu : nom dupliqué {nom!r}")
        unites[nom] = _Unite(nom, rang, Fraction(deb), Fraction(fin), parent)

    # enfants : dérivés du champ parent
    enfants = {nom: [] for nom in unites}
    for u in unites.values():
        if u.parent is not None:
            if u.parent not in unites:
                raise RuntimeError(f"catalogue corrompu : parent inconnu {u.parent!r} de {u.nom!r}")
            enfants[u.parent].append(u.nom)

    # INVARIANT 1 : début > fin pour tout intervalle
    for u in unites.values():
        if not (u.debut > u.fin):
            raise RuntimeError(f"invariant violé : début ≤ fin pour {u.nom!r} ({u.debut}..{u.fin})")

    # INVARIANT 2 : les enfants pavent exactement leur parent (contigus, sans trou ni recouvrement)
    for parent_nom, fils in enfants.items():
        if not fils:
            continue
        p = unites[parent_nom]
        # trie du plus vieux (grand début) au plus jeune
        fils_tries = sorted(fils, key=lambda n: unites[n].debut, reverse=True)
        premier = unites[fils_tries[0]]
        dernier = unites[fils_tries[-1]]
        if premier.debut != p.debut:
            raise RuntimeError(
                f"pavage violé : {premier.nom!r} ne commence pas au début de {parent_nom!r}")
        if dernier.fin != p.fin:
            raise RuntimeError(
                f"pavage violé : {dernier.nom!r} ne finit pas à la fin de {parent_nom!r}")
        for a, b in zip(fils_tries, fils_tries[1:]):
            if unites[a].fin != unites[b].debut:
                raise RuntimeError(
                    f"pavage violé : trou/recouvrement entre {a!r} et {b!r} sous {parent_nom!r}")

    return unites, {n: sorted(f, key=lambda m: unites[m].debut, reverse=True) for n, f in enfants.items()}


_UNITES, _ENFANTS = _construire()


# ── helpers de validation ────────────────────────────────────────────────────────────────────────────────────
def _est_reel_fini(x) -> bool:
    """True ssi x est un réel fini (bool REFUSÉ ; NaN/inf REFUSÉS ; str/complexe REFUSÉS).

    Fraction est accepté (exact). float NaN/inf rejeté."""
    if isinstance(x, bool):
        return False
    if isinstance(x, Fraction):
        return True
    if isinstance(x, int):
        return True
    if isinstance(x, float):
        return x == x and x not in (float("inf"), float("-inf"))
    return False


def _exige_nom(nom) -> str:
    if not isinstance(nom, str):
        raise ValueError(f"nom invalide : chaîne attendue, reçu {type(nom).__name__}")
    if nom not in _UNITES:
        raise ValueError(f"nom hors charte ICS : {nom!r} (abstention)")
    return nom


def _exige_age(age):
    """Renvoie age (numérique) validé : réel fini, 0 ≤ age ≤ 4567. Sinon ValueError."""
    if not _est_reel_fini(age):
        raise ValueError(f"âge invalide : réel fini attendu, reçu {age!r}")
    if age < 0 or age > _AGE_MAX:
        raise ValueError(f"âge hors domaine [0, 4567] Ma : {age!r} (abstention)")
    return age


# ── API ──────────────────────────────────────────────────────────────────────────────────────────────────────
def intervalle(nom: str):
    """(début_Ma, fin_Ma) de l'unité `nom` (Fraction exactes). Nom hors charte -> ValueError."""
    u = _UNITES[_exige_nom(nom)]
    return (u.debut, u.fin)


def duree(nom: str) -> Fraction:
    """Durée (Ma) de l'unité `nom` = début − fin (Fraction exacte). Nom hors charte -> ValueError."""
    u = _UNITES[_exige_nom(nom)]
    return u.debut - u.fin


def parent(nom: str):
    """Nom du parent de `nom`, ou None pour un éon (racine). Nom hors charte -> ValueError."""
    return _UNITES[_exige_nom(nom)].parent


def enfants(nom: str):
    """Tuple des noms des enfants de `nom`, du plus vieux au plus jeune (vide si feuille)."""
    return tuple(_ENFANTS[_exige_nom(nom)])


def _unite_a(age, rang):
    """Nom de l'unité de rang `rang` contenant `age` (fin ≤ age < début). Aucune -> ValueError."""
    age = _exige_age(age)
    for u in _UNITES.values():
        if u.rang == rang and u.fin <= age < u.debut:
            return u.nom
    raise ValueError(f"aucune unité de rang {rang!r} pour l'âge {age!r} Ma (abstention)")


def eon_a(age) -> str:
    """Nom de l'éon contenant `age` (Ma). Hors domaine -> ValueError."""
    return _unite_a(age, EON)


def ere_a(age) -> str:
    """Nom de l'ère contenant `age` (Ma). Aucune ère (ex. pré-Phanérozoïque) -> ValueError."""
    return _unite_a(age, ERE)


def periode_a(age) -> str:
    """Nom de la période contenant `age` (Ma). Aucune période -> ValueError."""
    return _unite_a(age, PERIODE)


def catalogue():
    """Tuple déterministe des noms de la charte, triés du plus vieux début au plus jeune."""
    return tuple(sorted(_UNITES, key=lambda n: (-_UNITES[n].debut, _UNITES[n].fin, n)))
