"""
BLACKBOARD / MÉMOIRE DE TRAVAIL PARTAGÉE — brique fondatrice Vague 7 (l'orchestration).

POURQUOI : ce qui transforme des dizaines de briques isolées en une CHAÎNE réelle. Chaque moteur (lecteur, loi,
simulation, limite…) POSTE ses résultats intermédiaires sur un espace commun, d'où les autres LISENT — ainsi le flux
« fait → loi → limite → écart → mécanisme → design → vérification → confiance » circule vraiment de bout en bout.

MODÈLE : un tableau d'entrées indexées par SUJET. Chaque entrée porte sa PROVENANCE (source) et une confiance
optionnelle. Append-only (traçable) ; plusieurs entrées par sujet possibles (l'arbitrage des contradictions est le rôle
d'arbitre.py, pas du blackboard).

FAUX=0 :
  • PROVENANCE OBLIGATOIRE : aucune entrée sans source (on sait toujours d'où vient un résultat).
  • `lis` renvoie les entrées réellement postées, ou [] — jamais une valeur inventée.
  • Append-only : on n'écrase pas silencieusement une entrée (les contradictions restent visibles pour l'arbitre).
Stdlib pur, déterministe, souverain.
"""
from __future__ import annotations


class Entree:
    __slots__ = ("sujet", "valeur", "source", "confiance", "seq")

    def __init__(self, sujet, valeur, source, confiance, seq):
        self.sujet = sujet
        self.valeur = valeur
        self.source = source
        self.confiance = confiance
        self.seq = seq

    def __repr__(self):
        c = f", conf={self.confiance}" if self.confiance is not None else ""
        return f"Entree({self.sujet!r}={self.valeur!r} <- {self.source!r}{c})"


class Blackboard:
    __slots__ = ("_entrees", "_seq")

    def __init__(self):
        self._entrees: dict = {}         # sujet -> list[Entree] (ordre de dépôt)
        self._seq = 0

    def poste(self, sujet, valeur, source: str, confiance: float = None):
        """Dépose un résultat sur le tableau. `source` (provenance) OBLIGATOIRE. Renvoie l'entrée créée."""
        if not source or not str(source).strip():
            raise ValueError("provenance (source) obligatoire pour poster sur le blackboard")
        self._seq += 1
        e = Entree(sujet, valeur, str(source), confiance, self._seq)
        self._entrees.setdefault(sujet, []).append(e)
        return e

    def lis(self, sujet) -> list:
        """Toutes les entrées d'un sujet, dans l'ordre de dépôt (ou [] si aucune)."""
        return list(self._entrees.get(sujet, ()))

    def dernier(self, sujet):
        """La dernière entrée postée sur un sujet, ou None."""
        lst = self._entrees.get(sujet)
        return lst[-1] if lst else None

    def valeurs(self, sujet) -> list:
        """Les valeurs DISTINCTES postées sur un sujet (pour repérer une contradiction)."""
        vus, out = set(), []
        for e in self._entrees.get(sujet, ()):
            cle = repr(e.valeur)
            if cle not in vus:
                vus.add(cle)
                out.append(e.valeur)
        return out

    def en_conflit(self, sujet) -> bool:
        """True ssi plusieurs valeurs distinctes ont été postées sur ce sujet (à arbitrer)."""
        return len(self.valeurs(sujet)) > 1

    def sujets(self) -> set:
        return set(self._entrees)

    # ── COUCHE ATOMES (Phase 2 axes ①+② : le substrat partagé parle le contrat d'atome) ──
    def poste_atome(self, sujet, atome, source: str):
        """Dépose un ATOME (contrat atome.py) : le statut épistémique voyage AVEC la valeur sur le tableau.
        Refuse tout non-Atome (une valeur nue passe par poste() — mais elle ne sera jamais relue comme fait).
        La confiance de l'entrée = celle de l'atome (une seule vérité, pas deux)."""
        import atome as A
        if not isinstance(atome, A.Atome):
            raise ValueError("poste_atome() exige un Atome (contrat atome.py) — pour une valeur nue, poste()")
        return self.poste(sujet, atome, source, confiance=atome.confiance)

    def atomes(self, sujet) -> list:
        """Les entrées d'un sujet dont la valeur est un Atome (dans l'ordre de dépôt)."""
        import atome as A
        return [e for e in self.lis(sujet) if isinstance(e.valeur, A.Atome)]

    def faits(self, sujet, contexte: dict = None) -> list:
        """SEULS les atomes du sujet SERVABLES COMME FAIT (invariants revalidés, statut fait/convention, portée
        couvrant `contexte` s'il est fourni). Une supposition / un réfuté / un atome muté n'en sort JAMAIS —
        la garde FAUX=0 de la RELECTURE : le tableau ne blanchit rien."""
        return [e for e in self.atomes(sujet) if e.valeur.est_servable_comme_fait(contexte)]

    def suppositions(self, sujet) -> list:
        """Les atomes SUPPOSITION du sujet (matière à travailler, jamais des faits)."""
        import atome as A
        return [e for e in self.atomes(sujet) if e.valeur.statut == A.SUPPOSITION]
