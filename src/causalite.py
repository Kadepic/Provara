"""
CAUSALITÉ — brique Vague 1 (graphe causal + intervention). Cœur du raisonnement d'invention.

POURQUOI : inventer = CHANGER un résultat. Pour le faire, il faut savoir quelle CAUSE agir sur laquelle — et
distinguer OBSERVER (corrélation, remonte aux ancêtres) d'INTERVENIR (do-opérateur : on force une variable, seuls
ses DESCENDANTS bougent, pas ses causes). Sans ça, une machine confond « le baromètre chute quand il pleut » et
« casser le baromètre fait pleuvoir ». C'est la distinction qui rend le design causalement correct.

MODÈLE : graphe causal orienté (DAG). Nœud = variable/événement. Arête cause→effet, portant un MÉCANISME optionnel
(un frame.Frame, ou tout objet) et un SIGNE optionnel (+/−). Hypothèse DAG (acyclique), comme les modèles causals
structurels standard ; la boucle de rétroaction (modèle dynamique) est une extension ultérieure, hors périmètre ici.

FAUX=0 (jamais une causalité inventée) :
  • ACYCLIQUE : une cause ne peut se causer elle-même (directement ou transitivement) — arête créant un cycle REFUSÉE.
  • do(x) (INTERVENTION) coupe les arêtes ENTRANTES de x : l'effet d'une intervention = x ∪ descendants(x), JAMAIS
    ses ancêtres. Observer x, lui, informe sur les ancêtres — les deux ne sont pas confondus.
  • `descendants`/`ancetres`/`chaines` ne renvoient que des relations RÉELLEMENT posées ; aucun lien deviné.
Stdlib pur, déterministe, souverain.
"""
from __future__ import annotations


class CycleCausal(Exception):
    """Une arête cause→effet fermerait une boucle causale (A cause … cause A) — refus FAUX=0 (DAG)."""


class GrapheCausal:
    __slots__ = ("_effets", "_causes", "_meca")

    def __init__(self):
        self._effets: dict = {}          # cause -> set(effets directs)
        self._causes: dict = {}          # effet -> set(causes directes)
        self._meca: dict = {}            # (cause, effet) -> (mecanisme, signe)

    def ajoute_cause(self, cause, effet, mecanisme=None, signe=None):
        """Pose « cause → effet ». Refuse l'auto-causalité et tout cycle."""
        if cause == effet:
            raise CycleCausal(f"irréflexif : {cause!r} ne peut se causer lui-même")
        # une arête cause→effet crée un cycle si `cause` est déjà un descendant de `effet`.
        if cause in self.descendants(effet):
            raise CycleCausal(f"cycle refusé : {cause!r} est déjà (transitivement) un effet de {effet!r}")
        self._effets.setdefault(cause, set()).add(effet)
        self._causes.setdefault(effet, set()).add(cause)
        self._meca[(cause, effet)] = (mecanisme, signe)

    def effets_directs(self, x) -> set:
        return set(self._effets.get(x, ()))

    def causes_directes(self, x) -> set:
        return set(self._causes.get(x, ()))

    def descendants(self, x) -> set:
        """Tout ce que x cause, directement ou transitivement (conséquences causales). Terminant (DAG)."""
        vus, pile = set(), list(self._effets.get(x, ()))
        while pile:
            n = pile.pop()
            if n in vus:
                continue
            vus.add(n)
            pile.extend(self._effets.get(n, ()))
        return vus

    def ancetres(self, x) -> set:
        """Toutes les causes (directes/indirectes) de x."""
        vus, pile = set(), list(self._causes.get(x, ()))
        while pile:
            n = pile.pop()
            if n in vus:
                continue
            vus.add(n)
            pile.extend(self._causes.get(n, ()))
        return vus

    def intervenir(self, x) -> set:
        """do(x) : effet d'une INTERVENTION forçant x. Renvoie {x} ∪ descendants(x) — ce qui peut changer.
        Les ancêtres de x NE sont PAS affectés (l'intervention coupe les causes entrantes de x). C'est la
        différence entre agir et observer."""
        return {x} | self.descendants(x)

    def observer_informe(self, x) -> set:
        """Ce qu'OBSERVER x renseigne (dépendance statistique) : ancêtres ∪ descendants ∪ {x}. À NE PAS confondre
        avec intervenir(x) : observer un effet informe sur ses causes, mais agir dessus ne les change pas."""
        return {x} | self.ancetres(x) | self.descendants(x)

    def cause_de(self, cause, effet) -> bool:
        """True ssi `cause` est (transitivement) une cause de `effet` — uniquement via des arêtes réelles."""
        return effet in self.descendants(cause)

    def chaines(self, cause, effet) -> list:
        """Toutes les chaînes causales (chemins) de `cause` à `effet`. [] s'il n'y a pas de lien réel."""
        chemins = []

        def dfs(courant, chemin):
            if courant == effet:
                chemins.append(list(chemin))
                return
            for suiv in sorted(self._effets.get(courant, ()), key=repr):
                if suiv not in chemin:                # DAG -> pas de re-visite
                    dfs(suiv, chemin + [suiv])

        if cause == effet:
            return []
        dfs(cause, [cause])
        return chemins

    def mecanisme(self, cause, effet):
        """(mecanisme, signe) de l'arête directe cause→effet, ou None si pas d'arête directe."""
        return self._meca.get((cause, effet))

    def leviers(self, cible) -> set:
        """Les variables sur lesquelles INTERVENIR peut changer `cible` = ses ancêtres (les causes actionnables).
        C'est la question d'invention : « sur quoi agir pour modifier ce résultat ? »"""
        return {a for a in self.ancetres(cible)}
