#!/usr/bin/env python3
"""
VALIDATION de localisation_faute.py — localisation spectrum-based (Ochiai) + réparation par recherche. FAUX=0 :
suspicion = mesure (candidat, jamais « le bug » certain) ; réparation acceptée seulement si `teste` (held-out inclus)
passe. Léger (stdlib pur, pas de lecteur).
"""
from __future__ import annotations

import sys

import localisation_faute as L


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

    # ── Spectrum-based : la ligne exécutée UNIQUEMENT par les tests qui échouent est la plus suspecte ──
    # 4 tests ; l'élément 'L3' n'est couvert que par les tests échoués -> suspicion maximale.
    couverture = {
        "t1": {"L1", "L2"},            # passe
        "t2": {"L1", "L3"},            # échoue (couvre L3)
        "t3": {"L1", "L2", "L3"},      # échoue (couvre L3)
        "t4": {"L1", "L2"},            # passe
    }
    verdicts = {"t1": True, "t2": False, "t3": False, "t4": True}
    scores = L.localise(couverture, verdicts)
    top = scores[0]
    check("LOCALISATION : L3 (exécuté seulement par les tests échoués) est le plus suspect", top[0] == "L3")
    check("LOCALISATION : L3 suspicion maximale (=1.0, exclusif aux échecs)", abs(top[1] - 1.0) < 1e-9)
    check("LOCALISATION : L1 (couvre tout) moins suspect que L3",
          dict(scores)["L1"] < dict(scores)["L3"])
    check("element_le_plus_suspect = L3", L.element_le_plus_suspect(couverture, verdicts) == "L3")
    # FAUX=0 : aucun test n'échoue -> aucun suspect (pas d'accusation gratuite)
    check("FAUX=0 : aucun échec -> element_le_plus_suspect None",
          L.element_le_plus_suspect(couverture, {"t1": True, "t2": True, "t3": True, "t4": True}) is None)

    # ── Réparation par recherche : garde le patch qui passe TOUT (held-out inclus) ────────────
    # cible : une fonction qui double ; patches candidats, seul le bon passe le held-out.
    visibles = [(2, 4), (3, 6)]
    held = [(5, 10), (0, 0), (-1, -2)]

    def teste(patch):                              # patch = une fonction candidate ; DOIT passer visible + held-out
        return all(patch(x) == y for x, y in visibles) and all(patch(x) == y for x, y in held)

    candidats = [lambda x: x + 2,                  # passe (2,4),(3,6) visibles mais ÉCHOUE le held-out (5->7≠10)
                 lambda x: x * 2,                  # LE BON : passe tout
                 lambda x: x ** 2]                 # échoue
    r = L.repare(candidats, teste)
    check("RÉPARATION : trouve le patch qui passe visible + held-out (x*2)",
          r["trouve"] and r["repare"](5) == 10 and r["repare"](-1) == -2)
    check("RÉPARATION FAUX=0 : le patch x+2 (sur-apprend le visible) n'est PAS retenu",
          r["repare"](5) == 10)                    # x+2 donnerait 7 ; on a bien x*2

    # aucun patch ne répare -> None honnête
    r2 = L.repare([lambda x: x + 1, lambda x: x - 1], teste)
    check("RÉPARATION : aucun patch valide -> None (honnête)", not r2["trouve"] and r2["repare"] is None)

    # ── Couverture Python automatique (bonus, sys.settrace) ───────────────────────────────────
    def f(x):
        if x > 0:
            return "positif"        # ligne A
        return "negatif"            # ligne B
    cov = L.couverture_python(f, [5, -3])
    check("COUVERTURE : entrées différentes exécutent des lignes différentes",
          cov[repr(5)] != cov[repr(-3)])

    # ── CÂBLAGE ia.py ─────────────────────────────────────────────────────────────────────────
    import ia
    check("CÂBLAGE ia.localise_faute : L3 en tête", ia.localise_faute(couverture, verdicts)[0][0] == "L3")
    check("CÂBLAGE ia.repare_par_recherche : trouve x*2",
          ia.repare_par_recherche(candidats, teste)["repare"](5) == 10)

    print(f"\n=== valide_localisation_faute : {ok}/{ok + len(fails)} ===")
    if fails:
        print("ÉCHECS :", ", ".join(fails))
    return 0 if not fails else 1


if __name__ == "__main__":
    sys.exit(main())
