"""
LOGIQUE TRIVALUÉE + MONDE OUVERT/FERMÉ (logique_tri) — brique Vague 1 (fin du socle de représentation).

POURQUOI : une machine honnête doit distinguer « connu FAUX » de « INCONNU ». Sans ça, l'absence d'un fait est prise
pour sa fausseté (« je n'ai pas l'info » devient « c'est faux ») — une sur-confiance, la ligne rouge du projet. La
négation de 1ʳᵉ classe (faits négatifs explicites) + l'hypothèse du monde ouvert (OWA) rendent l'abstention par défaut.

MODÈLE : logique TRIVALUÉE (VRAI / FAUX / INCONNU, Kleene). Un store de faits POSITIFS et de faits NÉGATIFS. Par
défaut MONDE OUVERT : ce qui n'est ni affirmé ni nié est INCONNU. Une relation peut être déclarée COMPLÈTE (monde
fermé, CWA) : alors l'absence vaut FAUX — mais SEULEMENT pour ces relations où la complétude est garantie.

FAUX=0 :
  • OWA (défaut) : jamais FAUX sans fait négatif explicite -> INCONNU au doute (abstention honnête).
  • CWA opt-in par relation déclarée complète uniquement.
  • CONTRADICTION (un fait affirmé ET nié) -> détectée (Contradiction), jamais tolérée.
  • non(INCONNU)=INCONNU ; et/ou de Kleene (INCONNU ne devient VRAI/FAUX que si l'autre opérande le force).
Stdlib pur, déterministe, souverain.
"""
from __future__ import annotations

VRAI = "vrai"
FAUX = "faux"
INCONNU = "inconnu"


class Contradiction(Exception):
    """Un même fait est à la fois affirmé et nié — incohérence, refus FAUX=0."""


def non(v):
    """Négation trivaluée : non(VRAI)=FAUX, non(FAUX)=VRAI, non(INCONNU)=INCONNU."""
    return FAUX if v == VRAI else VRAI if v == FAUX else INCONNU


def et(a, b):
    """ET de Kleene : FAUX domine ; sinon INCONNU si l'un est INCONNU ; sinon VRAI."""
    if a == FAUX or b == FAUX:
        return FAUX
    if a == INCONNU or b == INCONNU:
        return INCONNU
    return VRAI


def ou(a, b):
    """OU de Kleene : VRAI domine ; sinon INCONNU si l'un est INCONNU ; sinon FAUX."""
    if a == VRAI or b == VRAI:
        return VRAI
    if a == INCONNU or b == INCONNU:
        return INCONNU
    return FAUX


class BaseTrivaluee:
    __slots__ = ("_pos", "_neg", "_completes")

    def __init__(self):
        self._pos: set = set()           # faits affirmés VRAIS
        self._neg: set = set()           # faits explicitement niés (FAUX)
        self._completes: set = set()     # relations en monde fermé (CWA)

    def affirme(self, fait):
        if fait in self._neg:
            raise Contradiction(f"{fait!r} est déjà nié — ne peut être affirmé")
        self._pos.add(fait)

    def nie(self, fait):
        if fait in self._pos:
            raise Contradiction(f"{fait!r} est déjà affirmé — ne peut être nié")
        self._neg.add(fait)

    def declare_complete(self, relation):
        """Passe une relation en MONDE FERMÉ : pour ses faits, l'absence vaudra FAUX (CWA). À n'utiliser que si
        la relation est réellement exhaustive dans le store."""
        self._completes.add(relation)

    def evalue(self, fait, relation=None):
        """VRAI si affirmé, FAUX si nié. Sinon : FAUX si la relation est déclarée complète (CWA), INCONNU sinon (OWA)."""
        if fait in self._pos:
            return VRAI
        if fait in self._neg:
            return FAUX
        if relation is not None and relation in self._completes:
            return FAUX                  # monde fermé : absence = faux (relation exhaustive)
        return INCONNU                   # monde ouvert : abstention honnête

    def connu(self, fait) -> bool:
        return fait in self._pos or fait in self._neg
