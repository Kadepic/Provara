"""
JUGE RAPIDE (fork-par-candidat) — chemin PYTHON uniquement, OPT-IN, verdict BIT-IDENTIQUE au juge subprocess.

Technique adaptée du FORKSERVER (fuzzing AFL) : au lieu d'`exec` un interpréteur Python NEUF par candidat
(~8 ms de démarrage, mesuré dans executeur.py), on `os.fork()` le process COURANT — déjà chaud — pour CHAQUE
candidat. Le fork est en copy-on-write (~1 ms). On supprime ainsi le démarrage de l'interpréteur, qui domine
le coût du jugement (donc de toute la boucle : recherche, invention, runtime -> vitesse ET puissance).

ISOLATION PRÉSERVÉE (le juge reste incorruptible) : chaque candidat tourne dans son PROPRE process enfant avec
les MÊMES garde-fous que le juge subprocess — rlimits (CPU/mémoire/core/fichier), timeout mur, sentinelle
anti-sabotage. Le parent (forkserver) n'exécute JAMAIS le code candidat : il fork, lit, classe, attend.

ÉQUIVALENCE : le verdict (statut + passe) est conçu identique au juge subprocess et PROUVÉ par
`valide_juge_rapide.py` sur batterie adverse (pass/fail/timeout/crash/oom/sabotage/isolation). Tant que
l'équivalence n'est pas prouvée, ce module reste OPT-IN (le juge subprocess demeure le défaut).

Langage != python -> on délègue au juge subprocess classique (polyglotte intact).
"""
from __future__ import annotations

import os
import secrets
import select
import signal
import sys
import textwrap
import time

try:
    import resource
except ImportError:  # pragma: no cover (POSIX-only)
    resource = None

from juge import ERROR, FAIL, KILLED, PASS, SABOTAGE, TIMEOUT, Limites, Verdict, _classe

_MAX_SORTIE = 1 << 20  # 1 Mo de stdout/stderr capturés max (anti-bombe sortie ; au-delà on tronque)


def _enfant(programme: str, limites: Limites, w_out: int, w_err: int) -> None:
    """Exécuté dans le PROCESS ENFANT. Ne revient JAMAIS (os._exit). Reproduit EXACTEMENT le contrat du juge
    subprocess : applique les rlimits, exécute solution+tests+sentinelle, code de sortie = sort du process."""
    code_sortie = 0
    try:
        os.dup2(w_out, 1)               # stdout -> pipe
        os.dup2(w_err, 2)               # stderr -> pipe
        if resource is not None:
            # MÊMES limites que juge._applique_limites (incorruptibilité côté ressources).
            resource.setrlimit(resource.RLIMIT_CPU, (limites.cpu_s, limites.cpu_s + 1))
            octets = limites.memoire_mo * 1024 * 1024
            resource.setrlimit(resource.RLIMIT_AS, (octets, octets))
            resource.setrlimit(resource.RLIMIT_CORE, (0, 0))
            cap = limites.fichier_mo * 1024 * 1024
            resource.setrlimit(resource.RLIMIT_FSIZE, (cap, cap))
        ns = {"__name__": "__main__"}
        exec(compile(programme, "<candidat>", "exec"), ns)
    except SystemExit as e:               # sys.exit / quit() : le process « se termine proprement »
        c = e.code
        code_sortie = 0 if (c is None or c == 0) else (c if isinstance(c, int) else 1)
    except BaseException:                  # toute exception (AssertionError, MemoryError, crash…) -> trace en stderr
        try:
            import traceback
            traceback.print_exc()          # le NOM de l'exception part en stderr -> classe_echec le lit (FAIL/KILLED/ERROR)
        except BaseException:
            pass
        code_sortie = 1
    finally:
        # CRUCIAL : flusher les buffers Python AVANT os._exit (qui ne les vide PAS). Sinon la sentinelle,
        # restée dans le buffer de sys.stdout, n'atteindrait jamais le pipe -> faux SABOTAGE.
        try:
            sys.stdout.flush()
        except BaseException:
            pass
        try:
            sys.stderr.flush()
        except BaseException:
            pass
    os._exit(code_sortie)


