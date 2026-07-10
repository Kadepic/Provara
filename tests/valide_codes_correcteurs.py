"""
VALIDE codes_correcteurs.py — held-out ADVERSE.

ANCRES EXTERNES NON CIRCULAIRES (valeurs connues INDÉPENDAMMENT des formules testées) :
  • d(0000, 1111) = 4 : les 4 positions diffèrent (comptage à la main).
  • Hamming(7,4) a d_min = 3 -> détecte 2 erreurs, corrige 1 (fait classique de la théorie des codes).
  • encode("1011") = "0110011" : l'exemple canonique du code de Hamming(7,4) (p1=0, p2=1, p3=0,
    parités calculées À LA MAIN : p1=1⊕0⊕1=0, p2=1⊕1⊕1=1, p3=0⊕1⊕1=0) ; "0000"->"0000000", "1111"->"1111111".
  • ANCRE FORTE EN BOUCLE FERMÉE : pour CHACUN des 16 mots de 4 bits, encoder puis injecter UNE erreur à
    CHACUNE des 7 positions puis corriger redonne EXACTEMENT le codeword d'origine (16×7 = 112 cas).
  • DEUX erreurs -> la correction ÉCHOUE (comportement ATTENDU d'un code de distance 3 : la gate documente
    que le module ne prétend PAS corriger 2 erreurs).
  • Code de répétition {000, 111} : d = 3 (comptage à la main), corrige 1 ; Singleton 3 = 3−1+1 -> MDS.
  • MDS BINAIRES = familles TRIVIALES uniquement ([n,n,1], [n,n−1,2], [n,1,n]) : théorème classique
    (MacWilliams & Sloane, The Theory of Error-Correcting Codes, ch. 11, vrai même en non linéaire).
    Ancres indépendantes : le MEILLEUR [7,4] binaire est le Hamming(7,4) avec d = 3 (fait classique ;
    A(7,4) = 8 < 16 = 2^4, table classique), donc AUCUN [7,4,4] binaire n'existe -> est_mds(7,4,4) DOIT
    être False ; idem (23,12,12) (le meilleur [23,12] binaire est le Golay avec d = 7) et (10,5,6)
    (A(10,6) = 6 < 32 = 2^5, table classique : aucun code binaire de longueur 10 et distance 6
    n'a 32 mots).
  • Parité (4,3) : les 8 mots pairs de 4 bits ont d_min = 2 -> détecte 1, corrige 0.
  • Borne de Hamming : Hamming(7,4,t=1) PARFAIT (2⁴·8 = 128 = 2⁷) ; Golay(23,12,t=3) PARFAIT
    (2¹²·2048 = 2²³, car 1+23+253+1771 = 2048, somme faite à la main) ; (7,5,t=1) IMPOSSIBLE (256 > 128).

SOUNDNESS : longueurs différentes, alphabet non binaire, mot vide, < 2 mots, code vide, duplicats,
bool/str/float/NaN/inf, k > n, d > n, t < 0 -> ValueError. DÉTERMINISME : double appel identique.
"""
import codes_correcteurs as C

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


# ── 1) ANCRE : distance de Hamming, valeurs comptées à la main ──
check(C.distance_hamming("0000", "1111") == 4, "d(0000,1111) = 4 (ancre imposée)")
check(C.distance_hamming("0000", "0000") == 0, "d(u,u) = 0")
check(C.distance_hamming("1011101", "1001001") == 2, "d(1011101,1001001) = 2 (positions 3 et 5, à la main)")
check(C.distance_hamming("0", "1") == 1, "d(0,1) = 1")
check(C.distance_hamming("10", "01") == 2, "d(10,01) = 2")
# symétrie (axiome de métrique)
check(C.distance_hamming("110", "011") == C.distance_hamming("011", "110"), "symétrie d(u,v)=d(v,u)")

