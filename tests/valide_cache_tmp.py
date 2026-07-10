"""
VALIDE L'ÉCRITURE ATOMIQUE DU CACHE — aucun .tmp ne fuit, les abandonnés sont balayés.

DÉFAUT MESURÉ (2026-07-12). Le cache écrivait `mkstemp -> write -> os.replace` sous `except: pass`. Un
échec APRÈS mkstemp, ou un kill DUR (OOM/SIGKILL, non rattrapable), laissait un .tmp orphelin. Un cache
vécu portait **4 371 .tmp (26 Go)** — tous des écritures interrompues de tables VIVANTES (vérifié : aucun
ne portait une relation absente du store, donc AUCUN « manque à câbler » caché). Deux défenses, ici gardées :

  1. `_ecrit_atomique` : le .tmp est TOUJOURS retiré si le replace n'a pas eu lieu (try/finally) ;
  2. `_purge_tmp_orphelins` : au 1ᵉʳ write d'un process, les .tmp plus vieux que `_TMP_TTL` sont balayés
     — seule parade au kill dur. Un .tmp RÉCENT (writer concurrent) n'est JAMAIS touché.
"""
import os
import sys
import tempfile
import time

sys.path.insert(0, os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "src"))
import lecteur as L

ok = 0
ko = 0


def check(cond, label):
    global ok, ko
    if cond:
        ok += 1
    else:
        ko += 1
        print(f"  FAIL: {label}")


_tmp = tempfile.mkdtemp(prefix="verax_cachetmp_")
_sauve_dir, _sauve_flag = L._CACHE_DIR, L._purge_tmp_faite
L._CACHE_DIR = _tmp
L._purge_tmp_faite = False


def _tmps():
    return [f for f in os.listdir(_tmp) if f.endswith(".tmp")]


# ── 1) ÉCRITURE NORMALE : le .tmp est consommé, rien ne fuit ─────────────────────────────────────────
cible = os.path.join(_tmp, "essai.bin")
L._ecrit_atomique(cible, lambda fh: fh.write(b"contenu"))
check(os.path.exists(cible) and open(cible, "rb").read() == b"contenu", "le fichier final est écrit")
check(_tmps() == [], "aucun .tmp ne subsiste après une écriture réussie")

# ── 2) ÉCHEC PENDANT L'ÉCRITURE : le .tmp est nettoyé (pas de fuite) ─────────────────────────────────
def _explose(fh):
    fh.write(b"partiel")
    raise RuntimeError("kill simulé avant le replace")

try:
    L._ecrit_atomique(os.path.join(_tmp, "jamais.bin"), _explose)
    check(False, "l'exception doit remonter (pas d'avalage ici)")
except RuntimeError:
    check(True, "l'exception d'écriture remonte")
check(_tmps() == [], "un échec d'écriture ne laisse AUCUN .tmp (try/finally)")
check(not os.path.exists(os.path.join(_tmp, "jamais.bin")), "le fichier final n'est pas créé sur échec")

# ── 3) PURGE : les .tmp ABANDONNÉS (vieux) tombent, les RÉCENTS restent ──────────────────────────────
vieux = os.path.join(_tmp, "tmpVIEUX.tmp")
recent = os.path.join(_tmp, "tmpRECENT.tmp")
open(vieux, "wb").write(b"z")
open(recent, "wb").write(b"z")
os.utime(vieux, (time.time() - L._TMP_TTL - 100, time.time() - L._TMP_TTL - 100))   # au-delà du TTL
L._purge_tmp_faite = False                                   # ré-arme la purge une fois
L._ecrit_atomique(os.path.join(_tmp, "decl.bin"), lambda fh: fh.write(b"x"))
check(not os.path.exists(vieux), "un .tmp abandonné (plus vieux que _TMP_TTL) est balayé")
check(os.path.exists(recent), "un .tmp RÉCENT n'est JAMAIS touché (pas de course avec un writer concurrent)")

# ── 4) LA PURGE NE S'EXÉCUTE QU'UNE FOIS PAR PROCESS ─────────────────────────────────────────────────
autre_vieux = os.path.join(_tmp, "tmpVIEUX2.tmp")
open(autre_vieux, "wb").write(b"z")
os.utime(autre_vieux, (time.time() - L._TMP_TTL - 100, time.time() - L._TMP_TTL - 100))
L._ecrit_atomique(os.path.join(_tmp, "decl2.bin"), lambda fh: fh.write(b"x"))   # purge déjà faite
check(os.path.exists(autre_vieux),
      "la purge ne re-balaye pas au 2ᵉ write (garde `_purge_tmp_faite` : un seul scan par process)")

L._CACHE_DIR, L._purge_tmp_faite = _sauve_dir, _sauve_flag
print("=== valide_cache_tmp : %d ok, %d ko ===" % (ok, ko))
sys.exit(1 if ko else 0)
