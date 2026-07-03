"""
VALIDE posologie.py — held-out ADVERSE. Exactitude des formules de dosage,
ancrées sur des cas CONNUS non circulaires (Mosteller à résultat ENTIER exact
sqrt(180·80/3600)=2.0 et sqrt(100·36/3600)=1.0 ; identité microgouttes
gouttes/min=ml/h ; règle de Clark proportionnelle) + SOUNDNESS : masse/durée/
taille/facteur ≤ 0, dose/volume < 0, entrées non numériques / non finies -> ValueError
(abstention, jamais un faux) + DÉTERMINISME. Ces cas ne figurent pas dans posologie.py.
"""
import math
import posologie as P

ok = 0
ko = 0


def check(cond, label):
    global ok, ko
    if cond:
        ok += 1
    else:
        ko += 1
        print(f"  FAIL: {label}")


def approx(v, attendu, tol=1e-6):
    return v is not None and abs(v - attendu) <= tol


def leve(fn, *a, **k):
    try:
        fn(*a, **k)
        return False
    except ValueError:
        return True
    except Exception:
        return False


# ── 1) EXACTITUDE — cas de référence de l'énoncé ──
check(approx(P.dose_totale(10, 70), 700.0), "10 mg/kg · 70 kg = 700 mg")
check(approx(P.debit_perfusion(1000, 8), 125.0), "1000 ml / 8 h = 125 ml/h")
check(approx(P.surface_corporelle_mosteller(170, 70), 1.8181, 1e-4), "BSA Mosteller(170,70) ≈ 1.8181 m²")

# ── 2) EXACTITUDE — dose_totale (proportionnalité) ──
check(approx(P.dose_totale(15, 4), 60.0), "15 mg/kg · 4 kg = 60 mg")
check(approx(P.dose_totale(2.5, 80), 200.0), "2.5 mg/kg · 80 kg = 200 mg")
check(approx(P.dose_totale(0, 70), 0.0), "0 mg/kg -> 0 mg")
check(approx(P.dose_totale(5, 12.4), 62.0), "5 mg/kg · 12.4 kg = 62 mg")

# ── 3) EXACTITUDE — débit de perfusion (ml/h) ──
check(approx(P.debit_perfusion(500, 4), 125.0), "500 ml / 4 h = 125 ml/h")
check(approx(P.debit_perfusion(1000, 24), 41.6667, 1e-4), "1000 ml / 24 h ≈ 41.67 ml/h")
check(approx(P.debit_perfusion(250, 0.5), 500.0), "250 ml / 0.5 h = 500 ml/h")
check(approx(P.debit_perfusion(0, 8), 0.0), "0 ml -> 0 ml/h")

# ── 4) EXACTITUDE — débit en gouttes/min ──
check(approx(P.debit_gouttes(1000, 480, 20), 41.6667, 1e-4), "1000 ml / 480 min · 20 = 41.67 gtt/min")
check(approx(P.debit_gouttes(60, 60, 20), 20.0), "60 ml / 60 min · 20 = 20 gtt/min")
# ANCRE NON CIRCULAIRE : microgouttes (facteur=60) => gouttes/min == débit ml/h
vol, dmin = 120.0, 60.0
check(approx(P.debit_gouttes(vol, dmin, 60), P.debit_perfusion(vol, dmin / 60.0)),
      "microgouttes : gouttes/min = débit ml/h (identité)")
check(approx(P.debit_gouttes(1000, 60, 60), 1000.0), "microgouttes 1000 ml/h = 1000 gtt/min")

# ── 5) EXACTITUDE — BSA Mosteller : ANCRES à résultat ENTIER (non circulaires) ──
check(approx(P.surface_corporelle_mosteller(180, 80), 2.0, 1e-6), "Mosteller(180,80) = 2.0 m² exact")
check(approx(P.surface_corporelle_mosteller(100, 36), 1.0, 1e-6), "Mosteller(100,36) = 1.0 m² exact")
check(approx(P.surface_corporelle_mosteller(160, 90), 2.0, 1e-6), "Mosteller(160,90) = 2.0 m² exact")
# 1 m² = sqrt(taille·masse/3600)=1 <=> taille·masse=3600 (vérification croisée arithmétique)

