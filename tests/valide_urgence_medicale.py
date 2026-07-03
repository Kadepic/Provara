"""VALIDE urgence_medicale.py — ADVERSE, FAUX=0. Scores d'urgence cliniques établis.
Ancres = valeurs connues des échelles (Glasgow 15 normal / 3 coma, Apgar 10 parfait,
indice de choc) + mécanisme de somme + plages exactes + classifications consensus
+ SOUNDNESS (sous-score hors plage / non entier, PAS≤0, FC≤0, non fini -> ValueError)
+ déterminisme."""
import urgence_medicale as M

ok = 0
ko = 0


def check(c, l):
    global ok, ko
    if c:
        ok += 1
    else:
        ko += 1
        print(f"  FAIL: {l}")


def leve(fn, *a):
    try:
        fn(*a)
        return False
    except ValueError:
        return True
    except Exception:
        return False


# ===================== GLASGOW : ancres établies =====================
# Patient normal : 4 (yeux spontanés) + 5 (orienté) + 6 (obéit) = 15
check(M.score_glasgow(4, 5, 6) == 15, "Glasgow 4+5+6 = 15 (normal)")
check(M.est_coma_grave(4, 5, 6) is False, "Glasgow 15 -> pas coma grave")
check(M.gravite_glasgow(4, 5, 6) == "leger", "Glasgow 15 -> léger")
# Coma profond : 1+1+1 = 3 (minimum possible, jamais 0)
check(M.score_glasgow(1, 1, 1) == 3, "Glasgow 1+1+1 = 3 (coma profond, minimum)")
check(M.est_coma_grave(1, 1, 1) is True, "Glasgow 3 -> coma grave")
check(M.gravite_glasgow(1, 1, 1) == "grave", "Glasgow 3 -> grave")
# Seuil de coma ≤ 8 : exactement 8 = grave, 9 = modéré
check(M.est_coma_grave(2, 2, 4) is True, "Glasgow total 8 -> coma grave (seuil inclusif ≤8)")
check(M.gravite_glasgow(2, 2, 4) == "grave", "Glasgow 8 -> grave")
check(M.est_coma_grave(2, 3, 4) is False, "Glasgow total 9 -> pas coma grave")
check(M.gravite_glasgow(2, 3, 4) == "modere", "Glasgow 9 -> modéré")
check(M.gravite_glasgow(3, 4, 5) == "modere", "Glasgow 12 -> modéré")
check(M.gravite_glasgow(3, 4, 6) == "leger", "Glasgow 13 -> léger")
# Bornes des sous-scores : max légitime de chaque axe
check(M.score_glasgow(4, 5, 6) == 15, "max sous-scores = total max 15")
# total = somme exacte (mécanisme)
check(M.score_glasgow(3, 4, 5) == 12, "Glasgow somme exacte 3+4+5=12")

# ===================== GLASGOW : soundness (hors plage / non entier) =====================
check(leve(M.score_glasgow, 5, 5, 6), "yeux=5 (>4) -> ValueError")
check(leve(M.score_glasgow, 0, 5, 6), "yeux=0 (<1) -> ValueError")
check(leve(M.score_glasgow, 4, 6, 6), "verbal=6 (>5) -> ValueError")
check(leve(M.score_glasgow, 4, 0, 6), "verbal=0 (<1) -> ValueError")
check(leve(M.score_glasgow, 4, 5, 7), "moteur=7 (>6) -> ValueError")
check(leve(M.score_glasgow, 4, 5, 0), "moteur=0 (<1) -> ValueError")
check(leve(M.score_glasgow, 3.5, 5, 6), "yeux non entier (3.5) -> ValueError")
check(leve(M.score_glasgow, True, 5, 6), "yeux=bool -> ValueError")
check(leve(M.score_glasgow, "4", 5, 6), "yeux non numérique -> ValueError")
check(leve(M.est_coma_grave, 9, 5, 6), "est_coma_grave yeux hors plage -> ValueError")
check(leve(M.gravite_glasgow, 4, 9, 6), "gravite_glasgow verbal hors plage -> ValueError")

# ===================== APGAR : ancres établies =====================
# Nouveau-né parfait : tous critères à 2 -> 10
check(M.score_apgar(2, 2, 2, 2, 2) == 10, "Apgar 2x5 = 10 (parfait)")
check(M.interpretation_apgar(2, 2, 2, 2, 2) == "normal", "Apgar 10 -> normal")
# Mort-né / état critique : tous à 0 -> 0
check(M.score_apgar(0, 0, 0, 0, 0) == 0, "Apgar 0 (minimum)")
check(M.interpretation_apgar(0, 0, 0, 0, 0) == "critique", "Apgar 0 -> critique")
# Somme exacte (mécanisme)
check(M.score_apgar(2, 2, 1, 1, 2) == 8, "Apgar somme exacte 2+2+1+1+2=8")
check(M.interpretation_apgar(2, 2, 1, 1, 2) == "normal", "Apgar 8 -> normal (≥7)")
# Seuils de classification : 7 normal, 6 modéré, 4 modéré, 3 critique
check(M.interpretation_apgar(2, 2, 1, 1, 1) == "normal", "Apgar 7 -> normal (seuil inclusif)")
check(M.interpretation_apgar(2, 2, 1, 1, 0) == "modere", "Apgar 6 -> modéré")
check(M.interpretation_apgar(2, 1, 1, 0, 0) == "modere", "Apgar 4 -> modéré (seuil inclusif)")
check(M.interpretation_apgar(1, 1, 1, 0, 0) == "critique", "Apgar 3 -> critique")