def _lit_jusqu_a(fd: int, accu: bytearray, limite: int) -> bool:
    """Lit ce qui est disponible sur fd (non bloquant côté appelant via select). True si EOF (pipe fermé)."""
    try:
        bloc = os.read(fd, 65536)
    except (BlockingIOError, InterruptedError):
        return False
    except OSError:
        return True
    if not bloc:
        return True
    if len(accu) < limite:
        accu.extend(bloc[: limite - len(accu)])
    return False


def juge_fork(solution: str, tests: str, limites: Limites | None = None, executeur=None) -> Verdict:
    """Juge un candidat PYTHON par fork (rapide). Verdict identique au juge subprocess. Langage non-python
    ou plateforme sans fork/resource -> délègue au juge subprocess classique (polyglotte préservé)."""
    limites = limites or Limites()
    langage = getattr(executeur, "langage", "python") if executeur is not None else "python"
    if langage != "python" or resource is None or not hasattr(os, "fork"):
        from juge import juge
        return juge(solution, tests, limites, executeur)

    jeton = "JUGE_SENTINELLE_" + secrets.token_hex(16)
    # MÊME assemblage que ExecuteurPython.assemble (solution + tests + sentinelle imprimée APRÈS les tests).
    programme = (textwrap.dedent(solution) + "\n\n" + textwrap.dedent(tests) + "\n" + f"print({jeton!r})\n")

    r_out, w_out = os.pipe()
    r_err, w_err = os.pipe()
    debut = time.monotonic()
    pid = os.fork()
    if pid == 0:                          # ENFANT — ne revient jamais
        try:
            os.close(r_out)
            os.close(r_err)
            _enfant(programme, limites, w_out, w_err)
        except BaseException:
            os._exit(1)
        os._exit(1)                       # garde-fou (jamais atteint)

    # PARENT
    os.close(w_out)
    os.close(w_err)
    for fd in (r_out, r_err):
        os.set_blocking(fd, False)
    out, err = bytearray(), bytearray()
    ouverts = {r_out, r_err}
    # poll() (et non select()) : select.select a une limite DURE à 1024 (FD_SETSIZE) -> « filedescriptor out of
    # range » dès que le process a ≥1024 FD ouverts. poll() n'a AUCUNE limite de numéro de descripteur : le juge
    # encaisse n'importe quelle échelle (esprit machine, pas de plafond humain arbitraire). Verdict inchangé.
    poller = select.poll()
    for fd in ouverts:
        poller.register(fd, select.POLLIN)
    statut_timeout = False
    while ouverts:
        reste = limites.temps_s - (time.monotonic() - debut)
        if reste <= 0:
            statut_timeout = True
            break
        evts = poller.poll(reste * 1000)      # timeout en millisecondes
        if not evts:
            statut_timeout = True
            break
        for fd, _ev in evts:
            accu = out if fd == r_out else err
            if _lit_jusqu_a(fd, accu, _MAX_SORTIE):
                ouverts.discard(fd)
                poller.unregister(fd)
                os.close(fd)

    if statut_timeout:
        # boucle infinie / trop lent : on tue l'enfant et on draine, comme le timeout mur du subprocess.
        try:
            os.kill(pid, signal.SIGKILL)
        except OSError:
            pass
        for fd in list(ouverts):
            try:
                os.close(fd)
            except OSError:
                pass
        os.waitpid(pid, 0)
        duree = time.monotonic() - debut
        return Verdict(statut=TIMEOUT, duree_s=duree,
                       stdout=out.decode("utf-8", "replace"), stderr=err.decode("utf-8", "replace"))

    _, status = os.waitpid(pid, 0)
    duree = time.monotonic() - debut
    # Convention IDENTIQUE au subprocess : returncode = code de sortie, ou -signal si tué par signal.
    if os.WIFSIGNALED(status):
        returncode = -os.WTERMSIG(status)
    else:
        returncode = os.WEXITSTATUS(status)

    stdout = out.decode("utf-8", "replace")
    stderr = err.decode("utf-8", "replace")

    if executeur is None:
        from executeur import DEFAUT
        executeur = DEFAUT
    statut = _classe(returncode, stderr, executeur)          # MÊME classification universelle que le juge
    if statut == PASS and jeton not in stdout:               # MÊME garde sentinelle anti-sabotage
        statut = SABOTAGE
    stdout = stdout.replace(jeton + "\n", "").replace(jeton, "")
    return Verdict(statut=statut, duree_s=duree, stdout=stdout, stderr=stderr)
