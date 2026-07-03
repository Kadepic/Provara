"""
VALIDE toxicologie.py — held-out ADVERSE.

Ancres CONNUES non circulaires (définitions de toxicologie + arithmétique vérifiée à la main) :
  • Index thérapeutique IT = DL50/DE50 (Goodman & Gilman). IT>1 = marge de sécurité.
      DL50=200, DE50=20 -> IT=10 (sûr) ; DL50=100, DE50=100 -> IT=1 ; DL50=2, DE50=20 -> 0.1 (dangereux).
  • Dose totale = mg/kg · kg : 10 mg/kg chez 70 kg = 700 mg ; 15 mg/kg chez 20 kg = 300 mg.
  • Marge de sécurité = DL1/DE99 : 100/50 = 2 ; 50/100 = 0.5 (recouvrement = danger).
  • Échelle DL50 orale (mg/kg), composés réels solidement DANS une classe :
      1 (spec, p.ex. toxines puissantes) -> 'extrêmement toxique' (<5)
      caféine ≈192 -> 'toxique' (50-500) ; sel de table ≈3000 -> 'modérément' (500-5000) ;
      éthanol ≈7060 -> 'peu toxique' (>5000).
SOUNDNESS : DE50<=0, DE99<=0, masse<=0, doses<0, non fini, non numérique -> ValueError.
DÉTERMINISME : mêmes entrées -> mêmes sorties.
"""

import toxicologie as T

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


# ── 1) ANCRE — index thérapeutique IT = DL50/DE50 ──
it = T.index_therapeutique(200, 20)
check(approx(it, 10.0), f"IT(200,20) = 10 (obtenu {it})")
check(it > 1.0, "IT(200,20) > 1 -> marge de sécurité (sûr)")
check(approx(T.index_therapeutique(100, 100), 1.0), "IT(100,100) = 1 (fenêtre nulle)")
check(approx(T.index_therapeutique(2, 20), 0.1), "IT(2,20) = 0.1 (< 1, dangereux : létale < efficace)")
check(approx(T.index_therapeutique(1000, 10), 100.0), "IT(1000,10) = 100 (large marge)")
check(approx(T.index_therapeutique(0, 50), 0.0), "IT(0,50) = 0 (DL50 nulle admise, dose>=0)")
check(approx(T.index_therapeutique(7, 2), 3.5), "IT(7,2) = 3.5")
# cohérence : multiplier DL50 par k multiplie l'IT par k (homogénéité)
check(approx(T.index_therapeutique(400, 20), 2 * T.index_therapeutique(200, 20)),
      "IT homogène : DL50 doublée -> IT doublé")

# ── 2) ANCRE — dose totale = mg/kg · kg ──
check(approx(T.dose_totale(10, 70), 700.0), "10 mg/kg · 70 kg = 700 mg")
check(approx(T.dose_totale(15, 20), 300.0), "15 mg/kg · 20 kg = 300 mg (enfant)")
check(approx(T.dose_totale(5, 2), 10.0), "5 mg/kg · 2 kg = 10 mg")
check(approx(T.dose_totale(0, 70), 0.0), "0 mg/kg · 70 kg = 0 mg (dose nulle admise)")
check(approx(T.dose_totale(2.5, 80), 200.0), "2.5 mg/kg · 80 kg = 200 mg")
# cohérence avec IT : dose totale léthale médiane = DL50_par_kg · masse
check(approx(T.dose_totale(200, 0.25), 50.0), "200 mg/kg · 0.25 kg = 50 mg (rongeur)")

# ── 3) ANCRE — marge de sécurité = DL1/DE99 ──
check(approx(T.marge_securite(100, 50), 2.0), "marge(100,50) = 2 (sûr, pas de recouvrement)")
check(approx(T.marge_securite(50, 100), 0.5), "marge(50,100) = 0.5 (< 1, recouvrement dangereux)")
check(approx(T.marge_securite(300, 100), 3.0), "marge(300,100) = 3")
check(approx(T.marge_securite(0, 10), 0.0), "marge(0,10) = 0 (DL1 nulle admise)")
# La marge de sécurité (DL1/DE99) est plus stricte que l'IT (DL50/DE50) :
# pour une distribution réaliste DL1<DL50 et DE99>DE50 -> marge <= IT.
check(T.marge_securite(150, 60) <= T.index_therapeutique(200, 50),
      "marge(DL1/DE99) <= IT(DL50/DE50) sur jeu réaliste (critère plus strict)")

