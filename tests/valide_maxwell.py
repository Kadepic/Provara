"""
VALIDE maxwell.py — held-out ADVERSE.

ANCRES EXTERNES (valeurs CONNUES, NON recalculées par la même expression du module) :
  • vitesse de la lumière c = 299 792 458 m/s (définition SI du mètre) ;
  • impédance du vide Z0 = 376.730 313 668 Ω (valeur de référence textbook) ;
  • u_E(1e6 V/m) = 4.427 093 906 4 J/m³ (calcul à la main : ½·ε0·1e12) ;
  • u_B(1 T) = 397 887.357 7 J/m³ (calcul à la main : 1/(2·µ0)) ;
  • IDENTITÉ croisée des deux fonctions : u_E(c) == u_B(1) car c² = 1/(µ0·ε0) ;
  • IDENTITÉ Z0 == µ0·c.
SOUNDNESS : champ non numérique / non fini / bool -> ValueError (abstention) ; champ négatif ACCEPTÉ (carré).
DÉTERMINISME. Aucune de ces ancres n'est codée en dur dans maxwell.py.
"""
import maxwell as M

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


# ── 1) ANCRES EXTERNES ────────────────────────────────────────────────────────────────────────────────────────
c = M.vitesse_lumiere_calculee()
check(abs(c - 299_792_458.0) <= 0.001 * 299_792_458.0, "c calculée ≈ 299 792 458 m/s (tol 0.1%)")
check(abs(c - 299_792_458.0) < 10.0, "c calculée à <10 m/s du c connu (en fait quasi exact)")

z0 = M.impedance_vide()
check(abs(z0 - 376.730_313_668) < 1e-4, "Z0 du vide ≈ 376.730 313 668 Ω")

check(abs(M.densite_energie_E(1e6) - 4.427_093_906_4) < 1e-6, "u_E(1e6 V/m) ≈ 4.4270939 J/m³ (calcul main)")
check(abs(M.densite_energie_B(1.0) - 397_887.357_7) < 1e-3, "u_B(1 T) ≈ 397887.3577 J/m³ (calcul main)")

# ── 2) IDENTITÉS croisées (relient deux expressions différentes -> vrai test, pas une tautologie) ──
check(abs(M.densite_energie_E(299_792_458.0) - M.densite_energie_B(1.0)) < 1e-3,
      "identité de Maxwell : u_E(c) == u_B(1) (c² = 1/µ0ε0)")
check(abs(M.impedance_vide() - M.MU0 * M.vitesse_lumiere_calculee()) < 1e-5,
      "identité : Z0 == µ0·c")

# ── 3) SOUNDNESS — entrée non numérique -> ValueError (abstention, jamais un faux) ──
check(leve(M.densite_energie_E, "champ"), "u_E('champ') -> ValueError")
check(leve(M.densite_energie_E, None), "u_E(None) -> ValueError")
check(leve(M.densite_energie_E, True), "u_E(True) bool -> ValueError")
check(leve(M.densite_energie_E, [1, 2]), "u_E([1,2]) -> ValueError")
check(leve(M.densite_energie_E, float("nan")), "u_E(nan) non fini -> ValueError")
check(leve(M.densite_energie_E, float("inf")), "u_E(inf) non fini -> ValueError")
check(leve(M.densite_energie_B, None), "u_B(None) -> ValueError")
check(leve(M.densite_energie_B, "x"), "u_B('x') -> ValueError")
check(leve(M.densite_energie_totale, 1.0, "T"), "u_total(1,'T') -> ValueError")

# ── 4) CHAMP NÉGATIF ACCEPTÉ (dépend du carré — physiquement licite, surtout PAS une erreur) ──
check(M.densite_energie_E(-5.0) == M.densite_energie_E(5.0), "u_E(-5) == u_E(5) (carré)")
check(M.densite_energie_B(-2.0) == M.densite_energie_B(2.0), "u_B(-2) == u_B(2) (carré)")
check(M.densite_energie_E(0.0) == 0.0, "u_E(0) == 0")

# ── 5) DÉTERMINISME ──
check(M.vitesse_lumiere_calculee() == M.vitesse_lumiere_calculee(), "c déterministe")
check(M.densite_energie_E(7.5) == M.densite_energie_E(7.5), "u_E déterministe")

print(f"\n=== valide_maxwell : {ok}/{ok+ko} ===")
import sys
sys.exit(0 if ko == 0 else 1)
