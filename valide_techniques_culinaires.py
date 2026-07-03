"""
VALIDE techniques_culinaires.py — held-out ADVERSE.
Ancres connues (taxonomie cuisson + températures de référence) + soundness (inconnu -> ValueError)
+ déterminisme. FAUX=0 : aucune réponse inventée ; toute entrée hors référentiel -> abstention.
"""
import techniques_culinaires as T

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


# 1) MODE DE CUISSON — ancres du sujet.
check(T.mode_cuisson("bouillir") == "humide", "bouillir = humide")
check(T.mode_cuisson("pocher") == "humide", "pocher = humide")
check(T.mode_cuisson("vapeur") == "humide", "vapeur = humide")
check(T.mode_cuisson("rotir") == "sec", "rotir = sec")
check(T.mode_cuisson("griller") == "sec", "griller = sec")
check(T.mode_cuisson("four") == "sec", "four = sec")
check(T.mode_cuisson("frire") == "matiere_grasse", "frire = matiere_grasse")
check(T.mode_cuisson("sauter") == "matiere_grasse", "sauter = matiere_grasse")
check(T.mode_cuisson("braiser") == "mixte", "braiser = mixte")

# 2) MILIEU DE TRANSFERT — 'eau/humide', 'air/sec'.
check(T.milieu_cuisson("bouillir") == "eau", "bouillir -> milieu eau")
check(T.milieu_cuisson("vapeur") == "eau", "vapeur -> milieu eau")
check(T.milieu_cuisson("rotir") == "air", "rotir -> milieu air")
check(T.milieu_cuisson("griller") == "air", "griller -> milieu air")
check(T.milieu_cuisson("frire") == "matiere_grasse", "frire -> milieu matiere_grasse")
check(T.milieu_cuisson("braiser") == "mixte", "braiser -> milieu mixte")

# 3) ACCENTS / SYNONYMES / CASSE — held-out, normalisation robuste.
check(T.mode_cuisson("Rôtir") == "sec", "Rôtir (accent+casse) = sec")
check(T.mode_cuisson("sauté") == "matiere_grasse", "sauté (accent) = matiere_grasse")
check(T.mode_cuisson("à la vapeur") == "humide", "à la vapeur = humide")
check(T.mode_cuisson("cuire au four") == "sec", "cuire au four = sec")
check(T.mode_cuisson("friture") == "matiere_grasse", "friture = matiere_grasse")
check(T.mode_cuisson("mijoter") == "humide", "mijoter = humide")
check(T.mode_cuisson("blanchir") == "humide", "blanchir = humide")
check(T.mode_cuisson("rissoler") == "matiere_grasse", "rissoler = matiere_grasse")
check(T.mode_cuisson("ragoût") == "mixte", "ragoût = mixte")
check(T.mode_cuisson(" GRILLER ") == "sec", "espaces + majuscules tolérés")

# 4) decrit + cohérence : chaque canonique se résout, mode/milieu valides.
for tech in T.CANON:
    d = T.decrit(tech)
    check(d["mode"] in T.MODES and d["milieu"] in T.MILIEUX and d["technique"] == tech,
          f"decrit cohérent {tech}")
# invariant : milieu eau/air <=> mode humide/sec ; matiere_grasse/mixte alignés.
for tech, (mode, milieu) in T.CANON.items():
    coherent = ((milieu == "eau" and mode == "humide")
                or (milieu == "air" and mode == "sec")
                or (milieu == "matiere_grasse" and mode == "matiere_grasse")
                or (milieu == "mixte" and mode == "mixte"))
    check(coherent, f"alignement mode/milieu {tech}")

# 5) techniques_du_mode.
check("bouillir" in T.techniques_du_mode("humide"), "humide contient bouillir")
check("braiser" in T.techniques_du_mode("mixte"), "mixte contient braiser")
check(set(T.techniques_du_mode("sec")) >= {"rotir", "griller", "four"}, "sec >= {rotir,griller,four}")

# 6) TEMPÉRATURES DE RÉFÉRENCE — faits physico-chimiques.
check(T.temperature_reference("ebullition_eau") == 100.0, "eau bout à 100 °C")
check(T.temperature_reference("congelation_eau") == 0.0, "eau gèle à 0 °C")
check(abs(T.temperature_reference("maillard") - 140.0) < 1e-9, "Maillard amorce ~140 °C")
check(abs(T.temperature_reference("caramelisation") - 160.0) < 1e-9, "caramélisation ~160 °C")
# synonymes de phénomènes
check(T.temperature_reference("réaction de Maillard") == 140.0, "synonyme 'réaction de Maillard'")
check(T.temperature_reference("ébullition") == 100.0, "synonyme 'ébullition'")
check(T.temperature_reference("caramel") == 160.0, "synonyme 'caramel'")

