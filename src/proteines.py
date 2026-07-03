"""
PROTÉINES, ENZYMES — structure et classification (faits SOURCÉS établis + calculs EXACTS).

Domaine BORNÉ par la réalité : la biochimie fixe la réponse.
  • STRUCTURE des protéines : 4 niveaux d'organisation établis (primaire/secondaire/tertiaire/quaternaire) ;
  • CLASSIFICATION EC des enzymes : 6 classes établies par l'Enzyme Commission (EC 1 à EC 6) ;
  • LIAISONS PEPTIDIQUES : pour une chaîne polypeptidique LINÉAIRE de n acides aminés, il y a EXACTEMENT
    n−1 liaisons peptidiques (chaque liaison joint deux résidus consécutifs).

GARANTIE (vérifiée en adverse par valide_proteines.py) :
  - le MÉCANISME n−1 est EXACT ; les FAITS (noms des niveaux, classes EC) sont des données sourcées certaines ;
  - toute entrée HORS référentiel -> ValueError (abstention, JAMAIS un faux) :
      n_acides_amines < 1 ou non entier ; chiffre EC hors 1..6 ou non entier ; niveau inconnu ;
  - déterministe et pur.

SOURCES :
  - niveaux de structure : biochimie classique (Lehninger / IUPAC-IUBMB) — 4 niveaux établis ;
  - classification EC : Enzyme Commission, IUBMB Recommendations (classes EC 1 à 6 — classification établie).
"""
from __future__ import annotations

SOURCE = "biochimie établie (Lehninger ; classification EC, IUBMB)"

# ── STRUCTURE DES PROTÉINES — 4 niveaux d'organisation établis (ordre canonique) ──
# clé canonique (minuscule) -> description établie.
NIVEAUX_STRUCTURE: dict[str, str] = {
    "primaire": "séquence linéaire des acides aminés (ordre des résidus, liaisons peptidiques)",
    "secondaire": "repliements locaux réguliers : hélice α et feuillet β (stabilisés par liaisons hydrogène)",
    "tertiaire": "structure tridimensionnelle (3D) globale d'une seule chaîne polypeptidique repliée",
    "quaternaire": "assemblage de plusieurs sous-unités (chaînes polypeptidiques) en un complexe fonctionnel",
}

# ── CLASSIFICATION EC DES ENZYMES — 6 classes établies (1er chiffre du numéro EC) ──
CLASSES_EC: dict[int, str] = {
    1: "oxydoréductase",   # transfert d'électrons (oxydation-réduction)
    2: "transférase",      # transfert d'un groupe fonctionnel
    3: "hydrolase",        # hydrolyse (coupure par addition d'eau)
    4: "lyase",            # coupure non hydrolytique / non oxydative
    5: "isomérase",        # réarrangement intramoléculaire (isomérisation)
    6: "ligase",           # liaison de deux molécules couplée à l'hydrolyse d'un triphosphate (ATP…)
}


def _est_entier(x) -> bool:
    """True ssi x est un entier strict (exclut bool, qui est sous-classe d'int, et les flottants)."""
    return isinstance(x, int) and not isinstance(x, bool)


def niveau_structure(nom: str) -> str:
    """Description du niveau d'organisation structurale d'une protéine.

    nom ∈ {primaire, secondaire, tertiaire, quaternaire} (insensible à la casse / espaces).
    Niveau inconnu ou entrée non-str -> ValueError (abstention)."""
    if not isinstance(nom, str):
        raise ValueError(f"niveau non textuel : {nom!r}")
    cle = nom.strip().lower()
    if cle not in NIVEAUX_STRUCTURE:
        raise ValueError(f"niveau de structure inconnu : {nom!r}")
    return NIVEAUX_STRUCTURE[cle]


def nombre_niveaux_structure() -> int:
    """Nombre de niveaux d'organisation structurale des protéines : 4 (fait établi)."""
    return len(NIVEAUX_STRUCTURE)


def classe_enzyme_ec(numero_ec_1er_chiffre: int) -> str:
    """Classe enzymatique d'après le 1er chiffre du numéro EC (classification établie).

    1=oxydoréductase, 2=transférase, 3=hydrolase, 4=lyase, 5=isomérase, 6=ligase.
    Chiffre hors 1..6 ou non entier -> ValueError (abstention)."""
    if not _est_entier(numero_ec_1er_chiffre):
        raise ValueError(f"chiffre EC non entier : {numero_ec_1er_chiffre!r}")
    if numero_ec_1er_chiffre not in CLASSES_EC:
        raise ValueError(f"classe EC hors 1..6 : {numero_ec_1er_chiffre!r}")
    return CLASSES_EC[numero_ec_1er_chiffre]


def nombre_liaisons_peptidiques(n_acides_amines: int) -> int:
    """Nombre de liaisons peptidiques d'une chaîne polypeptidique LINÉAIRE de n acides aminés = n−1.

    n_acides_amines entier ≥ 1 (une chaîne a au moins 1 résidu). n < 1 ou non entier -> ValueError."""
    if not _est_entier(n_acides_amines):
        raise ValueError(f"nombre d'acides aminés non entier : {n_acides_amines!r}")
    if n_acides_amines < 1:
        raise ValueError(f"nombre d'acides aminés invalide (< 1) : {n_acides_amines!r}")
    return n_acides_amines - 1
