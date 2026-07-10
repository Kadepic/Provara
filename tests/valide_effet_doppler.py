"""
VALIDE effet_doppler.py — held-out ADVERSE.

ANCRES EXTERNES NON CIRCULAIRES (valeurs connues ou calculées À LA MAIN, PAS recalculées par la formule testée) :
  • Source et observateur IMMOBILES -> f' = f EXACTEMENT (aucun effet Doppler sans mouvement relatif — physique
    élémentaire, indépendante de toute formule).
  • Ambulance f = 1000 Hz s'approchant à 30 m/s (v = 343 m/s) : f' = 1000·343/313 = 343000/313.
    À LA MAIN : 313 × 1095.8466453674121 = 343000 (vérifié par multiplication inverse) -> 1095.8466453674121 Hz.
  • Après passage (v_src = −30) : f' = 1000·343/373 = 343000/373.
    À LA MAIN : 373 × 919.5710455764075 = 343000 -> 919.5710455764075 Hz.
  • Observateur s'approchant à 30 m/s (source fixe) : f' = 1000·373/343 = 373000/343.
    À LA MAIN : 343 × 1087.4635568513119 = 373000 -> 1087.4635568513119 Hz.
    ASYMÉTRIE CLASSIQUE : 1095.85 ≠ 1087.46 (le milieu brise la symétrie source/observateur).
  • Encadrement : f_approche > f > f_éloignement (le son monte à l'approche, descend à l'éloignement — vécu).
  • RELATIVISTE : β = 0 -> f' = f EXACTEMENT ; β = 3/5 (rapprochement) -> f' = 2f EXACTEMENT car
    sqrt((1+3/5)/(1−3/5)) = sqrt((8/5)/(2/5)) = sqrt(4) = 2 (ancre remarquable, calculée à la main) ;
    β = −3/5 -> f' = f/2 (sqrt((2/5)/(8/5)) = sqrt(1/4) = 1/2) ; β = 4/5 -> f' = 3f (sqrt(9) = 3).
  • Réciprocité relativiste : facteur(β)·facteur(−β) = 1, vérifiée sur les ancres exactes : 2000 × 500 = 1000².

SOUNDNESS : f≤0, v≤0, |v_src|≥v (mur du son), |v_obs|≥v, |β|≥1, bool/str/NaN/±inf -> ValueError ;
DÉBORDEMENT/SOUS-DÉBORDEMENT du résultat (f' vrai strictement positif mais inf/0.0 en flottant) -> ValueError.
"""
import math
from fractions import Fraction

import effet_doppler as D

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


def proche(x, attendu, tol=1e-5):
    return x is not None and abs(x - attendu) <= tol


# ── 1) CONSTANTE SOURCÉE ──
check(D.V_SON_AIR_20C == 343.0, "célérité du son air 20°C = 343 m/s (tables acoustiques)")

# ── 2) ANCRE : immobiles -> f' = f EXACTEMENT ──
check(D.doppler_acoustique(1000.0, 0.0, 0.0) == 1000.0, "source+observateur immobiles : f' = f = 1000 Hz exact")
check(D.doppler_acoustique(440.0) == 440.0, "défauts (v_src=v_obs=0) : f' = f = 440 Hz exact")

# ── 3) ANCRE : ambulance 1000 Hz, source s'approche à 30 m/s ──
# À la main : 1000·343/313 = 343000/313 = 1095.8466453674121 (vérif : 313 × 1095.8466453674121 = 343000)
f_app = D.doppler_acoustique(1000.0, 30.0, 0.0, 343.0)
check(proche(f_app, 1095.8466453674121, tol=5e-3), f"approche 30 m/s : f' = {f_app} ≈ 1095.847 Hz")

# ── 4) ANCRE : après passage, source s'éloigne (v_src = −30) ──
# À la main : 1000·343/373 = 343000/373 = 919.5710455764075 (vérif : 373 × 919.5710455764075 = 343000)
f_elo = D.doppler_acoustique(1000.0, -30.0, 0.0, 343.0)
check(proche(f_elo, 919.5710455764075, tol=5e-3), f"éloignement 30 m/s : f' = {f_elo} ≈ 919.571 Hz")

# ── 5) ENCADREMENT : f_approche > f > f_éloignement ──
check(f_app > 1000.0, "f_approche > f (le son monte à l'approche)")
check(f_elo < 1000.0, "f_éloignement < f (le son descend à l'éloignement)")
check(f_app > 1000.0 > f_elo, "encadrement complet f_app > f > f_elo")

