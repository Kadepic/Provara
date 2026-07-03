"""
OXYDORÉDUCTION — nombre d'oxydation (n.o.) dans un composé NEUTRE + électrons échangés.

MÉCANISME EXACT (déterministe, FAUX=0) :
  n.o. d'un élément cible = on résout l'équation de neutralité « Σ (n.o.ᵢ × nbᵢ) = 0 » lorsque l'élément cible
  est la SEULE inconnue. Les autres éléments reçoivent un n.o. FIXÉ par des règles sûres :
      • F  = −1 (toujours, élément le plus électronégatif) ;
      • métaux alcalins   Li, Na, K, Rb, Cs = +1 ;
      • alcalino-terreux   Be, Mg, Ca, Sr, Ba = +2 ;
      • O = −2  (règle « molle » : fausse dans les peroxydes/superoxydes/fluorures d'oxygène) ;
      • H = +1  (règle « molle » : fausse dans les hydrures métalliques/métalloïdiques).
  Le parseur de formule est RÉUTILISÉ depuis chimie.composition (un seul parseur, garanti).

ABSTENTION STRUCTURELLE (ValueError, JAMAIS un faux positif) :
  - formule invalide, ou élément absent du composé ;
  - PLUSIEURS éléments sans règle fixée (la cible n'est pas la seule inconnue) ;
  - n.o. de la cible non entier (ex. superoxyde KO₂ : O = −½ → on refuse) ;
  - n.o. de la cible HORS de sa plage d'oxydation réelle documentée (garde anti-peroxyde :
    CrO₅ « donnerait » +10 > +6 → refus ; H₂O₂ pour H « donnerait » +2 > +1 → refus) ;
  - règle H=+1 utilisée pour un H NON-cible alors qu'un voisin est MOINS électronégatif que H
    (SiH₄, B₂H₆, PH₃ ambigu) → refus (condition suffisante : tous les voisins de H plus électronégatifs).

Ce que la méthode obtient JUSTE sans tricher (la cible est résolue, pas devinée) :
  - S dans H₂SO₄ = +6 ; S dans H₂S = −2 ; Mn dans KMnO₄ = +7 ; Cr dans K₂Cr₂O₇ = +6 ;
    N dans HNO₃ = +5 ; C dans CO₂ = +4 ; O peroxyde (H₂O₂, Na₂O₂) résolu = −1 ; H hydrure (NaH) = −1.

equilibre_electronique(no_avant, no_apres) = nombre d'électrons échangés = |Δ n.o.| (entiers requis).

Stdlib uniquement. Import léger : `import chimie` (qui n'importe que `re`).
"""
from __future__ import annotations

import chimie

# n.o. FIXÉS et sûrs pour un élément NON-cible.
_HARD = {
    "F": -1,
    "Li": 1, "Na": 1, "K": 1, "Rb": 1, "Cs": 1,
    "Be": 2, "Mg": 2, "Ca": 2, "Sr": 2, "Ba": 2,
}
# Règles « molles » O/H : valables seulement sous garde (peroxyde / hydrure).
_SOFT = {"O": -2, "H": 1}
# Règle utilisable pour un élément NON-cible = règle dure OU molle.
_RULES = {**_HARD, **_SOFT}

# Éléments STRICTEMENT plus électronégatifs que H (Pauling > 2.20). Si tous les voisins d'un H non-cible
# sont dans cet ensemble, alors H est forcément l'électropositif partout -> H=+1 est SÛR.
_EN_GT_H = {"C", "N", "O", "F", "S", "Cl", "Se", "Br", "I"}

