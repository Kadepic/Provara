"""
Brique 1 — LE JUGE.

Le cœur incorruptible de toute la boucle d'auto-amélioration.
Son seul rôle : prendre un bout de code candidat + des tests CACHÉS, les exécuter
en SANDBOX isolée, et trancher de façon binaire : passe / échoue.

Principes (cf. PROJET-AUTO-AMELIORATION-CODE.md §3, §4, §5) :
  - Le signal vient de la RÉALITÉ (le code tourne ou pas), jamais d'une auto-évaluation.
  - Incorruptible : le candidat ne voit jamais les tests, et tourne dans un PROCESSUS
    SÉPARÉ avec des limites (temps, mémoire) — il ne peut ni boucler à l'infini, ni
    dévorer la machine, ni polluer le harnais.
  - Binaire et gratuit : le verdict est pass/fail, sans humain dans la boucle.

AGNOSTIQUE AU LANGAGE : le juge orchestre la sandbox, les limites, la sentinelle
et la classification UNIVERSELLE, mais tout ce qui est propre à un langage (écrire
le source, la commande d'exécution, traduire un échec) est délégué à un Executeur
(cf. executeur.py). Ajouter PHP/JS/Rust = un nouvel Executeur, pas un nouveau juge.

Cette brique ne sait RIEN du générateur ni de l'apprentissage. Elle juge, point.
"""

from __future__ import annotations

import dataclasses
try:
    import resource  # POSIX-only. Sur Windows : absent -> on s'appuie sur le
                     # timeout mur du subprocess (cf. preexec_fn gardé en win32).
except ImportError:
    resource = None
import os
import secrets
import signal
import subprocess
import sys
import tempfile
import time
from pathlib import Path


# --- Le verdict --------------------------------------------------------------

# Statuts possibles d'un jugement. Le seul qui compte pour "garder" est PASS.
PASS = "pass"          # le code a passé tous les tests cachés
FAIL = "fail"          # le code a tourné mais un test a échoué (AssertionError, mauvais résultat)
TIMEOUT = "timeout"    # le code a dépassé le temps alloué (boucle infinie, trop lent)
ERROR = "error"        # le code a planté (exception, syntaxe invalide) avant/pendant les tests
KILLED = "killed"      # tué par une limite de ressources (mémoire) ou un signal
SABOTAGE = "sabotage"  # le process s'est terminé "proprement" (code 0) mais les tests ne sont
                       # PAS allés au bout : sortie prématurée (sys.exit, os._exit, quit...) qui
                       # tente de faire dire "pass" sans exécuter les tests. Détecté par la
                       # SENTINELLE (cf. juge()). Faille rattrapée structurellement, pas par motif.


@dataclasses.dataclass(frozen=True)
class Verdict:
    """Le résultat d'un jugement. Immuable : un verdict ne se renégocie pas."""
    statut: str            # une des constantes ci-dessus
    duree_s: float         # temps d'exécution mesuré (secondes)
    stdout: str            # sortie standard du candidat (debug)
    stderr: str            # erreurs / trace (debug, c'est là qu'on lit POURQUOI ça a échoué)

    @property
    def passe(self) -> bool:
        """Le seul bit qui pilote la boucle : a-t-on RÉELLEMENT passé ?"""
        return self.statut == PASS

    def __str__(self) -> str:
        return f"<Verdict {self.statut} en {self.duree_s:.3f}s>"


# --- Les limites de la sandbox ----------------------------------------------

@dataclasses.dataclass(frozen=True)
class Limites:
    """Les garde-fous de la sandbox. Valeurs par défaut volontairement serrées."""
    temps_s: float = 5.0        # temps mur max (timeout du subprocess)
    cpu_s: int = 5              # temps CPU max (setrlimit, coupe les boucles infinies)
    memoire_mo: int = 512       # mémoire adresse max en Mo (setrlimit)
    fichier_mo: int = 64        # taille max d'un fichier écrit par le candidat en Mo (anti-bombe disque)


