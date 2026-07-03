"""
MOTEUR DE RAISONNEMENT — CÂBLAGE end-to-end des briques (2026-07-02). Le dernier morceau de COMMENT : faire
DIALOGUER les briques génériques sur un problème réel, au lieu de 31 modules isolés.

Il orchestre la chaîne `fait → loi → limite → écart → vérification → arbitrage → confiance` via le BLACKBOARD (mémoire
de travail partagée), en traçant chaque étape (TRACE vérifiable), en arbitrant les contradictions (ARBITRE) et en
tranchant l'affirmation par la POLITIQUE D'ABSTENTION unifiée. Briques câblées : blackboard, trace, arbitre, abstention,
loi, limite, grandeur, dimensions.

FAUX=0 (l'orchestrateur n'introduit AUCUN faux) :
  • Ne pose sur le tableau que des résultats RÉELS (loi.resout / limite.evalue renvoient une Grandeur/dict ou None).
  • Une étape qui échoue (None) est tracée telle quelle et fait pencher le verdict vers ABSTENTION — jamais d'invention.
  • Contradiction non résolue par l'arbitre → verdict HORS. Réel violant une borne physique → HORS.
  • Le verdict final passe par abstention.decide (défaut = ABSTENTION) ; toute la chaîne est re-vérifiable via la trace.
Stdlib pur, souverain.
"""
from __future__ import annotations

from blackboard import Blackboard
from trace import Trace
from arbitre import arbitre, TRANCHE, CONSENSUS
from abstention import decide, VERIFIE, ABSTENTION, HORS
from grandeur import Grandeur


class MoteurRaisonnement:
    def __init__(self):
        self.bb = Blackboard()
        self.tr = Trace()
        self._impossible = False        # une borne physique a-t-elle été violée ?
        self._confiances = []

    # — 1. OBSERVER : entrée d'un fait/mesure (blackboard + prémisse tracée) —
    def observe(self, sujet, valeur, source, confiance=None):
        self.bb.poste(sujet, valeur, source, confiance)
        if sujet not in self.tr._etapes:
            self.tr.premisse(sujet, valeur, source)
        if confiance is not None:
            self._confiances.append(confiance)
        return valeur

    def _val(self, sujet):
        e = self.bb.dernier(sujet)
        return e.valeur if e else None

    # — 2. DÉRIVER une grandeur via une loi (à partir de sujets du tableau) —
    def derive(self, cible_sujet, loi, cible_var, mapping):
        """mapping = {var_de_la_loi: sujet_du_blackboard}. Résout la loi ; pose le résultat (ou rien si None)."""
        connues = {}
        for var, suj in mapping.items():
            g = self._val(suj)
            if not isinstance(g, Grandeur):
                return None                      # entrée absente/non typée -> pas de dérivation (FAUX=0)
            connues[var] = g
        res = loi.resout(cible_var, **connues)
        if res is None:
            return None
        self.bb.poste(cible_sujet, res, source=f"loi:{loi.nom}")
        entrees = [s for s in mapping.values() if s in self.tr._etapes]
        self.tr.etape(cible_sujet, f"loi:{loi.nom}", entrees, res, f"résolu par {loi.nom}")
        return res

    # — 3. ÉCART au théorique + faisabilité (brique limite) —
    def marge(self, sujet_resultat, limite, reel_sujet, params_mapping, borne_sujet=None):
        """Compare le réel (reel_sujet) à la borne calculée par `limite`. Pose {borne, marge, respecte} ; marque
        impossible si le réel viole la borne physique. Si `borne_sujet` (borne déjà dérivée) est fourni, l'étape en
        DÉPEND dans la trace -> chaîne pleinement reliée fait → borne → écart."""
        reel = self._val(reel_sujet)
        params = {}
        for var, suj in params_mapping.items():
            g = self._val(suj)
            if not isinstance(g, Grandeur):
                return None
            params[var] = g
        r = limite.evalue(reel, **params)
        if r is None:
            return None
        if r["impossible"]:
            self._impossible = True
        self.bb.poste(sujet_resultat, r, source=f"limite:{limite.nom}")
        deps = [reel_sujet] + list(params_mapping.values()) + ([borne_sujet] if borne_sujet else [])
        entrees = [s for s in deps if s in self.tr._etapes]
        self.tr.etape(sujet_resultat, f"limite:{limite.nom}", entrees, r,
                      f"écart au théorique via {limite.nom}",
                      verificateur=lambda rr=r: (not rr["impossible"]))
        return r

    # — 4. ARBITRER les valeurs contradictoires d'un sujet —
    def resout_conflit(self, sujet, fiabilites):
        """Si plusieurs sources ont posté des valeurs différentes, arbitre. Renvoie (statut, valeur). Contradiction
        non résolue -> None (le verdict abstiendra/HORS)."""
        propositions = [(e.valeur, e.source) for e in self.bb.lis(sujet)]
        statut, valeur, detail = arbitre(propositions, fiabilites)
        if statut in (CONSENSUS, TRANCHE):
            self.bb.poste(sujet, valeur, source=f"arbitre:{statut}")
            return statut, valeur
        return statut, None                      # ABSTENTION : conflit non tranché

    # — 5. VERDICT final unifié —
    def verdict(self, sujet, seuil=0.5, contradiction_non_resolue=False):
        """Décide VERIFIE / ABSTENTION / HORS pour un sujet, via la politique unifiée. Prend en compte l'évidence
        (le sujet est-il sur le tableau ?), l'impossibilité physique cumulée, et les contradictions."""
        preuve = self.bb.dernier(sujet) is not None
        conf = min(self._confiances) if self._confiances else None
        return decide(preuve=preuve, confiance=conf, seuil=seuil,
                      contradiction=contradiction_non_resolue, impossible=self._impossible)

    def trace_verifie(self, sujet) -> bool:
        """La sous-trace menant à `sujet` est-elle vérifiable (aucune étape ne casse) ?"""
        return self.tr.verifie(sujet) if sujet in self.tr._etapes else False
