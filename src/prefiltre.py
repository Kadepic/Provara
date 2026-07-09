"""
PRÉ-FILTRE EN-PROCESS DES CANDIDATS (2026-06-19, levier « tomber au plus petit possible » — Yohan).

CONSTAT : le coût réel d'une résolution = les APPELS JUGE, et chaque appel juge SPAWNE UN SOUS-PROCESS sandbox
(~10-50 ms). Or 99 % des candidats échouent ; les sandboxer tous est un gâchis de temps réel énorme.

IDÉE (inspirée de la synthèse bottom-up à équivalence observationnelle + Probe) : évaluer le candidat EN-PROCESS sur
les exemples (quasi-gratuit, comme means-end `_empreinte`), et ne SANDBOXER que le(s) survivant(s). N sous-process -> ~1.

SÛRETÉ (« sûr avant rapide ») — invariants :
  - Le JUGE reste l'arbitre FINAL : tout candidat accepté est reconfirmé en sandbox. La sécurité de ce qu'on ACCEPTE
    est inchangée.
  - Le pré-filtre ne fait que RÉDUIRE l'ensemble sandboxé. Il ne REJETTE un candidat sans sandbox QUE s'il échoue
    proprement en-process (AssertionError = mauvais résultat) -> pour nos candidats PURS et DÉTERMINISTES, échec
    en-process == échec sandbox -> AUCUNE perte de couverture.
  - Tout DOUTE (exception non-assertion, timeout en-process, exec impossible) -> "incertain" -> on SANDBOXE (on ne
    rejette jamais sur un doute). Couverture strictement préservée.
  - Timeout en-process dur (SIGALRM) -> un candidat qui boucle ne bloque pas (il devient "incertain" -> sandbox, qui
    a ses propres limites kernel).
"""

from __future__ import annotations

import signal
from contextlib import contextmanager

try:
    import resource                     # POSIX seulement — le pré-filtre en-process exige les gardes kernel
except ImportError:                     # Windows (.exe) : vécu 2026-07-09, l'import en dur tuait demande/
    resource = None                     # strategies et toutes les routes au-dessus (invente_et_retiens…).

from juge import juge

# Sans les DEUX gardes kernel (setrlimit + SIGALRM — Windows n'a ni l'un ni l'autre), exécuter un candidat
# EN-PROCESS serait un risque réel (boucle infinie = thread gelé, allocation folle = process à terre).
# HONNÊTE ET SÛR : le pré-filtre se déclare indisponible et TOUT passe par la sandbox juge (sous-processus
# bornés par timeout) — même verdict final, juste sans l'optimisation.
GARDES_KERNEL = resource is not None and hasattr(signal, "SIGALRM")


class _Timeout(Exception):
    pass


def _handler(signum, frame):
    raise _Timeout()


_MARGE_MEM = 512 * 1024 ** 2   # +512 Mo = EXACTEMENT la borne sandbox juge (juge.py memoire_mo=512). SOUND : un candidat
                               # qui dépasse échoue AUSSI en sandbox -> aucun rejet de valide, MAIS le pic en-process est
                               # capé à VMS+512 Mo au lieu de VMS+1 Gio (2026-06-20 : à +1 Gio, un candidat fou sur
                               # daily_temperatures piquait à ~1,5 Go RSS et tombait au ras du plafond ulimit -v 1,5 Go,
                               # faisant flaker vague16/25. À +512 Mo le pic reste ~600 Mo. Cf. REPRISE mémoire-échelle).


def _vms_octets() -> int | None:
    """Taille mémoire VIRTUELLE courante du process (Linux/WSL, /proc/self/statm, en pages). None si indisponible."""
    try:
        with open("/proc/self/statm") as _f:
            return int(_f.read().split()[0]) * resource.getpagesize()
    except (OSError, ValueError, IndexError):
        return None


