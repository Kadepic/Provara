"""
VALIDE recettes.py — held-out ADVERSE.

Exactitude ANCRÉE sur des équivalences culinaires CONNUES (pas re-dérivées par la même expression) :
  recette 4→6 personnes = ×1.5 ; 1 tasse = 240 ml ; 2 c.à.s = 30 ml ; 3 c.à.c = 1 c.à.s ;
  240 ml d'eau = 240 g (densité 1).
+ SOUNDNESS : portions ≤ 0, quantité < 0, unité inconnue, conversion volume↔masse sans densité
  conventionnelle -> ValueError (abstention). Aucun de ces cas ne renvoie un faux.
+ DÉTERMINISME : deux appels identiques -> résultat identique.
"""
import recettes as R

ok = 0
ko = 0


def check(cond, label):
    global ok, ko
    if cond:
        ok += 1
    else:
        ko += 1
        print(f"  FAIL: {label}")


def approx(a, b, tol=1e-9):
    return abs(a - b) <= tol * max(1.0, abs(b)) + 1e-12


def leve(fn, *a, **k):
    try:
        fn(*a, **k)
        return False
    except ValueError:
        return True
    except Exception:
        return False


# ── 1) MISE À L'ÉCHELLE — ancres connues ──
check(approx(R.adapte_quantite(1, 4, 6), 1.5), "1 unité (4→6) = ×1.5 = 1.5")
check(approx(R.adapte_quantite(2, 4, 6), 3.0), "2 (4→6) = 3.0")
check(approx(R.adapte_quantite(200, 4, 6), 300.0), "200 g (4→6) = 300 g")
check(approx(R.adapte_quantite(3, 6, 2), 1.0), "3 (6→2) = 1.0 (réduction ÷3)")
check(approx(R.adapte_quantite(5, 5, 5), 5.0), "5 (5→5) = identité")
check(approx(R.adapte_quantite(10, 4, 0), 0.0), "0 portion cible -> 0 quantité")
check(approx(R.facteur_echelle(4, 6), 1.5), "facteur 4→6 = 1.5")
check(approx(R.facteur_echelle(2, 8), 4.0), "facteur 2→8 = 4.0")

# ── 2) CONVERSIONS DE VOLUME — facteurs conventionnels ──
check(approx(R.convertir_mesure(1, "tasse", "ml"), 240.0), "1 tasse = 240 ml")
check(approx(R.convertir_mesure(2, "cuillere_soupe", "ml"), 30.0), "2 c.à.s = 30 ml")
check(approx(R.convertir_mesure(1, "cuillere_soupe", "ml"), 15.0), "1 c.à.s = 15 ml")
check(approx(R.convertir_mesure(1, "cuillere_cafe", "ml"), 5.0), "1 c.à.c = 5 ml")
check(approx(R.convertir_mesure(2, "cuillere_cafe", "ml"), 10.0), "2 c.à.c = 10 ml")
check(approx(R.convertir_mesure(3, "cuillere_cafe", "cuillere_soupe"), 1.0), "3 c.à.c = 1 c.à.s")
check(approx(R.convertir_mesure(1, "tasse", "cuillere_soupe"), 16.0), "1 tasse = 16 c.à.s")
check(approx(R.convertir_mesure(1, "l", "ml"), 1000.0), "1 L = 1000 ml")
check(approx(R.convertir_mesure(1, "dl", "ml"), 100.0), "1 dl = 100 ml")
check(approx(R.convertir_mesure(1, "cl", "ml"), 10.0), "1 cl = 10 ml")
check(approx(R.convertir_mesure(240, "ml", "tasse"), 1.0), "240 ml = 1 tasse")

# alias robustes (normalisation)
check(approx(R.convertir_mesure(1, "Tasse", "ml"), 240.0), "alias casse 'Tasse'")
check(approx(R.convertir_mesure(1, "cup", "ml"), 240.0), "alias 'cup' = tasse")
check(approx(R.convertir_mesure(1, "cuillère à soupe", "ml"), 15.0), "alias 'cuillère à soupe'")

