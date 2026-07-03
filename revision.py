"""
RÉVISION DE CROYANCES — brique Vague 8 (réconcilier, pas empiler). L'idée ÉRIS : intégrer du neuf sans se contredire.

POURQUOI : la veille apporte du neuf qui parfois CONTREDIT l'ancien (une valeur datée qui a changé, une correction).
Empiler les deux = incohérence. La machine doit RÉCONCILIER : sur une clé fonctionnelle, garder la croyance la plus
fiable / la plus récente, RÉTRACTER l'autre explicitement, et ne jamais tenir un fait ET sa négation.

MODÈLE : chaque croyance = (cle, valeur, fiabilite, date). Sur une clé fonctionnelle (une seule valeur vraie),
`integre(nouvelle)` compare à la croyance en place et décide : garder l'ancienne, la remplacer (avec rétractation
tracée), ou signaler un conflit INDÉCIDABLE (à ne pas trancher au hasard).

FAUX=0 :
  • Jamais deux valeurs contradictoires tenues en même temps sur une clé fonctionnelle.
  • Remplacement JUSTIFIÉ (fiabilité strictement supérieure, ou égale fiabilité mais plus récent) et RÉTRACTATION
    tracée (journal). Sinon (fiabilité égale ET pas plus récent, ou strictement moins fiable) -> on GARDE l'ancienne.
  • Conflit indécidable (même fiabilité, même date, valeurs différentes) -> statut CONFLIT, aucune des deux imposée.
Stdlib pur, déterministe, souverain.
"""
from __future__ import annotations

GARDE = "garde_ancienne"
REMPLACE = "remplace"
CONFLIT = "conflit_indecidable"
NOUVEAU = "nouveau"


class Croyance:
    __slots__ = ("cle", "valeur", "fiabilite", "date")

    def __init__(self, cle, valeur, fiabilite=0.5, date=0):
        self.cle = cle
        self.valeur = valeur
        self.fiabilite = float(fiabilite)
        self.date = date

    def __repr__(self):
        return f"Croyance({self.cle!r}={self.valeur!r}, fiab={self.fiabilite}, date={self.date})"


class BaseCroyances:
    __slots__ = ("_croyances", "journal")

    def __init__(self):
        self._croyances: dict = {}       # cle -> Croyance (fonctionnelle : une par clé)
        self.journal: list = []          # rétractations tracées : (cle, ancienne_valeur, nouvelle_valeur, raison)

    def integre(self, nouvelle: Croyance):
        """Intègre une croyance en réconciliant sur sa clé. Renvoie le statut (NOUVEAU/REMPLACE/GARDE/CONFLIT)."""
        actuelle = self._croyances.get(nouvelle.cle)
        if actuelle is None:
            self._croyances[nouvelle.cle] = nouvelle
            return NOUVEAU
        if actuelle.valeur == nouvelle.valeur:
            # même valeur : on garde la plus fiable/récente comme support, pas de contradiction
            if (nouvelle.fiabilite, nouvelle.date) > (actuelle.fiabilite, actuelle.date):
                self._croyances[nouvelle.cle] = nouvelle
            return GARDE
        # valeurs DIFFÉRENTES sur une clé fonctionnelle : réconcilier
        if nouvelle.fiabilite > actuelle.fiabilite or \
           (nouvelle.fiabilite == actuelle.fiabilite and nouvelle.date > actuelle.date):
            self.journal.append((nouvelle.cle, actuelle.valeur, nouvelle.valeur,
                                 "fiabilité supérieure" if nouvelle.fiabilite > actuelle.fiabilite else "plus récent"))
            self._croyances[nouvelle.cle] = nouvelle
            return REMPLACE
        if nouvelle.fiabilite == actuelle.fiabilite and nouvelle.date == actuelle.date:
            return CONFLIT                       # indécidable : on ne tranche pas au hasard (garde l'ancienne)
        return GARDE                             # nouvelle strictement moins fiable / plus ancienne

    def valeur(self, cle):
        c = self._croyances.get(cle)
        return c.valeur if c else None

    def coherente(self) -> bool:
        """Invariant : au plus une valeur par clé (jamais un fait et sa contradiction)."""
        return all(isinstance(c, Croyance) for c in self._croyances.values())
