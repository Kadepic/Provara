"""
ORCHESTRATEUR MULTI-MODE D'INVENTION — le CAPSTONE de la couche COMMENT (2026-07-02).

POURQUOI : les 6 gestes divergents (apprend_loi / leve_contrainte-TRIZ / transfere_analogie / arbitre_compromis-Pareto
/ explique_observations-abduction / plan_procede) sont sound et câblés, mais ISOLÉS. Inventer pour de vrai, c'est les
ENCHAÎNER vers un but : abduction→plan (diagnostiquer puis réparer), apprend_loi→leve_contrainte (découvrir une loi
puis l'exploiter comme contrainte à lever), etc. Cet orchestrateur les fait DIALOGUER via un blackboard, en laissant
CHAQUE mode faire sa propre vérification.

FAUX=0 — LIGNE ROUGE (l'orchestrateur n'a AUCUNE logique de décision propre) :
  • Il n'appelle QUE des modes déjà sound (invention_divergente), qui abstiennent (None) sans preuve et re-vérifient
    leur sortie. Il ne poste sur le blackboard QUE les sorties NON-None.
  • Il ABSTIENT et s'arrête au 1er mode qui rend None (le plan ne « pousse » pas au-delà d'une étape non vérifiée).
  • Il ne SYNTHÉTISE / ne PLAUSIBILISE JAMAIS une conclusion combinée au-delà de ce que chaque mode a vérifié : il
    rapporte la TRACE des sorties de chaque mode, avec provenance. Aucune agrégation inventée.
Stdlib pur, déterministe, souverain. FAUX=0 entièrement DÉLÉGUÉ aux modes.
"""
from __future__ import annotations

import blackboard as _bb
import invention_divergente as _inv

MODES = {
    "apprend_loi": _inv.apprend_loi,
    "leve_contrainte": _inv.leve_contrainte,
    "transfere_analogie": _inv.transfere_analogie,
    "arbitre_compromis": _inv.arbitre_compromis,
    "explique_observations": _inv.explique_observations,
    "plan_procede": _inv.plan_procede,
}


class OrchestrateurInvention:
    """Enchaîne des gestes divergents sur un blackboard partagé. Chaque geste re-vérifie sa sortie ; l'orchestrateur
    abstient au 1er None et ne rapporte que des sorties vérifiées."""

    def __init__(self):
        self.bb = _bb.Blackboard()
        self._trace = []          # [(sujet, mode, produit:bool)]

    def applique(self, sujet: str, mode: str, **args):
        """Exécute un mode divergent ; poste son résultat (si non-None) sur le blackboard avec provenance, ou trace
        une abstention. Renvoie le résultat ou None. FAUX=0 : rien posté si le mode abstient."""
        if mode not in MODES:
            raise ValueError(f"mode d'invention inconnu : {mode!r} (connus : {sorted(MODES)})")
        res = MODES[mode](**args)
        produit = res is not None
        self._trace.append((sujet, mode, produit))
        if produit:
            self.bb.poste(sujet, res, source=f"mode:{mode}")
        return res

    def lis(self, sujet):
        """Dernière valeur postée pour `sujet`, ou None (jamais inventée)."""
        e = self.bb.dernier(sujet)
        return e.valeur if e else None

    def enchaine(self, plan) -> dict:
        """Exécute une SÉQUENCE `plan` = [(sujet, mode, args_fn)] où `args_fn(self) -> dict d'args` (peut LIRE le
        blackboard via self.lis pour consommer une étape précédente ; ou un dict d'args statique). ABSTIENT et
        s'arrête au 1er mode qui rend None. Renvoie {complet, abstenu_a, resultats, trace}."""
        resultats = {}
        for etape in plan:
            sujet, mode, args = etape
            a = args(self) if callable(args) else dict(args)
            res = self.applique(sujet, mode, **a)
            if res is None:
                return {"complet": False, "abstenu_a": sujet, "resultats": resultats, "trace": list(self._trace)}
            resultats[sujet] = res
        return {"complet": True, "abstenu_a": None, "resultats": resultats, "trace": list(self._trace)}

    def trace(self):
        """La séquence des gestes appliqués : [(sujet, mode, a_produit_un_résultat)]. Rejouable/auditable."""
        return list(self._trace)
