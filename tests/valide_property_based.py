#!/usr/bin/env python3
"""
VALIDATION de property_based.py — falsification active. FAUX=0 : refute=True -> contre-exemple RÉEL et réduit qui
viole encore ; refute=False = « non réfuté en N essais » (jamais « prouvé ») ; déterministe (graine). Léger.
"""
from __future__ import annotations

import sys

import property_based as PB


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

    # ── Propriété FAUSSE sur entiers : « tout x∈[0,100] est < 50 » -> contre-exemple minimal = 50 ──
    r = PB.pour_tout(lambda x: x < 50, lambda rng: rng.randint(0, 100), n=500, graine=1)
    check("ENTIER : propriété fausse réfutée", r["refute"] is True)
    check("ENTIER : contre-exemple viole réellement (≥ 50)", r["contre_exemple"] >= 50)
    check("ENTIER : shrinking -> le plus petit reproducteur = 50", r["contre_exemple"] == 50)

    # ── Propriété VRAIE : x + 0 == x -> non réfutée (JAMAIS « prouvée ») ───────────────────────
    r2 = PB.pour_tout(lambda x: x + 0 == x, lambda rng: rng.randint(-1000, 1000), n=300, graine=2)
    check("VRAIE : non réfutée en 300 essais (refute=False)", r2["refute"] is False and r2["contre_exemple"] is None)

    # ── Propriété FAUSSE sur listes : « somme < 5 » pour listes d'entiers positifs -> liste minimale ──
    def gen_liste(rng):
        return [rng.randint(0, 9) for _ in range(rng.randint(0, 8))]
    r3 = PB.pour_tout(lambda xs: sum(xs) < 5, gen_liste, n=500, graine=3)
    check("LISTE : propriété fausse réfutée", r3["refute"] is True)
    check("LISTE FAUX=0 : le contre-exemple viole encore (somme ≥ 5)", sum(r3["contre_exemple"]) >= 5)
    check("LISTE : shrinking minimise (reproducteur court)", len(r3["contre_exemple"]) <= 3)

    # ── Propriété qui CRASHE sur certaines entrées : le crash = violation (1/x avec x=0) ──────
    r4 = PB.pour_tout(lambda x: (1 / x) == (1 / x), lambda rng: rng.randint(-5, 5), n=200, graine=4)
    check("CRASH = violation : division par 0 attrapée comme contre-exemple",
          r4["refute"] is True and r4["contre_exemple"] == 0)

    # ── Déterminisme : même graine -> même verdict ────────────────────────────────────────────
    ra = PB.pour_tout(lambda x: x < 50, lambda rng: rng.randint(0, 100), n=500, graine=1)
    check("DÉTERMINISTE : même graine -> même contre-exemple", ra["contre_exemple"] == r["contre_exemple"])

    # ── FAUX=0 transverse : tout refute=True fournit un contre-exemple qui viole réellement ───
    tous_ok = True
    for res, prop in ((r, lambda x: x < 50), (r3, lambda xs: sum(xs) < 5)):
        if res["refute"] and PB._sur(prop, res["contre_exemple"]):
            tous_ok = False                          # un "réfuté" dont le contre-exemple ne viole pas = FAUX
    check("FAUX=0 : aucun contre-exemple rapporté ne satisfait la propriété", tous_ok)

    # ── CÂBLAGE ia.py ─────────────────────────────────────────────────────────────────────────
    import ia
    ri = ia.falsifie(lambda x: x < 50, lambda rng: rng.randint(0, 100), n=500, graine=1)
    check("CÂBLAGE ia.falsifie : réfute et minimise à 50", ri["refute"] and ri["contre_exemple"] == 50)

    print(f"\n=== valide_property_based : {ok}/{ok + len(fails)} ===")
    if fails:
        print("ÉCHECS :", ", ".join(fails))
    return 0 if not fails else 1


if __name__ == "__main__":
    sys.exit(main())
