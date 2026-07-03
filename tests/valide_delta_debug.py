#!/usr/bin/env python3
"""
VALIDATION de delta_debug.py — ddmin. FAUX=0 : le résultat déclenche TOUJOURS l'échec et est 1-minimal (retirer
tout élément fait disparaître l'échec). Déterministe. Léger (stdlib pur, pas de lecteur).
"""
from __future__ import annotations

import sys

import delta_debug as D


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

    # ── Cas canonique : l'échec survient ssi 3 ET 7 sont présents ─────────────────────────────
    def echoue_3_7(sous):
        return 3 in sous and 7 in sous

    r = D.ddmin(list(range(1, 9)), echoue_3_7)         # [1..8]
    check("ddmin : réduit [1..8] au minimal {3,7}", sorted(r) == [3, 7])
    check("FAUX=0 : le résultat déclenche encore l'échec", echoue_3_7(r))
    check("1-minimal : retirer 3 ou 7 fait disparaître l'échec", D.est_1_minimal(r, echoue_3_7))

    # ── Un seul élément fautif ────────────────────────────────────────────────────────────────
    def echoue_5(sous):
        return 5 in sous
    r2 = D.ddmin(list(range(1, 100)), echoue_5)
    check("ddmin : réduit [1..99] à [5]", r2 == [5] and D.est_1_minimal(r2, echoue_5))

    # ── L'entrée n'échoue pas -> renvoyée inchangée (honnête) ─────────────────────────────────
    def jamais(sous):
        return False
    check("entrée qui n'échoue pas -> renvoyée inchangée", D.ddmin([1, 2, 3], jamais) == [1, 2, 3])

    # ── Échec = taille >= 3 (le minimal est n'importe quel triplet) ───────────────────────────
    def echoue_taille(sous):
        return len(sous) >= 3
    r3 = D.ddmin(list(range(20)), echoue_taille)
    check("ddmin : échec sur taille>=3 -> résultat de taille 3 qui échoue",
          len(r3) == 3 and echoue_taille(r3) and D.est_1_minimal(r3, echoue_taille))

    # ── Minimisation de TEXTE (par caractères) : garder ce qui contient 'bug' ─────────────────
    def contient_bug(s):
        return "bug" in s
    m = D.minimise_texte("il y a un gros bug caché ici", contient_bug)
    check("minimise_texte : réduit à 'bug'", m == "bug" and contient_bug(m))

    # ── Minimisation de TEXTE par lignes ──────────────────────────────────────────────────────
    src = "ligne ok 1\nligne FAUTIVE\nligne ok 2\nligne ok 3\n"
    def contient_fautive(s):
        return "FAUTIVE" in s
    ml = D.minimise_texte(src, contient_fautive, par_ligne=True)
    check("minimise_texte par ligne : garde la ligne fautive", "FAUTIVE" in ml and ml.count("\n") <= 1)

    # ── Déterminisme ──────────────────────────────────────────────────────────────────────────
    check("ddmin déterministe (même entrée -> même sortie)",
          D.ddmin(list(range(1, 9)), echoue_3_7) == r)

    # ── CÂBLAGE ia.py ─────────────────────────────────────────────────────────────────────────
    import ia
    check("CÂBLAGE ia.minimise_echec : réduit au minimal {3,7}",
          sorted(ia.minimise_echec(list(range(1, 9)), echoue_3_7)) == [3, 7])

    print(f"\n=== valide_delta_debug : {ok}/{ok + len(fails)} ===")
    if fails:
        print("ÉCHECS :", ", ".join(fails))
    return 0 if not fails else 1


if __name__ == "__main__":
    sys.exit(main())
