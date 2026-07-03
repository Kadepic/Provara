"""VALIDE bioinfo.py — held-out ADVERSE, FAUX=0. Ancres EXTERNES (cas comptés/dérivés à la main : Hamming, contenu
GC, reverse complement, Levenshtein) NON recalculées par la même expression + SOUNDNESS : entrée invalide ->
ValueError (jamais faux) + déterminisme.
"""
import bioinfo as M

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
    try:
        fn(*a)
        return False
    except ValueError:
        return True
    except Exception:
        return False


# ── HAMMING — comptes à la main ──
# GATTACA / GACTATA : positions 3 (T/C) et 6 (C/T) diffèrent -> 2.
check(M.distance_hamming("GATTACA", "GACTATA") == 2, "hamming GATTACA/GACTATA = 2")
check(M.distance_hamming("AAAA", "AAAA") == 0, "hamming identiques = 0")
check(M.distance_hamming("AAAA", "TTTT") == 4, "hamming tout différent = 4")
check(M.distance_hamming("", "") == 0, "hamming chaînes vides = 0")
check(M.distance_hamming("AGGCTTA", "AGGCATA") == 1, "hamming une substitution = 1")
# Hamming est général (pas restreint à l'ADN) :
check(M.distance_hamming("karolin", "kathrin") == 3, "hamming exemple classique karolin/kathrin = 3")

# ── TAUX GC ──
check(M.taux_gc("GGCC") == 1.0, "GC GGCC = 1.0")
check(M.taux_gc("ATAT") == 0.0, "GC ATAT = 0.0")
check(abs(M.taux_gc("GATTACA") - 2 / 7) < 1e-12, "GC GATTACA = 2/7 (G,C)")
check(M.taux_gc("ACGT") == 0.5, "GC ACGT = 0.5")
check(M.taux_gc("ggcc") == 1.0, "GC minuscules acceptées = 1.0")

# ── COMPLÉMENT INVERSE (reverse complement) ──
check(M.complement_inverse("GATTACA") == "TGTAATC", "revcomp GATTACA = TGTAATC")
check(M.complement_inverse("ATGC") == "GCAT", "revcomp ATGC = GCAT")
check(M.complement_inverse("AAAA") == "TTTT", "revcomp AAAA = TTTT")
check(M.complement_inverse("") == "", "revcomp vide = vide")
# Involutivité : revcomp(revcomp(x)) == x (vérité structurelle, ancre non triviale).
check(M.complement_inverse(M.complement_inverse("GATTACAGGC")) == "GATTACAGGC", "revcomp involutif")

# ── DISTANCE D'ÉDITION (Levenshtein) ──
check(M.distance_edition("chat", "chats") == 1, "edit chat/chats = 1 (insertion)")
check(M.distance_edition("chat", "chien") == 3, "edit chat/chien = 3 (calculé à la main)")
check(M.distance_edition("", "abc") == 3, "edit ''/abc = 3")
check(M.distance_edition("abc", "") == 3, "edit abc/'' = 3")
check(M.distance_edition("abc", "abc") == 0, "edit identiques = 0")
check(M.distance_edition("kitten", "sitting") == 3, "edit kitten/sitting = 3 (exemple canonique)")
check(M.distance_edition("flaw", "lawn") == 2, "edit flaw/lawn = 2 (exemple canonique)")
# Symétrie de Levenshtein :
check(M.distance_edition("chien", "chat") == M.distance_edition("chat", "chien"), "edit symétrique")

# ── SOUNDNESS — entrée invalide -> ValueError (jamais faux) ──
check(leve(M.distance_hamming, "ABC", "AB"), "hamming longueurs différentes -> ValueError")
check(leve(M.distance_hamming, "ABCDE", "ABCDEF"), "hamming longueurs différentes (2) -> ValueError")
check(leve(M.distance_hamming, 123, "ABC"), "hamming type non-str -> ValueError")
check(leve(M.taux_gc, "ATBX"), "taux_gc base invalide -> ValueError")
check(leve(M.taux_gc, "ACGU"), "taux_gc U (ARN) hors ADN -> ValueError")
check(leve(M.taux_gc, ""), "taux_gc séquence vide -> ValueError")
check(leve(M.taux_gc, "AC GT"), "taux_gc espace invalide -> ValueError")
check(leve(M.taux_gc, 42), "taux_gc type non-str -> ValueError")
check(leve(M.complement_inverse, "ATXC"), "complement_inverse base invalide -> ValueError")
check(leve(M.complement_inverse, None), "complement_inverse type non-str -> ValueError")
check(leve(M.distance_edition, "abc", 5), "edit type non-str -> ValueError")

# ── DÉTERMINISME ──
check(M.distance_edition("kitten", "sitting") == M.distance_edition("kitten", "sitting"), "déterminisme edit")
check(M.complement_inverse("GATTACA") == M.complement_inverse("GATTACA"), "déterminisme revcomp")

print(f"\n=== valide_bioinfo : {ok}/{ok + ko} ===")
import sys
sys.exit(0 if ko == 0 else 1)