@contextmanager
def _limite_memoire():
    """Borne SOFT adaptative de l'adresse virtuelle autour de l'exec EN-PROCESS : un candidat qui MATÉRIALISE une
    structure géante (ex. permutations d'une grande liste, comprehension N^k) lève un MemoryError CATCHABLE (-> 'fail')
    au lieu d'un SIGKILL/OOM du process principal (mesuré : daily_temperatures tuait le moteur sans cette garde).
    SOUND : la sandbox juge est DÉJÀ bornée (RLIMIT_AS ~512 Mo) -> tout candidat dépassant ce plafond échoue AUSSI en
    sandbox ; comme la cible = VMS + 1 Gio >> 512 Mo, on ne rejette que ce qui aurait de toute façon échoué -> couverture
    préservée. Best-effort : si /proc ou setrlimit indisponibles, on n'altère rien."""
    cur = _vms_octets()
    if cur is None:
        yield
        return
    try:
        soft, hard = resource.getrlimit(resource.RLIMIT_AS)
    except (ValueError, OSError):
        yield
        return
    cible = cur + _MARGE_MEM
    if hard != resource.RLIM_INFINITY:
        cible = min(cible, hard)
    pose = (soft == resource.RLIM_INFINITY) or (cible < soft)
    try:
        if pose:
            resource.setrlimit(resource.RLIMIT_AS, (cible, hard))
        yield
    finally:
        if pose:
            try:
                resource.setrlimit(resource.RLIMIT_AS, (soft, hard))
            except (ValueError, OSError):
                pass


@contextmanager
def _limite_temps(secondes: float):
    """Timeout dur en-process (POSIX, thread principal). En cas de dépassement -> _Timeout -> 'incertain' -> sandbox."""
    ancien = signal.signal(signal.SIGALRM, _handler)
    signal.setitimer(signal.ITIMER_REAL, secondes)
    try:
        yield
    finally:
        signal.setitimer(signal.ITIMER_REAL, 0)
        signal.signal(signal.SIGALRM, ancien)


def pre_juge(code: str, tests: str, held: str | None = None, timeout: float = 0.5) -> str:
    """Évalue EN-PROCESS le candidat contre les tests (visible + held), sans sous-process. Renvoie :
      - "fail"      : un assert a échoué (mauvais résultat) -> rejet SÛR (déterministe == sandbox).
      - "pass"      : tous les asserts passent en-process -> candidat PROMETTEUR (à sandbox-confirmer).
      - "incertain" : exec/exception non-assertion/timeout -> on NE conclut pas -> sandbox décide.
    Mime la sémantique du juge (exec code puis exec tests qui appellent check(fn)), mais en-process."""
    if not GARDES_KERNEL:
        return "incertain"             # pas de filet kernel -> JAMAIS d'exec en-process ; la sandbox tranche
    ns: dict = {}
    try:
        with _limite_temps(timeout), _limite_memoire():
            exec(code, ns)
            exec(tests, ns)
            if held:
                exec(held, ns)
    except AssertionError:
        return "fail"                  # mauvais résultat : == FAIL sandbox
    except _Timeout:
        return "incertain"             # trop lent EN-PROCESS -> la sandbox (limites kernel propres) tranche
    except MemoryError:
        return "fail"                  # candidat qui matérialise trop : échoue AUSSI en sandbox 512 Mo -> rejet SÛR
    except Exception:
        # SAIN (mesuré : couverture préservée) : une exception DÉTERMINISTE (NameError/TypeError/IndexError/
        # SyntaxError/MemoryError…) sur le MÊME code+inputs se reproduit en sandbox (`python -I -S`, stdlib dispo,
        # aucun import injecté, l'in-process a STRICTEMENT PLUS) -> ERROR/KILLED == non-pass. Donc rejet SÛR sans
        # sous-process. (Seul le TIMEOUT reste "incertain" car les limites temps diffèrent.)
        return "fail"
    return "pass"


def faire_gagne_prefiltre(tache, limites, compteurs: dict | None = None, timeout: float = 0.5):
    """Fabrique un `gagne(code)` PRÉ-FILTRÉ : d'abord en-process (rejette les échecs propres sans sous-process), puis
    sandbox-confirme (visible+held) les prometteurs/incertains. `compteurs` (optionnel) accumule {'inproc','sandbox'}
    pour mesurer honnêtement. Sémantique de couverture IDENTIQUE à un gagne sandbox-only (le sandbox tranche pareil)."""
    c = compteurs if compteurs is not None else {}
    c.setdefault("inproc", 0)
    c.setdefault("sandbox", 0)

    def gagne(code: str) -> bool:
        c["inproc"] += 1
        verdict = pre_juge(code, tache.tests, tache.tests_held_out, timeout)
        if verdict == "fail":
            return False                                   # rejet sûr sans sous-process
        # "pass" ou "incertain" -> le JUGE tranche (arbitre final)
        c["sandbox"] += 1
        if not juge(code, tache.tests, limites).passe:
            return False
        if tache.tests_held_out and not juge(code, tache.tests_held_out, limites).passe:
            return False
        return True

    return gagne
