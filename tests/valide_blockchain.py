"""VALIDE blockchain.py — ADVERSE, FAUX=0. Intégrité d'une chaîne (valide vs altérée de multiples façons), racine de
Merkle déterministe et sensible, preuve de travail + SOUNDNESS (chaîne/bloc mal formé -> ValueError)."""
import blockchain as B

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


# CHAÎNE VALIDE
g = B.cree_bloc(0, "genesis", "0")
b1 = B.cree_bloc(1, "Alice->Bob:5", g["hash"])
b2 = B.cree_bloc(2, "Bob->Carl:3", b1["hash"])
check(B.chaine_valide([g, b1, b2]) is True, "chaîne intègre -> valide")
check(B.chaine_valide([g]) is True, "chaîne d'un seul bloc -> valide")

# ALTÉRATIONS détectées
check(B.chaine_valide([g, dict(b1, donnees="Alice->Bob:5000"), b2]) is False, "données altérées -> invalide")
check(B.chaine_valide([g, dict(b1, hash="deadbeef"), b2]) is False, "hash falsifié -> invalide")
check(B.chaine_valide([g, b2, b1]) is False, "ordre cassé -> chaînage rompu")
b1_bis = B.cree_bloc(1, "autre", g["hash"])
check(B.chaine_valide([g, b1_bis, b2]) is False, "bloc remplacé -> chaînage du suivant rompu")

# le hachage est déterministe et sensible à chaque champ
check(B.hash_bloc(1, "x", "0", 0) == B.hash_bloc(1, "x", "0", 0), "hash déterministe")
check(B.hash_bloc(1, "x", "0", 0) != B.hash_bloc(1, "x", "0", 1), "hash sensible au nonce")
check(B.hash_bloc(1, "x", "0", 0) != B.hash_bloc(1, "y", "0", 0), "hash sensible aux données")
check(len(g["hash"]) == 64, "SHA-256 -> 64 hex")

# MERKLE
check(B.merkle_root(["a"]) == __import__("hashlib").sha256(b"a").hexdigest(), "Merkle 1 tx = H(tx)")
check(B.merkle_root(["a", "b", "c", "d"]) == B.merkle_root(["a", "b", "c", "d"]), "Merkle déterministe")
check(B.merkle_root(["a", "b"]) != B.merkle_root(["b", "a"]), "Merkle sensible à l'ordre")
check(B.merkle_root(["a", "b", "c"]) != B.merkle_root(["a", "b", "c", "d"]), "Merkle sensible au contenu")

# PREUVE DE TRAVAIL
check(B.preuve_travail_valide("000abc", 3) is True, "3 zéros -> PoW difficulté 3 OK")
check(B.preuve_travail_valide("000abc", 4) is False, "PoW difficulté 4 -> échec")
check(B.preuve_travail_valide("abc", 0) is True, "difficulté 0 -> toujours OK")

# SOUNDNESS
check(leve(B.chaine_valide, []), "chaîne vide -> ValueError")
check(leve(B.chaine_valide, [{"index": 0}]), "bloc mal formé -> ValueError")
check(leve(B.merkle_root, []), "Merkle sans transaction -> ValueError")
check(leve(B.preuve_travail_valide, "abc", -1), "difficulté négative -> ValueError")

print(f"\n=== valide_blockchain : {ok}/{ok + ko} ===")
import sys
sys.exit(0 if ko == 0 else 1)
