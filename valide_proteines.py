"""
VALIDE proteines.py — held-out ADVERSE. Exactitude des FAITS établis (structure, classification EC) et du
calcul EXACT n−1 (références biochimie) + SOUNDNESS (abstention ValueError hors référentiel) + déterminisme.
"""
import proteines as P

ok = 0
ko = 0


def check(cond, label):
    global ok, ko
    if cond:
        ok += 1
    else:
        ko += 1
        print(f"  FAIL: {label}")


def leve_v(fn, *a, **k):
    """True ssi fn(*a, **k) lève ValueError (et rien d'autre)."""
    try:
        fn(*a, **k)
        return False
    except ValueError:
        return True
    except Exception:
        return False


# 1) CAS DEMANDÉS PAR LA SPÉC (ancres).
check(P.nombre_liaisons_peptidiques(100) == 99, "100 aa -> 99 liaisons peptidiques")
check(P.classe_enzyme_ec(3) == "hydrolase", "EC 3 = hydrolase")
check(P.nombre_niveaux_structure() == 4, "4 niveaux de structure")

# 2) CLASSIFICATION EC — les 6 classes établies (held-out exhaustif).
EC = {1: "oxydoréductase", 2: "transférase", 3: "hydrolase",
      4: "lyase", 5: "isomérase", 6: "ligase"}
for n, nom in EC.items():
    check(P.classe_enzyme_ec(n) == nom, f"EC {n} = {nom}")
check(len(P.CLASSES_EC) == 6, "exactement 6 classes EC")

# 3) STRUCTURE — les 4 niveaux établis présents et descriptions distinctes.
for niv in ["primaire", "secondaire", "tertiaire", "quaternaire"]:
    d = P.niveau_structure(niv)
    check(isinstance(d, str) and len(d) > 0, f"niveau {niv} a une description")
check(len({P.niveau_structure(n) for n in
           ["primaire", "secondaire", "tertiaire", "quaternaire"]}) == 4,
      "4 descriptions distinctes")
# faits caractéristiques attendus dans les descriptions (sans inventer).
check("séquence" in P.niveau_structure("primaire").lower(), "primaire = séquence d'aa")
check("hélice" in P.niveau_structure("secondaire").lower()
      and "feuillet" in P.niveau_structure("secondaire").lower(), "secondaire = hélice α / feuillet β")
check("3d" in P.niveau_structure("tertiaire").lower()
      or "tridimensionnelle" in P.niveau_structure("tertiaire").lower(), "tertiaire = 3D")
check("sous-unité" in P.niveau_structure("quaternaire").lower(), "quaternaire = sous-unités")
# insensibilité casse / espaces.
check(P.niveau_structure("  PRIMAIRE ") == P.niveau_structure("primaire"), "casse/espaces tolérés")

# 4) LIAISONS PEPTIDIQUES = n−1 (held-out, divers n).
for n, attendu in [(1, 0), (2, 1), (3, 2), (10, 9), (51, 50), (100, 99), (245, 244), (1000, 999)]:
    check(P.nombre_liaisons_peptidiques(n) == attendu, f"{n} aa -> {attendu} liaisons")
# cohérence interne : liaisons(n) = liaisons(n-1) + 1.
check(all(P.nombre_liaisons_peptidiques(n) == P.nombre_liaisons_peptidiques(n - 1) + 1
          for n in range(2, 200)), "récurrence n -> n+1 cohérente")

# 5) SOUNDNESS — n_acides_amines < 1 ou non entier -> ValueError (jamais un faux).
for bad in [0, -1, -100]:
    check(leve_v(P.nombre_liaisons_peptidiques, bad), f"n={bad} < 1 -> ValueError")
for bad in [1.5, 100.0, "100", None, True, False, [3], 2 + 1j]:
    check(leve_v(P.nombre_liaisons_peptidiques, bad), f"n non entier {bad!r} -> ValueError")

# 6) SOUNDNESS — chiffre EC hors 1..6 ou non entier -> ValueError.
for bad in [0, 7, 8, 9, -1, 100]:
    check(leve_v(P.classe_enzyme_ec, bad), f"EC {bad} hors 1..6 -> ValueError")
for bad in [3.0, "3", None, True, False, [3], 1.0]:
    check(leve_v(P.classe_enzyme_ec, bad), f"EC non entier {bad!r} -> ValueError")

# 7) SOUNDNESS — niveau de structure inconnu / non-str -> ValueError.
for bad in ["primair", "alpha", "domaine", "", "  ", "0", "supersecondaire"]:
    check(leve_v(P.niveau_structure, bad), f"niveau inconnu {bad!r} -> ValueError")
for bad in [None, 1, 3.14, ["primaire"], True]:
    check(leve_v(P.niveau_structure, bad), f"niveau non-str {bad!r} -> ValueError")

# 8) DÉTERMINISME.
check(P.nombre_liaisons_peptidiques(100) == P.nombre_liaisons_peptidiques(100), "déterminisme liaisons")
check(P.classe_enzyme_ec(3) == P.classe_enzyme_ec(3), "déterminisme EC")
check(P.niveau_structure("tertiaire") == P.niveau_structure("tertiaire"), "déterminisme structure")

print(f"\n=== valide_proteines : {ok}/{ok+ko} ===")
import sys
sys.exit(0 if ko == 0 else 1)
