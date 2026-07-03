"""CARTE_LIMITES_FRANCAIS — la frontière du model-free est mesurée, pas affirmée.
REGLE : barreaux 1-6 (réglés) TOUS atteints. FRONTIÈRE : 7-9 (lexical/structurel) NON atteints mais COMBLABLES.
MUR DUR : 10 (SENS) non atteint ET non comblable. COHÉRENT : le verdict pointe la frontière au bon barreau."""
from __future__ import annotations

from carte_limites_francais import carte, verdict

CATS = {"REGLE", "LEXICAL", "STRUCTUREL", "SENS"}


def _check(nom, c):
    print(f"  [{'OK ' if c else 'RATÉ'}] {nom}")
    return c


def main() -> int:
    c = carte()
    par_n = {r["n"]: r for r in c}
    r = []

    r.append(_check("REGLE : les 6 barreaux réglés (1-6) sont TOUS atteints par le model-free assemblé",
                    all(par_n[n]["categorie"] == "REGLE" and par_n[n]["atteint"] for n in range(1, 7))))

    r.append(_check("FRONTIÈRE : 7 (3ᵉ groupe) et 8 (genre) = LEXICAL, NON atteints mais comblables par TABLE",
                    all(par_n[n]["categorie"] == "LEXICAL" and not par_n[n]["atteint"] and par_n[n]["comblable"]
                        for n in (7, 8))))

    r.append(_check("STRUCTUREL : 9 (accord GN) NON atteint mais comblable par une brique de composition",
                    par_n[9]["categorie"] == "STRUCTUREL" and not par_n[9]["atteint"] and par_n[9]["comblable"]))

    r.append(_check("MUR DUR : 10 (SENS) NON atteint ET NON comblable (aucun juge mécanique)",
                    par_n[10]["categorie"] == "SENS" and not par_n[10]["atteint"] and not par_n[10]["comblable"]))

    v = verdict(c)
    r.append(_check(f"COHÉRENT : plafond REGLE = barreau {v['plafond_regle']}, 1er mur = barreau {v['premier_mur']}, "
                    f"mur dur = {v['mur_dur']}",
                    v["plafond_regle"] == 6 and v["premier_mur"] == 7 and v["mur_dur"] == [10]
                    and all(r2["categorie"] in CATS for r2 in c)))

    print()
    print("CARTE DES LIMITES VALIDÉE — 5/5." if all(r) else f"ÉCHEC — {sum(r)}/5.")
    return 0 if all(r) else 1


if __name__ == "__main__":
    raise SystemExit(main())
