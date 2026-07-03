"""
VALIDE — RÉSOLUTION CHAÎNÉE (2026-06-22, point 4). Contrat de `resoudre_tout` :
  - tâche résoluble -> rend un CODE qui passe le juge (visible + held-out), via 'principal' OU 'auto-invention' ;
  - tâche incohérente -> 'HORS' (jamais de faux) ;
  - la branche auto-invention est SOUND (held-out exigé) et `demande.py` reste intact (zéro régression).
SÉQUENTIEL + garde mémoire.
"""
from __future__ import annotations

from auto_invention_ouverte import LIM
from demande import _asserts
from garde_ressources import borne
from juge import juge
from resoudre_tout import resoudre_tout


def _passe(pe, code, ex, held):
    ex_pairs = [((a,), o) for a, o in ex]
    held_pairs = [((a,), o) for a, o in held]
    return (juge(code, _asserts(pe, ex_pairs), LIM).passe
            and juge(code, _asserts(pe, held_pairs), LIM).passe)


def _check(nom, cond):
    print(f"  [{'OK ' if cond else 'RATÉ'}] {nom}")
    return cond


def main() -> int:
    borne()
    res = []

    # 1) résoluble (multi-arg) -> code correct (généralise).
    pe, sig, ex, held = "somme_carres", "xs", [([1, 2, 3], 14), ([2, 3], 13)], [([5], 25), ([0, 4], 16)]
    o, code = resoudre_tout(pe, sig, ex, held)
    res.append(_check(f"somme_carres [{o}] code généralise", o in ("principal", "auto-invention") and code and _passe(pe, code, ex, held)))

    # 2) domaine chaîne (mono-arg) -> code correct (principal ou relais autonome).
    pe, sig, ex, held = "renverse", "x", [("abc", "cba"), ("hello", "olleh")], [("xy", "yx"), ("a", "a")]
    o, code = resoudre_tout(pe, sig, ex, held)
    res.append(_check(f"renverse [{o}] code généralise", o in ("principal", "auto-invention") and code and _passe(pe, code, ex, held)))

    # 3) incohérent -> HORS honnête (jamais de faux).
    o, code = resoudre_tout("incoherent", "x", [([3, 1, 2], 42)], [([5], 99)])
    res.append(_check(f"incohérent -> {o}", o == "HORS" and code is None))

    n = sum(res)
    print(f"\nRESOUDRE_TOUT {'VALIDÉ' if n == len(res) else 'ÉCHEC'} — {n}/{len(res)}.")
    return 0 if n == len(res) else 1


if __name__ == "__main__":
    raise SystemExit(main())
