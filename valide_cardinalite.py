"""VALIDE cardinalite.py — held-out ADVERSE. Ancres EXTERNES (énumération diagonale construite INDÉPENDAMMENT de la
formule (i+j)(i+j+1)/2+j ; valeurs connues 2^n ; verdicts de dénombrabilité = théorèmes de Cantor) + SOUNDNESS
(entrée invalide -> ValueError, jamais un faux) + déterminisme. Aucun de ces cas n'est dans cardinalite.py.
"""
import cardinalite as C

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


# ── ANCRE EXTERNE : énumération diagonale construite À LA MAIN (n'utilise PAS la formule du module) ──
# Ordre de Cantor : diagonales s=0,1,2,… ; sur chaque diagonale j=0..s donne le couple (i=s-j, j).
attendu = []
s = 0
while len(attendu) < 30:
    for j in range(s + 1):
        attendu.append((s - j, j))
    s += 1
# attendu[z] = π⁻¹(z) selon l'énumération de référence.
check(attendu[0] == (0, 0) and attendu[1] == (1, 0) and attendu[2] == (0, 1)
      and attendu[3] == (2, 0) and attendu[4] == (1, 1) and attendu[5] == (0, 2),
      "ancre : ordre diagonal de référence")

# couple_cantor doit reproduire EXACTEMENT cette énumération de référence
check(all(C.couple_cantor(i, j) == z for z, (i, j) in enumerate(attendu)),
      "couple_cantor = index dans l'énumération diagonale (bijection ℕ×ℕ→ℕ)")

# decouple_cantor doit rendre le bon couple de référence
check(all(C.decouple_cantor(z) == attendu[z] for z in range(len(attendu))),
      "decouple_cantor = π⁻¹ de référence")

# cas explicites demandés
check(C.couple_cantor(0, 0) == 0, "couple_cantor(0,0)=0")
check(C.couple_cantor(1, 0) == 1, "couple_cantor(1,0)=1")
check(C.couple_cantor(0, 1) == 2, "couple_cantor(0,1)=2")
check(C.couple_cantor(2, 0) == 3, "couple_cantor(2,0)=3")
check(C.couple_cantor(1, 1) == 4, "couple_cantor(1,1)=4")

# aller-retour (bijectivité) sur une plage large
check(all(C.decouple_cantor(C.couple_cantor(i, j)) == (i, j)
          for i in range(40) for j in range(40)), "round-trip découple∘couple = id sur ℕ×ℕ")
check(all(C.couple_cantor(*C.decouple_cantor(z)) == z for z in range(2000)),
      "round-trip couple∘découple = id sur ℕ")
# injectivité explicite : 1600 couples → 1600 images distinctes
imgs = [C.couple_cantor(i, j) for i in range(40) for j in range(40)]
check(len(set(imgs)) == len(imgs), "couple_cantor injective (images toutes distinctes)")

# ── CARDINAL DES PARTIES : 2^n (valeurs connues, non recalculées par le module) ──
check(C.cardinal_parties(3) == 8, "cardinal_parties(3)=8")
check(C.cardinal_parties(0) == 1, "cardinal_parties(0)=1 (P(∅)={∅})")
check(C.cardinal_parties(1) == 2, "cardinal_parties(1)=2")
check(C.cardinal_parties(10) == 1024, "cardinal_parties(10)=1024")
check(C.cardinal_parties(64) == 18446744073709551616, "cardinal_parties(64)=2^64 (entier exact)")

# ── CARDINAL FINI : éléments DISTINCTS ──
check(C.cardinal_ensemble([1, 1, 2, 3, 3, 3]) == 3, "cardinal {1,2,3} = 3")
check(C.cardinal_ensemble([]) == 0, "cardinal ∅ = 0")
check(C.cardinal_ensemble(["a", "a", "b"]) == 2, "cardinal {a,b} = 2")
check(C.cardinal_ensemble([1, 2, 3, 4, 5]) == 5, "cardinal sans doublon = 5")
check(C.cardinal_ensemble({7, 8, 9}) == 3, "cardinal d'un set = 3")

# ── DÉNOMBRABILITÉ (théorèmes de Cantor) ──
check(C.est_denombrable("N") is True, "ℕ dénombrable")
check(C.est_denombrable("Z") is True, "ℤ dénombrable")
check(C.est_denombrable("Q") is True, "ℚ dénombrable")
check(C.est_denombrable("N×N") is True and C.est_denombrable("NxN") is True, "ℕ×ℕ dénombrable")
check(C.est_denombrable("R") is False, "ℝ NON dénombrable (diagonale de Cantor)")
check(C.est_denombrable("P(N)") is False, "P(ℕ) NON dénombrable (théorème de Cantor)")
check(C.est_denombrable("[0,1]") is False, "[0,1] NON dénombrable")
check(C.est_denombrable("C") is False, "ℂ NON dénombrable")

# ── SOUNDNESS — entrée invalide -> ValueError (jamais un faux résultat) ──
check(leve(C.cardinal_parties, -1), "cardinal_parties(-1) -> ValueError")
check(leve(C.cardinal_parties, 2.0), "cardinal_parties(float) -> ValueError")
check(leve(C.cardinal_parties, True), "cardinal_parties(bool) -> ValueError")
check(leve(C.couple_cantor, -1, 0), "couple_cantor(-1,0) -> ValueError")
check(leve(C.couple_cantor, 0, -1), "couple_cantor(0,-1) -> ValueError")
check(leve(C.decouple_cantor, -1), "decouple_cantor(-1) -> ValueError")
check(leve(C.est_denombrable, "blabla"), "ensemble inconnu -> ValueError (abstention)")
check(leve(C.est_denombrable, 42), "nom non-chaîne -> ValueError")
check(leve(C.cardinal_ensemble, 5), "cardinal d'un non-itérable -> ValueError")
check(leve(C.cardinal_ensemble, [[1, 2], [3]]), "élément non hachable -> ValueError")
check(leve(C.cardinal_ensemble, "abc"), "chaîne ambiguë -> ValueError")

# ── DÉTERMINISME ──
check(C.couple_cantor(7, 13) == C.couple_cantor(7, 13)
      and C.decouple_cantor(999) == C.decouple_cantor(999), "déterminisme")

print(f"\n=== valide_cardinalite : {ok}/{ok + ko} ===")
import sys
sys.exit(0 if ko == 0 else 1)
