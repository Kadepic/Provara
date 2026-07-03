"""
VALIDE inflation.py — held-out ADVERSE.

Ancres CONNUES (non circulaires — recoupées par arithmétique indépendante / identités économiques) :
  • IPC 100 -> 105 : taux d'inflation = 5 % (manuel : 5/100·100).
  • déflation : IPC 100 -> 90 -> −10 % ; IPC 200 -> 250 -> +25 %.
  • 100 € après 5 % d'inflation : pouvoir d'achat = 100/1.05 = 95.24 € (référence du sujet).
  • un salaire de 105 € après +5 % d'inflation rachète exactement ce que 100 € rachetaient : pouvoir_achat(105,5)=100.
  • valeur réelle : 100 nominal, IPC base 100, courant 125 -> 80 (déflation par indice).
  • IDENTITÉ croisée (preuve indépendante) : valeur_reelle(v, b, c) = pouvoir_achat(v, taux_inflation(b, c)),
        car v·b/c = v/(1 + ((c−b)/b)) = v/(c/b). Recoupe DEUX fonctions par une 3e.
  • taux réel (Fisher approx) : nominal 5 %, inflation 2 % -> 3 % ; nominal 3 %, inflation 5 % -> −2 % (réel négatif).
  • Fisher EXACT : ((1.05/1.02)−1)·100 = 2.94 % < 3 % (l'approx surestime le réel) ; exact == nominal si inflation = 0.
SOUNDNESS : IPC <= 0, taux <= −100 % (facteur nul/négatif), entrée booléenne / non numérique / non finie -> ValueError.
DÉTERMINISME : mêmes entrées -> sorties identiques.
"""

import inflation as M

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


# ── 1) ANCRES — taux d'inflation (final−initial)/initial·100 ──
check(approx(M.taux_inflation(100, 105), 5.0), "IPC 100->105 -> 5 %")
check(approx(M.taux_inflation(100, 90), -10.0), "IPC 100->90 -> -10 % (déflation)")
check(approx(M.taux_inflation(200, 250), 25.0), "IPC 200->250 -> 25 %")
check(approx(M.taux_inflation(100, 100), 0.0), "IPC inchangé -> 0 %")
# Recoupement manuel : doublement de l'indice = +100 %.
check(approx(M.taux_inflation(50, 100), 100.0), "IPC 50->100 -> +100 %")
# Symétrie de signe : 100->110 = +10 mais 110->100 != -10 (base différente).
check(approx(M.taux_inflation(100, 110), 10.0), "100->110 -> +10 %")
check(approx(M.taux_inflation(110, 100), round(-10.0 / 110 * 100, 2)), "110->100 base différente (asymétrie)")

# ── 2) ANCRES — pouvoir d'achat montant/(1+taux/100) ──
check(approx(M.pouvoir_achat(100, 5), 95.24), "100 € à 5 % inflation -> 95.24 € (réf. sujet)")
check(approx(M.pouvoir_achat(100, 0), 100.0), "inflation 0 -> pouvoir d'achat inchangé")
check(approx(M.pouvoir_achat(105, 5), 100.0), "salaire 105 à +5 % rachète 100 € de base")
check(approx(M.pouvoir_achat(100, -2), round(100 / 0.98, 2)), "déflation -2 % -> pouvoir d'achat > 100")
check(approx(M.pouvoir_achat(0, 5), 0.0), "montant 0 -> 0")
# Recoupement : à +100 %, le pouvoir d'achat est divisé par 2.
check(approx(M.pouvoir_achat(100, 100), 50.0), "+100 % inflation -> pouvoir d'achat /2")

# ── 3) ANCRES — valeur réelle nominale·base/courant ──
check(approx(M.valeur_reelle(100, 100, 125), 80.0), "100, base 100, courant 125 -> 80")
check(approx(M.valeur_reelle(110, 100, 110), 100.0), "110, base 100, courant 110 -> 100")
check(approx(M.valeur_reelle(100, 100, 100), 100.0), "indices égaux -> valeur inchangée")
check(approx(M.valeur_reelle(100, 121, 100), 121.0), "base 121 > courant 100 -> valeur réelle 121")

# ── 4) IDENTITÉ CROISÉE (preuve indépendante reliant 3 fonctions) ──
for v, b, c in [(100, 100, 125), (100, 100, 200), (250, 80, 160), (100, 50, 100)]:
    t = M.taux_inflation(b, c)
    check(approx(M.valeur_reelle(v, b, c), M.pouvoir_achat(v, t)),
          f"valeur_reelle({v},{b},{c}) == pouvoir_achat({v}, taux_inflation({b},{c}))")

