"""
VALIDE alliages.py — held-out ADVERSE. Règle du levier (ancres calculées à la main + bilan de matière) +
catalogue (faits sourcés) + SOUNDNESS (hors intervalle, ligne dégénérée, entrée invalide, alliage inconnu ->
ValueError) + déterminisme. Aucun de ces cas n'est dans __main__.
"""
import alliages as A

ok = 0
ko = 0


def check(cond, label):
    global ok, ko
    if cond:
        ok += 1
    else:
        ko += 1
        print(f"  FAIL: {label}")


def _leve(fn, *a, **k):
    """True ssi fn(*a, **k) lève ValueError (abstention), False sinon."""
    try:
        fn(*a, **k)
        return False
    except ValueError:
        return True
    except Exception:
        return False


EPS = 1e-12

# 1) ANCRE PRINCIPALE — c=40 % entre c1=20 et c2=60 -> phase2 = (40-20)/(60-20) = 0.5, phase1 = 0.5.
f = A.fraction_phase(40, 20, 60)
check(abs(f.phase2 - 0.5) < EPS, "phase2(40,20,60) = 0.5")
check(abs(f.phase1 - 0.5) < EPS, "phase1(40,20,60) = 0.5")
check(abs((f.phase1 + f.phase2) - 1.0) < EPS, "somme des fractions = 1")

# 2) BORNES — aux extrémités de la ligne de conjugaison : 0 ou 1.
fb1 = A.fraction_phase(20, 20, 60)
check(abs(fb1.phase2 - 0.0) < EPS and abs(fb1.phase1 - 1.0) < EPS, "borne c=c1 -> (1,0)")
fb2 = A.fraction_phase(60, 20, 60)
check(abs(fb2.phase2 - 1.0) < EPS and abs(fb2.phase1 - 0.0) < EPS, "borne c=c2 -> (0,1)")

# 3) AUTRES ANCRES calculées à la main.
#    c=30, c1=0, c2=100 -> phase2 = 30/100 = 0.30 ; phase1 = 0.70.
f3 = A.fraction_phase(30, 0, 100)
check(abs(f3.phase2 - 0.30) < EPS and abs(f3.phase1 - 0.70) < EPS, "(30,0,100) -> 0.30/0.70")
#    c=25, c1=10, c2=50 -> phase2 = 15/40 = 0.375 ; phase1 = 0.625.
f4 = A.fraction_phase(25, 10, 50)
check(abs(f4.phase2 - 0.375) < EPS and abs(f4.phase1 - 0.625) < EPS, "(25,10,50) -> 0.375/0.625")
#    c=46, c1=8, c2=92 -> phase2 = 38/84 ; phase1 = 46/84.
f5 = A.fraction_phase(46, 8, 92)
check(abs(f5.phase2 - 38.0 / 84.0) < EPS, "(46,8,92) -> 38/84")

# 4) BORNES INVERSÉES (c1 > c2) : la règle reste exacte. c=40, c1=60, c2=20 -> (40-60)/(20-60)=0.5.
fi = A.fraction_phase(40, 60, 20)
check(abs(fi.phase2 - 0.5) < EPS, "ordre inversé (40,60,20) -> phase2=0.5")

# 5) PROPRIÉTÉ BILAN DE MATIÈRE : W1·c1 + W2·c2 == c (vérifie l'identité du levier sur des cas variés).
for c, c1, c2 in [(40, 20, 60), (30, 0, 100), (25, 10, 50), (46, 8, 92), (7.5, 5.0, 12.5)]:
    ff = A.fraction_phase(c, c1, c2)
    check(abs(ff.phase1 * c1 + ff.phase2 * c2 - c) < 1e-9, f"bilan matière ({c},{c1},{c2})")
    check(-EPS <= ff.phase1 <= 1 + EPS and -EPS <= ff.phase2 <= 1 + EPS,
          f"fractions dans [0,1] ({c},{c1},{c2})")

