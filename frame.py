"""
FRAME N-AIRE RÉIFIÉ — brique Vague 1 (relation à rôles). Socle des MÉCANISMES, PROCESSUS et de la CAUSALITÉ.

POURQUOI : la mémoire actuelle est en triplets binaires (relation, x, y). Impossible d'y représenter proprement un
mécanisme (« la combustion de X, en présence de Y, à température Z, produit W ») ni une relation causale (agent,
patient, conditions, instant). On RÉIFIE : une relation n-aire devient un objet `Frame(type, {rôle: filler, …})`.
C'est le prérequis de tout raisonnement sur « comment ça marche » — donc de l'invention (repenser un système = ré-
assembler des mécanismes). Les fillers peuvent être des entités, des valeurs, des Grandeur, ou d'AUTRES frames (nesting).

FAUX=0 :
  • Un type de frame peut déclarer un SCHÉMA (rôles requis / optionnels). Un rôle INCONNU pour un type schématisé est
    REJETÉ (on n'accepte pas de rôle fantaisiste) ; un requis MANQUANT rend le frame invalide (détecté par `valide`).
  • Interroger un rôle absent -> None (jamais un filler inventé).
  • Sans schéma déclaré, le frame est libre (open-vocab) mais reste inspectable ; aucune invention de rôle.
Stdlib pur, immuable, déterministe, souverain.
"""
from __future__ import annotations

from types import MappingProxyType

# Schémas de frame : type -> {"requis": (rôles…), "optionnels": (rôles…)}. Curé, extensible.
# Ces trois-là couvrent le mécanisme générique ; d'autres types s'ajoutent librement (register_schema).
SCHEMAS: dict[str, dict] = {
    # relation causale générique : quelle cause produit quel effet, par quel mécanisme, sous quelles conditions.
    "cause": {"requis": ("cause", "effet"), "optionnels": ("mecanisme", "conditions", "instant", "force")},
    # transition d'état d'un système (processus) : de quel état vers quel état, sous quelle action/condition.
    "transition": {"requis": ("systeme", "de", "vers"), "optionnels": ("action", "conditions", "duree")},
    # transfert d'une grandeur d'une source vers une cible (chaleur, charge, matière…).
    "transfert": {"requis": ("quoi", "source", "cible"), "optionnels": ("quantite", "mecanisme", "conditions")},
    # ÉVÉNEMENT neo-davidsonien (« qui fait quoi à qui, avec quoi, quand, où ») : le patron canonique des
    # occurrences. `predicat` = le verbe/type d'action ; agent/patient = participants ; le reste optionnel.
    "evenement": {"requis": ("predicat", "agent"),
                  "optionnels": ("patient", "instrument", "beneficiaire", "temps", "lieu", "maniere", "resultat")},
}


def register_schema(type_frame: str, requis=(), optionnels=()):
    """Déclare/écrase le schéma d'un type de frame. requis+optionnels = ensemble des rôles admis."""
    SCHEMAS[type_frame] = {"requis": tuple(requis), "optionnels": tuple(optionnels)}


class RoleInconnu(Exception):
    """Un rôle non prévu par le schéma d'un type de frame a été fourni — rejet FAUX=0."""


