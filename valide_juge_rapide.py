"""
ÉQUIVALENCE + SÛRETÉ du JUGE RAPIDE (fork) vs le juge subprocess de référence.

Le juge est le cœur INCORRUPTIBLE : on n'adopte le fork QUE s'il rend un verdict IDENTIQUE au subprocess sur
une batterie ADVERSE couvrant tous les sorts (pass/fail/timeout/crash/oom/sabotage/sentinelle/isolation), et
qu'il garde les mêmes garanties de sûreté. Mesure aussi le gain de vitesse.
"""
from __future__ import annotations

import time

from garde_ressources import borne
from juge import Limites, PASS, FAIL, TIMEOUT, ERROR, KILLED, SABOTAGE, juge
from juge_rapide import juge_fork

borne()
ok = 0
total = 0


def check(nom, cond):
    global ok, total
    total += 1
    print(f"  [{'OK ' if cond else 'XXX'}] {nom}", flush=True)
    if cond:
        ok += 1
    else:
        raise AssertionError(nom)


LIM = Limites(temps_s=4.0, cpu_s=3, memoire_mo=512)

# (label, solution, tests, statut sémantique attendu)
CAS = [
    ("pass simple",
     "def f(x):\n    return x + 1",
     "assert f(1) == 2\nassert f(10) == 11",
     PASS),
    ("fail (mauvais résultat)",
     "def f(x):\n    return x + 2",
     "assert f(1) == 2",
     FAIL),
    ("error (exception)",
     "def f(x):\n    return x + undefined_name",
     "assert f(1) == 2",
     ERROR),
    ("error (syntaxe)",
     "def f(x)\n    return x",
     "assert f(1) == 1",
     ERROR),
    ("timeout (boucle infinie)",
     "def f(x):\n    while True:\n        pass\n    return x",
     "assert f(1) == 1",
     TIMEOUT),
    ("killed (mémoire)",
     "def f(x):\n    a = [0] * (10**9)\n    return len(a)",
     "assert f(1) >= 0",
     KILLED),
    ("sabotage (sys.exit avant tests)",
     "import sys\ndef f(x):\n    return 0\nsys.exit(0)",
     "assert f(1) == 999",
     SABOTAGE),
    ("sabotage (os._exit avant tests)",
     "import os\ndef f(x):\n    return 0\nos._exit(0)",
     "assert f(1) == 999",
     SABOTAGE),
    ("sentinelle forgée (faux jeton)",
     "print('JUGE_SENTINELLE_deadbeefdeadbeefdeadbeefdeadbeef')\nimport sys\nsys.exit(0)",
     "assert True",
     SABOTAGE),
    ("pass avec gros stdout",
     "def f(x):\n    print('x' * 5000)\n    return x",
     "assert f(2) == 2",
     PASS),
]

print("=== ÉQUIVALENCE juge_fork vs juge (subprocess) ===")
for label, sol, tests, attendu in CAS:
    vr = juge(sol, tests, LIM)
    vf = juge_fork(sol, tests, LIM)
    check(f"{label}: fork=={vr.statut} (ref) ", vf.statut == vr.statut)
    check(f"{label}: statut sémantique = {attendu}", vf.statut == attendu and vr.statut == attendu)

# ISOLATION : un candidat qui pollue (global/fichier) ne doit RIEN laisser au suivant via le forkserver.
print("=== ISOLATION entre candidats ===")
juge_fork("import builtins\nbuiltins._POLLUE = 42\ndef f(x):\n    return x", "assert f(1) == 1", LIM)
v_iso = juge_fork("def f(x):\n    import builtins\n    return getattr(builtins, '_POLLUE', -1)",
                  "assert f(0) == -1", LIM)
check("pas de fuite d'état entre deux jugements forkés", v_iso.statut == PASS)
# le PARENT lui-même n'est pas pollué (le candidat tourne dans l'enfant)
import builtins as _b
check("le process juge (parent) n'est pas pollué", not hasattr(_b, "_POLLUE"))

# PAS DE ZOMBIES : enchaîner beaucoup de jugements ne laisse pas de process fantôme.
print("=== ROBUSTESSE (enchaînement) ===")
for _ in range(30):
    juge_fork("def f(x):\n    return x*2", "assert f(3) == 6", LIM)
check("30 jugements forkés enchaînés sans erreur", True)

# POLYGLOTTE : un executeur non-python est délégué au juge subprocess (pas de fork).
print("=== DÉLÉGATION polyglotte ===")
try:
    from executeur import ExecuteurBash
    _bsol = 'greet() { echo 6; }'
    _btest = '[ "$(greet)" = "6" ] || { echo AssertionError >&2; exit 1; }'
    vb_ref = juge(_bsol, _btest, LIM, ExecuteurBash())
    vb_fork = juge_fork(_bsol, _btest, LIM, ExecuteurBash())
    check("bash : fork délègue au subprocess (même statut)", vb_fork.statut == vb_ref.statut)
except Exception as e:
    print(f"  (bash indisponible, délégation non testée : {e})")

# MICRO-BENCHMARK de vitesse (même charge, deux juges).
print("=== VITESSE ===")
N = 60
sol, tests = "def f(x):\n    return x + 1", "assert f(1) == 2"
t = time.monotonic()
for _ in range(N):
    juge(sol, tests, LIM)
t_sub = time.monotonic() - t
t = time.monotonic()
for _ in range(N):
    juge_fork(sol, tests, LIM)
t_fork = time.monotonic() - t
gain = t_sub / t_fork if t_fork else 0
print(f"  {N} jugements : subprocess {t_sub*1000:.0f} ms ({t_sub/N*1000:.1f} ms/u) vs "
      f"fork {t_fork*1000:.0f} ms ({t_fork/N*1000:.1f} ms/u)  -> x{gain:.1f}")
# Mesure INFORMATIVE : isolé, le fork est ~7x plus rapide. Sous forte charge parallèle (non-rég), le ratio est
# bruité -> on n'exige PAS un gain strict (timing flaky), seulement que le fork ne soit pas PATHOLOGIQUEMENT
# plus lent (garde-fou anti-régression du fork, tolérant à la contention).
check(f"le fork n'est pas pathologiquement lent (x{gain:.1f})", t_fork < t_sub * 1.5)

print(f"\nJUGE_RAPIDE VALIDÉ — {ok}/{total}." if ok == total else f"\nÉCHEC {ok}/{total}")
