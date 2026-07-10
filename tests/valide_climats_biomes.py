"""
Gate adverse de `climats_biomes` (classification de Köppen-Geiger).

ANCRES NON CIRCULAIRES : classifications de villes UNIVERSELLEMENT publiées (Wikipedia / atlas
climatiques / Peel-Finlayson-McMahon 2007). Les 12 normales mensuelles (T en °C, P en mm) sont
écrites EN DUR ci-dessous ; on exige que `koppen(...)` retrouve le code publié. Aucune valeur
attendue n'est recalculée avec le code testé.

  Paris (nord)            -> Cfb  (océanique tempéré)
  Singapour (nord)        -> Af   (équatorial)
  Le Caire (nord)         -> BWh  (désert chaud)
  Moscou (nord)           -> Dfb  (continental humide)
  Reykjavik (nord)        -> Cfc ou ET selon la série (SENSIBILITÉ : mois le plus chaud ~11 °C,
                             juste au-dessus du seuil E de 10 °C -> une série légèrement plus froide
                             bascule en ET ; nos normales donnent Cfc ; on accepte les DEUX)
  Utqiaġvik/Barrow (nord) -> ET   (toundra)
  Perth (SUD)             -> Csa  (méditerranéen ; test d'hémisphère : l'été austral déc.-fév. est sec —
                             une mauvaise gestion de l'hémisphère donnerait Cwa au lieu de Csa)
"""
from __future__ import annotations

import math

import climats_biomes as cb

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


# ── ANCRES : normales climatiques (T °C, P mm), Jan..Déc ──────────────────────────────────────────────────────────
# Paris-Montsouris (normales ~1991-2020). Attendu : Cfb.
PARIS_T = [5.4, 6.0, 9.2, 11.8, 15.4, 18.8, 20.9, 20.8, 17.2, 13.3, 8.6, 5.8]
PARIS_P = [47.6, 41.9, 45.9, 47.0, 64.7, 56.3, 55.4, 55.5, 46.6, 60.0, 55.3, 59.0]

# Singapour (Changi). Attendu : Af (mois le plus froid ≥ 18, pluie mini ≥ 60).
SING_T = [26.6, 27.2, 27.6, 28.0, 28.4, 28.3, 27.9, 27.8, 27.7, 27.6, 27.0, 26.6]
SING_P = [234.6, 112.8, 170.3, 154.8, 171.0, 132.0, 158.6, 176.0, 169.0, 194.0, 258.0, 289.0]

# Le Caire. Attendu : BWh (aride, T_moy ≈ 22 °C).
CAIRE_T = [14.0, 15.0, 17.8, 21.8, 25.4, 27.9, 28.9, 28.7, 26.7, 23.6, 19.5, 15.3]
CAIRE_P = [5.0, 3.8, 3.8, 1.1, 0.5, 0.1, 0.0, 0.0, 0.0, 0.7, 3.8, 5.9]

# Moscou. Attendu : Dfb (mois le plus froid ≤ −3, pas de saison sèche, été tempéré).
MOSCOU_T = [-6.5, -6.7, -1.0, 6.7, 13.2, 16.9, 18.7, 16.8, 11.1, 5.1, -1.2, -4.4]
MOSCOU_P = [42.0, 36.0, 34.0, 43.0, 51.0, 75.0, 94.0, 77.0, 65.0, 59.0, 53.0, 51.0]

# Reykjavik. Attendu : Cfc (mois le plus chaud ~11 °C) OU ET (série plus froide). On accepte les deux.
REYK_T = [0.1, 0.6, 1.3, 3.5, 6.9, 9.5, 11.1, 10.8, 8.2, 4.7, 2.1, 0.3]
REYK_P = [76.0, 72.0, 82.0, 58.0, 44.0, 50.0, 52.0, 62.0, 67.0, 86.0, 73.0, 79.0]

# Utqiaġvik / Barrow (Alaska). Attendu : ET (mois le plus chaud ~4 °C, 0 ≤ T_max < 10).
BARROW_T = [-25.0, -26.0, -24.0, -16.0, -5.0, 1.0, 4.0, 4.0, -1.0, -9.0, -18.0, -23.0]
BARROW_P = [4.0, 5.0, 4.0, 4.0, 4.0, 9.0, 25.0, 25.0, 16.0, 14.0, 7.0, 5.0]

# Perth (Australie, hémisphère SUD). Attendu : Csa (été austral sec, mois le plus chaud ≥ 22 °C).
PERTH_T = [24.5, 24.8, 23.1, 19.8, 16.2, 13.8, 12.9, 13.3, 14.8, 16.5, 19.4, 22.0]
PERTH_P = [15.0, 12.0, 19.0, 42.0, 96.0, 145.0, 143.0, 121.0, 76.0, 44.0, 25.0, 13.0]

