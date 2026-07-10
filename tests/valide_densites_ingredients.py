"""
GATE ADVERSE — densites_ingredients.

ANCRES NON CIRCULAIRES (aucune n'est recalculée avec la fonction testée) :
  • Densités conventionnelles écrites EN DUR (livres de cuisine) : eau 1.00, miel 1.42, huile 0.92, ...
  • 250 mL d'eau = 250 g EXACTEMENT (densité 1).
  • 1 cup coutumière de farine ≈ 236.588 × 0.53 = 125 g ; la référence des livres est 120-125 g :
    l'INTERVALLE [masse−inc, masse+inc] rendu doit CONTENIR 120 et 125 (ancre forte, non circulaire).
  • 1 cup de sucre ≈ 236.588 × 0.85 = 201 g ≈ 200 g (référence livres) : l'intervalle doit contenir 200.
  • 1 cup légale = 240 mL exact ; 1 cup coutumière = 236.588 mL.
  • Miel PLUS dense que l'eau, huile MOINS : ordre 1.42 > 1.00 > 0.92 vérifié.
  • ROUND-TRIP HONNÊTE (aucune sur-affirmation) : EXACT pour l'EAU (densité 1) sur toute valeur ;
    NON exact en général (contre-exemple mesuré farine t55 651.593321 mL) mais STABLE à ~10 chiffres
    significatifs (|Δ| ≤ 1e-9·|v|) — prouvé par un balayage LARGE de 3600 volumes NON ronds (pire mesuré
    8.56e-10 < 1e-9), pas par une poignée de volumes triés sur le volet.
"""
from __future__ import annotations

import densites_ingredients as di
import recettes

ok = 0
ko = 0


def check(cond, label):
    global ok, ko
    if cond:
        ok += 1
    else:
        ko += 1
        print(f"  FAIL: {label}")


def leve(fn, *a, **k) -> bool:
    try:
        fn(*a, **k)
        return False
    except ValueError:
        return True
    except Exception:
        return False


# ── (a) MASSE VOLUMIQUE : ancres EN DUR (valeurs conventionnelles) ───────────────────────────────────────────────
ANCRES_DENSITE = {
    "eau": 1.00, "lait": 1.03, "huile": 0.92, "farine t55": 0.53, "sucre en poudre": 0.85,
    "sucre glace": 0.56, "sel fin": 1.20, "beurre": 0.91, "miel": 1.42, "riz cru": 0.85,
    "cacao en poudre": 0.41, "levure chimique": 0.72, "creme liquide": 1.01,
}
for ing, d in ANCRES_DENSITE.items():
    res = di.masse_volumique(ing)
    check(isinstance(res, tuple) and len(res) == 2, f"masse_volumique({ing!r}) rend un couple")
    check(abs(res[0] - d) < 1e-12, f"densité {ing!r} == {d}")
    check(res[1] > 0, f"incertitude relative {ing!r} > 0 (valeur apparente, jamais nue)")

# COUPLE, jamais scalaire nu
check(not isinstance(di.masse_volumique("eau"), (int, float)), "masse_volumique ne rend PAS un scalaire nu")

# ── ORDRE physique (ancre non circulaire : le miel coule, l'huile flotte) ────────────────────────────────────────
d_miel = di.masse_volumique("miel")[0]
d_eau = di.masse_volumique("eau")[0]
d_huile = di.masse_volumique("huile")[0]
check(d_miel > d_eau, "miel PLUS dense que l'eau")
check(d_huile < d_eau, "huile MOINS dense que l'eau")
check(d_miel > d_eau > d_huile, "ordre miel > eau > huile")

# alias
check(di.masse_volumique("farine")[0] == 0.53, "alias 'farine' -> farine t55")
check(di.masse_volumique("FARINE T55")[0] == 0.53, "casse ignorée")
check(di.masse_volumique("crème liquide")[0] == 1.01, "accent 'crème' normalisé")
check(di.masse_volumique("  sucre  ")[0] == 0.85, "alias 'sucre' + espaces")
check(di.masse_volumique("water")[0] == 1.00, "alias EN 'water' -> eau")

# ── (b/c) CONVERSIONS + ancres fortes ────────────────────────────────────────────────────────────────────────────
# 250 mL d'eau = 250 g EXACTEMENT
m_eau = di.volume_vers_masse(250, "eau")
check(m_eau[0] == 250.0, "250 mL d'eau = 250 g exactement")