# ── 6) EXACTITUDE — dose pédiatrique (Clark + BSA) ──
check(approx(P.dose_pediatrique(500, 35, 70), 250.0), "Clark : 500 mg · 35/70 = 250 mg")
check(approx(P.dose_pediatrique(600, 14, 70), 120.0), "Clark : 600 mg · 14/70 = 120 mg")
check(approx(P.dose_pediatrique(500, 70, 70), 500.0), "Clark identité : masse enfant=adulte -> dose adulte")
check(approx(P.dose_pediatrique_bsa(500, 0.865, 1.73), 250.0), "BSA : 500 mg · 0.865/1.73 = 250 mg")
check(approx(P.dose_pediatrique_bsa(1730, 1.0, 1.73), 1000.0), "BSA : 1730 · 1.0/1.73 = 1000 mg")
check(approx(P.dose_pediatrique_bsa(346, 1.73, 1.73), 346.0), "BSA identité : bsa enfant=adulte -> dose adulte")

# ── 7) SOUNDNESS — diviseurs / grandeurs ≤ 0 -> ValueError ──
check(leve(P.dose_totale, 10, 0), "masse_kg = 0 -> ValueError")
check(leve(P.dose_totale, 10, -5), "masse_kg < 0 -> ValueError")
check(leve(P.debit_perfusion, 1000, 0), "duree_h = 0 -> ValueError")
check(leve(P.debit_perfusion, 1000, -8), "duree_h < 0 -> ValueError")
check(leve(P.debit_gouttes, 1000, 0, 20), "duree_min = 0 -> ValueError")
check(leve(P.debit_gouttes, 1000, 480, 0), "facteur = 0 -> ValueError")
check(leve(P.debit_gouttes, 1000, 480, -20), "facteur < 0 -> ValueError")
check(leve(P.surface_corporelle_mosteller, 0, 70), "taille_cm = 0 -> ValueError")
check(leve(P.surface_corporelle_mosteller, 170, 0), "masse_kg = 0 (BSA) -> ValueError")
check(leve(P.surface_corporelle_mosteller, -170, 70), "taille_cm < 0 -> ValueError")
check(leve(P.dose_pediatrique, 500, 0, 70), "masse_enfant = 0 -> ValueError")
check(leve(P.dose_pediatrique, 500, 35, 0), "masse_adulte = 0 -> ValueError")
check(leve(P.dose_pediatrique_bsa, 500, 0.865, 0), "bsa_adulte = 0 -> ValueError")

# ── 8) SOUNDNESS — dose / volume négatif -> ValueError ──
check(leve(P.dose_totale, -10, 70), "dose_par_kg < 0 -> ValueError")
check(leve(P.debit_perfusion, -1000, 8), "volume_ml < 0 -> ValueError")
check(leve(P.debit_gouttes, -1000, 480, 20), "volume_ml < 0 (gouttes) -> ValueError")
check(leve(P.dose_pediatrique, -500, 35, 70), "dose_adulte < 0 -> ValueError")

# ── 9) SOUNDNESS — entrées non numériques / non finies -> ValueError ──
check(leve(P.dose_totale, "dix", 70), "str -> ValueError")
check(leve(P.dose_totale, True, 70), "bool n'est pas un nombre -> ValueError")
check(leve(P.dose_totale, 10, None), "None -> ValueError")
check(leve(P.dose_totale, float("nan"), 70), "NaN -> ValueError")
check(leve(P.debit_perfusion, 1000, float("inf")), "inf -> ValueError")
check(leve(P.surface_corporelle_mosteller, float("nan"), 70), "NaN (BSA) -> ValueError")

# ── 10) DÉTERMINISME ──
check(P.dose_totale(10, 70) == P.dose_totale(10, 70), "déterminisme dose_totale")
check(P.debit_gouttes(1000, 480, 20) == P.debit_gouttes(1000, 480, 20), "déterminisme debit_gouttes")
check(P.surface_corporelle_mosteller(170, 70) == P.surface_corporelle_mosteller(170, 70),
      "déterminisme BSA")

print(f"\n=== valide_posologie : {ok}/{ok+ko} ===")
import sys
sys.exit(0 if ko == 0 else 1)
