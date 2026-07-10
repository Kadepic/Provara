"""
VALIDE atome_hydrogene.py — held-out ADVERSE.

ANCRES EXTERNES NON CIRCULAIRES (valeurs spectroscopiques MESURÉES / CODATA, écrites EN DUR,
PAS recalculées par la formule testée) :
  • E_1 = −13.6057 eV : énergie du fondamental (spectroscopie / CODATA 2018, hcR∞).
  • E_2 = −3.40142 eV : mesuré, ET = E_1/4 (signature de la loi en 1/n²).
  • Balmer Hα (3->2) : λ ≈ 656.3 nm (±0.5 nm) — raie rouge MESURÉE de l'hydrogène (Ångström, 1850s).
  • Balmer Hβ (4->2) : λ ≈ 486.1 nm (±0.5 nm) — raie bleu-vert MESURÉE.
  • Lyman α (2->1)   : λ ≈ 121.6 nm (±0.5 nm) — UV, MESURÉE (Lyman, 1906).
  • Paschen α (4->3) : λ ≈ 1875.1 nm (±1.5 nm) — IR, MESURÉE (Paschen, 1908).
  • Limite de Balmer (∞->2) : λ ≈ 364.6 nm (±0.5 nm) — approchée ici par n_i=10000 (E_10000 ≈ −1.4e-7 eV,
    négligeable devant E_2 : la limite est atteinte bien sous la tolérance).
  • Énergie d'ionisation depuis n=1 = 13.6057 eV (mesurée : potentiel d'ionisation de H ≈ 13.6 V).
  • a0 = 5.29177210903e-11 m ≈ 0.0529 nm (CODATA 2018, rayon de Bohr).
  • E_1 en joules = −2.1798723611e-18 J (énergie de Rydberg CODATA, en J).
  • Calculs à la main (écrits en dur, indépendants du code) :
      ΔE(3->2) = −13.605693122994·5/36 = −1.8896796 eV ; ΔE(1->2) = +13.605693122994·3/4 = +10.2042698 eV ;
      r_2 = 4·a0 = 2.1167088436e-10 m ; r_3 = 9·a0 = 4.7625948981e-10 m.
  • GRANDS n (anti-annulation catastrophique) — ancres calculées par un SECOND chemin, INDÉPENDANT
    du code testé : différence DIRECTE des niveaux exacts en arithmétique rationnelle,
    ΔE = (−E_R/n_f²) − (−E_R/n_i²) avec Fraction("13.605693122994"), valeurs écrites EN DUR :
      ΔE(10⁸ -> 10⁸+1)   = +2.721138584e-23 eV ;
      ΔE(10¹⁶ -> 10¹⁶+1) = +2.721138625e-47 eV (l'évaluation float naïve 1/n_i²−1/n_f² rend
                            1.86e-47, fausse de 32 % : c'est exactement le défaut corrigé) ;
      ΔE(10¹⁸ -> 10¹⁸+1) = +2.721138625e-53 eV (l'évaluation naïve rendait 0.0 : zéro trompeur) ;
      λ(10¹⁶, 10¹⁶+1)    = 4.556335253e+40 m  (= h·c/|ΔE|, mêmes rationnels exacts, second chemin).

SOUNDNESS : n<1, n non entier (float/str/NaN/inf), bool, n_i==n_f, série inconnue/non-str -> ValueError ;
ABSTENTION structurelle quand le résultat exact n'est pas représentable en float à pleine précision :
sous-flow (0.0/subnormal trompeur, ex. ΔE(10¹¹⁰ -> 10¹¹⁰+1)) et dépassement (ex. λ(10¹¹⁰, 10¹¹⁰+1),
r(10¹⁶⁰)) -> ValueError.
"""
import atome_hydrogene as H

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
    """True ssi fn(*a) lève ValueError (abstention structurelle)."""
    try:
        fn(*a)
        return False
    except ValueError:
        return True


def proche(x, attendu, tol):
    return x is not None and abs(x - attendu) <= tol