# ── 3) CONVERSIONS DE MASSE ──
check(approx(R.convertir_mesure(1, "kg", "g"), 1000.0), "1 kg = 1000 g")
check(approx(R.convertir_mesure(500, "g", "kg"), 0.5), "500 g = 0.5 kg")
check(approx(R.convertir_mesure(1000, "mg", "g"), 1.0), "1000 mg = 1 g")

# ── 4) VOLUME ↔ MASSE pour l'EAU (densité 1) ──
check(approx(R.convertir_mesure(240, "ml", "g"), 240.0), "240 ml eau = 240 g")
check(approx(R.convertir_mesure(240, "g", "ml"), 240.0), "240 g eau = 240 ml")
check(approx(R.convertir_mesure(1, "tasse", "g"), 240.0), "1 tasse eau = 240 g")
check(approx(R.convertir_mesure(1, "l", "kg"), 1.0), "1 L eau = 1 kg")
check(approx(R.convertir_mesure(1, "cuillere_soupe", "g"), 15.0), "1 c.à.s eau = 15 g")

# ── 5) TEMPS DE CUISSON ADAPTÉ ──
check(approx(R.temps_cuisson_adapte(30, 4, 6, exposant=0.0), 30.0), "exposant 0 -> temps inchangé")
check(approx(R.temps_cuisson_adapte(30, 4, 6, exposant=1.0), 45.0), "exposant 1 -> 30·1.5 = 45")
check(approx(R.temps_cuisson_adapte(20, 2, 2, exposant=1.0), 20.0), "portions égales -> temps inchangé")

# ── 6) SOUNDNESS — abstention (ValueError), jamais un faux ──
check(leve(R.adapte_quantite, 2, 0, 6), "portions_origine = 0 -> ValueError")
check(leve(R.adapte_quantite, 2, -4, 6), "portions_origine < 0 -> ValueError")
check(leve(R.adapte_quantite, -2, 4, 6), "quantite < 0 -> ValueError")
check(leve(R.adapte_quantite, 2, 4, -6), "portions_cible < 0 -> ValueError")
check(leve(R.facteur_echelle, 1, -1), "facteur portions_cible < 0 -> ValueError")
check(leve(R.facteur_echelle, 0, 6), "facteur portions_origine 0 -> ValueError")
check(leve(R.convertir_mesure, 1, "pincee", "ml"), "unité départ inconnue -> ValueError")
check(leve(R.convertir_mesure, 1, "tasse", "furlong"), "unité arrivée inconnue -> ValueError")
check(leve(R.convertir_mesure, -1, "tasse", "ml"), "valeur < 0 -> ValueError")
check(leve(R.convertir_mesure, 1, "tasse", "g", ingredient="farine"), "vol↔masse farine (densité≠1) -> ValueError")
check(leve(R.convertir_mesure, 1, "g", "tasse", ingredient="huile"), "masse↔vol huile -> ValueError")
check(leve(R.temps_cuisson_adapte, 30, 4, 6, exposant=-1), "exposant < 0 -> ValueError")
check(leve(R.temps_cuisson_adapte, 30, 0, 6), "temps: portions_origine 0 -> ValueError")
check(leve(R.adapte_quantite, 2, True, 6), "bool rejeté (portions) -> ValueError")
check(leve(R.convertir_mesure, 1, 5, "ml"), "unité non textuelle -> ValueError")

# ── 7) DÉTERMINISME ──
check(R.adapte_quantite(2, 4, 6) == R.adapte_quantite(2, 4, 6), "déterminisme adapte_quantite")
check(R.convertir_mesure(1, "tasse", "ml") == R.convertir_mesure(1, "tasse", "ml"), "déterminisme convertir_mesure")

print(f"\n=== valide_recettes : {ok}/{ok+ko} ===")
import sys
sys.exit(0 if ko == 0 else 1)
