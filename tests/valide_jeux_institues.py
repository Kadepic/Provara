"""
VALIDE jeux_institues.py — held-out ADVERSE. Les valeurs attendues sont ANCRÉES sur des théorèmes/faits
connus INDÉPENDAMMENT du code testé (jamais recalculées par la fonction testée) :

  • NIM / Bouton — la position (1,2,3) a une somme de Nim 1^2^3 = 0 : elle est PERDANTE pour le joueur au trait,
    donc `nim_coup_gagnant((1,2,3))` doit ABSTENIR (ValueError). ANCRE FORTE.
    (1,2,4) a une somme 7 != 0 : gagnante ; INVARIANT vérifié par un CHEMIN INDÉPENDANT — le coup rendu, une
    fois appliqué à la main, doit laisser une somme de Nim NULLE (peu importe la valeur littérale du tas).
    (3,4,5) a une somme 3^4^5 = 2 != 0 : gagnante.
  • MINIMAX générique confronté à Bouton : un minimax EXHAUSTIF sur l'arbre du Nim (fixtures écrites ici, sans
    aucune connaissance du XOR) doit donner « le joueur au trait gagne » SSI la somme de Nim est non nulle.
    Deux chemins de code totalement disjoints -> non circulaire.
  • MORPION (délégué à strategie_jeux) : jeu parfait = NULLE, valeur du jeu = 0.
  • PUISSANCE 4 : victoire immédiate raisonnée à la main (4e jeton d'une colonne) -> coup connu, valeur +1,
    exacte=True ; menace adverse imparable en 1 coup -> le coup optimal BLOQUE (colonne raisonnée à la main).
  • ÉCHECS : les quatre conditions de nulle sont nommées ; `coup_optimal('echecs', ...)` -> ValueError.

SOUNDNESS : tas invalides, plateaux invalides/terminaux, profondeur hors bornes, règles non callables, état non
hashable, types (bool/str/NaN/inf), mauvaise arité -> ValueError. DÉTERMINISME : double appel identique.
"""
import math

import jeux_institues as J

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
    except Exception:
        return False


# ════════════════════════════════════════════════════════════════════════════════════════════════════════════════
# 1) NIM — théorème de Bouton (ancres non circulaires)
# ════════════════════════════════════════════════════════════════════════════════════════════════════════════════
# Somme de Nim calculée À LA MAIN (XOR), écrite EN DUR :
check(J.nim_somme((1, 2, 3)) == 0, "nim_somme(1,2,3) = 1^2^3 = 0")     # 01^10^11 = 00
check(J.nim_somme((1, 2, 4)) == 7, "nim_somme(1,2,4) = 7")            # 001^010^100 = 111
check(J.nim_somme((3, 4, 5)) == 2, "nim_somme(3,4,5) = 2")           # 011^100^101 = 010
check(J.nim_somme((5,)) == 5, "nim_somme(5) = 5")
check(J.nim_somme((7, 7)) == 0, "nim_somme(7,7) = 0")

# Position perdante ssi somme nulle :
check(J.nim_position_perdante((1, 2, 3)) is True, "(1,2,3) perdante (somme 0)")
check(J.nim_position_perdante((1, 2, 4)) is False, "(1,2,4) gagnante")
check(J.nim_position_perdante((0, 0, 0)) is True, "tas tous vides = perdante")

# ANCRE FORTE : (1,2,3) perdante -> pas de coup gagnant -> ABSTENTION
check(leve(J.nim_coup_gagnant, (1, 2, 3)), "(1,2,3) perdante -> nim_coup_gagnant ABSTIENT")
check(leve(J.nim_coup_gagnant, (7, 7)), "(7,7) perdante -> ABSTIENT")
check(leve(J.nim_coup_gagnant, (0, 0)), "tas vides -> ABSTIENT")


def _applique_retrait(tas, coup):
    """Chemin INDÉPENDANT : applique (index, nb) au tas et renvoie le nouveau tuple."""
    i, nb = coup
    lst = list(tas)
    lst[i] -= nb
    return tuple(lst)


# INVARIANT : le coup gagnant ramène la somme de Nim à 0 (vérifié par chemin indépendant)
for tas in [(1, 2, 4), (3, 4, 5), (5,), (2, 3, 8), (1, 4, 6)]:
    i, nb = J.nim_coup_gagnant(tas)
    check(0 <= i < len(tas) and 1 <= nb <= tas[i], f"coup {tas} bien formé (retrait légal)")
    nouveau = _applique_retrait(tas, (i, nb))
    check(J.nim_somme(nouveau) == 0, f"coup {tas} -> somme de Nim NULLE (invariant Bouton) : {nouveau}")

