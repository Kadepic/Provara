"""VALIDATION qualitatif.py (Vague 4). FAUX=0 : ambiguïté (+ et -) -> ? honnête ; propagation sur influences réelles."""
from __future__ import annotations
from qualitatif import ReseauInfluences, signe_produit, signe_somme, PLUS, MOINS, ZERO, IND

ok = 0; total = 0
def check(nom, cond):
    global ok, total; total += 1
    print(f"  [{'OK ' if cond else 'XXX'}] {nom}", flush=True)
    if cond: ok += 1
    else: raise AssertionError(nom)

# Algèbre des signes
check("produit + × - = -", signe_produit(PLUS, MOINS) == MOINS)
check("produit - × - = +", signe_produit(MOINS, MOINS) == PLUS)
check("produit 0 absorbe", signe_produit(ZERO, IND) == ZERO)
check("produit ? contamine (hors 0)", signe_produit(IND, PLUS) == IND)
check("somme + et + = +", signe_somme(PLUS, PLUS) == PLUS)
check("somme + et - = ? (AMBIGU, honnête)", signe_somme(PLUS, MOINS) == IND)
check("somme 0 neutre", signe_somme(ZERO, MOINS) == MOINS)

# Réseau : pression P --(-)-> volume V ; volume V --(+)-> travail W. Augmenter P.
R = ReseauInfluences()
R.influence("P", "V", MOINS)     # ↑P -> ↓V
R.influence("V", "W", PLUS)      # ↑V -> ↑W
check("↑P propage : effet sur V = - (baisse)", R.effet("P", PLUS, cible="V") == MOINS)
check("↑P propage sur W via V : (-)×(+) = - ", R.effet("P", PLUS, cible="W") == MOINS)

# Deux chemins de signes opposés -> ? honnête
R2 = ReseauInfluences()
R2.influence("X", "Y", PLUS)     # chemin direct +
R2.influence("X", "Z", PLUS)
R2.influence("Z", "Y", MOINS)    # chemin indirect X->Z->Y : (+)×(-) = -
check("deux chemins X->Y de signes opposés -> ? (indéterminé, pas deviné)", R2.effet("X", PLUS, cible="Y") == IND)

# Pas d'influence posée -> effet nul (0), aucune influence inventée
check("variable non influencée -> 0 (aucune influence inventée)", R.effet("P", PLUS, cible="inconnue") == ZERO)

# Cycle : terminaison (pas de boucle infinie)
Rc = ReseauInfluences()
Rc.influence("A", "B", PLUS); Rc.influence("B", "A", PLUS)
eff = Rc.effet("A", PLUS)
check("cycle A<->B : terminant (renvoie un dict fini)", isinstance(eff, dict) and "B" in eff)

print(f"\n=== valide_qualitatif : {ok}/{total} checks OK ===")
if ok != total: raise SystemExit(1)
