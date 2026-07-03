#!/usr/bin/env python3
"""
VALIDATION de fait_negatif.py — fait négatif trivalué au store. FAUX=0 : FAUX conclu SEULEMENT sur relation
fonctionnelle ; absence -> INCONNU ; multi-valuée -> INCONNU (jamais FAUX). Léger (stdlib pur, pas de lecteur).
"""
from __future__ import annotations

import sys

import fait_negatif as N


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

    # ── Relation FONCTIONNELLE (capitale) : une autre valeur est CERTAINEMENT fausse ──────────
    check("FONCTIONNELLE : capitale(France)=Paris -> Paris VRAI",
          N.statut_fait("Paris", "Paris", fonctionnelle=True) == N.VRAI)
    check("FONCTIONNELLE : capitale(France)=Berlin -> FAUX (une seule capitale possible)",
          N.statut_fait("Berlin", "Paris", fonctionnelle=True) == N.FAUX)

    # ── Relation NON fonctionnelle (langue_parlée) : une autre valeur reste INCONNU ───────────
    check("MULTI-VALUÉE : langue(France)=anglais -> INCONNU (peut coexister avec français)",
          N.statut_fait("anglais", "français", fonctionnelle=False) == N.INCONNU)
    check("MULTI-VALUÉE : la valeur connue reste VRAIE",
          N.statut_fait("français", "français", fonctionnelle=False) == N.VRAI)

    # ── FAUX=0 : absence de valeur connue -> INCONNU (monde ouvert, jamais FAUX) ───────────────
    check("MONDE OUVERT : valeur absente + fonctionnelle -> INCONNU (pas FAUX)",
          N.statut_fait("Paris", None, fonctionnelle=True) == N.INCONNU)
    check("MONDE OUVERT : valeur absente + non fonctionnelle -> INCONNU",
          N.statut_fait("x", None, fonctionnelle=False) == N.INCONNU)

    # ── negatifs_certains : uniquement pour relation fonctionnelle ────────────────────────────
    domaine = {"Paris", "Berlin", "Madrid", "Rome"}
    check("NÉGATIFS : fonctionnelle -> tous les autres du domaine sont faux",
          N.negatifs_certains("Paris", domaine, fonctionnelle=True) == {"Berlin", "Madrid", "Rome"})
    check("NÉGATIFS FAUX=0 : non fonctionnelle -> AUCUN négatif certain (monde ouvert)",
          N.negatifs_certains("français", domaine, fonctionnelle=False) == set())
    check("NÉGATIFS FAUX=0 : valeur connue absente -> aucun négatif certain",
          N.negatifs_certains(None, domaine, fonctionnelle=True) == set())

    # ── PRINCIPE FAUX=0 : le stockage mono-valeur ne SUFFIT pas à conclure FAUX ────────────────
    check("PRINCIPE : fonctionnalité explicite requise (stockage mono ≠ fonctionnel sémantique)",
          N.statut_fait("autre", "connue", fonctionnelle=False) == N.INCONNU)

    # ── CÂBLAGE ia.py ─────────────────────────────────────────────────────────────────────────
    import ia
    check("CÂBLAGE ia.statut_fait : fonctionnelle + différent -> FAUX",
          ia.statut_fait("Berlin", "Paris", fonctionnelle=True) == N.FAUX)
    check("CÂBLAGE ia.statut_fait : multi-valuée -> INCONNU",
          ia.statut_fait("anglais", "français", fonctionnelle=False) == N.INCONNU)

    print(f"\n=== valide_fait_negatif : {ok}/{ok + len(fails)} ===")
    if fails:
        print("ÉCHECS :", ", ".join(fails))
    return 0 if not fails else 1


if __name__ == "__main__":
    sys.exit(main())