# ── 2) ANCRE : encodage Hamming(7,4), exemples canoniques calculés à la main ──
check(C.hamming74_encode("1011") == "0110011", "encode(1011) = 0110011 (exemple canonique)")
check(C.hamming74_encode("0000") == "0000000", "encode(0000) = 0000000 (code linéaire : 0 -> 0)")
check(C.hamming74_encode("1111") == "1111111", "encode(1111) = 1111111 (mot tout-un)")
# 1000 : d1=1,d2=0,d3=0,d4=0 -> p1=1,p2=1,p3=0 -> 1 1 1 0 0 0 0
check(C.hamming74_encode("1000") == "1110000", "encode(1000) = 1110000 (parités à la main)")
# 0001 : p1=0⊕0⊕1=1, p2=0⊕0⊕1=1, p3=0⊕0⊕1=1 -> 1 1 0 1 0 0 1
check(C.hamming74_encode("0001") == "1101001", "encode(0001) = 1101001 (parités à la main)")

# ── 3) ANCRE : d_min de Hamming(7,4) = 3 (fait classique), sur les 16 codewords exhaustifs ──
tous_les_mots4 = [f"{i:04b}" for i in range(16)]
codewords = [C.hamming74_encode(m) for m in tous_les_mots4]
check(len(set(codewords)) == 16, "les 16 codewords sont distincts (encodage injectif)")
check(C.distance_minimale(codewords) == 3, "d_min(Hamming(7,4)) = 3 (fait classique)")
check(C.detecte_jusqu_a(3) == 2, "d=3 -> détecte 2 erreurs (théorème d−1)")
check(C.corrige_jusqu_a(3) == 1, "d=3 -> corrige 1 erreur (théorème ⌊(d−1)/2⌋)")

# ── 4) SYNDROME : position de l'erreur = valeur du syndrome (construction canonique) ──
mot_sain = "0110011"                                # codeword de 1011
check(C.hamming74_syndrome(mot_sain) == 0, "syndrome(codeword) = 0 (aucune erreur)")
for pos in range(1, 8):
    b = list(mot_sain)
    b[pos - 1] = "1" if b[pos - 1] == "0" else "0"
    check(C.hamming74_syndrome("".join(b)) == pos,
          f"syndrome(erreur en position {pos}) = {pos}")

# ── 5) ANCRE FORTE EN BOUCLE FERMÉE : 16 mots × 7 positions = 112 cas, correction exacte ──
for m4 in tous_les_mots4:
    cw = C.hamming74_encode(m4)
    for pos in range(1, 8):
        b = list(cw)
        b[pos - 1] = "1" if b[pos - 1] == "0" else "0"
        corrige = C.hamming74_corrige("".join(b))
        check(corrige == cw and C.hamming74_extrait(corrige) == m4,
              f"boucle fermée : {m4} + erreur pos {pos} -> corrigé = codeword d'origine")

# codeword intact : la correction ne touche rien
check(C.hamming74_corrige(mot_sain) == mot_sain, "corrige(codeword sain) = identité")
check(C.hamming74_extrait("0110011") == "1011", "extrait(0110011) = 1011 (données aux positions 3,5,6,7)")

# ── 6) DEUX ERREURS : la correction ÉCHOUE — comportement ATTENDU d'un code de distance 3 ──
# On documente : le module ne prétend JAMAIS corriger 2 erreurs (corrige_jusqu_a(3) = 1).
for m4 in ("1011", "0000", "0110"):
    cw = C.hamming74_encode(m4)
    rates = 0
    total = 0
    for p1 in range(1, 8):
        for p2 in range(p1 + 1, 8):
            b = list(cw)
            b[p1 - 1] = "1" if b[p1 - 1] == "0" else "0"
            b[p2 - 1] = "1" if b[p2 - 1] == "0" else "0"
            if C.hamming74_corrige("".join(b)) != cw:
                rates += 1
            total += 1
    check(rates == total == 21,
          f"2 erreurs sur {m4} : les 21 doubles erreurs sont TOUTES mal corrigées (limite d=3, documentée)")

# ── 7) CODE DE RÉPÉTITION {000, 111} : d = 3 (à la main), corrige 1, MDS ──
check(C.distance_minimale(["000", "111"]) == 3, "répétition (3,1) : d = 3")
check(C.detecte_jusqu_a(3) == 2, "répétition : détecte 2")
check(C.corrige_jusqu_a(3) == 1, "répétition : corrige 1")
check(C.verifie_singleton(3, 1, 3) is True, "Singleton : 3 <= 3−1+1")
check(C.est_mds(3, 1, 3) is True, "répétition (3,1,3) : d = n−k+1 -> MDS (ancre imposée)")

