"""
VALIDE strategie_jeux.py — held-out ADVERSE. On NE re-déduit pas la valeur par la même expression : on l'ancre sur
des FAITS connus du morpion (jeu résolu = NUL ; gain immédiat ; blocage qui tient le nul ; FOURCHETTE imparable dont
l'issue est démontrable à la main). SOUNDNESS : positions structurellement impossibles -> ValueError. Déterminisme.
Aucun de ces plateaux n'est codé en dur dans le module — ils sont jugés par l'énumération minimax.
"""
import strategie_jeux as S

ok = 0
ko = 0


def check(cond, label):
    global ok, ko
    if cond:
        ok += 1
    else:
        ko += 1
        print(f"  FAIL: {label}")


def _leve_v(fn, *a, **k):
    try:
        fn(*a, **k)
        return False
    except ValueError:
        return True
    except Exception:
        return False


V = S.VIDE

# ── 1) JEU RÉSOLU : morpion en jeu parfait depuis le début = NUL (valeur 0). FAIT de référence du jeu. ──
vide = [V] * 9
check(S.valeur_minimax(vide) == 0, "morpion vide, jeu parfait -> nul (0)")
check(S.valeur_minimax(vide, "X") == 0, "trait X explicite cohérent -> 0")
# Toute ouverture de X (centre, coin, bord) reste NULLE sous jeu parfait : aucune n'est gagnante.
for ouv in (0, 1, 4):  # coin, bord, centre
    p = [V] * 9
    p[ouv] = "X"
    check(S.valeur_minimax(p) == 0, f"après X en {ouv}, jeu parfait -> nul")

# ── 2) GAIN IMMÉDIAT : deux en ligne + 3e case libre -> le coup optimal complète la ligne. ──
# X au trait, X:0,1 -> joue 2 et gagne (+1).
pgx = ["X", "X", V, "O", "O", V, V, V, V]            # X:0,1 O:3,4 ; nx==no -> X au trait
check(S.morpion_coup_optimal(pgx) == 2, "X complète la ligne 0-1-2 en jouant 2")
check(S.valeur_minimax(pgx) == 1, "X gagne au trait -> +1")
# O au trait, O:0,1 -> joue 2 et gagne (−1).
pgo = ["O", "O", V, "X", "X", "O", "X", V, V]        # X:3,4,6 O:0,1,5 ; nx=3 no=3 -> X au trait ? recompose ci-dessous
pgo = ["O", "O", V, "X", "X", V, "X", V, V]          # X:3,4,6 (3) O:0,1 (2) ; nx=no+1 -> O au trait
check(S.gagnant(pgo) is None, "pgo non terminale")
check(S.morpion_coup_optimal(pgo) == 2, "O complète 0-1-2 en jouant 2")
check(S.valeur_minimax(pgo) == -1, "O gagne au trait -> −1")

# ── 3) BLOCAGE d'une menace adverse : X au trait, O menace 3-4-5 (case 5) -> X DOIT bloquer en 5 et tient le nul. ──
pb = ["X", V, V, "O", "O", V, V, V, "X"]             # X:0,8 O:3,4 ; nx==no -> X au trait
check(S.gagnant(pb) is None, "pb non terminale")
check(S.morpion_coup_optimal(pb) == 5, "X bloque la menace O en 5")
check(S.valeur_minimax(pb) == 0, "menace bloquable -> X tient le nul (0)")

