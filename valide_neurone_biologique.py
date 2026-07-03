"""
VALIDE neurone_biologique.py — held-out ADVERSE.

Vérifie : 1) EXACTITUDE des mécanismes établis (seuil de PA, potentiel de repos,
courbe f-I rectifiée, plafond réfractaire) sur ancres connues recalculées à la main ;
2) SOUNDNESS — gain négatif, entrée non numérique, période réfractaire <= 0,
NaN/inf, booléen -> ValueError (abstention, JAMAIS un faux) ;
3) DÉTERMINISME.
"""
import math
import neurone_biologique as N

ok = 0
ko = 0


def check(cond, label):
    global ok, ko
    if cond:
        ok += 1
    else:
        ko += 1
        print(f"  FAIL: {label}")


def leve_v(fn, *a, **k):
    try:
        fn(*a, **k)
        return False
    except ValueError:
        return True
    except Exception:
        return False


# 1) DÉPASSEMENT DU SEUIL — déclenchement du potentiel d'action.
# Cas du sujet : -50 mV >= -55 mV -> déclenche.
check(N.depasse_seuil(-50, -55) is True, "-50 >= -55 -> déclenche PA")
# -60 mV -> non (sous le seuil).
check(N.depasse_seuil(-60, -55) is False, "-60 < -55 -> pas de PA")
# Exactement au seuil : -55 >= -55 -> déclenche (>=).
check(N.depasse_seuil(-55, -55) is True, "-55 == seuil -> déclenche (>=)")
# Seuil par défaut = -55 mV : repos -70 mV ne déclenche pas.
check(N.depasse_seuil(-70) is False, "repos -70 (seuil défaut -55) -> pas de PA")
# Dépolarisation forte déclenche.
check(N.depasse_seuil(-30) is True, "-30 (seuil défaut) -> déclenche")
# Juste sous le seuil défaut.
check(N.depasse_seuil(-55.01) is False, "-55.01 < -55 -> pas de PA")
check(N.depasse_seuil(-54.99) is True, "-54.99 >= -55 -> déclenche")

# 2) POTENTIEL DE REPOS — fait établi.
check(N.potentiel_repos() == -70.0, "potentiel de repos = -70 mV")
check(N.POTENTIEL_REPOS_MV == -70.0, "constante POTENTIEL_REPOS_MV")
check(N.SEUIL_DEFAUT_MV == -55.0, "constante SEUIL_DEFAUT_MV")

# 3) COURBE f-I RECTIFIÉE — f = max(0, gain*(courant - seuil_courant)).
# Au-dessus du seuil : gain*(I-Iseuil) recalculé à la main.
check(abs(N.frequence_decharge(2, 1, 10) - 10.0) < 1e-9, "f-I : 10*(2-1)=10 Hz")
check(abs(N.frequence_decharge(3, 1, 5) - 10.0) < 1e-9, "f-I : 5*(3-1)=10 Hz")
check(abs(N.frequence_decharge(5.0, 2.0, 4.0) - 12.0) < 1e-9, "f-I : 4*(5-2)=12 Hz")
# Sous le seuil (rhéobase) -> rectifié à 0, jamais négatif.
check(N.frequence_decharge(0.5, 1, 10) == 0.0, "f-I sous rhéobase -> 0 (rectifié)")
check(N.frequence_decharge(1, 1, 10) == 0.0, "f-I au seuil exact -> 0")
check(N.frequence_decharge(-5, 1, 3) == 0.0, "f-I courant < seuil -> 0")
# Propriété : f >= 0 toujours (rectification).
for c, s, g in [(2, 1, 10), (0.5, 1, 10), (10, 3, 2), (-1, 0, 5), (0, 0, 0)]:
    check(N.frequence_decharge(c, s, g) >= 0.0, f"f-I rectifiée >=0 ({c},{s},{g})")
# gain=0 -> f=0 partout.
check(N.frequence_decharge(100, 1, 0) == 0.0, "gain=0 -> f=0")

