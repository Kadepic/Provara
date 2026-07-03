"""
VALIDE liaisons_chimiques.py — held-out ADVERSE. Exactitude ancrée sur des FAITS CHIMIQUES CONNUS, non recalculés
par la même expression : H–H (Δχ=0) covalente non polaire, H–Cl (Δχ=0.96) covalente polaire, Na–Cl (Δχ=2.23)
ionique avec ~71 % de caractère ionique (valeur de manuel via la formule de Pauling), Cs–F (Δχ=3.19) la liaison la
plus ionique ~92 %. Bornes de classification (0.4 et 1.7) testées des deux côtés. SOUNDNESS : électronégativité ≤ 0
ou type non numérique (bool/str) -> ValueError (jamais un faux résultat). Déterminisme vérifié.
"""
import liaisons_chimiques as L

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


# χ Pauling : H=2.20, C=2.55, N=3.04, O=3.44, F=3.98, Na=0.93, Cl=3.16, Cs=0.79, Si=1.90

# ── 1) NATURE — ancres qualitatives connues ──
check(L.nature_liaison(2.20, 2.20) == "covalente_non_polaire", "H–H -> covalente_non_polaire")
check(L.nature_liaison(2.20, 3.16) == "covalente_polaire", "H–Cl -> covalente_polaire")
check(L.nature_liaison(0.93, 3.16) == "ionique", "Na–Cl -> ionique")
check(L.nature_liaison(0.79, 3.98) == "ionique", "Cs–F -> ionique")
check(L.nature_liaison(2.55, 2.20) == "covalente_non_polaire", "C–H (Δχ=0.35) -> covalente_non_polaire")
check(L.nature_liaison(2.20, 3.04) == "covalente_polaire", "N–H (Δχ=0.84) -> covalente_polaire")
check(L.nature_liaison(3.16, 0.93) == "ionique", "symétrie χ1<->χ2 -> ionique")

# ── 2) BORNES de classification (0.4 et 1.7), testées des deux côtés ──
check(L.nature_liaison(2.0, 2.39) == "covalente_non_polaire", "Δχ=0.39 (<0.4) -> non polaire")
check(L.nature_liaison(2.0, 2.40) == "covalente_polaire", "Δχ=0.40 (=0.4) -> polaire")
check(L.nature_liaison(2.0, 3.69) == "covalente_polaire", "Δχ=1.69 (<1.7) -> polaire")
check(L.nature_liaison(2.0, 3.70) == "ionique", "Δχ=1.70 (=1.7) -> ionique")

# ── 3) DIFFÉRENCE — valeur exacte |χ1−χ2| ──
check(abs(L.difference_electronegativite(2.20, 3.16) - 0.96) < 1e-9, "|2.20−3.16| = 0.96")
check(abs(L.difference_electronegativite(0.79, 3.98) - 3.19) < 1e-9, "|0.79−3.98| = 3.19")
check(abs(L.difference_electronegativite(2.20, 2.20) - 0.0) < 1e-9, "|2.20−2.20| = 0")
check(L.difference_electronegativite(0.93, 3.16) == L.difference_electronegativite(3.16, 0.93), "diff symétrique")

# ── 4) POURCENTAGE IONIQUE — ancres de manuel (Pauling), non recalculées par l'appel ──
check(abs(L.pourcentage_ionique(2.20, 2.20) - 0.0) < 1e-6, "%ionique H–H = 0")
check(abs(L.pourcentage_ionique(2.20, 3.16) - 20.5784) < 1e-3, "%ionique H–Cl ≈ 20.6 %")
check(abs(L.pourcentage_ionique(0.93, 3.16) - 71.1548) < 1e-3, "%ionique Na–Cl ≈ 71 %")
check(abs(L.pourcentage_ionique(0.79, 3.98) - 92.1450) < 1e-3, "%ionique Cs–F ≈ 92 %")

# ── 5) MONOTONIE — %ionique croît avec Δχ ──
check(L.pourcentage_ionique(2.20, 2.20) < L.pourcentage_ionique(2.20, 3.16) < L.pourcentage_ionique(0.93, 3.16)
      < L.pourcentage_ionique(0.79, 3.98), "%ionique strictement croissant avec Δχ")
check(0.0 <= L.pourcentage_ionique(0.79, 3.98) <= 100.0, "%ionique borné dans [0,100]")

# ── 6) SOUNDNESS — électronégativité ≤ 0 -> ValueError ──
check(leve(L.difference_electronegativite, 0, 3.16), "χ=0 -> ValueError")
check(leve(L.difference_electronegativite, -1.0, 3.16), "χ<0 -> ValueError")
check(leve(L.nature_liaison, 0.93, 0), "nature χ=0 -> ValueError")
check(leve(L.nature_liaison, -2.2, 3.16), "nature χ<0 -> ValueError")
check(leve(L.pourcentage_ionique, 2.2, 0.0), "%ionique χ=0 -> ValueError")
check(leve(L.pourcentage_ionique, 2.2, -0.5), "%ionique χ<0 -> ValueError")

# ── 7) SOUNDNESS — types invalides (bool/str/None) -> ValueError ──
check(leve(L.nature_liaison, True, 3.16), "bool n'est pas une électronégativité -> ValueError")
check(leve(L.difference_electronegativite, 2.2, False), "bool (False) -> ValueError")
check(leve(L.pourcentage_ionique, "deux", 3.16), "str -> ValueError")
check(leve(L.nature_liaison, None, 3.16), "None -> ValueError")

# ── 8) DÉTERMINISME ──
check(L.nature_liaison(0.93, 3.16) == L.nature_liaison(0.93, 3.16), "déterminisme nature")
check(L.pourcentage_ionique(0.93, 3.16) == L.pourcentage_ionique(0.93, 3.16), "déterminisme %ionique")

print(f"\n=== valide_liaisons_chimiques : {ok}/{ok+ko} ===")
import sys
sys.exit(0 if ko == 0 else 1)
