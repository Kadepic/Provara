"""
VALIDE mecanismes_machines.py — held-out ADVERSE.

Ancres = mécanismes CONNUS dont la mobilité est établie par la cinématique (4 barres, bielle-manivelle,
six-barres de Watt, came, train d'engrenage, pendule, triangle articulé, liaison hyperstatique) — calculés
à la main, PAS re-dérivés par la formule du module. + SOUNDNESS (n < 1, liaison < 0, type non entier, booléen
-> ValueError) + DÉTERMINISME.
"""
import mecanismes_machines as M

ok = 0
ko = 0


def check(cond, label):
    global ok, ko
    if cond:
        ok += 1
    else:
        ko += 1
        print(f"  FAIL: {label}")


def _leve_v(fn, *a, **k) -> bool:
    """True ssi fn(*a, **k) lève ValueError (abstention), False sinon."""
    try:
        fn(*a, **k)
        return False
    except ValueError:
        return True
    except Exception:
        return False


# ── 1) ANCRES — mobilité de mécanismes CONNUS (valeurs établies, non circulaires) ──
# Mécanisme à 4 barres (quadrilatère articulé) : 4 corps, 4 pivots -> mouvement déterminé M=1.
check(M.mobilite(4, 4) == 1, "4 barres : M = 3·3 − 2·4 = 1")
check(M.mobilite(4, 4, 0) == 1, "4 barres (j2 explicite 0) : M = 1")
# Bielle-manivelle (slider-crank) : 4 corps, 3 pivots + 1 glissière = 4 liaisons 1ddl -> M=1.
check(M.mobilite(4, 4) == 1, "bielle-manivelle : M = 1")
# Mécanisme à 5 barres : 5 corps, 5 pivots -> 2 ddl (deux actionneurs).
check(M.mobilite(5, 5) == 2, "5 barres : M = 3·4 − 2·5 = 2")
# Six-barres de Watt / Stephenson : 6 corps, 7 pivots -> M=1.
check(M.mobilite(6, 7) == 1, "six-barres (Watt) : M = 3·5 − 2·7 = 1")
# Came à galet : 3 corps, 2 pivots + 1 contact came (paire supérieure) -> M=1.
check(M.mobilite(3, 2, 1) == 1, "came à galet : M = 3·2 − 2·2 − 1 = 1")
# Engrenage simple : 3 corps (bâti + 2 roues), 2 pivots + 1 engrènement -> M=1.
check(M.mobilite(3, 2, 1) == 1, "train d'engrenage simple : M = 1")
# Pendule / porte : 2 corps (bâti + barre), 1 pivot -> M=1.
check(M.mobilite(2, 1) == 1, "pendule simple : M = 3·1 − 2·1 = 1")
# Triangle articulé (3 barres, 3 pivots) : STRUCTURE isostatique, M=0 (bloqué).
check(M.mobilite(3, 3) == 0, "triangle articulé : M = 3·2 − 2·3 = 0 (structure)")
# Liaison hyperstatique : 1 barre doublement appuyée au bâti (2 corps, 2 pivots) -> M=-1.
check(M.mobilite(2, 2) == -1, "barre bi-articulée : M = 3·1 − 2·2 = −1 (hyperstatique)")
check(M.mobilite(3, 4) == -2, "surcontrainte : M = 3·2 − 2·4 = −2")
# Bâti seul (1 corps fixe, aucune liaison) -> 0 ddl.
check(M.mobilite(1, 0) == 0, "bâti seul : M = 3·0 = 0")
# Solide libre (2 corps, aucune liaison) -> le mobile a 3 ddl dans le plan.
check(M.mobilite(2, 0) == 3, "solide libre + bâti : M = 3·1 = 3")

# degres_liberte est un synonyme strict de mobilite.
check(M.degres_liberte(4, 4) == 1, "degres_liberte ≡ mobilite (4 barres)")
check(M.degres_liberte(6, 7) == M.mobilite(6, 7), "degres_liberte ≡ mobilite (Watt)")

# ── 2) INTERPRÉTATION — mouvement déterminé / structure / nature ──
check(M.mouvement_determine(4, 4) is True, "4 barres : mouvement déterminé (M=1)")
check(M.mouvement_determine(5, 5) is False, "5 barres : non déterminé (M=2)")
check(M.mouvement_determine(3, 3) is False, "triangle : non déterminé (M=0)")
check(M.mouvement_determine(3, 2, 1) is True, "came : mouvement déterminé (M=1)")

check(M.est_structure(3, 3) is True, "triangle : est une structure (M=0)")
check(M.est_structure(2, 2) is True, "bi-articulée : est une structure (M=-1)")
check(M.est_structure(4, 4) is False, "4 barres : n'est pas une structure (M=1)")
check(M.est_structure(5, 5) is False, "5 barres : n'est pas une structure (M=2)")

check(M.nature(4, 4) == M.MECANISME, "nature 4 barres = mecanisme")
check(M.nature(5, 5) == M.MECANISME, "nature 5 barres = mecanisme")
check(M.nature(3, 3) == M.STRUCTURE_ISOSTATIQUE, "nature triangle = isostatique")
check(M.nature(2, 2) == M.STRUCTURE_HYPERSTATIQUE, "nature bi-articulée = hyperstatique")
check(M.nature(3, 4) == M.STRUCTURE_HYPERSTATIQUE, "nature surcontrainte = hyperstatique")

# ── 3) SOUNDNESS — entrée invalide -> ValueError (abstention, JAMAIS un faux) ──
check(_leve_v(M.mobilite, 0, 0), "n_corps = 0 (< 1) -> ValueError")
check(_leve_v(M.mobilite, -1, 0), "n_corps = -1 -> ValueError")
check(_leve_v(M.mobilite, 4, -1), "j1 = -1 -> ValueError")
check(_leve_v(M.mobilite, 4, 4, -2), "j2 = -2 -> ValueError")
check(_leve_v(M.mobilite, 4.0, 4), "n_corps flottant -> ValueError")
check(_leve_v(M.mobilite, 4, 4.5), "j1 flottant -> ValueError")
check(_leve_v(M.mobilite, 4, 4, 1.0), "j2 flottant -> ValueError")
check(_leve_v(M.mobilite, True, 4), "n_corps booléen -> ValueError")
check(_leve_v(M.mobilite, 4, False), "j1 booléen -> ValueError")
check(_leve_v(M.mobilite, "4", 4), "n_corps str -> ValueError")
check(_leve_v(M.mobilite, 4, None), "j1 None -> ValueError")
check(_leve_v(M.mouvement_determine, 0, 0), "mouvement_determine propage ValueError")
check(_leve_v(M.est_structure, 4, -1), "est_structure propage ValueError")
check(_leve_v(M.nature, -3, 0), "nature propage ValueError")

# ── 4) DÉTERMINISME — fonctions pures, mêmes entrées -> mêmes sorties ──
check(M.mobilite(6, 7) == M.mobilite(6, 7), "mobilite déterministe")
check(M.nature(3, 2, 1) == M.nature(3, 2, 1), "nature déterministe")
check([M.mobilite(4, 4) for _ in range(5)] == [1, 1, 1, 1, 1], "5 appels identiques -> 1")

print(f"\n=== valide_mecanismes_machines : {ok}/{ok+ko} ===")
import sys
sys.exit(0 if ko == 0 else 1)
