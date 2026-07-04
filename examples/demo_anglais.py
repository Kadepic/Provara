import os, sys; sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), '..'))
import verax_boot  # noqa: F401  -- chemins Provara (src/, ...)
"""
DÉMO ANGLAIS — preuve que le RAISONNEMENT est AGNOSTIQUE à la langue (2026-06-18).

Mêmes briques SENS (est_un, ancetre_commun, …) et mêmes outils (convertit_kaikki, SavoirMassif) que le français —
on change SEULEMENT la source de données (English Wiktionary via kaikki) et la langue ('en', hyperonymes structurés).
L'IA répond « is a cat an animal? -> yes » avec exactement le même moteur. Rien de français n'est touché.
"""
from __future__ import annotations

import sys
import urllib.parse
import urllib.request

from convertit_kaikki import convertit
from savoir_massif import SavoirMassif

BASE = "https://kaikki.org/dictionary/English/meaning"


def _url(mot):
    return f"{BASE}/{urllib.parse.quote(mot[:1])}/{urllib.parse.quote(mot[:2])}/{urllib.parse.quote(mot)}.jsonl"


def _fetch(mots):
    out = []
    for m in mots:
        try:
            with urllib.request.urlopen(_url(m), timeout=20) as r:
                txt = r.read().decode("utf-8")
            premiere = next((ln for ln in txt.splitlines() if ln.strip()), None)
            if premiere:
                out.append(premiere)
        except Exception as e:
            print(f"  ! {m}: {type(e).__name__}", file=sys.stderr)
    return out


def _closure(seeds, rounds=3, cap=140):
    """Fermeture transitive (mêmes principes qu'etend_savoir) sur English Wiktionary."""
    lignes, vus, todo = [], set(), list(dict.fromkeys(seeds))
    for _ in range(rounds):
        todo = [m for m in todo if m not in vus][: max(0, cap - len(vus))]
        if not todo:
            break
        vus.update(todo)
        lignes += _fetch(todo)
        lex = convertit(lignes, langue="en", hyper_prioritaire=True)
        hypers = {d["hyper"] for d in lex.values() if d.get("hyper")}
        todo = sorted(h for h in hypers if h not in lex)
    return convertit(lignes, langue="en", hyper_prioritaire=True)


def main(argv) -> int:
    seeds = argv or ["cat", "dog", "lion", "tiger", "car", "guitar", "apple", "rose"]
    lex = _closure(seeds)
    sav = SavoirMassif(lex)
    print(f"Lexique ANGLAIS auto-construit (English Wiktionary) : {sav.n} entrées, {len(sav.suiv)} arêtes is-a\n")
    print("is-a chains:")
    for m in seeds:
        if m in lex:
            print(f"    {m:<8}: {' -> '.join(sav.ancetres(m))}")
    print("\nReasoning (same living briques as French):")
    for x, y in [("cat", "animal"), ("dog", "animal"), ("car", "animal"), ("guitar", "instrument")]:
        print(f"    is a {x} a(n) {y}? -> {'YES' if sav.est_un(x, y) else 'no'}")
    print(f"    common ancestor(cat, dog) -> {sav.ancetre_commun('cat', 'dog')}")
    print(f"    synonyms(car) -> {sav.synonymes('car')[:5]}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main(sys.argv[1:]))
