"""VALIDE arithmetique_modulaire.py — held-out ADVERSE, FAUX=0. Ancres connues (Bézout vérifié, inverses, primalité
incl. Carmichael, round-trip RSA) NON circulaires + SOUNDNESS : inverse inexistant / entrées invalides -> ValueError.
"""
import arithmetique_modulaire as A

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


# ── PGCD ──
check(A.pgcd(48, 36) == 12 and A.pgcd(17, 5) == 1 and A.pgcd(0, 7) == 7 and A.pgcd(0, 0) == 0, "pgcd connus")
check(A.pgcd(-48, 36) == 12, "pgcd valeur absolue")

# ── EUCLIDE ÉTENDU — identité de Bézout a·x+b·y=g vérifiée indépendamment ──
for a, b in [(240, 46), (17, 5), (100, 35), (1, 1), (13, 0)]:
    g, x, y = A.euclide_etendu(a, b)
    check(g == A.pgcd(a, b) and a * x + b * y == g, f"Bézout {a},{b} : {a}·{x}+{b}·{y}={g}")

# ── INVERSE MODULAIRE — a·inv ≡ 1 vérifié indépendamment ──
for a, n in [(3, 11), (7, 26), (17, 3233), (2, 5)]:
    inv = A.inverse_modulaire(a, n)
    check(0 <= inv < n and (a * inv) % n == 1, f"inverse {a} mod {n} = {inv} (a·inv≡1)")
check(leve(A.inverse_modulaire, 6, 9), "pgcd(6,9)=3≠1 -> pas d'inverse -> ValueError")
check(leve(A.inverse_modulaire, 3, 1), "module ≤1 -> ValueError")

# ── EXPONENTIATION MODULAIRE — accord avec pow() de référence ──
for b, e, m in [(7, 128, 13), (2, 10, 1000), (123, 456, 789), (5, 0, 7), (10, 5, 1)]:
    check(A.exp_modulaire(b, e, m) == pow(b, e, m), f"{b}^{e} mod {m} = {pow(b, e, m)}")
check(leve(A.exp_modulaire, 2, -1, 5), "exposant négatif -> ValueError")
check(leve(A.exp_modulaire, 2, 3, 0), "module 0 -> ValueError")

# ── PRIMALITÉ — Miller-Rabin déterministe (dont Carmichael, faux-témoins) ──
check([k for k in range(2, 50) if A.est_premier(k)] == [2, 3, 5, 7, 11, 13, 17, 19, 23, 29, 31, 37, 41, 43, 47],
      "premiers < 50 exacts")
check(not A.est_premier(1) and not A.est_premier(0) and not A.est_premier(-7), "≤1 et négatifs non premiers")
check(A.est_premier(561) is False and A.est_premier(1105) is False, "Carmichael 561/1105 démasqués (composés)")
check(A.est_premier(2147483647) is True, "Mersenne M31 = 2147483647 premier")
check(A.est_premier(1000003) is True and A.est_premier(1000000) is False, "grand premier vs composé")
check(A.est_premier(9) is False and A.est_premier(25) is False and A.est_premier(49) is False, "carrés de premiers composés")

# ── RSA — round-trip déchiffre(chiffre(m)) = m (clé manuel p=61,q=53,n=3233,e=17,d=2753) ──
N, E, D = 3233, 17, 2753
for m in [0, 1, 2, 65, 100, 3232]:
    c = A.rsa_chiffre(m, E, N)
    check(A.rsa_dechiffre(c, D, N) == m, f"RSA round-trip m={m}")
check(A.rsa_chiffre(65, 17, 3233) == 2790, "RSA chiffre(65) = 2790 (ancre manuelle)")
check(leve(A.rsa_chiffre, 5000, E, N), "message ≥ n -> ValueError")

# ── SOUNDNESS types ──
check(leve(A.pgcd, 1.5, 2) and leve(A.est_premier, "7") and leve(A.exp_modulaire, True, 2, 3), "non-entiers -> ValueError")

# ── DÉTERMINISME ──
check(A.est_premier(7919) == A.est_premier(7919) and A.exp_modulaire(7, 128, 13) == A.exp_modulaire(7, 128, 13),
      "déterminisme")

print(f"\n=== valide_arithmetique_modulaire : {ok}/{ok + ko} ===")
import sys
sys.exit(0 if ko == 0 else 1)
