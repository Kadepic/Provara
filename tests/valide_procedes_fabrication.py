"""
VALIDE procedes_fabrication.py — held-out ADVERSE. FAUX=0 : ancres connues + soundness (entrée invalide ->
ValueError) + déterminisme. On ne classe jamais un procédé hors référentiel ; on ne calcule jamais sur masse <= 0.
"""
import procedes_fabrication as M

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


# ── 1) ANCRES de classification (CAS de la spec) ────────────────────────────────────────────────────────────────
check(M.type_procede("fraisage") == M.SOUSTRACTIF, "fraisage soustractif")
check(M.type_procede("tournage") == M.SOUSTRACTIF, "tournage soustractif")
check(M.type_procede("perçage") == M.SOUSTRACTIF, "perçage soustractif (accent)")
check(M.type_procede("percage") == M.SOUSTRACTIF, "percage soustractif (sans accent)")
check(M.type_procede("impression_3d") == M.ADDITIF, "impression 3D additif")
check(M.type_procede("frittage") == M.ADDITIF, "frittage additif")
check(M.type_procede("moulage") == M.FORMAGE, "moulage formage")
check(M.type_procede("forgeage") == M.FORMAGE, "forgeage formage")
check(M.type_procede("estampage") == M.FORMAGE, "estampage formage")
check(M.type_procede("soudage") == M.ASSEMBLAGE, "soudage assemblage")
check(M.type_procede("collage") == M.ASSEMBLAGE, "collage assemblage")

# ── 2) NORMALISATION tolérante (mêmes faits, libellés équivalents) ───────────────────────────────────────────────
check(M.type_procede("  Fraisage  ") == M.SOUSTRACTIF, "casse + espaces")
check(M.type_procede("IMPRESSION 3D") == M.ADDITIF, "impression 3D (espace)")
check(M.type_procede("impression-3d") == M.ADDITIF, "impression-3d (tiret)")

# ── 3) SOUNDNESS classification : hors référentiel -> abstention (jamais inventer une famille) ───────────────────
check(leve(M.type_procede, "alchimie"), "procédé inconnu -> ValueError")
check(leve(M.type_procede, "usinage"), "terme générique non listé -> ValueError")
check(leve(M.type_procede, "decoupe_laser"), "decoupe_laser absent du référentiel -> ValueError")
check(leve(M.type_procede, ""), "procédé vide -> ValueError")
check(leve(M.type_procede, "   "), "procédé blancs -> ValueError")
check(leve(M.type_procede, None), "None -> ValueError")
check(leve(M.type_procede, 42), "non textuel -> ValueError")

# ── 4) RENDEMENT matière : ancres + bornes ──────────────────────────────────────────────────────────────────────
check(abs(M.rendement_matiere(0.6, 1.0) - 0.6) < 1e-12, "rendement 0.6 (CAS spec)")
check(abs(M.rendement_matiere(3.0, 5.0) - 0.6) < 1e-12, "rendement 3/5 = 0.6")
check(abs(M.rendement_matiere(1.0, 1.0) - 1.0) < 1e-12, "additif ≈ 1 (conservation)")
check(0.0 < M.rendement_matiere(0.4, 1.0) < 1.0, "soustractif < 1")
check(abs(M.rendement_matiere(2, 8) - 0.25) < 1e-12, "entiers acceptés (2/8)")

# ── 5) SOUNDNESS rendement : masses <= 0 / non finies / >1 -> abstention ─────────────────────────────────────────
check(leve(M.rendement_matiere, 0.0, 1.0), "masse_finale=0 -> ValueError")
check(leve(M.rendement_matiere, 1.0, 0.0), "masse_initiale=0 -> ValueError")
check(leve(M.rendement_matiere, -1.0, 2.0), "masse_finale<0 -> ValueError")
check(leve(M.rendement_matiere, 1.0, -2.0), "masse_initiale<0 -> ValueError")
check(leve(M.rendement_matiere, 1.5, 1.0), "rendement>1 (matière créée) -> ValueError")
check(leve(M.rendement_matiere, float("nan"), 1.0), "masse NaN -> ValueError")
check(leve(M.rendement_matiere, float("inf"), 1.0), "masse inf -> ValueError")
check(leve(M.rendement_matiere, True, 1.0), "bool -> ValueError")
check(leve(M.rendement_matiere, "0.6", 1.0), "chaîne -> ValueError")

# ── 6) DÉTERMINISME ─────────────────────────────────────────────────────────────────────────────────────────────
check(M.type_procede("fraisage") == M.type_procede("fraisage"), "déterminisme classe")
check(M.rendement_matiere(0.6, 1.0) == M.rendement_matiere(0.6, 1.0), "déterminisme rendement")

print(f"\n=== valide_procedes_fabrication : {ok}/{ok+ko} ===")
import sys
sys.exit(0 if ko == 0 else 1)
