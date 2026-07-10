"""
VALIDE trigonometrie_triangle.py — held-out ADVERSE.

ANCRES NON CIRCULAIRES (valeurs connues INDÉPENDAMMENT de la formule testée) :
  • Triangle 3-4-5 : angle opposé à 5 = 90° (Pythagore) ; angles 36.87° / 53.13° / 90° ; aire = 6 par Héron
    ET par ½·3·4 (deux chemins qui coïncident).
  • Triangle équilatéral de côté 2 : aire = √3 ≈ 1.7320508 ; tous les angles = 60°.
  • sin(30°)=1/2 EXACT ; sin(45°)=√2/2 ; sin(60°)=√3/2 ; sin(37°) APPROCHÉ et marqué tel.
  • LOI DES SINUS : a=10, A=30°, B=45° -> b = 10·sin45/sin30 = 14.1421356 (calcul à la main).
  • CAS AMBIGU SSA :
      a=6, b=8, A=30° -> h=4, 4<6<8 -> DEUX solutions (B ≈ 41.81° et B ≈ 138.19°) ;
      a=3, b=8, A=30° -> h=4>3 -> ZÉRO solution ;
      a=10, b=8, A=30° -> a≥b -> UNE solution ;
      a=4, b=8, A=30° -> a=h -> UNE solution (rectangle, B=90°).

SOUNDNESS : inégalité triangulaire, côté ≤ 0, angle hors ]0,180[, somme angles ≥ 180, cas inconnu,
clé manquante, types (bool/str/NaN/inf), mauvaise arité -> ValueError. DÉTERMINISME vérifié.
"""
import math
from fractions import Fraction

import trigonometrie_triangle as G

ok = 0
ko = 0


def check(cond, label):
    global ok, ko
    if cond:
        ok += 1
    else:
        ko += 1
        print(f"  FAIL: {label}")


def leve(fn, *a):
    """True ssi fn(*a) lève ValueError (abstention structurelle)."""
    try:
        fn(*a)
        return False
    except ValueError:
        return True


def proche(x, attendu, tol=1e-6):
    return x is not None and abs(x - attendu) <= tol


# ── 1) LOI DES SINUS (ancre calculée à la main) ──
check(proche(G.loi_sinus(10, 30, 45), 14.1421356, tol=1e-6), "loi_sinus(10,30,45) = 14.1421356")
# a/sinA = b/sinB : a=7,A=90,B=30 -> b = 7·sin30/sin90 = 3.5
check(proche(G.loi_sinus(7, 90, 30), 3.5), "loi_sinus(7,90,30) = 3.5")
# symétrie triviale : loi_sinus(a,A,A) = a
check(proche(G.loi_sinus(5, 50, 50), 5.0), "loi_sinus(a,A,A) = a")

# ── 2) CCC : triangle 3-4-5 (angles connus) ──
tri = G.resout_triangle({"cas": "CCC", "a": 3, "b": 4, "c": 5})
check(len(tri) == 1, "CCC 3-4-5 -> 1 triangle")
t = tri[0]
check(proche(t["C"], 90.0), "3-4-5 : angle opposé à 5 = 90°")       # Pythagore
check(proche(t["A"], 36.8698976, tol=1e-5), "3-4-5 : angle opposé à 3 = 36.87°")
check(proche(t["B"], 53.1301024, tol=1e-5), "3-4-5 : angle opposé à 4 = 53.13°")
check(proche(t["A"] + t["B"] + t["C"], 180.0), "3-4-5 : somme des angles = 180°")

# ── 3) AIRE — deux chemins qui coïncident ──
check(proche(G.aire_heron(3, 4, 5), 6.0), "aire Héron 3-4-5 = 6")            # s=6 -> √(6·3·2·1)=6
check(proche(G.aire_sinus(3, 4, 90), 6.0), "aire sinus ½·3·4·sin90 = 6")     # ½·3·4·1 = 6
check(proche(G.aire_heron(3, 4, 5), G.aire_sinus(3, 4, 90)), "Héron == sinus (3-4-5)")
# équilatéral de côté 2 : aire = √3 ≈ 1.7320508
check(proche(G.aire_heron(2, 2, 2), 1.7320508, tol=1e-6), "aire équilatéral côté 2 = √3")
check(proche(G.aire_sinus(2, 2, 60), 1.7320508, tol=1e-6), "aire sinus équilatéral = √3")
check(proche(G.aire_heron(2, 2, 2), G.aire_sinus(2, 2, 60)), "Héron == sinus (équilatéral)")

