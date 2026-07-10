"""Gate adverse de `expression_genique` — ANCRES NON CIRCULAIRES (biologie moléculaire classique + calcul à
la main + boucle fermée reverse-complement involutive). Prouve : réplication (brin fille 5'->3'),
semi-conservative (Meselson-Stahl 100% hybride), matrice/codant, sens 5'->3' + Okazaki, dogme central.
Soundness (abstention sur bool/str/NaN/inf/vide/base illégale/len%3) + déterminisme."""
from __future__ import annotations

from fractions import Fraction

import expression_genique as eg

ok = 0
ko = 0


def check(cond, label):
    global ok, ko
    if cond:
        ok += 1
    else:
        ko += 1
        print(f"  FAIL: {label}")


def leve(fn, *a, **k) -> bool:
    """True ssi fn(*a) lève ValueError (abstention structurelle attendue)."""
    try:
        fn(*a, **k)
        return False
    except ValueError:
        return True
    except Exception:
        return False


# ── (a) RÉPLICATION : brin fille lu 5'->3' = reverse complement ──────────────────────────────────────────────
# ANCRE 1 (biologie classique) : complément de 'ATGC' = 'TACG' ; antiparallèle lu 5'->3' = 'GCAT'.
check(eg.replique("ATGC") == "GCAT", "replique(ATGC)==GCAT (reverse complement)")
# ANCRE 2 (à la main) : A->T ; 'AAAA' -> compl 'TTTT' -> inverse 'TTTT'.
check(eg.replique("AAAA") == "TTTT", "replique(AAAA)==TTTT")
# ANCRE 3 (à la main) : 'GATTACA' -> compl 'CTAATGT' -> inverse 'TGTAATC'.
check(eg.replique("GATTACA") == "TGTAATC", "replique(GATTACA)==TGTAATC")
# ANCRE 4 (à la main) : palindrome de restriction EcoRI 'GAATTC' est son propre reverse complement.
check(eg.replique("GAATTC") == "GAATTC", "replique(GAATTC)==GAATTC (palindrome EcoRI)")
# casse : entrée minuscule normalisée en majuscules.
check(eg.replique("atgc") == "GCAT", "replique insensible a la casse")

# ANCRE FORTE (boucle fermée) : replique(replique(x)) == x pour 50 brins pseudo-aléatoires DÉTERMINISTES.
_bases = "ACGT"
def _brin_pseudo(i: int) -> str:
    n = 4 + (i % 11)  # longueur 4..14
    return "".join(_bases[(i * 7 + j * 13 + 3) % 4] for j in range(n))

_involution_ok = True
for _i in range(50):
    _b = _brin_pseudo(_i)
    if eg.replique(eg.replique(_b)) != _b:
        _involution_ok = False
        break
check(_involution_ok, "replique(replique(x))==x pour 50 brins deterministes (involution)")
# et le brin pseudo est bien un ADN valide.
check(all(c in "ACGT" for c in _brin_pseudo(0)), "brin_pseudo(0) est un ADN valide")

# soundness replique
check(leve(eg.replique, ""), "replique('') -> ValueError")
check(leve(eg.replique, "ATBX"), "replique base illegale -> ValueError")
check(leve(eg.replique, "AUG"), "replique('AUG') U interdit en ADN -> ValueError")
check(leve(eg.replique, True), "replique(True) bool -> ValueError")
check(leve(eg.replique, 1234), "replique(int) -> ValueError")
check(leve(eg.replique, None), "replique(None) -> ValueError")
check(leve(eg.replique, ["A", "T"]), "replique(list) -> ValueError")
# déterminisme
check(eg.replique("ATGC") == eg.replique("ATGC"), "replique deterministe")