# ── 1) ANCRES : niveaux d'énergie (spectroscopie / CODATA, valeurs EN DUR) ──
check(proche(H.energie_niveau(1), -13.6057, 1e-3), "E_1 = −13.6057 eV (fondamental, mesuré)")
check(proche(H.energie_niveau(2), -3.40142, 1e-4), "E_2 = −3.40142 eV (mesuré ; = E_1/4)")
# calcul à la main : 13.605693122994/9 = 1.5117436803
check(proche(H.energie_niveau(3), -1.5117437, 1e-5), "E_3 = −1.5117437 eV (main : E_R/9)")
# calcul à la main : 13.605693122994/16 = 0.8503558202
check(proche(H.energie_niveau(4), -0.8503558, 1e-5), "E_4 = −0.8503558 eV (main : E_R/16)")
# loi en 1/n² : E_2 doit valoir le quart de l'ancre E_1 (−13.6057/4 = −3.401425, calcul à la main)
check(proche(H.energie_niveau(2), -13.6057 / 4.0, 1e-4), "cohérence 1/n² : E_2 = E_1(ancre)/4")
# état lié : E_n < 0 pour tout n
for n in (1, 2, 3, 5, 10, 100):
    check(H.energie_niveau(n) < 0, f"E_{n} < 0 (état lié)")
# E_n croît (se rapproche de 0) quand n croît
check(H.energie_niveau(1) < H.energie_niveau(2) < H.energie_niveau(3) < H.energie_niveau(10) < 0,
      "E_1 < E_2 < E_3 < E_10 < 0 (niveaux qui se resserrent vers 0)")

# ── 2) ANCRE : E_1 en joules = −2.1798723611e-18 J (énergie de Rydberg CODATA, en J) ──
check(proche(H.energie_niveau_joules(1), -2.1798723611e-18, 1e-22),
      "E_1 = −2.1798723611e-18 J (Rydberg CODATA en joules)")
# calcul à la main : E_2(J) = E_1(J)/4 = −5.4496809e-19 J
check(proche(H.energie_niveau_joules(2), -5.4496809e-19, 1e-23), "E_2(J) = −5.4496809e-19 J (main)")

# ── 3) ANCRES : longueurs d'onde MESURÉES (spectroscopie, indépendantes de la formule) ──
check(proche(H.longueur_onde_transition(3, 2), 656.3e-9, 0.5e-9), "Balmer Hα (3->2) ≈ 656.3 nm (mesuré)")
check(proche(H.longueur_onde_transition(4, 2), 486.1e-9, 0.5e-9), "Balmer Hβ (4->2) ≈ 486.1 nm (mesuré)")
check(proche(H.longueur_onde_transition(2, 1), 121.6e-9, 0.5e-9), "Lyman α (2->1) ≈ 121.6 nm (mesuré)")
check(proche(H.longueur_onde_transition(4, 3), 1875.1e-9, 1.5e-9), "Paschen α (4->3) ≈ 1875.1 nm (mesuré)")
# limite de Balmer (∞->2) approchée par n_i=10000 : λ ≈ 364.6 nm (mesuré)
check(proche(H.longueur_onde_transition(10000, 2), 364.6e-9, 0.5e-9),
      "limite de Balmer (∞->2, via n_i=10000) ≈ 364.6 nm (mesuré)")
# symétrie : |ΔE| identique dans les deux sens
check(H.longueur_onde_transition(3, 2) == H.longueur_onde_transition(2, 3), "λ(3,2) = λ(2,3) (symétrie)")
# classification physique des séries (bandes spectrales connues) :
check(H.longueur_onde_transition(2, 1) < 380e-9, "Lyman dans l'UV (< 380 nm)")
check(380e-9 < H.longueur_onde_transition(3, 2) < 750e-9, "Balmer Hα dans le VISIBLE")
check(H.longueur_onde_transition(4, 3) > 750e-9, "Paschen dans l'IR (> 750 nm)")

# ── 4) ÉNERGIES DE TRANSITION (calculs à la main EN DUR) ──
# ΔE(3->2) = E_2 − E_3 = −E_R·(1/4 − 1/9) = −E_R·5/36 = −1.8896796 eV (main)
check(proche(H.energie_transition(3, 2), -1.8896796, 1e-5), "ΔE(3->2) = −1.8896796 eV (main, émission)")
# ΔE(1->2) = E_2 − E_1 = +E_R·3/4 = +10.2042698 eV (main)
check(proche(H.energie_transition(1, 2), 10.2042698, 1e-5), "ΔE(1->2) = +10.2042698 eV (main, absorption)")
check(H.energie_transition(2, 1) < 0, "émission (n_i > n_f) -> ΔE < 0")
check(H.energie_transition(1, 3) > 0, "absorption (n_i < n_f) -> ΔE > 0")
check(H.energie_transition(1, 2) == -H.energie_transition(2, 1), "antisymétrie ΔE(1,2) = −ΔE(2,1)")

