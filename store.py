"""
Brique 2 — LE STORE.

Le coffre des SUCCÈS VÉRIFIÉS. C'est lui qui transforme la boucle en
apprentissage : tout ce qui a RÉELLEMENT passé le juge (et rien d'autre) est
persisté ici, et constituera le jeu de ré-entraînement (fine-tuning) du modèle.

Principes (cf. PROJET-AUTO-AMELIORATION-CODE.md §3, §5) :
  - On ne garde QUE le vrai-vérifié. Le store REFUSE un verdict non passant —
    c'est le garde-fou anti-dérive : le jeu d'apprentissage ne peut pas se
    polluer de "convaincant mais faux".
  - Append-only (JSONL) : un succès acquis ne se réécrit pas ; l'historique est
    une vérité-terrain qu'on accumule (utile aussi pour le REJEU anti-oubli).
  - Dé-dupliqué : la même solution pour la même tâche n'est comptée qu'une fois,
    sinon la boucle gonflerait le jeu avec des copies et fausserait l'apprentissage.
  - Self-contained : chaque entrée garde l'énoncé ET la solution -> paire
    (prompt -> solution) directement exploitable pour le fine-tuning.

Le store ne sait RIEN du générateur ni du modèle. Il archive le réel-vérifié.
"""

from __future__ import annotations

import dataclasses
import hashlib
import json
import time
from pathlib import Path
from typing import Iterator

from juge import Verdict


def _empreinte(tache_id: str, solution: str) -> str:
    """
    Identité d'un succès = (tâche, solution normalisée). Deux solutions qui ne
    diffèrent que par des espaces de fin / lignes vides sont la MÊME idée : on
    normalise avant de hacher pour que la dé-duplication soit robuste.
    """
    lignes = [ligne.rstrip() for ligne in solution.strip().splitlines()]
    noyau = "\n".join(lignes)
    brut = f"{tache_id}\0{noyau}".encode("utf-8")
    return hashlib.sha256(brut).hexdigest()


@dataclasses.dataclass(frozen=True)
class Succes:
    """Une entrée du store : un succès vérifié, prêt pour le ré-entraînement."""
    empreinte: str       # sha256(tâche, solution normalisée) — clé de dé-dup
    tache_id: str        # quelle tâche a été résolue
    prompt: str          # l'énoncé (pour la paire prompt -> solution)
    solution: str        # le code qui a RÉELLEMENT passé le juge
    duree_s: float       # temps d'exécution mesuré par le juge (info de qualité)
    ts: float            # quand on l'a archivé (epoch)

    def to_json(self) -> str:
        return json.dumps(dataclasses.asdict(self), ensure_ascii=False)

    @classmethod
    def from_json(cls, ligne: str) -> "Succes":
        return cls(**json.loads(ligne))


class Store:
    """
    Coffre append-only des succès vérifiés, adossé à un fichier JSONL.

    Usage :
        store = Store("succes.jsonl")
        ajoute = store.ajoute(tache, solution, verdict)  # True si nouveau, False si doublon
    """

    def __init__(self, chemin: str | Path):
        self.chemin = Path(chemin)
        self._empreintes: set[str] = set()   # index en mémoire pour la dé-dup O(1)
        self._n = 0
        self._charge()

    def _charge(self) -> None:
        """Reconstruit l'index depuis le fichier existant (reprise à chaud)."""
        if not self.chemin.exists():
            return
        with self.chemin.open("r", encoding="utf-8") as f:
            for ligne in f:
                ligne = ligne.strip()
                if not ligne:
                    continue
                s = Succes.from_json(ligne)
                self._empreintes.add(s.empreinte)
                self._n += 1

    def ajoute(self, tache, solution: str, verdict: Verdict) -> bool:
        """
        Archive un succès. Renvoie True s'il a été ajouté, False si c'était un doublon.

        Lève ValueError si le verdict n'a pas passé : le store est le garde-fou
        anti-dérive — il ne contient QUE du vrai-vérifié.
        """
        if not verdict.passe:
            raise ValueError(
                f"Refus d'archiver un non-succès (statut={verdict.statut!r}). "
                f"Le store ne garde que ce qui a réellement passé le juge."
            )

        empreinte = _empreinte(tache.id, solution)
        if empreinte in self._empreintes:
            return False  # déjà connu : on ne gonfle pas le jeu de doublons

        succes = Succes(
            empreinte=empreinte,
            tache_id=tache.id,
            prompt=tache.prompt,
            solution=solution.strip(),
            duree_s=verdict.duree_s,
            ts=time.time(),
        )
        with self.chemin.open("a", encoding="utf-8") as f:
            f.write(succes.to_json() + "\n")
        self._empreintes.add(empreinte)
        self._n += 1
        return True

    def __len__(self) -> int:
        return self._n

    def __iter__(self) -> Iterator[Succes]:
        """Relit tous les succès depuis le disque (source de vérité = le fichier)."""
        if not self.chemin.exists():
            return
        with self.chemin.open("r", encoding="utf-8") as f:
            for ligne in f:
                ligne = ligne.strip()
                if ligne:
                    yield Succes.from_json(ligne)

    def par_tache(self) -> dict[str, int]:
        """Combien de solutions distinctes vérifiées par tâche (santé du jeu)."""
        compte: dict[str, int] = {}
        for s in self:
            compte[s.tache_id] = compte.get(s.tache_id, 0) + 1
        return compte