# 4) PÉRIODE RÉFRACTAIRE — plafond de fréquence f_max = 1000/T(ms).
check(abs(N.frequence_max_refractaire(2.0) - 500.0) < 1e-9, "T=2ms -> f_max=500 Hz")
check(abs(N.frequence_max_refractaire(1.0) - 1000.0) < 1e-9, "T=1ms -> f_max=1000 Hz")
check(abs(N.frequence_max_refractaire(4.0) - 250.0) < 1e-9, "T=4ms -> f_max=250 Hz")
# Décharge bornée par la réfractaire.
# f brute = 10*(100-1)=990 mais plafond T=2ms -> 500.
check(abs(N.frequence_decharge_bornee(100, 1, 10, 2.0) - 500.0) < 1e-9,
      "bornée : 990 plafonné à 500 Hz (réfractaire)")
# f brute = 10 < plafond 500 -> inchangée.
check(abs(N.frequence_decharge_bornee(2, 1, 10, 2.0) - 10.0) < 1e-9,
      "bornée : 10 < 500 -> inchangée")
# Sous le seuil -> 0 même avec plafond.
check(N.frequence_decharge_bornee(0, 5, 10, 1.0) == 0.0, "bornée sous rhéobase -> 0")

# 5) SOUNDNESS — abstention par ValueError (JAMAIS un faux).
# gain < 0 (pente physiquement absurde).
check(leve_v(N.frequence_decharge, 2, 1, -1), "gain<0 -> ValueError")
check(leve_v(N.frequence_decharge, 5, 2, -0.001), "gain légèrement <0 -> ValueError")
# courant / entrées non numériques.
check(leve_v(N.frequence_decharge, "x", 1, 10), "courant non numérique -> ValueError")
check(leve_v(N.frequence_decharge, 2, "s", 10), "seuil_courant non num -> ValueError")
check(leve_v(N.frequence_decharge, 2, 1, "g"), "gain non num -> ValueError")
check(leve_v(N.frequence_decharge, None, 1, 10), "courant None -> ValueError")
check(leve_v(N.depasse_seuil, "a"), "potentiel non num -> ValueError")
check(leve_v(N.depasse_seuil, -50, "b"), "seuil non num -> ValueError")
check(leve_v(N.depasse_seuil, None), "potentiel None -> ValueError")
# Booléens rejetés (bool n'est pas une grandeur physique).
check(leve_v(N.depasse_seuil, True), "bool potentiel -> ValueError")
check(leve_v(N.frequence_decharge, True, 1, 10), "bool courant -> ValueError")
# NaN / inf rejetés.
check(leve_v(N.depasse_seuil, float("nan")), "NaN -> ValueError")
check(leve_v(N.depasse_seuil, float("inf")), "inf -> ValueError")
check(leve_v(N.frequence_decharge, float("nan"), 1, 10), "NaN courant -> ValueError")
check(leve_v(N.frequence_decharge, 2, 1, float("inf")), "inf gain -> ValueError")
# Période réfractaire <= 0.
check(leve_v(N.frequence_max_refractaire, 0), "T=0 -> ValueError")
check(leve_v(N.frequence_max_refractaire, -2), "T<0 -> ValueError")
check(leve_v(N.frequence_max_refractaire, "t"), "T non num -> ValueError")
check(leve_v(N.frequence_decharge_bornee, 2, 1, 10, 0), "bornée T=0 -> ValueError")
check(leve_v(N.frequence_decharge_bornee, 2, 1, -1, 2), "bornée gain<0 -> ValueError")

# 6) DÉTERMINISME.
check(N.frequence_decharge(3, 1, 5) == N.frequence_decharge(3, 1, 5), "déterminisme f-I")
check(N.depasse_seuil(-50, -55) == N.depasse_seuil(-50, -55), "déterminisme seuil")
check(N.frequence_max_refractaire(2.0) == N.frequence_max_refractaire(2.0),
      "déterminisme f_max")

# 7) COHÉRENCE — un PA est tout-ou-rien (booléen strict).
check(isinstance(N.depasse_seuil(-50), bool), "depasse_seuil renvoie un bool")
# Le seuil de PA est plus dépolarisé que le repos (fait : -55 > -70).
check(N.SEUIL_DEFAUT_MV > N.POTENTIEL_REPOS_MV, "seuil PA au-dessus du repos")

print(f"\n=== valide_neurone_biologique : {ok}/{ok+ko} ===")
import sys
sys.exit(0 if ko == 0 else 1)