# ── 6) ANCRE : observateur s'approche à 30 m/s, source fixe ──
# À la main : 1000·373/343 = 373000/343 = 1087.4635568513119 (vérif : 343 × 1087.4635568513119 = 373000)
f_obs = D.doppler_acoustique(1000.0, 0.0, 30.0, 343.0)
check(proche(f_obs, 1087.4635568513119, tol=5e-3), f"observateur s'approche : f' = {f_obs} ≈ 1087.464 Hz")
# Asymétrie classique du Doppler acoustique : même vitesse, effets différents
check(abs(f_app - f_obs) > 8.0, "asymétrie source/observateur : 1095.85 ≠ 1087.46 (le milieu compte)")
# Observateur qui s'éloigne : f' = 1000·(343−30)/343 = 313000/343 = 912.5364431486880 (343 × ça = 313000)
f_obs_elo = D.doppler_acoustique(1000.0, 0.0, -30.0, 343.0)
check(proche(f_obs_elo, 912.5364431486880, tol=5e-3), f"observateur s'éloigne : f' = {f_obs_elo} ≈ 912.536 Hz")

# ── 7) ANCRE : mouvements combinés, cas trivial v_obs = v_src = u -> se suivent, mais formule ≠ f ──
# Source approche 30 ET observateur approche 30 : f' = 1000·373/313 = 373000/313 = 1191.6932907348243
# (vérif : 313 × 1191.6932907348243 = 373000)
f_deux = D.doppler_acoustique(1000.0, 30.0, 30.0, 343.0)
check(proche(f_deux, 1191.6932907348243, tol=5e-3), f"double approche 30+30 : f' = {f_deux} ≈ 1191.693 Hz")
check(f_deux > f_app > f_obs, "double approche > source seule > observateur seul")

# ── 8) AUTRE CÉLÉRITÉ (le v est un paramètre, pas un dogme) : v=340, source approche 170 = v/2 -> f'=2f ──
check(D.doppler_acoustique(500.0, 170.0, 0.0, 340.0) == 1000.0,
      "v_src = v/2 -> f' = 2f exact (500 -> 1000 Hz, v=340)")

# ── 9) RELATIVISTE : β = 0 -> f' = f EXACTEMENT ──
check(D.doppler_relativiste_longitudinal(1000.0, 0) == 1000.0, "relativiste β=0 : f' = f = 1000 Hz exact")
check(D.doppler_relativiste_longitudinal(432.0, 0.0) == 432.0, "relativiste β=0.0 (float) : f' = f exact")

# ── 10) RELATIVISTE : β = 3/5 -> f' = 2f EXACTEMENT (sqrt((8/5)/(2/5)) = sqrt(4) = 2, à la main) ──
check(D.doppler_relativiste_longitudinal(1000.0, Fraction(3, 5)) == 2000.0,
      "β=3/5 rapprochement : f' = 2f = 2000 Hz EXACT")
check(D.doppler_relativiste_longitudinal(1000.0, 0.6) == 2000.0,
      "β=0.6 (float) : f' = 2000 Hz (arrondi 10 chiffres significatifs)")

# ── 11) RELATIVISTE : β = −3/5 -> f' = f/2 EXACTEMENT (sqrt((2/5)/(8/5)) = 1/2, à la main) ──
check(D.doppler_relativiste_longitudinal(1000.0, Fraction(-3, 5)) == 500.0,
      "β=−3/5 éloignement : f' = f/2 = 500 Hz EXACT")

# ── 12) RELATIVISTE : β = 4/5 -> f' = 3f EXACTEMENT (sqrt((9/5)/(1/5)) = sqrt(9) = 3, à la main) ──
check(D.doppler_relativiste_longitudinal(1000.0, Fraction(4, 5)) == 3000.0,
      "β=4/5 : f' = 3f = 3000 Hz EXACT")

# ── 13) RÉCIPROCITÉ RELATIVISTE : facteur(β)·facteur(−β) = 1, sur ancres exactes 2000 × 500 = 1000² ──
check(D.doppler_relativiste_longitudinal(1000.0, Fraction(3, 5))
      * D.doppler_relativiste_longitudinal(1000.0, Fraction(-3, 5)) == 1000.0 ** 2,
      "réciprocité : f'(β)·f'(−β) = f² (2000 × 500 = 1 000 000)")

# ── 14) ENCADREMENT RELATIVISTE : β>0 -> f'>f (blueshift), β<0 -> f'<f (redshift) ──
check(D.doppler_relativiste_longitudinal(1000.0, 0.1) > 1000.0, "β=0.1 : blueshift (f' > f)")
check(D.doppler_relativiste_longitudinal(1000.0, -0.1) < 1000.0, "β=−0.1 : redshift (f' < f)")
check(D.doppler_relativiste_longitudinal(1000.0, 0.9) > D.doppler_relativiste_longitudinal(1000.0, 0.1),
      "monotonie : β=0.9 décale plus que β=0.1")

