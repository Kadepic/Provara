"""
VALIDE commerce_international.py — held-out ADVERSE.

Ancres CONNUES non circulaires : valeurs calculées À LA MAIN (pas re-dérivées par l'expression du module dans le
test). Énoncé pivot : X=120, M=100 -> balance +20 (excédent), couverture 120 %. Loi de Ricardo : avantage
comparatif au coût d'opportunité le PLUS BAS. + SOUNDNESS (importations <= 0 pour la couverture, flux négatifs,
coûts d'opportunité <= 0, indices de prix <= 0, NaN/inf, type non numérique, bool -> ValueError) +
DÉTERMINISME (deux appels identiques).
"""
import commerce_international as M

ok = 0
ko = 0


def check(cond, label):
    global ok, ko
    if cond:
        ok += 1
    else:
        ko += 1
        print(f"  FAIL: {label}")


def approx(val, attendu, tol=1e-9):
    return isinstance(val, float) and abs(val - attendu) <= tol * (1 + abs(attendu))


def leve(fn, *a):
    try:
        fn(*a)
        return False
    except ValueError:
        return True
    except Exception:
        return False


# ── 1) BALANCE COMMERCIALE : X − M (énoncé pivot + signes) ──
check(approx(M.balance_commerciale(120, 100), 20.0), "X=120,M=100 -> balance = +20 (énoncé)")
check(approx(M.balance_commerciale(100, 120), -20.0), "X=100,M=120 -> balance = −20 (déficit)")
check(approx(M.balance_commerciale(100, 100), 0.0), "X=M=100 -> balance = 0 (équilibre)")
check(approx(M.balance_commerciale(500, 0), 500.0), "M=0 admis pour la balance -> +500")
check(approx(M.balance_commerciale(0, 250), -250.0), "X=0 -> balance = −250")

# ── 2) NATURE DE LA BALANCE : excédent / déficit / équilibre ──
check(M.nature_balance(120, 100) == M.EXCEDENT, "X>M -> excédent")
check(M.nature_balance(100, 120) == M.DEFICIT, "X<M -> déficit")
check(M.nature_balance(100, 100) == M.EQUILIBRE, "X=M -> équilibre")

# ── 3) TAUX DE COUVERTURE : X / M · 100 ──
check(approx(M.taux_couverture(120, 100), 120.0), "X=120,M=100 -> couverture 120 % (énoncé)")
check(approx(M.taux_couverture(100, 120), 83.333333), "X=100,M=120 -> 83.333333 % (déficitaire)")
check(approx(M.taux_couverture(100, 100), 100.0), "X=M -> couverture = 100 %")
check(approx(M.taux_couverture(0, 100), 0.0), "X=0 -> couverture = 0 %")
check(approx(M.taux_couverture(250, 50), 500.0), "X=250,M=50 -> 500 %")

# ── 4) AVANTAGE COMPARATIF (Ricardo) : le plus FAIBLE coût d'opportunité ──
check(M.avantage_comparatif(0.5, 0.8) == "A", "coA=0.5 < coB=0.8 -> avantage A")
check(M.avantage_comparatif(2.0, 1.0) == "B", "coB=1.0 < coA=2.0 -> avantage B")
check(M.avantage_comparatif(1.0, 1.0) == M.AUCUN, "coûts d'opportunité égaux -> aucun avantage (autarcie)")
# Exemple Ricardo classique : Portugal (vin) coût d'opp 80/90, Angleterre (vin) 120/100 -> avantage Portugal (A)
check(M.avantage_comparatif(80 / 90, 120 / 100) == "A", "vin : Portugal 0.889 < Angleterre 1.2 -> A (Portugal)")
# le drap : Portugal 90/80=1.125 vs Angleterre 100/120=0.833 -> avantage Angleterre (B)
check(M.avantage_comparatif(90 / 80, 100 / 120) == "B", "drap : Angleterre 0.833 < Portugal 1.125 -> B (Angleterre)")

# ── 5) TERMES DE L'ÉCHANGE : Px / Pm · 100 ──
check(approx(M.termes_echange(100, 100), 100.0), "Px=Pm -> termes = 100 (neutre)")
check(approx(M.termes_echange(110, 100), 110.0), "Px=110,Pm=100 -> 110 (amélioration)")
check(approx(M.termes_echange(100, 125), 80.0), "Px=100,Pm=125 -> 80 (dégradation)")
check(approx(M.termes_echange(120, 96), 125.0), "Px=120,Pm=96 -> 125")

# ── 6) DÉTERMINISME ──
check(M.balance_commerciale(120, 100) == M.balance_commerciale(120, 100), "déterministe balance_commerciale")
check(M.taux_couverture(120, 100) == M.taux_couverture(120, 100), "déterministe taux_couverture")
check(M.avantage_comparatif(0.5, 0.8) == M.avantage_comparatif(0.5, 0.8), "déterministe avantage_comparatif")
check(M.termes_echange(110, 100) == M.termes_echange(110, 100), "déterministe termes_echange")

# ── 7) SOUNDNESS — domaines invalides -> ValueError (abstention, jamais un faux) ──
check(leve(M.taux_couverture, 120, 0), "importations = 0 (couverture) -> ValueError")
check(leve(M.taux_couverture, 120, -50), "importations < 0 (couverture) -> ValueError")
check(leve(M.taux_couverture, -10, 100), "exportations < 0 (couverture) -> ValueError")
check(leve(M.balance_commerciale, -1, 100), "exportations < 0 (balance) -> ValueError")
check(leve(M.balance_commerciale, 100, -1), "importations < 0 (balance) -> ValueError")
check(leve(M.avantage_comparatif, 0.0, 0.8), "coût d'opportunité = 0 -> ValueError")
check(leve(M.avantage_comparatif, -0.5, 0.8), "coût d'opportunité < 0 -> ValueError")
check(leve(M.avantage_comparatif, 0.5, -0.8), "coût d'opportunité B < 0 -> ValueError")
check(leve(M.termes_echange, 0, 100), "indice prix export = 0 -> ValueError")
check(leve(M.termes_echange, 100, 0), "indice prix import = 0 -> ValueError")
check(leve(M.termes_echange, 100, -5), "indice prix import < 0 -> ValueError")

# ── 8) SOUNDNESS — entrées non numériques / non finies / booléennes -> ValueError ──
check(leve(M.balance_commerciale, float("nan"), 100), "NaN -> ValueError")
check(leve(M.balance_commerciale, float("inf"), 100), "inf -> ValueError")
check(leve(M.taux_couverture, "120", 100), "chaîne -> ValueError")
check(leve(M.balance_commerciale, True, 100), "bool exportations (True) -> ValueError")
check(leve(M.avantage_comparatif, None, 0.8), "None coût d'opportunité -> ValueError")
check(leve(M.termes_echange, 100, float("nan")), "indice prix import NaN -> ValueError")

print(f"\n=== valide_commerce_international : {ok}/{ok+ko} ===")
import sys; sys.exit(0 if ko == 0 else 1)
