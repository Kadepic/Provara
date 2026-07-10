"""
VALIDE selection_naturelle.py — held-out ADVERSE.

ANCRES NON CIRCULAIRES (valeurs connues INDÉPENDAMMENT de la formule testée, écrites EN DUR) :
  • HARDY-WEINBERG, cas de cours :
      – p = 1/2 -> (1/4, 1/2, 1/4)  (résultat classique, calculé à la main).
      – p = 9/10 -> (81/100, 18/100, 1/100)  (0.81, 0.18, 0.01 — valeurs de manuel).
      – INVARIANT p² + 2pq + q² = 1 EXACTEMENT, vérifié sur 101 valeurs de p (bien plus fort que 1e-12).
  • Population à l'équilibre HW : 100 AA, 200 Aa, 100 aa -> N=400, p = (2·100 + 200)/(2·400) = 400/800 = 1/2,
    attendus = 400·(1/4,1/2,1/4) = (100, 200, 100) == observés -> écart 0 -> équilibre.
    Contre-exemple : 50 AA, 0 Aa, 50 aa a la MÊME p=1/2 donc les mêmes attendus (25,50,25) mais un écart de 50
    sur les hétérozygotes -> PAS à l'équilibre (calculé à la main, chemin distinct de equilibre_hw).
  • SÉLECTION, récessif létal (w_AA=w_Aa=1, w_aa=0), formule classique q_n = q0/(1+n·q0) écrite À LA MAIN :
      – q0 = 1/2  -> q1 = (1/2)/(1+1/2) = 1/3,  q2 = (1/2)/(1+2·1/2) = 1/4.
        Donc p1 = 1 − 1/3 = 2/3 et p2 = 1 − 1/4 = 3/4 : ANCRE FORTE, indépendante de p_generation_suivante.
      – atteindre p=3/4 depuis p0=1/2 demande donc EXACTEMENT 2 générations.
  • Fitness toutes égales -> p CONSTANT (démontré : num = p(p+q) = p, dén = (p+q)² = 1).
  • w̄ à la main : p=1/2, (1,1,1) -> 1 ; p=1/2, (1,1,0) -> 1/4 + 1/2 + 0 = 3/4.
  • s = 1 − w : w=1 -> 0 ; w=0 -> 1 ; w=4/5 -> 1/5.

SOUNDNESS : p hors [0,1], fitness négative, effectif négatif, N=0, w̄=0, bool/str/float/complexe, mauvaise
arité, non-convergence, plafond de générations -> ValueError. DÉTERMINISME : double appel identique.
"""
from fractions import Fraction as F

import selection_naturelle as S

ok = 0
ko = 0


def check(cond, label):
    global ok, ko
    if cond:
        ok += 1
    else:
        ko += 1
        print(f"  FAIL: {label}")


def leve(fn, *a, **k):
    """True ssi fn(*a, **k) lève ValueError (abstention structurelle)."""
    try:
        fn(*a, **k)
        return False
    except ValueError:
        return True


# ── 1) HARDY-WEINBERG : fréquences génotypiques (ancres de cours EXACTES) ──
check(S.frequences_genotypiques(F(1, 2)) == (F(1, 4), F(1, 2), F(1, 4)), "p=1/2 -> (1/4,1/2,1/4)")
check(S.frequences_genotypiques(F(9, 10)) == (F(81, 100), F(18, 100), F(1, 100)), "p=9/10 -> (0.81,0.18,0.01)")
check(S.frequences_genotypiques(0) == (F(0), F(0), F(1)), "p=0 -> (0,0,1) tout aa")
check(S.frequences_genotypiques(1) == (F(1), F(0), F(0)), "p=1 -> (1,0,0) tout AA")
check(S.frequences_genotypiques(F(1, 3)) == (F(1, 9), F(4, 9), F(4, 9)), "p=1/3 -> (1/9,4/9,4/9)")