# ── 4) CAS AMBIGU SSA — le cœur FAUX=0 ──
deux = G.resout_triangle({"cas": "CCA", "a": 6, "b": 8, "A": 30})
check(len(deux) == 2, "SSA a=6,b=8,A=30 -> DEUX solutions")
angles_B = sorted(s["B"] for s in deux)
check(proche(angles_B[0], 41.8103149, tol=1e-4), "SSA solution 1 : B ≈ 41.81°")
check(proche(angles_B[1], 138.1896851, tol=1e-4), "SSA solution 2 : B ≈ 138.19°")
for s in deux:
    check(proche(s["A"], 30.0), "SSA : chaque solution a A = 30°")
    check(proche(s["A"] + s["B"] + s["C"], 180.0), "SSA : somme angles = 180°")

zero = G.resout_triangle({"cas": "CCA", "a": 3, "b": 8, "A": 30})
check(len(zero) == 0, "SSA a=3,b=8,A=30 (h=4>3) -> ZÉRO solution")

une = G.resout_triangle({"cas": "CCA", "a": 10, "b": 8, "A": 30})
check(len(une) == 1, "SSA a=10,b=8,A=30 (a≥b) -> UNE solution")

rect = G.resout_triangle({"cas": "CCA", "a": 4, "b": 8, "A": 30})
check(len(rect) == 1, "SSA a=4,b=8,A=30 (a=h) -> UNE solution")
check(proche(rect[0]["B"], 90.0, tol=1e-4), "SSA a=h -> triangle RECTANGLE (B=90°)")

# ── 5) CAC (SAS) : b=3,c=4,A=90 -> a = hypoténuse 5 (Pythagore) ──
sas = G.resout_triangle({"cas": "CAC", "b": 3, "c": 4, "A": 90})
check(len(sas) == 1 and proche(sas[0]["a"], 5.0), "CAC b=3,c=4,A=90 -> a=5 (hypoténuse)")
check(proche(sas[0]["A"], 90.0), "CAC : angle opposé à a = 90°")

# ── 6) ACA / AAC : équilatéral (tous angles 60°, tous côtés égaux) ──
asa = G.resout_triangle({"cas": "ACA", "A": 60, "C": 60, "b": 2})[0]
check(proche(asa["a"], 2.0) and proche(asa["c"], 2.0), "ACA équilatéral -> côtés = 2")
check(proche(asa["A"], 60.0) and proche(asa["B"], 60.0) and proche(asa["C"], 60.0), "ACA -> angles 60°")
aas = G.resout_triangle({"cas": "AAC", "A": 60, "B": 60, "a": 2})[0]
check(proche(aas["b"], 2.0) and proche(aas["c"], 2.0), "AAC équilatéral -> côtés = 2")
# AAC non équilatéral cohérent avec loi des sinus : A=30,B=90,a=5 -> C=60, b = 5·sin90/sin30 = 10
aas2 = G.resout_triangle({"cas": "AAC", "A": 30, "B": 90, "a": 5})[0]
check(proche(aas2["b"], 10.0), "AAC A=30,B=90,a=5 -> b=10 (loi des sinus)")

# ── 7) verifie_triangle ──
check(G.verifie_triangle(3, 4, 5) is True, "verifie_triangle(3,4,5) = True")
check(leve(G.verifie_triangle, 1, 2, 3), "1-2-3 dégénéré (1+2=3) -> ValueError")
check(leve(G.verifie_triangle, 1, 1, 10), "1-1-10 impossible -> ValueError")

# ── 8) VALEURS EXACTES (ancres littérales) ──
check(G.sin_exact(0) == Fraction(0, 1), "sin_exact(0) = 0 (Fraction)")
check(G.sin_exact(30) == Fraction(1, 2), "sin_exact(30) = 1/2 EXACT")
check(G.sin_exact(90) == Fraction(1, 1), "sin_exact(90) = 1 EXACT")
check(G.sin_exact(45) == (1, 2, 2), "sin_exact(45) = (1,2,2) = √2/2")
check(G.sin_exact(60) == (1, 3, 2), "sin_exact(60) = (1,3,2) = √3/2")
# la représentation (num,rad,den) évalue bien à la valeur numérique attendue
n, r, d = G.sin_exact(45)
check(proche(n * math.sqrt(r) / d, 0.70710678, tol=1e-6), "(1,2,2) évalue à √2/2 ≈ 0.7071")
n, r, d = G.sin_exact(60)
check(proche(n * math.sqrt(r) / d, 0.86602540, tol=1e-6), "(1,3,2) évalue à √3/2 ≈ 0.8660")
# sin(37°) : APPROCHÉ et MARQUÉ tel
s37 = G.sin_exact(37)
check(isinstance(s37, tuple) and s37[1] == "approchee", "sin_exact(37) marqué 'approchee'")
check(proche(s37[0], 0.601815023, tol=1e-6), "sin_exact(37) ≈ 0.6018 (valeur approchée)")
check(not isinstance(G.sin_exact(30), tuple), "sin_exact(30) n'est PAS marqué approché")

