"""
TYPAGE DE SORTIE DES CANDIDATS (2026-06-22, levier « élégance : compteur d'appels plus bas, sound, sans perte »).

IDÉE (term-indexing / discrimination-tree adapté + BUSTLE property-signatures) : on connaît le TYPE de sortie ATTENDU
d'une tâche (bool/int/str/list/dict) par ses exemples ; un template qui renvoie un autre type ne peut JAMAIS la résoudre.
On RÉORDONNE donc (PAS d'élagage -> couverture STRICTEMENT préservée) les candidats d'un étage : type-correspondant
d'abord, inconnu ensuite, non-correspondant en dernier. Le vrai solveur (bon type) remonte -> jugé tôt -> compteur bas.

SÛRETÉ :
  - RÉORDONNANCEMENT seulement : rien n'est retiré. Si `type_sortie` se trompe et classe mal le winner, il finit dans
    le groupe « inconnu/non-correspondant » -> trouvé un peu plus tard, JAMAIS perdu. Zéro risque de couverture.
  - Pas de masquage : on ne réordonne qu'À L'INTÉRIEUR d'un étage -> l'étage gagnant est inchangé (épinglages intacts).
  - `type_sortie` est MÉMOÏSÉ par chaîne de code : il exécute le template sur des sondes canoniques UNE fois (amorti sur
    toutes les tâches), sous garde temps+mémoire (anti-boucle/anti-OOM). Erreur/ambiguïté -> None (= « inconnu » -> gardé).
"""

from __future__ import annotations

import functools
import re

from prefiltre import _limite_memoire, _limite_temps

# Sondes canoniques variées : couvrent les formes d'entrée usuelles (liste d'entiers, chaîne, matrice, scalaire, binaire).
_SONDES = [([1, 2, 3],), ([3, 1, 2],), ("abc",), ([[1, 2], [3, 4]],), (5,),
           ([1, 0, 1, 0, 1],), (12,), ("aabb",), ([5, 5, 1],), (121,), ([1, 8, 6, 2, 5],)]


def _classe(o) -> str | None:
    # bool AVANT int (bool est sous-type d'int en Python).
    if isinstance(o, bool):
        return "bool"
    if isinstance(o, int):
        return "int"
    if isinstance(o, str):
        return "str"
    if isinstance(o, list):
        return "list"
    if isinstance(o, dict):
        return "dict"
    return None


@functools.lru_cache(maxsize=20000)
def type_sortie(code: str) -> str | None:
    """Type de sortie d'un template, déduit en l'exécutant sur les sondes canoniques (1×, mémoïsé). None si l'exec
    échoue partout, si aucune sonde ne s'applique, ou si le type VARIE selon la sonde (ambigu) -> traité « inconnu »."""
    ns: dict = {}
    try:
        with _limite_temps(0.3), _limite_memoire():
            exec(code, ns)
    except Exception:
        return None
    m = re.search(r"def\s+(\w+)\s*\(", code)
    fn = ns.get(m.group(1)) if m else None
    if fn is None:
        return None
    seen: set[str] = set()
    for p in _SONDES:
        try:
            with _limite_temps(0.3), _limite_memoire():
                o = fn(*p)
        except Exception:
            continue
        t = _classe(o)
        if t:
            seen.add(t)
    return next(iter(seen)) if len(seen) == 1 else None   # type STABLE seulement -> sinon « inconnu » (sûr)


_MAP = {"list[list]": "list", "list[int]": "list", "list[str]": "list"}


def type_attendu(out_t: str) -> str | None:
    """Mappe le type de sortie LU dans les exemples (cle_tache[2]) vers une classe comparable à type_sortie()."""
    if not out_t or out_t == "?":
        return None
    return _MAP.get(out_t, out_t)


# Types RARES seulement : trier le type majoritaire `int` (a) n'aide presque pas (presque tous les templates renvoient
# int) et (b) SURFACE des solveurs int alternatifs/coïncidents dans les étages génériques -> masquage (single_number_ii
# basculait premier-unique -> tableaux, valide_vague28 cassé, 2026-06-22). On ne trie donc QUE bool/str/list/dict.
_TRIABLES = {"bool", "str", "list", "dict"}


def reordonne_par_type(cands: list[str], att: str | None) -> list[str]:
    """Tri STABLE : type-correspondant (0) -> inconnu (1) -> non-correspondant (2). Couverture préservée (rien retiré).
    `att` None ou `int` -> renvoie tel quel (pas de tri : voir _TRIABLES, anti-masquage)."""
    if att not in _TRIABLES or len(cands) < 2:
        return cands
    def rang(c: str) -> int:
        t = type_sortie(c)
        return 0 if t == att else 1 if t is None else 2
    return sorted(cands, key=rang)
