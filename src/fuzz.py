"""
Brique 6 — LE CRIBLE SÉCURITÉ (fuzzing différentiel).

Le juge v1 demande : « ça passe les tests ? ». Le crible demande la question
VERAX : « ça SURVIT au réel ? ». Un code peut passer tous les tests visibles
et held-out, et pourtant CRASHER ou se TROMPER sur des entrées non vues. Le
crible le débusque (cf. PROJET-AUTO-AMELIORATION-CODE.md §4 juge v2, §6).

Méthode : FUZZING DIFFÉRENTIEL contre la solution de référence.
  - On génère des centaines d'entrées aléatoires (dont des cas aberrants : liste
    vide, singleton, valeurs proches non adjacentes, seuils nuls...).
  - Pour chaque entrée, on compare le candidat à solution_ref (l'oracle) :
      * le candidat LÈVE une exception là où la référence non -> CRASH (fragile) ;
      * le candidat REND un résultat ≠ de la référence            -> DIVERGENCE (faux) ;
      * sinon                                                      -> robuste.

Élégance : un fuzz n'est qu'un AUTRE jeu de « tests ». On RÉUTILISE donc le juge
(B1) tel quel — sandbox isolée, limites, sentinelle comprises. Le crible ne fait
que FABRIQUER le programme de fuzz, le juge l'exécute.
"""

from __future__ import annotations

import dataclasses

from juge import ERROR, FAIL, PASS, TIMEOUT, Limites, juge


# Sous-types de faille de robustesse (pour le routage/diagnostic).
ROBUSTE = "robuste"          # survit à toutes les entrées fuzz
CRASH = "crash"              # lève une exception là où la référence tient
DIVERGENCE = "divergence"    # résultat différent de la référence (faux sur du non-vu)
LENT = "lent"                # dépasse le budget de temps sur une entrée
INCRIBLABLE = "incriblable"  # tâche sans oracle/générateur -> on ne peut pas cribler


@dataclasses.dataclass(frozen=True)
class RapportFuzz:
    """Le verdict de robustesse d'un candidat."""
    robuste: bool
    type_faille: str         # ROBUSTE / CRASH / DIVERGENCE / LENT / INCRIBLABLE
    n_essais: int            # combien d'entrées tentées
    detail: str              # le contre-exemple / la trace (le COMMENT, pour comprendre)

    def __str__(self) -> str:
        return f"<Fuzz {self.type_faille} sur {self.n_essais} essais>"


def _programme_fuzz(tache, n_essais: int, seed: int) -> str:
    """
    Fabrique le jeu de « tests » de fuzzing, à passer au juge comme des tests.

    - La référence est exécutée dans un namespace isolé (évite le conflit de nom
      avec la fonction du candidat, définie au niveau module).
    - Une entrée pour laquelle la RÉFÉRENCE elle-même échoue est hors domaine :
      on l'ignore (on ne reproche pas au candidat un cas non spécifié).
    """
    fn = tache.point_entree
    return f'''
import random as _random
_ref_ns = {{}}
exec({tache.solution_ref!r}, _ref_ns)
_ref = _ref_ns[{fn!r}]

{tache.gen_entrees}

_rng = _random.Random({seed})
for _i in range({n_essais}):
    _inp = _gen(_rng)
    try:
        _attendu = _ref(*_inp)
    except Exception:
        continue  # entrée hors domaine pour la référence -> ignorée
    _obtenu = globals()[{fn!r}](*_inp)   # candidat : peut lever -> CRASH (juge ERROR)
    assert _obtenu == _attendu, "DIVERGENCE essai %d sur %r : obtenu=%r attendu=%r" % (
        _i, _inp, _obtenu, _attendu)
'''


def crible(tache, solution: str, n_essais: int = 200, seed: int = 0,
           limites: Limites | None = None) -> RapportFuzz:
    """
    Soumet une solution au fuzzing différentiel. Renvoie un RapportFuzz.

    Pré-requis : la tâche fournit solution_ref (oracle) ET gen_entrees (générateur).
    Sinon -> INCRIBLABLE (on ne prétend pas avoir criblé ce qu'on ne peut pas).
    """
    if not tache.solution_ref or not tache.gen_entrees or not tache.point_entree:
        return RapportFuzz(robuste=False, type_faille=INCRIBLABLE, n_essais=0,
                           detail="tâche sans oracle/générateur/point d'entrée : non criblable")

    programme = _programme_fuzz(tache, n_essais, seed)
    verdict = juge(solution, programme, limites)

    if verdict.statut == PASS:
        return RapportFuzz(True, ROBUSTE, n_essais, "")
    if verdict.statut == FAIL:
        # AssertionError = nos asserts de comparaison -> divergence avec l'oracle.
        return RapportFuzz(False, DIVERGENCE, n_essais, _trace(verdict.stderr))
    if verdict.statut == ERROR:
        # Exception du candidat sur une entrée que la référence encaisse -> crash.
        return RapportFuzz(False, CRASH, n_essais, _trace(verdict.stderr))
    if verdict.statut == TIMEOUT:
        return RapportFuzz(False, LENT, n_essais, "dépasse le budget de temps sous fuzz")
    # killed / sabotage : comportement anormal sous fuzz -> non robuste.
    return RapportFuzz(False, verdict.statut, n_essais, _trace(verdict.stderr))


def _trace(stderr: str, n: int = 400) -> str:
    """Garde la fin de la trace : c'est là qu'on lit le contre-exemple."""
    stderr = (stderr or "").strip()
    return stderr[-n:]
