"""
VALIDE habitabilite.py — held-out ADVERSE. Exactitude des formules ancrée sur des valeurs ASTROPHYSIQUES CONNUES,
NON recalculées par la même expression :
  - température d'équilibre de la Terre ≈ 255 K (albédo 0.3) — valeur de manuel ;
  - température d'équilibre de Mars ≈ 210 K (albédo 0.25, d=1.524 UA) — valeur de manuel ;
  - corps noir gris à 1 UA, albédo nul ≈ 278.6 K (le préfacteur) ;
  - zone habitable du Soleil ≈ (0.95, 1.37) UA (ordre de grandeur usuel) ;
  - loi du flux en 1/d² : flux à 2 UA = ¼ du flux à 1 UA.
+ SOUNDNESS : L ≤ 0, d ≤ 0, albédo ∉ [0,1], type non numérique -> ValueError (jamais un faux) + déterminisme.
"""
import habitabilite as H

ok = 0
ko = 0


def check(cond, label):
    global ok, ko
    if cond:
        ok += 1
    else:
        ko += 1
        print(f"  FAIL: {label}")


def leve(fn, *a, **k):
    try:
        fn(*a, **k)
        return False
    except ValueError:
        return True
    except Exception:
        return False


def proche(x, attendu, rel=1e-4):
    return abs(x - attendu) <= rel * abs(attendu) + 1e-12


# ── 1) ANCRES EXTERNES — température d'équilibre ──
check(abs(H.temperature_equilibre(1.0, 1.0, 0.3) - 255.0) <= 0.02 * 255.0,
      "Terre L=1,d=1,A=0.3 -> T_eq ≈ 255 K (tol 2%)")
check(abs(H.temperature_equilibre(1.0, 1.524, 0.25) - 210.0) <= 0.02 * 210.0,
      "Mars L=1,d=1.524,A=0.25 -> T_eq ≈ 210 K (tol 2%)")
check(proche(H.temperature_equilibre(1.0, 1.0, 0.0), 278.6),
      "corps noir gris A=0 à 1 UA -> T_eq = préfacteur 278.6 K")

# ── 2) ANCRES EXTERNES — valeurs exactes du modèle (vérifiées à la main, pas via H) ──
# A=0.3 -> facteur (0.7)^0.25 = 0.9146904 ; 278.6·0.9146904 = 254.833 K
check(proche(H.temperature_equilibre(1.0, 1.0, 0.3), 254.833),
      "Terre T_eq exact = 278.6·0.7^0.25 = 254.833 K")
# Doubler la distance divise T_eq par √2 (T ∝ d^-0.5) : 254.833 / √2 = 180.193 K
check(proche(H.temperature_equilibre(1.0, 2.0, 0.3), 254.833 / (2 ** 0.5), rel=1e-3),
      "T_eq ∝ d^-0.5 : à 2 UA = T_eq(1 UA)/√2")
# Multiplier L par 16 multiplie T_eq par 2 (T ∝ L^0.25) : 254.833·2 = 509.666 K
check(proche(H.temperature_equilibre(16.0, 1.0, 0.3), 254.833 * 2.0, rel=1e-3),
      "T_eq ∝ L^0.25 : L=16 -> ×2")

# ── 3) ANCRES EXTERNES — zone habitable ──
bi, be = H.zone_habitable(1.0)
check(abs(bi - 0.95) <= 0.02, "Soleil : bord interne ≈ 0.95 UA")
check(abs(be - 1.37) <= 0.02, "Soleil : bord externe ≈ 1.37 UA")
check(bi < be, "bord interne < bord externe")
# valeurs exactes : √(1/1.1)=0.953463 ; √(1/0.53)=1.373606
check(proche(bi, 0.953463) and proche(be, 1.373606), "bornes exactes √(L/1.1), √(L/0.53)")
# L=4 -> bornes ×2 (√ scaling) : 1.906925 / 2.747211
b4i, b4e = H.zone_habitable(4.0)
check(proche(b4i, 0.953463 * 2.0, rel=1e-3) and proche(b4e, 1.373606 * 2.0, rel=1e-3),
      "L=4 -> bornes de zone ×2 (loi en √L)")

# ── 4) ANCRES EXTERNES — flux & appartenance ──
check(proche(H.flux_stellaire_recu(1.0, 1.0), 1.0), "flux Terre = 1 S_⊕")
check(proche(H.flux_stellaire_recu(1.0, 2.0), 0.25), "flux à 2 UA = 1/4 (loi 1/d²)")
check(H.dans_zone_habitable(1.0, 1.0) is True, "Terre (1 UA) DANS la zone habitable du Soleil")
check(H.dans_zone_habitable(1.0, 0.5) is False, "0.5 UA HORS zone (trop chaud)")
check(H.dans_zone_habitable(1.0, 2.0) is False, "2.0 UA HORS zone (trop froid)")

# ── 5) SOUNDNESS — luminosité invalide -> ValueError ──
check(leve(H.temperature_equilibre, 0.0, 1.0), "L=0 -> ValueError")
check(leve(H.temperature_equilibre, -3.0, 1.0), "L<0 -> ValueError")
check(leve(H.zone_habitable, 0.0), "zone L=0 -> ValueError")
check(leve(H.zone_habitable, -1.0), "zone L<0 -> ValueError")
check(leve(H.flux_stellaire_recu, 0.0, 1.0), "flux L=0 -> ValueError")

# ── 6) SOUNDNESS — distance invalide -> ValueError ──
check(leve(H.temperature_equilibre, 1.0, 0.0), "d=0 -> ValueError")
check(leve(H.temperature_equilibre, 1.0, -2.0), "d<0 -> ValueError")
check(leve(H.flux_stellaire_recu, 1.0, 0.0), "flux d=0 -> ValueError")
check(leve(H.dans_zone_habitable, 1.0, 0.0), "dans_zone d=0 -> ValueError")

# ── 7) SOUNDNESS — albédo hors [0,1] -> ValueError ──
check(leve(H.temperature_equilibre, 1.0, 1.0, 1.5), "A>1 -> ValueError")
check(leve(H.temperature_equilibre, 1.0, 1.0, -0.1), "A<0 -> ValueError")
check(not leve(H.temperature_equilibre, 1.0, 1.0, 0.0), "A=0 valide (borne incluse)")
check(not leve(H.temperature_equilibre, 1.0, 1.0, 1.0), "A=1 valide (borne incluse)")

# ── 8) SOUNDNESS — types non numériques (bool/str) -> ValueError ──
check(leve(H.temperature_equilibre, True, 1.0), "bool L -> ValueError")
check(leve(H.temperature_equilibre, 1.0, "deux"), "str d -> ValueError")
check(leve(H.temperature_equilibre, 1.0, 1.0, True), "bool albédo -> ValueError")
check(leve(H.zone_habitable, "x"), "str L -> ValueError")
check(leve(H.temperature_equilibre, float("nan"), 1.0), "NaN L -> ValueError")

# ── 9) DÉTERMINISME ──
check(H.temperature_equilibre(1.0, 1.0, 0.3) == H.temperature_equilibre(1.0, 1.0, 0.3), "déterminisme T_eq")
check(H.zone_habitable(2.5) == H.zone_habitable(2.5), "déterminisme zone")

print(f"\n=== valide_habitabilite : {ok}/{ok+ko} ===")
import sys
sys.exit(0 if ko == 0 else 1)