# ── 8) PARITÉ (4,3) : 8 mots pairs de 4 bits, d = 2, détecte 1, corrige 0 ──
mots_pairs = [f"{i:04b}" for i in range(16) if f"{i:04b}".count("1") % 2 == 0]
check(len(mots_pairs) == 8, "code de parité (4,3) : 8 mots de poids pair")
check(C.distance_minimale(mots_pairs) == 2, "parité (4,3) : d = 2 (ancre imposée)")
check(C.detecte_jusqu_a(2) == 1, "parité : détecte 1")
check(C.corrige_jusqu_a(2) == 0, "parité : corrige 0")
check(C.bit_parite("101") == "0", "bit_parite(101) = 0 (poids 2, déjà pair)")
check(C.bit_parite("111") == "1", "bit_parite(111) = 1 (poids 3, impair)")
check(C.bit_parite("0000") == "0", "bit_parite(0000) = 0")
check(C.detecte_parite("1010") is False, "poids pair : aucune erreur détectée")
check(C.detecte_parite("1011") is True, "poids impair : erreur DÉTECTÉE")
# mot + son bit de parité est toujours de poids pair (propriété, second chemin : comptage direct)
for m in ("1", "10", "1101", "0111011"):
    etendu = m + C.bit_parite(m)
    check(etendu.count("1") % 2 == 0, f"{m} + bit_parite est de poids pair")
    check(C.detecte_parite(etendu) is False, f"{m} + bit_parite : rien à détecter")

# ── 9) BORNE DE SINGLETON : d <= n − k + 1, MDS ssi égalité ──
check(C.verifie_singleton(7, 4, 3) is True, "Hamming(7,4,3) : 3 <= 7−4+1 = 4")
check(C.est_mds(7, 4, 3) is False, "Hamming(7,4,3) : 3 < 4 -> PAS MDS")
check(C.verifie_singleton(4, 3, 2) is True, "parité (4,3,2) : 2 <= 4−3+1 = 2")
check(C.est_mds(4, 3, 2) is True, "parité (4,3,2) : 2 = 2 -> MDS (les codes de parité sont MDS)")
check(C.verifie_singleton(5, 2, 5) is False, "(5,2,5) : 5 > 5−2+1 = 4 -> Singleton VIOLÉE")
check(leve(C.est_mds, 5, 2, 5), "est_mds sur Singleton violée -> ValueError (code impossible)")
check(C.verifie_singleton(7, 7, 1) is True, "(7,7,1) : code trivial, 1 <= 1")
check(C.est_mds(7, 7, 1) is True, "(7,7,1) : d = n−k+1 = 1 -> MDS trivial")

# ── 9bis) MDS BINAIRES : l'égalité de Singleton NE SUFFIT PAS sur GF(2) (théorème de trivialité) ──
# Ancre : le meilleur [7,4] binaire est le Hamming(7,4), d = 3 ; A(7,4) = 8 < 2^4 (table classique).
check(C.verifie_singleton(7, 4, 4) is True, "(7,4,4) : 4 <= 4, Singleton non violée (paramétrique)")
check(C.est_mds(7, 4, 4) is False, "(7,4,4) : égalité de Singleton mais AUCUN [7,4,4] binaire -> PAS MDS")
# Ancre : le meilleur [23,12] binaire est le Golay, d = 7 (fait classique) — pas de [23,12,12].
check(C.est_mds(23, 12, 12) is False, "(23,12,12) : pas de [23,12,12] binaire (Golay : d = 7) -> PAS MDS")
# Ancre : A(10,6) = 6 < 32 = 2^5 (table classique) — pas de code binaire (10, 32, 6).
check(C.est_mds(10, 5, 6) is False, "(10,5,6) : A(10,6) = 6 < 2^5 -> PAS MDS")
# Les TROIS familles triviales, seules MDS binaires (MacWilliams & Sloane, ch. 11) :
check(C.est_mds(5, 5, 1) is True, "[5,5,1] espace entier : MDS binaire trivial")
check(C.est_mds(6, 5, 2) is True, "[6,5,2] parité : MDS binaire trivial")
check(C.est_mds(5, 1, 5) is True, "[5,1,5] répétition : MDS binaire trivial")
check(C.est_mds(1, 1, 1) is True, "[1,1,1] : cas dégénéré, les trois familles coïncident")
# Balayage adverse : pour 2 <= k <= n−2 et d = n−k+1 >= 3, JAMAIS MDS en binaire (théorème).
for n_ in range(4, 13):
    check(all(C.est_mds(n_, k_, n_ - k_ + 1) is False for k_ in range(2, n_ - 1)),
          f"n={n_} : aucune égalité de Singleton avec 2<=k<=n−2 n'est MDS en binaire")