# ── 4bis) GRANDS n : exactitude anti-annulation (ancres second chemin, différence directe des
#          niveaux exacts en Fraction — voir docstring — valeurs EN DUR) ──
check(proche(H.energie_transition(10**8, 10**8 + 1), 2.721138584e-23, 1e-32),
      "ΔE(10^8 -> 10^8+1) = 2.721138584e-23 eV (second chemin rationnel exact)")
check(proche(H.energie_transition(10**16, 10**16 + 1), 2.721138625e-47, 1e-56),
      "ΔE(10^16 -> 10^16+1) = 2.721138625e-47 eV (le float naïf rendait 1.86e-47, faux de 32 %)")
check(proche(H.energie_transition(10**18, 10**18 + 1), 2.721138625e-53, 1e-62),
      "ΔE(10^18 -> 10^18+1) = 2.721138625e-53 eV (le float naïf rendait 0.0 : zéro trompeur)")
check(H.energie_transition(10**18, 10**18 + 1) != 0.0,
      "ΔE entre niveaux DISTINCTS n'est JAMAIS 0.0 (garantie de la docstring tenue)")
check(H.energie_transition(10**18, 10**18 + 1) > 0, "absorption vers le haut même à n astronomique (ΔE > 0)")
check(H.energie_transition(10**16, 10**16 + 1) == -H.energie_transition(10**16 + 1, 10**16),
      "antisymétrie ΔE conservée à grand n")
check(proche(H.longueur_onde_transition(10**16, 10**16 + 1), 4.556335253e+40, 1e31),
      "λ(10^16, 10^16+1) = 4.556335253e+40 m (second chemin rationnel exact)")
check(H.longueur_onde_transition(10**16, 10**16 + 1) == H.longueur_onde_transition(10**16 + 1, 10**16),
      "symétrie λ conservée à grand n")

# ── 5) ANCRE : rayon de Bohr (CODATA 2018) ──
check(proche(H.rayon_bohr(1), 5.29177210903e-11, 1e-15), "r_1 = a0 = 5.29177210903e-11 m (CODATA)")
check(proche(H.rayon_bohr(1), 0.0529e-9, 1e-13), "a0 ≈ 0.0529 nm (valeur classique)")
# calculs à la main : r_2 = 4·a0 = 2.1167088436e-10 ; r_3 = 9·a0 = 4.7625948981e-10
check(proche(H.rayon_bohr(2), 2.1167088436e-10, 1e-14), "r_2 = 4·a0 (main)")
check(proche(H.rayon_bohr(3), 4.7625948981e-10, 1e-14), "r_3 = 9·a0 (main)")
check(H.rayon_bohr(1) < H.rayon_bohr(2) < H.rayon_bohr(3), "r_n croissant en n²")

# ── 6) SÉRIES SPECTRALES (convention historique : Lyman 1906, Balmer 1885, Paschen 1908) ──
check(H.serie("Lyman") == 1, "Lyman -> n_f = 1")
check(H.serie("Balmer") == 2, "Balmer -> n_f = 2")
check(H.serie("Paschen") == 3, "Paschen -> n_f = 3")
check(H.serie("BALMER") == 2, "insensible à la casse")

# ── 7) IONISATION : E_ion(1) = 13.6057 eV (potentiel d'ionisation MESURÉ de H) ──
check(proche(H.energie_ionisation(1), 13.6057, 1e-3), "E_ion(1) = 13.6057 eV (mesuré)")
check(proche(H.energie_ionisation(2), 3.40142, 1e-4), "E_ion(2) = 3.40142 eV")
check(H.energie_ionisation(3) == -H.energie_niveau(3), "cohérence : E_ion(n) = −E_n")
check(H.energie_ionisation(2) > 0, "E_ion > 0 (il FAUT fournir de l'énergie)")

# ── 8) SOUNDNESS — nombre quantique n ──
check(leve(H.energie_niveau, 0), "n=0 -> ValueError")
check(leve(H.energie_niveau, -3), "n<0 -> ValueError")
check(leve(H.energie_niveau, 2.5), "n float -> ValueError")
check(leve(H.energie_niveau, 2.0), "n=2.0 (float même entier) -> ValueError")
check(leve(H.energie_niveau, True), "n bool -> ValueError")
check(leve(H.energie_niveau, "2"), "n str -> ValueError")
check(leve(H.energie_niveau, float("nan")), "n NaN -> ValueError")
check(leve(H.energie_niveau, float("inf")), "n inf -> ValueError")
check(leve(H.energie_niveau_joules, 0), "joules n=0 -> ValueError")
check(leve(H.energie_niveau_joules, True), "joules bool -> ValueError")
check(leve(H.rayon_bohr, 0), "rayon n=0 -> ValueError")
check(leve(H.rayon_bohr, -1), "rayon n<0 -> ValueError")
check(leve(H.rayon_bohr, 1.0), "rayon n float -> ValueError")
check(leve(H.rayon_bohr, True), "rayon bool -> ValueError")
check(leve(H.energie_ionisation, 0), "ionisation n=0 -> ValueError")
check(leve(H.energie_ionisation, True), "ionisation bool -> ValueError")
check(leve(H.energie_ionisation, 3.5), "ionisation n float -> ValueError")

