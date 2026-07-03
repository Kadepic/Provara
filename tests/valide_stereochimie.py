"""VALIDE stereochimie.py — ADVERSE, FAUX=0.

Ancres CONNUES : règle de Le Bel–van't Hoff (2^n stéréoisomères, 2^(n-1) paires
d'énantiomères) sur cas chimiques de référence (1 centre -> 2 ; 2 centres -> 4 ;
3 centres -> 8) + relations RR/SS = énantiomères, RR/RS = diastéréomères.
SOUNDNESS : n < 0, descripteur ≠ R/S, longueurs différentes, suite vide ->
ValueError (jamais une réponse inventée). DÉTERMINISME : même entrée -> même sortie.
"""
import stereochimie as S

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


# ── nombre_stereoisomeres = 2^n (ancres : n = 0..6) ──
attendus_iso = {0: 1, 1: 2, 2: 4, 3: 8, 4: 16, 5: 32, 6: 64}
for n, v in attendus_iso.items():
    check(S.nombre_stereoisomeres(n) == v, f"nombre_stereoisomeres({n}) = {v}")

# Exemples chimiques de référence
check(S.nombre_stereoisomeres(1) == 2, "1 centre chiral -> 2 stéréoisomères")
check(S.nombre_stereoisomeres(2) == 4, "2 centres chiraux -> 4 stéréoisomères")

# ── paires_enantiomeres = 2^(n-1), 0 pour n = 0 ──
attendus_paires = {0: 0, 1: 1, 2: 2, 3: 4, 4: 8, 5: 16}
for n, v in attendus_paires.items():
    check(S.paires_enantiomeres(n) == v, f"paires_enantiomeres({n}) = {v}")
check(S.paires_enantiomeres(1) == 1, "1 centre -> 1 paire d'énantiomères")

# Cohérence : 2 * paires = total stéréoisomères (n >= 1)
for n in range(1, 7):
    check(2 * S.paires_enantiomeres(n) == S.nombre_stereoisomeres(n),
          f"2 x paires == total (n = {n})")

# ── nombre_enantiomeres = 2^n (n>=1), 0 si n = 0 ──
check(S.nombre_enantiomeres(0) == 0, "n = 0 : molécule achirale, 0 énantiomère")
check(S.nombre_enantiomeres(1) == 2, "n = 1 : 2 formes optiquement actives")
check(S.nombre_enantiomeres(3) == 8, "n = 3 : 8 formes optiquement actives")
for n in range(1, 7):
    check(S.nombre_enantiomeres(n) == S.nombre_stereoisomeres(n),
          f"sans méso, tous chiraux (n = {n})")

# ── classe_relation : ancres ──
check(S.classe_relation("RR", "SS") == "enantiomeres", "RR/SS = énantiomères")
check(S.classe_relation("RR", "RS") == "diastereomeres", "RR/RS = diastéréomères")
check(S.classe_relation("RR", "RR") == "identiques", "RR/RR = identiques")
check(S.classe_relation("R", "S") == "enantiomeres", "R/S = énantiomères")
check(S.classe_relation("R", "R") == "identiques", "R/R = identiques")
check(S.classe_relation("RS", "SR") == "enantiomeres", "RS/SR = énantiomères (tout inversé)")
check(S.classe_relation("RSR", "RSS") == "diastereomeres", "RSR/RSS = diastéréomères (1 centre diffère)")
check(S.classe_relation("RRS", "SSR") == "enantiomeres", "RRS/SSR = énantiomères (tout inversé)")
check(S.classe_relation("RRR", "SSS") == "enantiomeres", "RRR/SSS = énantiomères")
check(S.classe_relation("RRR", "SSR") == "diastereomeres", "RRR/SSR = diastéréomères")
# Accepte suites et casse mixte
check(S.classe_relation(["R", "R"], ("S", "S")) == "enantiomeres", "listes/tuples acceptés")
check(S.classe_relation("rr", "ss") == "enantiomeres", "casse mixte tolérée")

# ── DÉTERMINISME ──
check(S.nombre_stereoisomeres(4) == S.nombre_stereoisomeres(4), "déterminisme dénombrement")
check(S.classe_relation("RSR", "SRS") == S.classe_relation("RSR", "SRS"), "déterminisme relation")

# ── SOUNDNESS (abstention -> ValueError ; aucun faux positif) ──
check(leve(S.nombre_stereoisomeres, -1), "n < 0 -> ValueError")
check(leve(S.nombre_stereoisomeres, 1.5), "n non entier -> ValueError")
check(leve(S.nombre_stereoisomeres, True), "n booléen -> ValueError")
check(leve(S.nombre_stereoisomeres, "2"), "n chaîne -> ValueError")
check(leve(S.paires_enantiomeres, -3), "paires n < 0 -> ValueError")
check(leve(S.nombre_enantiomeres, -1), "énantiomères n < 0 -> ValueError")
check(leve(S.classe_relation, "RR", "R"), "longueurs différentes -> ValueError")
check(leve(S.classe_relation, "RR", "RX"), "descripteur invalide -> ValueError")
check(leve(S.classe_relation, "", ""), "configuration vide -> ValueError")
check(leve(S.classe_relation, "RZ", "RR"), "descripteur Z invalide -> ValueError")
check(leve(S.classe_relation, 5, "RR"), "config non textuelle/suite -> ValueError")
check(leve(S.classe_relation, ["R", 1], "RR"), "élément non textuel -> ValueError")

print(f"\n=== valide_stereochimie : {ok}/{ok + ko} ===")
import sys
sys.exit(0 if ko == 0 else 1)