# Coups déterministes attendus, calculés à la main :
# (1,2,4) : s=7 ; seul le tas de 4 a a^s<a (4^7=3<4) -> retirer 4-3 = 1 ; -> (2,1)
check(J.nim_coup_gagnant((1, 2, 4)) == (2, 1), "(1,2,4) -> retirer 1 du tas index 2 (laisse (1,2,3))")
# (3,4,5) : s=2 ; tas index 0 : 3^2=1<3 -> retirer 3-1 = 2 ; -> (0,2)
check(J.nim_coup_gagnant((3, 4, 5)) == (0, 2), "(3,4,5) -> retirer 2 du tas index 0 (laisse (1,4,5))")

# SOUNDNESS Nim
check(leve(J.nim_somme, (1, True, 3)), "bool dans tas -> ValueError")
check(leve(J.nim_somme, (1, -2, 3)), "négatif dans tas -> ValueError")
check(leve(J.nim_somme, (1, "2", 3)), "str dans tas -> ValueError")
check(leve(J.nim_somme, ()), "tas vide -> ValueError")
check(leve(J.nim_somme, 5), "tas non-séquence -> ValueError")
check(leve(J.nim_somme, (1, 2.0, 3)), "float dans tas -> ValueError")
# Déterminisme
check(J.nim_somme((3, 4, 5)) == J.nim_somme((3, 4, 5)), "nim_somme déterministe")
check(J.nim_coup_gagnant((3, 4, 5)) == J.nim_coup_gagnant((3, 4, 5)), "nim_coup_gagnant déterministe")


# ════════════════════════════════════════════════════════════════════════════════════════════════════════════════
# 2) CADRE MINIMAX GÉNÉRIQUE confronté à Bouton (chemins disjoints)
# ════════════════════════════════════════════════════════════════════════════════════════════════════════════════
# Fixtures Nim en ARBRE, sans aucune notion de XOR : état = (piles, joueur) ; joueur 0 = MAX au trait.
def _coups(e):
    piles, _ = e
    return [(i, k) for i, p in enumerate(piles) for k in range(1, p + 1)]


def _applique(e, c):
    piles, j = e
    i, k = c
    lst = list(piles)
    lst[i] -= k
    return (tuple(lst), 1 - j)


def _terminal(e):
    piles, _ = e
    return all(p == 0 for p in piles)


def _valeur(e):
    # aux feuilles : le joueur AU TRAIT ne peut plus jouer et PERD.
    # joueur 0 = MAX : s'il est au trait à la feuille, MAX perd -> -1 ; sinon MAX gagne -> +1.
    _, j = e
    return -1 if j == 0 else 1


def _joueur_max(e):
    return e[1] == 0


def _val_minimax(piles):
    prof = sum(piles) + 1
    return J.minimax((tuple(piles), 0), _coups, _applique, _terminal, _valeur, _joueur_max, prof)


# Confrontation : minimax exhaustif == +1 (MAX au trait gagne) SSI somme de Nim != 0
for piles in [(1, 2, 3), (1, 2, 4), (3, 4, 5), (1, 1), (2, 2), (1,), (0, 0), (3,)]:
    v = _val_minimax(piles)
    perdante = (J.nim_somme(piles) == 0)
    attendu = -1 if perdante else 1
    check(v == attendu, f"minimax({piles}) = {v} confirme Bouton (perdante={perdante})")

# (1,2,3) : minimax dit explicitement -1 (MAX au trait PERD), cf ancre forte
check(_val_minimax((1, 2, 3)) == -1, "minimax (1,2,3) = -1 (joueur au trait perd) [ANCRE]")
check(_val_minimax((1, 2, 4)) == 1, "minimax (1,2,4) = +1 (joueur au trait gagne)")

# coup_optimal_generique : le coup rendu mène à une position PERDANTE pour l'adversaire (somme de Nim 0)
prof = sum((1, 2, 4)) + 1
coup, val = J.coup_optimal_generique(((1, 2, 4), 0), _coups, _applique, _terminal, _valeur, _joueur_max, prof)
check(val == 1, "coup_optimal_generique (1,2,4) : valeur +1 (gagnante)")
piles_apres, joueur_apres = _applique(((1, 2, 4), 0), coup)
check(J.nim_somme(piles_apres) == 0, f"coup générique (1,2,4) -> somme de Nim 0 pour l'adversaire : {piles_apres}")

# SOUNDNESS du CADRE
check(leve(J.minimax, ((1, 2), 0), _coups, _applique, _terminal, _valeur, _joueur_max, 0),
      "profondeur_max=0 -> ValueError")
