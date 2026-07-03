"""
RAISONNEMENT QUALITATIF — brique Vague 4 (algèbre des signes + influences monotones).

POURQUOI : souvent on n'a pas les valeurs mais on connaît les SENS (« si la pression monte, le volume baisse »).
Raisonner sur les signes (+, −, 0) et les monotonies (Q+ : croît avec ; Q− : décroît avec) permet de propager un
« qu'arrive-t-il si j'augmente X ? » à travers un réseau d'influences — utile pour explorer un design sans chiffres.

FAUX=0 (l'ambiguïté est HONNÊTE, jamais tranchée au hasard) :
  • Somme de signes opposés (+ et −) -> `?` (indéterminé), pas un signe deviné.
  • Une influence n'existe que si elle est POSÉE ; propagation uniquement le long d'influences réelles.
  • Sur un chemin, une influence `?` contamine en `?` ; deux chemins de signes opposés -> `?`.
Signes : "+", "-", "0", "?". Stdlib pur, déterministe, souverain.
"""
from __future__ import annotations

PLUS, MOINS, ZERO, IND = "+", "-", "0", "?"


def signe_produit(a, b):
    """Produit qualitatif de deux signes (règle des signes ; ? est absorbant sauf par 0)."""
    if a == ZERO or b == ZERO:
        return ZERO
    if a == IND or b == IND:
        return IND
    return PLUS if a == b else MOINS


def signe_somme(a, b):
    """Somme qualitative : 0 neutre ; mêmes signes -> ce signe ; signes opposés -> ? (indéterminé, honnête)."""
    if a == ZERO:
        return b
    if b == ZERO:
        return a
    if a == IND or b == IND:
        return IND
    return a if a == b else IND          # + et - -> ? (on ne devine pas l'ampleur)


class ReseauInfluences:
    """Graphe d'influences monotones : arête x --(signe)--> y signifie « y varie dans ce sens quand x augmente »."""

    __slots__ = ("_infl",)

    def __init__(self):
        self._infl: dict = {}            # x -> list[(y, signe)]

    def influence(self, x, y, signe):
        if signe not in (PLUS, MOINS, IND):
            raise ValueError("signe d'influence : '+', '-' ou '?'")
        self._infl.setdefault(x, []).append((y, signe))
        return self

    def effet(self, source, variation=PLUS, cible=None):
        """Effet qualitatif d'une variation de `source` sur toutes les variables (ou sur `cible`). Combine les
        chemins : produit des signes le long d'un chemin, somme qualitative entre chemins. Cycle -> chemin coupé.
        Renvoie {variable: signe} (ou le signe de `cible`). L'indéterminé `?` est propagé honnêtement."""
        effets = {}

        def dfs(noeud, signe_courant, vus):
            for (y, s) in self._infl.get(noeud, []):
                if y in vus:
                    continue                      # coupe les cycles (terminaison)
                contrib = signe_produit(signe_courant, s)
                effets[y] = signe_somme(effets.get(y, ZERO), contrib)
                dfs(y, contrib, vus | {y})

        dfs(source, variation, {source})
        if cible is not None:
            return effets.get(cible, ZERO)
        return effets
