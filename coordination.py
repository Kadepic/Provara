"""COORDINATION / COMPLEXES — chimie de coordination, mécanisme EXACT, FAUX=0 (formule/concept 2026-06-29).

Trois mécanismes vérifiables, sans aucune réponse inventée :

1) Nombre d'oxydation du métal central : n.o.(M) = charge_complexe − Σ charges des ligands.
   C'est de l'arithmétique exacte sur un CATALOGUE de charges de ligands ÉTABLIES (faits de chimie certains :
   halogénures −1, ammine 0, aqua 0, cyano −1, hydroxo −1, oxalato −2, EDTA −4, …).
   Ex. [Fe(CN)6]³⁻ : Fe = −3 − 6·(−1) = +3. [Co(NH3)6]³⁺ : Co = +3 − 6·0 = +3.

2) Règle des 18 électrons : compte = d + 2·n (d électrons du métal + 2 par ligand donneur σ).
   Ex. [Co(NH3)6]³⁺ (Co³⁺ = d6, 6 donneurs) → 6 + 12 = 18. Ni(CO)4 (d10, 4) → 18.

3) Nombre de coordination = nombre d'atomes donneurs = Σ denticités des ligands.
   Pour des ligands monodentés c'est len(ligands) ; pour [Co(en)3]³⁺ (en bidenté) c'est 3·2 = 6.

ABSTENTION STRUCTURELLE : ligand HORS catalogue -> ValueError ; charge/d/n invalides -> ValueError.
Jamais de charge de ligand devinée. Tout ligand dont la denticité est ambiguë (ex. carbonato, oxido pontant)
est volontairement ABSENT du catalogue.

Vérifié en adverse par `valide_coordination.py` (ancres : ferricyanure +3, hexammine cobalt(III) +3, 18 e⁻…).
"""
from __future__ import annotations

# Catalogue de ligands : nom canonique -> (charge, denticité). Faits de chimie ÉTABLIS et NON AMBIGUS.
# charge = charge formelle du ligand ; denticité = nombre d'atomes donneurs (sites de liaison) certain.
_LIGANDS = {
    # --- monodentés, denticité 1 ---
    "Cl-": (-1, 1),   # chlorido
    "Br-": (-1, 1),   # bromido
    "I-": (-1, 1),    # iodido
    "F-": (-1, 1),    # fluorido
    "CN-": (-1, 1),   # cyano
    "OH-": (-1, 1),   # hydroxo
    "H-": (-1, 1),    # hydrido
    "NO2-": (-1, 1),  # nitro/nitrito (ambidenté mais 1 atome donneur)
    "SCN-": (-1, 1),  # thiocyanato (ambidenté mais 1 atome donneur)
    "NH3": (0, 1),    # ammine
    "H2O": (0, 1),    # aqua
    "CO": (0, 1),     # carbonyl
    "NO": (0, 1),     # nitrosyl (compté ici comme donneur neutre 1 site)
    "py": (0, 1),     # pyridine
    "PPh3": (0, 1),   # triphénylphosphine
    # --- bidentés, denticité 2 ---
    "en": (0, 2),       # éthylènediamine
    "bpy": (0, 2),      # 2,2'-bipyridine
    "phen": (0, 2),     # 1,10-phénanthroline
    "C2O4^2-": (-2, 2),  # oxalato
    "acac-": (-1, 2),    # acétylacétonato
    # --- hexadenté, denticité 6 ---
    "EDTA^4-": (-4, 6),  # éthylènediaminetétraacétato (entièrement déprotoné)
}

# Alias acceptés (synonymes certains) vers la clé canonique.
_ALIAS = {
    "ox": "C2O4^2-", "ox^2-": "C2O4^2-", "oxalato": "C2O4^2-",
    "EDTA": "EDTA^4-", "edta": "EDTA^4-",
    "Cl": "Cl-", "Br": "Br-", "I": "I-", "F": "F-",
    "CN": "CN-", "OH": "OH-",
    "NH₃": "NH3", "H₂O": "H2O",
}


def _cle(ligand) -> str:
    """Normalise un nom de ligand vers la clé du catalogue ou lève ValueError (abstention)."""
    if not isinstance(ligand, str):
        raise ValueError(f"ligand attendu str, reçu {ligand!r}")
    nom = ligand.strip()
    if nom in _LIGANDS:
        return nom
    if nom in _ALIAS:
        return _ALIAS[nom]
    raise ValueError(f"ligand inconnu : {ligand!r} (hors catalogue -> abstention)")


def charge_ligand(ligand: str) -> int:
    """Charge formelle d'un ligand connu. Ligand inconnu -> ValueError."""
    return _LIGANDS[_cle(ligand)][0]


def denticite(ligand: str) -> int:
    """Nombre d'atomes donneurs (denticité) d'un ligand connu. Inconnu -> ValueError."""
    return _LIGANDS[_cle(ligand)][1]