# ── (b) SEMI-CONSERVATIVE (Meselson & Stahl 1958) ────────────────────────────────────────────────────────────
_sc = eg.semi_conservative("ATGC")
# ANCRE : fraction hybride = 100% = 1/1 (Meselson-Stahl), et surtout PAS 1/2 (50/50 refuse).
check(_sc["fraction_hybride"] == Fraction(1, 1), "semi_conservative : 100% hybride (1/1)")
check(_sc["fraction_hybride"] != Fraction(1, 2), "semi_conservative : PAS 50/50")
check("Meselson" in _sc["source"], "semi_conservative cite Meselson & Stahl")
# ANCRE : brin parental 'ATGC' conserve, partenaire neosynthetise 'GCAT'.
check(_sc["duplex_1"]["parental"] == "ATGC", "duplex_1 parental == ATGC (conserve)")
check(_sc["duplex_1"]["neosynthetise"] == "GCAT", "duplex_1 neosynthetise == GCAT")
check(_sc["duplex_2"]["parental"] == "GCAT", "duplex_2 parental == GCAT")
check(_sc["duplex_2"]["neosynthetise"] == "ATGC", "duplex_2 neosynthetise == ATGC")
# chaque duplex est HYBRIDE : un brin parental + un brin neosynthetise DISTINCTS.
check(_sc["duplex_1"]["parental"] != _sc["duplex_1"]["neosynthetise"], "duplex_1 est hybride (2 brins distincts)")
check("100%" in _sc["commentaire"] and "50/50" in _sc["commentaire"], "commentaire dit 100% et refute 50/50")
# soundness
check(leve(eg.semi_conservative, ""), "semi_conservative('') -> ValueError")
check(leve(eg.semi_conservative, "ATBX"), "semi_conservative base illegale -> ValueError")
check(leve(eg.semi_conservative, False), "semi_conservative(bool) -> ValueError")
check(eg.semi_conservative("ATGC") == eg.semi_conservative("ATGC"), "semi_conservative deterministe")


# ── (c) BRIN CODANT / BRIN MATRICE ───────────────────────────────────────────────────────────────────────────
# ANCRE : ARNm 'AUG' (START) -> brin codant 'ATG' (U->T) -> brin matrice 'TAC' (complement, 3'->5').
check(eg.brin_codant("AUG") == "ATG", "brin_codant(AUG)==ATG")
check(eg.brin_matrice("AUG") == "TAC", "brin_matrice(AUG)==TAC (complement, 3'->5')")
# ANCRE (a la main) : 'AUGGCUUAA' -> codant 'ATGGCTTAA' -> matrice compl 'TACCGAATT'.
check(eg.brin_codant("AUGGCUUAA") == "ATGGCTTAA", "brin_codant(AUGGCUUAA)==ATGGCTTAA")
check(eg.brin_matrice("AUGGCUUAA") == "TACCGAATT", "brin_matrice(AUGGCUUAA)==TACCGAATT")
# cohérence : le brin codant, transcrit, redonne l'ARNm (second chemin de code via genetique).
import genetique as _gen
check(_gen.transcrit(eg.brin_codant("AUGGCUUAA"))[1] == "AUGGCUUAA", "transcrit(brin_codant)==ARNm (round-trip)")
# soundness : T interdit en ARN, vide, bool, non-str.
check(leve(eg.brin_codant, "ATG"), "brin_codant('ATG') T interdit en ARN -> ValueError")
check(leve(eg.brin_codant, ""), "brin_codant('') -> ValueError")
check(leve(eg.brin_codant, True), "brin_codant(bool) -> ValueError")
check(leve(eg.brin_matrice, "AXG"), "brin_matrice base illegale -> ValueError")
check(leve(eg.brin_matrice, "ATG"), "brin_matrice('ATG') T interdit -> ValueError")
check(leve(eg.brin_matrice, None), "brin_matrice(None) -> ValueError")
check(eg.brin_matrice("AUG") == eg.brin_matrice("AUG"), "brin_matrice deterministe")