# ── 2) INVARIANT p²+2pq+q² = 1 EXACTEMENT sur 101 valeurs (plus fort que 1e-12) ──
somme_toutes_un = True
compte = 0
for k in range(0, 101):
    fAA, fAa, faa = S.frequences_genotypiques(F(k, 100))
    compte += 1
    if fAA + fAa + faa != 1:
        somme_toutes_un = False
check(compte == 101 and somme_toutes_un, "invariant p²+2pq+q² = 1 exact sur 101 valeurs de p")

# ── 3) FRÉQUENCE ALLÉLIQUE sur effectifs (calcul à la main) ──
check(S.frequence_allelique(100, 200, 100) == F(1, 2), "p(100,200,100) = 400/800 = 1/2")
check(S.frequence_allelique(80, 20, 0) == F(9, 10), "p(80,20,0) = 180/200 = 9/10")
check(S.frequence_allelique(0, 0, 5) == F(0), "p(0,0,5) = 0 (tout aa)")
check(S.frequence_allelique(5, 0, 0) == F(1), "p(5,0,0) = 1 (tout AA)")
check(S.frequence_allelique(1, 1, 1) == F(1, 2), "p(1,1,1) = 3/6 = 1/2")

# ── 4) ÉCART / ÉQUILIBRE HW (chemin ecart_hw indépendant du bool) ──
check(S.ecart_hw(100, 200, 100) == F(0), "écart HW (100,200,100) = 0 (à l'équilibre)")
check(S.equilibre_hw(100, 200, 100) is True, "(100,200,100) à l'équilibre HW")
# 50,0,50 : p=1/2, attendus (25,50,25), observés (50,0,50) -> écart max = |0-50| = 50
check(S.ecart_hw(50, 0, 50) == F(50), "écart HW (50,0,50) = 50 (déficit d'hétérozygotes)")
check(S.equilibre_hw(50, 0, 50) is False, "(50,0,50) PAS à l'équilibre (tol 0)")
check(S.equilibre_hw(50, 0, 50, tol=50) is True, "(50,0,50) conforme si tol=50")
check(S.equilibre_hw(50, 0, 50, tol=49) is False, "(50,0,50) non conforme si tol=49 (borne)")
check(S.equilibre_hw(50, 0, 50, tol=F(1, 2)) is False, "tol Fraction acceptée")

# ── 5) FITNESS MOYENNE w̄ (à la main) ──
check(S.w_moyen(F(1, 2), 1, 1, 1) == F(1), "w̄(1/2, 1,1,1) = 1")
check(S.w_moyen(F(1, 2), 1, 1, 0) == F(3, 4), "w̄(1/2, 1,1,0) = 1/4+1/2+0 = 3/4")
check(S.w_moyen(0, 1, 1, 0) == F(0), "w̄(p=0, 1,1,0) = q²·w_aa = 0")
check(S.w_moyen(1, 2, 1, 1) == F(2), "w̄(p=1, 2,1,1) = w_AA = 2")

# ── 6) SÉLECTION : p' (récessif létal, ancre forte q_n = q0/(1+n q0)) ──
p1 = S.p_generation_suivante(F(1, 2), 1, 1, 0)
check(p1 == F(2, 3), "p1 récessif létal depuis 1/2 = 2/3 (q1 = 1/3)")
p2 = S.p_generation_suivante(p1, 1, 1, 0)
check(p2 == F(3, 4), "p2 récessif létal = 3/4 (q2 = 1/4)")
# fitness égales -> p constant
check(S.p_generation_suivante(F(1, 3), 1, 1, 1) == F(1, 3), "fitness égales -> p constant (1/3)")
check(S.p_generation_suivante(F(2, 5), 3, 3, 3) == F(2, 5), "fitness égales (=3) -> p constant (2/5)")
# points fixes 0 et 1
check(S.p_generation_suivante(1, 2, 1, 1) == F(1), "p=1 point fixe")
check(S.p_generation_suivante(0, 1, 1, 1) == F(0), "p=0 point fixe")
# sélection en faveur de A (dominant avantagé) : p augmente
p_dir = S.p_generation_suivante(F(1, 2), 1, 1, F(1, 2))  # w_aa désavantagé
check(p_dir > F(1, 2), "sélection contre aa -> p augmente")

