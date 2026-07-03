"""
NIVEAU DE RICHESSE — le « cran » sélectionnable (2026-06-17, vision Yohan : pouvoir choisir une bonne réponse
de base OU une réponse complète, sans jamais recevoir du faux). Le juge restant binaire, la richesse est
définie de façon VÉRIFIABLE = largeur du domaine adverse (T1..T4) que la réponse couvre RÉELLEMENT.

`resoudre_niveau(orchestre, prompt, point_entree, paliers, niveau)` s'engage sur le 1er candidat passant la
porte CUMULÉE du niveau (visibles + held-out T1..TN). Mesure `mesure_richesse.py` : une porte « nue » (visibles
faibles seuls) laisse passer une COÏNCIDENCE (gcd ≈ a%b matche 2 points par hasard) -> dangereux. Le held-out
PAR NIVEAU est le garde-fou : il tue la coïncidence.

Critères de MORT (4) :
  1. DANGER prouvé : porte NUE (visibles T1 seuls) -> le moteur s'engage sur une coïncidence qui ÉCHOUE l'adverse.
  2. SÛRETÉ      : porte du niveau 1 (visibles + held-out) -> le candidat engagé PASSE l'adverse (pas de coïncidence).
  3. MONOTONE    : la réponse du niveau 4 (complète) satisfait AUSSI la porte du niveau 1 (riche ⊇ étroit).
  4. LEVIER      : quand un candidat correct-sur-le-domaine-étroit existe en amont, niveau bas s'engage MOINS CHER
                   que niveau haut (et chacun correct sur SON domaine) — le cran règle puissance ↔ complétude.
"""

from __future__ import annotations

from compounding import _porte_niveau, resoudre_niveau
from diable import _moteur_complet, _seede
from juge import Limites, juge
from store import Store
from taches import Tache  # noqa: F401  (cohérence d'import du harnais)

import tempfile
from pathlib import Path

LIM = Limites(temps_s=3, cpu_s=2)
K = 600

# --- gcd : la capacité où la mesure a vu une coïncidence cheap (a%b matche 2 points) ---
GCD_PROMPT = 'def gcd(a, b):\n    """..."""'
# paliers du plus basique (T1) au plus adverse (T4). Held-out PAR NIVEAU = cas frais qui tuent les coïncidences.
GCD_PALIERS = [
    (["    assert c(12, 8) == 4", "    assert c(7, 3) == 1"],
     ["    assert c(100, 60) == 20", "    assert c(8, 12) == 4"]),      # a%b: 100%60=40≠20 ; 8%12=8≠4 -> tue a%b
    (["    assert c(5, 5) == 5", "    assert c(1, 9) == 1"],
     ["    assert c(17, 5) == 1", "    assert c(48, 36) == 12"]),
    (["    assert c(81, 27) == 27", "    assert c(14, 21) == 7"],
     ["    assert c(1000, 4) == 4", "    assert c(13, 7) == 1"]),
    (["    assert c(36, 24) == 12", "    assert c(100, 75) == 25"],
     ["    assert c(7, 7) == 7", "    assert c(1, 1) == 1"]),
]
GCD_ADVERSE_T1 = GCD_PALIERS[0][1]   # le held-out du niveau 1, utilisé comme épreuve d'anti-coïncidence


def _moteur():
    with tempfile.TemporaryDirectory() as d:
        st = Store(Path(d) / "s.jsonl")
        _seede(st)
        return _moteur_complet(st)


def _adverse_t1_program():
    return "def check(c):\n" + "\n".join(GCD_ADVERSE_T1) + "\ncheck(gcd)\n"


# --- LEVIER : orchestre minimal à 2 étages (mécanisme déterministe). Un candidat correct-plus-étroit
#     (`xs[-1]`, juste sur listes TRIÉES) précède le complet (`max(xs)`, juste partout). ---
class _OrchestreStub:
    def __init__(self, etages):
        self._etages = etages

    def etages(self, prompt, k):
        return self._etages