# ── 4) ANCRE — classe de toxicité par DL50 (échelle établie + composés réels) ──
# Cas spec.
check(T.classe_toxicite_dl50(1) == "extrêmement toxique", "DL50=1 mg/kg -> extrêmement toxique (spec)")
# Composés réels solidement dans leur classe.
check(T.classe_toxicite_dl50(0.001) == "extrêmement toxique", "DL50≈0.001 (toxine) -> extrêmement toxique")
check(T.classe_toxicite_dl50(192) == "toxique", "caféine DL50≈192 -> toxique")
check(T.classe_toxicite_dl50(200) == "toxique", "aspirine DL50≈200 -> toxique")
check(T.classe_toxicite_dl50(3000) == "modérément", "sel de table DL50≈3000 -> modérément")
check(T.classe_toxicite_dl50(7060) == "peu toxique", "éthanol DL50≈7060 -> peu toxique")
check(T.classe_toxicite_dl50(11900) == "peu toxique", "vitamine C DL50≈11900 -> peu toxique")
check(T.classe_toxicite_dl50(20) == "très toxique", "DL50=20 -> très toxique (5-50)")
# Bornes exactes (convention : borne incluse va à la classe MOINS toxique).
check(T.classe_toxicite_dl50(4.999) == "extrêmement toxique", "4.999 -> extrêmement toxique (<5)")
check(T.classe_toxicite_dl50(5) == "très toxique", "5 (borne) -> très toxique")
check(T.classe_toxicite_dl50(49.999) == "très toxique", "49.999 -> très toxique")
check(T.classe_toxicite_dl50(50) == "toxique", "50 (borne) -> toxique")
check(T.classe_toxicite_dl50(499.999) == "toxique", "499.999 -> toxique")
check(T.classe_toxicite_dl50(500) == "modérément", "500 (borne) -> modérément")
check(T.classe_toxicite_dl50(4999.999) == "modérément", "4999.999 -> modérément")
check(T.classe_toxicite_dl50(5000) == "peu toxique", "5000 (borne) -> peu toxique")
check(T.classe_toxicite_dl50(0) == "extrêmement toxique", "0 -> extrêmement toxique (dose>=0 admise)")
# Monotonie : DL50 plus grand -> jamais plus toxique (ordre des classes).
_ordre = ["extrêmement toxique", "très toxique", "toxique", "modérément", "peu toxique"]
_vals = [0.5, 3, 10, 100, 600, 3000, 9000]
_classes = [T.classe_toxicite_dl50(v) for v in _vals]
check(all(_ordre.index(_classes[i]) <= _ordre.index(_classes[i + 1]) for i in range(len(_classes) - 1)),
      "DL50 croissant -> classe non plus toxique (monotone)")

# ── 5) SOUNDNESS — abstention (ValueError), faux positif INTERDIT ──
check(_leve_v(T.index_therapeutique, 100, 0), "DE50 = 0 -> ValueError")
check(_leve_v(T.index_therapeutique, 100, -20), "DE50 < 0 -> ValueError")
check(_leve_v(T.index_therapeutique, -1, 20), "DL50 < 0 -> ValueError")
check(_leve_v(T.index_therapeutique, float("nan"), 20), "DL50 NaN -> ValueError")
check(_leve_v(T.index_therapeutique, 100, float("inf")), "DE50 inf -> ValueError")
check(_leve_v(T.index_therapeutique, "x", 20), "DL50 non numérique -> ValueError")
check(_leve_v(T.index_therapeutique, True, 20), "DL50 booléen -> ValueError")
check(_leve_v(T.dose_totale, 10, 0), "masse_kg = 0 -> ValueError")
check(_leve_v(T.dose_totale, 10, -70), "masse_kg < 0 -> ValueError")
check(_leve_v(T.dose_totale, -5, 70), "dose_par_kg < 0 -> ValueError")
check(_leve_v(T.dose_totale, 10, float("nan")), "masse_kg NaN -> ValueError")
check(_leve_v(T.dose_totale, float("inf"), 70), "dose_par_kg inf -> ValueError")
check(_leve_v(T.dose_totale, 10, "kg"), "masse_kg non numérique -> ValueError")
check(_leve_v(T.marge_securite, 100, 0), "DE99 = 0 -> ValueError")
check(_leve_v(T.marge_securite, 100, -50), "DE99 < 0 -> ValueError")
check(_leve_v(T.marge_securite, -1, 50), "DL1 < 0 -> ValueError")
check(_leve_v(T.marge_securite, float("nan"), 50), "DL1 NaN -> ValueError")
check(_leve_v(T.classe_toxicite_dl50, -1), "DL50 < 0 -> ValueError")
check(_leve_v(T.classe_toxicite_dl50, float("nan")), "DL50 NaN -> ValueError")
check(_leve_v(T.classe_toxicite_dl50, float("inf")), "DL50 inf -> ValueError")
check(_leve_v(T.classe_toxicite_dl50, "toxique"), "DL50 non numérique -> ValueError")
check(_leve_v(T.classe_toxicite_dl50, True), "DL50 booléen -> ValueError")

# ── 6) DÉTERMINISME ──
check(T.index_therapeutique(200, 20) == T.index_therapeutique(200, 20), "IT déterministe")
check(T.dose_totale(10, 70) == T.dose_totale(10, 70), "dose_totale déterministe")
check(T.marge_securite(100, 50) == T.marge_securite(100, 50), "marge_securite déterministe")
check(T.classe_toxicite_dl50(192) == T.classe_toxicite_dl50(192), "classe_toxicite déterministe")

print(f"\n=== valide_toxicologie : {ok}/{ok+ko} ===")
import sys
sys.exit(0 if ko == 0 else 1)