# ── 7) COEFFICIENT DE SÉLECTION s = 1 − w ──
check(S.coefficient_selection(1) == F(0), "s(w=1) = 0")
check(S.coefficient_selection(0) == F(1), "s(w=0) = 1 (létal)")
check(S.coefficient_selection(F(4, 5)) == F(1, 5), "s(w=4/5) = 1/5")
check(S.coefficient_selection(F(3, 2)) == F(-1, 2), "s(w=3/2) = -1/2 (allèle avantagé)")

# ── 8) GÉNÉRATIONS POUR ATTEINDRE UNE FRÉQUENCE (ancre = 2 générations) ──
check(S.generations_pour_frequence(F(1, 2), F(3, 4), 1, 1, 0) == 2, "1/2 -> 3/4 en 2 générations (récessif létal)")
check(S.generations_pour_frequence(F(1, 2), F(2, 3), 1, 1, 0) == 1, "1/2 -> 2/3 en 1 génération")
check(S.generations_pour_frequence(F(1, 2), F(1, 2), 1, 1, 0) == 0, "déjà à la cible -> 0")
# non-convergence : fitness égales (p constant), cible différente
check(leve(S.generations_pour_frequence, F(1, 2), F(3, 4), 1, 1, 1), "fitness égales -> non-convergence")
# mauvaise direction : sélection augmente p mais cible < p0
check(leve(S.generations_pour_frequence, F(1, 2), F(1, 4), 1, 1, 0), "cible dans la mauvaise direction -> ValueError")
# plafond de générations : approche trop lente pour la limite donnée
check(leve(S.generations_pour_frequence, F(1, 2), F(999, 1000), 1, 1, 0, 3), "plafond atteint -> ValueError")

# ── 9) DÉRIVE : hors périmètre (abstention systématique) ──
check(leve(S.derive_allelique), "dérive (0 arg) -> ValueError")
check(leve(S.derive_allelique, 100, F(1, 2)), "dérive (args) -> ValueError")

# ── 10) SOUNDNESS — p hors [0,1] ──
check(leve(S.frequences_genotypiques, F(3, 2)), "p>1 -> ValueError")
check(leve(S.frequences_genotypiques, F(-1, 2)), "p<0 -> ValueError")
check(leve(S.w_moyen, 2, 1, 1, 1), "w_moyen p=2 -> ValueError")
check(leve(S.p_generation_suivante, F(-1, 10), 1, 1, 1), "p_gen p<0 -> ValueError")

# ── 11) SOUNDNESS — fitness négative / w̄ = 0 ──
check(leve(S.w_moyen, F(1, 2), -1, 1, 1), "fitness négative -> ValueError")
check(leve(S.p_generation_suivante, F(1, 2), 1, F(-1, 2), 1), "w_Aa négative -> ValueError")
check(leve(S.coefficient_selection, -1), "s(w<0) -> ValueError")
check(leve(S.p_generation_suivante, F(1, 2), 0, 0, 0), "w̄=0 (toutes fitness 0) -> ValueError")
check(leve(S.p_generation_suivante, 1, 0, 1, 1), "w̄=0 (p=1, w_AA=0) -> ValueError")

# ── 12) SOUNDNESS — effectifs / population vide ──
check(leve(S.frequence_allelique, -1, 0, 0), "effectif négatif -> ValueError")
check(leve(S.frequence_allelique, 0, 0, 0), "population vide (N=0) -> ValueError")
check(leve(S.ecart_hw, 0, 0, 0), "ecart_hw N=0 -> ValueError")
check(leve(S.equilibre_hw, 1, 2, 1, -1), "tol négative -> ValueError")