# est_mds reste False sous l'égalité stricte (d < n−k+1), même pour de bons codes :
check(C.est_mds(23, 12, 7) is False, "Golay(23,12,7) : 7 < 12 -> PAS MDS (excellent code, pas MDS)")
check(C.est_mds(1, 1, 1) == C.est_mds(1, 1, 1) and C.est_mds(7, 4, 4) == C.est_mds(7, 4, 4),
      "déterminisme est_mds")

# ── 10) BORNE DE HAMMING (sphères) : 2^k · Σ C(n,i) <= 2^n ──
# Hamming(7,4), t=1 : 16 · (1+7) = 128 = 2^7 -> borne atteinte (code PARFAIT, fait classique)
check(C.verifie_hamming(7, 4, 1) is True, "Hamming(7,4,t=1) : 16·8 = 128 = 2^7 (parfait)")
check(C.verifie_hamming(7, 5, 1) is False, "(7,5,t=1) : 32·8 = 256 > 128 -> IMPOSSIBLE")
# répétition (3,1), t=1 : 2 · (1+3) = 8 = 2^3 -> parfait
check(C.verifie_hamming(3, 1, 1) is True, "répétition (3,1,t=1) : 2·4 = 8 = 2^3 (parfait)")
# Golay binaire (23,12), t=3 : 1+23+253+1771 = 2048 (somme à la main) ; 2^12·2048 = 2^23 -> parfait
check(C.verifie_hamming(23, 12, 3) is True, "Golay(23,12,t=3) : 2^12·2048 = 2^23 (parfait, fait classique)")
check(C.verifie_hamming(23, 13, 3) is False, "(23,13,t=3) : dépasse 2^23 -> IMPOSSIBLE")
check(C.verifie_hamming(7, 4, 0) is True, "t=0 : 16·1 <= 128, trivialement vrai")

# ── 11) SOUNDNESS — distance : longueurs, alphabet, vide, types ──
check(leve(C.distance_hamming, "000", "0000"), "longueurs différentes -> ValueError (ancre d'abstention)")
check(leve(C.distance_hamming, "012", "010"), "alphabet non binaire (2) -> ValueError")
check(leve(C.distance_hamming, "abc", "abc"), "alphabet non binaire (lettres) -> ValueError")
check(leve(C.distance_hamming, "", ""), "mot vide -> ValueError")
check(leve(C.distance_hamming, 101, "101"), "int au lieu de str -> ValueError")
check(leve(C.distance_hamming, True, "1"), "bool -> ValueError")
check(leve(C.distance_hamming, ["1", "0"], "10"), "liste au lieu de str -> ValueError")

# ── 12) SOUNDNESS — distance minimale : code vide, < 2 mots, duplicats, longueurs ──
check(leve(C.distance_minimale, []), "code vide -> ValueError")
check(leve(C.distance_minimale, ["101"]), "1 seul mot -> ValueError")
check(leve(C.distance_minimale, ["101", "101"]), "mots dupliqués (d=0) -> ValueError")
check(leve(C.distance_minimale, ["10", "101"]), "longueurs mixtes -> ValueError")
check(leve(C.distance_minimale, ["10", "1x"]), "alphabet non binaire dans le code -> ValueError")
check(leve(C.distance_minimale, "0011"), "chaîne au lieu de liste -> ValueError")