# 7) Faits d'ordre ROBUSTES (vrais quelle que soit la source).
check(T.temperature_reference("caramelisation") > T.temperature_reference("maillard"),
      "caramélisation (160) > Maillard (140)")
check(T.temperature_reference("ebullition_eau") > T.temperature_reference("congelation_eau"),
      "ébullition > congélation")
lo, hi = T.plage_maillard()
check(lo == 140.0 and hi == 165.0 and lo <= T.temperature_reference("maillard") <= hi,
      "plage Maillard (140-165) encadre l'amorce")
# Maillard amorce dans la fourchette 140-165 demandée par le sujet.
check(140.0 <= T.temperature_reference("maillard") <= 165.0, "Maillard dans 140-165 °C")

# 8) POINTS DE FUMÉE — données sourcées, testées par bornes/ordre ROBUSTES (pas d'exact fragile).
check(T.point_de_fumee("beurre") < 175.0, "beurre = point de fumée bas (< 175)")
check(160.0 <= T.point_de_fumee("huile_olive_vierge_extra") <= 220.0, "EVOO ~190 (160-220)")
check(T.point_de_fumee("huile_arachide") >= 215.0, "arachide raffinée élevé (>=215)")
check(T.point_de_fumee("huile_tournesol") >= 210.0, "tournesol raffiné élevé (>=210)")
check(T.point_de_fumee("beurre") < T.point_de_fumee("huile_arachide"),
      "beurre < arachide (ordre robuste)")
check(T.point_de_fumee("ghee") > T.point_de_fumee("beurre"),
      "beurre clarifié (ghee) > beurre")
check(T.point_de_fumee("Huile d'olive vierge extra") == T.point_de_fumee("huile_olive_vierge_extra"),
      "synonyme EVOO normalisé")
check(all(v > 0 for v in T.POINTS_FUMEE.values()), "tous points de fumée > 0")
# friture : huile à haut point de fumée convient, beurre non.
check(T.convient_friture("huile_arachide") is True, "arachide convient à la friture (180)")
check(T.convient_friture("beurre") is False, "beurre ne convient pas à 180 °C")

# 9) SOUNDNESS — inconnu / invalide -> ValueError (JAMAIS inventer).
check(leve(T.mode_cuisson, "léviter"), "technique inconnue -> ValueError")
check(leve(T.mode_cuisson, "micro-ondes"), "micro-ondes (hors taxo thermique classique) -> ValueError")
check(leve(T.mode_cuisson, ""), "technique vide -> ValueError")
check(leve(T.mode_cuisson, "   "), "technique espaces -> ValueError")
check(leve(T.mode_cuisson, None), "technique None -> ValueError")
check(leve(T.mode_cuisson, 42), "technique non-str -> ValueError")
check(leve(T.milieu_cuisson, "inconnu"), "milieu_cuisson inconnu -> ValueError")
check(leve(T.decrit, "xyz"), "decrit inconnu -> ValueError")
check(leve(T.temperature_reference, "fusion_du_titane"), "phénomène inconnu -> ValueError")
check(leve(T.temperature_reference, ""), "phénomène vide -> ValueError")
check(leve(T.point_de_fumee, "huile_de_licorne"), "huile inconnue -> ValueError")
check(leve(T.point_de_fumee, None), "huile None -> ValueError")
check(leve(T.techniques_du_mode, "tiede"), "mode inconnu -> ValueError")
check(leve(T.convient_friture, "huile_arachide", 0), "température friture nulle -> ValueError")
check(leve(T.convient_friture, "huile_arachide", -5), "température friture négative -> ValueError")
check(leve(T.convient_friture, "huile_arachide", "chaud"), "température non num -> ValueError")
check(leve(T.convient_friture, "huile_inconnue"), "friture huile inconnue -> ValueError")

# 10) DÉTERMINISME.
check(T.mode_cuisson("braiser") == T.mode_cuisson("braiser"), "déterminisme mode")
check(T.temperature_reference("maillard") == T.temperature_reference("maillard"), "déterminisme température")
check(T.point_de_fumee("beurre") == T.point_de_fumee("beurre"), "déterminisme point de fumée")

print(f"\n=== valide_techniques_culinaires : {ok}/{ok+ko} ===")
import sys
sys.exit(0 if ko == 0 else 1)
