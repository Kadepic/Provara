"""
VALIDE impression_3d.py — held-out ADVERSE.

Exactitude des formules FDM, ancrée sur des valeurs CONNUES/recalculées INDÉPENDAMMENT (pas via la même
expression) :
  - 20 mm / couche 0.2 mm = 100 couches ; ratio non entier -> arrondi vers le haut (ceil) ;
  - 1000 mm³ à 5 mm³/s = 200 s ;
  - PLA densité 1.24 -> 1 cm³ (1000 mm³) = 1.24 g ;
  - filament Ø1.75 mm, 1000 mm³ -> section π·0.875² mm² recalculée à la main.
+ SOUNDNESS : hauteur de couche ≤ 0, débit ≤ 0, volume ≤ 0, diamètre ≤ 0, densité ≤ 0, non-numérique, booléen,
  NaN/inf -> ValueError (jamais un faux).
+ DÉTERMINISME.
"""
import math

import impression_3d as M

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


def approx(x, attendu, rel=1e-9):
    return x is not None and abs(x - attendu) <= rel * abs(attendu) + 1e-12


# ── 1) ANCRES — cas de la spec ────────────────────────────────────────────────────────────────────────────────
check(M.nombre_couches(20, 0.2) == 100, "20 mm / 0.2 mm = 100 couches")
check(isinstance(M.nombre_couches(20, 0.2), int), "nombre_couches renvoie un int")
check(approx(M.temps_impression(1000, 5), 200.0), "1000 mm³ à 5 mm³/s = 200 s")
check(approx(M.masse_filament(1000, 1.24), 1.24), "PLA 1.24 -> 1 cm³ = 1.24 g")

# ── 2) ANCRES INDÉPENDANTES — recalculées sans la formule du module ───────────────────────────────────────────
# nombre_couches : ratio non entier -> ceil
check(M.nombre_couches(10, 0.3) == 34, "10 / 0.3 = 33.33… -> 34 couches (ceil)")
check(M.nombre_couches(1, 0.1) == 10, "1 / 0.1 = 10 couches (snap entier malgré bruit flottant)")
check(M.nombre_couches(0.15, 0.2) == 1, "objet plus mince qu'une couche -> 1 couche")
check(M.nombre_couches(50, 0.25) == 200, "50 / 0.25 = 200 couches")
check(M.nombre_couches(20.00000003, 0.2) == 101, "vrai dépassement (20.00000003) -> 101, pas snappé")

# temps_impression
check(approx(M.temps_impression(3600, 1), 3600.0), "3600 mm³ à 1 mm³/s = 3600 s")
check(approx(M.temps_impression(750, 5), 150.0), "750 / 5 = 150 s")

# masse_filament : densités sourcées (PLA 1.24, ABS 1.04, PETG 1.27)
check(approx(M.masse_filament(2000, 1.24), 2.48), "2 cm³ PLA = 2.48 g")
check(approx(M.masse_filament(1000, 1.04), 1.04), "1 cm³ ABS (1.04) = 1.04 g")
check(approx(M.masse_filament(500, 1.27), 0.635), "0.5 cm³ PETG (1.27) = 0.635 g")

# longueur_filament : section recalculée à la main
sect_175 = math.pi * (1.75 / 2.0) ** 2          # ≈ 2.405282 mm²
check(approx(M.longueur_filament(1000, 1.75), 1000.0 / sect_175), "1000 mm³ Ø1.75 = V/section")
check(approx(M.longueur_filament(1000, 1.75), 415.7516880767878, rel=1e-9), "Ø1.75 -> ≈415.75 mm")
sect_285 = math.pi * (2.85 / 2.0) ** 2
check(approx(M.longueur_filament(1000, 2.85), 1000.0 / sect_285), "Ø2.85 filament : V/section")
# Une longueur de section unité : V = section -> longueur 1
check(approx(M.longueur_filament(sect_175, 1.75), 1.0), "V = section -> 1 mm de filament")

# ── 3) SOUNDNESS — abstention (ValueError) sur entrée invalide ────────────────────────────────────────────────
check(leve(M.nombre_couches, 20, 0), "hauteur_couche = 0 -> ValueError")
check(leve(M.nombre_couches, 20, -0.2), "hauteur_couche < 0 -> ValueError")
check(leve(M.nombre_couches, 0, 0.2), "hauteur_objet = 0 -> ValueError")
check(leve(M.nombre_couches, -20, 0.2), "hauteur_objet < 0 -> ValueError")
check(leve(M.temps_impression, 1000, 0), "débit = 0 -> ValueError (pas de division par zéro)")
check(leve(M.temps_impression, 1000, -5), "débit < 0 -> ValueError")
check(leve(M.temps_impression, 0, 5), "volume = 0 -> ValueError")
check(leve(M.temps_impression, -1000, 5), "volume < 0 -> ValueError")
check(leve(M.masse_filament, 1000, 0), "densité = 0 -> ValueError")
check(leve(M.masse_filament, 1000, -1.24), "densité < 0 -> ValueError")
check(leve(M.masse_filament, 0, 1.24), "volume = 0 (masse) -> ValueError")
check(leve(M.longueur_filament, 1000, 0), "diamètre = 0 -> ValueError (pas de division par zéro)")
check(leve(M.longueur_filament, 1000, -1.75), "diamètre < 0 -> ValueError")
check(leve(M.longueur_filament, 0, 1.75), "volume = 0 (longueur) -> ValueError")

# Non numérique / booléen / non fini
check(leve(M.nombre_couches, "20", 0.2), "hauteur non numérique -> ValueError")
check(leve(M.temps_impression, 1000, None), "débit None -> ValueError")
check(leve(M.nombre_couches, True, 0.2), "booléen refusé (hauteur=True) -> ValueError")
check(leve(M.temps_impression, 1000, False), "booléen refusé (débit=False) -> ValueError")
check(leve(M.masse_filament, 1000, True), "booléen refusé (densité=True) -> ValueError")
check(leve(M.temps_impression, float("nan"), 5), "volume NaN -> ValueError")
check(leve(M.temps_impression, 1000, float("inf")), "débit inf -> ValueError")
check(leve(M.longueur_filament, float("inf"), 1.75), "volume inf -> ValueError")

# ── 4) DÉTERMINISME ───────────────────────────────────────────────────────────────────────────────────────────
check(M.nombre_couches(20, 0.2) == M.nombre_couches(20, 0.2), "déterminisme nombre_couches")
check(M.temps_impression(1000, 5) == M.temps_impression(1000, 5), "déterminisme temps_impression")
check(M.masse_filament(1000, 1.24) == M.masse_filament(1000, 1.24), "déterminisme masse_filament")
check(M.longueur_filament(1000, 1.75) == M.longueur_filament(1000, 1.75), "déterminisme longueur_filament")

print(f"\n=== valide_impression_3d : {ok}/{ok+ko} ===")
import sys
sys.exit(0 if ko == 0 else 1)
