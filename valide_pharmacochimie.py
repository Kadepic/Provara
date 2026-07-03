"""VALIDE pharmacochimie.py — ADVERSE, FAUX=0. Règle de cinq de Lipinski.
Ancres = molécules réelles à descripteurs établis (aspirine, caféine, paracétamol, atorvastatine)
+ mécanisme de comptage de seuils + bornes inclusives (≤) + SOUNDNESS (valeurs invalides -> ValueError)
+ déterminisme."""
import pharmacochimie as P

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


# === ANCRES : molécules réelles, descripteurs établis ===
# Aspirine C9H8O4 : MM=180.16, logP≈1.2, donneurs=1, accepteurs=4 -> drug-like, 0 violation
check(P.respecte_lipinski(180.16, 1.2, 1, 4) is True, "aspirine respecte Lipinski")
check(P.nombre_violations(180.16, 1.2, 1, 4) == 0, "aspirine 0 violation")
check(P.est_drug_like(180.16, 1.2, 1, 4) is True, "aspirine drug-like")
# Caféine C8H10N4O2 : logP≈-0.07 (NÉGATIF, légitime), donneurs=0, accepteurs=6 -> 0 violation
check(P.nombre_violations(194.19, -0.07, 0, 6) == 0, "caféine 0 violation (logP négatif accepté)")
check(P.respecte_lipinski(194.19, -0.07, 0, 6) is True, "caféine respecte Lipinski")
# Paracétamol C8H9NO2 : MM=151.16, logP≈0.46, donneurs=2, accepteurs=3 -> 0 violation
check(P.nombre_violations(151.16, 0.46, 2, 3) == 0, "paracétamol 0 violation")
# Atorvastatine C33H35FN2O5 : MM=558.64>500 et logP≈5.7>5 -> 2 violations (médicament qui viole Ro5)
check(P.nombre_violations(558.64, 5.7, 4, 7) == 2, "atorvastatine 2 violations (MM>500, logP>5)")
check(P.respecte_lipinski(558.64, 5.7, 4, 7) is False, "atorvastatine ne respecte pas (strict)")
check(P.est_drug_like(558.64, 5.7, 4, 7) is False, "atorvastatine non drug-like (>1 violation)")

# === MÉCANISME : une violation par critère ===
check(P.nombre_violations(600, 2, 2, 5) == 1, "MM=600 -> 1 violation (masse)")
check(P.nombre_violations(300, 6, 2, 5) == 1, "logP=6 -> 1 violation (lipophilie)")
check(P.nombre_violations(300, 2, 7, 5) == 1, "donneurs=7 -> 1 violation")
check(P.nombre_violations(300, 2, 2, 12) == 1, "accepteurs=12 -> 1 violation")
# 3 critères violés -> non drug-like ; 4 critères violés
check(P.nombre_violations(700, 7, 8, 5) == 3, "molécule violant 3 critères")
check(P.est_drug_like(700, 7, 8, 5) is False, "3 violations -> non drug-like")
check(P.respecte_lipinski(700, 7, 8, 5) is False, "3 violations -> ne respecte pas")
check(P.nombre_violations(700, 7, 8, 12) == 4, "tous critères violés -> 4 violations")

# === TOLÉRANCE PRATIQUE : 1 violation reste drug-like mais ne « respecte » pas (strict) ===
check(P.est_drug_like(600, 2, 2, 5) is True, "1 violation -> drug-like (toléré)")
check(P.respecte_lipinski(600, 2, 2, 5) is False, "1 violation -> ne respecte pas (strict 0)")

# === BORNES INCLUSIVES (≤, pas <) : exactement au seuil = OK ===
check(P.nombre_violations(500, 5, 5, 10) == 0, "tous exactement aux seuils -> 0 violation")
check(P.respecte_lipinski(500, 5, 5, 10) is True, "seuils inclusifs : 500/5/5/10 respecte")
check(P.nombre_violations(501, 5, 5, 10) == 1, "MM=501 (>500) -> 1 violation")
check(P.nombre_violations(500, 5.01, 5, 10) == 1, "logP=5.01 (>5) -> 1 violation")
check(P.nombre_violations(500, 5, 6, 10) == 1, "donneurs=6 (>5) -> 1 violation")
check(P.nombre_violations(500, 5, 5, 11) == 1, "accepteurs=11 (>10) -> 1 violation")

