"""
TRACE DE RAISONNEMENT VÉRIFIABLE — brique Vague 7. Rendre toute conclusion traçable jusqu'aux prémisses et re-vérifiable.

POURQUOI : une invention est une longue chaîne d'inférences. Pour lui faire confiance, il faut pouvoir REMONTER chaque
conclusion à ses justifications et REJOUER les étapes. Une conclusion dont une étape n'est pas justifiée est suspecte.

MODÈLE : un DAG d'ÉTAPES. Chaque étape = (id, operation, entrées=[ids d'étapes/prémisses], sortie, justification,
verificateur optionnel fn()->bool). Les prémisses sont des étapes sans entrées, marquées comme telles.

FAUX=0 :
  • ACYCLIQUE : une étape ne peut dépendre (transitivement) d'elle-même — cycle refusé.
  • Toute étape non-prémisse DOIT avoir une justification non vide et des entrées existantes — sinon refus.
  • `verifie(id)` rejoue les vérificateurs de toute la sous-trace : True seulement si CHAQUE étape passe le sien
    (une étape sans vérificateur est neutre) — une étape qui échoue casse la conclusion (jamais masquée).
  • `remonte(id)` renvoie la vraie chaîne de dépendances (jamais une justification inventée).
Stdlib pur, déterministe, souverain.
"""
from __future__ import annotations


class Cycle(Exception):
    """Une étape dépendrait (transitivement) d'elle-même — trace incohérente (refus FAUX=0)."""


class Trace:
    __slots__ = ("_etapes",)

    def __init__(self):
        self._etapes: dict = {}          # id -> dict(operation, entrees, sortie, justification, verif, premisse)

    def premisse(self, id_, valeur, source: str):
        """Ajoute une prémisse (fait de base) avec sa source. Pas d'entrées, justification = la source."""
        if not source or not str(source).strip():
            raise ValueError("une prémisse exige une source")
        self._etapes[id_] = {"operation": "prémisse", "entrees": [], "sortie": valeur,
                             "justification": str(source), "verif": None, "premisse": True}
        return id_

    def etape(self, id_, operation, entrees, sortie, justification, verificateur=None):
        """Ajoute une étape dérivée. `entrees` = ids d'étapes existantes ; justification non vide obligatoire."""
        if not justification or not str(justification).strip():
            raise ValueError(f"étape {id_!r} : justification obligatoire")
        for e in entrees:
            if e not in self._etapes:
                raise ValueError(f"étape {id_!r} : entrée inconnue {e!r}")
        # acyclicité : id_ ne doit pas être atteignable depuis ses entrées
        if id_ in self._etapes:
            raise ValueError(f"étape {id_!r} déjà définie")
        self._etapes[id_] = {"operation": operation, "entrees": list(entrees), "sortie": sortie,
                             "justification": str(justification), "verif": verificateur, "premisse": False}
        # vérifie l'acyclicité après insertion (remonte lèvera si cycle — impossible ici car entrées préexistantes)
        self.remonte(id_)
        return id_

    def remonte(self, id_) -> list:
        """Sous-trace : tous les ids dont dépend `id_` (transitivement), y compris lui-même. Détecte les cycles."""
        vus, ordre = set(), []

        def dfs(n, pile):
            if n in pile:
                raise Cycle(f"cycle de justification en {n!r}")
            if n in vus:
                return
            vus.add(n)
            for e in self._etapes.get(n, {}).get("entrees", []):
                dfs(e, pile | {n})
            ordre.append(n)

        if id_ not in self._etapes:
            return []
        dfs(id_, set())
        return ordre

    def justification(self, id_):
        e = self._etapes.get(id_)
        return e["justification"] if e else None

    def verifie(self, id_) -> bool:
        """Rejoue les vérificateurs de toute la sous-trace de `id_`. True ssi AUCUN ne renvoie faux. Une étape sans
        vérificateur est neutre ; une étape dont le vérificateur échoue (ou lève) casse la conclusion."""
        for n in self.remonte(id_):
            v = self._etapes[n]["verif"]
            if v is None:
                continue
            try:
                if not bool(v()):
                    return False
            except Exception:
                return False
        return True

    def sortie(self, id_):
        e = self._etapes.get(id_)
        return e["sortie"] if e else None
