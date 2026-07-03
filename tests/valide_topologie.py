"""VALIDE topologie.py — held-out ADVERSE, FAUX=0. Ancres EXTERNES connues (polyèdres réguliers de Platon, polyèdre
de Császár = tore à 7 sommets, nombres de Betti classiques, genres de surfaces) NON recalculées par la même
expression + SOUNDNESS : entrée invalide -> ValueError (jamais faux) + déterminisme.
"""
import topologie as M

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


# ── CARACTÉRISTIQUE D'EULER — 5 solides de Platon, tous χ=2 (sphère) ──
check(M.caracteristique_euler(4, 6, 4) == 2, "tétraèdre V=4,E=6,F=4 -> χ=2")
check(M.caracteristique_euler(8, 12, 6) == 2, "cube V=8,E=12,F=6 -> χ=2")
check(M.caracteristique_euler(6, 12, 8) == 2, "octaèdre V=6,E=12,F=8 -> χ=2")
check(M.caracteristique_euler(20, 30, 12) == 2, "dodécaèdre V=20,E=30,F=12 -> χ=2")
check(M.caracteristique_euler(12, 30, 20) == 2, "icosaèdre V=12,E=30,F=20 -> χ=2")
# Tore : polyèdre de Császár (triangulation du tore à 7 sommets) χ=0
check(M.caracteristique_euler(7, 21, 14) == 0, "Császár (tore) V=7,E=21,F=14 -> χ=0")
# Triangulation minimale du tore (Möbius, 7 sommets) — autre comptage du même tore χ=0
check(M.caracteristique_euler(9, 27, 18) == 0, "tore subdivisé V=9,E=27,F=18 -> χ=0")

# ── CARACTÉRISTIQUE PAR NOMBRES DE BETTI (homologie, mécanisme indépendant) ──
check(M.caracteristique_euler_betti([1, 0, 1]) == 2, "Betti sphère [1,0,1] -> χ=2")
check(M.caracteristique_euler_betti([1, 2, 1]) == 0, "Betti tore [1,2,1] -> χ=0")
check(M.caracteristique_euler_betti([1, 4, 1]) == -2, "Betti bitore [1,4,1] -> χ=-2")
check(M.caracteristique_euler_betti([1]) == 1, "Betti point [1] -> χ=1")
check(M.caracteristique_euler_betti([1, 1]) == 0, "Betti cercle [1,1] -> χ=0")

# ── GENRE ORIENTABLE depuis χ ──
check(M.genre_depuis_euler(2) == 0, "sphère χ=2 -> genre 0")
check(M.genre_depuis_euler(0) == 1, "tore χ=0 -> genre 1")
check(M.genre_depuis_euler(-2) == 2, "bitore χ=-2 -> genre 2")
check(M.genre_depuis_euler(-4) == 3, "tritore χ=-4 -> genre 3")
# cohérence χ = 2 - 2g sur la même échelle
check(all(M.genre_depuis_euler(2 - 2 * g) == g for g in range(0, 6)), "genre(2-2g)=g pour g=0..5")

# ── GENRE NON ORIENTABLE (bonnets croisés) depuis χ ──
check(M.genre_non_orientable_depuis_euler(1) == 1, "RP² χ=1 -> k=1")
check(M.genre_non_orientable_depuis_euler(0) == 2, "Klein χ=0 -> k=2")
check(M.genre_non_orientable_depuis_euler(-1) == 3, "Dyck χ=-1 -> k=3")

# ── SOMME CONNEXE ──
check(M.caracteristique_euler_somme_connexe(0, 0) == -2, "tore#tore -> χ=-2 (genre 2)")
check(M.genre_depuis_euler(M.caracteristique_euler_somme_connexe(0, 0)) == 2, "genre(tore#tore)=2 (additivité)")
check(M.caracteristique_euler_somme_connexe(2, 0) == 0, "sphère#tore -> χ=0 (élément neutre = tore)")

# ── CLASSIFICATION sphère ──
check(M.est_homeomorphe_sphere(8, 12, 6) is True, "cube homéomorphe à la sphère")
check(M.est_homeomorphe_sphere(20, 30, 12) is True, "dodécaèdre homéomorphe à la sphère")
check(M.est_homeomorphe_sphere(7, 21, 14) is False, "tore (Császár) NON homéomorphe à la sphère")
check(M.est_homeomorphe_sphere(9, 27, 18) is False, "tore subdivisé NON homéomorphe à la sphère")

# ── SOUNDNESS — entrée invalide -> ValueError (jamais un faux résultat) ──
check(leve(M.caracteristique_euler, -1, 12, 6), "V<0 -> ValueError")
check(leve(M.caracteristique_euler, 8, -1, 6), "E<0 -> ValueError")
check(leve(M.caracteristique_euler, 8, 12, -1), "F<0 -> ValueError")
check(leve(M.caracteristique_euler, 8.0, 12, 6), "V flottant -> ValueError")
check(leve(M.caracteristique_euler, 8, 12, True), "F booléen -> ValueError")
check(leve(M.caracteristique_euler, "8", 12, 6), "V chaîne -> ValueError")
check(leve(M.genre_depuis_euler, 1), "χ=1 impair -> ValueError (genre non entier)")
check(leve(M.genre_depuis_euler, 3), "χ=3 impair -> ValueError")
check(leve(M.genre_depuis_euler, 4), "χ=4 > 2 -> ValueError (genre négatif)")
check(leve(M.genre_depuis_euler, 2.0), "χ flottant -> ValueError")
check(leve(M.genre_non_orientable_depuis_euler, 2), "χ=2 > 1 -> ValueError (k ≤ 0)")
check(leve(M.caracteristique_euler_betti, []), "Betti vide -> ValueError")
check(leve(M.caracteristique_euler_betti, [1, -2, 1]), "Betti négatif -> ValueError")
check(leve(M.caracteristique_euler_betti, [1, 2.0, 1]), "Betti flottant -> ValueError")
check(leve(M.est_homeomorphe_sphere, -1, 12, 6), "homéo sphère V<0 -> ValueError")
check(leve(M.caracteristique_euler_somme_connexe, 0.0, 0), "somme connexe χ flottant -> ValueError")

# ── DÉTERMINISME ──
check(M.caracteristique_euler(8, 12, 6) == M.caracteristique_euler(8, 12, 6), "déterminisme χ")
check(M.genre_depuis_euler(-2) == M.genre_depuis_euler(-2), "déterminisme genre")

print(f"\n=== valide_topologie : {ok}/{ok + ko} ===")
import sys
sys.exit(0 if ko == 0 else 1)