# ===================== APGAR : soundness =====================
check(leve(M.score_apgar, 3, 2, 2, 2, 2), "coloration=3 (>2) -> ValueError")
check(leve(M.score_apgar, -1, 2, 2, 2, 2), "coloration=-1 (<0) -> ValueError")
check(leve(M.score_apgar, 2, 3, 2, 2, 2), "fc=3 (>2) -> ValueError")
check(leve(M.score_apgar, 2, 2, 2, 2, 3), "respiration=3 (>2) -> ValueError")
check(leve(M.score_apgar, 2, 2, 2, 2, 1.5), "critère non entier (1.5) -> ValueError")
check(leve(M.score_apgar, True, 2, 2, 2, 2), "critère=bool -> ValueError")
check(leve(M.interpretation_apgar, 2, 2, 2, 2, 9), "interpretation critère hors plage -> ValueError")

# ===================== INDICE DE CHOC : ancres et mécanisme =====================
# FC 120 / PAS 100 = 1.2 -> choc (> 0.9)
check(abs(M.indice_choc(120, 100) - 1.2) < 1e-9, "indice_choc 120/100 = 1.2")
check(M.est_choc(120, 100) is True, "indice 1.2 -> choc")
# Sujet sain : FC 70 / PAS 120 ≈ 0.583 -> pas de choc
check(abs(M.indice_choc(70, 120) - (70 / 120)) < 1e-12, "indice_choc 70/120 exact")
check(M.est_choc(70, 120) is False, "indice ~0.58 -> pas de choc (normal)")
# Seuil STRICT > 0.9 : exactement 0.9 -> pas de choc ; juste au-dessus -> choc
check(abs(M.indice_choc(90, 100) - 0.9) < 1e-9, "indice_choc 90/100 = 0.9")
check(M.est_choc(90, 100) is False, "indice 0.9 (= seuil) -> pas de choc (strict >)")
check(M.est_choc(91, 100) is True, "indice 0.91 (> seuil) -> choc")
# Choc hémorragique typique : FC 120 / PAS 80 = 1.5
check(abs(M.indice_choc(120, 80) - 1.5) < 1e-9, "indice_choc 120/80 = 1.5 (choc)")
check(M.est_choc(120, 80) is True, "indice 1.5 -> choc")
# PAS et FC en float acceptés
check(abs(M.indice_choc(110.0, 100.0) - 1.1) < 1e-9, "indice_choc accepte float")

# ===================== INDICE DE CHOC : soundness =====================
check(leve(M.indice_choc, 120, 0), "PAS=0 -> ValueError")
check(leve(M.indice_choc, 120, -50), "PAS<0 -> ValueError")
check(leve(M.est_choc, 120, 0), "est_choc PAS=0 -> ValueError")
check(leve(M.indice_choc, 0, 100), "FC=0 -> ValueError (impossible)")
check(leve(M.indice_choc, -120, 100), "FC<0 -> ValueError")
check(leve(M.indice_choc, float("nan"), 100), "FC NaN -> ValueError")
check(leve(M.indice_choc, float("inf"), 100), "FC inf -> ValueError")
check(leve(M.indice_choc, 120, float("inf")), "PAS inf -> ValueError")
check(leve(M.indice_choc, True, 100), "FC=bool -> ValueError")
check(leve(M.indice_choc, "120", 100), "FC non numérique -> ValueError")

# ===================== DÉTERMINISME =====================
check(M.score_glasgow(4, 5, 6) == M.score_glasgow(4, 5, 6), "déterminisme score_glasgow")
check(M.score_apgar(2, 2, 2, 2, 2) == M.score_apgar(2, 2, 2, 2, 2), "déterminisme score_apgar")
check(M.indice_choc(120, 100) == M.indice_choc(120, 100), "déterminisme indice_choc")
check(M.gravite_glasgow(1, 1, 1) == M.gravite_glasgow(1, 1, 1), "déterminisme gravite_glasgow")
check(M.interpretation_apgar(2, 2, 2, 2, 2) == M.interpretation_apgar(2, 2, 2, 2, 2),
      "déterminisme interpretation_apgar")

print(f"\n=== valide_urgence_medicale : {ok}/{ok + ko} ===")
import sys
sys.exit(0 if ko == 0 else 1)
