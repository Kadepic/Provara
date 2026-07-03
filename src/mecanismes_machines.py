"""
MACHINES ET MÉCANISMES — mobilité d'un mécanisme plan (critère de Grübler–Kutzbach).

Posture FAUX=0 (la réalité — ici la cinématique — juge, jamais un faux) :
  • Le MÉCANISME est EXACT et ÉTABLI : pour un mécanisme PLAN, le degré de mobilité (nombre de
    degrés de liberté du mouvement d'ensemble) vaut

            M = 3·(n − 1) − 2·j1 − j2

    où  n  = nombre de CORPS (solides, y compris le bâti/châssis fixe),
        j1 = nombre de liaisons à 1 ddl dans le plan (paires inférieures : pivot, glissière…),
             chacune SUPPRIME 2 ddl,
        j2 = nombre de liaisons à 2 ddl dans le plan (paires supérieures : came, contact
             d'engrenage…), chacune SUPPRIME 1 ddl.
    Le « n − 1 » retranche le bâti : un solide libre dans le plan a 3 ddl (2 translations + 1 rotation),
    et le bâti, immobile, n'en apporte aucun.

  • INTERPRÉTATION (établie) :
        M = 1  -> mouvement DÉTERMINÉ par UN seul actionneur (cas usuel : 4 barres, bielle-manivelle,
                  came, train d'engrenage simple, six-barres de Watt/Stephenson) ;
        M = 0  -> STRUCTURE isostatique (mécanisme « bloqué », aucun mouvement : triangle articulé) ;
        M ≥ 1  -> MOBILE ( M actionneurs indépendants requis pour un mouvement déterminé) ;
        M < 0  -> structure HYPERSTATIQUE (surcontrainte, liaisons surabondantes).

GARANTIES (vérifiées en adverse par `valide_mecanismes_machines.py`) :
  - les COMPTES sont des entiers NON négatifs ; n_corps ≥ 1 (il faut au moins un bâti) ;
  - entrée invalide (n < 1, liaisons < 0, type non entier, booléen) -> ValueError (abstention, jamais un faux) ;
  - fonctions PURES, DÉTERMINISTES ; aucune autre dépendance que la stdlib.

Ce module se FOCALISE sur la mobilité / les degrés de liberté ; l'avantage mécanique (rapport de forces)
est traité ailleurs.
"""
from __future__ import annotations

# Étiquettes de nature (déterminées par le signe/valeur de M)
MECANISME = "mecanisme"                       # M >= 1 : mobile
STRUCTURE_ISOSTATIQUE = "structure_isostatique"   # M == 0 : bloqué, exactement contraint
STRUCTURE_HYPERSTATIQUE = "structure_hyperstatique"  # M < 0 : surcontraint

SOURCE = "critère de Grübler–Kutzbach (mécanisme plan)"


def _entier_non_negatif(x, nom: str, mini: int) -> int:
    """Valide qu'un COMPTE est un entier (pas un booléen, pas un flottant) ≥ mini ; sinon ValueError."""
    if isinstance(x, bool):
        raise ValueError(f"{nom} : un compteur ne peut pas être un booléen ({x!r})")
    if not isinstance(x, int):
        raise ValueError(f"{nom} : compteur entier attendu, reçu {type(x).__name__} ({x!r})")
    if x < mini:
        raise ValueError(f"{nom} = {x} : doit être ≥ {mini}")
    return x


def mobilite(n_corps, n_liaisons_1ddl, n_liaisons_2ddl: int = 0) -> int:
    """
    Degré de mobilité M d'un mécanisme PLAN (Grübler–Kutzbach) :

        M = 3·(n_corps − 1) − 2·n_liaisons_1ddl − n_liaisons_2ddl

    n_corps INCLUT le bâti (≥ 1). Compteurs entiers non négatifs.
    Entrée invalide -> ValueError (abstention).
    """
    n = _entier_non_negatif(n_corps, "n_corps", 1)
    j1 = _entier_non_negatif(n_liaisons_1ddl, "n_liaisons_1ddl", 0)
    j2 = _entier_non_negatif(n_liaisons_2ddl, "n_liaisons_2ddl", 0)
    return 3 * (n - 1) - 2 * j1 - j2


# `degres_liberte` = synonyme établi : la mobilité EST le nombre de degrés de liberté du mécanisme.
degres_liberte = mobilite


def mouvement_determine(n_corps, n_liaisons_1ddl, n_liaisons_2ddl: int = 0) -> bool:
    """True ssi M = 1 : le mouvement est déterminé par un seul actionneur (entrée). Invalide -> ValueError."""
    return mobilite(n_corps, n_liaisons_1ddl, n_liaisons_2ddl) == 1


def est_structure(n_corps, n_liaisons_1ddl, n_liaisons_2ddl: int = 0) -> bool:
    """True ssi M ≤ 0 : aucun mouvement possible (structure bloquée ou hyperstatique). Invalide -> ValueError."""
    return mobilite(n_corps, n_liaisons_1ddl, n_liaisons_2ddl) <= 0


def nature(n_corps, n_liaisons_1ddl, n_liaisons_2ddl: int = 0) -> str:
    """
    Classe le système d'après M :
        M ≥ 1 -> MECANISME (mobile) ; M = 0 -> STRUCTURE_ISOSTATIQUE ; M < 0 -> STRUCTURE_HYPERSTATIQUE.
    Invalide -> ValueError.
    """
    M = mobilite(n_corps, n_liaisons_1ddl, n_liaisons_2ddl)
    if M >= 1:
        return MECANISME
    if M == 0:
        return STRUCTURE_ISOSTATIQUE
    return STRUCTURE_HYPERSTATIQUE
