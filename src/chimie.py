"""
CHIMIE BORNÉE — stœchiométrie de base (mandat Yohan 2026-06-23 : « tous les sujets bornés, cités ou jamais »).

Domaine BORNÉ par la réalité (cat PHYSIQUE/CONVENTION) : les MASSES ATOMIQUES STANDARD sont des constantes
établies (valeurs conventionnelles IUPAC). À partir d'elles, des grandeurs sont EXACTEMENT calculables :
  • masse molaire d'une formule (somme pondérée des masses atomiques) ;
  • nombre d'atomes / composition élémentaire d'une formule ;
  • pourcentage massique d'un élément dans un composé.

CE QUI EST BORNÉ (sound) : le MÉCANISME parse-formule + somme est EXACT. C'est la garantie.
CE QUI EST UNE DONNÉE SOURCÉE : les valeurs de masse atomique (référentiel IUPAC ; certaines portent une
incertitude / varient selon la source). Comme `regle`/`base_faits` : le mécanisme est garanti, le contenu est
une donnée apprise, sourcée. On rend une valeur ARRONDIE (3 décimales) — précision honnête, pas un faux exact.

GARANTIES STRUCTURELLES (vérifiées en adverse par `valide_chimie.py`) :
  - élément INCONNU du référentiel -> (HORS, None) : JAMAIS une masse inventée ;
  - formule MAL FORMÉE (parenthèses déséquilibrées, minuscule en tête, caractère invalide) -> (HORS, None) ;
  - parenthèses imbriquées, multiplicateurs de groupe et HYDRATES (CuSO4·5H2O) gérés exactement ;
  - déterministe.
"""
from __future__ import annotations

import re

VERIFIE = "verifie"
HORS = "hors"

SOURCE = "masses atomiques standard IUPAC (valeurs conventionnelles)"

# Masses atomiques standard conventionnelles (g/mol), IUPAC. Sous-ensemble des éléments courants.
# Élément absent -> HORS (jamais deviné). Étendre = ajouter une entrée sourcée (même boucle).
MASSES = {
    "H": 1.008, "He": 4.0026, "Li": 6.94, "Be": 9.0122, "B": 10.81, "C": 12.011,
    "N": 14.007, "O": 15.999, "F": 18.998, "Ne": 20.180, "Na": 22.990, "Mg": 24.305,
    "Al": 26.982, "Si": 28.085, "P": 30.974, "S": 32.06, "Cl": 35.45, "Ar": 39.948,
    "K": 39.098, "Ca": 40.078, "Sc": 44.956, "Ti": 47.867, "V": 50.942, "Cr": 51.996,
    "Mn": 54.938, "Fe": 55.845, "Co": 58.933, "Ni": 58.693, "Cu": 63.546, "Zn": 65.38,
    "Ga": 69.723, "Ge": 72.630, "As": 74.922, "Se": 78.971, "Br": 79.904, "Kr": 83.798,
    "Rb": 85.468, "Sr": 87.62, "Y": 88.906, "Zr": 91.224, "Nb": 92.906, "Mo": 95.95,
    "Ru": 101.07, "Rh": 102.906, "Pd": 106.42, "Ag": 107.868, "Cd": 112.414, "In": 114.818,
    "Sn": 118.710, "Sb": 121.760, "Te": 127.60, "I": 126.904, "Xe": 131.293, "Cs": 132.905,
    "Ba": 137.327, "La": 138.905, "Ce": 140.116, "W": 183.84, "Pt": 195.084, "Au": 196.967,
    "Hg": 200.592, "Tl": 204.38, "Pb": 207.2, "Bi": 208.980, "Th": 232.038, "U": 238.029,
}


def _counts_simple(s: str) -> dict[str, int]:
    """Parse une formule SANS séparateur d'hydrate. Gère [A-Z][a-z]? , compteurs, ( ) [ ] imbriqués.
    Lève ValueError sur toute malformation (minuscule en tête, caractère invalide, parenthèses déséquilibrées)."""
    i, n = 0, len(s)
    stack: list[dict[str, int]] = [{}]
    while i < n:
        c = s[i]
        if c in "([":
            stack.append({})
            i += 1
        elif c in ")]":
            i += 1
            j = i
            while j < n and s[j].isdigit():
                j += 1
            mult = int(s[i:j]) if j > i else 1
            i = j
            if len(stack) == 1:
                raise ValueError("parenthèse fermante sans ouvrante")
            top = stack.pop()
            for el, k in top.items():
                stack[-1][el] = stack[-1].get(el, 0) + k * mult
        elif c.isalpha():
            if not c.isupper():
                raise ValueError("symbole d'élément invalide (minuscule en tête)")
            j = i + 1
            while j < n and s[j].islower():
                j += 1
            el = s[i:j]
            i = j
            k = i
            while k < n and s[k].isdigit():
                k += 1
            cnt = int(s[i:k]) if k > i else 1
            i = k
            stack[-1][el] = stack[-1].get(el, 0) + cnt
        else:
            raise ValueError(f"caractère invalide: {c!r}")
    if len(stack) != 1:
        raise ValueError("parenthèses déséquilibrées")
    return stack[0]


