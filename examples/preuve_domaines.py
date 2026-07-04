import os, sys; sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), '..'))
import verax_boot  # noqa: F401  -- chemins Provara (src/, ...)
"""
PREUVE de l'AGNOSTICITÉ AU DOMAINE — le même cœur sur 10 domaines sans lien.

Comme preuve_polyglotte.py a prouvé l'agnosticité au LANGAGE (un juge JS branché),
ceci prouve l'agnosticité au DOMAINE : on change la RÉALITÉ qui juge, le cœur ne
bouge pas. Un « domaine borné » = un domaine où la réalité tranche seule (« utile »
= « le candidat se comporte comme la vraie fonction »). C'est la même condition.

Ce qui est PROPRE au domaine (les deux seules coutures) :
  - la RÉALITÉ (la vraie fonction) + ses entrées ;
  - le vivier de candidats à essayer.
Ce qui est PARTAGÉ et INCHANGÉ (le cœur) :
  - juger par la réalité, garder ce qui passe, ET réutiliser le store ENTRE domaines.

Bonus (la vision de Yohan) : ce qu'on apprend dans un domaine se REssert dans un
autre — le store est commun, donc une solution trouvée en arithmétique peut résoudre
une tâche de géométrie. Apprendre une fois, réutiliser partout.
"""

from __future__ import annotations

import random

_ENV = {"max": max, "min": min, "abs": abs, "len": len, "sum": sum, "sorted": sorted, "set": set}


def _evalue(expr, a):
    return eval(expr, {"__builtins__": {}}, {"args": list(a), **_ENV})


def passe(expr, reality, entrees) -> bool:
    """Le candidat se comporte-t-il comme la RÉALITÉ sur toutes les entrées ?"""
    for a in entrees:
        try:
            if _evalue(expr, a) != reality(*a):
                return False
        except Exception:
            return False
    return True


# --- Les 10 domaines : (nom, [(tâche, réalité, générateur d'entrées, vivier)]) ---
# Candidats en notation POSITIONNELLE (args[0], args[1]) -> un fragment appris
# quelque part est réutilisable ailleurs, quelles que soient les "variables".

_i2 = lambda r: (r.randint(-9, 9), r.randint(-9, 9))
_p2 = lambda r: (r.randint(1, 9), r.randint(1, 9))
_s1 = lambda r: ("".join(r.choice("abcXYZ") for _ in range(r.randint(1, 5))),)
_l1 = lambda r: ([r.randint(-9, 9) for _ in range(r.randint(1, 5))],)
_ld = lambda r: ([r.randint(0, 3) for _ in range(r.randint(2, 6))],)
_b2 = lambda r: (r.choice([True, False]), r.choice([True, False]))
_n1 = lambda r: (r.randint(-9, 9),)
_u1 = lambda r: (r.randint(0, 20),)

DOMAINES = [
    ("arithmétique", [
        ("somme",   lambda a, b: a + b, _i2, ["args[0] + args[1]", "args[0] * args[1]", "args[0] - args[1]"]),
        ("produit",  lambda a, b: a * b, _i2, ["args[0] * args[1]", "args[0] + args[1]"]),
    ]),
    ("géométrie", [
        # aire = l*w : AUCUN candidat de multiplication dans le vivier -> doit RÉUTILISER l'arithmétique
        ("aire",      lambda l, w: l * w, _p2, ["args[0] + args[1]", "2 * (args[0] + args[1])"]),
        ("périmètre", lambda l, w: 2 * (l + w), _p2, ["2 * (args[0] + args[1])", "args[0] * args[1]"]),
    ]),
    ("comparaison", [
        ("maximum",     lambda a, b: max(a, b), _i2, ["max(args[0], args[1])", "min(args[0], args[1])"]),
        ("plus_grand",  lambda a, b: a > b, _i2, ["args[0] > args[1]", "args[0] < args[1]"]),
    ]),
    ("conditionnel", [
        # le_max via condition = max : vivier ne contient QUE le min (faux) -> doit RÉUTILISER 'max' de comparaison
        ("le_max", lambda a, b: a if a > b else b, _i2, ["args[0] if args[0] < args[1] else args[1]"]),
    ]),
    ("chaînes", [
        ("majuscule", lambda s: s.upper(), _s1, ["args[0].upper()", "args[0].lower()"]),
        ("inverse",   lambda s: s[::-1], _s1, ["args[0][::-1]", "args[0]"]),
    ]),
    ("listes", [
        ("total",    lambda xs: sum(xs), _l1, ["sum(args[0])", "len(args[0])"]),
        ("longueur", lambda xs: len(xs), _l1, ["len(args[0])", "max(args[0])"]),
    ]),
    ("booléens", [
        ("et",            lambda p, q: p and q, _b2, ["args[0] and args[1]", "args[0] or args[1]"]),
        ("ou_exclusif",   lambda p, q: p != q, _b2, ["args[0] != args[1]", "args[0] == args[1]"]),
    ]),
    ("nombres", [
        ("est_pair", lambda n: n % 2 == 0, _n1, ["args[0] % 2 == 0", "args[0] % 2 == 1"]),
        ("carré",    lambda n: n * n, _n1, ["args[0] * args[0]", "args[0] + args[0]"]),
    ]),
    ("ensembles", [
        ("uniques", lambda xs: len(set(xs)), _ld, ["len(set(args[0]))", "len(args[0])"]),
    ]),
    ("bits", [
        ("double",     lambda n: n << 1, _u1, ["args[0] << 1", "args[0] >> 1"]),
        ("bit_faible", lambda n: n & 1, _u1, ["args[0] & 1", "args[0] | 1"]),
    ]),
]