# 6) SOUNDNESS — c hors de [c1,c2] -> ValueError (jamais une fraction hors [0,1]).
check(_leve(A.fraction_phase, 70, 20, 60), "c=70 hors [20,60] -> ValueError")
check(_leve(A.fraction_phase, 10, 20, 60), "c=10 hors [20,60] -> ValueError")
check(_leve(A.fraction_phase, 19.999, 20, 60), "c juste sous c1 -> ValueError")
check(_leve(A.fraction_phase, 60.001, 20, 60), "c juste au-dessus c2 -> ValueError")

# 7) SOUNDNESS — ligne de conjugaison dégénérée c1==c2 -> ValueError (pas de division par zéro).
check(_leve(A.fraction_phase, 20, 30, 30), "c1==c2 -> ValueError")
check(_leve(A.fraction_phase, 30, 30, 30), "c1==c2 (c sur la borne) -> ValueError")

# 8) SOUNDNESS — entrées invalides -> ValueError (abstention, jamais un faux).
check(_leve(A.fraction_phase, "40", 20, 60), "c non numérique -> ValueError")
check(_leve(A.fraction_phase, None, 20, 60), "c None -> ValueError")
check(_leve(A.fraction_phase, 40, None, 60), "c1 None -> ValueError")
check(_leve(A.fraction_phase, float("nan"), 20, 60), "c NaN -> ValueError")
check(_leve(A.fraction_phase, float("inf"), 20, 60), "c inf -> ValueError")
check(_leve(A.fraction_phase, 40, 20, float("inf")), "c2 inf -> ValueError")
check(_leve(A.fraction_phase, True, 20, 60), "c booléen -> ValueError")

# 9) CATALOGUE — faits sourcés exacts.
check(A.classe_alliage("acier").constituants == ("fer", "carbone"), "acier = fer+carbone")
check(A.classe_alliage("bronze").constituants == ("cuivre", "étain"), "bronze = cuivre+étain")
check(A.classe_alliage("laiton").constituants == ("cuivre", "zinc"), "laiton = cuivre+zinc")
check(A.classe_alliage("duralumin").constituants == ("aluminium", "cuivre"), "duralumin = aluminium+cuivre")
check(A.classe_alliage("acier").base == "fer" and A.classe_alliage("acier").ajout == "carbone",
      "champs base/ajout acier")

# 10) CATALOGUE — normalisation casse / espaces.
check(A.classe_alliage("ACIER").constituants == ("fer", "carbone"), "casse majuscule normalisée")
check(A.classe_alliage("  Bronze  ").constituants == ("cuivre", "étain"), "espaces normalisés")

# 11) CATALOGUE — distinction bronze vs laiton (même base cuivre, ajout différent).
check(A.classe_alliage("bronze") != A.classe_alliage("laiton"), "bronze != laiton")

# 12) SOUNDNESS catalogue — alliage inconnu / entrée invalide -> ValueError (jamais deviné).
check(_leve(A.classe_alliage, "inox"), "alliage inconnu 'inox' -> ValueError")
check(_leve(A.classe_alliage, "or"), "métal pur 'or' -> ValueError")
check(_leve(A.classe_alliage, ""), "chaîne vide -> ValueError")
check(_leve(A.classe_alliage, "fonte"), "alliage hors catalogue 'fonte' -> ValueError")
check(_leve(A.classe_alliage, 123), "nom non textuel -> ValueError")
check(_leve(A.classe_alliage, None), "nom None -> ValueError")

# 13) DÉTERMINISME.
check(A.fraction_phase(40, 20, 60) == A.fraction_phase(40, 20, 60), "déterminisme fraction_phase")
check(A.classe_alliage("acier") == A.classe_alliage("acier"), "déterminisme classe_alliage")

print(f"\n=== valide_alliages : {ok}/{ok+ko} ===")
import sys
sys.exit(0 if ko == 0 else 1)
