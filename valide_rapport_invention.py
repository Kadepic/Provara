"""
VALIDATION du RAPPORT D'INVENTION UNIFIÉ (rapport_invention.py).
Vérifie la structure, le bon classement des cibles sur les 2 substrats, et la SOUNDNESS (aucune
invention listée n'est fausse : son code reproduit le held-out).
"""
from __future__ import annotations

from garde_ressources import borne
import rapport_invention as R
import moteur_invention as MI

borne()
ok = 0
total = 0


def check(nom, cond):
    global ok, total
    total += 1
    print(f"  [{'OK ' if cond else 'XXX'}] {nom}")
    if cond:
        ok += 1
    else:
        raise AssertionError(nom)


CORPUS = [
    ("somme_totale", "xs", [([1, 2, 3], 6), ([5], 5)], [([0, 4], 4), ([2, 2], 4)]),
    ("somme_carres", "xs", [([1, 2, 3], 14), ([2, 3], 13)], [([5], 25), ([0, 4], 16), ([1, 1], 2)]),
    ("max_carres", "xs", [([-3, 2], 9), ([1, 4], 16), ([-1, -5], 25)], [([0, 3], 9), ([2, -2], 4), ([-6, 1], 36)]),
    ("amp_faible", "x", [([3, 1, 5], 4), ([2, 2], 0)], [([0, 9, 4], 9)]),
    ("deep_reverse", "x", [([1, [2, 3], 4], [4, [3, 2], 1]), ([[1, 2], [3, 4]], [[4, 3], [2, 1]])],
     [([1, [2, [3, 4]]], [[[4, 3], 2], 1]), ([5, [6, 7], 8, 9], [9, 8, [7, 6], 5])]),  # NOUVELLE frontière (flatten_rec résolu via récursion auto-application)
]
PHYS = [("lumiere", "electricite"), ("pression", "lumiere"), ("chaleur", "radio"), ("son", "gravite")]
held = {nom: h for nom, _s, _e, h in CORPUS}

rap = R.rapport(CORPUS, PHYS)

check("structure complète", set(rap) == {"realisables", "a_preciser", "frontieres", "abstractions", "principes_manquants"})

rea = {(s, n) for s, n, _ in rap["realisables"]}
check("réalisable code : somme_carres + max_carres", {("code", "somme_carres"), ("code", "max_carres")} <= rea)
check("réalisable physique : pression→lumiere + chaleur→radio",
      {("physique", "pression→lumiere"), ("physique", "chaleur→radio")} <= rea)

check("à préciser : amp_faible", ("code", "amp_faible") in {(s, n) for s, n in rap["a_preciser"]})

fro = {(s, n) for s, n, _ in rap["frontieres"]}
check("frontière code : deep_reverse", ("code", "deep_reverse") in fro)
check("frontière physique : son→gravite", ("physique", "son→gravite") in fro)

check("abstraction « _e * _e » présente", any(t == "_e * _e" for t, _ in rap["abstractions"]))
check("principes manquants non vides + triés", rap["principes_manquants"]
      and all(rap["principes_manquants"][i][0] >= rap["principes_manquants"][i + 1][0]
              for i in range(len(rap["principes_manquants"]) - 1)))

# SOUNDNESS : chaque invention CODE listée a un code qui reproduit son held-out.
sound = all(MI._reproduit(MI._callable(code, "f"), held[nom])
            for substrat, nom, code in rap["realisables"] if substrat == "code")
check("INVARIANT : aucune invention code fausse dans le rapport", sound)

# le rendu texte ne plante pas et contient les sections.
t = R.texte(rap)
check("rendu texte contient les 3 sections", "RÉALISABLES" in t and "À PRÉCISER" in t and "FRONTIÈRES" in t)

print(f"\nRAPPORT_INVENTION VALIDÉ — {ok}/{total}." if ok == total else f"\nÉCHEC {ok}/{total}")