def _applique_limites(limites: Limites):
    """
    Exécuté dans le processus enfant JUSTE avant le code candidat (preexec_fn).
    Pose des limites dures que le candidat ne peut pas lever. C'est ce qui rend
    le juge incorruptible côté ressources : pas de fork-bomb, pas de fuite mémoire,
    pas de boucle infinie qui bloque la machine.
    """
    # Temps CPU : soft un cran sous le hard. À 'cpu_s', le noyau envoie SIGXCPU
    # (identifiable = "plus de temps CPU" -> TIMEOUT) ; le hard à cpu_s+1 n'est
    # qu'un filet (SIGKILL) si le candidat ignorait SIGXCPU. Si soft==hard, le
    # noyau saute direct à SIGKILL et on perd l'info de la cause.
    resource.setrlimit(resource.RLIMIT_CPU, (limites.cpu_s, limites.cpu_s + 1))
    # Mémoire adressable : empêche le candidat d'allouer toute la RAM.
    octets = limites.memoire_mo * 1024 * 1024
    resource.setrlimit(resource.RLIMIT_AS, (octets, octets))
    # Pas de fichiers de core dump (inutile, salit le disque).
    resource.setrlimit(resource.RLIMIT_CORE, (0, 0))
    # DURCISSEMENT sécurité : taille max des fichiers écrits par le candidat (anti-bombe disque). stdout/stderr
    # sont des PIPES, non concernés -> la sentinelle (print) n'est pas affectée. Cap généreux : bloque l'abus de
    # disque sans gêner une écriture incidente légitime. Le candidat tourne déjà dans un cwd jetable.
    cap_fichier = limites.fichier_mo * 1024 * 1024
    resource.setrlimit(resource.RLIMIT_FSIZE, (cap_fichier, cap_fichier))


def _classe(returncode: int, stderr: str, executeur) -> str:
    """
    Traduit le sort du processus candidat en statut UNIVERSEL.

    Le code de retour 0 et les signaux (CPU, kill) sont AGNOSTIQUES — un process
    est un process, quel que soit le langage. Seule la signification d'une sortie
    NON NULLE (test raté ? crash ? OOM ?) dépend du langage : on la délègue au
    backend via classe_echec().
    """
    if returncode == 0:
        return PASS

    if returncode < 0:
        # Tué par un signal. -returncode == numéro du signal. (Universel.)
        sig = -returncode
        if sig == signal.SIGXCPU:
            return TIMEOUT          # a épuisé son temps CPU = trop lent / boucle
        return KILLED               # SIGKILL (OOM noyau), etc.

    # Exit non-zéro : la cause dépend du langage -> le backend tranche.
    return executeur.classe_echec(returncode, stderr)


# --- Le juge -----------------------------------------------------------------

