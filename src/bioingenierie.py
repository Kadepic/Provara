"""
BIO-INGÉNIERIE — cinétique enzymatique de Michaelis-Menten (loi ÉTABLIE, mécanisme EXACT).

Posture FAUX=0 (même que `physique`/`chimie` : la réalité juge, jamais un faux) :
  • Le MÉCANISME est la loi de Michaelis-Menten, modèle de référence de la cinétique enzymatique :
        v = Vmax · [S] / (Km + [S])
    Vmax = vitesse maximale (saturation), Km = constante de Michaelis (concentration en substrat à v=Vmax/2),
    [S] = concentration en substrat. La formule est EXACTE par définition du modèle.
  • Propriétés exactes garanties :
        - à [S] = Km                 -> v = Vmax/2          (définition même de Km)
        - à [S] >> Km                -> v -> Vmax            (saturation)
        - à [S] = 0                  -> v = 0
        - efficacité catalytique     -> kcat / Km           (constante de spécificité)
  • Déterministe, pur, stdlib uniquement.

SOUNDNESS (domaine physique de l'enzymologie) :
  - Vmax <= 0  -> ValueError (une vitesse maximale doit être strictement positive) ;
  - Km   <= 0  -> ValueError (une constante de Michaelis doit être strictement positive) ;
  - S    < 0   -> ValueError (une concentration ne peut être négative) ;
  - kcat <= 0 ou Km <= 0 (efficacité) -> ValueError ;
  - toute entrée non numérique -> ValueError (jamais une réponse inventée).
"""
from __future__ import annotations


def _num(x) -> bool:
    """Vrai si x est un nombre réel (et pas un booléen, qui est un int en Python)."""
    return isinstance(x, (int, float)) and not isinstance(x, bool)


def vitesse(Vmax: float, Km: float, S: float) -> float:
    """
    Vitesse de réaction de Michaelis-Menten : v = Vmax·S/(Km+S).

    Vmax > 0, Km > 0, S >= 0. Toute violation -> ValueError (abstention, jamais un faux).
    """
    if not (_num(Vmax) and _num(Km) and _num(S)):
        raise ValueError("Vmax, Km, S doivent être numériques")
    if Vmax <= 0:
        raise ValueError("Vmax doit être > 0 (vitesse maximale)")
    if Km <= 0:
        raise ValueError("Km doit être > 0 (constante de Michaelis)")
    if S < 0:
        raise ValueError("S (concentration en substrat) doit être >= 0")
    return Vmax * S / (Km + S)


def km_vitesse_demi(Vmax: float, Km: float) -> float:
    """
    Vitesse à [S] = Km : par définition de Km, v = Vmax/2 (EXACT).

    On l'établit en évaluant la loi en S=Km (cohérence garantie), pas par un raccourci numérique.
    """
    if not (_num(Vmax) and _num(Km)):
        raise ValueError("Vmax, Km doivent être numériques")
    if Vmax <= 0:
        raise ValueError("Vmax doit être > 0")
    if Km <= 0:
        raise ValueError("Km doit être > 0")
    return vitesse(Vmax, Km, Km)


def efficacite_catalytique(kcat: float, Km: float) -> float:
    """
    Efficacité catalytique (constante de spécificité) : kcat / Km.

    kcat > 0, Km > 0. Sinon -> ValueError.
    """
    if not (_num(kcat) and _num(Km)):
        raise ValueError("kcat, Km doivent être numériques")
    if kcat <= 0:
        raise ValueError("kcat doit être > 0 (constante catalytique)")
    if Km <= 0:
        raise ValueError("Km doit être > 0 (constante de Michaelis)")
    return kcat / Km


if __name__ == "__main__":
    # CAS de la spécification.
    print("v(10,2,2) =", vitesse(10, 2, 2))      # 5.0 = Vmax/2 (S=Km)
    print("v(10,2,6) =", vitesse(10, 2, 6))      # 7.5
    print("v(10,2,0) =", vitesse(10, 2, 0))      # 0.0
    print("v(10,2,2000) =", vitesse(10, 2, 2000))  # ~Vmax
    print("km_vitesse_demi(10,2) =", km_vitesse_demi(10, 2))  # 5.0
    print("efficacite_catalytique(100,2) =", efficacite_catalytique(100, 2))  # 50.0