# 1 cup coutumière de FARINE : intervalle doit contenir 120-125 g (référence livres de cuisine)
masse_f, inc_f = di.volume_vers_masse(236.588, "farine t55")
bas_f, haut_f = masse_f - inc_f, masse_f + inc_f
check(abs(masse_f - 125.39164) < 1e-4, "masse cup farine ≈ 125 g (236.588×0.53)")
check(bas_f <= 120.0 <= haut_f, "intervalle farine CONTIENT 120 g (référence)")
check(bas_f <= 125.0 <= haut_f, "intervalle farine CONTIENT 125 g (référence)")

# 1 cup de SUCRE : intervalle doit contenir 200 g (référence livres)
masse_s, inc_s = di.volume_vers_masse(236.588, "sucre en poudre")
check(abs(masse_s - 201.1) < 0.5, "masse cup sucre ≈ 201 g (236.588×0.85)")
check(masse_s - inc_s <= 200.0 <= masse_s + inc_s, "intervalle sucre CONTIENT 200 g (référence)")

# incertitude_g cohérente = masse × inc_rel (second chemin indépendant)
for ing in ("miel", "beurre", "cacao en poudre"):
    d, ir = di.masse_volumique(ing)
    mg, ig = di.volume_vers_masse(100.0, ing)
    check(abs(mg - 100.0 * d) < 1e-9, f"masse 100mL {ing} == 100×densité")
    check(abs(ig - mg * ir) < 1e-9, f"incertitude_g {ing} == masse×inc_rel")

# masse_vers_volume : ancre à la main (100 g de miel -> 100/1.42 = 70.42 mL)
vol_miel = di.masse_vers_volume(100.0, "miel")
check(abs(vol_miel[0] - 70.42253521) < 1e-6, "100 g de miel -> 70.42 mL (100/1.42)")

# couple toujours (jamais scalaire nu)
check(isinstance(di.volume_vers_masse(10, "eau"), tuple), "volume_vers_masse rend un couple")
check(isinstance(di.masse_vers_volume(10, "eau"), tuple), "masse_vers_volume rend un couple")

# ── ROUND-TRIP : propriété HONNÊTE (pas d'exactitude UNIVERSELLE — cf. audit) ─────────────────────────────────────
# (1) EAU (densité 1) : round-trip EXACT pour toute valeur ≤10 chiffres significatifs (v·1 arrondi = v).
for v in [1.0, 3.14159, 651.593321, 236.588, 999999.9999, 0.001234567, 42.42424242]:
    m_e = di.volume_vers_masse(v, "eau")[0]
    check(di.masse_vers_volume(m_e, "eau")[0] == v, f"eau round-trip EXACT v={v}")

# (2) CONTRE-EXEMPLE de l'audit : farine t55 651.593321 mL n'est PAS exact — on ne SUR-affirme pas.
#     Attendu EN DUR (calculé à la main hors des fonctions) : round10(651.593321·0.53)=345.3444601 ;
#     round10(345.3444601/0.53)=651.5933209 ≠ 651.593321.
m_cx = di.volume_vers_masse(651.593321, "farine t55")[0]
check(abs(m_cx - 345.3444601) < 1e-7, "farine 651.593321 mL -> 345.3444601 g (round10 du produit)")
v_cx = di.masse_vers_volume(m_cx, "farine t55")[0]
check(abs(v_cx - 651.5933209) < 1e-7, "retour -> 651.5933209 mL (round10 du quotient)")
check(v_cx != 651.593321, "farine round-trip PAS exact (honnêteté : 651.5933209 != 651.593321)")
check(abs(v_cx - 651.593321) <= 1e-9 * 651.593321, "mais STABLE à ~10 chiffres (|Δ| ≤ 1e-9·v)")

# (3) BALAYAGE LARGE, volumes NON ronds (jamais triés sur le volet) : la stabilité ~10 chiffres tient
#     pour TOUS les ingrédients. Pire mesuré indépendamment = 8.56e-10 (< 1e-9). EAU reste EXACTE.
INGR_BOUCLE = ["eau", "lait", "huile", "farine t55", "sucre en poudre", "sel fin",
               "miel", "levure chimique", "cacao en poudre"]