# ── 4) FOURCHETTE imparable (raisonnée à la main, indépendamment du module) ──
# (a) O a une double menace DÉJÀ debout (O:0,1,3 -> menace 0-1-2 via 2 ET 0-3-6 via 6) ; c'est à X de jouer.
#     X ne peut bloquer qu'UNE des deux cases {2,6} ; O complète l'autre au coup suivant. X n'a ni alignement ni
#     contre-fourchette plus rapide (O a une menace immédiate). Donc O gagne en jeu parfait -> valeur −1.
ploss = ["O", "O", V, "O", "X", "X", V, "X", V]      # O:0,1,3 ; X:4,5,7 ; nx==no -> X au trait
check(S.gagnant(ploss) is None, "fourchette O : position non terminale")
check(S.valeur_minimax(ploss) == -1, "double menace O imparable -> −1 (O gagne)")
# (b) Symétrique : X a une double menace debout (X:0,1,3 -> menace 2 ET 6) ; c'est à O de jouer -> X gagne (+1).
pwin = ["X", "X", V, "X", "O", "O", V, V, V]         # X:0,1,3 ; O:4,5 ; nx==no+1 -> O au trait
check(S.gagnant(pwin) is None, "fourchette X : position non terminale")
check(S.valeur_minimax(pwin) == 1, "double menace X imparable -> +1 (X gagne)")

# ── 5) gagnant() ──
check(S.gagnant(["X", "X", "X", "O", "O", V, V, V, V]) == "X", "X aligné -> 'X'")
check(S.gagnant(["X", "O", "X", "X", "O", "O", "O", "X", "X"]) is None, "grille pleine nulle -> None")
check(S.gagnant([V] * 9) is None, "plateau vide -> aucun gagnant")
# Colonne 1-4-7 pour O :
check(S.gagnant(["X", "O", "X", "X", "O", V, V, "O", V]) == "O", "O colonne 1-4-7 -> 'O'")

# ── 6) SOUNDNESS — positions structurellement impossibles -> ValueError (jamais une réponse) ──
check(_leve_v(S.valeur_minimax, [V] * 8), "longueur 8 -> ValueError")
check(_leve_v(S.valeur_minimax, [V] * 10), "longueur 10 -> ValueError")
check(_leve_v(S.morpion_coup_optimal, ["Z"] + [V] * 8), "symbole 'Z' invalide -> ValueError")
check(_leve_v(S.gagnant, "XXXOO    "), "str (non liste/tuple) -> ValueError (spec : liste de 9)")
check(_leve_v(S.valeur_minimax, ["X", "X", "X", "X", "X", V, V, V, V]), "5 X / 0 O incohérent -> ValueError")
check(_leve_v(S.valeur_minimax, ["O", V, V, V, V, V, V, V, V]), "O en premier (0 X / 1 O) -> ValueError")
check(_leve_v(S.gagnant, ["X", "X", "X", "O", "O", "O", V, V, V]), "X et O gagnants ensemble -> ValueError")
check(_leve_v(S.valeur_minimax, ["X", "X", "X", "O", "O", "O", "O", V, V]), "X gagne mais 3X/4O -> ValueError")
check(_leve_v(S.valeur_minimax, [V] * 9, "O"), "trait=O sur plateau vide -> ValueError")
check(_leve_v(S.valeur_minimax, [V] * 9, "Z"), "joueur invalide -> ValueError")
check(_leve_v(S.morpion_coup_optimal, ["X", "O", "X", "O", "X", "O", "X", "O", "X"]), "plateau plein -> pas de coup")
check(_leve_v(S.morpion_coup_optimal, ["X", "X", "X", "O", "O", V, V, V, V]), "déjà gagné -> pas de coup")

# ── 7) DÉTERMINISME + sortie bien formée ──
ps = ["X", V, V, V, "O", V, V, V, V]
check(S.morpion_coup_optimal(ps) == S.morpion_coup_optimal(ps), "coup optimal déterministe")
check(S.valeur_minimax(ps) == S.valeur_minimax(ps) == 0, "valeur déterministe (position symétrique -> nul)")
c = S.morpion_coup_optimal(ps)
check(isinstance(c, int) and 0 <= c <= 8 and list(ps)[c] == V, "coup optimal = case vide valide (0..8)")
# Le coup gagnant immédiat préserve toujours la valeur de la position :
check(S.valeur_minimax(pgx) == 1 and S.valeur_minimax(["X", "X", "X", "O", "O", V, V, V, V]) == 1,
      "après le coup gagnant, X est gagnant (+1)")

print(f"\n=== valide_strategie_jeux : {ok}/{ok+ko} ===")
import sys
sys.exit(0 if ko == 0 else 1)
