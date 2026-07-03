#!/usr/bin/env python3
"""
VALIDATION de routeur_langage.py — trie les langages présents+jugeables par besoin. FAUX=0 : ne propose qu'un
langage réellement présent ET doté d'un Executeur. Léger (which + registre, pas de lecteur).
"""
from __future__ import annotations

import sys

import environnement
import routeur_langage as R
from executeur import EXECUTEURS


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

    bd = R.backends_disponibles()
    dispo = set(environnement.disponibles())
    check("backends_disponibles ⊆ (présents ∩ Executeurs)",
          all(l in dispo and l in EXECUTEURS for l in bd))
    check("python fait partie des backends (toujours présent)", "python" in bd)

    # choisit ne rend qu'un langage présent + jugeable
    for besoin in ("perf", "web", "systeme", "texte", "general", "stats", "logique"):
        r = R.choisit(besoin)
        if r is not None:
            lang, exe = r
            check(f"choisit('{besoin}') -> '{lang}' présent+jugeable, Executeur cohérent",
                  lang in dispo and lang in EXECUTEURS and exe is EXECUTEURS[lang])

    # 'perf' : si un compilé natif est présent+jugeable, il doit être choisi (c/cpp/rust/go)
    rp = R.choisit("perf")
    if rp is not None:
        check("choisit('perf') -> un langage natif (c/cpp/rust/go)", rp[0] in ("c", "cpp", "rust", "go"))
    # 'web' : javascript si présent
    if "javascript" in dispo:
        rw = R.choisit("web")
        check("choisit('web') -> javascript", rw is not None and rw[0] == "javascript")

    # FAUX=0 : un besoin sans aucun langage présent+jugeable -> None (pas d'invention)
    check("FAUX=0 : besoin sans backend présent -> None",
          R.choisit("besoin_totalement_inexistant_xyz") is None)
    # executeur_pour : cohérent
    check("executeur_pour('python') = ExecuteurPython présent", R.executeur_pour("python") is EXECUTEURS["python"])
    check("FAUX=0 : executeur_pour d'un langage absent/sans backend -> None",
          R.executeur_pour("cobol") is None)

    # ── CÂBLAGE ia.py ─────────────────────────────────────────────────────────────────────────
    import ia
    ri = ia.choisit_langage("perf")
    check("CÂBLAGE ia.choisit_langage('perf') cohérent avec routeur_langage",
          ri == R.choisit("perf"))

    print(f"\n=== valide_routeur_langage : {ok}/{ok + len(fails)} ===")
    print(f"  → portfolio jugeable : {bd}")
    if fails:
        print("ÉCHECS :", ", ".join(fails))
    return 0 if not fails else 1


if __name__ == "__main__":
    sys.exit(main())
