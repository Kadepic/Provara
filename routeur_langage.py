"""
ROUTEUR DE LANGAGE — « l'IA trie les langages selon le besoin » (2026-07-02, vision Yohan, portfolio polyglotte).

Relie la DÉTECTION d'environnement (environnement.py : quels langages présents, à quoi chacun excelle) aux BACKENDS
jugeables (executeur.EXECUTEURS : ceux qu'on sait générer+compiler+juger). Pour un BESOIN (perf/web/systeme/…),
`choisit` rend le MEILLEUR langage à la fois PRÉSENT et doté d'un Executeur — de sorte que l'IA génère dans le langage
le mieux placé et que le JUGE tranche (FAUX=0 quel que soit le langage).

FAUX=0 : ne propose QU'UN langage réellement exécutable ET jugeable (présent + backend). Aucun match -> None
(l'appelant garde le défaut Python). Aucune promesse sur un langage absent ou sans backend.
Stdlib pur, souverain.
"""
from __future__ import annotations

import environnement
from executeur import EXECUTEURS


def backends_disponibles() -> list:
    """Langages à la fois PRÉSENTS (environnement) ET jugeables (ont un Executeur) — le portfolio réel end-to-end."""
    return sorted(set(environnement.disponibles()) & set(EXECUTEURS))


def choisit(besoin: str):
    """Meilleur langage présent AVEC backend pour `besoin` -> (langage, Executeur), ou None. Ordre = tri
    d'adéquation d'environnement.pour_besoin (spécialiste d'abord). FAUX=0 : jamais un langage non jugeable."""
    for lang in environnement.pour_besoin(besoin):
        if lang in EXECUTEURS:
            return (lang, EXECUTEURS[lang])
    return None


def executeur_pour(langage: str):
    """L'Executeur d'un langage nommé s'il est présent ET jugeable, sinon None (jamais un backend absent)."""
    if langage in EXECUTEURS and langage in environnement.disponibles():
        return EXECUTEURS[langage]
    return None