def juge(solution: str, tests: str, limites: Limites | None = None,
         executeur=None) -> Verdict:
    """
    Juge une SOLUTION candidate contre des TESTS cachés.

    Args:
        solution  : le code proposé (ce que le générateur a produit).
        tests     : le code des tests cachés. Le candidat ne le voit jamais ; ici
                    on l'assemble APRÈS la solution dans un processus isolé.
        limites   : garde-fous de la sandbox (défaut : Limites()).
        executeur : le backend de langage (défaut : Python). C'est lui, et lui
                    seul, qui sait écrire/lancer le code -> juge polyglotte.

    Returns:
        Un Verdict. verdict.passe == True seulement si le process candidat se
        termine avec le code 0 ET que la sentinelle prouve que les tests sont
        allés au bout.

    Le contrat : 'tests' doit faire échouer le process si la solution est fausse,
    et se terminer proprement (code 0) si elle est correcte. Convention standard
    des datasets type HumanEval / MBPP.
    """
    limites = limites or Limites()
    if executeur is None:
        # Import paresseux : évite le cycle juge <-> executeur au chargement.
        from executeur import DEFAUT
        executeur = DEFAUT

    # FAST PATH (forkserver) : pour le langage PYTHON, on FORK le process chaud au lieu de spawner un interpréteur
    # neuf par candidat (~7x, mesuré). Verdict PROUVÉ bit-identique au chemin subprocess ci-dessous
    # (valide_juge_rapide.py 25/25 : pass/fail/timeout/oom/sabotage/sentinelle/isolation). Soupape : JUGE_NO_FORK=1
    # revient au subprocess. POSIX seulement (fork+resource) ; tout autre langage garde le subprocess (polyglotte).
    if (getattr(executeur, "langage", None) == "python" and resource is not None
            and hasattr(os, "fork") and os.environ.get("JUGE_NO_FORK") != "1"):
        from juge_rapide import juge_fork
        return juge_fork(solution, tests, limites, executeur)

    # LA SENTINELLE (durcissement anti-exploit, cf. découverte B5) :
    # un jeton ALÉATOIRE imprimé APRÈS les tests (par l'executeur, dans la syntaxe
    # du langage). Le juge ne déclarera "pass" que si ce jeton apparaît dans la
    # sortie -> preuve que l'exécution est allée jusqu'au bout des tests. Toute
    # sortie prématurée (sys.exit, exit(), exception avalée...) saute l'impression
    # -> jeton absent -> SABOTAGE, pas pass. Aléatoire et par-run : le candidat ne
    # peut pas l'imprimer lui-même. Robuste contre les exploits non encore listés.
    jeton = "JUGE_SENTINELLE_" + secrets.token_hex(16)

    # Le backend assemble le source complet (solution + tests + sentinelle).
    programme = executeur.assemble(solution, tests, jeton)

    # Fichier temporaire isolé. On NE passe PAS le code par stdin pour avoir
    # des numéros de ligne propres dans les traces (debug).
    with tempfile.TemporaryDirectory(prefix="juge_") as bac:
        chemin = Path(bac) / executeur.fichier
        chemin.write_text(programme, encoding="utf-8")

        # preexec_fn n'existe que sur POSIX. Sur Linux/WSL (notre cible), parfait.
        preexec = (lambda: _applique_limites(limites)) if sys.platform != "win32" else None

        debut = time.monotonic()
        try:
            proc = subprocess.run(
                executeur.commande(str(chemin)),       # la commande dépend du langage
                capture_output=True,
                text=True,
                timeout=limites.temps_s,
                preexec_fn=preexec,
                cwd=bac,                               # cwd jetable
                # Windows : jamais de fenêtre console pour un candidat (0 ailleurs — sans effet POSIX).
                creationflags=getattr(subprocess, "CREATE_NO_WINDOW", 0),
            )
        except subprocess.TimeoutExpired as e:
            return Verdict(
                statut=TIMEOUT,
                duree_s=time.monotonic() - debut,
                stdout=(e.stdout or "") if isinstance(e.stdout, str) else "",
                stderr=(e.stderr or "") if isinstance(e.stderr, str) else "",
            )
        duree = time.monotonic() - debut

        # On classe le verdict pour le debug ET la détection d'exploits.
        # Le seul bit qui pilote la boucle reste 'passe' (statut == PASS).
        statut = _classe(proc.returncode, proc.stderr or "", executeur)

        # Vérification de la sentinelle : un "pass" sans le jeton = sortie
        # prématurée -> les tests ne sont pas allés au bout -> SABOTAGE.
        stdout = proc.stdout or ""
        if statut == PASS and jeton not in stdout:
            statut = SABOTAGE
        # On retire le jeton de la sortie rendue (bruit de debug).
        stdout = stdout.replace(jeton + "\n", "").replace(jeton, "")

        return Verdict(
            statut=statut,
            duree_s=duree,
            stdout=stdout,
            stderr=proc.stderr or "",
        )