# ── 9) SOUNDNESS — angles / côtés hors domaine ──
check(leve(G.loi_sinus, 0, 30, 45), "loi_sinus côté=0 -> ValueError")
check(leve(G.loi_sinus, -1, 30, 45), "loi_sinus côté<0 -> ValueError")
check(leve(G.loi_sinus, 5, 0, 45), "loi_sinus angle=0 -> ValueError")
check(leve(G.loi_sinus, 5, 180, 45), "loi_sinus angle=180 -> ValueError")
check(leve(G.loi_sinus, 5, 200, 45), "loi_sinus angle>180 -> ValueError")
check(leve(G.aire_sinus, 3, 4, 0), "aire_sinus angle=0 -> ValueError")
check(leve(G.aire_sinus, 3, 4, 180), "aire_sinus angle=180 -> ValueError")
check(leve(G.aire_heron, 1, 2, 3), "aire_heron dégénéré -> ValueError")

# ── 10) SOUNDNESS — somme des angles ≥ 180 / cas / clés ──
check(leve(G.resout_triangle, {"cas": "ACA", "A": 120, "C": 90, "b": 2}), "ACA A+C≥180 -> ValueError")
check(leve(G.resout_triangle, {"cas": "AAC", "A": 120, "B": 90, "a": 2}), "AAC A+B≥180 -> ValueError")
check(leve(G.resout_triangle, {"cas": "CCC", "a": 1, "b": 2, "c": 3}), "CCC 1-2-3 dégénéré -> ValueError")
check(leve(G.resout_triangle, {"cas": "XXX", "a": 1}), "cas inconnu -> ValueError")
check(leve(G.resout_triangle, {"cas": "CCC", "a": 3, "b": 4}), "CCC clé 'c' manquante -> ValueError")
check(leve(G.resout_triangle, {"a": 3, "b": 4, "c": 5}), "donnees sans 'cas' -> ValueError")
check(leve(G.resout_triangle, "CCC"), "donnees non-dict -> ValueError")
check(leve(G.resout_triangle, {"cas": 123}), "cas non-str -> ValueError")

# ── 11) SOUNDNESS — types invalides (bool / str / NaN / inf / arité) ──
check(leve(G.loi_sinus, True, 30, 45), "loi_sinus bool -> ValueError")
check(leve(G.loi_sinus, "5", 30, 45), "loi_sinus str -> ValueError")
check(leve(G.loi_sinus, float("nan"), 30, 45), "loi_sinus NaN -> ValueError")
check(leve(G.loi_sinus, float("inf"), 30, 45), "loi_sinus inf -> ValueError")
check(leve(G.sin_exact, True), "sin_exact bool -> ValueError")
check(leve(G.sin_exact, "30"), "sin_exact str -> ValueError")
check(leve(G.sin_exact, float("nan")), "sin_exact NaN -> ValueError")
check(leve(G.aire_heron, 3, 4, float("inf")), "aire_heron inf -> ValueError")
check(leve(G.aire_sinus, "3", 4, 60), "aire_sinus str -> ValueError")

# ── 12) DÉTERMINISME ──
check(G.loi_sinus(10, 30, 45) == G.loi_sinus(10, 30, 45), "déterminisme loi_sinus")
check(G.resout_triangle({"cas": "CCA", "a": 6, "b": 8, "A": 30})
      == G.resout_triangle({"cas": "CCA", "a": 6, "b": 8, "A": 30}), "déterminisme SSA")
check(G.sin_exact(45) == G.sin_exact(45), "déterminisme sin_exact")

print(f"\n=== valide_trigonometrie_triangle : {ok}/{ok+ko} ===")
import sys
sys.exit(0 if ko == 0 else 1)