# ── 15) SOUNDNESS acoustique — fréquence ──
check(leve(D.doppler_acoustique, 0.0, 30.0, 0.0, 343.0), "f=0 -> ValueError")
check(leve(D.doppler_acoustique, -440.0, 30.0, 0.0, 343.0), "f<0 -> ValueError")
check(leve(D.doppler_acoustique, True, 30.0, 0.0, 343.0), "f bool -> ValueError")
check(leve(D.doppler_acoustique, "1000", 30.0, 0.0, 343.0), "f str -> ValueError")
check(leve(D.doppler_acoustique, float("nan"), 30.0, 0.0, 343.0), "f NaN -> ValueError")
check(leve(D.doppler_acoustique, float("inf"), 30.0, 0.0, 343.0), "f inf -> ValueError")

# ── 16) SOUNDNESS acoustique — MUR DU SON (v_src ≥ v : dénominateur nul ou négatif) ──
check(leve(D.doppler_acoustique, 1000.0, 343.0, 0.0, 343.0), "v_src = v (mur du son) -> ValueError")
check(leve(D.doppler_acoustique, 1000.0, 400.0, 0.0, 343.0), "v_src > v (supersonique) -> ValueError")
check(leve(D.doppler_acoustique, 1000.0, -343.0, 0.0, 343.0), "v_src = −v (supersonique fuyant) -> ValueError")
check(leve(D.doppler_acoustique, 1000.0, -500.0, 0.0, 343.0), "v_src < −v -> ValueError")

# ── 17) SOUNDNESS acoustique — observateur supersonique ──
check(leve(D.doppler_acoustique, 1000.0, 0.0, 343.0, 343.0), "v_obs = v -> ValueError")
check(leve(D.doppler_acoustique, 1000.0, 0.0, -343.0, 343.0), "v_obs = −v (aucun son reçu) -> ValueError")
check(leve(D.doppler_acoustique, 1000.0, 0.0, -400.0, 343.0), "v_obs < −v -> ValueError")

# ── 18) SOUNDNESS acoustique — célérité et types des vitesses ──
check(leve(D.doppler_acoustique, 1000.0, 30.0, 0.0, 0.0), "v=0 -> ValueError")
check(leve(D.doppler_acoustique, 1000.0, 30.0, 0.0, -343.0), "v<0 -> ValueError")
check(leve(D.doppler_acoustique, 1000.0, 30.0, 0.0, float("nan")), "v NaN -> ValueError")
check(leve(D.doppler_acoustique, 1000.0, float("nan"), 0.0, 343.0), "v_src NaN -> ValueError")
check(leve(D.doppler_acoustique, 1000.0, float("inf"), 0.0, 343.0), "v_src inf -> ValueError")
check(leve(D.doppler_acoustique, 1000.0, True, 0.0, 343.0), "v_src bool -> ValueError")
check(leve(D.doppler_acoustique, 1000.0, "30", 0.0, 343.0), "v_src str -> ValueError")
check(leve(D.doppler_acoustique, 1000.0, 30.0, float("nan"), 343.0), "v_obs NaN -> ValueError")
check(leve(D.doppler_acoustique, 1000.0, 30.0, True, 343.0), "v_obs bool -> ValueError")

# ── 19) SOUNDNESS relativiste — |β| ≥ 1 et types ──
check(leve(D.doppler_relativiste_longitudinal, 1000.0, 1), "β=1 -> ValueError")
check(leve(D.doppler_relativiste_longitudinal, 1000.0, -1), "β=−1 -> ValueError")
check(leve(D.doppler_relativiste_longitudinal, 1000.0, 1.5), "β=1.5 -> ValueError")
check(leve(D.doppler_relativiste_longitudinal, 1000.0, Fraction(-7, 5)), "β=−7/5 -> ValueError")
check(leve(D.doppler_relativiste_longitudinal, 1000.0, float("nan")), "β NaN -> ValueError")
check(leve(D.doppler_relativiste_longitudinal, 1000.0, float("inf")), "β inf -> ValueError")
check(leve(D.doppler_relativiste_longitudinal, 1000.0, True), "β bool -> ValueError")
check(leve(D.doppler_relativiste_longitudinal, 1000.0, "0.6"), "β str -> ValueError")
check(leve(D.doppler_relativiste_longitudinal, 0.0, 0.5), "relativiste f=0 -> ValueError")
check(leve(D.doppler_relativiste_longitudinal, -1000.0, 0.5), "relativiste f<0 -> ValueError")
check(leve(D.doppler_relativiste_longitudinal, float("nan"), 0.5), "relativiste f NaN -> ValueError")
check(leve(D.doppler_relativiste_longitudinal, True, 0.5), "relativiste f bool -> ValueError")

