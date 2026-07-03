#!/usr/bin/env python3
"""
VALIDATION de la normalisation de VALEUR avant conflit (lecteur._norme_valeur, durcissement 2026-07-02).
FAUX=0 : deux graphies du MÊME fait (espace insécable, blancs multiples, bords) ne déclenchent plus un faux
conflit et ne coexistent pas comme deux valeurs ; deux valeurs RÉELLEMENT différentes (casse, accents, texte)
restent un conflit REFUSÉ. Léger : LECTEUR_AMORCE_SEULE=1 (aucun chargement de corpus). Les blancs exotiques
sont écrits en ÉCHAPPEMENTS \\uXXXX explicites — jamais de littéral invisible dans un test.
"""
from __future__ import annotations

import os
import sys

os.environ["LECTEUR_AMORCE_SEULE"] = "1"       # AVANT l'import : Lecteur léger, pas de datasets
import lecteur as L

NBSP, NNBSP, FINE = "\u00a0", "\u202f", "\u2009"


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

    # ── Unité _norme_valeur ────────────────────────────────────────────────────────────────────
    n = L._norme_valeur
    check("NBSP -> espace", n(f"Paris{NBSP}Ville") == "Paris Ville")
    check("fine insécable + tab + séquences -> un espace", n(f"a{NNBSP}\tb  c") == "a b c")
    check("espace fine (U+2009) -> espace", n(f"1{FINE}024") == "1 024")
    check("bords rognés", n("  Paris ") == "Paris")
    check("multiligne aplati", n("Paris\nVille") == "Paris Ville")
    propre = "Wolfgang Amadeus Mozart"
    check("valeur propre : renvoyée TELLE QUELLE (même objet, zéro allocation)", n(propre) is propre)
    check("casse/accents/ponctuation INTOUCHÉS", n("École, N°1 — ÉTÉ") == "École, N°1 — ÉTÉ")
    check("blancs seuls -> vide (garde-fou aval)", n(f" {NBSP} ") == "")

    # ── ingere_table : idempotence inter-graphies, conflits réels préservés ───────────────────
    lec = L.Lecteur()
    n1 = lec.ingere_table("t_norme", [("france", "Paris")], "convention", "src_a")
    check("ingestion initiale : 1 nouvelle entrée", n1 == 1)
    n2 = lec.ingere_table("t_norme", [("france", f"Paris{NBSP}"), ("france", "  Paris")], "convention", "src_a")
    check("MÊME fait en 3 graphies (NBSP, bords) -> idempotent, 0 conflit, 0 nouvelle", n2 == 0)
    try:
        lec.ingere_table("t_norme", [("france", "Lyon")], "convention", "src_a")
        check("conflit RÉEL (Paris vs Lyon) -> toujours refusé", False)
    except ValueError:
        check("conflit RÉEL (Paris vs Lyon) -> toujours refusé", True)
    try:
        lec.ingere_table("t_norme", [("france", "paris")], "convention", "src_a")
        check("casse différente = valeurs différentes -> conflit refusé (pas de sur-normalisation)", False)
    except ValueError:
        check("casse différente = valeurs différentes -> conflit refusé (pas de sur-normalisation)", True)
    n3 = lec.ingere_table("t_norme", [("espagne", f"  Madrid{NBSP}Centre  ")], "convention", "src_a")
    check("valeur STOCKÉE = forme normalisée", n3 == 1
          and lec.tables["t_norme"][lec._cle("t_norme", "espagne")].valeur == "Madrid Centre")
    check("valeur en blancs seuls -> ignorée (pas d'entrée vide)",
          lec.ingere_table("t_norme", [("italie", f" {NBSP} ")], "convention", "src_a") == 0)

    print(f"\n=== valide_lecteur_norme : {ok}/{ok + len(fails)} ===")
    if fails:
        print("ÉCHECS :", ", ".join(fails))
    return 0 if not fails else 1


if __name__ == "__main__":
    sys.exit(main())