# ── 13) SOUNDNESS — capacités : d hors domaine ──
check(leve(C.detecte_jusqu_a, 0), "d=0 -> ValueError")
check(leve(C.detecte_jusqu_a, -3), "d<0 -> ValueError")
check(leve(C.detecte_jusqu_a, 2.0), "d flottant -> ValueError")
check(leve(C.detecte_jusqu_a, True), "d bool -> ValueError")
check(leve(C.corrige_jusqu_a, 0), "corrige d=0 -> ValueError")
check(leve(C.corrige_jusqu_a, "3"), "corrige d str -> ValueError")
check(leve(C.corrige_jusqu_a, float("nan")), "corrige d=NaN -> ValueError")
check(leve(C.corrige_jusqu_a, float("inf")), "corrige d=inf -> ValueError")

# ── 14) SOUNDNESS — Hamming(7,4) : longueurs et alphabet stricts ──
check(leve(C.hamming74_encode, "101"), "encode 3 bits -> ValueError")
check(leve(C.hamming74_encode, "10111"), "encode 5 bits -> ValueError")
check(leve(C.hamming74_encode, "10a1"), "encode alphabet invalide -> ValueError")
check(leve(C.hamming74_encode, 1011), "encode int -> ValueError")
check(leve(C.hamming74_syndrome, "011001"), "syndrome 6 bits -> ValueError")
check(leve(C.hamming74_syndrome, "01100112"), "syndrome 8 bits -> ValueError")
check(leve(C.hamming74_corrige, "0110"), "corrige 4 bits -> ValueError")
check(leve(C.hamming74_extrait, "1110011"), "extrait d'un mot ERRONÉ (syndrome≠0) -> ValueError")
check(leve(C.hamming74_extrait, "011"), "extrait 3 bits -> ValueError")

# ── 15) SOUNDNESS — parité ──
check(leve(C.bit_parite, ""), "bit_parite mot vide -> ValueError")
check(leve(C.bit_parite, "21"), "bit_parite alphabet invalide -> ValueError")
check(leve(C.detecte_parite, 7), "detecte_parite int -> ValueError")
check(leve(C.detecte_parite, ""), "detecte_parite mot vide -> ValueError")

# ── 16) SOUNDNESS — bornes : paramètres impossibles / types ──
check(leve(C.verifie_singleton, 3, 5, 1), "Singleton k > n -> ValueError")
check(leve(C.verifie_singleton, 3, 1, 4), "Singleton d > n -> ValueError")
check(leve(C.verifie_singleton, 0, 1, 1), "Singleton n=0 -> ValueError")
check(leve(C.verifie_singleton, 3.0, 1, 1), "Singleton n flottant -> ValueError")
check(leve(C.verifie_singleton, 3, True, 1), "Singleton k bool -> ValueError")
check(leve(C.verifie_hamming, 7, 8, 1), "Hamming k > n -> ValueError")
check(leve(C.verifie_hamming, 7, 4, -1), "Hamming t < 0 -> ValueError")
check(leve(C.verifie_hamming, 7, 4, 8), "Hamming t > n -> ValueError")
check(leve(C.verifie_hamming, 7, 4, 1.0), "Hamming t flottant -> ValueError")
check(leve(C.verifie_hamming, 7, 4, True), "Hamming t bool -> ValueError")
check(leve(C.verifie_hamming, float("inf"), 4, 1), "Hamming n=inf -> ValueError")

# ── 17) DÉTERMINISME : double appel identique ──
check(C.distance_hamming("0000", "1111") == C.distance_hamming("0000", "1111"), "déterminisme distance")
check(C.distance_minimale(codewords) == C.distance_minimale(codewords), "déterminisme d_min")
check(C.hamming74_encode("1011") == C.hamming74_encode("1011"), "déterminisme encode")
check(C.hamming74_corrige("1110011") == C.hamming74_corrige("1110011"), "déterminisme corrige")
check(C.verifie_hamming(23, 12, 3) == C.verifie_hamming(23, 12, 3), "déterminisme borne de Hamming")

print(f"\n=== valide_codes_correcteurs : {ok}/{ok+ko} ===")
import sys; sys.exit(0 if ko == 0 else 1)