def _verifie_ligands(ligands) -> list:
    if isinstance(ligands, (str, bytes)) or not isinstance(ligands, (list, tuple)):
        raise ValueError(f"liste de ligands attendue, reçu {ligands!r}")
    if len(ligands) == 0:
        raise ValueError("un complexe doit avoir au moins un ligand")
    return [_cle(l) for l in ligands]


def nombre_oxydation_metal(charge_complexe: int, ligands: list) -> int:
    """n.o. du métal central = charge_complexe − Σ charges des ligands.

    charge_complexe : entier (charge globale de l'ion complexe).
    ligands : liste des ligands (catalogue connu). Ligand inconnu -> ValueError.
    Ex. [Fe(CN)6]³⁻ : nombre_oxydation_metal(-3, ['CN-']*6) = +3.
    """
    if isinstance(charge_complexe, bool) or not isinstance(charge_complexe, int):
        raise ValueError(f"charge_complexe entière attendue, reçu {charge_complexe!r}")
    cles = _verifie_ligands(ligands)
    somme = sum(_LIGANDS[c][0] for c in cles)
    return charge_complexe - somme


def nombre_coordination(ligands: list) -> int:
    """Nombre de coordination = nombre d'atomes donneurs = Σ denticités.

    Pour des ligands monodentés vaut len(ligands). Ligand inconnu -> ValueError.
    Ex. nombre_coordination(['NH3']*6) = 6 ; nombre_coordination(['en']*3) = 6.
    """
    cles = _verifie_ligands(ligands)
    return sum(_LIGANDS[c][1] for c in cles)


def compte_electrons_18(electrons_d_metal: int, n_ligands_donneurs: int) -> int:
    """Compte d'électrons de valence (règle des 18 électrons) = d + 2·n.

    electrons_d_metal : nombre d'électrons d du métal (0..10).
    n_ligands_donneurs : nombre de ligands donneurs σ à 2 électrons.
    Ex. [Co(NH3)6]³⁺ : compte_electrons_18(6, 6) = 18.
    """
    if isinstance(electrons_d_metal, bool) or not isinstance(electrons_d_metal, int):
        raise ValueError(f"électrons d entiers attendus, reçu {electrons_d_metal!r}")
    if isinstance(n_ligands_donneurs, bool) or not isinstance(n_ligands_donneurs, int):
        raise ValueError(f"n entier attendu, reçu {n_ligands_donneurs!r}")
    if not (0 <= electrons_d_metal <= 10):
        raise ValueError(f"électrons d hors plage 0..10 : {electrons_d_metal}")
    if n_ligands_donneurs < 0:
        raise ValueError(f"nombre de ligands donneurs négatif : {n_ligands_donneurs}")
    return electrons_d_metal + 2 * n_ligands_donneurs


def respecte_regle_18(electrons_d_metal: int, n_ligands_donneurs: int) -> bool:
    """True ssi le compte d'électrons vaut exactement 18."""
    return compte_electrons_18(electrons_d_metal, n_ligands_donneurs) == 18


def _p_coordination() -> bool:
    import coordination as M

    def _leve_v(fn, *a) -> bool:
        try:
            fn(*a)
            return False
        except ValueError:
            return True
        except Exception:
            return False

    return (M.nombre_oxydation_metal(-3, ["CN-"] * 6) == 3       # [Fe(CN)6]³⁻
            and M.nombre_oxydation_metal(-4, ["CN-"] * 6) == 2   # [Fe(CN)6]⁴⁻
            and M.nombre_oxydation_metal(3, ["NH3"] * 6) == 3    # [Co(NH3)6]³⁺
            and M.nombre_oxydation_metal(-2, ["Cl-"] * 4) == 2   # [PtCl4]²⁻
            and M.nombre_coordination(["NH3"] * 6) == 6
            and M.nombre_coordination(["en"] * 3) == 6           # bidenté
            and M.compte_electrons_18(6, 6) == 18                # Co³⁺ d6
            and M.compte_electrons_18(10, 4) == 18               # Ni(CO)4
            and M.respecte_regle_18(8, 5) is True                # Fe(CO)5
            and _leve_v(M.nombre_oxydation_metal, 0, ["XYZ"])    # ligand inconnu
            and _leve_v(M.nombre_coordination, ["Zz-"])          # ligand inconnu
            and _leve_v(M.compte_electrons_18, 11, 6))           # d hors plage


if __name__ == "__main__":
    print("[Fe(CN)6]3-  n.o. Fe =", nombre_oxydation_metal(-3, ["CN-"] * 6))
    print("[Co(NH3)6]3+ n.o. Co =", nombre_oxydation_metal(3, ["NH3"] * 6))
    print("nombre de coordination [Co(NH3)6]3+ =", nombre_coordination(["NH3"] * 6))
    print("18 e- [Co(NH3)6]3+ ?", respecte_regle_18(6, 6))