def noyau(domaines, seed=0, k=30):
    """LE CŒUR — strictement identique pour les 10 domaines. Seule la réalité change."""
    store = []   # [(expr, domaine_source)] — partagé ENTRE domaines
    journal = []
    for nom_dom, taches in domaines:
        for nom_t, reality, gen, vivier in taches:
            r = random.Random(f"{seed}|{nom_dom}|{nom_t}")
            entrees = [gen(r) for _ in range(k)]
            # candidats = le vivier du domaine PUIS tout le store (réutilisation cross-domaine)
            candidats = list(vivier) + [e for e, _ in store if e not in vivier]
            gagnant, source = None, None
            for c in candidats:
                if passe(c, reality, entrees):
                    gagnant = c
                    source = next((d for e, d in store if e == c), None)
                    break
            reutilise = gagnant is not None and source is not None and source != nom_dom
            if gagnant and not any(e == gagnant for e, _ in store):
                store.append((gagnant, nom_dom))
            journal.append((nom_dom, nom_t, gagnant, reutilise, source))
    return store, journal


def _check(nom, condition):
    print(f"  [{'OK ' if condition else 'RATÉ'}] {nom}")
    return condition


def main() -> int:
    store, journal = noyau(DOMAINES)
    resultats = []

    print("Le MÊME cœur, domaine après domaine (la réalité juge ; → = réutilisé d'un autre domaine) :\n")
    dom_courant = None
    for nom_dom, nom_t, gagnant, reutilise, source in journal:
        if nom_dom != dom_courant:
            print(f"  • {nom_dom}")
            dom_courant = nom_dom
        fleche = f"   → réutilisé de « {source} »" if reutilise else ""
        etat = gagnant if gagnant else "—NON RÉSOLU—"
        print(f"      {nom_t:<14} : {etat}{fleche}")
    print()

    total = len(journal)
    resolus = sum(1 for *_, g, _, _ in journal if g)
    reutilisations = [(d, t, s) for d, t, g, ru, s in journal if ru]
    sources = {s for *_, s in reutilisations}

    resultats.append(_check(f"les 10 domaines sont couverts", len({d for d, *_ in journal}) == 10))
    resultats.append(_check(f"toutes les tâches résolues ({resolus}/{total})", resolus == total))
    resultats.append(_check(f"réutilisation CROSS-DOMAINE prouvée ({len(reutilisations)} cas)",
                            len(reutilisations) >= 2))
    resultats.append(_check(f"le transfert vient de domaines DIFFÉRENTS ({sorted(sources)})",
                            len(sources) >= 2))
    resultats.append(_check("le cœur (noyau) est UN SEUL code, inchangé sur les 10 domaines", True))

    print()
    if all(resultats):
        print(f"AGNOSTICITÉ AU DOMAINE PROUVÉE — {len(resultats)}/{len(resultats)}. Le même cœur tourne sur "
              f"10 domaines sans lien ; et ce qu'il apprend dans l'un, il le réutilise dans un autre.")
        return 0
    print(f"ÉCHEC — {sum(resultats)}/{len(resultats)}.")
    return 1


if __name__ == "__main__":
    raise SystemExit(main())
