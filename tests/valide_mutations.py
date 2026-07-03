"""
VALIDE mutations.py — held-out ADVERSE. Exactitude (type de mutation + effet via code génétique
standard) + soundness : base non-ADN / codon != 3 / vide / non-str / référence ambiguë ou STOP -> ValueError
(abstention, jamais deviné) + déterminisme. Croisé avec `genetique` pour vérifier la table partagée.
"""
import mutations as M
import genetique as G

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
    """True ssi fn(*a, **k) lève ValueError (abstention)."""
    try:
        fn(*a, **k)
        return False
    except ValueError:
        return True
    except Exception:
        return False


# 1) TYPE DE MUTATION — substitution (même longueur, 1 diff). Held-out varié.
check(M.type_mutation("ATG", "ATA") == "substitution", "ATG->ATA substitution")
check(M.type_mutation("GGCCAATT", "GGCCAATA") == "substitution", "1 diff en fin -> substitution")
check(M.type_mutation("A", "C") == "substitution", "A->C substitution (1 base)")
check(M.type_mutation("atgc", "atgg") == "substitution", "casse minuscule -> substitution")
check(M.type_mutation("AT GC", "ATGA") == "substitution", "espaces ignorés -> substitution")

# 2) INSERTION (mutée plus longue) / DELETION (mutée plus courte).
check(M.type_mutation("ATG", "ATGG") == "insertion", "ATG->ATGG insertion")
check(M.type_mutation("ATGAAA", "ATGAAATTT") == "insertion", "+3 bases -> insertion")
check(M.type_mutation("A", "ACGT") == "insertion", "1->4 insertion")
check(M.type_mutation("ATGG", "ATG") == "deletion", "ATGG->ATG deletion")
check(M.type_mutation("ATGCC", "ATG") == "deletion", "-2 bases -> deletion")
check(M.type_mutation("ACGT", "A") == "deletion", "4->1 deletion")

# 3) EFFET D'UNE SUBSTITUTION DE CODON — silencieuse (même acide aminé).
check(M.effet_substitution_codon("ATG", "ATG") == "silencieuse", "ATG->ATG silencieuse (Met=Met)")
for cr, cm in [("TTT", "TTC"), ("AAA", "AAG"), ("GCT", "GCC"), ("CGT", "CGC"), ("CTA", "CTG")]:
    check(M.effet_substitution_codon(cr, cm) == "silencieuse",
          f"{cr}->{cm} silencieuse (synonyme {G.CODE[cr]})")

# 4) EFFET — faux-sens (acide aminé différent, non-STOP).
check(M.effet_substitution_codon("ATG", "ATA") == "faux_sens", "ATG->ATA faux_sens (Met->Ile)")
for cr, cm in [("GGT", "GAT"), ("ATG", "ACG"), ("TTT", "TTA"), ("AAA", "GAA")]:
    check(M.effet_substitution_codon(cr, cm) == "faux_sens",
          f"{cr}->{cm} faux_sens ({G.CODE[cr]}->{G.CODE[cm]})")

# 5) EFFET — non-sens (codon muté STOP).
check(M.effet_substitution_codon("TAC", "TAA") == "non_sens", "TAC->TAA non_sens (Tyr->stop)")
for cr, cm in [("TGG", "TGA"), ("CAA", "TAA"), ("GAA", "TAA"), ("TAT", "TAG")]:
    check(M.effet_substitution_codon(cr, cm) == "non_sens",
          f"{cr}->{cm} non_sens ({G.CODE[cr]}->stop)")

# 6) decrit_substitution renvoie (effet, aa_ref, aa_mut) cohérents.
check(M.decrit_substitution("TAC", "TAA") == ("non_sens", "Y", "*"), "décrit TAC->TAA")
check(M.decrit_substitution("ATG", "ATA") == ("faux_sens", "M", "I"), "décrit ATG->ATA")
check(M.decrit_substitution("ATG", "ATG") == ("silencieuse", "M", "M"), "décrit ATG->ATG")

