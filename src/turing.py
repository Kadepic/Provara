"""MACHINES DE TURING — simulation DÉTERMINISTE bornée, FAUX=0 (mission formule/concept 2026-06-29).

Une MT = (δ, état initial, états acceptants, symbole blanc). δ : (état, symbole) -> (état, symbole_écrit, sens∈{L,R}).
On simule pas-à-pas, ruban infini (dict position->symbole). Arrêt : état acceptant -> 'accepte' ; pas de transition
-> 'bloque' (rejette) ; dépassement du budget -> 'timeout' (HONNÊTE : on n'invente pas le verdict d'un calcul non
terminé — le problème de l'arrêt est indécidable, donc le budget est explicite). Déterministe, EXACT.

Couvre le sujet borné « Machines de Turing ».
Vérifié en adverse par `valide_turing.py` (MT incrément binaire : succ("111")="1000", etc.).
"""
from __future__ import annotations


def execute(mt: dict, entree: str, max_etapes: int = 10000):
    """Simule la MT sur `entree`. Renvoie (statut, ruban, etapes) avec statut ∈ {'accepte','bloque','timeout'}.
    `ruban` = contenu non-blanc final (rogné). ValueError si MT mal formée ou max_etapes ≤ 0."""
    for cle in ("transitions", "initial", "acceptants", "blanc"):
        if cle not in mt:
            raise ValueError(f"MT : clé manquante {cle!r}")
    if not isinstance(max_etapes, int) or isinstance(max_etapes, bool) or max_etapes <= 0:
        raise ValueError("max_etapes entier > 0 requis")
    blanc = mt["blanc"]
    delta = mt["transitions"]
    acceptants = set(mt["acceptants"])
    ruban = {i: c for i, c in enumerate(entree)}
    tete, etat, etapes = 0, mt["initial"], 0
    while etapes < max_etapes:
        if etat in acceptants:
            return ("accepte", _rogne(ruban, blanc), etapes)
        sym = ruban.get(tete, blanc)
        regle = delta.get((etat, sym))
        if regle is None:
            return ("bloque", _rogne(ruban, blanc), etapes)
        nouvel_etat, ecrit, sens = regle
        if sens not in ("L", "R"):
            raise ValueError(f"sens invalide : {sens!r}")
        ruban[tete] = ecrit
        tete += 1 if sens == "R" else -1
        etat = nouvel_etat
        etapes += 1
    if etat in acceptants:
        return ("accepte", _rogne(ruban, blanc), etapes)
    return ("timeout", _rogne(ruban, blanc), etapes)


def _rogne(ruban: dict, blanc: str) -> str:
    """Contenu non-blanc du ruban, des positions min à max occupées (chaîne ; '' si tout blanc)."""
    occupes = [i for i, c in ruban.items() if c != blanc]
    if not occupes:
        return ""
    lo, hi = min(occupes), max(occupes)
    return "".join(ruban.get(i, blanc) for i in range(lo, hi + 1))


if __name__ == "__main__":
    # MT incrément binaire : va à droite, puis propage la retenue vers la gauche.
    B = "_"
    mt = {
        "blanc": B, "initial": "droite", "acceptants": {"fini"},
        "transitions": {
            ("droite", "0"): ("droite", "0", "R"),
            ("droite", "1"): ("droite", "1", "R"),
            ("droite", B):   ("retenue", B, "L"),
            ("retenue", "0"): ("fini", "1", "L"),
            ("retenue", "1"): ("retenue", "0", "L"),
            ("retenue", B):   ("fini", "1", "L"),
        },
    }
    for x in ["0", "1", "101", "111", "1011"]:
        st, ruban, n = execute(mt, x, 1000)
        print(f"  succ({x}) -> {ruban!r}  [{st}, {n} étapes]")
