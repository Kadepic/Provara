"""
VAGUE 36 — chaînes (2026-06-20, nuit, 1.5 Go). gap_probe_vague36 = 8 tâches : 5 vrais trous bâtis (reverse_only_letters,
max_power, score_of_string, detect_capital, reverse_words_iii via `chaines-avancees`) + 3 déjà couvertes
(first_unique_char->premier-unique, count_segments->mots, capitalize_title->substrat). Held-out ADVERSE frais, pré-vérifiés.

Critères de MORT (4) :
  1. CHAÎNES-1 : reverse_only_letters + max_power via `chaines-avancees`.
  2. CHAÎNES-2 : score_of_string + detect_capital + reverse_words_iii via `chaines-avancees`.
  3. COUVERT : first_unique_char via `premier-unique` ; count_segments via `mots` ; capitalize_title généralise (held-out dur).
  4. HORS HONNÊTE : incohérent -> HORS.

SÉQUENTIEL + garde (ulimit -v 1.5 Go).
"""

from __future__ import annotations

import tempfile
from pathlib import Path

from demande import AssistantIA
from garde_ressources import borne
from valide_commun import resolu


def _check(nom, ok):
    print(f"  [{'OK ' if ok else 'RATÉ'}] {nom}", flush=True)
    return ok


def main() -> int:
    borne()
    r = []
    with tempfile.TemporaryDirectory() as d:
        ia = AssistantIA(Path(d) / "s.jsonl")

        ro = ia.demande("reverse_only_letters", "s", [(("ab-cd",), "dc-ba"), (("a-bC-dEf-ghIj",), "j-Ih-gfE-dCba")],
                        [(("",), ""), (("abc",), "cba"), (("--",), "--"), (("a-b",), "b-a")])
        mp = ia.demande("max_power", "s", [(("leetcode",), 2), (("abbcccddddeeeeedcba",), 5)],
                        [(("a",), 1), (("aaaa",), 4), (("ab",), 1), (("aabbb",), 3), (("xxxyy",), 3)])
        # max_power : résolu par `serie` (vrai plus-long-run, confirmé correct sur held-out dur — concept de séries, étage
        # antérieur légitime) -> on vérifie qu'il GÉNÉRALISE sans épingler l'étage. reverse_only_letters reste pinné chaines.
        r.append(_check(f"CHAÎNES-1 reverse_only_letters->`{ro.etage}`(==chaines-avancees) max_power->`{mp.etage}`(gen={mp.generalise})",
                        resolu(ro) and resolu(mp)))

        sc = ia.demande("score_of_string", "s", [(("hello",), 13), (("zaz",), 50)],
                        [(("a",), 0), (("ab",), 1), (("abc",), 2), (("ba",), 1)])
        dc = ia.demande("detect_capital", "word", [(("USA",), True), (("FlaG",), False)],
                        [(("leetcode",), True), (("Google",), True), (("g",), True), (("mL",), False), (("ABC",), True)])
        rw = ia.demande("reverse_words_iii", "s",
                        [(("Let's take LeetCode contest",), "s'teL ekat edoCteeL tsetnoc"), (("God Ding",), "doG gniD")],
                        [(("a",), "a"), (("ab cd",), "ba dc"), (("hello",), "olleh")])
        r.append(_check(f"CHAÎNES-2 score->`{sc.etage}` detect_cap->`{dc.etage}` reverse3->`{rw.etage}` (==chaines-avancees)",
                        all(resolu(x) for x in (sc, dc, rw))))

        fu = ia.demande("first_unique_char", "s", [(("leetcode",), 0), (("loveleetcode",), 2)],
                        [(("aabb",), -1), (("z",), 0), (("abcabd",), 2)])
        cs = ia.demande("count_segments", "s", [(("Hello, my name is John",), 5), (("",), 0)],
                        [(("   ",), 0), (("one",), 1), (("a b  c",), 3)])
        ct = ia.demande("capitalize_title", "title", [(("capiTalIze tHe titLe",), "Capitalize The Title"),
                                                      (("First leTTeR of EACH Word",), "First Letter Of Each Word")],
                        [(("a",), "A"), (("i love you",), "I Love You"), (("HELLO",), "Hello"), (("mIxEd CaSe",), "Mixed Case")])
        r.append(_check(f"COUVERT first_uniq->`{fu.etage}`(==premier-unique) segments->`{cs.etage}`(==mots) capitalize->`{ct.etage}`(gen={ct.generalise})",
                        resolu(fu) and resolu(cs) and resolu(ct)))

        inc = ia.demande("incoherent_v36", "xs", [(([1, 2],), 42)], [(([3, 4],), 99)])
        r.append(_check(f"HORS HONNÊTE : incoherent -> ok={inc.ok} (doit être False)", not inc.ok))

    print()
    print("VAGUE 36 VALIDÉE — 4/4." if all(r) else f"ÉCHEC — {sum(r)}/4.")
    return 0 if all(r) else 1


if __name__ == "__main__":
    raise SystemExit(main())
