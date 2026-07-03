"""
VALIDE cybernetique.py — held-out ADVERSE. Vérifie l'algèbre de la boucle asservie sur des ANCRES EXTERNES CONNUES
(résultats d'automatique non recalculés par la même expression : retour unitaire G=10 → 0.909, limite haut-gain
1/H d'un ampli à contre-réaction, erreur statique 1/(1+Kp), identité S+T=1) + SOUNDNESS (dénominateur nul =
système singulier, H=0, types/valeurs invalides -> ValueError) + déterminisme.
"""
import cybernetique as C

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


def leve(fn, *a):
    try:
        fn(*a)
        return False
    except ValueError:
        return True


# ── 1) GAIN EN BOUCLE FERMÉE — cas de référence du sujet ──
check(approx(C.gain_boucle_fermee(10, 1), 10 / 11), "gain(10,1) = 10/11 ≈ 0.9090909")
check(approx(C.gain_boucle_fermee(100, 0.1), 100 / 11), "gain(100,0.1) = 100/11 ≈ 9.090909")
check(approx(C.gain_boucle_fermee(1, 1), 0.5), "gain(1,1) = 1/2 = 0.5")
check(approx(C.gain_boucle_fermee(0, 5), 0.0), "gain(0,H) = 0 (pas de chaîne directe)")
check(approx(C.gain_boucle_fermee(4, 0), 4.0), "gain(G,0) = G (boucle ouverte, H=0)")

# ── 2) ANCRE EXTERNE : ampli à contre-réaction haute boucle → gain ≈ 1/H ──
# G très grand, H = 0.01 → gain en boucle fermée ≈ 1/0.01 = 100 (résultat d'électronique connu).
check(abs(C.gain_boucle_fermee(1_000_000, 0.01) - 100.0) < 0.02, "haut gain, H=0.01 → ≈ 1/H = 100")
check(approx(C.gain_ideal(0.01), 100.0), "gain idéal 1/H = 100")
check(approx(C.gain_ideal(0.1), 10.0), "gain idéal 1/H = 10")
check(approx(C.gain_ideal(2.0), 0.5), "gain idéal 1/H = 0.5")

# ── 3) ERREUR STATIQUE — ess = 1/(1+Kp) (système de type 0, échelon) ──
check(approx(C.erreur_statique(1, 9), 0.1), "ess unité, Kp=9 → 1/10 = 0.1")
check(approx(C.erreur_statique(5, 4), 1.0), "ess(5,4) = 5/5 = 1.0")
check(approx(C.erreur_statique(1, 99), 0.01), "ess unité, Kp=99 → 0.01")
check(approx(C.erreur_statique(1, 0), 1.0), "ess(1,0) = 1 (aucun gain → erreur = consigne)")

# ── 4) IDENTITÉ S + T = 1 (sensibilité + transfert complémentaire) ──
for (g, h) in [(10, 1), (100, 0.1), (3, 7), (0.5, 2)]:
    s = C.fonction_sensibilite(g, h)
    t = C.transfert_complementaire(g, h)
    check(abs(s + t - 1.0) < 1e-9, f"S+T=1 pour G={g},H={h}")
# liens connus : gain = G·S  et  T = H·gain
check(abs(C.gain_boucle_fermee(10, 1) - 10 * C.fonction_sensibilite(10, 1)) < 1e-9, "gain = G·S")
check(abs(C.transfert_complementaire(10, 1) - 1 * C.gain_boucle_fermee(10, 1)) < 1e-9, "T = H·gain")
check(approx(C.fonction_sensibilite(10, 1), 1 / 11), "S(10,1) = 1/11")
check(approx(C.transfert_complementaire(10, 1), 10 / 11), "T(10,1) = 10/11")

# ── 5) STABILITÉ ──
check(C.est_stable(10, 1) is True, "stable (10,1)")
check(C.est_stable(100, 0.1) is True, "stable (100,0.1)")
check(C.est_stable(1, -1) is False, "1+G·H=0 → instable/singulier")
check(C.est_stable(2, -0.5) is False, "1+2·(−0.5)=0 → instable")

# ── 6) EFFET RÉTROACTION NÉGATIVE : ↑G rapproche le gain de 1/H ──
check(C.effet_retroaction_negative(1, 1000, 1) is True, "↑G → gain → 1/H (H=1)")
check(C.effet_retroaction_negative(0, 50, 0.1) is True, "↑G → gain → 1/H (H=0.1)")
check(C.effet_retroaction_negative(10, 1_000_000, 2) is True, "↑G → gain → 1/H (H=2)")
# l'écart au gain idéal décroît effectivement
e_petit = abs(C.gain_boucle_fermee(1, 1) - C.gain_ideal(1))
e_grand = abs(C.gain_boucle_fermee(1000, 1) - C.gain_ideal(1))
check(e_grand < e_petit, "écart au gain idéal décroît quand G augmente")

# ── 7) SOUNDNESS — dénominateurs nuls / H=0 / hors régime -> ValueError ──
check(leve(C.gain_boucle_fermee, 1, -1), "1+G·H=0 (gain) -> ValueError")
check(leve(C.gain_boucle_fermee, 2, -0.5), "1+G·H=0 (gain, autre) -> ValueError")
check(leve(C.fonction_sensibilite, 1, -1), "1+G·H=0 (S) -> ValueError")
check(leve(C.transfert_complementaire, 1, -1), "1+G·H=0 (T) -> ValueError")
check(leve(C.erreur_statique, 1, -1), "1+G=0 (ess) -> ValueError")
check(leve(C.gain_ideal, 0), "H=0 (gain idéal) -> ValueError")
check(leve(C.effet_retroaction_negative, 1, 10, 0), "H=0 (effet) -> ValueError")
check(leve(C.effet_retroaction_negative, 1, 10, -1), "H<0 hors régime -> ValueError")
check(leve(C.effet_retroaction_negative, -1, 10, 1), "G1<0 hors domaine -> ValueError")
check(leve(C.effet_retroaction_negative, 10, 5, 1), "G2≤G1 -> ValueError")

# ── 8) SOUNDNESS — types/valeurs invalides -> ValueError ──
check(leve(C.gain_boucle_fermee, True, 1), "bool -> ValueError")
check(leve(C.gain_boucle_fermee, "dix", 1), "str -> ValueError")
check(leve(C.gain_boucle_fermee, float("inf"), 1), "inf -> ValueError")
check(leve(C.gain_boucle_fermee, float("nan"), 1), "nan -> ValueError")
check(leve(C.erreur_statique, 1, None), "None -> ValueError")
check(leve(C.est_stable, "x", 1), "est_stable type invalide -> ValueError")

# ── 9) DÉTERMINISME ──
check(C.gain_boucle_fermee(10, 1) == C.gain_boucle_fermee(10, 1), "déterminisme gain")
check(C.erreur_statique(5, 4) == C.erreur_statique(5, 4), "déterminisme erreur statique")

print(f"\n=== valide_cybernetique : {ok}/{ok+ko} ===")
import sys
sys.exit(0 if ko == 0 else 1)
