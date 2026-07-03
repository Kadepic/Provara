"""
VALIDE physique.py — held-out ADVERSE. Exactitude des formules (ancrées sur des valeurs PHYSIQUES CONNUES, pas
re-calculées par la même expression : gravité terrestre 9.81, libération 11.2 km/s, période d'1 UA = 1 an, eau
neutre pH 7…) + SOUNDNESS : grandeur inconnue / paramètre manquant / domaine invalide -> HORS (jamais un faux).
Aucun de ces cas n'est dans physique.py.
"""
import physique as P

ok = 0
ko = 0


def check(cond, label):
    global ok, ko
    if cond:
        ok += 1
    else:
        ko += 1
        print(f"  FAIL: {label}")


def approx(grandeur, params, attendu, rel=1e-4):
    st, v, _ = P.calcule(grandeur, params)
    return st == P.VERIFIE and v is not None and abs(v - attendu) <= rel * abs(attendu) + 1e-12


# ── 1) EXACTITUDE — grandeurs à résultat exact (entier/simple) ──
check(approx("quantite_mouvement", {"m": 2, "v": 3}, 6), "p = m·v = 6")
check(approx("energie_cinetique", {"m": 2, "v": 3}, 9.0), "Ec = ½·2·3² = 9 J")
check(approx("force_newton", {"m": 2, "a": 5}, 10), "F = m·a = 10 N")
check(approx("travail", {"force": 5, "deplacement": 4}, 20), "W = F·d = 20 J")
check(approx("loi_ohm_tension", {"R": 10, "I": 2}, 20), "U = R·I = 20 V")
check(approx("puissance_electrique", {"U": 12, "I": 2}, 24), "P = U·I = 24 W")
check(approx("rendement_carnot", {"Tc": 300, "Th": 600}, 0.5), "η_Carnot = 1−300/600 = 0.5")
check(approx("cop_carnot_pompe", {"Tc": 300, "Th": 600}, 2.0), "COP pompe = 600/300 = 2")
check(approx("cop_carnot_froid", {"Tc": 300, "Th": 600}, 1.0), "COP froid = 300/300 = 1")
check(approx("moment_force", {"force": 10, "bras_levier": 0.5}, 5), "moment = F·d = 5 N·m")
check(approx("premier_principe", {"Q": 100, "W": 30}, 70), "ΔU = Q−W = 70 J")
check(approx("vitesse_onde", {"frequence": 100, "longueur_onde": 3}, 300), "v = ν·λ = 300 m/s")
check(approx("decroissance_radioactive", {"N0": 1000, "t": 20, "demi_vie": 10}, 250),
      "décroissance : 1000·½² = 250 (2 demi-vies)")

# ── 2) EXACTITUDE — constantes sourcées (valeurs de référence) ──
check(approx("force_poids", {"m": 10}, 98.0665), "Poids = 10·g = 98.0665 N")
check(approx("energie_potentielle_pesanteur", {"m": 2, "h": 10}, 196.133), "Ep = m·g·h = 196.133 J")
check(approx("energie_repos", {"m": 1}, 8.98755e16, rel=1e-3), "E = mc² ≈ 8.98755e16 J (1 kg)")
check(approx("energie_gaz_parfait", {"n": 1, "T": 300}, 3741.51, rel=1e-4), "U = 3/2·nRT ≈ 3741.5 J")
check(approx("force_coulomb", {"q1": 1e-6, "q2": 1e-6, "r": 0.1}, 0.898755, rel=1e-4),
      "Coulomb 1µC/1µC à 0.1 m ≈ 0.8988 N")
check(approx("champ_electrique", {"q": 1e-6, "r": 0.1}, 898755, rel=1e-4), "E = k·q/r² (1µC à 0.1 m)")
check(approx("energie_photon", {"frequence": 5e14}, 3.31304e-19, rel=1e-4), "E = h·ν (5e14 Hz)")
check(approx("energie_masse_defaut", {"delta_m": 1}, 8.98755e16, rel=1e-3), "E = Δm·c² (1 kg)")