check(leve(J.minimax, ((1, 2), 0), _coups, _applique, _terminal, _valeur, _joueur_max, True),
      "profondeur_max bool -> ValueError")
check(leve(J.minimax, ((1, 2), 0), _coups, _applique, _terminal, _valeur, _joueur_max, 1000),
      "profondeur_max > borne dure -> ValueError")
check(leve(J.minimax, ((1, 2, 3), 0), _coups, _applique, _terminal, _valeur, _joueur_max, 2),
      "budget trop court (arbre non prouvé fini) -> ValueError")
check(leve(J.minimax, ((1, 2), 0), "pas_callable", _applique, _terminal, _valeur, _joueur_max, 8),
      "règle non callable -> ValueError")
# état non hashable (liste)
check(leve(J.minimax, ([1, 2], 0), _coups, _applique, _terminal, _valeur, _joueur_max, 8),
      "état non hashable -> ValueError")
# Déterminisme du CADRE
check(_val_minimax((3, 4, 5)) == _val_minimax((3, 4, 5)), "minimax déterministe")


# ════════════════════════════════════════════════════════════════════════════════════════════════════════════════
# 3) MORPION délégué (jeu parfait = nul)
# ════════════════════════════════════════════════════════════════════════════════════════════════════════════════
V = " "
vide = [V] * 9
coup_m, val_m = J.coup_optimal("morpion", vide)
check(val_m == 0, "coup_optimal('morpion', vide) : valeur 0 (jeu parfait = NUL) [ANCRE]")
check(isinstance(coup_m, int) and 0 <= coup_m <= 8, "coup_optimal morpion : case 0..8 valide")
# Gain immédiat délégué : X:0,1 au trait -> joue 2
pgx = ["X", "X", V, "O", "O", V, V, V, V]
cm2, vm2 = J.coup_optimal("morpion", pgx)
check(cm2 == 2 and vm2 == 1, "morpion gain immédiat : coup 2, valeur +1")
check(leve(J.coup_optimal, "morpion", ["X", "X", "X", "O", "O", V, V, V, V]), "morpion terminal -> ValueError")
check(leve(J.coup_optimal, "morpion", [V] * 8), "morpion plateau invalide -> ValueError")


# ════════════════════════════════════════════════════════════════════════════════════════════════════════════════
# 4) DISPATCHER coup_optimal — nim / échecs / go / puissance4 / hors catalogue
# ════════════════════════════════════════════════════════════════════════════════════════════════════════════════
cn, vn = J.coup_optimal("nim", (1, 2, 4))
check(vn == 1 and cn == J.nim_coup_gagnant((1, 2, 4)), "coup_optimal('nim',(1,2,4)) = coup de Bouton, valeur +1")
check(leve(J.coup_optimal, "nim", (1, 2, 3)), "coup_optimal('nim',(1,2,3)) perdante -> ValueError")
check(leve(J.coup_optimal, "echecs", None), "coup_optimal('echecs') -> ValueError (on ne joue pas) [ANCRE]")
check(leve(J.coup_optimal, "go", None), "coup_optimal('go') -> ValueError (on ne joue pas)")
check(leve(J.coup_optimal, "puissance4", None), "coup_optimal('puissance4') -> ValueError (hors budget)")
check(leve(J.coup_optimal, "dames", None), "jeu hors catalogue -> ValueError")
check(leve(J.coup_optimal, 42, None), "jeu non-str -> ValueError")


# ════════════════════════════════════════════════════════════════════════════════════════════════════════════════
# 5) PUISSANCE 4 — victoire immédiate, blocage, exactitude, soundness
# ════════════════════════════════════════════════════════════════════════════════════════════════════════════════
# Plateau = 7 colonnes empilées bas->haut. VICTOIRE IMMÉDIATE : X a 3 jetons en colonne 3, X au trait.
#   colonnes : 0..2 vides côté X ; on met X (3) et O (3) pour que ce soit à X de jouer.
p4_gain = (("O",), ("O",), ("O",), ("X", "X", "X"), (), (), ())   # X:3 (col3) ; O:3 (col0,1,2) ; nx==no -> X au trait
# À la main : X joue col3 -> 4 jetons verticaux -> victoire X.
r = J.puissance4_coup_optimal(p4_gain, 1)
check(r["coup"] == 3, "P4 victoire immédiate : coup = colonne 3")
check(r["valeur"] == 1.0, "P4 victoire immédiate : valeur +1 (X gagne)")
check(r["exacte"] is True, "P4 victoire immédiate : exacte=True (résultat prouvé)")

