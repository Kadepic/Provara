"""VALIDE turing.py — ADVERSE, FAUX=0. MT incrément binaire vérifiée contre l'arithmétique (succ(x)=x+1 en binaire)
sur de nombreuses entrées + arrêt/blocage/timeout + SOUNDNESS (MT mal formée / budget ≤ 0 -> ValueError)."""
import turing as T

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


B = "_"
INCR = {
    "blanc": B, "initial": "droite", "acceptants": {"fini"},
    "transitions": {
        ("droite", "0"): ("droite", "0", "R"),
        ("droite", "1"): ("droite", "1", "R"),
        ("droite", B):   ("retenue", B, "L"),
        ("retenue", "0"): ("fini", "1", "L"),
        ("retenue", "1"): ("retenue", "0", "L"),
        ("retenue", B):   ("fini", "1", "L"),
    },
}

# Incrément binaire = arithmétique vérifiable indépendamment
for x in ["0", "1", "10", "11", "101", "111", "1011", "1111", "100000", "10101"]:
    st, ruban, _ = T.execute(INCR, x, 1000)
    attendu = bin(int(x, 2) + 1)[2:]
    check(st == "accepte" and ruban == attendu, f"succ({x}) = {attendu} (vu {ruban!r}, {st})")

# BLOCAGE : aucune transition définie -> 'bloque'
BLOQUE = {"blanc": B, "initial": "q", "acceptants": {"fin"}, "transitions": {}}
st, _, n = T.execute(BLOQUE, "1", 100)
check(st == "bloque" and n == 0, "pas de transition -> bloque immédiat")

# TIMEOUT : boucle infinie (va à droite sans fin) -> 'timeout' HONNÊTE (pas de verdict inventé)
BOUCLE = {"blanc": B, "initial": "q", "acceptants": set(),
          "transitions": {("q", "0"): ("q", "0", "R"), ("q", "1"): ("q", "1", "R"), ("q", B): ("q", B, "R")}}
st, _, n = T.execute(BOUCLE, "101", 500)
check(st == "timeout" and n == 500, "boucle infinie -> timeout au budget (problème de l'arrêt assumé)")

# ACCEPTE immédiat si l'état initial est acceptant
DEJA = {"blanc": B, "initial": "ok", "acceptants": {"ok"}, "transitions": {}}
check(T.execute(DEJA, "1", 10)[0] == "accepte", "état initial acceptant -> accepte")

# SOUNDNESS
check(leve(T.execute, {"initial": "q", "acceptants": set(), "blanc": B}, "1", 10), "clé transitions manquante -> ValueError")
check(leve(T.execute, INCR, "1", 0), "budget 0 -> ValueError")
check(leve(T.execute, INCR, "1", -5), "budget négatif -> ValueError")

# DÉTERMINISME
check(T.execute(INCR, "111", 1000) == T.execute(INCR, "111", 1000), "déterminisme")

print(f"\n=== valide_turing : {ok}/{ok + ko} ===")
import sys
sys.exit(0 if ko == 0 else 1)