# Plage d'oxydation RÉELLE documentée (min, max) pour la cible. La borne MAX = maximum réel connu de
# l'élément : un n.o. calculé au-dessus trahit une hypothèse fausse (peroxyde gonfle le n.o.) -> abstention.
# Élément absent de cette table (et non « dur ») -> abstention (on ne garantit pas).
_RANGE = {
    "H": (-1, 1), "B": (-3, 3), "C": (-4, 4), "N": (-3, 5), "O": (-2, 2),
    "Al": (0, 3), "Si": (-4, 4), "P": (-3, 5), "S": (-2, 6), "Cl": (-1, 7),
    "Sc": (0, 3), "Ti": (0, 4), "V": (0, 5), "Cr": (-4, 6), "Mn": (-3, 7),
    "Fe": (-2, 6), "Cu": (0, 3), "Zn": (0, 2), "As": (-3, 5), "Se": (-2, 6),
    "Br": (-1, 7), "Mo": (0, 6), "Sn": (-4, 4), "Sb": (-3, 5), "Te": (-2, 6),
    "I": (-1, 7), "W": (0, 6), "Re": (0, 7), "Pb": (-4, 4), "Bi": (-3, 5),
}

SOURCE = "règles de n.o. (IUPAC) + plages d'oxydation documentées ; parseur = chimie.composition"


def _composition(formule) -> dict[str, int]:
    """Composition élémentaire via chimie.composition, ValueError si la formule est invalide."""
    st, comp = chimie.composition(formule)
    if st != chimie.VERIFIE or not comp:
        raise ValueError("formule invalide")
    return comp


def nombre_oxydation(formule, element) -> int:
    """n.o. de `element` dans le composé NEUTRE `formule`.

    Renvoie un entier si — et seulement si — la règle donne une réponse UNIQUE et sûre.
    Lève ValueError sinon (formule invalide, élément absent, plusieurs inconnues, n.o. non entier,
    n.o. hors plage réelle, ou hypothèse H=+1 non garantie).
    """
    if not isinstance(element, str) or not element:
        raise ValueError("élément invalide")
    comp = _composition(formule)
    if element not in comp:
        raise ValueError("élément absent du composé")

    # Cas « dur » : group 1/2 et F valent toujours leur n.o. fixe dans un composé neutre réel.
    if element in _HARD:
        return _HARD[element]

    # Sinon il faut connaître la plage réelle de la cible (sinon on ne garantit rien).
    if element not in _RANGE:
        raise ValueError("élément cible hors référentiel de plages d'oxydation")

    others = {e: n for e, n in comp.items() if e != element}

    # Tous les autres éléments doivent avoir une règle (sinon : plusieurs inconnues).
    for e in others:
        if e not in _RULES:
            raise ValueError(f"plusieurs inconnues : {e} sans n.o. fixé")

    # Garde hydrure : si un H non-cible est présent (donc supposé +1), exiger que TOUS les voisins
    # soient plus électronégatifs que H (condition suffisante pour H=+1).
    if "H" in others:
        for e in comp:
            if e != "H" and e not in _EN_GT_H:
                raise ValueError(f"H=+1 non garanti (voisin {e} moins électronégatif)")

    somme_connue = sum(_RULES[e] * n for e, n in others.items())
    nb_cible = comp[element]
    # Neutralité : nb_cible * x + somme_connue = 0.
    if (-somme_connue) % nb_cible != 0:
        raise ValueError("n.o. non entier (composé exclu : superoxyde/ambigu)")
    x = (-somme_connue) // nb_cible

    bas, haut = _RANGE[element]
    if x < bas or x > haut:
        raise ValueError(f"n.o. {x} hors plage réelle [{bas},{haut}] (hypothèse fausse, ex. peroxyde)")
    return x


def equilibre_electronique(no_avant, no_apres) -> int:
    """Nombre d'électrons échangés par atome lors d'un changement de n.o. = |Δ n.o.|.
    Les n.o. doivent être des entiers ; sinon ValueError."""
    for v in (no_avant, no_apres):
        if isinstance(v, bool) or not isinstance(v, int):
            raise ValueError("n.o. doit être un entier")
    return abs(no_apres - no_avant)