# === indice_lipinski : verdict détaillé exact ===
i = P.indice_lipinski(180.16, 1.2, 1, 4)
check(i["masse_ok"] and i["logP_ok"] and i["donneurs_ok"] and i["accepteurs_ok"], "indice aspirine : 4 critères ok")
check(i["n_violations"] == 0 and i["n_satisfaits"] == 4 and i["respecte"] is True and i["drug_like"] is True,
      "indice aspirine : synthèse")
j = P.indice_lipinski(558.64, 5.7, 4, 7)
check(j["masse_ok"] is False and j["logP_ok"] is False, "indice atorvastatine : masse & logP KO")
check(j["donneurs_ok"] is True and j["accepteurs_ok"] is True, "indice atorvastatine : donneurs & accepteurs ok")
check(j["n_violations"] == 2 and j["n_satisfaits"] == 2 and j["respecte"] is False and j["drug_like"] is False,
      "indice atorvastatine : synthèse")
# invariant structurel : n_violations + n_satisfaits == 4
for args in [(180.16, 1.2, 1, 4), (558.64, 5.7, 4, 7), (700, 7, 8, 12), (500, 5, 5, 10)]:
    d = P.indice_lipinski(*args)
    check(d["n_violations"] + d["n_satisfaits"] == 4, f"invariant violations+satisfaits=4 {args}")
    check(d["n_violations"] == P.nombre_violations(*args), f"indice cohérent avec nombre_violations {args}")

# === SOUNDNESS : valeurs invalides -> ValueError ===
check(leve(P.respecte_lipinski, -10, 1.2, 1, 4), "MM<0 -> ValueError")
check(leve(P.nombre_violations, 0, 1.2, 1, 4), "MM=0 -> ValueError (masse doit être >0)")
check(leve(P.nombre_violations, 180, 1.2, -1, 4), "donneurs<0 -> ValueError")
check(leve(P.nombre_violations, 180, 1.2, 1, -4), "accepteurs<0 -> ValueError")
check(leve(P.indice_lipinski, 180, 1.2, -2, 4), "indice donneurs<0 -> ValueError")
check(leve(P.nombre_violations, "x", 1.2, 1, 4), "MM non numérique -> ValueError")
check(leve(P.nombre_violations, 180, "y", 1, 4), "logP non numérique -> ValueError")
check(leve(P.nombre_violations, 180, float("nan"), 1, 4), "logP NaN -> ValueError")
check(leve(P.nombre_violations, 180, float("inf"), 1, 4), "logP inf -> ValueError")
check(leve(P.nombre_violations, float("inf"), 1.2, 1, 4), "MM inf -> ValueError")
check(leve(P.respecte_lipinski, True, 1.2, 1, 4), "MM=bool -> ValueError (bool rejeté)")
check(leve(P.nombre_violations, 180, 1.2, 1, float("inf")), "accepteurs inf -> ValueError")
# logP négatif NE doit PAS lever (descripteur légitime) :
check(P.nombre_violations(180, -3.5, 1, 4) == 0, "logP négatif accepté (pas de ValueError)")

# === DÉTERMINISME ===
check(P.nombre_violations(558.64, 5.7, 4, 7) == P.nombre_violations(558.64, 5.7, 4, 7), "déterminisme nombre_violations")
check(P.respecte_lipinski(180.16, 1.2, 1, 4) == P.respecte_lipinski(180.16, 1.2, 1, 4), "déterminisme respecte_lipinski")
check(P.indice_lipinski(500, 5, 5, 10) == P.indice_lipinski(500, 5, 5, 10), "déterminisme indice_lipinski")

print(f"\n=== valide_pharmacochimie : {ok}/{ok + ko} ===")
import sys
sys.exit(0 if ko == 0 else 1)
