#!/usr/bin/env python3
"""
VALIDATION de refactor.py — refactor préservant le comportement. FAUX=0 : adopte SEULEMENT si équivalence PROUVÉE
sur domaine fini ; jamais sur échantillon ; différence -> rejet avec contre-exemple ; ne régresse jamais. Léger.
"""
from __future__ import annotations

import sys

import refactor as R
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

    def leve(fn):
        try:
            fn(); return False
        except ValueError:
            return True

    orig = lambda x: x * 2
    propre = lambda x: x + x                # équivalent, "plus propre"
    faux = lambda x: x * 3                  # NON équivalent

    # ── Domaine fini : équivalent -> ADOPTÉ (certain) ─────────────────────────────────────────
    d = R.adopte_refactor(orig, propre, domaine=range(-50, 51))
    check("PREUVE : refactor équivalent adopté (certain)", d["adopte"] and d["certain"] and d["statut"] == E.EQUIVALENTES)

    # ── Domaine fini : non équivalent -> REJET + contre-exemple ───────────────────────────────
    d2 = R.adopte_refactor(orig, faux, domaine=range(1, 20))
    check("PREUVE : refactor non équivalent REJETÉ", not d2["adopte"] and d2["statut"] == E.DIFFERENTES)
    check("REJET FAUX=0 : contre-exemple distingue (orig != faux)",
          orig(d2["contre_exemple"]) != faux(d2["contre_exemple"]))

    # ── Échantillon seul : équivalent -> JAMAIS adopté (pas de preuve), statut NON_DISTINGUEES ─
    d3 = R.adopte_refactor(orig, propre, generateur=lambda rng: rng.randint(-10 ** 6, 10 ** 6), n=500)
    check("ÉCHANTILLON FAUX=0 : jamais adopté sans preuve (adopte=False), NON_DISTINGUEES",
          not d3["adopte"] and d3["statut"] == E.NON_DISTINGUEES)

    # ── Échantillon : différent -> rejet détecté (certain=True car DIFFERENTES) ────────────────
    d4 = R.adopte_refactor(orig, faux, generateur=lambda rng: rng.randint(1, 1000), n=500)
    check("ÉCHANTILLON : différence détectée -> DIFFERENTES", not d4["adopte"] and d4["statut"] == E.DIFFERENTES)

    # ── meilleur_si_equivalent : adopte seulement si équivalent ET moins coûteux ──────────────
    cout = lambda f: len(str(f.__code__.co_code))    # proxy de coût déterministe
    # candidat équivalent mais on force un coût : ici on teste la LOGIQUE (équivalent + moins cher -> adopté)
    res = R.meilleur_si_equivalent(orig, propre, cout=lambda f: 10 if f is orig else 5, domaine=range(0, 10))
    check("MEILLEUR : équivalent + moins coûteux -> candidat choisi", res["choisi"] is propre and res["adopte"])
    res2 = R.meilleur_si_equivalent(orig, propre, cout=lambda f: 5 if f is orig else 10, domaine=range(0, 10))
    check("MEILLEUR : équivalent mais plus coûteux -> garde l'original", res2["choisi"] is orig and not res2["adopte"])
    res3 = R.meilleur_si_equivalent(orig, faux, cout=lambda f: 10 if f is orig else 1, domaine=range(1, 10))
    check("MEILLEUR FAUX=0 : non équivalent -> garde l'original même si « moins cher »",
          res3["choisi"] is orig and not res3["adopte"])

    check("FAUX=0 : ni domaine ni generateur -> ValueError", leve(lambda: R.adopte_refactor(orig, propre)))

    # ── CÂBLAGE ia.py ─────────────────────────────────────────────────────────────────────────
    import ia
    check("CÂBLAGE ia.refactor_sur : adopte un refactor prouvé équivalent",
          ia.refactor_sur(orig, propre, domaine=range(0, 10))["adopte"])

    print(f"\n=== valide_refactor : {ok}/{ok + len(fails)} ===")
    if fails:
        print("ÉCHECS :", ", ".join(fails))
    return 0 if not fails else 1


if __name__ == "__main__":
    sys.exit(main())