def composition(formule: str) -> tuple[str, dict[str, int] | None]:
    """(VERIFIE, {élément: nombre}) ou (HORS, None). Gère les hydrates (séparateurs . * ·, coefficient en tête)."""
    if not isinstance(formule, str):
        return (HORS, None)
    f = formule.strip().replace(" ", "")
    if not f:
        return (HORS, None)
    total: dict[str, int] = {}
    for partie in re.split(r"[.*·]", f):
        if partie == "":
            return (HORS, None)               # séparateur en double / en bord -> malformé
        m = re.match(r"^(\d+)(.+)$", partie)
        coef, corps = 1, partie
        if m:
            coef, corps = int(m.group(1)), m.group(2)
        try:
            d = _counts_simple(corps)
        except ValueError:
            return (HORS, None)
        if not d:
            return (HORS, None)
        for el, k in d.items():
            if el not in MASSES:
                return (HORS, None)           # symbole hors référentiel d'éléments réels -> jamais validé
            total[el] = total.get(el, 0) + k * coef
    if not total:
        return (HORS, None)
    return (VERIFIE, total)


def masse_molaire(formule: str) -> tuple[str, float | None]:
    """(VERIFIE, masse g/mol arrondie 3 déc.) ou (HORS, None) si élément inconnu / formule malformée."""
    st, comp = composition(formule)
    if st == HORS:
        return (HORS, None)
    total = 0.0
    for el, k in comp.items():
        if el not in MASSES:
            return (HORS, None)               # élément hors référentiel : jamais inventé
        total += MASSES[el] * k
    return (VERIFIE, round(total, 3))


def nb_atomes(formule: str) -> tuple[str, int | None]:
    """(VERIFIE, nombre total d'atomes) ou (HORS, None). N'exige PAS de connaître la masse (compte structurel)."""
    st, comp = composition(formule)
    if st == HORS:
        return (HORS, None)
    return (VERIFIE, sum(comp.values()))


def pourcentage_massique(formule: str, element: str) -> tuple[str, float | None]:
    """(VERIFIE, % massique de `element` dans le composé, arrondi 2 déc.) ou (HORS, None)."""
    st, comp = composition(formule)
    if st == HORS or not isinstance(element, str) or element not in comp or element not in MASSES:
        return (HORS, None)
    stm, m = masse_molaire(formule)
    if stm == HORS or not m:
        return (HORS, None)
    return (VERIFIE, round(100.0 * MASSES[element] * comp[element] / m, 2))


# --- Gabarit NL SOUND : extraction VÉRIFIÉE par le parseur, abstention par défaut (pas de devinette fuzzy). ---
_NL = re.compile(r"masse\s+molaire\s+(?:de\s+|du\s+|d['’]\s*)?([A-Za-z0-9()\[\].*·]+)", re.I)


def repond_nl(texte: str) -> tuple[str, float | None, str]:
    """Reconnaît « masse molaire de <FORMULE> ». L'extraction est VALIDÉE par masse_molaire (parse réel) :
    si la formule est invalide/inconnue -> HORS (jamais un faux). (statut, valeur, formule_extraite)."""
    if not isinstance(texte, str):
        return (HORS, None, "")
    m = _NL.search(texte)
    if not m:
        return (HORS, None, "")
    formule = m.group(1).rstrip(" ?.")
    st, val = masse_molaire(formule)
    return (st, val, formule)


if __name__ == "__main__":
    for f in ["H2O", "CO2", "NaCl", "C6H12O6", "H2SO4", "CaCO3", "(NH4)2SO4",
              "Ca(OH)2", "Fe2(SO4)3", "CuSO4.5H2O", "Xx2", "h2o", "Ca(OH", ""]:
        print(f"{f:14s} -> masse {masse_molaire(f)} | atomes {nb_atomes(f)}")
    print("\nNL:", repond_nl("Quelle est la masse molaire de H2O ?"))
    print("% O dans H2O:", pourcentage_massique("H2O", "O"))