# ── 13) SOUNDNESS — types invalides (bool / str / float / complexe) ──
check(leve(S.frequences_genotypiques, True), "p bool -> ValueError")
check(leve(S.frequences_genotypiques, 0.5), "p float -> ValueError (0.9 binaire ≠ 9/10)")
check(leve(S.frequences_genotypiques, "0.5"), "p str -> ValueError")
check(leve(S.frequences_genotypiques, 1 + 0j), "p complexe -> ValueError")
check(leve(S.frequence_allelique, True, 1, 1), "effectif bool -> ValueError")
check(leve(S.frequence_allelique, 1.0, 1, 1), "effectif float -> ValueError")
check(leve(S.w_moyen, F(1, 2), True, 1, 1), "fitness bool -> ValueError")
check(leve(S.coefficient_selection, 0.8), "w float -> ValueError")
check(leve(S.generations_pour_frequence, F(1, 2), F(3, 4), 1, 1, 0, True), "max_generations bool -> ValueError")
check(leve(S.generations_pour_frequence, F(1, 2), F(3, 4), 1, 1, 0, 0), "max_generations=0 -> ValueError")

# ── 14) DÉTERMINISME ──
check(S.frequences_genotypiques(F(3, 7)) == S.frequences_genotypiques(F(3, 7)), "déterminisme frequences")
check(S.p_generation_suivante(F(1, 2), 1, 1, 0) == S.p_generation_suivante(F(1, 2), 1, 1, 0), "déterminisme p'")
check(S.generations_pour_frequence(F(1, 2), F(3, 4), 1, 1, 0)
      == S.generations_pour_frequence(F(1, 2), F(3, 4), 1, 1, 0), "déterminisme générations")

# ── GARDE D'EXPLOSION EXACTE (bug RÉEL du 2026-07-10 : 5 processus bloqués à 100 % de CPU) ────────────────
# En rationnels exacts, le dénominateur de p double presque à chaque génération. Le plafond
# `max_generations` ne protège de rien : à la 40ᵉ génération une seule opération coûte déjà des milliards
# de bits. Ces cas DOIVENT abstenir vite, et ne jamais tourner sans fin.
import time as _t

_t0 = _t.time()
# Surdominance (w_Aa > w_AA, w_aa) : l'équilibre stable est p = 1/2. Une cible ÉGALE à l'équilibre n'est
# jamais atteinte (approche asymptotique) : la trajectoire progresse toujours, donc la garde de
# non-convergence ne se déclenche PAS. Seule la garde de taille sauve.
check(leve(S.generations_pour_frequence, F(1, 4), F(1, 2), 1, 2, 1, 50),
      "surdominance vers l'équilibre asymptotique -> abstention (explosion exacte)")
check(_t.time() - _t0 < 5.0, "l'abstention est IMMÉDIATE (aucune boucle infinie)")

_t0 = _t.time()
check(leve(S.generations_pour_frequence, F(1, 10), F(1, 2), 1, 3, 1, 1000),
      "surdominance p0=1/10 vers l'équilibre -> abstention")
check(_t.time() - _t0 < 5.0, "abstention immédiate (2e cas)")

# Le cas SAIN reste calculable : la surdominance atteint une cible EN DEÇÀ de l'équilibre.
check(isinstance(S.generations_pour_frequence(F(1, 4), F(2, 5), 1, 2, 1, 500), int),
      "surdominance vers une cible atteignable : le calcul aboutit (pas d'abstention abusive)")
# Le récessif létal garde des dénominateurs LINÉAIRES (q_n = q0/(1+n·q0)) : il ne doit PAS être abstenu.
check(S.generations_pour_frequence(F(1, 2), F(3, 4), 1, 1, 0) >= 1,
      "récessif létal : dénominateurs linéaires, le calcul aboutit")

print(f"\n=== valide_selection_naturelle : {ok}/{ok+ko} ===")
import sys
sys.exit(0 if ko == 0 else 1)
