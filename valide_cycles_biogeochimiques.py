"""
VALIDE cycles_biogeochimiques.py — held-out ADVERSE. Ancres EXTERNES connues :
  • τ = M/Φ : réservoir 1000 / flux 100 -> 10 ans (cas du sujet, division exacte) ;
  • bilan stationnaire ⇔ entrée == sortie ;
  • catalogue de faits de manuel CERTAINS : azote = N2 ≈ 78 % de l'atmosphère ; eau = océans ≈ 97 % ;
    carbone : réservoir actif dominant = océans ; phosphore : cycle sédimentaire SANS phase gazeuse.
+ SOUNDNESS : flux ≤ 0, réservoir < 0, flux < 0, cycle inconnu, type non numérique (bool/str/None/NaN/inf) -> ValueError.
+ DÉTERMINISME.
"""
import cycles_biogeochimiques as C

ok = 0
ko = 0


def check(cond, label):
    global ok, ko
    if cond:
        ok += 1
    else:
        ko += 1
        print(f"  FAIL: {label}")


def approx(v, attendu, rel=1e-9):
    return isinstance(v, float) and abs(v - attendu) <= rel * abs(attendu) + 1e-12


def leve(fn, *a, **k):
    try:
        fn(*a, **k)
        return False
    except ValueError:
        return True
    except Exception:
        return False


# ── 1) TEMPS DE RÉSIDENCE — ancre du sujet : 1000/100 = 10 ───────────────────────────────────────────────────────
check(approx(C.temps_residence(1000, 100), 10.0), "τ(1000, 100) = 10 ans (cas du sujet)")
check(approx(C.temps_residence(1000, 100), 1000 / 100), "τ = réservoir / flux (identité exacte)")
check(approx(C.temps_residence(0, 100), 0.0), "réservoir vide -> τ = 0 (valide)")
# Échelles : doubler le réservoir double τ ; doubler le flux divise τ par 2 (cohérence du ratio).
check(approx(C.temps_residence(2000, 100), 2 * C.temps_residence(1000, 100)), "réservoir ×2 -> τ ×2")
check(approx(C.temps_residence(1000, 200), C.temps_residence(1000, 100) / 2), "flux ×2 -> τ /2")
# Cas réaliste de manuel : eau de l'océan ~1.37e21 kg, flux ~4.25e17 kg/an -> ~3224 ans (ordre de grandeur connu).
check(approx(C.temps_residence(1.37e21, 4.25e17), 1.37e21 / 4.25e17), "τ océan = M/Φ (millénaire, exact)")
check(2000 < C.temps_residence(1.37e21, 4.25e17) < 5000, "τ de l'eau océanique ~ quelques milliers d'années")

# ── 2) BILAN — stationnaire ⇔ entrée == sortie ──────────────────────────────────────────────────────────────────
check(C.bilan_equilibre(100, 100) is True, "entrée=sortie=100 -> stationnaire")
check(C.bilan_equilibre(50, 50) is True, "entrée=sortie=50 -> stationnaire")
check(C.bilan_equilibre(0, 0) is True, "flux nuls égaux -> stationnaire trivial")
check(C.bilan_equilibre(100, 110) is False, "100 ≠ 110 -> NON stationnaire (réservoir se vide)")
check(C.bilan_equilibre(110, 100) is False, "110 ≠ 100 -> NON stationnaire (réservoir se remplit)")
check(C.bilan_equilibre(100, 100.0000000001) is True, "écart sous tolérance -> stationnaire")

# ── 3) CATALOGUE — faits de manuel CERTAINS ─────────────────────────────────────────────────────────────────────
az = C.cycle("azote")
check(az["fraction_atmospherique_N2"] == 0.78, "azote : N2 ≈ 78 % de l'atmosphère")
check("N2" in az["reservoir_principal"], "azote : réservoir principal = atmosphère (N2)")
check(az["phase_gazeuse"] is True, "azote : phase gazeuse (N2)")

eau = C.cycle("eau")
check(eau["reservoir_principal"] == "océans", "eau : réservoir principal = océans")
check(eau["fraction_eau_oceans"] == 0.97, "eau : océans ≈ 97 % de l'eau de la planète")

carb = C.cycle("carbone")
check(carb["reservoir_principal"] == "océans", "carbone : réservoir actif dominant = océans")
check(carb["phase_gazeuse"] is True, "carbone : phase gazeuse (CO2)")

phos = C.cycle("phosphore")
check(phos["reservoir_principal"] == "roches/sédiments", "phosphore : réservoir = roches/sédiments")
check(phos["phase_gazeuse"] is False, "phosphore : PAS de phase gazeuse (cycle sédimentaire)")

check(set(C.cycles_connus()) == {"carbone", "azote", "eau", "phosphore"}, "4 cycles catalogués")
# Insensibilité casse/espaces.
check(C.cycle("  Azote ")["fraction_atmospherique_N2"] == 0.78, "nom normalisé (casse/espaces)")
# Pureté : muter le dict rendu ne corrompt pas le catalogue.
d = C.cycle("eau")
d["reservoir_principal"] = "PIRATE"
check(C.cycle("eau")["reservoir_principal"] == "océans", "catalogue immuable (copie défensive)")

# ── 4) SOUNDNESS — domaine invalide -> ValueError (jamais un faux) ──────────────────────────────────────────────
check(leve(C.temps_residence, 1000, 0), "flux sortant = 0 -> ValueError")
check(leve(C.temps_residence, 1000, -100), "flux sortant < 0 -> ValueError")
check(leve(C.temps_residence, -1, 100), "réservoir < 0 -> ValueError")
check(leve(C.bilan_equilibre, -1, 100), "flux entrant < 0 -> ValueError")
check(leve(C.bilan_equilibre, 100, -1), "flux sortant < 0 -> ValueError")
check(leve(C.cycle, "soufre"), "cycle 'soufre' inconnu -> ValueError (abstention)")
check(leve(C.cycle, "oxygène"), "cycle 'oxygène' hors catalogue -> ValueError")
check(leve(C.cycle, "xyz"), "cycle bidon -> ValueError")

# ── 5) SOUNDNESS — types non numériques / non-str -> ValueError ─────────────────────────────────────────────────
check(leve(C.temps_residence, True, 100), "réservoir = bool -> ValueError")
check(leve(C.temps_residence, "mille", 100), "réservoir = str -> ValueError")
check(leve(C.temps_residence, 1000, None), "flux = None -> ValueError")
check(leve(C.temps_residence, float("nan"), 100), "réservoir = NaN -> ValueError")
check(leve(C.temps_residence, 1000, float("inf")), "flux = inf -> ValueError")
check(leve(C.bilan_equilibre, "x", 100), "bilan : entrée = str -> ValueError")
check(leve(C.cycle, 3), "cycle : nom non-str -> ValueError")
check(leve(C.cycle, None), "cycle : None -> ValueError")
check(leve(C.cycle, True), "cycle : bool -> ValueError")

# ── 6) DÉTERMINISME ─────────────────────────────────────────────────────────────────────────────────────────────
check(C.temps_residence(1000, 100) == C.temps_residence(1000, 100), "déterminisme τ")
check(C.bilan_equilibre(100, 100) == C.bilan_equilibre(100, 100), "déterminisme bilan")
check(C.cycle("azote") == C.cycle("azote"), "déterminisme cycle")

print(f"\n=== valide_cycles_biogeochimiques : {ok}/{ok+ko} ===")
import sys
sys.exit(0 if ko == 0 else 1)
