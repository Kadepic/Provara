"""
VALIDE petrochimie.py — held-out ADVERSE. Exactitude des coupes pétrolières
(plages de distillation établies) + moyenne volumique de l'indice d'octane +
soundness (volume<=0 / température non numérique -> ValueError) + déterminisme.
Aucune ancre recalculée à la main n'apparaît dans __main__ du module.
"""
import petrochimie as P

ok = 0
ko = 0


def check(cond, label):
    global ok, ko
    if cond:
        ok += 1
    else:
        ko += 1
        print(f"  FAIL: {label}")


# ----------------------------------------------------------------------------
# 1) EXACTITUDE — coupes pétrolières aux cas demandés.
check(P.fraction_distillation(100) == "essence", "100°C -> essence (coupe 30-200)")
check(P.fraction_distillation(250) == "kerosene", "250°C -> kérosène (~250)")
check(P.fraction_distillation(20) == "gaz", "20°C -> gaz (<30)")
check(P.fraction_distillation(350) == "diesel/gazole", "350°C -> diesel/gazole")
check(P.fraction_distillation(500) == "residu/bitume", "500°C -> résidu/bitume")

# 2) EXACTITUDE — bornes (partition semi-ouverte [inf, sup)).
check(P.fraction_distillation(29.999) == "gaz", "29.999 -> gaz")
check(P.fraction_distillation(30) == "essence", "30 -> essence (borne incluse)")
check(P.fraction_distillation(199.999) == "essence", "199.999 -> essence")
check(P.fraction_distillation(200) == "kerosene", "200 -> kérosène (borne incluse)")
check(P.fraction_distillation(299.999) == "kerosene", "299.999 -> kérosène")
check(P.fraction_distillation(300) == "diesel/gazole", "300 -> diesel/gazole (borne)")
check(P.fraction_distillation(399.999) == "diesel/gazole", "399.999 -> diesel/gazole")
check(P.fraction_distillation(400) == "residu/bitume", "400 -> résidu/bitume (borne)")

# 3) EXACTITUDE — températures extrêmes / négatives (gaz légers : méthane -161°C).
check(P.fraction_distillation(-161) == "gaz", "méthane -161°C -> gaz")
check(P.fraction_distillation(0) == "gaz", "0°C -> gaz")
check(P.fraction_distillation(1000) == "residu/bitume", "1000°C -> résidu/bitume")

# 4) EXACTITUDE — indice d'octane (moyenne volumique). Ancres recalculées main.
# (87*50 + 91*50)/(50+50) = 8900/100 = 89.0
check(abs(P.indice_octane_melange(87, 50, 91, 50) - 89.0) < 1e-9,
      "octane 87 & 91 à 50/50 -> 89")
# (95*30 + 98*70)/100 = (2850 + 6860)/100 = 9710/100 = 97.1
check(abs(P.indice_octane_melange(95, 30, 98, 70) - 97.1) < 1e-9,
      "octane 95/98 à 30/70 -> 97.1")
# (80*1 + 100*3)/4 = 380/4 = 95.0  (pondération par volume, pas 90)
check(abs(P.indice_octane_melange(80, 1, 100, 3) - 95.0) < 1e-9,
      "octane 80/100 à 1/3 -> 95 (volumique, pas arithmétique 90)")
# identiques -> identité : (90*10 + 90*40)/50 = 90
check(abs(P.indice_octane_melange(90, 10, 90, 40) - 90.0) < 1e-9,
      "octane identiques -> 90")
# proportion : tout le volume sur o1 (v2 -> 0+) tend vers o1, ici 60/40
# (87*60 + 91*40)/100 = (5220 + 3640)/100 = 8860/100 = 88.6
check(abs(P.indice_octane_melange(87, 60, 91, 40) - 88.6) < 1e-9,
      "octane 87/91 à 60/40 -> 88.6")

# 5) SOUNDNESS — volumes <= 0 -> ValueError (abstention, jamais un faux indice).
def leve(fn, *a):
    try:
        fn(*a)
        return False
    except ValueError:
        return True
    except Exception:
        return False

check(leve(P.indice_octane_melange, 87, 0, 91, 50), "volume_1 = 0 -> ValueError")
check(leve(P.indice_octane_melange, 87, 50, 91, 0), "volume_2 = 0 -> ValueError")
check(leve(P.indice_octane_melange, 87, -10, 91, 50), "volume_1 < 0 -> ValueError")
check(leve(P.indice_octane_melange, 87, 50, 91, -5), "volume_2 < 0 -> ValueError")
check(leve(P.indice_octane_melange, 87, 0, 91, 0), "v1=v2=0 (div/0 évitée) -> ValueError")

# 6) SOUNDNESS — entrées non numériques -> ValueError.
check(leve(P.fraction_distillation, "chaud"), "température str -> ValueError")
check(leve(P.fraction_distillation, None), "température None -> ValueError")
check(leve(P.fraction_distillation, True), "température bool -> ValueError")
check(leve(P.fraction_distillation, float("nan")), "température NaN -> ValueError")
check(leve(P.indice_octane_melange, "x", 50, 91, 50), "octane_1 str -> ValueError")
check(leve(P.indice_octane_melange, 87, "v", 91, 50), "volume_1 str -> ValueError")
check(leve(P.indice_octane_melange, 87, 50, None, 50), "octane_2 None -> ValueError")
check(leve(P.indice_octane_melange, 87, float("nan"), 91, 50), "volume_1 NaN -> ValueError")

# 7) DÉTERMINISME (entrées pures -> sorties stables).
check(P.fraction_distillation(250) == P.fraction_distillation(250), "déterminisme coupe")
check(P.indice_octane_melange(87, 50, 91, 50) == P.indice_octane_melange(87, 50, 91, 50),
      "déterminisme octane")

# 8) Catalogue de faits exposé et cohérent avec les cas.
check(P.coupes() == ["gaz", "essence", "kerosene", "diesel/gazole", "residu/bitume"],
      "catalogue des 5 coupes")
check(len(set(P.coupes())) == 5, "5 coupes distinctes")

print(f"\n=== valide_petrochimie : {ok}/{ok+ko} ===")
import sys
sys.exit(0 if ko == 0 else 1)