# ── 3) ANCRES PHYSIQUES EXTERNES CONNUES (validation NON circulaire) ──
TERRE_M, TERRE_R = 5.972e24, 6.371e6
check(approx("gravite_surface", {"M": TERRE_M, "r": TERRE_R}, 9.81, rel=2e-3),
      "gravité de surface Terre ≈ 9.81 m/s²")
check(approx("vitesse_liberation", {"M": TERRE_M, "r": TERRE_R}, 11186, rel=5e-3),
      "vitesse de libération Terre ≈ 11.19 km/s")
# période orbitale d'1 UA autour du Soleil ≈ 1 an = 3.156e7 s
check(approx("periode_orbitale", {"a": 1.496e11, "M": 1.989e30}, 3.156e7, rel=5e-3),
      "période orbitale 1 UA ≈ 1 an")
check(approx("ph", {"concentration_H": 1e-7}, 7.0), "pH eau neutre = 7")
check(approx("ph", {"concentration_H": 1e-3}, 3.0), "pH [H+]=1e-3 = 3")
check(approx("poh", {"concentration_OH": 1e-7}, 7.0), "pOH eau neutre = 7")

# ── 4) SOUNDNESS — grandeur inconnue / paramètre manquant -> HORS ──
check(P.calcule("teleportation", {"m": 1})[0] == P.HORS, "grandeur inconnue -> HORS")
check(P.calcule("energie_cinetique", {"m": 2})[0] == P.HORS, "paramètre v manquant -> HORS")
check(P.calcule("force_coulomb", {"q1": 1, "q2": 1})[0] == P.HORS, "paramètre r manquant -> HORS")
check(P.calcule("quantite_mouvement", "pas_un_dict")[0] == P.HORS, "params non-dict -> HORS")

# ── 5) SOUNDNESS — domaine physique invalide -> HORS (jamais un nombre absurde) ──
check(P.calcule("force_poids", {"m": -5})[0] == P.HORS, "masse négative -> HORS")
check(P.calcule("energie_cinetique", {"m": -2, "v": 3})[0] == P.HORS, "masse négative (Ec) -> HORS")
check(P.calcule("rendement_carnot", {"Tc": 600, "Th": 300})[0] == P.HORS, "Th<Tc -> HORS")
check(P.calcule("rendement_carnot", {"Tc": 300, "Th": 300})[0] == P.HORS, "Th=Tc -> HORS")
check(P.calcule("rendement_carnot", {"Tc": -10, "Th": 300})[0] == P.HORS, "Tc<0 (Kelvin) -> HORS")
check(P.calcule("force_coulomb", {"q1": 1, "q2": 1, "r": 0})[0] == P.HORS, "r=0 -> HORS")
check(P.calcule("vitesse_liberation", {"M": -1, "r": 100})[0] == P.HORS, "M<0 -> HORS")
check(P.calcule("decroissance_radioactive", {"N0": 100, "t": 5, "demi_vie": 0})[0] == P.HORS,
      "demi-vie=0 -> HORS")
check(P.calcule("energie_masse_defaut", {"delta_m": -1})[0] == P.HORS, "Δm<0 -> HORS")
check(P.calcule("ph", {"concentration_H": 0})[0] == P.HORS, "[H+]=0 -> HORS (log indéfini)")
check(P.calcule("ph", {"concentration_H": -1})[0] == P.HORS, "[H+]<0 -> HORS")

# ── 6) SOUNDNESS — types invalides (bool/str) -> HORS ──
check(P.calcule("energie_cinetique", {"m": True, "v": 3})[0] == P.HORS, "bool n'est pas un nombre -> HORS")
check(P.calcule("quantite_mouvement", {"m": "deux", "v": 3})[0] == P.HORS, "str -> HORS")

# ── 7) DÉTERMINISME + UNITÉ rendue ──
check(P.calcule("energie_cinetique", {"m": 2, "v": 3}) == P.calcule("energie_cinetique", {"m": 2, "v": 3}),
      "déterminisme")
check(P.calcule("force_poids", {"m": 1})[2] == "N", "unité du poids = N")
check(len(P.grandeurs()) == 26, "26 grandeurs au catalogue")

print(f"\n=== valide_physique : {ok}/{ok+ko} ===")
import sys
sys.exit(0 if ko == 0 else 1)
