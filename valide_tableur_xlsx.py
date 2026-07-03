"""VALIDE tableur_xlsx.py — round-trip des valeurs (oracle unzip+XML) + refs A1 exactes + FAUX=0.

Oracle : ce qu'`encode` écrit, `decode` le relit ; on EXIGE l'égalité des valeurs ET la préservation du typage
(str reste str, nombre reste nombre). Contrôles négatifs : valeur non scalaire, feuille invalide, zip corrompu.
"""
import tableur_xlsx as X

ok = 0
ko = 0


def check(cond, label):
    global ok, ko
    if cond:
        ok += 1
    else:
        ko += 1
        print(f"  FAIL: {label}")


def leve(fn, *a, **k):
    try:
        fn(*a, **k)
        return False
    except ValueError:
        return True
    except Exception:
        return False


# ── 1) Références A1 (oracle re-dérivé) ──
check(X.colonne_vers_lettre(0) == "A" and X.colonne_vers_lettre(25) == "Z", "colonne 0->A, 25->Z")
check(X.colonne_vers_lettre(26) == "AA" and X.colonne_vers_lettre(701) == "ZZ", "colonne 26->AA, 701->ZZ")
check(X.colonne_vers_lettre(702) == "AAA", "colonne 702->AAA")
check(all(X.lettre_vers_colonne(X.colonne_vers_lettre(i)) == i for i in range(0, 1000, 7)), "bijection lettre<->colonne")

# ── 2) Round-trip valeurs + typage ──
cl = X.Classeur()
f = cl.feuille("Données")
f.set(0, 0, "Nom")
f.set(0, 1, "Score")
f.set(1, 0, "Alice")
f.set(1, 1, 42)
f.set(2, 0, "Bob")
f.set(2, 1, 3.5)
octets = X.encode(cl)
d = X.decode(octets)
check(d["noms"] == ["Données"], "nom de feuille round-trip")
g = d["feuilles"]["Données"]
check(g[(0, 0)] == "Nom" and g[(1, 0)] == "Alice", "texte round-trip")
check(g[(1, 1)] == 42 and isinstance(g[(1, 1)], int), "entier round-trip + typé int")
check(g[(2, 1)] == 3.5 and isinstance(g[(2, 1)], float), "float round-trip + typé float")

# ── 3) Caractères spéciaux XML échappés ──
cl2 = X.Classeur()
f2 = cl2.feuille("Sp")
f2.set(0, 0, 'a & b < c > d " e \' f')
g2 = X.decode(X.encode(cl2))["feuilles"]["Sp"]
check(g2[(0, 0)] == 'a & b < c > d " e \' f', "échappement XML round-trip (&<>\"')")

# ── 4) Plusieurs feuilles, ordre préservé ──
cl3 = X.Classeur()
cl3.feuille("Un").set(0, 0, 1)
cl3.feuille("Deux").set(0, 0, 2)
cl3.feuille("Trois").set(0, 0, 3)
d3 = X.decode(X.encode(cl3))
check(d3["noms"] == ["Un", "Deux", "Trois"], "3 feuilles, ordre préservé")
check(d3["feuilles"]["Deux"][(0, 0)] == 2, "valeur dans la 2e feuille")

# ── 5) ligne_depuis + cellule effacée (None) ──
cl4 = X.Classeur()
f4 = cl4.feuille("L")
f4.ligne_depuis(0, ["x", 10, 2.5])
f4.set(0, 1, None)                       # efface la cellule
g4 = X.decode(X.encode(cl4))["feuilles"]["L"]
check(g4.get((0, 0)) == "x" and (0, 1) not in g4 and g4.get((0, 2)) == 2.5, "ligne_depuis + effacement None")

# ── 6) Déterminisme ──
check(X.encode(cl) == X.encode(cl), "déterminisme : même classeur -> mêmes octets")

# ── 7) FAUX=0 ──
check(leve(X.Feuille("a").set, 0, 0, [1, 2]), "valeur liste -> ValueError")
check(leve(X.Feuille("a").set, 0, 0, True), "valeur booléenne -> ValueError")
check(leve(X.Feuille("a").set, 0, 0, float("inf")), "valeur infinie -> ValueError")
check(leve(X.Feuille("a").set, -1, 0, 1), "ligne négative -> ValueError")
check(leve(X.Classeur().feuille, "a:b"), "nom de feuille invalide -> ValueError")
check(leve(X.Feuille, ""), "nom de feuille vide -> ValueError")
check(leve(X.colonne_vers_lettre, -1), "colonne négative -> ValueError")
check(leve(X.encode, X.Classeur()), "classeur vide -> ValueError")
check(leve(X.decode, b"not a zip"), "octets non-zip -> ValueError")
cl5 = X.Classeur()
cl5.feuille("A")
try:
    cl5.feuille("A")
    check(False, "feuille dupliquée -> ValueError")
except ValueError:
    check(True, "feuille dupliquée -> ValueError")

print(f"\n=== valide_tableur_xlsx : {ok}/{ok + ko} ===")
import sys
sys.exit(0 if ko == 0 else 1)
