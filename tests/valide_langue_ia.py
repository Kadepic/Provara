#!/usr/bin/env python3
"""
VALIDATION du câblage LANGUE de ia.py — `ia.conjugue` / `ia.ecris` / `ia.comprends` / `ia.comprends_texte`
(les moteurs langue existants, certifiés par leurs propres validateurs, cessent d'être orphelins). FAUX=0 :
conjugaison ABSTIENT hors périmètre garanti ; l'écrivain REFUSE une phrase incohérente plutôt que produire faux ;
le répondeur dit « je ne sais pas » hors portée ; la lecture-compréhension est trivaluée (oui/non/inconnu).
Léger (pas de lecteur ; UN mint d'Ecrivain paresseux ≈ secondes).
"""
from __future__ import annotations

import sys

import ia


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

    # ── ia.conjugue : formes garanties + ABSTENTION hors périmètre ────────────────────────────
    check("conjugue chanter p1/p4 + finir p4", ia.conjugue("chanter", 1) == "chante"
          and ia.conjugue("chanter", 4) == "chantons" and ia.conjugue("finir", 4) == "finissons")
    for verbe, personne in [("manger", 4), ("aller", 1), ("prendre", 2)]:
        try:
            ia.conjugue(verbe, personne)
            check(f"conjugue {verbe!r} p{personne} -> ABSTENTION (ValueError)", False)
        except ValueError:
            check(f"conjugue {verbe!r} p{personne} -> ABSTENTION (ValueError)", True)

    # ── ia.comprends : graine lexicale + faits, honnête hors portée ───────────────────────────
    import questions
    check("comprends contraire (graine, sans faits)", ia.comprends("quel est le contraire de chaud ?") == "froid")
    check("comprends SVO avec faits", ia.comprends("qui mange la souris ?", faits=questions.FAITS) == "chat")
    check("comprends HORS PORTÉE -> « je ne sais pas » (jamais inventé)",
          ia.comprends("quelle est la capitale de la France ?") == "je ne sais pas")

    # ── ia.comprends_texte : déduction trivaluée ──────────────────────────────────────────────
    import lecture_comprehension
    F = lecture_comprehension.FAITS
    check("comprends_texte transitif -> oui", ia.comprends_texte(F, "le chat est-il un animal ?") == "oui")
    check("comprends_texte non dérivable -> inconnu (monde ouvert)",
          ia.comprends_texte(F, "le chat est-il un oiseau ?") == "inconnu")
    check("comprends_texte fait négatif -> non", ia.comprends_texte(F, "le chat est-il un reptile ?") == "non")

    # ── ia.ecris : triple garantie, refus plutôt que faux (UN mint paresseux ici) ─────────────
    p1, c1, _ = ia.ecris("chat", "manger", "souris")
    check("ecris cohérente : « le chat mange la souris »", c1 and p1 == "le chat mange la souris")
    pv, cv, raison = ia.ecris("voiture", "manger", "souris")
    check("ecris INCOHÉRENTE (voiture ne mange pas) -> REFUS motivé", not cv and "incohérent" in raison)
    pq, cq, _ = ia.ecris("chat", "manger", "souris", question=True)
    check("ecris question -> interrogative cohérente", cq and pq.endswith("?"))
    pp, cp, _ = ia.ecris("chat", "manger", "souris", pluriel=True)
    check("ecris pluriel -> accord (« les chats mangent... »)", cp and pp.startswith("les chats mangent"))

    print(f"\n=== valide_langue_ia : {ok}/{ok + len(fails)} ===")
    if fails:
        print("ÉCHECS :", ", ".join(fails))
    return 0 if not fails else 1


if __name__ == "__main__":
    sys.exit(main())