# ── 20) DÉTERMINISME ──
check(D.doppler_acoustique(1000.0, 30.0, 0.0, 343.0) == D.doppler_acoustique(1000.0, 30.0, 0.0, 343.0),
      "déterminisme acoustique")
check(D.doppler_relativiste_longitudinal(1000.0, 0.37) == D.doppler_relativiste_longitudinal(1000.0, 0.37),
      "déterminisme relativiste")

# ── 21bis) SOUNDNESS — DÉBORDEMENT/SOUS-DÉBORDEMENT FLOTTANT DU RÉSULTAT (défauts d'audit corrigés) ──
# Le f' vrai est STRICTEMENT positif et fini ; si le flottant rend inf ou 0.0, c'est FAUX -> abstention.
# Cas d'audit 1 : 1e308·643/43 ≈ 1.5e309 > max float (~1.8e308) -> débordait en inf.
check(leve(D.doppler_acoustique, 1e308, 300.0, 300.0, 343.0),
      "acoustique 1e308 Hz, résultat > max float -> ValueError (plus jamais inf)")
# Cas d'audit 2 : β=4/5 -> facteur exact 3 ; 3e308 > max float -> débordait en inf.
check(leve(D.doppler_relativiste_longitudinal, 1e308, Fraction(4, 5)),
      "relativiste 1e308 Hz × 3 -> ValueError (plus jamais inf)")
# Cas d'audit 3 : f = 5e-324 (plus petit dénormal) × facteur ≈ 2.2e-4 -> sous-débordait en 0.0 Hz,
# valeur FAUSSE (le vrai f' est strictement positif, f'=0 n'arrive qu'à |β|=1 refusé).
check(leve(D.doppler_relativiste_longitudinal, 5e-324, -0.9999999),
      "relativiste 5e-324 Hz, β≈−1 : sous-débordement -> ValueError (plus jamais 0.0 Hz)")
# Sous-débordement acoustique symétrique : 5e-324 × (43/643) -> 0.0 en flottant -> abstention.
check(leve(D.doppler_acoustique, 5e-324, -300.0, -300.0, 343.0),
      "acoustique 5e-324 Hz double éloignement : sous-débordement -> ValueError")
# β en Fraction aux entiers énormes : le facteur relativiste lui-même déborde le flottant
# (OverflowError interne convertie) -> même contrat, ValueError.
check(leve(D.doppler_relativiste_longitudinal, 1000.0, Fraction(10**600 - 1, 10**600)),
      "β = (10^600−1)/10^600 : facteur non représentable -> ValueError (pas d'OverflowError brute)")
# Branche EXACTE (carré parfait) avec facteur géant : ratio = (10^200)² via β=(10^400−1)/(10^400+1),
# f' vrai = 1e308·10^200 -> non représentable -> ValueError.
check(leve(D.doppler_relativiste_longitudinal, 1e308, Fraction(10**400 - 1, 10**400 + 1)),
      "branche exacte, facteur 10^200 sur f=1e308 -> ValueError (plus jamais inf)")
# NON-RÉGRESSION : les grandes/petites valeurs LÉGITIMES (représentables) passent toujours.
# À la main : 1e10 × 2 = 2e10 (facteur exact 2 pour β=3/5, ancre du bloc 10).
check(D.doppler_relativiste_longitudinal(1e10, Fraction(3, 5)) == 2e10,
      "non-régression : f=1e10, β=3/5 -> 2e10 Hz exact (représentable, pas d'abstention)")
# À la main : 1e-20 × 343/313 ≈ 1.0958466454e-20 (même rapport que l'ancre ambulance, bloc 3).
check(proche(D.doppler_acoustique(1e-20, 30.0, 0.0, 343.0), 1.0958466454e-20, tol=1e-29),
      "non-régression : f=1e-20 Hz s'approche 30 m/s -> ≈1.0958e-20 Hz (représentable)")

# ── 21) COHÉRENCE PETITES VITESSES : à β<<1, relativiste ≈ 1+β (développement limité, à la main) ──
# β = 0.001 -> facteur ≈ 1.0010005, soit f' ≈ 1001.0005 Hz pour f = 1000 Hz (erreur relative < 1e-6)
check(proche(D.doppler_relativiste_longitudinal(1000.0, 0.001), 1001.0005, tol=1e-2),
      "β=0.001 : f' ≈ 1001.0005 Hz (développement limité 1+β+β²/2)")

print(f"\n=== valide_effet_doppler : {ok}/{ok+ko} ===")
import sys
sys.exit(0 if ko == 0 else 1)