# ── 9) SOUNDNESS — transitions ──
check(leve(H.energie_transition, 2, 2), "n_i == n_f -> ValueError")
check(leve(H.energie_transition, 0, 2), "transition n_i=0 -> ValueError")
check(leve(H.energie_transition, 2, 0), "transition n_f=0 -> ValueError")
check(leve(H.energie_transition, True, 2), "transition n_i bool -> ValueError")
check(leve(H.energie_transition, 1, True), "transition n_f bool -> ValueError")
check(leve(H.energie_transition, 1.5, 2), "transition n_i float -> ValueError")
check(leve(H.longueur_onde_transition, 3, 3), "λ n_i == n_f -> ValueError")
check(leve(H.longueur_onde_transition, 0, 1), "λ n_i=0 -> ValueError")
check(leve(H.longueur_onde_transition, True, 2), "λ bool -> ValueError")
check(leve(H.longueur_onde_transition, 2, "1"), "λ str -> ValueError")

# ── 9bis) SOUNDNESS — abstention sur non-représentable (sous-flow / dépassement) ──
# ΔE(10^110 -> 10^110+1) exact ≈ 2.7e-329 eV : sous le plus petit float subnormal (4.9e-324)
# -> l'exact s'arrondirait à 0.0 entre deux niveaux DISTINCTS : le module DOIT refuser.
check(leve(H.energie_transition, 10**110, 10**110 + 1),
      "ΔE sous-flow (n=10^110 adjacents) -> ValueError (jamais un zéro/subnormal trompeur)")
check(leve(H.energie_transition, 10**110 + 1, 10**110),
      "ΔE sous-flow, sens émission -> ValueError (abstention symétrique)")
# λ correspondante ≈ 4.6e+322 m > plus grand float (1.8e308) -> refus, jamais inf.
check(leve(H.longueur_onde_transition, 10**110, 10**110 + 1),
      "λ dépassement (niveaux quasi dégénérés) -> ValueError (jamais un infini)")
# E(10^160) exact ≈ −1.36e-319 eV : subnormal (< 2.2e-308), précision dégradée -> refus.
check(leve(H.energie_niveau, 10**160), "E_n subnormal (n=10^160) -> ValueError")
check(leve(H.energie_niveau_joules, 10**160), "E_n joules sous-flow (n=10^160) -> ValueError")
check(leve(H.energie_ionisation, 10**160), "E_ion subnormal (n=10^160) -> ValueError")
# r(10^160) = 10^320·a0 ≈ 5.3e+309 m > plus grand float -> refus.
check(leve(H.rayon_bohr, 10**160), "r_n dépassement (n=10^160) -> ValueError")

# ── 10) SOUNDNESS — séries (closed-set) ──
check(leve(H.serie, "Brackett"), "Brackett (hors closed-set) -> ValueError (abstention)")
check(leve(H.serie, "euclide"), "série inconnue -> ValueError")
check(leve(H.serie, ""), "série vide -> ValueError")
check(leve(H.serie, 2), "série int -> ValueError")
check(leve(H.serie, True), "série bool -> ValueError")

# ── 11) DÉTERMINISME ──
check(H.energie_niveau(3) == H.energie_niveau(3), "déterminisme energie_niveau")
check(H.longueur_onde_transition(3, 2) == H.longueur_onde_transition(3, 2), "déterminisme λ")
check(H.rayon_bohr(2) == H.rayon_bohr(2), "déterminisme rayon_bohr")
check(H.energie_transition(3, 2) == H.energie_transition(3, 2), "déterminisme ΔE")
check(H.energie_transition(10**16, 10**16 + 1) == H.energie_transition(10**16, 10**16 + 1),
      "déterminisme ΔE à grand n (chemin rationnel exact)")

print(f"\n=== valide_atome_hydrogene : {ok}/{ok+ko} ===")
import sys
sys.exit(0 if ko == 0 else 1)
