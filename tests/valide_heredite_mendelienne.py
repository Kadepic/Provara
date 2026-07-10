"""
VALIDE heredite_mendelienne.py — held-out ADVERSE.

ANCRES EXTERNES NON CIRCULAIRES : les proportions CANONIQUES de Mendel (1866), écrites en dur, connues
indépendamment de tout code.
  • Aa × Aa, dominance complète            -> 3/4 dominants, 1/4 récessifs   (le fameux 3:1)
  • Aa × Aa, dominance incomplète           -> 1/4 : 1/2 : 1/4               (1:2:1 — le régime CHANGE tout)
  • AaBb × AaBb, dominance complète         -> 9/16 : 3/16 : 3/16 : 1/16     (le fameux 9:3:3:1)
  • Croisement-test 'Aa' × 'aa'             -> 1/2 : 1/2 (c'est ce qui RÉVÈLE l'hétérozygotie)
  • Croisement-test 'AA' × 'aa'             -> 100 % dominants
Ces valeurs sont posées à la main ; le module ne les recalcule jamais pour lui-même.

ANCRE DE DISCRIMINATION : le même croisement Aa × Aa donne 3:1 en dominance complète et 1:2:1 en dominance
incomplète. Un module qui rendrait la même chose pour les deux serait FAUX. Le régime doit être NOMMÉ.

SOUNDNESS : génotype mal formé, allèles de gènes différents ('Ab'), régime non nommé, gènes liés,
entrées non-str/bool -> ValueError. Invariant : la somme des proportions vaut EXACTEMENT 1 (Fraction).
"""
import sys
from fractions import Fraction as F

import heredite_mendelienne as M

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


# ── 1) GAMÈTES : loi de ségrégation ──
check(M.gametes("Aa") == (("A", F(1, 2)), ("a", F(1, 2))), "Aa produit A et a à 1/2 chacun")
check(M.gametes("AA") == (("A", F(1)),), "AA ne produit que A (probabilité 1)")
check(M.gametes("aa") == (("a", F(1)),), "aa ne produit que a")
check(all(isinstance(p, F) for _, p in M.gametes("Aa")), "probabilités en Fraction EXACTE")

# ── 2) ANCRE 3:1 — le résultat le plus célèbre de la génétique ──
p = M.proportions_phenotypiques("Aa", "Aa", "complete")
check(p == {"[A]": F(3, 4), "[a]": F(1, 4)}, "Aa × Aa, dominance complète -> 3/4 : 1/4 (le 3:1 de Mendel)")
check(sum(p.values()) == 1, "somme des proportions = 1 exactement")

# ── 3) ANCRE 1:2:1 — le MÊME croisement, un AUTRE régime : les proportions changent ──
q = M.proportions_phenotypiques("Aa", "Aa", "incomplete")
check(sorted(q.values()) == [F(1, 4), F(1, 4), F(1, 2)], "dominance incomplète -> 1:2:1")
check(len(q) == 3, "dominance incomplète : TROIS phénotypes distincts")
check(len(p) == 2, "dominance complète : DEUX phénotypes seulement")
check(p != q, "ANCRE DISCRIMINANTE : le régime de dominance change les proportions")

c = M.proportions_phenotypiques("Aa", "Aa", "codominance")
check(len(c) == 3 and sorted(c.values()) == [F(1, 4), F(1, 4), F(1, 2)], "codominance -> 1:2:1, 3 phénotypes")
check(any("et" in k for k in c), "codominance : l'hétérozygote exprime LES DEUX allèles")

# ── 4) GÉNOTYPES du croisement mono-hybride ──
g = M.croisement("Aa", "Aa")
check(g == {"AA": F(1, 4), "Aa": F(1, 2), "aa": F(1, 4)}, "Aa × Aa -> 1/4 AA, 1/2 Aa, 1/4 aa")
check(M.croisement("AA", "aa") == {"Aa": F(1)}, "AA × aa -> 100 % Aa (F1 uniforme, 1re loi)")
check(M.croisement("Aa", "aa") == {"Aa": F(1, 2), "aa": F(1, 2)}, "Aa × aa -> 1/2 : 1/2")
check(M.croisement("aA", "Aa") == M.croisement("Aa", "Aa"), "'aA' et 'Aa' sont le même génotype")

