"""
VALIDE ceramiques.py — held-out ADVERSE (FAUX=0).

ANCRES EXTERNES CONNUES (vérifiées par définition / manuel, non recalculées par la même expression du module) :
  • Retrait de cuisson = (d_crue − d_cuite)/d_crue : 100 mm -> 88 mm = 12/100 = 0.12 (cas de l'énoncé) ;
    200 -> 150 = 50/200 = 0.25 ; pas de retrait (100 -> 100) = 0.0.
  • Porosité = vides/total : 2/10 = 0.2 ; 1/4 = 0.25 ; massif (0/5) = 0.0 ; tout vide (5/5) = 1.0.
  • Classification conventionnelle : porcelaine ~1300 °C, faïence ~1000 °C, grès ~1250 °C, terre cuite ~950 °C ;
    hiérarchie établie terre cuite < faïence < grès < porcelaine ; porcelaine cuit PLUS CHAUD que faïence.
  • Faits matériaux : compression élevée, fragilité (faible ténacité) ; porcelaine vitrifiée et translucide,
    terre cuite poreuse et opaque.
SOUNDNESS : dimensions/volumes ≤ 0, retrait négatif (d_cuite>d_crue), porosité > 1 (vides>total), type non
numérique/booléen/non fini, classe inconnue -> ValueError (jamais un faux).
DÉTERMINISME : double appel identique ; les tables de faits sont protégées (copies).
"""
import ceramiques as C

ok = 0
ko = 0


def check(cond, label):
    global ok, ko
    if cond:
        ok += 1
    else:
        ko += 1
        print(f"  FAIL: {label}")


def approx(x, attendu, tol=1e-9):
    return x is not None and abs(x - attendu) <= tol


def leve(fn, *args):
    try:
        fn(*args)
        return False
    except ValueError:
        return True
    except Exception:
        return False


# ── 1) RETRAIT DE CUISSON : (d_crue − d_cuite)/d_crue (ancres connues) ──
check(approx(C.retrait_cuisson(100, 88), 0.12), "retrait 100->88 = 12 % (énoncé)")
check(approx(C.retrait_cuisson(200, 150), 0.25), "retrait 200->150 = 0.25")
check(approx(C.retrait_cuisson(100, 100), 0.0), "pas de retrait 100->100 = 0")
check(approx(C.retrait_cuisson(50, 44), 0.12), "retrait 50->44 = 0.12 (échelle invariante)")
check(approx(C.retrait_cuisson(10, 9), 0.1), "retrait 10->9 = 0.1")
check(0.0 <= C.retrait_cuisson(120, 100) < 1.0, "retrait ∈ [0,1[")

# ── 2) POROSITÉ : vides/total (ancres connues) ──
check(approx(C.porosite(2, 10), 0.2), "porosité 2/10 = 0.2")
check(approx(C.porosite(1, 4), 0.25), "porosité 1/4 = 0.25")
check(approx(C.porosite(0, 5), 0.0), "porosité massive 0/5 = 0")
check(approx(C.porosite(5, 5), 1.0), "porosité totale 5/5 = 1")
check(approx(C.porosite(3.5, 14), 0.25), "porosité 3.5/14 = 0.25")
check(0.0 <= C.porosite(7, 20) <= 1.0, "porosité ∈ [0,1]")

# ── 3) CLASSIFICATION : température de cuisson typique (convention établie) ──
check(C.classe_ceramique("porcelaine") == 1300.0, "porcelaine ~1300 °C")
check(C.classe_ceramique("faience") == 1000.0, "faïence ~1000 °C")
check(C.classe_ceramique("gres") == 1250.0, "grès ~1250 °C")
check(C.classe_ceramique("terre_cuite") == 950.0, "terre cuite ~950 °C")
# robustesse de normalisation (accents, casse, espaces/tirets) — même fait
check(C.classe_ceramique("Porcelaine") == 1300.0, "casse insensible")
check(C.classe_ceramique("faïence") == 1000.0, "accent ï toléré")
check(C.classe_ceramique("Grès") == 1250.0, "accent è + casse tolérés")
check(C.classe_ceramique("terre cuite") == 950.0, "espace toléré")
check(C.classe_ceramique("terre-cuite") == 950.0, "tiret toléré")

# ── 4) HIÉRARCHIE ÉTABLIE (porcelaine cuit plus chaud que faïence, etc.) ──
check(C.classe_ceramique("porcelaine") > C.classe_ceramique("faience"), "porcelaine > faïence (énoncé)")
check(C.classe_ceramique("gres") > C.classe_ceramique("faience"), "grès > faïence")
check(C.classe_ceramique("porcelaine") > C.classe_ceramique("gres"), "porcelaine > grès")
check(C.classe_ceramique("faience") > C.classe_ceramique("terre_cuite"), "faïence > terre cuite")
check(C.classes_connues() == ("terre_cuite", "faience", "gres", "porcelaine"),
      "ordre croissant de cuisson terre cuite < faïence < grès < porcelaine")

