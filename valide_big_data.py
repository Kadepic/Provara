"""VALIDE big_data.py — ADVERSE, FAUX=0. Word-count MapReduce connu, MapReduce générique, filtre de Bloom (propriété
GARANTIE : aucun faux négatif) + SOUNDNESS (paramètres invalides -> ValueError)."""
import big_data as BD

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


# WORD-COUNT MapReduce
wc = BD.compte_mots(["le chat dort", "le chien court", "le chat court"])
check(wc == {"le": 3, "chat": 2, "dort": 1, "chien": 1, "court": 2}, "word-count exact")
check(BD.compte_mots([]) == {}, "corpus vide -> {}")
check(BD.compte_mots(["Mot mot MOT"]) == {"mot": 3}, "insensible à la casse")

# MapReduce générique : somme des carrés par parité
res = BD.mapreduce(range(6),
                   lambda x: [("pair" if x % 2 == 0 else "impair", x * x)],
                   lambda k, vs: sum(vs))
check(res == {"pair": 0 + 4 + 16, "impair": 1 + 9 + 25}, "MapReduce somme des carrés par parité")

# FILTRE DE BLOOM — aucun faux négatif (propriété fondamentale)
b = BD.FiltreBloom(2048, 5)
elements = [f"element-{i}" for i in range(50)]
for e in elements:
    b.ajoute(e)
check(all(b.contient(e) for e in elements), "AUCUN faux négatif : tous les ajoutés sont détectés")
# éléments non ajoutés : majoritairement absents (faux positif possible mais rare avec 2048 bits / 50 éléments)
absents = [f"absent-{i}" for i in range(50)]
faux_positifs = sum(1 for e in absents if b.contient(e))
check(faux_positifs < 10, f"faux positifs rares ({faux_positifs}/50)")
check(BD.FiltreBloom(1024).contient("rien") is False, "filtre vide -> rien n'est contenu")

# ÉCHANTILLONNAGE RÉSERVOIR (déterministe ici)
check(BD.echantillon_reservoir(["a", "b", "c", "d"], 2, {0, 2}) == ["a", "c"], "réservoir indices {0,2}")
check(len(BD.echantillon_reservoir(range(100), 5, set(range(100)))) == 5, "réservoir borné à `taille`")

# SOUNDNESS
check(leve(BD.mapreduce, [], "pas une fonction", lambda k, v: v), "map non appelable -> ValueError")
check(leve(lambda: BD.FiltreBloom(0)), "taille 0 -> ValueError")
check(leve(lambda: BD.FiltreBloom(100, 0)), "k=0 -> ValueError")
check(leve(BD.echantillon_reservoir, [1, 2], 0, {0}), "taille 0 -> ValueError")

# DÉTERMINISME
check(BD.compte_mots(["a a b"]) == BD.compte_mots(["a a b"]), "déterminisme")

print(f"\n=== valide_big_data : {ok}/{ok + ko} ===")
import sys
sys.exit(0 if ko == 0 else 1)