# ── vérité des codes publiés ──────────────────────────────────────────────────────────────────────────────────────
check(cb.koppen(PARIS_T, PARIS_P, "nord") == "Cfb", "Paris -> Cfb")
check(cb.koppen(SING_T, SING_P, "nord") == "Af", "Singapour -> Af")
check(cb.koppen(CAIRE_T, CAIRE_P, "nord") == "BWh", "Le Caire -> BWh")
check(cb.koppen(MOSCOU_T, MOSCOU_P, "nord") == "Dfb", "Moscou -> Dfb")
check(cb.koppen(REYK_T, REYK_P, "nord") in ("Cfc", "ET"), "Reykjavik -> Cfc ou ET")
check(cb.koppen(REYK_T, REYK_P, "nord") == "Cfc", "Reykjavik (nos normales) -> Cfc précisément")
check(cb.koppen(BARROW_T, BARROW_P, "nord") == "ET", "Barrow -> ET")
check(cb.koppen(PERTH_T, PERTH_P, "sud") == "Csa", "Perth (sud) -> Csa")

# Test d'hémisphère : Perth mal étiqueté 'nord' NE doit PAS rester Csa (l'été/hiver s'inversent).
check(cb.koppen(PERTH_T, PERTH_P, "nord") != "Csa", "Perth étiqueté nord -> code différent de Csa")
check(cb.koppen(PERTH_T, PERTH_P, "nord") == "Cwa", "Perth mal étiqueté nord -> Cwa (hiver 'sec' NH)")

# ── décomposition : première lettre / groupe ──────────────────────────────────────────────────────────────────────
check(cb.koppen(SING_T, SING_P, "nord")[0] == "A", "Singapour groupe A")
check(cb.koppen(CAIRE_T, CAIRE_P, "nord")[0] == "B", "Le Caire groupe B")
check(cb.koppen(PARIS_T, PARIS_P, "nord")[0] == "C", "Paris groupe C")
check(cb.koppen(MOSCOU_T, MOSCOU_P, "nord")[0] == "D", "Moscou groupe D")
check(cb.koppen(BARROW_T, BARROW_P, "nord")[0] == "E", "Barrow groupe E")

# ── EF (calotte) : un lieu dont le mois le plus chaud reste sous 0 °C ─────────────────────────────────────────────
# Vostok-like : toutes T < 0. Attendu EF (calcul à la main : T_max < 0 -> EF).
EF_T = [-32.0, -44.0, -58.0, -65.0, -66.0, -65.0, -67.0, -68.0, -66.0, -57.0, -43.0, -33.0]
EF_P = [1.0, 1.0, 1.0, 1.0, 1.0, 1.0, 1.0, 1.0, 1.0, 1.0, 1.0, 1.0]
check(cb.koppen(EF_T, EF_P, "sud") == "EF", "calotte glaciaire -> EF")

# ── seuil de sécheresse : ancre calculée À LA MAIN ────────────────────────────────────────────────────────────────
# Le Caire : T_moy = 264.6/12 = 22.05 °C ; ≥70 % des pluies en hiver -> add = 0 ; seuil = 20·22.05 = 441 mm.
s_caire = cb.seuil_secheresse(CAIRE_T, CAIRE_P, "nord")
check(abs(s_caire - 441.0) < 1e-6, f"seuil Le Caire = 441 (obtenu {s_caire})")
# P_annuelle du Caire (somme écrite à la main) = 24.7 mm < 441 -> aride ; < 441/2=220.5 -> désert (BW).
check(abs(sum(CAIRE_P) - 24.7) < 1e-6, "P_annuelle Le Caire = 24.7 mm")

# Perth : T_moy = 221.1/12 = 18.425 ; ≥70 % en hiver austral -> add = 0 ; seuil = 20·18.425 = 368.5 mm.
s_perth = cb.seuil_secheresse(PERTH_T, PERTH_P, "sud")
check(abs(s_perth - 368.5) < 1e-6, f"seuil Perth = 368.5 (obtenu {s_perth})")
# P_annuelle Perth = 751 mm > 368.5 -> NON aride (donc groupe C, pas B).
check(abs(sum(PERTH_P) - 751.0) < 1e-6, "P_annuelle Perth = 751 mm")