# ── 5) FAITS MATÉRIAUX ÉTABLIS (compression élevée, fragilité, pâte) ──
pm = C.proprietes_mecaniques()
check(pm["resistance_compression"] == "elevee", "résistance compression élevée")
check(pm["tenacite"] == "faible" and pm["fragile"] is True, "ténacité faible -> fragile")
check(pm["ductile"] is False, "non ductile (rupture cassante)")
check(C.est_fragile() is True, "céramique fragile")
pp = C.proprietes_ceramique("porcelaine")
check(pp["pate"] == "vitrifiee" and pp["translucide"] is True, "porcelaine vitrifiée et translucide")
pt = C.proprietes_ceramique("terre_cuite")
check(pt["pate"] == "poreuse" and pt["translucide"] is False, "terre cuite poreuse et opaque")
check(C.proprietes_ceramique("gres")["pate"] == "vitrifiee", "grès vitrifié")
check(C.proprietes_ceramique("faience")["pate"] == "poreuse", "faïence poreuse")

# ── 6) SOUNDNESS — domaine invalide -> ValueError ──
check(leve(C.retrait_cuisson, 0, 0), "dim_crue = 0 -> ValueError")
check(leve(C.retrait_cuisson, -10, 5), "dim_crue < 0 -> ValueError")
check(leve(C.retrait_cuisson, 100, 0), "dim_cuite = 0 -> ValueError")
check(leve(C.retrait_cuisson, 100, -5), "dim_cuite < 0 -> ValueError")
check(leve(C.retrait_cuisson, 88, 100), "d_cuite > d_crue (retrait négatif) -> ValueError")
check(leve(C.porosite, 1, 0), "volume_total = 0 -> ValueError")
check(leve(C.porosite, 1, -4), "volume_total < 0 -> ValueError")
check(leve(C.porosite, -1, 10), "volume_vides < 0 -> ValueError")
check(leve(C.porosite, 11, 10), "volume_vides > volume_total (porosité > 1) -> ValueError")
check(leve(C.classe_ceramique, "inconnu"), "classe inconnue -> ValueError")
check(leve(C.classe_ceramique, "ciment"), "ciment (hors référentiel) -> ValueError")
check(leve(C.classe_ceramique, ""), "nom vide -> ValueError")
check(leve(C.proprietes_ceramique, "verre"), "verre (hors référentiel) -> ValueError")

# ── 7) SOUNDNESS — type non numérique / booléen / non fini -> ValueError ──
check(leve(C.retrait_cuisson, "100", 88), "dim_crue str -> ValueError")
check(leve(C.retrait_cuisson, None, 88), "dim_crue None -> ValueError")
check(leve(C.retrait_cuisson, True, 88), "dim_crue booléen -> ValueError")
check(leve(C.retrait_cuisson, float("nan"), 88), "dim_crue NaN -> ValueError")
check(leve(C.retrait_cuisson, float("inf"), 88), "dim_crue inf -> ValueError")
check(leve(C.porosite, 2, "10"), "volume_total str -> ValueError")
check(leve(C.porosite, True, 10), "volume_vides booléen -> ValueError")
check(leve(C.classe_ceramique, 1300), "nom numérique -> ValueError")
check(leve(C.classe_ceramique, None), "nom None -> ValueError")

# ── 8) DÉTERMINISME + immutabilité des tables de faits ──
check(C.retrait_cuisson(100, 88) == C.retrait_cuisson(100, 88), "retrait déterministe")
check(C.porosite(2, 10) == C.porosite(2, 10), "porosité déterministe")
check(C.classe_ceramique("gres") == C.classe_ceramique("gres"), "classe déterministe")
m = C.proprietes_mecaniques()
m["fragile"] = "ALTÉRÉ"
check(C.proprietes_mecaniques()["fragile"] is True, "proprietes_mecaniques renvoie une copie (table protégée)")
p = C.proprietes_ceramique("porcelaine")
p["temperature_cuisson_C"] = -1
check(C.proprietes_ceramique("porcelaine")["temperature_cuisson_C"] == 1300.0,
      "proprietes_ceramique renvoie une copie (table protégée)")

print(f'\n=== valide_ceramiques : {ok}/{ok+ko} ===')
import sys
sys.exit(0 if ko == 0 else 1)
