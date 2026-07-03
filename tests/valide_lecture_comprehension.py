"""LECTURE & COMPRÉHENSION — l'IA lit des faits et répond par LOGIQUE (capstone du mandat compréhension).
DÉDUCTION : « X est-il un Z ? » transitif -> oui. HONNÊTE : non dérivable -> inconnu (jamais inventé). SVO : « qui
<verbe> Y ? » -> le bon sujet. INTÉGRÉ : la déduction passe par l'étage `inference` du moteur assemblé. HELD-OUT."""
from __future__ import annotations

from lecture_comprehension import FAITS, Lecteur


def _check(nom, c):
    print(f"  [{'OK ' if c else 'RATÉ'}] {nom}")
    return c


def main() -> int:
    lec = Lecteur(FAITS)
    r = []

    r.append(_check("DÉDUCTION : « le chat est-il un mammifère ? » -> oui (transitif, 2 sauts)",
                    lec.repond("le chat est-il un mammifère ?") == "oui"))
    r.append(_check("DÉDUCTION held-out : « le chat est-il un animal ? » -> oui (3 sauts, fait jamais direct)",
                    lec.repond("le chat est-il un animal ?") == "oui"))
    r.append(_check("HONNÊTE : « le chat est-il un oiseau ? » -> inconnu (non dérivable, pas d'invention)",
                    lec.repond("le chat est-il un oiseau ?") == "inconnu"))
    r.append(_check("NÉGATION/DISCOURS : « le félin n'est pas un reptile » -> « le chat est-il un reptile ? » -> non",
                    lec.repond("le chat est-il un reptile ?") == "non"))
    r.append(_check("SVO + négation : « qui mange la souris ? » -> chat (le fait NIÉ « le chien ne mange pas » n'y répond pas)",
                    lec.repond("qui mange la souris ?") == "chat"))
    r.append(_check(f"INTÉGRÉ : déduction + négation via l'étage assemblé `{lec._etage}` (= inference)",
                    lec._etage == "inference"))

    print()
    print(f"LECTURE & COMPRÉHENSION VALIDÉE — {sum(r)}/{len(r)}." if all(r) else f"ÉCHEC — {sum(r)}/{len(r)}.")
    return 0 if all(r) else 1


if __name__ == "__main__":
    raise SystemExit(main())