# ── (d) SENS DE SYNTHÈSE + FRAGMENTS D'OKAZAKI ───────────────────────────────────────────────────────────────
check(eg.SENS == "5'->3'", "SENS == 5'->3'")
check("5'->3'" in eg.sens_synthese(), "sens_synthese cite 5'->3'")
check("TOUJOURS" in eg.sens_synthese(), "sens_synthese dit TOUJOURS")
_ok_ = eg.fragments_okazaki("ATGC")
check(_ok_["sens_polymerase"] == "5'->3'", "fragments_okazaki : sens 5'->3'")
check("Okazaki" in _ok_["brin_retarde_discontinu"]["synthese"], "brin retarde = fragments d'Okazaki")
check(_ok_["brin_meneur_continu"]["synthese"] == "continue", "brin meneur = synthese continue")
check("Okazaki" in _ok_["reponse"], "reponse cite Okazaki")
check("RETARDE" in _ok_["reponse"], "reponse designe le brin retarde comme discontinu")
# exactement un continu, un discontinu (fait structurel) : les deux matrices sont complementaires.
check(eg.replique(_ok_["brin_meneur_continu"]["matrice"]) == _ok_["brin_retarde_discontinu"]["matrice"],
      "les deux matrices sont complementaires antiparalleles")
check(leve(eg.fragments_okazaki, ""), "fragments_okazaki('') -> ValueError")
check(leve(eg.fragments_okazaki, "ATBX"), "fragments_okazaki base illegale -> ValueError")
check(leve(eg.fragments_okazaki, 3.14), "fragments_okazaki(float) -> ValueError")
check(eg.fragments_okazaki("ATGC") == eg.fragments_okazaki("ATGC"), "fragments_okazaki deterministe")


# ── (e) DOGME CENTRAL ────────────────────────────────────────────────────────────────────────────────────────
# ANCRE MAITRESSE : dogme_central('ATGGCTTAA') -> peptide 'Met-Ala' puis STOP.
_d = eg.dogme_central("ATGGCTTAA")
check(_d["peptide"] == "Met-Ala", "dogme_central(ATGGCTTAA) peptide == Met-Ala")
check(_d["proteine_1lettre"] == "MA", "dogme_central proteine 1-lettre == MA")
check(_d["stop_rencontre"] is True, "dogme_central : STOP rencontre")
# ANCRE : transcription ATG->AUG (codon START).
check(_d["arnm"] == "AUGGCUUAA", "dogme_central arnm == AUGGCUUAA (T->U)")
# ANCRE : replication -> brin fille = reverse complement de ATGGCTTAA = TTAAGCCAT.
check(_d["brin_fille_5_3"] == "TTAAGCCAT", "dogme_central brin_fille == TTAAGCCAT (reverse complement)")
# ANCRE : les 3 codons STOP UAA/UAG/UGA arretent la traduction (ADN TAA/TAG/TGA).
for _stop_dna in ("TAA", "TAG", "TGA"):
    _ds = eg.dogme_central("ATG" + _stop_dna)
    check(_ds["proteine_1lettre"] == "M" and _ds["peptide"] == "Met",
          f"dogme_central(ATG{_stop_dna}) -> Met puis STOP")
# sans stop : pas de stop_rencontre.
_d2 = eg.dogme_central("ATGGCT")  # Met-Ala, pas de stop
check(_d2["peptide"] == "Met-Ala" and _d2["stop_rencontre"] is False, "dogme_central sans stop : Met-Ala, stop=False")
# soundness : base illegale, len%3, vide, bool, non-str.
check(leve(eg.dogme_central, "ATGG"), "dogme_central len%3!=0 -> ValueError")
check(leve(eg.dogme_central, "ATBXAA"), "dogme_central base illegale -> ValueError")
check(leve(eg.dogme_central, ""), "dogme_central('') -> ValueError")
check(leve(eg.dogme_central, True), "dogme_central(bool) -> ValueError")
check(leve(eg.dogme_central, 42), "dogme_central(int) -> ValueError")
check(eg.dogme_central("ATGGCTTAA") == eg.dogme_central("ATGGCTTAA"), "dogme_central deterministe")


print(f"\n=== valide_expression_genique : {ok}/{ok+ko} ===")
import sys; sys.exit(0 if ko == 0 else 1)
