"""VALIDE bases_donnees.py — ADVERSE, FAUX=0. Algèbre relationnelle sur tables connues (sélection/projection/jointure/
union/différence/agrégats) + SOUNDNESS (colonne absente, opérateur inconnu, schémas incompatibles -> ValueError)."""
import bases_donnees as B

ok = 0
ko = 0


def check(c, l):
    global ok, ko
    if c:
        ok += 1
    else:
        ko += 1
        print(f"  FAIL: {l}")


def leve(fn, *a):
    try:
        fn(*a)
        return False
    except ValueError:
        return True
    except Exception:
        return False


T = [{"id": 1, "nom": "Alice", "dept": "R&D", "age": 30},
     {"id": 2, "nom": "Bob", "dept": "Vente", "age": 40},
     {"id": 3, "nom": "Carl", "dept": "R&D", "age": 50}]
S = [{"id": 1, "salaire": 50}, {"id": 2, "salaire": 40}, {"id": 3, "salaire": 60}]

# SÉLECTION
check([r["nom"] for r in B.selection(T, "dept", "==", "R&D")] == ["Alice", "Carl"], "σ dept=R&D")
check([r["nom"] for r in B.selection(T, "age", ">", 35)] == ["Bob", "Carl"], "σ age>35")
check(B.selection(T, "dept", "==", "Inexistant") == [], "σ vide")
check(len(B.selection(T, "age", "!=", 30)) == 2, "σ age≠30")

# PROJECTION (avec dédoublonnage)
check(B.projection(T, ["dept"]) == [{"dept": "R&D"}, {"dept": "Vente"}], "π dept (distinct)")
check(len(B.projection(T, ["nom", "age"])) == 3, "π nom,age")

# JOINTURE
j = B.jointure(T, S, "id")
check(len(j) == 3 and j[0]["nom"] == "Alice" and j[0]["salaire"] == 50, "⋈ sur id")
check(B.jointure(T, [{"id": 1, "x": 1}], "id")[0]["x"] == 1, "⋈ partielle")
check(B.jointure(T, [{"id": 99, "x": 1}], "id") == [], "⋈ sans correspondance -> vide")

# UNION / DIFFÉRENCE
a = [{"x": 1}, {"x": 2}]
b = [{"x": 2}, {"x": 3}]
check(len(B.union(a, b)) == 3, "union distincte = 3")
check(B.difference(a, b) == [{"x": 1}], "différence a−b = {1}")
check(B.union(a, a) == a, "union idempotente")

# AGRÉGATS
check(B.agregat(S, "salaire", "count") == 3, "count = 3")
check(B.agregat(S, "salaire", "sum") == 150, "sum = 150")
check(B.agregat(S, "salaire", "avg") == 50.0, "avg = 50")
check(B.agregat(S, "salaire", "min") == 40 and B.agregat(S, "salaire", "max") == 60, "min/max")
check(B.agregat(B.selection(T, "dept", "==", "R&D"), "id", "count") == 2, "count après sélection")

# SOUNDNESS
check(leve(B.selection, T, "inexistant", "==", 1), "colonne absente -> ValueError")
check(leve(B.selection, T, "age", "~~", 1), "opérateur inconnu -> ValueError")
check(leve(B.projection, T, ["inexistant"]), "projection colonne absente -> ValueError")
check(leve(B.jointure, T, S, "inexistant"), "jointure clé absente -> ValueError")
check(leve(B.union, [{"x": 1}], [{"y": 1}]), "union schémas incompatibles -> ValueError")
check(leve(B.agregat, S, "salaire", "median"), "agrégat inconnu -> ValueError")

# DÉTERMINISME
check(B.jointure(T, S, "id") == B.jointure(T, S, "id"), "déterminisme")

print(f"\n=== valide_bases_donnees : {ok}/{ok + ko} ===")
import sys
sys.exit(0 if ko == 0 else 1)