STUB = _OrchestreStub([
    ("rapide", ["def f(*args, **kwargs):\n    return args[0][-1]\n"]),   # juste sur trié seulement
    ("complet", ["def f(*args, **kwargs):\n    return max(args[0])\n"]),  # juste partout (plus cher : 2e étage)
])
MAX_PALIERS = [
    (["    assert c([1,2,3]) == 3", "    assert c([5,9]) == 9"],          # T1 : listes TRIÉES
     ["    assert c([1,1,4]) == 4", "    assert c([2,7,8]) == 8"]),       # held trié -> xs[-1] reste correct
    (["    assert c([3,1,2]) == 3"], ["    assert c([9,1,5]) == 9"]),     # T2 : NON triées -> xs[-1] casse
    (["    assert c([4,4,1]) == 4"], ["    assert c([2,8,3,1]) == 8"]),
    (["    assert c([10,-5,7]) == 10"], ["    assert c([-1,-9,-3]) == -1"]),
]
MAX_PROMPT = 'def f(xs):\n    """..."""'


def _check(nom, ok):
    print(f"  [{'OK ' if ok else 'RATÉ'}] {nom}", flush=True)
    return ok


def main() -> int:
    r = []

    # 1. DANGER : porte NUE (visibles T1 seuls, held-out vidé) -> coïncidence engagée, échoue l'adverse.
    paliers_nus = [(GCD_PALIERS[0][0], [])]
    e, ap, code_nu = resoudre_niveau(_moteur(), GCD_PROMPT, "gcd", paliers_nus, 1, LIM, K)
    danger = code_nu is not None and not juge(code_nu, _adverse_t1_program(), LIM).passe
    r.append(_check(f"DANGER : porte NUE engage une COÏNCIDENCE via `{e}` ({ap} appels) qui ÉCHOUE l'adverse "
                    f"-> tests faibles = faux", danger))

    # 2. SÛRETÉ : porte du niveau 1 (visibles + held-out) -> le candidat engagé PASSE l'adverse.
    e1, ap1, code1 = resoudre_niveau(_moteur(), GCD_PROMPT, "gcd", GCD_PALIERS, 1, LIM, K)
    sur = code1 is not None and juge(code1, _adverse_t1_program(), LIM).passe
    r.append(_check(f"SÛRETÉ : porte niveau 1 (held-out par niveau) engage via `{e1}` un candidat qui PASSE "
                    f"l'adverse -> coïncidence refusée, jamais de faux", sur))

    # 3. MONOTONE : la réponse complète (niveau 4) satisfait AUSSI la porte du niveau 1.
    e4, ap4, code4 = resoudre_niveau(_moteur(), GCD_PROMPT, "gcd", GCD_PALIERS, 4, LIM, K)
    porte1_vis = _porte_niveau("gcd", GCD_PALIERS, 1, 0)
    porte1_held = _porte_niveau("gcd", GCD_PALIERS, 1, 1)
    mono = (code4 is not None and juge(code4, porte1_vis, LIM).passe and juge(code4, porte1_held, LIM).passe)
    r.append(_check(f"MONOTONE : la réponse complète niveau 4 (`{e4}`, {ap4} appels) satisfait aussi la porte "
                    f"niveau 1 (riche ⊇ étroit)", mono))

    # 4. LEVIER : niveau bas s'engage MOINS CHER sur un correct-plus-étroit ; niveau haut force le complet.
    eb, apb, codeb = resoudre_niveau(STUB, MAX_PROMPT, "f", MAX_PALIERS, 1, LIM, K)
    eh, aph, codeh = resoudre_niveau(STUB, MAX_PROMPT, "f", MAX_PALIERS, 4, LIM, K)
    levier = (codeb is not None and codeh is not None and eb == "rapide" and eh == "complet" and apb < aph)
    r.append(_check(f"LEVIER : niveau 1 -> `{eb}` ({apb} appels, correct sur trié) ; niveau 4 -> `{eh}` ({aph} "
                    f"appels, correct partout) -> le cran règle puissance ↔ complétude", levier))

    print()
    print("NIVEAU DE RICHESSE VALIDÉ — 4/4." if all(r) else f"ÉCHEC — {sum(r)}/4.")
    return 0 if all(r) else 1


if __name__ == "__main__":
    raise SystemExit(main())
