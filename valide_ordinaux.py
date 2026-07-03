"""VALIDE ordinaux.py — ADVERSE, FAUX=0. Ancres connues (arithmétique ordinale non commutative, Cantor) +
soundness (ordinal mal formé / comparaison indécidable dans ZFC -> ValueError) + déterminisme."""
import ordinaux as M

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


# raccourcis
Z = M.ZERO
w = M.OMEGA                       # ω
un = M.fini(1)
deux = M.fini(2)
trois = M.fini(3)
w1 = M.addition_ordinale(w, un)  # ω+1
w2 = M.multiplication_ordinale(w, deux)   # ω·2
wc = M.omega_puissance(2)        # ω²

# ── ADDITION ORDINALE (non commutative) ──
check(M.addition_ordinale(un, w) == w, "1 + ω = ω (absorption à gauche)")
check(M.addition_ordinale(M.fini(5), w) == w, "5 + ω = ω")
check(M.addition_ordinale(w, un) == ((1, 1), (0, 1)), "ω + 1 = ω+1")
check(M.addition_ordinale(w, un) != w, "ω + 1 ≠ ω")
check(M.addition_ordinale(w, w) == ((1, 2),), "ω + ω = ω·2")
check(M.addition_ordinale(w, Z) == w, "ω + 0 = ω")
check(M.addition_ordinale(Z, w) == w, "0 + ω = ω")
check(M.addition_ordinale(w1, w) == w2, "(ω+1) + ω = ω·2")
check(M.addition_ordinale(wc, w) == ((2, 1), (1, 1)), "ω² + ω = ω²+ω")
check(M.addition_ordinale(wc, un) == ((2, 1), (0, 1)), "ω² + 1 = ω²+1")
check(M.addition_ordinale(((1, 2),), ((1, 3),)) == ((1, 5),), "ω·2 + ω·3 = ω·5")
# associativité (vraie pour l'addition ordinale)
A, B, C = w, un, w
check(M.addition_ordinale(M.addition_ordinale(A, B), C)
      == M.addition_ordinale(A, M.addition_ordinale(B, C)), "associativité (ω+1)+ω = ω+(1+ω)")

# ── MULTIPLICATION ORDINALE (non commutative) ──
check(M.multiplication_ordinale(deux, w) == w, "2·ω = ω (limite)")
check(M.multiplication_ordinale(w, deux) == ((1, 2),), "ω·2 = ω+ω")
check(M.multiplication_ordinale(deux, w) != M.multiplication_ordinale(w, deux), "2·ω ≠ ω·2 (non commutatif)")
check(M.multiplication_ordinale(w, w) == wc, "ω·ω = ω²")
check(M.multiplication_ordinale(w1, w) == wc, "(ω+1)·ω = ω² (terme inférieur absorbé)")
check(M.multiplication_ordinale(w, w1) == ((2, 1), (1, 1)), "ω·(ω+1) = ω²+ω")
check(M.multiplication_ordinale(w1, deux) == ((1, 2), (0, 1)), "(ω+1)·2 = ω·2+1")
check(M.multiplication_ordinale(deux, trois) == ((0, 6),), "2·3 = 6 (fini)")
check(M.multiplication_ordinale(w, un) == w, "ω·1 = ω")
check(M.multiplication_ordinale(un, w) == w, "1·ω = ω")
check(M.multiplication_ordinale(w, Z) == Z, "ω·0 = 0")
check(M.multiplication_ordinale(Z, w) == Z, "0·ω = 0")
check(M.multiplication_ordinale(wc, w) == ((3, 1),), "ω²·ω = ω³")
check(M.multiplication_ordinale(w, wc) == ((3, 1),), "ω·ω² = ω³")
# distributivité À GAUCHE (vraie) vs À DROITE (fausse)
check(M.multiplication_ordinale(w, M.addition_ordinale(deux, trois))
      == M.addition_ordinale(M.multiplication_ordinale(w, deux), M.multiplication_ordinale(w, trois)),
      "distributivité à gauche : ω·(2+3) = ω·2 + ω·3")
check(M.multiplication_ordinale(M.addition_ordinale(un, un), w)
      != M.addition_ordinale(M.multiplication_ordinale(un, w), M.multiplication_ordinale(un, w)),
      "PAS de distributivité à droite : (1+1)·ω = ω ≠ ω·2 = 1·ω+1·ω")
check(M.multiplication_ordinale(deux, M.multiplication_ordinale(wc, M.addition_ordinale(w, trois)))
      == M.multiplication_ordinale(M.multiplication_ordinale(deux, wc), M.addition_ordinale(w, trois)),
      "associativité du produit (échantillon)")

# ── COMPARAISON ──
check(M.compare_ordinaux(w, w1) == -1, "ω < ω+1")
check(M.compare_ordinaux(w1, w2) == -1, "ω+1 < ω·2")
check(M.compare_ordinaux(w2, wc) == -1, "ω·2 < ω²")
check(M.compare_ordinaux(w, wc) == -1, "ω < ω²")
check(M.compare_ordinaux(((1, 100),), wc) == -1, "ω·100 < ω²")
check(M.compare_ordinaux(w1, M.addition_ordinale(w, deux)) == -1, "ω+1 < ω+2")
check(M.compare_ordinaux(M.fini(5), w) == -1, "5 < ω")
check(M.compare_ordinaux(trois, M.fini(5)) == -1, "3 < 5 (fini)")
check(M.compare_ordinaux(w, w) == 0, "ω = ω")
check(M.compare_ordinaux(w1, w1) == 0, "ω+1 = ω+1")
check(M.compare_ordinaux(w1, w) == 1, "ω+1 > ω")
# antisymétrie / trichotomie
for x, y in [(w, w1), (w2, wc), (M.fini(5), w), (w1, w1)]:
    check(M.compare_ordinaux(x, y) == -M.compare_ordinaux(y, x), f"antisymétrie compare({M.ecrit(x)},{M.ecrit(y)})")