# ── libellés & biomes (ancres imposées) ──────────────────────────────────────────────────────────────────────────
check(cb.biome_associe("Af") == "forêt tropicale humide", "biome Af")
check(cb.biome_associe("ET") == "toundra", "biome ET")
check(cb.biome_associe("BWh") == "désert chaud", "biome BWh")
check(cb.biome_associe("Dfc") == "taïga (forêt boréale)", "biome Dfc = taïga")
check(cb.biome_associe("Aw") == "savane", "biome Aw = savane")
check(cb.biome_associe("cfb") == "forêt tempérée", "biome normalisé 'cfb' -> forêt tempérée")
check("océanique" in cb.libelle("Cfb"), "libellé Cfb mentionne océanique")
check("désert" in cb.libelle("BWh"), "libellé BWh mentionne désert")
check("toundra" in cb.libelle("ET"), "libellé ET mentionne toundra")
check(len(cb.codes_connus()) >= 25, "au moins 25 codes catalogués")

# ── DÉTERMINISME ─────────────────────────────────────────────────────────────────────────────────────────────────
check(cb.koppen(PARIS_T, PARIS_P, "nord") == cb.koppen(PARIS_T, PARIS_P, "nord"), "koppen déterministe")
check(cb.seuil_secheresse(CAIRE_T, CAIRE_P, "nord") == cb.seuil_secheresse(CAIRE_T, CAIRE_P, "nord"),
      "seuil déterministe")
check(cb.biome_associe("Af") == cb.biome_associe("Af"), "biome déterministe")

# ── SOUNDNESS : abstentions (faux positif interdit) ──────────────────────────────────────────────────────────────
# longueur ≠ 12
check(leve(cb.koppen, PARIS_T[:11], PARIS_P, "nord"), "T longueur 11 -> ValueError")
check(leve(cb.koppen, PARIS_T, PARIS_P + [0.0], "nord"), "P longueur 13 -> ValueError")
check(leve(cb.koppen, [], [], "nord"), "listes vides -> ValueError")
# hémisphère invalide
check(leve(cb.koppen, PARIS_T, PARIS_P, "est"), "hémisphère 'est' -> ValueError")
check(leve(cb.koppen, PARIS_T, PARIS_P, ""), "hémisphère vide -> ValueError")
check(leve(cb.koppen, PARIS_T, PARIS_P, 1), "hémisphère non-str -> ValueError")
# valeurs non numériques
check(leve(cb.koppen, [float("nan")] + PARIS_T[1:], PARIS_P, "nord"), "T NaN -> ValueError")
check(leve(cb.koppen, PARIS_T, [float("inf")] + PARIS_P[1:], "nord"), "P inf -> ValueError")
check(leve(cb.koppen, [True] + PARIS_T[1:], PARIS_P, "nord"), "T bool -> ValueError")
check(leve(cb.koppen, PARIS_T, ["x"] + PARIS_P[1:], "nord"), "P str -> ValueError")
check(leve(cb.koppen, "abc", PARIS_P, "nord"), "T str global -> ValueError")
check(leve(cb.koppen, None, PARIS_P, "nord"), "T None -> ValueError")
# précipitation négative
check(leve(cb.koppen, PARIS_T, [-1.0] + PARIS_P[1:], "nord"), "P négative -> ValueError")
# seuil : mêmes gardes
check(leve(cb.seuil_secheresse, PARIS_T[:5], PARIS_P, "nord"), "seuil T courte -> ValueError")
check(leve(cb.seuil_secheresse, PARIS_T, PARIS_P, "ouest"), "seuil hémisphère invalide -> ValueError")
# libelle / biome : code inconnu ou mal typé
check(leve(cb.libelle, "Zz"), "libelle code inconnu -> ValueError")
check(leve(cb.libelle, "Xyz"), "libelle code inconnu 3 -> ValueError")
check(leve(cb.libelle, 42), "libelle non-str -> ValueError")
check(leve(cb.biome_associe, "Qq"), "biome code inconnu -> ValueError")
check(leve(cb.biome_associe, None), "biome None -> ValueError")

# ── cohérence croisée : chaque code produit par les ancres a un biome et un libellé ──────────────────────────────
for nom, T, P, hemi in [
    ("Paris", PARIS_T, PARIS_P, "nord"),
    ("Singapour", SING_T, SING_P, "nord"),
    ("Caire", CAIRE_T, CAIRE_P, "nord"),
    ("Moscou", MOSCOU_T, MOSCOU_P, "nord"),
    ("Barrow", BARROW_T, BARROW_P, "nord"),
    ("Perth", PERTH_T, PERTH_P, "sud"),
]:
    code = cb.koppen(T, P, hemi)
    check(isinstance(cb.libelle(code), str) and len(cb.libelle(code)) > 0, f"{nom}: libellé de {code}")
    check(isinstance(cb.biome_associe(code), str) and len(cb.biome_associe(code)) > 0, f"{nom}: biome de {code}")

print(f"\n=== valide_climats_biomes : {ok}/{ok+ko} ===")
import sys; sys.exit(0 if ko == 0 else 1)
