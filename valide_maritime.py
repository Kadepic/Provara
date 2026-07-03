"""VALIDE maritime.py — ADVERSE, FAUX=0. Vitesse de coque (hull speed, 1.34·√ft = 2.427·√m), poussée d'Archimède
(ρVg) + flottabilité (masse < ρV), nombre de Froude (v/√(gL)) + SOUNDNESS (longueur/volume/ρ/g ≤ 0, vitesse < 0,
non-numérique -> ValueError) + déterminisme. Ancres CONNUES non circulaires (recalculées à la main)."""
import math

import maritime as M

ok = 0
ko = 0


def check(c, l):
    global ok, ko
    if c:
        ok += 1
    else:
        ko += 1
        print(f"  FAIL: {l}")


def proche(a, b, tol=1e-3):
    return abs(a - b) <= tol


def leve(fn, *a, **k):
    try:
        fn(*a, **k)
        return False
    except ValueError:
        return True
    except Exception:
        return False


# ── VITESSE DE COQUE ──────────────────────────────────────────────────────────────────────────────────────────
# Ancre indépendante : LWL=9 m -> 9/0.3048 = 29.5276 ft ; √ = 5.43393 ; ×1.34 = 7.28147 noeuds (≈7.3).
check(proche(M.vitesse_coque(9), 7.28146, 1e-3), "hull speed LWL=9 m ≈ 7.28 noeuds")
check(proche(M.vitesse_coque(9), 7.3, 0.05), "hull speed LWL=9 m ≈ 7.3 noeuds (cas spec)")
# LWL=25 m -> 2.427154·5 = 12.1358 noeuds (= 1.34·√(25/0.3048) = 1.34·√82.0210 = 1.34·9.05655)
check(proche(M.vitesse_coque(25), 12.1358, 1e-3), "hull speed LWL=25 m = 12.1358 noeuds")
# Cohérence des deux formes (mètres vs pieds) : doivent coïncider
check(proche(M.vitesse_coque(9), M.vitesse_coque_depuis_pieds(9 / 0.3048), 1e-3), "forme mètre == forme pied")
check(proche(M.vitesse_coque_depuis_pieds(100), 13.4, 1e-3), "1.34·√100 = 13.4 noeuds")
# alias max == coque
check(M.vitesse_coque_max(16) == M.vitesse_coque(16), "vitesse_coque_max alias de vitesse_coque")
# loi d'échelle √ : ×4 sur LWL -> ×2 sur vitesse
check(proche(M.vitesse_coque(36), 2 * M.vitesse_coque(9), 1e-3), "LWL ×4 -> vitesse ×2 (loi √)")
# constante dérivée vaut bien ≈ 2.427
check(proche(M.NOEUD_PAR_RAC_METRE, 2.427154, 1e-5), "coefficient mètre dérivé ≈ 2.42715")

# ── POUSSÉE D'ARCHIMÈDE ──────────────────────────────────────────────────────────────────────────────────────
# F = ρVg : eau douce 1000·1·9.80665 = 9806.65 N
check(M.poussee_archimede(1, 1000) == 9806.65, "Archimède V=1 m³ eau douce = 9806.65 N")
# défaut eau de mer 1025·2·9.80665 = 20103.6 N
check(proche(M.poussee_archimede(2), 20103.6, 1e-1), "Archimède V=2 m³ eau de mer (ρ=1025) = 20103.6 N")
# proportionnalité au volume
check(proche(M.poussee_archimede(4, 1000), 4 * M.poussee_archimede(1, 1000), 1e-1), "poussée ∝ volume")

# ── FLOTTABILITÉ : flotte si masse < ρ·V_carène ─────────────────────────────────────────────────────────────
# V=2 m³, eau de mer -> masse_max = 2050 kg
check(M.masse_max_flottante(2, 1025) == 2050.0, "masse max flottante V=2 ρ=1025 = 2050 kg")
check(M.flotte(1000, 2, 1025) is True, "masse 1000 < 2050 -> flotte")
check(M.flotte(3000, 2, 1025) is False, "masse 3000 > 2050 -> coule")
check(M.flotte(2050, 2, 1025) is False, "masse = ρ·V (neutre) -> ne flotte pas (strict)")
check(M.flotte(0, 1) is True, "masse nulle -> flotte")
# cohérence flotte <-> masse_max
check(M.flotte(M.masse_max_flottante(3) - 1, 3) is True, "juste sous la masse max -> flotte")