# ── 5) ANCRES — taux réel (Fisher) ──
check(approx(M.taux_reel(5, 2), 3.0), "réel approx = nominal 5 − inflation 2 = 3 %")
check(approx(M.taux_reel(3, 5), -2.0), "réel approx négatif : 3 − 5 = -2 %")
check(approx(M.taux_reel(0, 0), 0.0), "0 − 0 = 0")
check(approx(M.taux_reel(10, 0), 10.0), "inflation nulle -> réel = nominal")
# Fisher exact recoupé à la main : ((1.05/1.02)-1)*100 = 2.94 %.
check(approx(M.taux_reel_exact(5, 2), round((1.05 / 1.02 - 1) * 100, 2)), "Fisher exact 5/2 -> 2.94 %")
check(M.taux_reel_exact(5, 2) < M.taux_reel(5, 2), "exact < approx (l'approx surestime le réel)")
check(approx(M.taux_reel_exact(7, 0), 7.0), "Fisher exact : inflation 0 -> nominal")

# ── 6) SOUNDNESS — abstention (ValueError), faux positif INTERDIT ──
check(_leve_v(M.taux_inflation, 0, 105), "IPC_initial=0 -> ValueError")
check(_leve_v(M.taux_inflation, 100, 0), "IPC_final=0 -> ValueError")
check(_leve_v(M.taux_inflation, -100, 105), "IPC_initial<0 -> ValueError")
check(_leve_v(M.taux_inflation, 100, -5), "IPC_final<0 -> ValueError")
check(_leve_v(M.taux_inflation, float("nan"), 105), "IPC NaN -> ValueError")
check(_leve_v(M.taux_inflation, float("inf"), 105), "IPC inf -> ValueError")
check(_leve_v(M.taux_inflation, True, 105), "IPC booléen -> ValueError")
check(_leve_v(M.taux_inflation, "100", 105), "IPC chaîne -> ValueError")

check(_leve_v(M.pouvoir_achat, 100, -100), "taux=-100 % (facteur 0) -> ValueError")
check(_leve_v(M.pouvoir_achat, 100, -150), "taux<-100 % (facteur<0) -> ValueError")
check(_leve_v(M.pouvoir_achat, "100", 5), "montant non numérique -> ValueError")
check(_leve_v(M.pouvoir_achat, 100, float("nan")), "taux NaN -> ValueError")
check(_leve_v(M.pouvoir_achat, 100, True), "taux booléen -> ValueError")
check(_leve_v(M.pouvoir_achat, True, 5), "montant booléen -> ValueError")

check(_leve_v(M.valeur_reelle, 100, 0, 100), "IPC_base=0 -> ValueError")
check(_leve_v(M.valeur_reelle, 100, 100, 0), "IPC_courant=0 -> ValueError")
check(_leve_v(M.valeur_reelle, 100, -100, 100), "IPC_base<0 -> ValueError")
check(_leve_v(M.valeur_reelle, 100, 100, -100), "IPC_courant<0 -> ValueError")
check(_leve_v(M.valeur_reelle, "100", 100, 100), "valeur non numérique -> ValueError")
check(_leve_v(M.valeur_reelle, 100, 100, float("inf")), "IPC inf -> ValueError")

check(_leve_v(M.taux_reel, "5", 2), "taux_reel non numérique -> ValueError")
check(_leve_v(M.taux_reel, 5, float("nan")), "taux_reel NaN -> ValueError")
check(_leve_v(M.taux_reel, True, 2), "taux_reel booléen -> ValueError")
check(_leve_v(M.taux_reel_exact, 5, -100), "Fisher exact inflation=-100 % -> ValueError")
check(_leve_v(M.taux_reel_exact, 5, float("inf")), "Fisher exact inflation inf -> ValueError")

# ── 7) DÉTERMINISME ──
check(M.taux_inflation(123, 177) == M.taux_inflation(123, 177), "taux_inflation déterministe")
check(M.pouvoir_achat(1234.5, 7.3) == M.pouvoir_achat(1234.5, 7.3), "pouvoir_achat déterministe")
check(M.valeur_reelle(987.0, 103.2, 141.7) == M.valeur_reelle(987.0, 103.2, 141.7), "valeur_reelle déterministe")
check(M.taux_reel(4.25, 1.9) == M.taux_reel(4.25, 1.9), "taux_reel déterministe")
check(M.taux_reel_exact(4.25, 1.9) == M.taux_reel_exact(4.25, 1.9), "taux_reel_exact déterministe")

print(f"\n=== valide_inflation : {ok}/{ok+ko} ===")
import sys
sys.exit(0 if ko == 0 else 1)
