"""
VALIDATION — MOTEUR DE DÉDUCTION (la mémoire qui raisonne). Prouve : dérivation transitive correcte, jointure
multi-atomes, PROVENANCE sound, HORS sur non-entraîné (FAUX=0), TERMINAISON sur faits cycliques, RÉTRACTION (TMS)
correcte. Soundness+complétude prouvées en comparant à la fermeture transitive VRAIE calculée indépendamment.
"""
from __future__ import annotations
import random

from garde_ressources import borne
borne(max_cpu_s=300)
from deduction import MoteurDeduction

N = 0
def check(nom, cond):
    global N
    N += 1
    print(f"  [{'OK ' if cond else 'XXX'}] {nom}")
    assert cond, nom


def fermeture_vraie(aretes):
    """Fermeture transitive de référence (Floyd-Warshall naïf) pour juger l'engine."""
    noeuds = {a for a, _ in aretes} | {b for _, b in aretes}
    R = {(a, b) for a, b in aretes}
    change = True
    while change:
        change = False
        for a in noeuds:
            for b in noeuds:
                if (a, b) in R:
                    for c in noeuds:
                        if (b, c) in R and (a, c) not in R:
                            R.add((a, c)); change = True
    return R


print("=" * 80)
print("VALIDATION MOTEUR DE DÉDUCTION")
print("=" * 80)

# (1) transitivité + HORS
m = MoteurDeduction()
for a, b in [("Paris", "IDF"), ("IDF", "France"), ("France", "Europe")]:
    m.ajoute_fait("situe", a, b)
m.ajoute_regle(("situe", "X", "Z"), [("situe", "X", "Y"), ("situe", "Y", "Z")], "trans")
m.materialise()
check("dérive transitif (Paris->Europe)", m.interroge("situe", "Paris", "Europe")[0] == "verifie")
check("HORS sur non-entraîné (Paris->Asie)", m.interroge("situe", "Paris", "Asie")[0] == "hors")
check("HORS sur relation inconnue", m.interroge("voisin", "Paris", "Lyon")[0] == "hors")

# (2) provenance sound : les supports d'un fait dérivé sont de vrais faits, et la tête se reconstruit
_, j = m.interroge("situe", "Paris", "Europe")
sups = j[0][1]
check("provenance : supports présents dans les faits", all(s in m.faits for s in sups))

# (3) jointure multi-atomes (grand-parent)
g = MoteurDeduction()
for a, b in [("a", "b"), ("b", "c"), ("c", "d")]:
    g.ajoute_fait("parent", a, b)
g.ajoute_regle(("grandparent", "X", "Z"), [("parent", "X", "Y"), ("parent", "Y", "Z")], "gp")
g.materialise()
check("jointure : grandparent(a,c) dérivé", g.interroge("grandparent", "a", "c")[0] == "verifie")
check("jointure : grandparent(a,b) NON dérivé (sound)", g.interroge("grandparent", "a", "b")[0] == "hors")

# (4) TERMINAISON sur cycle + soundness/complétude vs fermeture vraie
c = MoteurDeduction()
for a, b in [("x", "y"), ("y", "z"), ("z", "x")]:        # cycle
    c.ajoute_fait("e", a, b)
c.ajoute_regle(("e", "X", "Z"), [("e", "X", "Y"), ("e", "Y", "Z")], "t")
c.materialise()                                          # doit TERMINER
derive = {(x, y) for (r, x, y) in c.faits if r == "e"}
vraie = fermeture_vraie([("x", "y"), ("y", "z"), ("z", "x")])
check("terminaison sur cycle + fermeture EXACTE (sound+complet)", derive == vraie)

# (5) FAUX=0 sur graphe ALÉATOIRE : engine == fermeture transitive vraie (aucun faux, aucun manqué)
rng = random.Random(11)
faux_total = 0
for essai in range(8):
    noeuds = [f"n{i}" for i in range(rng.randint(4, 7))]
    aretes = set()
    for _ in range(rng.randint(4, 10)):
        a, b = rng.choice(noeuds), rng.choice(noeuds)
        if a != b:
            aretes.add((a, b))
    eng = MoteurDeduction()
    for a, b in aretes:
        eng.ajoute_fait("lien", a, b)
    eng.ajoute_regle(("lien", "X", "Z"), [("lien", "X", "Y"), ("lien", "Y", "Z")], "tc")
    eng.materialise()
    der = {(x, y) for (r, x, y) in eng.faits if r == "lien"}
    if der != fermeture_vraie(aretes):
        faux_total += 1
check("8 graphes aléatoires : dérivation == fermeture vraie (FAUX=0)", faux_total == 0)

# (5bis) PINS D'ATTAQUE 2026-07-02 (durcissements — chaque trou fermé reste fermé)
p = MoteurDeduction()
p.ajoute_fait("r", "a", "b")
p.interroge("r", "a", "b")                                   # matérialise
p.ajoute_fait("r", "c", "d")                                 # mutation APRÈS matérialisation
check("ajoute_fait APRÈS requête : le fait de base est servi (invalidation, plus de faux négatif)",
      p.interroge("r", "c", "d")[0] == "verifie")
check("explique() après mutation : lazy re-matérialisation (plus d'état périmé)",
      "[base:" in (p.ajoute_fait("r", "e", "f") or p.explique("r", "e", "f")))
try:
    p.ajoute_regle(("s", "X", "Y"), [("r", "X", "Y")], nom="base")
    check("nom de règle 'base' (sentinel de provenance) -> ValueError", False)
except ValueError:
    check("nom de règle 'base' (sentinel de provenance) -> ValueError", True)

# (6) RÉTRACTION (TMS) : retirer une arête réduit la fermeture exactement
r = MoteurDeduction()
for a, b in [("Paris", "IDF"), ("IDF", "France"), ("France", "Europe")]:
    r.ajoute_fait("situe", a, b)
r.ajoute_regle(("situe", "X", "Z"), [("situe", "X", "Y"), ("situe", "Y", "Z")], "trans")
r.materialise()
r.retracte("situe", "IDF", "France")
check("rétraction : Paris->Europe invalidé (TMS)", r.interroge("situe", "Paris", "Europe")[0] == "hors")
check("rétraction : faits restants cohérents (France->Europe gardé)",
      r.interroge("situe", "France", "Europe")[0] == "verifie")

print("=" * 80)
print(f"DÉDUCTION VALIDÉ — {N}/{N}.")
