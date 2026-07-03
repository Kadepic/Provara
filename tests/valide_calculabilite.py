"""VALIDE calculabilite.py — held-out ADVERSE, FAUX=0.

Ancres EXTERNES connues : valeurs d'Ackermann de référence (A(0,n)=n+1, A(1,1)=3,
A(2,2)=7, A(3,3)=61 = 2^16-3), identités arithmétiques pour la récursion primitive,
décodage des numéraux de Church. + SOUNDNESS : entrée invalide / hors borne -> ValueError
(jamais une réponse inventée). + DÉTERMINISME.
"""
import calculabilite as M

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


# ── ANCRES Ackermann (valeurs de référence connues) ──
check(M.fonction_ackermann(0, 0) == 1, "A(0,0)=1")
check(M.fonction_ackermann(0, 4) == 5, "A(0,4)=5")
check(all(M.fonction_ackermann(0, n) == n + 1 for n in range(20)), "A(0,n)=n+1")
check(M.fonction_ackermann(1, 0) == 2, "A(1,0)=2")
check(M.fonction_ackermann(1, 1) == 3, "A(1,1)=3")
check(all(M.fonction_ackermann(1, n) == n + 2 for n in range(15)), "A(1,n)=n+2")
check(M.fonction_ackermann(2, 0) == 3, "A(2,0)=3")
check(M.fonction_ackermann(2, 2) == 7, "A(2,2)=7")
check(all(M.fonction_ackermann(2, n) == 2 * n + 3 for n in range(12)), "A(2,n)=2n+3")
check(M.fonction_ackermann(3, 0) == 5, "A(3,0)=5")
check(M.fonction_ackermann(3, 1) == 13, "A(3,1)=13")
check(M.fonction_ackermann(3, 3) == 61, "A(3,3)=61")
check(M.fonction_ackermann(3, 3) == 2 ** (3 + 3) - 3, "A(3,3)=2^6-3")
check(all(M.fonction_ackermann(3, n) == 2 ** (n + 3) - 3 for n in range(6)), "A(3,n)=2^(n+3)-3")
check(M.ackermann(2, 3) == 9, "alias ackermann(2,3)=9")
check(M.est_primitive_recursive_ackermann() is False, "Ackermann n'est PAS primitive récursive")

# ── ANCRES récursion primitive (identités arithmétiques externes) ──
check(M.successeur(0) == 1 and M.successeur(40) == 41, "successeur")
check(all(M.addition(a, b) == a + b for a in range(8) for b in range(8)), "addition = a+b")
check(M.addition(7, 5) == 12, "addition(7,5)=12")
check(all(M.multiplication(a, b) == a * b for a in range(8) for b in range(8)), "multiplication = a*b")
check(M.multiplication(6, 7) == 42, "multiplication(6,7)=42")
check(all(M.puissance(a, b) == a ** b for a in range(6) for b in range(6)), "puissance = a^b")
check(M.puissance(2, 10) == 1024, "puissance(2,10)=1024")
check(M.puissance(0, 0) == 1, "puissance(0,0)=1 (convention)")
check(M.primitive_recursive("addition", 9, 4) == 13, "dispatcher addition")
check(M.primitive_recursive("puissance", 3, 4) == 81, "dispatcher puissance")

# ── ANCRES numéraux de Church ──
check(M.church_vers_entier(M.church_numeral(0)) == 0, "church 0")
check(all(M.church_vers_entier(M.church_numeral(k)) == k for k in range(25)), "church k -> k")
check(M.church_numeral(3)(lambda x: x + 1)(0) == 3, "church 3 applique f 3 fois")
check(M.church_numeral(4)(lambda s: s + "a")("") == "aaaa", "church 4 sur chaînes")

# ── SOUNDNESS : invalide / hors borne -> ValueError ──
check(leve(M.fonction_ackermann, -1, 2), "A(-1,2) -> ValueError")
check(leve(M.fonction_ackermann, 2, -1), "A(2,-1) -> ValueError")
check(leve(M.fonction_ackermann, 4, 2), "A(4,2) borne sûreté -> ValueError")
check(leve(M.fonction_ackermann, 5, 3), "A(5,3) borne sûreté -> ValueError")
check(leve(M.fonction_ackermann, 4, 1), "A(4,1) budget/protection -> ValueError")
check(leve(M.fonction_ackermann, 1.5, 2), "A non entier -> ValueError")
check(leve(M.fonction_ackermann, True, 1), "A bool -> ValueError")
check(leve(M.addition, 3, -1), "addition arg négatif -> ValueError")
check(leve(M.multiplication, -2, 3), "multiplication arg négatif -> ValueError")
check(leve(M.puissance, 2, -1), "puissance arg négatif -> ValueError")
check(leve(M.puissance, 2.0, 3), "puissance float -> ValueError")
check(leve(M.successeur, -1), "successeur(-1) -> ValueError")
check(leve(M.primitive_recursive, "soustraction", 3, 1), "dispatcher inconnu -> ValueError")
check(leve(M.church_numeral, -1), "church_numeral(-1) -> ValueError")
check(leve(M.church_numeral, 1.5), "church_numeral(1.5) -> ValueError")
check(leve(M.church_vers_entier, 42), "church_vers_entier(non-callable) -> ValueError")

# ── DÉTERMINISME ──
check(M.fonction_ackermann(3, 3) == M.fonction_ackermann(3, 3), "déterminisme Ackermann")
check(M.puissance(3, 7) == M.puissance(3, 7), "déterminisme puissance")
check(M.church_vers_entier(M.church_numeral(9))
      == M.church_vers_entier(M.church_numeral(9)), "déterminisme Church")

print(f"\n=== valide_calculabilite : {ok}/{ok + ko} ===")
import sys
sys.exit(0 if ko == 0 else 1)
