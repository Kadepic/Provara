"""
MÉTAUX ET ALLIAGES — règle du levier (lever rule) + catalogue d'alliages binaires (mandat Yohan : « tous
les sujets bornés, chirurgical, FAUX=0 »).

Domaine BORNÉ par la réalité :

  1) RÈGLE DU LEVIER (lever rule). Dans la région biphasée d'un diagramme binaire, à la composition globale
     `c` (sur la ligne de conjugaison entre la phase 1 de composition `c1` et la phase 2 de composition `c2`),
     les fractions massiques des deux phases sont fixées EXACTEMENT par le bilan de matière :
            W1·c1 + W2·c2 = c   et   W1 + W2 = 1
        =>  W2 = (c − c1) / (c2 − c1)   et   W1 = 1 − W2.
     C'est une IDENTITÉ algébrique (pas une corrélation) : le mécanisme est EXACT et déterministe.

  2) CATALOGUE D'ALLIAGES. Faits SOURCÉS et certains (métallurgie classique) — le métal de base et l'élément
     d'alliage principal :
        acier     = fer       + carbone
        bronze    = cuivre    + étain
        laiton    = cuivre    + zinc
        duralumin = aluminium + cuivre

GARANTIES (vérifiées en adverse par `valide_alliages.py`) :
  - `c` hors de l'intervalle [c1, c2]  -> ValueError (jamais une fraction hors [0,1] inventée) ;
  - `c1 == c2` (ligne de conjugaison dégénérée) -> ValueError (pas de division par zéro masquée) ;
  - entrée non numérique / non finie / booléenne -> ValueError (abstention, jamais un faux) ;
  - alliage hors catalogue -> ValueError (jamais une composition devinée) ;
  - déterministe.
"""
from __future__ import annotations

import math
from collections import namedtuple

SOURCE_LEVIER = "règle du levier (bilan de matière sur la ligne de conjugaison d'un diagramme binaire)"
SOURCE_CATALOGUE = "métallurgie classique (composition des alliages binaires de référence)"

# Fractions massiques des deux phases (somme = 1).
Fractions = namedtuple("Fractions", ["phase1", "phase2"])

# Composition de l'alliage : métal de base + élément d'alliage principal.
Alliage = namedtuple("Alliage", ["nom", "base", "ajout", "constituants"])

# Catalogue SOURCÉ. Alliage absent -> abstention (ValueError), jamais deviné.
_CATALOGUE = {
    "acier": ("fer", "carbone"),
    "bronze": ("cuivre", "étain"),
    "laiton": ("cuivre", "zinc"),
    "duralumin": ("aluminium", "cuivre"),
}


def _reel(x, nom: str) -> float:
    """Renvoie le flottant fini réel ou lève ValueError.

    Seuls les vrais nombres int/float sont acceptés (pas de coercition silencieuse de chaîne) ; booléen et
    valeur non finie (NaN/inf) refusés.
    """
    if isinstance(x, bool) or not isinstance(x, (int, float)):
        raise ValueError(f"{nom} : valeur non numérique ({x!r})")
    v = float(x)
    if not math.isfinite(v):
        raise ValueError(f"{nom} : valeur non finie ({x!r})")
    return v


def fraction_phase(c_alliage, c_phase1, c_phase2) -> Fractions:
    """Règle du levier — fractions massiques des deux phases (EXACT).

    fraction phase2 = (c_alliage − c_phase1) / (c_phase2 − c_phase1)
    fraction phase1 = 1 − fraction phase2

    `c_alliage` doit être dans l'intervalle [c_phase1, c_phase2] (quel que soit l'ordre des bornes) ; sinon, ou
    si `c_phase1 == c_phase2`, ValueError (abstention).
    """
    c = _reel(c_alliage, "c_alliage")
    c1 = _reel(c_phase1, "c_phase1")
    c2 = _reel(c_phase2, "c_phase2")
    if c1 == c2:
        raise ValueError("ligne de conjugaison dégénérée : c_phase1 == c_phase2")
    lo, hi = (c1, c2) if c1 <= c2 else (c2, c1)
    if not (lo <= c <= hi):
        raise ValueError(
            f"c_alliage={c} hors de l'intervalle [{lo}, {hi}] : pas de mélange biphasé"
        )
    f2 = (c - c1) / (c2 - c1)
    f1 = 1.0 - f2
    return Fractions(phase1=f1, phase2=f2)


def classe_alliage(nom) -> Alliage:
    """Catalogue d'alliages — métal de base + élément d'alliage principal.

    Alliage hors catalogue (ou entrée non-str) -> ValueError (abstention, jamais une composition devinée).
    """
    if not isinstance(nom, str):
        raise ValueError(f"nom d'alliage non textuel ({nom!r})")
    cle = nom.strip().lower()
    if cle not in _CATALOGUE:
        raise ValueError(f"alliage hors catalogue : {nom!r}")
    base, ajout = _CATALOGUE[cle]
    return Alliage(nom=cle, base=base, ajout=ajout, constituants=(base, ajout))


if __name__ == "__main__":
    # c=40 % entre c1=20 et c2=60 -> moitié/moitié.
    f = fraction_phase(40, 20, 60)
    print(f"fraction_phase(40, 20, 60) = phase1={f.phase1}, phase2={f.phase2}")
    print(f"classe_alliage('acier')    = {classe_alliage('acier')}")
    print(f"classe_alliage('laiton')   = {classe_alliage('laiton')}")
