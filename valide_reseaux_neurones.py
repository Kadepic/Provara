"""VALIDE reseaux_neurones.py — ADVERSE, FAUX=0. Perceptron réalisant ET/OU (linéairement séparables), activations
connues, réseau 2 couches réalisant XOR (non séparable au 1ᵉ ordre) + SOUNDNESS (dimensions incompatibles -> ValueError)."""
import reseaux_neurones as N

ok = 0
ko = 0


def check(c, l):
    global ok, ko
    if c:
        ok += 1
    else:
        ko += 1
        print(f"  FAIL: {l}")


def proche(a, b, t=1e-9):
    return abs(a - b) <= t


def leve(fn, *a):
    try:
        fn(*a)
        return False
    except ValueError:
        return True
    except Exception:
        return False


ENTREES = [(0, 0), (0, 1), (1, 0), (1, 1)]

# PERCEPTRON — portes logiques linéairement séparables
ET = {(0, 0): 0, (0, 1): 0, (1, 0): 0, (1, 1): 1}
OU = {(0, 0): 0, (0, 1): 1, (1, 0): 1, (1, 1): 1}
check(all(N.neurone(list(x), [1, 1], -1.5) == ET[x] for x in ENTREES), "perceptron réalise ET")
check(all(N.neurone(list(x), [1, 1], -0.5) == OU[x] for x in ENTREES), "perceptron réalise OU")
# NON (un seul poids)
check(N.neurone([0], [-1], 0.5) == 1 and N.neurone([1], [-1], 0.5) == 0, "perceptron réalise NON")

# POTENTIEL
check(N.potentiel([1, 1], [1, 1], -1.5) == 0.5, "z = 1+1-1.5 = 0.5")
check(N.potentiel([2, 3], [1, -1], 0) == -1.0, "z = 2-3 = -1")

# ACTIVATIONS
check(N.echelon(0) == 1 and N.echelon(-0.1) == 0, "échelon")
check(N.signe(3) == 1 and N.signe(-3) == -1 and N.signe(0) == 0, "signe")
check(N.relu(-2) == 0.0 and N.relu(3) == 3.0, "ReLU")
check(proche(N.sigmoide(0), 0.5), "sigmoïde(0) = 0.5")
check(proche(N.tanh(0), 0.0), "tanh(0) = 0")
check(N.sigmoide(100) > 0.99 and N.sigmoide(-100) < 0.01, "sigmoïde saturée")

# XOR — non séparable au 1ᵉ ordre : réseau à 2 couches (cachée OR/NAND, sortie AND)
XOR = {(0, 0): 0, (0, 1): 1, (1, 0): 1, (1, 1): 0}


def xor_2couches(x):
    h = N.couche_dense(list(x), [[1, 1], [-1, -1]], [-0.5, 1.5])   # h1 = OR, h2 = NAND
    return N.neurone(h, [1, 1], -1.5)                               # sortie = AND(OR, NAND)


check(all(xor_2couches(x) == XOR[x] for x in ENTREES), "réseau 2 couches réalise XOR")
# un perceptron simple NE PEUT PAS réaliser XOR (aucun (w,b) ne sépare) — on vérifie qu'un candidat échoue
check(not all(N.neurone(list(x), [1, 1], -0.5) == XOR[x] for x in ENTREES), "perceptron simple échoue sur XOR")

# COUCHE DENSE
check(N.couche_dense([1, 1], [[1, 1], [1, 1]], [-1.5, -0.5]) == [1, 1], "couche : [ET, OU] sur (1,1)")

# SOUNDNESS
check(leve(N.potentiel, [1, 1], [1], 0), "dim entrées/poids incompatibles -> ValueError")
check(leve(N.neurone, [1], [1], 0, "inconnue"), "activation inconnue -> ValueError")
check(leve(N.couche_dense, [1], [[1], [1]], [0]), "neurones poids/biais incohérents -> ValueError")

# DÉTERMINISME
check(N.neurone([1, 1], [1, 1], -1.5) == N.neurone([1, 1], [1, 1], -1.5), "déterminisme")

print(f"\n=== valide_reseaux_neurones : {ok}/{ok + ko} ===")
import sys
sys.exit(0 if ko == 0 else 1)