# ── 5) ANCRE 9:3:3:1 — dihybride ──
d = M.proportions_phenotypiques_dihybride("AaBb", "AaBb", "complete")
check(sorted(d.values()) == [F(1, 16), F(3, 16), F(3, 16), F(9, 16)],
      "AaBb × AaBb, dominance complète -> 9:3:3:1")
check(sum(d.values()) == 1, "dihybride : somme = 1 exactement")
check(d.get("[A][B]") == F(9, 16), "double dominant = 9/16")
check(d.get("[a][b]") == F(1, 16), "double récessif = 1/16")
gd = M.croisement_dihybride("AaBb", "AaBb")
check(sum(gd.values()) == 1, "génotypes dihybrides : somme = 1")
check(len(gd) == 9, "dihybride : 9 génotypes distincts")

# ── 6) CROISEMENT-TEST : le geste expérimental de Mendel ──
check(M.test_cross("AA") == {"[A]": F(1)}, "test-cross d'un AA -> 100 % dominants")
check(M.test_cross("Aa") == {"[A]": F(1, 2), "[a]": F(1, 2)}, "test-cross d'un Aa -> 1/2 : 1/2 (révèle Aa)")
check(M.test_cross("AA") != M.test_cross("Aa"), "le test-cross DISCRIMINE AA de Aa")

# ── 7) PHÉNOTYPES ──
check(M.phenotype("AA", "complete") == "[A]", "AA -> [A]")
check(M.phenotype("aa", "complete") == "[a]", "aa -> [a]")
check(M.phenotype("Aa", "complete") == M.phenotype("AA", "complete"),
      "dominance complète : Aa indiscernable de AA")
check(M.phenotype("Aa", "incomplete") != M.phenotype("AA", "incomplete"),
      "dominance incomplète : Aa distinct de AA")

# ── 8) SOUNDNESS — génotypes mal formés ──
check(leve(M.croisement, "Ab", "Aa"), "'Ab' : allèles de gènes DIFFÉRENTS -> ValueError")
check(leve(M.croisement, "A", "Aa"), "génotype d'une seule lettre -> ValueError")
check(leve(M.croisement, "AAA", "Aa"), "génotype de trois lettres -> ValueError")
check(leve(M.croisement, "A1", "Aa"), "caractère non alphabétique -> ValueError")
check(leve(M.croisement, "", "Aa"), "génotype vide -> ValueError")
check(leve(M.gametes, 42), "entier -> ValueError")
check(leve(M.gametes, True), "bool -> ValueError")
check(leve(M.gametes, None), "None -> ValueError")

# ── 9) SOUNDNESS — le régime doit être NOMMÉ ──
check(leve(M.phenotype, "Aa", "dominant"), "régime inventé -> ValueError")
check(leve(M.phenotype, "Aa", None), "régime None -> ValueError")
check(leve(M.proportions_phenotypiques, "Aa", "Aa", "partielle"), "régime hors catalogue -> ValueError")
check(set(M.DOMINANCES) == {"complete", "incomplete", "codominance"}, "exactement trois régimes nommés")

# ── 10) SOUNDNESS — gènes liés : ABSTENTION (le taux de recombinaison est inconnu) ──
check(leve(M.croisement_dihybride, "AaBb", "AaBb", False),
      "gènes LIÉS -> ValueError (le taux de recombinaison n'est pas déductible)")
check(leve(M.croisement_dihybride, "AaAa", "AaAa"), "deux fois le même gène -> ValueError")
check(leve(M.croisement_dihybride, "AaB", "AaBb"), "dihybride de 3 lettres -> ValueError")
check(leve(M.proportions_phenotypiques_dihybride, "AaBb", "AaBb", "complete", False),
      "phénotypes dihybrides de gènes liés -> ValueError")

# ── 11) EXACTITUDE : aucun flottant nulle part ──
for v in list(g.values()) + list(d.values()) + list(gd.values()):
    check(isinstance(v, F), "proportion en Fraction exacte (jamais un flottant)")

# ── 12) DÉTERMINISME ──
check(M.croisement("Aa", "Aa") == M.croisement("Aa", "Aa"), "déterminisme du croisement")
check(M.proportions_phenotypiques_dihybride("AaBb", "AaBb", "complete")
      == M.proportions_phenotypiques_dihybride("AaBb", "AaBb", "complete"), "déterminisme du dihybride")

print(f"\n=== valide_heredite_mendelienne : {ok}/{ok+ko} ===")
sys.exit(0 if ko == 0 else 1)
