#!/usr/bin/env python3
"""
VALIDATION de equivalence_semantique.py. FAUX=0 : EQUIVALENTES seulement sur domaine fini exhaustif ; sinon
DIFFERENTES (contre-exemple réel) ou NON_DISTINGUEES (jamais « équivalentes »). Léger (stdlib pur, pas de lecteur).
"""
from __future__ import annotations

import sys

import equivalence_semantique as E


def main() -> int:
    ok, fails = 0, []

    def check(nom, cond):
        nonlocal ok
        if cond:
            ok += 1
            print(f"  [OK ] {nom}")
        else:
            fails.append(nom)
            print(f"  [XX ] {nom}")

    # ── Domaine fini : deux écritures de la même fonction -> EQUIVALENTES (preuve exhaustive) ──
    f1 = lambda x: x * 2
    f2 = lambda x: x + x
    r = E.sur_domaine(f1, f2, range(-100, 101))
    check("DOMAINE FINI : x*2 == x+x prouvé EQUIVALENTES", r["statut"] == E.EQUIVALENTES)

    # ── Domaine fini : deux fonctions qui diffèrent -> DIFFERENTES + contre-exemple ───────────
    g1 = lambda x: x * x
    g2 = lambda x: x + x
    r2 = E.sur_domaine(g1, g2, range(0, 50))
    check("DOMAINE FINI : x² vs x+x -> DIFFERENTES", r2["statut"] == E.DIFFERENTES)
    check("DIFFERENTES : contre-exemple réel (g1(ce) != g2(ce))",
          g1(r2["contre_exemple"]) != g2(r2["contre_exemple"]))
    # x²==x+x seulement pour x∈{0,2} ; le 1er point distinct dans range(0,50) est x=1
    check("DIFFERENTES : premier point distinct = 1", r2["contre_exemple"] == 1)

    # ── Exception d'un seul côté = différence de comportement ─────────────────────────────────
    h1 = lambda x: 10 // x if x != 0 else 0
    h2 = lambda x: 10 // x                    # lève sur x=0
    r3 = E.sur_domaine(h1, h2, range(0, 10))
    check("EXCEPTION : un côté lève sur x=0 -> DIFFERENTES",
          r3["statut"] == E.DIFFERENTES and r3["contre_exemple"] == 0)

    # ── Échantillonnage : fonctions équivalentes -> NON_DISTINGUEES (jamais « équivalentes ») ──
    r4 = E.par_echantillon(f1, f2, lambda rng: rng.randint(-10 ** 6, 10 ** 6), n=500, graine=1)
    check("ÉCHANTILLON : x*2 et x+x NON_DISTINGUEES (honnête, pas « prouvé »)",
          r4["statut"] == E.NON_DISTINGUEES)

    # ── Échantillonnage : fonctions différentes -> DIFFERENTES + contre-exemple réduit ────────
    r5 = E.par_echantillon(g1, g2, lambda rng: rng.randint(0, 1000), n=500, graine=2)
    check("ÉCHANTILLON : x² vs x+x -> DIFFERENTES", r5["statut"] == E.DIFFERENTES)
    check("ÉCHANTILLON FAUX=0 : le contre-exemple distingue réellement",
          g1(r5["contre_exemple"]) != g2(r5["contre_exemple"]))

    # ── Façade equivalent() ───────────────────────────────────────────────────────────────────
    check("FAÇADE : domaine -> preuve", E.equivalent(f1, f2, domaine=range(0, 10))["statut"] == E.EQUIVALENTES)
    check("FAÇADE : generateur -> échantillon",
          E.equivalent(g1, g2, generateur=lambda rng: rng.randint(1, 100), n=200)["statut"] == E.DIFFERENTES)
    check("FAÇADE FAUX=0 : ni domaine ni generateur -> ValueError",
          _leve(lambda: E.equivalent(f1, f2)))

    # ── CÂBLAGE ia.py ─────────────────────────────────────────────────────────────────────────
    import ia
    check("CÂBLAGE ia.equivalent : preuve sur domaine fini", ia.equivalent(f1, f2, domaine=range(0, 10))["statut"] == E.EQUIVALENTES)

    print(f"\n=== valide_equivalence_semantique : {ok}/{ok + len(fails)} ===")
    if fails:
        print("ÉCHECS :", ", ".join(fails))
    return 0 if not fails else 1


def _leve(fn):
    try:
        fn(); return False
    except ValueError:
        return True


if __name__ == "__main__":
    sys.exit(main())
