"""AUTOMATES FINIS (DFA) — simulation EXACTE, FAUX=0 (mission formule/concept 2026-06-29).

Un automate fini déterministe = (états, alphabet, δ, état initial, états acceptants). On simule l'exécution sur un
mot et on décide l'acceptation — EXACT, déterministe. Abstention STRUCTURELLE : automate mal formé (δ incomplète,
initial/acceptants hors états) ou symbole hors alphabet -> ValueError (jamais un verdict faux).

Couvre le sujet borné « Théorie des automates ».
Vérifié en adverse par `valide_automates.py` (langages connus : parité du nombre de 1, multiples de 3 en binaire…).
"""
from __future__ import annotations


def _valide(dfa):
    for cle in ("etats", "alphabet", "transitions", "initial", "acceptants"):
        if cle not in dfa:
            raise ValueError(f"DFA : clé manquante {cle!r}")
    etats, alpha, delta = set(dfa["etats"]), set(dfa["alphabet"]), dfa["transitions"]
    if dfa["initial"] not in etats:
        raise ValueError("état initial hors des états")
    if not set(dfa["acceptants"]) <= etats:
        raise ValueError("états acceptants hors des états")
    for e in etats:
        for s in alpha:
            if (e, s) not in delta:
                raise ValueError(f"δ incomplète : pas de transition ({e!r},{s!r})")
            if delta[(e, s)] not in etats:
                raise ValueError(f"δ({e!r},{s!r}) pointe hors des états")
    return etats, alpha, delta


def accepte(dfa: dict, mot) -> bool:
    """True ssi le DFA accepte `mot` (itérable de symboles). ValueError si DFA mal formé ou symbole hors alphabet."""
    _, alpha, delta = _valide(dfa)
    etat = dfa["initial"]
    for symbole in mot:
        if symbole not in alpha:
            raise ValueError(f"symbole hors alphabet : {symbole!r}")
        etat = delta[(etat, symbole)]
    return etat in set(dfa["acceptants"])


def etats_accessibles(dfa: dict) -> set:
    """Ensemble des états atteignables depuis l'état initial (BFS sur δ)."""
    _, alpha, delta = _valide(dfa)
    vus = {dfa["initial"]}
    pile = [dfa["initial"]]
    while pile:
        e = pile.pop()
        for s in alpha:
            f = delta[(e, s)]
            if f not in vus:
                vus.add(f)
                pile.append(f)
    return vus


if __name__ == "__main__":
    # Parité du nombre de 1 : accepte les mots avec un nombre PAIR de 1.
    parite = {
        "etats": {"pair", "impair"}, "alphabet": {"0", "1"},
        "transitions": {("pair", "0"): "pair", ("pair", "1"): "impair",
                        ("impair", "0"): "impair", ("impair", "1"): "pair"},
        "initial": "pair", "acceptants": {"pair"},
    }
    for m in ["", "0", "1", "11", "101", "111", "1010"]:
        print(f"  parité 1 « {m or 'ε'} » -> {accepte(parite, m)}")