class Frame:
    """Instance de relation n-aire : un `type` + une application rôle -> filler. Immuable."""

    __slots__ = ("type", "_roles")

    def __init__(self, type_frame: str, roles: dict):
        if not type_frame or not str(type_frame).strip():
            raise ValueError("type de frame obligatoire")
        schema = SCHEMAS.get(type_frame)
        if schema is not None:
            admis = set(schema["requis"]) | set(schema["optionnels"])
            inconnus = set(roles) - admis
            if inconnus:
                raise RoleInconnu(f"rôle(s) hors schéma de {type_frame!r} : {sorted(inconnus)} (admis : {sorted(admis)})")
        self.type = type_frame
        self._roles = MappingProxyType(dict(roles))     # lecture seule

    def role(self, nom):
        """Filler d'un rôle, ou None si absent (jamais inventé)."""
        return self._roles.get(nom)

    def roles(self):
        return dict(self._roles)

    def valide(self) -> bool:
        """True ssi tous les rôles REQUIS du schéma sont présents et non vides. Sans schéma -> True (open-vocab)."""
        schema = SCHEMAS.get(self.type)
        if schema is None:
            return True
        for r in schema["requis"]:
            if self._roles.get(r) in (None, "", ()):
                return False
        return True

    def roles_manquants(self) -> list:
        """Rôles requis non remplis (vide si valide ou sans schéma)."""
        schema = SCHEMAS.get(self.type)
        if schema is None:
            return []
        return [r for r in schema["requis"] if self._roles.get(r) in (None, "", ())]

    # — pont avec les faits binaires plats (entité, valeur) —
    @staticmethod
    def depuis_binaire(relation: str, entite, valeur) -> "Frame":
        """Réifie un triplet plat (relation, entité, valeur) en frame à 2 rôles sujet/objet — sans schéma."""
        return Frame(relation, {"sujet": entite, "objet": valeur})

    def vers_binaires(self) -> list:
        """Décompose le frame en triplets (type, rôle, filler) — pour indexation/stockage plat d'UN SEUL frame.
        ⚠ NE PAS utiliser pour aplatir PLUSIEURS frames dans un même bac plat : la sortie ne porte pas d'id
        d'instance, donc deux frames de même type y fusionneraient leurs rôles à la relecture (fait n-aire FAUX).
        Pour un stockage/relecture multi-frames SÛR, utiliser `vers_triplets(id)` + `depuis_triplets` (réification)."""
        return [(self.type, r, v) for r, v in self._roles.items()]

    # — réification SÛRE (round-trip multi-frames fidèle, FAUX=0) —
    # Pattern standard (blank-node / réification RDF) : chaque frame = un NŒUD portant un id d'instance unique ;
    # on émet (id, "__type__", type) + un (id, rôle, filler) par rôle. Deux frames d'id distincts ne peuvent JAMAIS
    # fusionner leurs rôles à la relecture (le regroupement se fait par id, pas par type) -> pas de fait n-aire faux.
    TYPE_ROLE = "__type__"          # rôle réservé portant le type du frame dans la forme aplatie

    def vers_triplets(self, id_instance) -> list:
        """Aplatit le frame en triplets réifiés (id_instance, rôle, filler), le type porté par le rôle `__type__`.
        `id_instance` DOIT être unique par instance (fourni par l'appelant qui en garantit l'unicité). FAUX=0 :
        c'est la seule voie sûre pour stocker N frames dans un bac plat commun sans confondre leurs rôles."""
        if id_instance is None or str(id_instance).strip() == "":
            raise ValueError("id_instance obligatoire pour la réification (unicité par instance = garde FAUX=0)")
        if self.TYPE_ROLE in self._roles:
            raise RoleInconnu(f"rôle réservé {self.TYPE_ROLE!r} interdit comme rôle métier")
        out = [(id_instance, self.TYPE_ROLE, self.type)]
        out.extend((id_instance, r, v) for r, v in self._roles.items())
        return out

    @staticmethod
    def depuis_triplets(triplets) -> dict:
        """Reconstruit fidèlement {id_instance: Frame} depuis des triplets réifiés (id, rôle, filler) — l'inverse
        exact de `vers_triplets`. Regroupe par id (jamais par type) : deux instances distinctes restent séparées.
        FAUX=0 : un groupe SANS rôle `__type__` est ignoré (on ne fabrique pas un frame sans type) ; deux triplets
        (même id, même rôle, valeurs différentes) -> ValueError (conflit, jamais un choix silencieux)."""
        par_id: dict = {}
        for id_instance, role, filler in triplets:
            d = par_id.setdefault(id_instance, {})
            if role in d and d[role] != filler:
                raise ValueError(f"conflit de rôle {role!r} pour l'instance {id_instance!r} : "
                                 f"{d[role]!r} vs {filler!r} (relecture ambiguë refusée)")
            d[role] = filler
        frames = {}
        for id_instance, d in par_id.items():
            type_frame = d.pop(Frame.TYPE_ROLE, None)
            if type_frame is None:                       # groupe sans type -> on n'invente pas de frame (HORS)
                continue
            frames[id_instance] = Frame(type_frame, d)
        return frames

    def __eq__(self, autre):
        return isinstance(autre, Frame) and self.type == autre.type and dict(self._roles) == dict(autre._roles)

    def __hash__(self):
        return hash((self.type, tuple(sorted((k, repr(v)) for k, v in self._roles.items()))))

    def __repr__(self):
        corps = ", ".join(f"{k}={v!r}" for k, v in self._roles.items())
        return f"Frame:{self.type}({corps})"