# BLOCAGE : O menace de compléter la ligne du bas (O en col 0,1,2 ; case ouverte = col3). X au trait DOIT bloquer col3.
#   X (3 jetons hors menace : col5 x2, col6 x1) ; O (3 : bas des col0,1,2). nx==no -> X au trait.
p4_bloc = (("O",), ("O",), ("O",), (), (), ("X", "X"), ("X",))
# À la main : si X ne bloque pas col3, O joue col3 et aligne 0-1-2-3 (bas) -> défaite. Seul col3 évite -1.
rb = J.puissance4_coup_optimal(p4_bloc, 2)
check(rb["coup"] == 3, "P4 blocage : X bloque la menace en colonne 3 [ANCRE raisonnée]")
check(rb["valeur"] > -1.0, "P4 blocage : valeur > -1 (la défaite est évitée)")
check(rb["exacte"] is False, "P4 blocage : exacte=False (valeur approchée, arbre coupé)")

# EXACTE=False sur position ouverte peu profonde (aucune issue prouvée en 2 plis)
r_open = J.puissance4_coup_optimal(((), (), (), (), (), (), ()), 2)
check(r_open["exacte"] is False, "P4 plateau vide, profondeur 2 : exacte=False (approché)")
check(0 <= r_open["coup"] <= 6, "P4 coup dans 0..6")
check(-1.0 < r_open["valeur"] < 1.0, "P4 valeur approchée strictement dans ]-1,1[")

# SOUNDNESS Puissance 4
check(leve(J.puissance4_coup_optimal, p4_gain, 0), "P4 profondeur 0 -> ValueError")
check(leve(J.puissance4_coup_optimal, p4_gain, 13), "P4 profondeur > 12 -> ValueError")
check(leve(J.puissance4_coup_optimal, p4_gain, True), "P4 profondeur bool -> ValueError")
check(leve(J.puissance4_coup_optimal, p4_gain, 2.0), "P4 profondeur float -> ValueError")
check(leve(J.puissance4_coup_optimal, (("O",), ("O",), ("O",)), 2), "P4 plateau ≠ 7 colonnes -> ValueError")
check(leve(J.puissance4_coup_optimal, (("Z",), (), (), (), (), (), ()), 2), "P4 jeton invalide -> ValueError")
check(leve(J.puissance4_coup_optimal, (("X",) * 7, (), (), (), (), (), ()), 2), "P4 colonne trop haute -> ValueError")
# Plateau terminal (X déjà aligné verticalement) -> aucun coup
p4_fini = (("X", "X", "X", "X"), ("O",), ("O",), ("O",), (), (), ())
check(leve(J.puissance4_coup_optimal, p4_fini, 2), "P4 position terminale -> ValueError")
# Compte incohérent (2 X / 0 O)
check(leve(J.puissance4_coup_optimal, (("X", "X"), (), (), (), (), (), ()), 2), "P4 compte incohérent -> ValueError")
# Déterminisme
check(J.puissance4_coup_optimal(p4_gain, 1) == J.puissance4_coup_optimal(p4_gain, 1), "P4 déterministe")


# ════════════════════════════════════════════════════════════════════════════════════════════════════════════════
# 6) RÈGLES — catalogue, échecs (4 nulles), immuabilité, abstention
# ════════════════════════════════════════════════════════════════════════════════════════════════════════════════
r_ech = J.regles("echecs")
check(set(r_ech["nulles"]) == {"pat", "règle des 50 coups", "triple répétition", "matériel insuffisant"},
      "échecs : les 4 conditions de nulle nommées [ANCRE]")
check(J.regles("morpion")["resolu"].startswith("oui"), "morpion résolu (nul)")
check("Bouton" in J.regles("nim")["resolu"], "nim résolu (Bouton)")
check("premier joueur" in J.regles("puissance4")["resolu"].lower()
      or "premier" in J.regles("puissance4")["resolu"].lower(), "puissance4 résolu (1er joueur)")
check(J.regles("go")["resolu"].startswith("non"), "go non résolu (module ne joue pas)")
check(leve(J.regles, "dames"), "regles('dames') hors catalogue -> ValueError")
check(leve(J.regles, 42), "regles(non-str) -> ValueError")
# Immuabilité : muter le résultat ne change pas un second appel (copie profonde)
r_ech["nulles"] = ("bidon",)
check(set(J.regles("echecs")["nulles"]) == {"pat", "règle des 50 coups", "triple répétition", "matériel insuffisant"},
      "regles() renvoie une COPIE (immuabilité du catalogue)")


print(f"\n=== valide_jeux_institues : {ok}/{ok+ko} ===")
import sys
sys.exit(0 if ko == 0 else 1)