# ── NOMBRE DE FROUDE ────────────────────────────────────────────────────────────────────────────────────────
# Fr = v/√(gL). Ancres avec g imposé pour racine exacte :
check(M.nombre_froude(2, 1, 4) == 1.0, "Fr v=2 L=1 g=4 -> 2/√4 = 1.0")
check(M.nombre_froude(10, 1, 25) == 2.0, "Fr v=10 L=1 g=25 -> 10/5 = 2.0")
check(M.nombre_froude(0, 9) == 0.0, "Fr v=0 -> 0 (au repos)")
# défaut g=9.81 : v=√9.81 -> Fr=1
check(proche(M.nombre_froude(math.sqrt(9.81), 1), 1.0, 1e-5), "Fr v=√9.81 L=1 g=9.81 -> 1.0")
# valeur réaliste : v=3 m/s, L=9 m, g=9.81 -> 3/√88.29 = 0.319275
check(proche(M.nombre_froude(3, 9, 9.81), 0.319275, 1e-4), "Fr v=3 L=9 = 0.319275")
# régime hull speed : Fr ≈ v/√(gL) ; cohérence interne (monotone en v)
check(M.nombre_froude(4, 9) > M.nombre_froude(2, 9), "Fr croît avec la vitesse")

# ── SOUNDNESS : entrées invalides -> ValueError (jamais un faux) ─────────────────────────────────────────────
check(leve(M.vitesse_coque, 0), "LWL=0 -> ValueError")
check(leve(M.vitesse_coque, -5), "LWL<0 -> ValueError")
check(leve(M.vitesse_coque, "9"), "LWL non numérique -> ValueError")
check(leve(M.vitesse_coque, True), "LWL booléen -> ValueError")
check(leve(M.vitesse_coque_depuis_pieds, 0), "LWL pieds=0 -> ValueError")
check(leve(M.poussee_archimede, 0), "volume=0 -> ValueError")
check(leve(M.poussee_archimede, -1), "volume<0 -> ValueError")
check(leve(M.poussee_archimede, 1, 0), "ρ=0 -> ValueError")
check(leve(M.poussee_archimede, 1, -1000), "ρ<0 -> ValueError")
check(leve(M.masse_max_flottante, 0), "V carène=0 -> ValueError")
check(leve(M.flotte, -1, 2), "masse<0 -> ValueError")
check(leve(M.flotte, 100, 0), "V carène=0 dans flotte -> ValueError")
check(leve(M.flotte, 100, 2, 0), "ρ=0 dans flotte -> ValueError")
check(leve(M.nombre_froude, 2, 0), "longueur=0 -> ValueError")
check(leve(M.nombre_froude, 2, -1), "longueur<0 -> ValueError")
check(leve(M.nombre_froude, -2, 1), "vitesse<0 -> ValueError")
check(leve(M.nombre_froude, 2, 1, 0), "g=0 -> ValueError")
check(leve(M.nombre_froude, 2, 1, -9.81), "g<0 -> ValueError")
check(leve(M.nombre_froude, float("inf"), 1), "vitesse non finie -> ValueError")
check(leve(M.vitesse_coque, float("nan")), "NaN -> ValueError")

# ── DÉTERMINISME ─────────────────────────────────────────────────────────────────────────────────────────────
check(M.vitesse_coque(9) == M.vitesse_coque(9), "déterminisme hull speed")
check(M.poussee_archimede(2) == M.poussee_archimede(2), "déterminisme Archimède")
check(M.nombre_froude(3, 9, 9.81) == M.nombre_froude(3, 9, 9.81), "déterminisme Froude")

print(f"\n=== valide_maritime : {ok}/{ok + ko} ===")
import sys
sys.exit(0 if ko == 0 else 1)
