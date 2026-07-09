"""
GARDE-RESSOURCES — filet dur kernel pour que l'exploration ne fasse JAMAIS tomber WSL (2026-06-19).

CONSTAT mesuré : `recherche_dirigee.synthetise` sur une cible SANS solution épuise son budget en
générant ~200 000 candidats ; chaque candidat = un `exec`/compile (un code-object). tracemalloc n'en
voit qu'une partie (~1,1 Go), mais le RSS réel grimpe à ~4 Go (code-objects + fragmentation de
l'allocateur CPython, qui ne rend pas les arènes au système). Sans `.wslconfig` ni `ulimit`, RIEN ne
borne ce process : vmmem gonfle et WSL crashe/redémarre. C'est exactement le plantage observé.

Ici on pose un PLAFOND DUR au niveau du noyau via setrlimit :
  - RLIMIT_AS  : adresse virtuelle max -> au-delà, malloc renvoie NULL -> Python lève MemoryError
                 (RATTRAPABLE : `synthetise` la convertit en None honnête, jamais en crash).
  - RLIMIT_CPU : temps CPU max -> SIGXCPU puis SIGKILL si un run part en boucle.

C'est `sûr avant rapide` : on PRÉFÈRE un None honnête (ou un process tué proprement) à un WSL par terre.
Idempotent et ne fait que DURCIR (jamais relâcher) une limite déjà posée. À appeler en tête de tout
runner lourd (`_diag_dirigee.py`, le `__main__` du moteur, les balayages).
"""
from __future__ import annotations

import os

try:
    import resource                     # POSIX seulement (WSL/Linux : le filet dur kernel fonctionne)
except ImportError:                     # Windows (.exe) : pas de setrlimit — vécu 2026-07-09, l'import en dur
    resource = None                     # tuait TOUTES les briques appelantes (invente_et_retiens & co.)


def pmap(fn, items):
    """map parallèle mais SÉQUENTIEL PAR DÉFAUT (`IA_NPROC=1`) — applique « un seul process lourd à la fois » :
    une FLOTTE de moteurs en RAM (Pool(cpu-1)) a déjà fait redémarrer le PC. Bump `IA_NPROC` SEULEMENT si la
    machine est libre. Drop-in pour `with Pool(...) as p: p.map(fn, items)`."""
    items = list(items)
    nproc = max(1, int(os.environ.get("IA_NPROC", "1")))
    if nproc == 1 or not items:
        return [fn(x) for x in items]
    from multiprocessing import Pool
    with Pool(processes=min(nproc, len(items))) as pool:
        return pool.map(fn, items)


def borne(max_go: float = 2.0, max_cpu_s: int = 120) -> dict:
    """Pose un plafond mémoire (Go) et CPU (s) sur le PROCESS courant. Renvoie ce qui a été appliqué.

    max_go convertit un dépassement mémoire en MemoryError rattrapable AVANT que WSL ne tombe.
    max_cpu_s borne un run parti en vrille. Les deux ne font que durcir une limite existante.
    """
    applique = {}
    if resource is None:
        # Windows : setrlimit n'existe pas. HONNÊTE : on le DIT (dict vide + clé explicite) au lieu de mentir
        # avec de fausses limites. Le risque WSL (vmmem) n'existe pas ici ; la sandbox juge garde ses propres
        # bornes par sous-processus (timeout subprocess), et l'utilisateur .exe reste protégé par le système.
        return {"indisponible": "setrlimit absent (Windows)"}
    octets = int(max_go * 1024 ** 3)
    for nom, ressource, val in (("AS", resource.RLIMIT_AS, octets),
                                ("CPU", resource.RLIMIT_CPU, max_cpu_s)):
        soft, hard = resource.getrlimit(ressource)
        # nouvelle borne = min(val demandé, hard existant si fini) ; on ne dépasse jamais le hard.
        plafond = val if hard == resource.RLIM_INFINITY else min(val, hard)
        nouveau_soft = plafond if soft == resource.RLIM_INFINITY else min(soft, plafond)
        try:
            resource.setrlimit(ressource, (nouveau_soft, plafond))
            applique[nom] = nouveau_soft
        except (ValueError, OSError):
            applique[nom] = soft  # impossible de durcir (déjà plus strict) : on garde l'existant
    return applique


if __name__ == "__main__":
    print("garde_ressources : applique ->", borne())
