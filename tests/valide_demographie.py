"""
VALIDE demographie.py — held-out ADVERSE.

Ancres CONNUES (définitions de manuel + arithmétique vérifiée À LA MAIN, non circulaires) :
  • taux_croissance_naturel : (20−8)/1000 = 0.012 ; (30−10)/1000 = 0.020 ;
                              (10−15)/1000 = −0.005 (décroissance, réel) ; (12−12)/1000 = 0.0
  • densite_population      : 1 000 000/500 = 2000.0 ; 8 000 000/100 = 80000.0 ; 0/100 = 0.0 ;
                              France 67 000 000/551 695 ≈ 121.44 hab/km² (ancre externe)
  • temps_doublement        : 70/2 = 35 ans ; 70/7 = 10 ; 70/1 = 70 ; 70/3.5 = 20 ; 70/10 = 7
  • taux_dependance         : (30+20)/50·100 = 100 ; (40+15)/100·100 = 55 ; (0+0)/100·100 = 0 ;
                              (20+30)/200·100 = 25
  • indice_fecondite        : 7 classes à 60‰, l=5 -> 5·420/1000 = 2.1 (seuil de remplacement) ;
                              [10,50,110,100,50,12,1] l=5 -> 5·333/1000 = 1.665 ;
                              30 classes annuelles à 100‰, l=1 -> 1·3000/1000 = 3.0 ; [0] -> 0.0
SOUNDNESS : surface<=0, actifs<=0, taux<=0 (doublement), largeur<=0, entrée<0, séquence vide /
            non itérable, valeur non finie / non numérique / booléenne -> ValueError (jamais un faux).
DÉTERMINISME : mêmes entrées -> mêmes sorties.
Aucun de ces cas (et aucune valeur-pays codée en dur) n'est dans demographie.py.
"""

import demographie as M

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
    return abs(a - b) <= tol


def _leve_v(fn, *a, **k):
    try:
        fn(*a, **k)
        return False
    except ValueError:
        return True
    except Exception:
        return False


# ── 1) taux_croissance_naturel — ancres arithmétiques exactes ──
check(approx(M.taux_croissance_naturel(20, 8), 0.012), "(20−8)/1000 = 0.012")
check(approx(M.taux_croissance_naturel(30, 10), 0.020), "(30−10)/1000 = 0.020")
check(approx(M.taux_croissance_naturel(10, 15), -0.005), "(10−15)/1000 = −0.005 (décroissance réelle)")
check(approx(M.taux_croissance_naturel(12, 12), 0.0), "(12−12)/1000 = 0.0")

# ── 2) densite_population — ancres exactes + ancre externe (France) ──
check(approx(M.densite_population(1_000_000, 500), 2000.0), "1e6/500 = 2000 hab/km²")
check(approx(M.densite_population(8_000_000, 100), 80000.0), "8e6/100 = 80000 hab/km²")
check(approx(M.densite_population(0, 100), 0.0), "0/100 = 0.0 (région vide)")
check(approx(M.densite_population(67_000_000, 551_695), 121.44, tol=1e-2),
      "France ≈ 67 M / 551 695 km² ≈ 121.44 hab/km²")

# ── 3) temps_doublement — règle des 70 ──
check(approx(M.temps_doublement(2), 35.0), "70/2 = 35 ans (cas de référence 2 %)")
check(approx(M.temps_doublement(7), 10.0), "70/7 = 10 ans")
check(approx(M.temps_doublement(1), 70.0), "70/1 = 70 ans")
check(approx(M.temps_doublement(3.5), 20.0), "70/3.5 = 20 ans")
check(approx(M.temps_doublement(10), 7.0), "70/10 = 7 ans")

# ── 4) taux_dependance — ratio de dépendance (%) ──
check(approx(M.taux_dependance(30, 20, 50), 100.0), "(30+20)/50·100 = 100 %")
check(approx(M.taux_dependance(40, 15, 100), 55.0), "(40+15)/100·100 = 55 %")
check(approx(M.taux_dependance(0, 0, 100), 0.0), "(0+0)/100·100 = 0 %")
check(approx(M.taux_dependance(20, 30, 200), 25.0), "(20+30)/200·100 = 25 %")

# ── 5) indice_fecondite — ISF / TFR (somme exacte) ──
check(approx(M.indice_fecondite([60, 60, 60, 60, 60, 60, 60], 5), 2.1),
      "7 classes à 60‰, l=5 -> 5·420/1000 = 2.1 (seuil de remplacement)")
check(approx(M.indice_fecondite([10, 50, 110, 100, 50, 12, 1], 5), 1.665),
      "profil réaliste somme 333‰, l=5 -> 1.665")