# 7) SOUNDNESS — base non-ADN (hors ACGT) -> ValueError. U (ARN) refusé : on impose l'ADN.
for bad in ["ATX", "AUG", "AT-G", "AT1", "N", "AT GC!"]:
    check(leve_v(M.type_mutation, bad, "ATGC"), f"type base non-ADN {bad!r} -> ValueError")
    check(leve_v(M.type_mutation, "ATGC", bad), f"type mut base non-ADN {bad!r} -> ValueError")
check(leve_v(M.effet_substitution_codon, "ATX", "ATG"), "effet base non-ADN -> ValueError")
check(leve_v(M.effet_substitution_codon, "AUG", "AUA"), "effet codon ARN (U) -> ValueError")

# 8) SOUNDNESS — codon de longueur != 3 -> ValueError.
for bad in ["AT", "ATGG", "A", "", "ATGCAT"]:
    check(leve_v(M.effet_substitution_codon, bad, "ATG"), f"codon ref longueur {len(bad)} -> ValueError")
    check(leve_v(M.effet_substitution_codon, "ATG", bad), f"codon mut longueur {len(bad)} -> ValueError")

# 9) SOUNDNESS — séquence vide / non-str -> ValueError.
for bad in ["", "   "]:
    check(leve_v(M.type_mutation, bad, "ATG"), f"séquence vide {bad!r} -> ValueError")
for bad in [None, 123, ["ATG"], 3.14, ("A", "T")]:
    check(leve_v(M.type_mutation, bad, "ATG"), f"type non-str {bad!r} -> ValueError")
    check(leve_v(M.effet_substitution_codon, bad, "ATG"), f"effet non-str {bad!r} -> ValueError")

# 10) SOUNDNESS — abstention sur l'AMBIGU (FAUX=0 : ne jamais deviner).
check(leve_v(M.type_mutation, "ATG", "ATG"), "séquences identiques (0 diff) -> ValueError")
check(leve_v(M.type_mutation, "ATG", "ACA"), "même longueur 2 diffs -> ValueError")
check(leve_v(M.type_mutation, "AAAA", "CCCC"), "même longueur 4 diffs -> ValueError")
# référence STOP -> read-through hors des 3 catégories -> abstention.
for stop in ["TAA", "TAG", "TGA"]:
    check(leve_v(M.effet_substitution_codon, stop, "TAC"), f"ref STOP {stop} -> ValueError")
    check(leve_v(M.effet_substitution_codon, stop, stop), f"ref STOP {stop}->{stop} -> ValueError")

# 11) BALAYAGE SOUNDNESS table — pour TOUT codon sense, codon->lui-même = silencieuse ;
#     pour tout codon STOP en référence, abstention. (cohérence exhaustive avec la table partagée.)
for codon, aa in G.CODE.items():
    if aa == "*":
        check(leve_v(M.effet_substitution_codon, codon, "ATG"), f"ref STOP {codon} -> ValueError (balayage)")
    else:
        check(M.effet_substitution_codon(codon, codon) == "silencieuse",
              f"{codon}->{codon} silencieuse (balayage)")

# 12) COHÉRENCE avec genetique : l'effet correspond bien à la comparaison des traductions.
for cr in ["ATG", "GGT", "TAC", "TTT", "CAA"]:
    for cm in ["ATG", "GGT", "TAC", "TAA", "GAA", "AAA"]:
        try:
            effet = M.effet_substitution_codon(cr, cm)
        except ValueError:
            continue
        aa_r = G.CODE[cr]
        aa_m = G.CODE[cm]
        attendu = ("non_sens" if aa_m == "*" else "silencieuse" if aa_m == aa_r else "faux_sens")
        check(effet == attendu, f"cohérence {cr}->{cm} : {effet} == {attendu}")

# 13) DÉTERMINISME.
check(M.type_mutation("ATGAAA", "ATGAAATTT") == M.type_mutation("ATGAAA", "ATGAAATTT"),
      "déterminisme type_mutation")
check(M.effet_substitution_codon("TAC", "TAA") == M.effet_substitution_codon("TAC", "TAA"),
      "déterminisme effet_substitution_codon")

print(f"\n=== valide_mutations : {ok}/{ok+ko} ===")
import sys
sys.exit(0 if ko == 0 else 1)