pire = 0.0
n_bcl = 0
for ing in INGR_BOUCLE:
    for k in range(1, 401):
        v = 0.5 + k * 7.31234567  # 9-10 chiffres significatifs, non ronds
        n_bcl += 1
        masse = di.volume_vers_masse(v, ing)[0]
        v2 = di.masse_vers_volume(masse, ing)[0]
        rel = abs(v2 - v) / v
        if rel > pire:
            pire = rel
check(n_bcl == 3600, f"balayage large = {n_bcl} volumes non ronds (9×400)")
check(pire <= 1e-9, f"round-trip STABLE ≤1e-9 rel sur {n_bcl} volumes non ronds (pire={pire:.2e})")
check(pire > 0.0, "round-trip PAS trivialement exact (pire > 0 : la garantie forte serait un faux)")

# ── (d) MESURES ANGLO-SAXONNES : ancres EN DUR ───────────────────────────────────────────────────────────────────
check(di.cup_vers_ml(1, "legale") == 240.0, "1 cup légale = 240 mL exact")
check(abs(di.cup_vers_ml(1, "coutumiere") - 236.588) < 1e-9, "1 cup coutumière = 236.588 mL")
check(di.cup_vers_ml(2, "legale") == 480.0, "2 cups légales = 480 mL")
check(di.cup_vers_ml(1, "customary") == di.cup_vers_ml(1, "coutumiere"), "alias 'customary'")
check(di.cup_vers_ml(1, "fda") == 240.0, "alias 'fda' -> légale")
check(abs(di.tablespoon_us_vers_ml(1) - 14.787) < 1e-9, "1 tbsp US = 14.787 mL")
check(abs(di.teaspoon_us_vers_ml(1) - 4.929) < 1e-9, "1 tsp US = 4.929 mL")
check(abs(di.tablespoon_us_vers_ml(3) - 44.361) < 1e-6, "3 tbsp = 44.361 mL")
# tablespoon ≈ 3 teaspoons (fait culinaire non circulaire) : 14.787 ≈ 3×4.929 = 14.787
check(abs(di.tablespoon_us_vers_ml(1) - di.teaspoon_us_vers_ml(3)) < 1e-9, "1 tbsp == 3 tsp (14.787=3×4.929)")

# CONVENTION de cup NON précisée / inconnue -> ValueError (abstention, jamais deviné)
check(leve(di.cup_vers_ml, 1), "cup sans convention -> ValueError")
check(leve(di.cup_vers_ml, 1, None), "cup convention None -> ValueError")
check(leve(di.cup_vers_ml, 1, "grande"), "cup convention inconnue -> ValueError")
check(leve(di.cup_vers_ml, 1, 240), "cup convention non-str -> ValueError")

# ── (e) MISE À L'ÉCHELLE (déléguée à recettes) ───────────────────────────────────────────────────────────────────
# ancre : recette 4->6 = facteur ×1.5 ; SECOND chemin = recettes.adapte_quantite directement
rec = {"farine": 200.0, "sucre": 100.0, "oeufs": 3.0}
out = di.adapte_recette(rec, 4, 6)
check(out["farine"] == recettes.adapte_quantite(200.0, 4, 6), "adapte_recette délègue (farine)")
check(out["farine"] == 300.0, "200 g farine 4->6 portions = 300 g (×1.5)")
check(out["sucre"] == 150.0, "100 g sucre 4->6 = 150 g")
check(out["oeufs"] == 4.5, "3 oeufs 4->6 = 4.5")
# liste de couples conserve la structure
outl = di.adapte_recette([("beurre", 50.0), ("miel", 20.0)], 2, 4)
check(outl == [("beurre", 100.0), ("miel", 40.0)], "adapte_recette liste de couples ×2")

