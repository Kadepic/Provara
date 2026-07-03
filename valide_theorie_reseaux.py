"""VALIDE theorie_reseaux.py — ADVERSE, FAUX=0. Métriques sur graphes CONNUS (complet -> densité 1, étoile, triangle,
chemin) + cohérence (Σdegrés = 2|E|) + SOUNDNESS (sommet hors plage, n<2 -> ValueError)."""
import theorie_reseaux as R

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


TRIANGLE = [(0, 1), (1, 2), (2, 0)]
ETOILE = [(0, 1), (0, 2), (0, 3)]
COMPLET4 = [(0, 1), (0, 2), (0, 3), (1, 2), (1, 3), (2, 3)]
CHEMIN = [(0, 1), (1, 2), (2, 3)]

# DEGRÉ
check(R.degre(4, ETOILE, 0) == 3 and R.degre(4, ETOILE, 1) == 1, "degré centre/feuille de l'étoile")
check(R.degre(3, TRIANGLE, 0) == 2, "degré dans un triangle = 2")
check(R.degre(4, [], 0) == 0, "sommet isolé -> degré 0")

# DEGRÉ MOYEN (Σdegrés = 2|E|)
check(proche(R.degre_moyen(4, ETOILE), 1.5), "degré moyen étoile = 6/4 = 1.5")
check(proche(R.degre_moyen(4, COMPLET4), 3.0), "degré moyen K4 = 3")
check(proche(R.degre_moyen(3, TRIANGLE), 2.0), "degré moyen triangle = 2")

# DENSITÉ
check(R.densite(3, TRIANGLE) == 1.0, "triangle = graphe complet -> densité 1")
check(R.densite(4, COMPLET4) == 1.0, "K4 -> densité 1")
check(R.densite(4, []) == 0.0, "graphe vide -> densité 0")
check(proche(R.densite(4, ETOILE), 0.5), "étoile S4 -> densité 0.5")
check(proche(R.densite(4, CHEMIN), 0.5), "chemin P4 -> densité 0.5")

# CENTRALITÉ DE DEGRÉ
check(R.centralite_degre(4, ETOILE, 0) == 1.0, "centre de l'étoile -> centralité 1")
check(proche(R.centralite_degre(4, ETOILE, 1), 1 / 3), "feuille -> 1/3")

# DISTRIBUTION
check(R.distribution_degres(4, ETOILE) == {3: 1, 1: 3}, "distribution étoile")
check(R.distribution_degres(4, COMPLET4) == {3: 4}, "distribution K4 : tous degré 3")

# CLUSTERING LOCAL
check(R.clustering_local(3, TRIANGLE, 0) == 1.0, "triangle -> clustering 1")
check(R.clustering_local(4, ETOILE, 0) == 0.0, "centre étoile -> clustering 0 (voisins non liés)")
check(R.clustering_local(4, COMPLET4, 0) == 1.0, "K4 -> clustering 1")
check(R.clustering_local(4, [(0, 1)], 0) == 0.0, "degré 1 -> clustering 0")

# SOUNDNESS
check(leve(R.degre, 3, TRIANGLE, 5), "sommet hors plage -> ValueError")
check(leve(R.densite, 1, []), "n<2 pour densité -> ValueError")
check(leve(R.degre, 3, [(0, 5)], 0), "arête hors plage -> ValueError")
check(leve(R.degre, 3, [(0, 1, 2)], 0), "arête mal formée -> ValueError")
check(leve(R.degre_moyen, 0, []), "graphe vide (n=0) -> ValueError")

# DÉTERMINISME
check(R.densite(4, ETOILE) == R.densite(4, ETOILE), "déterminisme")

print(f"\n=== valide_theorie_reseaux : {ok}/{ok + ko} ===")
import sys
sys.exit(0 if ko == 0 else 1)