check(approx(M.indice_fecondite([100] * 30, 1), 3.0),
      "30 classes annuelles à 100‰, l=1 -> 3.0")
check(approx(M.indice_fecondite([0], 5), 0.0), "[0] -> 0.0 (aucune fécondité)")
check(approx(M.indice_fecondite([60, 60, 60, 60, 60, 60, 60]), 2.1),
      "largeur_classe par défaut = 5 -> 2.1")

# ── 6) SOUNDNESS densite — dénominateur / entrée invalide ──
check(_leve_v(M.densite_population, 1000, 0), "surface = 0 -> ValueError")
check(_leve_v(M.densite_population, 1000, -10), "surface < 0 -> ValueError")
check(_leve_v(M.densite_population, -1, 100), "population < 0 -> ValueError")
check(_leve_v(M.densite_population, float("nan"), 100), "population NaN -> ValueError")
check(_leve_v(M.densite_population, 1000, float("inf")), "surface inf -> ValueError")
check(_leve_v(M.densite_population, 1000, "x"), "surface non numérique -> ValueError")

# ── 7) SOUNDNESS temps_doublement — taux <= 0 ──
check(_leve_v(M.temps_doublement, 0), "taux = 0 (pas de doublement) -> ValueError")
check(_leve_v(M.temps_doublement, -2), "taux < 0 (décroissance) -> ValueError")
check(_leve_v(M.temps_doublement, float("nan")), "taux NaN -> ValueError")
check(_leve_v(M.temps_doublement, float("inf")), "taux inf -> ValueError")
check(_leve_v(M.temps_doublement, "deux"), "taux non numérique -> ValueError")

# ── 8) SOUNDNESS taux_dependance — actifs <= 0 / entrée < 0 ──
check(_leve_v(M.taux_dependance, 30, 20, 0), "actifs = 0 -> ValueError")
check(_leve_v(M.taux_dependance, 30, 20, -1), "actifs < 0 -> ValueError")
check(_leve_v(M.taux_dependance, -1, 20, 50), "jeunes < 0 -> ValueError")
check(_leve_v(M.taux_dependance, 30, -1, 50), "âgés < 0 -> ValueError")
check(_leve_v(M.taux_dependance, float("nan"), 20, 50), "jeunes NaN -> ValueError")

# ── 9) SOUNDNESS taux_croissance_naturel — entrée < 0 / non finie ──
check(_leve_v(M.taux_croissance_naturel, -1, 8), "natalité < 0 -> ValueError")
check(_leve_v(M.taux_croissance_naturel, 20, -1), "mortalité < 0 -> ValueError")
check(_leve_v(M.taux_croissance_naturel, float("inf"), 8), "natalité inf -> ValueError")
check(_leve_v(M.taux_croissance_naturel, "vingt", 8), "natalité non numérique -> ValueError")

# ── 10) SOUNDNESS indice_fecondite — séquence / largeur / valeur invalide ──
check(_leve_v(M.indice_fecondite, []), "séquence vide -> ValueError")
check(_leve_v(M.indice_fecondite, [60, -1, 60]), "taux négatif -> ValueError")
check(_leve_v(M.indice_fecondite, [60, 60], 0), "largeur_classe = 0 -> ValueError")
check(_leve_v(M.indice_fecondite, [60, 60], -5), "largeur_classe < 0 -> ValueError")
check(_leve_v(M.indice_fecondite, [60, float("nan")], 5), "taux NaN -> ValueError")
check(_leve_v(M.indice_fecondite, 5, 5), "taux_par_age non itérable -> ValueError")
check(_leve_v(M.indice_fecondite, "60", 5), "taux_par_age = chaîne -> ValueError")

# ── 11) SOUNDNESS booléen rejeté (non quantité démographique) ──
check(_leve_v(M.densite_population, True, 100), "population booléenne -> ValueError")
check(_leve_v(M.temps_doublement, True), "taux booléen -> ValueError")

# ── 12) DÉTERMINISME — mêmes entrées -> mêmes sorties ──
check(M.taux_croissance_naturel(20, 8) == M.taux_croissance_naturel(20, 8), "croissance naturelle déterministe")
check(M.densite_population(1_000_000, 500) == M.densite_population(1_000_000, 500), "densité déterministe")
check(M.temps_doublement(2) == M.temps_doublement(2), "temps_doublement déterministe")
check(M.taux_dependance(30, 20, 50) == M.taux_dependance(30, 20, 50), "taux_dependance déterministe")
check(M.indice_fecondite([60] * 7, 5) == M.indice_fecondite([60] * 7, 5), "indice_fecondite déterministe")

print(f"\n=== valide_demographie : {ok}/{ok+ko} ===")
import sys
sys.exit(0 if ko == 0 else 1)
