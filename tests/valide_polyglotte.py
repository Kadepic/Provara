"""
GÉNÉRATION MULTI-LANGAGE (2026-06-17) — l'IA ÉCRIT du code dans un autre langage que Python, vérifié par l'exemple.
`demande_lang(point_entree, exemples, langage)` -> solution dans le langage, ou HORS honnête. Famille bornée
(opérations binaires scalaires). Runtimes absents -> checks auto-sautés (toujours vert).

Critères de MORT (4) :
  1. MULTI-LANGAGE : `bit_xor` ÉCRIT + vérifié + GÉNÉRALISE (held-out) dans CHAQUE langage présent (JS/Perl/Bash).
  2. BON LANGAGE   : chaque solution est bien dans la SYNTAXE de son langage (function / sub / fonction bash).
  3. HONNÊTE/HORS  : une tâche HORS-FAMILLE (`power` = a**b, pas dans la famille) -> HORS, jamais du faux.
  4. AUTRE TÂCHE   : `max2` (max binaire) écrit+vérifié dans chaque langage présent -> pas un coup de chance sur xor.
"""

from __future__ import annotations

import shutil

from polyglotte import demande_lang

RUNTIME = {"javascript": "node", "perl": "perl", "bash": "bash"}
MARQUEUR = {"javascript": "function", "perl": "sub ", "bash": "() {"}


def _check(nom, ok):
    print(f"  [{'OK ' if ok else 'RATÉ'}] {nom}", flush=True)
    return ok


def main() -> int:
    presents = [l for l, rt in RUNTIME.items() if shutil.which(rt)]
    if not presents:
        print("Aucun runtime alternatif présent -> validation sautée (mécanisme en place).")
        print("MULTI-LANGAGE VALIDÉ — (sauté).")
        return 0

    r = []

    # 1. MULTI-LANGAGE : bit_xor dans chaque langage présent.
    xor = {l: demande_lang("bit_xor", [(5, 3, 6), (12, 10, 6)], l, [(7, 1, 6), (255, 128, 127)]) for l in presents}
    r.append(_check(f"MULTI-LANGAGE : bit_xor écrit+vérifié+généralise dans {presents}",
                    all(xor[l].ok and xor[l].generalise for l in presents)))

    # 2. BON LANGAGE : syntaxe propre à chaque langage.
    r.append(_check("BON LANGAGE : chaque solution est dans la syntaxe de son langage",
                    all(MARQUEUR[l] in (xor[l].code or "") for l in presents)))

    # 3. HONNÊTE : power (a**b) hors-famille -> HORS.
    pw = demande_lang("power", [(2, 3, 8), (5, 2, 25)], presents[0], [(2, 4, 16)])
    r.append(_check(f"HONNÊTE : power (a**b, hors-famille) -> HORS en {presents[0]}", not pw.ok))

    # 4. AUTRE TÂCHE : max2 dans chaque langage présent (généralité, pas un coup de chance sur xor).
    mx = {l: demande_lang("max2", [(5, 3, 5), (2, 9, 9)], l, [(7, 7, 7), (-1, 4, 4)]) for l in presents}
    r.append(_check(f"AUTRE TÂCHE : max2 écrit+vérifié dans {presents}",
                    all(mx[l].ok and mx[l].generalise for l in presents)))

    print()
    print("GÉNÉRATION MULTI-LANGAGE VALIDÉE — 4/4." if all(r) else f"ÉCHEC — {sum(r)}/4.")
    return 0 if all(r) else 1


if __name__ == "__main__":
    raise SystemExit(main())