# ── SOUNDNESS : abstentions structurelles ────────────────────────────────────────────────────────────────────────
# ingrédient hors catalogue -> ValueError (jamais deviné)
check(leve(di.masse_volumique, "uranium"), "ingrédient inventé -> ValueError")
check(leve(di.masse_volumique, "chocolat fondu"), "ingrédient hors catalogue -> ValueError")
check(leve(di.volume_vers_masse, 100, "plutonium"), "volume_vers_masse ingrédient inconnu -> ValueError")
check(leve(di.masse_vers_volume, 100, "sable"), "masse_vers_volume ingrédient inconnu -> ValueError")
# ingrédient non textuel
check(leve(di.masse_volumique, 42), "ingrédient numérique -> ValueError")
check(leve(di.masse_volumique, None), "ingrédient None -> ValueError")
check(leve(di.masse_volumique, ""), "ingrédient vide -> ValueError")
# volume / masse <= 0
check(leve(di.volume_vers_masse, 0, "eau"), "volume 0 -> ValueError")
check(leve(di.volume_vers_masse, -5, "eau"), "volume négatif -> ValueError")
check(leve(di.masse_vers_volume, 0, "eau"), "masse 0 -> ValueError")
check(leve(di.masse_vers_volume, -1, "eau"), "masse négative -> ValueError")
# bool REFUSÉ (True n'est pas 1)
check(leve(di.volume_vers_masse, True, "eau"), "volume bool True -> ValueError")
check(leve(di.masse_vers_volume, False, "eau"), "masse bool False -> ValueError")
check(leve(di.cup_vers_ml, True, "legale"), "cup nombre bool -> ValueError")
# NaN / inf REFUSÉS
check(leve(di.volume_vers_masse, float("nan"), "eau"), "volume NaN -> ValueError")
check(leve(di.volume_vers_masse, float("inf"), "eau"), "volume inf -> ValueError")
check(leve(di.masse_vers_volume, float("-inf"), "eau"), "masse -inf -> ValueError")
# str là où un nombre est attendu
check(leve(di.volume_vers_masse, "100", "eau"), "volume str -> ValueError")
check(leve(di.tablespoon_us_vers_ml, "1"), "tbsp str -> ValueError")
check(leve(di.tablespoon_us_vers_ml, 0), "tbsp 0 -> ValueError")
check(leve(di.teaspoon_us_vers_ml, -1), "tsp négatif -> ValueError")
# adapte_recette : abstentions déléguées
check(leve(di.adapte_recette, rec, 0, 6), "portions_origine 0 -> ValueError")
check(leve(di.adapte_recette, rec, 4, -2), "portions_cible négatif -> ValueError")
check(leve(di.adapte_recette, {"farine": -1.0}, 4, 6), "quantité négative -> ValueError")
check(leve(di.adapte_recette, "farine", 4, 6), "ingredients non structuré -> ValueError")
check(leve(di.adapte_recette, {}, 4, 6), "recette vide -> ValueError")
check(leve(di.adapte_recette, [("farine", 1, 2)], 4, 6), "couple mal formé -> ValueError")
# NaN / ±inf : garde de finitude LOCALE (recettes._verifie_reel ne teste pas isfinite) — défaut audit corrigé
check(leve(di.adapte_recette, {"farine": float("nan")}, 4, 6), "quantité NaN (dict) -> ValueError")
check(leve(di.adapte_recette, {"farine": float("inf")}, 4, 6), "quantité +inf (dict) -> ValueError")
check(leve(di.adapte_recette, {"farine": float("-inf")}, 4, 6), "quantité -inf (dict) -> ValueError")
check(leve(di.adapte_recette, [("farine", float("nan"))], 4, 6), "quantité NaN (liste) -> ValueError")
check(leve(di.adapte_recette, [("farine", float("inf"))], 4, 6), "quantité +inf (liste) -> ValueError")
check(leve(di.adapte_recette, {"farine": 200.0}, float("nan"), 6), "portions_origine NaN -> ValueError")
check(leve(di.adapte_recette, {"farine": 200.0}, float("inf"), 6), "portions_origine +inf -> ValueError")
check(leve(di.adapte_recette, {"farine": 200.0}, 4, float("nan")), "portions_cible NaN -> ValueError")
check(leve(di.adapte_recette, {"farine": 200.0}, 4, float("inf")), "portions_cible +inf -> ValueError")

# ── DÉTERMINISME ─────────────────────────────────────────────────────────────────────────────────────────────────
check(di.masse_volumique("miel") == di.masse_volumique("miel"), "déterminisme masse_volumique")
check(di.volume_vers_masse(123.4, "farine") == di.volume_vers_masse(123.4, "farine"), "déterminisme volume_vers_masse")
check(di.cup_vers_ml(3, "legale") == di.cup_vers_ml(3, "legale"), "déterminisme cup_vers_ml")
check(di.adapte_recette(rec, 4, 6) == di.adapte_recette(rec, 4, 6), "déterminisme adapte_recette")

print(f"\n=== valide_densites_ingredients : {ok}/{ok+ko} ===")
import sys
sys.exit(0 if ko == 0 else 1)