# ── PRÉDICATS ORDINAUX ──
check(M.est_fini(M.fini(5)) and M.est_fini(Z) and not M.est_fini(w), "est_fini : 5,0 oui ; ω non")
check(M.est_limite(w) and M.est_limite(w2) and M.est_limite(wc), "est_limite : ω, ω·2, ω² oui")
check(not M.est_limite(w1) and not M.est_limite(Z) and not M.est_limite(trois), "est_limite : ω+1, 0, 3 non")
check(M.est_successeur(w1) and not M.est_successeur(w), "est_successeur : ω+1 oui ; ω non")

# ── DÉNOMBRABILITÉ ──
check(M.est_denombrable(w) and M.est_denombrable(w1) and M.est_denombrable(w2) and M.est_denombrable(wc),
      "ω, ω+1, ω·2, ω² dénombrables")

# ── CARDINAUX ──
check(M.cardinal_aleph(0) == "aleph_0", "cardinal_aleph(0) = aleph_0")
check(M.cardinal_aleph(1) == "aleph_1", "cardinal_aleph(1) = aleph_1")
check(M.cardinal_aleph(7) == "aleph_7", "cardinal_aleph(7) = aleph_7")
check(M.cardinal_continu() == "2^aleph_0", "cardinal_continu = 2^aleph_0")
check(M.compare_cardinaux("aleph_0", "aleph_1") == -1, "ℵ0 < ℵ1")
check(M.compare_cardinaux("aleph_3", "aleph_1") == 1, "ℵ3 > ℵ1")
check(M.compare_cardinaux("aleph_2", "aleph_2") == 0, "ℵ2 = ℵ2")
check(M.compare_cardinaux("aleph_0", "2^aleph_0") == -1, "|ℕ| < |ℝ| : ℵ0 < 2^ℵ0 (Cantor)")
check(M.compare_cardinaux("2^aleph_0", "aleph_0") == 1, "2^ℵ0 > ℵ0 (Cantor, symétrique)")
check(M.compare_cardinaux("2^aleph_0", "2^aleph_0") == 0, "2^ℵ0 = 2^ℵ0")
check(M.cardinal_est_denombrable("aleph_0") is True, "ℵ0 dénombrable")
check(M.cardinal_est_denombrable("aleph_1") is False, "ℵ1 indénombrable")
check(M.cardinal_est_denombrable("2^aleph_0") is False, "2^ℵ0 indénombrable")
check(M.continu_au_moins_aleph1() is True, "2^ℵ0 ≥ ℵ1 (ZFC)")
check(M.hypothese_du_continu_independante() is True, "CH indécidable dans ZFC (Gödel-Cohen)")

# ── SOUNDNESS : entrée mal formée / question indécidable -> ValueError ──
check(leve(M.addition_ordinale, "omega", w), "addition d'un non-ordinal (str) -> ValueError")
check(leve(M.addition_ordinale, ((-1, 1),), w), "exposant négatif -> ValueError")
check(leve(M.addition_ordinale, ((1, 0),), w), "coefficient nul -> ValueError")
check(leve(M.compare_ordinaux, ((0, 1), (1, 1)), w), "exposants croissants (non canonique) -> ValueError")
check(leve(M.compare_ordinaux, ((1, 1), (1, 1)), w), "exposants dupliqués (non canonique) -> ValueError")
check(leve(M.multiplication_ordinale, 42, w), "ordinal = entier nu -> ValueError")
check(leve(M.addition_ordinale, ((1.5, 1),), w), "exposant non entier -> ValueError")
check(leve(M.addition_ordinale, ((True, 1),), w), "exposant booléen -> ValueError")
check(leve(M.addition_ordinale, ((1, 2, 3),), w), "terme à 3 composantes -> ValueError")
check(leve(M.fini, -1), "fini(-1) -> ValueError")
check(leve(M.fini, 1.5), "fini(1.5) -> ValueError")
check(leve(M.omega_puissance, -2), "omega_puissance(-2) -> ValueError")
check(leve(M.cardinal_aleph, -1), "cardinal_aleph(-1) -> ValueError")
check(leve(M.cardinal_aleph, 1.5), "cardinal_aleph(1.5) -> ValueError")
check(leve(M.cardinal_aleph, "x"), "cardinal_aleph('x') -> ValueError")
check(leve(M.compare_cardinaux, "aleph_1", "2^aleph_0"), "ℵ1 vs 2^ℵ0 (CH) -> ValueError (abstention)")
check(leve(M.compare_cardinaux, "aleph_5", "2^aleph_0"), "ℵ5 vs 2^ℵ0 (CH) -> ValueError (abstention)")
check(leve(M.compare_cardinaux, "2^aleph_0", "aleph_2"), "2^ℵ0 vs ℵ2 (CH) -> ValueError (abstention)")
check(leve(M.compare_cardinaux, "garbage", "aleph_0"), "cardinal non reconnu -> ValueError")
check(leve(M.cardinal_est_denombrable, "garbage"), "cardinal_est_denombrable('garbage') -> ValueError")

# ── DÉTERMINISME ──
check(M.addition_ordinale(w1, w2) == M.addition_ordinale(w1, w2), "déterminisme addition")
check(M.multiplication_ordinale(w1, w) == M.multiplication_ordinale(w1, w), "déterminisme multiplication")
check(M.compare_ordinaux(w2, wc) == M.compare_ordinaux(w2, wc), "déterminisme comparaison")

print(f"\n=== valide_ordinaux : {ok}/{ok + ko} ===")
import sys
sys.exit(0 if ko == 0 else 1)
